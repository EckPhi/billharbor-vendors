from __future__ import annotations

import asyncio
import base64
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from amazon_business_de.connector import Connector as AmazonConnector
from billharbor.sdk import ArtifactPublication, SessionState
from billharbor.engine import DurableStore, RunnerConfig, RunnerContext, run_connector
import hashlib
import json
import tomllib
from oekostrom_at.connector import Connector as OekostromConnector

ROOT = Path(__file__).resolve().parents[1]


class FixtureContext:
    def __init__(self) -> None:
        self.artifacts: dict[str, bytes] = {}

    @property
    def deadline(self) -> datetime:
        return datetime.now(timezone.utc) + timedelta(minutes=1)

    def cancelled(self) -> bool:
        return False

    async def emit_safe_event(self, code: str, **counters: int) -> None:
        return None

    async def publish_artifact(
        self, *, artifact_id: str, filename: str, media_type: str, content: bytes
    ) -> ArtifactPublication:
        self.artifacts[artifact_id] = bytes(content)
        return ArtifactPublication(
            artifact_id=artifact_id,
            filename=filename,
            media_type=media_type,
            byte_size=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )


@pytest.mark.parametrize(
    ("connector_type", "fixture", "expected_transport"),
    [
        (AmazonConnector, ROOT / "vendors/amazon_business_de/tests/fixtures/synthetic_catalog.json", "api"),
        (OekostromConnector, ROOT / "vendors/oekostrom_at/tests/fixtures/synthetic_catalog.json", "browser"),
    ],
)
def test_connector_lifecycle_is_bounded_and_preserves_original_metadata(
    connector_type: type, fixture: Path, expected_transport: str
) -> None:
    async def exercise() -> None:
        connector = connector_type(fixture)
        context = FixtureContext()
        assert connector.capabilities().transports == (expected_transport,)
        assert await connector.check_session(context) is SessionState.READY
        scope = (await connector.list_scopes(context))[0]
        page = await connector.discover_page(
            context, starts_on=date(2026, 1, 1), ends_on=date(2026, 12, 31),
            scopes=(scope,), checkpoint_id=None,
        )
        assert page.documents
        assert all(value.source_path for value in page.documents[0].observations)
        artifact = await connector.fetch_document(context, page.documents[0])
        assert artifact.filename.endswith(".pdf")
        assert artifact.media_type == "application/pdf"
        assert len(artifact.sha256) == 64
        assert context.artifacts[artifact.artifact_id].startswith(b"%PDF-")
        await connector.close()
        with pytest.raises(RuntimeError, match="closed"):
            await connector.check_session(context)

    asyncio.run(exercise())


def test_pagination_is_scope_bound_and_terminal() -> None:
    async def exercise() -> None:
        connector = AmazonConnector(
            ROOT / "vendors/amazon_business_de/tests/fixtures/synthetic_catalog.json",
            page_size=1,
        )
        context = FixtureContext()
        scope = (await connector.list_scopes(context))[0]
        first = await connector.discover_page(
            context, starts_on=date(2026, 1, 1), ends_on=date(2026, 12, 31),
            scopes=(scope,), checkpoint_id=None,
        )
        assert first.checkpoint_id == "offset_1"
        assert first.terminal is False
        second = await connector.discover_page(
            context, starts_on=date(2026, 1, 1), ends_on=date(2026, 12, 31),
            scopes=(scope,), checkpoint_id=first.checkpoint_id,
        )
        assert second.checkpoint_id is None
        assert second.terminal is True
        assert first.documents[0].source_document_id != second.documents[0].source_document_id

    asyncio.run(exercise())


def test_connector_rejects_unmarked_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "unsafe.json"
    fixture.write_text('{"connector_id":"amazon_business_de"}', encoding="utf-8")
    with pytest.raises(ValueError, match="explicitly synthetic"):
        AmazonConnector(fixture)


def test_page_budget_is_bounded() -> None:
    with pytest.raises(ValueError, match="between 1 and 100"):
        AmazonConnector(
            ROOT / "vendors/amazon_business_de/tests/fixtures/synthetic_catalog.json",
            page_size=101,
        )


@pytest.mark.parametrize(
    ("connector_type", "fixture"),
    [
        (AmazonConnector, ROOT / "vendors/amazon_business_de/tests/fixtures/synthetic_catalog.json"),
        (OekostromConnector, ROOT / "vendors/oekostrom_at/tests/fixtures/synthetic_catalog.json"),
    ],
)
def test_connector_v2_bytes_reach_engine_outbox(
    connector_type: type, fixture: Path, tmp_path: Path
) -> None:
    async def exercise() -> None:
        store = DurableStore(tmp_path / "state.sqlite3", tmp_path / "artifacts")
        now = datetime.now(timezone.utc)
        store.create_execution("tenant", "run", "key", {}, now=now)
        lease = store.claim_execution("tenant", "run", lease_for=timedelta(minutes=2), now=now)
        delivery_ids = await run_connector(
            store,
            lease,
            connector_type(fixture, page_size=1),
            RunnerContext(deadline=now + timedelta(minutes=1)),
            RunnerConfig(
                tenant_id="tenant",
                account_binding_id="account_demo",
                destination_binding_id="destination_demo",
                destination_revision=1,
                connector_manifest=tomllib.loads(
                    (fixture.parents[2] / "vendor.toml").read_text(encoding="utf-8")
                ),
                starts_on=date(2026, 1, 1),
                ends_on=date(2026, 12, 31),
            ),
        )
        assert delivery_ids
        assert all(store.delivery("tenant", value)["state"] == "pending" for value in delivery_ids)
        assert store.execution("tenant", "run")["discovery_complete"] == 1
        fixture_payload = json.loads(fixture.read_text(encoding="utf-8"))
        for document in fixture_payload["documents"]:
            expected = base64.b64decode(document["content_base64"], validate=True)
            stored = store.artifact_bytes("tenant", f"fixture_{document['native_id']}")
            assert stored == expected

    asyncio.run(exercise())
