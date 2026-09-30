"""Invented portal only. These tests establish no real vendor compatibility."""
import asyncio
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import urlsplit

import pytest

from billharbor.sdk import DocumentKind, Scope, ScopeKind, SessionState
from oekostrom_at.browser import PortalMapping, create_browser_connector

PDF = b'%PDF-1.7\nInvented invoice bytes only\n%%EOF'


class Portal(BaseHTTPRequestHandler):
    mode = 'normal'

    def log_message(self, *_):
        pass

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/download/a':
            if self.mode == 'redirect':
                self.send_response(302)
                self.send_header('Location', 'http://127.0.0.1:1/forbidden')
                self.end_headers()
                return
            self.send_response(200)
            self.send_header('Content-Type', 'application/pdf')
            self.send_header('Content-Disposition', 'attachment; filename="invented.pdf"')
            self.end_headers()
            self.wfile.write(b'not a PDF' if self.mode == 'bad_pdf' else PDF)
            return
        if path == '/login':
            body = '<form action="/docs"><input name="username"><input name="password"><button>Login</button></form>'
        else:
            body = '<main id="ready"><i class="scope" data-scope="installation-a"></i>'
            if self.mode == 'challenge':
                body = '<i id="challenge"></i>'
            else:
                items = [('same-a', '2026-09-01'), ('same-b', '2026-09-02')]
                if self.mode == 'duplicate':
                    items[1] = items[0]
                for native, day in items:
                    body += f'<div class="document" data-scope="installation-a" data-id="{native}" data-date="{day}" data-kind="invoice"><a href="/download/a">PDF</a></div>'
                if self.mode == 'pagination':
                    body += '<button id="next">More</button>'
                if self.mode == 'foreign':
                    body += '<img src="http://127.0.0.1:1/forbidden">'
                body += '</main>'
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(body.encode())


@pytest.fixture
def portal():
    Portal.mode = 'normal'
    server = ThreadingHTTPServer(('127.0.0.1', 0), Portal)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}'
    server.shutdown()
    server.server_close()
    thread.join()


def mapping(origin):
    return PortalMapping(origin, '/login', '/docs', '[name=username]', '[name=password]',
                         'button', '#ready', '#challenge', '.scope', '.document', 'a',
                         '#next', 'data-scope', 'data-id', 'data-date', 'data-kind', page_size=1)


class Context:
    deadline = datetime.now(timezone.utc) + timedelta(minutes=10)
    requests = 0
    publications = None

    def cancelled(self):
        return False

    async def consume_request(self):
        self.requests += 1
        if self.requests > 100:
            raise RuntimeError('Budget spent')

    async def publish_artifact(self, **kwargs):
        self.publications = kwargs
        return kwargs


def test_live_profile_rejected():
    with pytest.raises(ValueError, match='live-reviewed'):
        mapping('https://mein.oekostrom.at')
    with pytest.raises(ValueError, match='live-reviewed'):
        replace(mapping('http://127.0.0.1:9876'), synthetic=False)


def test_actual_browser_lifecycle(portal):
    pytest.importorskip('playwright.async_api')

    async def run():
        context = Context()
        connector = await create_browser_connector(mapping(portal),
                     lambda: {'username': 'invented', 'password': 'fixture-only'})
        try:
            assert await connector.check_session(context) == SessionState.READY
            scopes = await connector.list_scopes(context)
            assert scopes == (Scope(ScopeKind.INSTALLATION, 'installation-a'),)
            query = dict(starts_on=date(2026, 9, 1), ends_on=date(2026, 9, 2), scopes=scopes)
            first = await connector.discover_page(context, checkpoint_id=None, **query)
            assert not first.terminal
            artifact = await connector.fetch_document(context, first.documents[0])
            assert artifact['content'] == PDF
            with pytest.raises(ValueError, match='scope/kind'):
                await connector.fetch_document(context, replace(first.documents[0], document_kind=DocumentKind.CREDIT_NOTE))
            second = await connector.discover_page(context, checkpoint_id=first.checkpoint_id, **query)
            assert second.terminal and second.documents[0].source_document_id != first.documents[0].source_document_id
            with pytest.raises(ValueError, match='filters or portal snapshot'):
                await connector.discover_page(context, checkpoint_id=first.checkpoint_id,
                    **dict(query, ends_on=date(2026, 9, 1)))
            empty = await connector.discover_page(context, checkpoint_id=None,
                **dict(query, starts_on=date(2026, 9, 3), ends_on=date(2026, 9, 3)))
            assert empty.terminal and not empty.documents
            Portal.mode = 'pagination'
            with pytest.raises(RuntimeError, match='pagination'):
                await connector.discover_page(context, checkpoint_id=None, **query)
            Portal.mode = 'challenge'
            interaction = await connector.discover_page(context, checkpoint_id=None, **query)
            assert interaction.safe_message_code == 'oekostrom_manual_challenge'
            assert context.requests > 0
        finally:
            await connector.close()
    asyncio.run(run())


def test_browser_origin_and_download_limits(portal):
    pytest.importorskip('playwright.async_api')

    async def run():
        context = Context()
        connector = await create_browser_connector(replace(mapping(portal), maximum_document_bytes=5))
        try:
            query = dict(starts_on=date(2026, 9, 1), ends_on=date(2026, 9, 2),
                         scopes=(Scope(ScopeKind.INSTALLATION, 'installation-a'),), checkpoint_id=None)
            page = await connector.discover_page(context, **query)
            with pytest.raises(ValueError, match='byte limit'):
                await connector.fetch_document(context, page.documents[0])
            Portal.mode = 'foreign'
            with pytest.raises(RuntimeError, match='network policy'):
                await connector.discover_page(context, **query)
        finally:
            await connector.close()
    asyncio.run(run())


def test_browser_recovery_and_invalid_originals(portal):
    pytest.importorskip('playwright.async_api')

    async def run():
        query = dict(starts_on=date(2026, 9, 1), ends_on=date(2026, 9, 2),
                     scopes=(Scope(ScopeKind.INSTALLATION, 'installation-a'),))
        first_connector = await create_browser_connector(mapping(portal))
        try:
            first = await first_connector.discover_page(Context(), checkpoint_id=None, **query)
        finally:
            await first_connector.close()
        connector = await create_browser_connector(mapping(portal))
        try:
            # Checkpoint survives process/session restart with an unchanged snapshot.
            second = await connector.discover_page(Context(), checkpoint_id=first.checkpoint_id, **query)
            assert second.terminal
            Portal.mode = 'bad_pdf'
            with pytest.raises(ValueError, match='not a PDF'):
                await connector.fetch_document(Context(), second.documents[0])
            Portal.mode = 'duplicate'
            with pytest.raises(ValueError, match='Duplicate document identity'):
                await connector.discover_page(Context(), checkpoint_id=None, **query)
        finally:
            await connector.close()
    asyncio.run(run())


def test_browser_candidate_runs_through_durable_engine(portal, tmp_path):
    """Invented account proof across the real runner and outbox boundaries."""
    pytest.importorskip('playwright.async_api')
    from pathlib import Path
    import tomllib
    from billharbor.engine.runner import RunnerConfig, RunnerContext, run_connector
    from billharbor.engine.store import DurableStore

    manifest = tomllib.loads((Path(__file__).parents[1] / 'vendors/oekostrom_at/browser-synthetic.toml').read_text())
    store = DurableStore(tmp_path / 'state.db', tmp_path / 'artifacts')
    store.create_execution('synthetic_tenant', 'run', 'key', {})
    lease = store.claim_execution('synthetic_tenant', 'run', lease_for=timedelta(minutes=5))
    config = RunnerConfig('synthetic_tenant', 'synthetic_account', 'synthetic_destination', 1,
        manifest, date(2026, 9, 1), date(2026, 9, 2), document_kinds=('invoice',),
        selected_scopes=(('installation', 'installation-a'),))

    async def run():
        connector = await create_browser_connector(mapping(portal),
            lambda: {'username':'invented', 'password':'fixture-only'})
        return await run_connector(store, lease, connector,
            RunnerContext(datetime.now(timezone.utc) + timedelta(minutes=3)), config)

    deliveries = asyncio.run(run())
    assert len(deliveries) == 2
    assert store.execution('synthetic_tenant', 'run')['state'] == 'succeeded'
    assert all(store.delivery_payload('synthetic_tenant', delivery)[1] == PDF
               for delivery in deliveries)
    assert not store.audit_artifacts('synthetic_tenant').missing
