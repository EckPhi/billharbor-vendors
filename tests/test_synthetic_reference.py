"""Reference fixture completeness and unchanged-original guardrails."""
import asyncio
import base64
import json
from datetime import date
from pathlib import Path

import pytest

from billharbor_synthetic.connector import Connector
from test_connectors import FixtureContext

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'vendors/billharbor_synthetic/tests/fixtures/synthetic_catalog.json'


def test_reference_scope_pagination_and_pdf_bytes():
    async def exercise():
        connector = Connector(FIXTURE, page_size=1)
        context = FixtureContext()
        scopes = await connector.list_scopes(context)
        assert [scope.id for scope in scopes] == ['installation-a', 'installation-b']
        checkpoint = None
        documents = []
        while True:
            page = await connector.discover_page(context, starts_on=date(2026, 1, 1),
                ends_on=date(2026, 1, 31), scopes=scopes, checkpoint_id=checkpoint)
            documents.extend(page.documents)
            if page.terminal:
                break
            checkpoint = page.checkpoint_id
        assert len(documents) == 4
        assert len({item.source_document_id for item in documents}) == 4
        for reference in documents:
            artifact = await connector.fetch_document(context, reference)
            content = context.artifacts[artifact.artifact_id]
            assert b'/Type /Page ' in content and b'startxref' in content
            assert b'not a financial document' in content
        assert len(set(context.artifacts.values())) == 4
        first = await connector.discover_page(context, starts_on=date(2026, 1, 1),
            ends_on=date(2026, 1, 1), scopes=(scopes[0],), checkpoint_id=None)
        assert len(first.documents) == 1 and first.terminal
        await connector.close()
    asyncio.run(exercise())


def test_reference_rejects_foreign_fixture_and_bad_pdf(tmp_path):
    payload = json.loads(FIXTURE.read_text())
    payload['connector_id'] = 'oekostrom_at'
    path = tmp_path / 'foreign.json'
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match='connector_id'):
        Connector(path)
    payload['connector_id'] = 'billharbor_synthetic'
    payload['documents'][0]['content_base64'] = base64.b64encode(b'<html>login</html>').decode()
    path.write_text(json.dumps(payload))
    async def exercise():
        connector = Connector(path)
        context = FixtureContext()
        scopes = await connector.list_scopes(context)
        page = await connector.discover_page(context, starts_on=date(2026, 1, 1),
            ends_on=date(2026, 1, 31), scopes=(scopes[0],), checkpoint_id=None)
        with pytest.raises(ValueError, match='not a PDF'):
            await connector.fetch_document(context, page.documents[0])
        await connector.close()
    asyncio.run(exercise())
