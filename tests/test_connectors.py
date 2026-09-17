from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from amazon_business_de.connector import Connector as AmazonConnector
from billharbor.sdk import SessionState
from oekostrom_at.connector import Connector as OekostromConnector

ROOT = Path(__file__).resolve().parents[1]


class FixtureContext:
    @property
    def deadline(self) -> datetime:
        return datetime.now(timezone.utc) + timedelta(minutes=1)

    def cancelled(self) -> bool:
        return False

    async def emit_safe_event(self, code: str, **counters: int) -> None:
        return None


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
