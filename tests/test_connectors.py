from __future__ import annotations

import asyncio
import base64
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from amazon_business_de.connector import Connector as AmazonConnector
from billharbor.sdk import ArtifactPublication, SessionState
from billharbor.engine import DurableStore, RunnerConfig, RunnerContext, run_connector
from billharbor.engine.runner import _scoped_artifact_identity, _scoped_source_identity
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
        query = {
            "starts_on": "2026-01-01",
            "ends_on": "2026-12-31",
            "scopes": sorted((item.kind.value, item.id) for item in (scope,)),
        }
        digest = hashlib.sha256(
            json.dumps(query, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16]
        assert first.checkpoint_id == f"cursor_{digest}_1"
        assert first.terminal is False
        second = await connector.discover_page(
            context, starts_on=date(2026, 1, 1), ends_on=date(2026, 12, 31),
            scopes=(scope,), checkpoint_id=first.checkpoint_id,
        )
        assert second.checkpoint_id is None
        assert second.terminal is True
        assert first.documents[0].source_document_id != second.documents[0].source_document_id

    asyncio.run(exercise())


def test_legacy_offset_checkpoint_can_finish_after_upgrade() -> None:
    async def exercise() -> None:
        connector = AmazonConnector(
            ROOT / "vendors/amazon_business_de/tests/fixtures/synthetic_catalog.json",
            page_size=1,
        )
        context = FixtureContext()
        scope = (await connector.list_scopes(context))[0]
        page = await connector.discover_page(
            context, starts_on=date(2026, 1, 1), ends_on=date(2026, 12, 31),
            scopes=(scope,), checkpoint_id="offset_1",
        )
        assert len(page.documents) == 1
        assert page.terminal is True

    asyncio.run(exercise())


def test_checkpoint_rejects_unemitted_offset() -> None:
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
        invalid = first.checkpoint_id.rsplit("_", 1)[0] + "_999"
        with pytest.raises(ValueError, match="not emitted"):
            await connector.discover_page(
                context, starts_on=date(2026, 1, 1), ends_on=date(2026, 12, 31),
                scopes=(scope,), checkpoint_id=invalid,
            )
        with pytest.raises(ValueError, match="not emitted"):
            await connector.discover_page(
                context, starts_on=date(2026, 1, 1), ends_on=date(2026, 12, 31),
                scopes=(scope,), checkpoint_id="offset_999",
            )

    asyncio.run(exercise())


def test_checkpoint_is_bound_to_scope_and_date_filters() -> None:
    async def exercise() -> None:
        connector = AmazonConnector(
            ROOT / "vendors/amazon_business_de/tests/fixtures/synthetic_catalog.json",
            page_size=1,
        )
        context = FixtureContext()
        scopes = await connector.list_scopes(context)
        first = await connector.discover_page(
            context, starts_on=date(2026, 1, 1), ends_on=date(2026, 12, 31),
            scopes=(scopes[0],), checkpoint_id=None,
        )
        replay = await connector.discover_page(
            context, starts_on=date(2026, 1, 1), ends_on=date(2026, 12, 31),
            scopes=(scopes[0],), checkpoint_id=first.checkpoint_id,
        )
        assert replay.terminal is True
        with pytest.raises(ValueError, match="does not match"):
            await connector.discover_page(
                context, starts_on=date(2026, 2, 1), ends_on=date(2026, 12, 31),
                scopes=(scopes[0],), checkpoint_id=first.checkpoint_id,
            )
        with pytest.raises(ValueError, match="does not match"):
            await connector.discover_page(
                context, starts_on=date(2026, 1, 1), ends_on=date(2026, 12, 31),
                scopes=(scopes[1],), checkpoint_id=first.checkpoint_id,
            )

    asyncio.run(exercise())


def test_empty_terminal_page_has_explicit_completion() -> None:
    async def exercise() -> None:
        connector = OekostromConnector(
            ROOT / "vendors/oekostrom_at/tests/fixtures/synthetic_catalog.json"
        )
        context = FixtureContext()
        scope = (await connector.list_scopes(context))[0]
        page = await connector.discover_page(
            context, starts_on=date(2030, 1, 1), ends_on=date(2030, 12, 31),
            scopes=(scope,), checkpoint_id=None,
        )
        assert page.documents == ()
        assert page.checkpoint_id is None
        assert page.terminal is True

    asyncio.run(exercise())


def test_connector_rejects_unmarked_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "unsafe.json"
    fixture.write_text('{"connector_id":"amazon_business_de"}', encoding="utf-8")
    with pytest.raises(ValueError, match="explicitly synthetic"):
        AmazonConnector(fixture)


def test_d4_rejects_duplicate_typed_source_identity(tmp_path: Path) -> None:
    source = ROOT / "vendors/amazon_business_de/tests/fixtures/synthetic_catalog.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["documents"].append(payload["documents"][0])
    fixture = tmp_path / "duplicate.json"
    fixture.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate synthetic document scope identity"):
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
        context = FixtureContext()
        for document in fixture_payload["documents"]:
            expected = base64.b64decode(document["content_base64"], validate=True)
            reference = connector_type(fixture)._reference(
                next(scope for scope in await connector_type(fixture).list_scopes(context)
                     if scope.kind.value == document["scope_kind"] and scope.id == document["scope_id"]),
                document,
            )
            source_identity = _scoped_source_identity(
                connector_type.connector_id, "account_demo", reference
            )
            stored = store.artifact_bytes(
                "tenant",
                _scoped_artifact_identity(source_identity),
            )
            assert stored == expected

    asyncio.run(exercise())


def test_d4_scoped_identity_and_document_types() -> None:
    async def exercise() -> None:
        amazon = AmazonConnector(ROOT / "vendors/amazon_business_de/tests/fixtures/synthetic_catalog.json")
        oeko = OekostromConnector(ROOT / "vendors/oekostrom_at/tests/fixtures/synthetic_catalog.json")
        context = FixtureContext()
        amazon_scopes = await amazon.list_scopes(context)
        pages = [await amazon.discover_page(context, starts_on=date(2026, 1, 1),
                 ends_on=date(2026, 12, 31), scopes=(scope,), checkpoint_id=None)
                 for scope in amazon_scopes]
        assert [len(page.documents) for page in pages] == [2, 1]
        assert pages[0].documents[0].source_document_id != pages[1].documents[0].source_document_id
        assert {item.document_kind.value for item in pages[0].documents} == {"invoice", "credit_note"}
        assert all(len(item.observations) >= 4 for page in pages for item in page.documents)
        with pytest.raises(ValueError, match="unknown synthetic scope"):
            await amazon.discover_page(context, starts_on=date(2026, 1, 1),
                ends_on=date(2026, 12, 31), scopes=(await oeko.list_scopes(context))[0:1], checkpoint_id=None)
        oeko_scopes = await oeko.list_scopes(context)
        oeko_pages = [await oeko.discover_page(context, starts_on=date(2026, 1, 1),
                      ends_on=date(2026, 12, 31), scopes=(scope,), checkpoint_id=None)
                      for scope in oeko_scopes]
        assert {item.document_kind.value for page in oeko_pages for item in page.documents} == {
            "invoice", "credit_note", "settlement"}
        await amazon.close()
        await oeko.close()

    asyncio.run(exercise())
