"""Bounded browser implementation; no reviewed live Ökostrom profile exists.

Selectors in tests describe an invented portal. Supplying live origins is
intentionally rejected until D6 establishes stable identity and date semantics.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from billharbor.sdk import (
    ConnectorCapabilities, DiscoveryPage, DocumentKind, DocumentReference,
    InteractionKind, InteractionRequest, Observation, ObservationField,
    ObservationSource, ObservationValueType, Scope, ScopeKind, SessionState,
)


@dataclass(frozen=True)
class PortalMapping:
    origin: str
    login_path: str
    documents_path: str
    username: str
    password: str
    submit: str
    ready: str
    challenge: str
    scope_rows: str
    document_rows: str
    download: str
    next_page: str
    scope_attribute: str
    native_id_attribute: str
    date_attribute: str
    kind_attribute: str
    synthetic: bool = True
    maximum_rows: int = 1000
    page_size: int = 100
    maximum_document_bytes: int = 25 * 1024 * 1024

    def __post_init__(self):
        parsed = urlsplit(self.origin)
        if (not self.synthetic or parsed.scheme != 'http'
                or parsed.hostname != '127.0.0.1' or not parsed.port
                or parsed.path or parsed.query or parsed.fragment
                or parsed.username or parsed.password):
            raise ValueError('No live-reviewed Ökostrom mapping: invented loopback only')
        for path in (self.login_path, self.documents_path):
            if not path.startswith('/') or path.startswith('//') or urlsplit(path).netloc:
                raise ValueError('Mapping paths must be relative to the approved origin')
        if not 1 <= self.page_size <= 100 or not 1 <= self.maximum_rows <= 10000:
            raise ValueError('Invalid discovery limits')
        if not 1 <= self.maximum_document_bytes <= 25 * 1024 * 1024:
            raise ValueError('Invalid download limit')


class BrowserConnector:
    def __init__(self, page, mapping: PortalMapping, credential_resolver=None,
                 *, resources=()):
        self.page, self.mapping = page, mapping
        self.credential_resolver = credential_resolver
        self.resources = resources
        self._closed = False
        self._guarded = False
        self._network_failure = False
        self._records = {}
        self._query = None

    def capabilities(self):
        return ConnectorCapabilities('oekostrom_at', (DocumentKind.INVOICE,), ('browser',), True)

    async def _prepare(self, context):
        if self._closed or context.cancelled() or datetime.now(timezone.utc) >= context.deadline:
            raise RuntimeError('Browser execution unavailable')
        if not self._guarded:
            async def route_request(route):
                parsed = urlsplit(route.request.url)
                origin = f'{parsed.scheme}://{parsed.netloc}'
                try:
                    if origin != self.mapping.origin or parsed.username or parsed.password:
                        raise RuntimeError('Origin not permitted')
                    await context.consume_request()
                except Exception:
                    self._network_failure = True
                    await route.abort()
                    return
                await route.continue_()
            await self.page.context.route('**/*', route_request)
            # WebSockets bypass ordinary request routing. No profile requires them.
            await self.page.context.route_web_socket('**/*', lambda socket: socket.close())
            self._guarded = True
        if self._network_failure:
            raise RuntimeError('Browser network policy or budget rejected a request')

    def _check_origin(self):
        parsed = urlsplit(self.page.url)
        if f'{parsed.scheme}://{parsed.netloc}' != self.mapping.origin or self._network_failure:
            raise RuntimeError('Browser network policy rejected navigation')

    async def _interaction(self, context):
        self._check_origin()
        if await self.page.locator(self.mapping.challenge).count():
            return InteractionRequest(InteractionKind.MFA, 'oekostrom_manual_challenge', context.deadline)
        if not await self.page.locator(self.mapping.ready).count():
            return InteractionRequest(InteractionKind.SESSION_EXPIRED, 'oekostrom_session_expired', context.deadline)
        return None

    async def check_session(self, context):
        await self._prepare(context)
        await self.page.goto(self.mapping.origin + self.mapping.login_path)
        self._check_origin()
        if await self.page.locator(self.mapping.challenge).count():
            return await self._interaction(context)
        if await self.page.locator(self.mapping.ready).count():
            return SessionState.READY
        if self.credential_resolver is None:
            return InteractionRequest(InteractionKind.SESSION_EXPIRED, 'oekostrom_manual_login', context.deadline)
        credentials = self.credential_resolver()
        try:
            await self.page.locator(self.mapping.username).fill(credentials['username'])
            await self.page.locator(self.mapping.password).fill(credentials['password'])
            await self.page.locator(self.mapping.submit).click()
            await self.page.wait_for_load_state('domcontentloaded')
        finally:
            del credentials
        return await self._interaction(context) or SessionState.READY

    async def _open_documents(self, context):
        await self._prepare(context)
        await self.page.goto(self.mapping.origin + self.mapping.documents_path)
        return await self._interaction(context)

    async def list_scopes(self, context):
        interaction = await self._open_documents(context)
        if interaction:
            # SDK list_scopes cannot return an InteractionRequest.
            raise RuntimeError(interaction.safe_message_code)
        rows = self.page.locator(self.mapping.scope_rows)
        count = await rows.count()
        if not 1 <= count <= self.mapping.maximum_rows:
            raise ValueError('Scope list exceeds bounds or is empty')
        scopes = tuple([Scope(ScopeKind.INSTALLATION,
                             await rows.nth(i).get_attribute(self.mapping.scope_attribute))
                       for i in range(count)])
        if len(set(scopes)) != len(scopes):
            raise ValueError('Duplicate installation identity')
        return scopes

    async def discover_page(self, context, *, starts_on: date, ends_on: date,
                            scopes: tuple[Scope, ...], checkpoint_id: str | None):
        await self._prepare(context)
        if starts_on > ends_on or not scopes or len(set(scopes)) != len(scopes):
            raise ValueError('Invalid discovery scope/date window')
        query = json.dumps([starts_on.isoformat(), ends_on.isoformat(),
                            sorted((s.kind.value, s.id) for s in scopes)])
        interaction = await self._open_documents(context)
        if interaction:
            return interaction
        if not set(scopes) <= set(await self.list_scopes(context)):
            raise ValueError('Unknown installation')
        # Only complete combined-view snapshots are supported. Never silently
        # report terminal when a portal adds pagination.
        if await self.page.locator(self.mapping.next_page).count():
            raise RuntimeError('Unreviewed portal pagination')
        rows = self.page.locator(self.mapping.document_rows)
        count = await rows.count()
        if count > self.mapping.maximum_rows:
            raise ValueError('Document list exceeds configured bound')
        selected = {s.id: s for s in scopes}
        records = {}
        seen = set()
        for i in range(count):
            row = rows.nth(i)
            scope_id = await row.get_attribute(self.mapping.scope_attribute)
            if scope_id not in selected:
                continue
            kind = await row.get_attribute(self.mapping.kind_attribute)
            if kind != 'invoice':
                continue  # Deposits, credits and PV settlements are unsupported.
            native = await row.get_attribute(self.mapping.native_id_attribute)
            issued = await row.get_attribute(self.mapping.date_attribute)
            if not native or len(native) > 200:
                raise ValueError('Missing stable document identity')
            identity = (scope_id, kind, native)
            if identity in seen:
                raise ValueError('Duplicate document identity in snapshot')
            seen.add(identity)
            if not starts_on <= date.fromisoformat(issued) <= ends_on:
                continue
            if await row.locator(self.mapping.download).count() != 1:
                raise ValueError('Invoice original download control missing or ambiguous')
            source_id = 'oekostrom_' + hashlib.sha256(json.dumps(identity).encode()).hexdigest()
            records[source_id] = (i, identity, issued)
        snapshot = hashlib.sha256(json.dumps([query, sorted(records.items())]).encode()).hexdigest()
        offset = 0
        if checkpoint_id:
            prefix = f'cursor_{snapshot}_'
            if not checkpoint_id.startswith(prefix):
                raise ValueError('Checkpoint filters or portal snapshot changed')
            try:
                offset = int(checkpoint_id[len(prefix):])
            except ValueError:
                raise ValueError('Invalid checkpoint') from None
            if offset <= 0 or offset >= len(records) or offset % self.mapping.page_size:
                raise ValueError('Invalid checkpoint offset')
        self._records, self._query = records, query
        ids = sorted(records)[offset:offset + self.mapping.page_size]
        references = tuple(DocumentReference(
            source_id, DocumentKind.INVOICE, datetime.now(timezone.utc),
            (selected[records[source_id][1][0]],),
            (Observation(ObservationField.ISSUE_DATE, ObservationValueType.DATE,
                         records[source_id][2], ObservationSource.VENDOR_PORTAL,
                         self.mapping.date_attribute),),
        ) for source_id in ids)
        next_offset = offset + len(ids)
        terminal = next_offset >= len(records)
        return DiscoveryPage(references, None if terminal else f'cursor_{snapshot}_{next_offset}', terminal)

    async def fetch_document(self, context, reference):
        await self._prepare(context)
        if reference.source_document_id not in self._records:
            raise ValueError('Document must be rediscovered before fetching')
        interaction = await self._interaction(context)
        if interaction:
            return interaction
        index, identity, issued = self._records[reference.source_document_id]
        if reference.document_kind != DocumentKind.INVOICE or reference.scopes != (Scope(ScopeKind.INSTALLATION, identity[0]),):
            raise ValueError('Document reference scope/kind mismatch')
        row = self.page.locator(self.mapping.document_rows).nth(index)
        current = tuple([await row.get_attribute(attr) for attr in (
            self.mapping.scope_attribute, self.mapping.kind_attribute, self.mapping.native_id_attribute)])
        if current != identity or await row.get_attribute(self.mapping.date_attribute) != issued:
            raise ValueError('Document row changed since discovery')
        async with self.page.expect_download() as pending:
            await row.locator(self.mapping.download).click()
        download = await pending.value
        try:
            parsed = urlsplit(download.url)
            if f'{parsed.scheme}://{parsed.netloc}' != self.mapping.origin or self._network_failure:
                raise ValueError('Unapproved download origin')
            path = await download.path()
            if path is None or await download.failure():
                raise RuntimeError('Original download failed')
            path = Path(path)
            if path.stat().st_size > self.mapping.maximum_document_bytes:
                raise ValueError('Original exceeds download byte limit')
            content = path.read_bytes()
            if not content.startswith(b'%PDF-'):
                raise ValueError('Downloaded original is not a PDF')
            await self._prepare(context)
            return await context.publish_artifact(
                artifact_id=reference.source_document_id,
                filename=reference.source_document_id + '.pdf',
                media_type='application/pdf', content=content)
        finally:
            await download.delete()

    async def close(self):
        self._closed = True
        try:
            await self.page.context.close()
        finally:
            for resource in self.resources:
                try:
                    if hasattr(resource, 'stop'):
                        await resource.stop()
                    else:
                        await resource.close()
                except Exception:
                    pass


async def create_browser_connector(mapping: PortalMapping, credential_resolver=None):
    """Worker factory; engine worker extra owns the pinned Playwright dependency."""
    from playwright.async_api import async_playwright
    playwright = await async_playwright().start()
    browser = None
    try:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True, service_workers='block')
        context.set_default_timeout(15000)
        page = await context.new_page()
        return BrowserConnector(page, mapping, credential_resolver, resources=(browser, playwright))
    except BaseException:
        if browser:
            await browser.close()
        await playwright.stop()
        raise
