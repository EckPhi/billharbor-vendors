"""Ökostrom SDK v2 connector over the broker-owned ``browser-rpc/1`` capability.

The plugin never launches or imports a browser. Every page interaction goes
through ``await context.browser(operation, **arguments)``; the worker owns
browser initialization, HTTPS-only origin enforcement and redirect rejection.
The connector additionally only ever navigates to ``mapping.origin + path`` for
the two paths of a reviewed, data-only portal mapping profile.

No reviewed live Ökostrom profile exists. The packaged ``oekostrom-live``
placeholder is ``unreviewed`` and fails closed; mappings accept only invented
``.test`` HTTPS origins. Supplying a URL or other options cannot select a live
portal.
"""
from __future__ import annotations

import hashlib
import json
import re
import tomllib
from dataclasses import dataclass
from datetime import date, datetime, timezone
from importlib.resources import files
from types import MappingProxyType
from urllib.parse import urlsplit

from billharbor_sdk import (
    ConnectorCapabilities, DiscoveryPage, DocumentKind, DocumentReference,
    InteractionKind, InteractionRequest, Observation, ObservationField,
    ObservationSource, ObservationValueType, Scope, ScopeKind, SessionState,
)

from .identity import source_id as label_source_id

PROFILE_SCHEMA = "oekostrom-portal-mapping/1"
# Reviewed packaged profiles; ids are never interpreted as paths.
PROFILES = MappingProxyType({
    "synthetic-invented-portal": "synthetic-invented-portal.toml",
    "oekostrom-live": "oekostrom-live.toml",
})
MAXIMUM_ARTIFACT_BYTES = 20 * 1024 * 1024  # browser-rpc/1 wire bound
_TOP_KEYS = {"schema", "profile_id", "status", "origin", "login_path", "documents_path",
             "page_size", "maximum_rows", "maximum_document_bytes", "selectors", "attributes"}
_SELECTOR_KEYS = ("username", "password", "submit", "ready", "challenge", "scope_rows",
                  "document_rows", "designation", "download", "next_page")
_ATTRIBUTE_KEYS = ("installation", "issue_date", "kind")
_HOST = re.compile(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+")
_PATH = re.compile(r"/[A-Za-z0-9._~-]+(?:/[A-Za-z0-9._~-]+)*")
_ATTRIBUTE = re.compile(r"[A-Za-z_][A-Za-z0-9_.:-]{0,127}")
_SCRIPT_ENGINE = re.compile(r"(javascript|js)\s*=", re.I)
_SCOPE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,199}")


def _selector(value):
    if (type(value) is not str or not 1 <= len(value) <= 512 or ">>" in value
            or _SCRIPT_ENGINE.search(value) or any(ord(c) < 32 or ord(c) == 127 for c in value)):
        raise ValueError("Invalid portal mapping selector")
    return value


@dataclass(frozen=True)
class PortalMapping:
    """Validated invented portal mapping; never constructed from a live URL."""

    profile_id: str
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
    designation: str
    download: str
    next_page: str
    scope_attribute: str
    date_attribute: str
    kind_attribute: str
    page_size: int = 2
    maximum_rows: int = 1000
    maximum_document_bytes: int = MAXIMUM_ARTIFACT_BYTES

    def __post_init__(self):
        origin = self.origin
        parsed = urlsplit(origin) if type(origin) is str else None
        if (parsed is None or parsed.scheme != "https" or parsed.hostname is None
                or not _HOST.fullmatch(parsed.hostname) or origin != "https://" + parsed.hostname):
            raise ValueError("Mapping origin must be exactly https://<host> (port 443, no path)")
        if not parsed.hostname.endswith(".test"):
            raise ValueError("No live-reviewed Ökostrom mapping: invented .test origins only")
        for path in (self.login_path, self.documents_path):
            if type(path) is not str or not _PATH.fullmatch(path) or ".." in path.split("/"):
                raise ValueError("Mapping paths must be plain paths relative to the origin")
        for name in _SELECTOR_KEYS:
            _selector(getattr(self, name))
        for value in (self.scope_attribute, self.date_attribute, self.kind_attribute):
            if type(value) is not str or not _ATTRIBUTE.fullmatch(value):
                raise ValueError("Invalid portal mapping attribute")
        for value, low, high in ((self.page_size, 1, 100), (self.maximum_rows, 1, 10000),
                                 (self.maximum_document_bytes, 1, MAXIMUM_ARTIFACT_BYTES)):
            if type(value) is not int or not low <= value <= high:
                raise ValueError("Invalid portal mapping limits")

    def url(self, path):
        if path not in (self.login_path, self.documents_path):
            raise ValueError("Navigation outside the mapping is not permitted")
        return self.origin + path


def load_profile(profile_id):
    """Load a packaged profile by explicit id; unreviewed profiles fail closed."""
    if type(profile_id) is not str or profile_id not in PROFILES:
        raise ValueError("Unknown Ökostrom portal mapping profile")
    raw = files("oekostrom_at").joinpath("data/profiles/" + PROFILES[profile_id]).read_bytes()
    if len(raw) > 64 * 1024:
        raise ValueError("Portal mapping profile exceeds its bound")
    value = tomllib.loads(raw.decode("utf-8"))
    if (set(value) != _TOP_KEYS or value["schema"] != PROFILE_SCHEMA
            or value["profile_id"] != profile_id):
        raise ValueError("Invalid Ökostrom portal mapping profile")
    if value["status"] == "unreviewed":
        raise ValueError("Ökostrom portal mapping profile is unreviewed; failing closed")
    if value["status"] != "synthetic":
        raise ValueError("No reviewed live Ökostrom portal mapping is supported")
    selectors, attributes = value["selectors"], value["attributes"]
    if (type(selectors) is not dict or set(selectors) != set(_SELECTOR_KEYS)
            or type(attributes) is not dict or set(attributes) != set(_ATTRIBUTE_KEYS)):
        raise ValueError("Invalid Ökostrom portal mapping profile")
    return PortalMapping(
        profile_id, value["origin"], value["login_path"], value["documents_path"],
        **{name: selectors[name] for name in _SELECTOR_KEYS},
        scope_attribute=attributes["installation"], date_attribute=attributes["issue_date"],
        kind_attribute=attributes["kind"], page_size=value["page_size"],
        maximum_rows=value["maximum_rows"], maximum_document_bytes=value["maximum_document_bytes"])


class BrowserConnector:
    """SDK v2 connector driving only ``context.browser``; holds no credentials."""

    def __init__(self, mapping: PortalMapping, credential_resolver=None, *, offline_browser=None):
        if type(mapping) is not PortalMapping:
            raise TypeError("A validated portal mapping is required")
        self.mapping = mapping
        self.credential_resolver = credential_resolver
        self._offline_browser = offline_browser
        self._closed = False
        self._location = None
        self._records = {}
        self._query = None

    def capabilities(self):
        return ConnectorCapabilities("oekostrom_at", (DocumentKind.INVOICE,), ("browser",), True)

    def _ensure(self, context):
        if self._closed or context.cancelled() or datetime.now(timezone.utc) >= context.deadline:
            raise RuntimeError("Browser execution unavailable")

    async def _browser(self, context, operation, **arguments):
        self._ensure(context)
        capability = self._offline_browser or getattr(context, "browser", None)
        if capability is None:
            raise RuntimeError("Browser capability unavailable")
        return await capability(operation, **arguments)

    async def _count(self, context, selector):
        value = await self._browser(context, "count", selector=selector)
        if type(value) is not int or value < 0:
            raise RuntimeError("Invalid browser count")
        return value

    async def _attribute(self, context, selector, name):
        value = await self._browser(context, "attribute", selector=selector, name=name)
        if value is not None and type(value) is not str:
            raise RuntimeError("Invalid browser attribute")
        return value

    async def _text(self, context, selector):
        value = await self._browser(context, "text", selector=selector)
        if type(value) is not str:
            raise RuntimeError("Invalid browser text")
        return value

    async def _navigate(self, context, path):
        url = self.mapping.url(path)
        self._location = None
        await self._browser(context, "navigate", url=url)
        self._location = path

    async def _interaction(self, context):
        if await self._count(context, self.mapping.challenge):
            return InteractionRequest(InteractionKind.MFA, "oekostrom_manual_challenge", context.deadline)
        if not await self._count(context, self.mapping.ready):
            return InteractionRequest(InteractionKind.SESSION_EXPIRED, "oekostrom_session_expired", context.deadline)
        return None

    async def check_session(self, context):
        await self._navigate(context, self.mapping.login_path)
        if await self._count(context, self.mapping.challenge):
            return await self._interaction(context)
        if await self._count(context, self.mapping.ready):
            return SessionState.READY
        form = [await self._count(context, selector) for selector in (
            self.mapping.username, self.mapping.password, self.mapping.submit)]
        if self.credential_resolver is None or form != [1, 1, 1]:
            return InteractionRequest(InteractionKind.SESSION_EXPIRED, "oekostrom_manual_login", context.deadline)
        credentials = self.credential_resolver()
        try:
            if (type(credentials) is not dict or type(credentials.get("username")) is not str
                    or type(credentials.get("password")) is not str):
                raise ValueError("Credential bundle unavailable")
            await self._browser(context, "fill", selector=self.mapping.username, value=credentials["username"])
            await self._browser(context, "fill", selector=self.mapping.password, value=credentials["password"])
        finally:
            del credentials
        self._location = None
        await self._browser(context, "click", selector=self.mapping.submit)
        return await self._interaction(context) or SessionState.READY

    async def _open_documents(self, context):
        await self._navigate(context, self.mapping.documents_path)
        return await self._interaction(context)

    async def _scopes_on_page(self, context):
        rows = self.mapping.scope_rows
        count = await self._count(context, rows)
        if not 1 <= count <= self.mapping.maximum_rows:
            raise ValueError("Scope list exceeds bounds or is empty")
        scopes = []
        for index in range(count):
            identifier = await self._attribute(context, f"{rows} >> nth={index}", self.mapping.scope_attribute)
            if identifier is None or not _SCOPE_ID.fullmatch(identifier):
                raise ValueError("Missing or invalid installation identity")
            scopes.append(Scope(ScopeKind.INSTALLATION, identifier))
        if len(set(scopes)) != len(scopes):
            raise ValueError("Duplicate installation identity")
        return tuple(scopes)

    async def list_scopes(self, context):
        interaction = await self._open_documents(context)
        if interaction:
            # SDK list_scopes cannot return an InteractionRequest.
            raise RuntimeError(interaction.safe_message_code)
        return await self._scopes_on_page(context)

    async def _row_identity(self, context, row):
        scope_id = await self._attribute(context, row, self.mapping.scope_attribute)
        kind = await self._attribute(context, row, self.mapping.kind_attribute)
        return scope_id, kind

    async def _designation(self, context, row):
        label = f"{row} >> {self.mapping.designation}"
        if await self._count(context, label) != 1:
            raise ValueError("Bezeichnung missing or ambiguous")
        return await self._text(context, label)

    async def discover_page(self, context, *, starts_on: date, ends_on: date,
                            scopes: tuple[Scope, ...], checkpoint_id: str | None):
        self._ensure(context)
        if (starts_on > ends_on or not scopes or len(set(scopes)) != len(scopes)
                or any(scope.kind != ScopeKind.INSTALLATION for scope in scopes)):
            raise ValueError("Invalid discovery scope/date window")
        query = json.dumps([starts_on.isoformat(), ends_on.isoformat(),
                            sorted((s.kind.value, s.id) for s in scopes)])
        interaction = await self._open_documents(context)
        if interaction:
            return interaction
        if not set(scopes) <= set(await self._scopes_on_page(context)):
            raise ValueError("Unknown installation")
        # Only complete combined-view snapshots are supported. Never silently
        # report terminal when a portal adds pagination.
        if await self._count(context, self.mapping.next_page):
            raise RuntimeError("Unreviewed portal pagination")
        count = await self._count(context, self.mapping.document_rows)
        if count > self.mapping.maximum_rows:
            raise ValueError("Document list exceeds configured bound")
        selected = {s.id: s for s in scopes}
        records, seen = {}, set()
        for index in range(count):
            row = f"{self.mapping.document_rows} >> nth={index}"
            scope_id, kind = await self._row_identity(context, row)
            if scope_id not in selected:
                continue
            if kind != "invoice":
                continue  # Deposits, credit notes, settlements and PV are unsupported; never fetched.
            native = await self._designation(context, row)
            if not native or not native.strip() or len(native) > 2000:
                raise ValueError("Missing exact Bezeichnung identity")
            identity = (scope_id, kind, native)
            if identity in seen:
                raise ValueError("Duplicate document identity in snapshot")
            seen.add(identity)
            issued = await self._attribute(context, row, self.mapping.date_attribute)
            try:
                issued_on = date.fromisoformat(issued)
            except (TypeError, ValueError):
                raise ValueError("Missing or invalid issue date") from None
            if issued_on.isoformat() != issued:
                raise ValueError("Missing or invalid issue date")
            if not starts_on <= issued_on <= ends_on:
                continue
            if await self._count(context, f"{row} >> {self.mapping.download}") != 1:
                raise ValueError("Invoice original download control missing or ambiguous")
            source_id = label_source_id("installation", scope_id, kind, native)
            records[source_id] = (index, identity, issued)
        snapshot = hashlib.sha256(json.dumps([query, sorted(records.items())]).encode()).hexdigest()
        offset = 0
        if checkpoint_id:
            prefix = f"cursor_{snapshot}_"
            if type(checkpoint_id) is not str or not checkpoint_id.startswith(prefix):
                raise ValueError("Checkpoint filters or portal snapshot changed")
            try:
                offset = int(checkpoint_id[len(prefix):])
            except ValueError:
                raise ValueError("Invalid checkpoint") from None
            if (checkpoint_id != prefix + str(offset) or offset <= 0 or offset >= len(records)
                    or offset % self.mapping.page_size):
                raise ValueError("Invalid checkpoint offset")
        self._records, self._query = records, query
        ids = sorted(records)[offset:offset + self.mapping.page_size]
        observed = datetime.now(timezone.utc)
        references = tuple(DocumentReference(
            source_id, DocumentKind.INVOICE, observed,
            (selected[records[source_id][1][0]],),
            (Observation(ObservationField.ISSUE_DATE, ObservationValueType.DATE,
                         records[source_id][2], ObservationSource.VENDOR_PORTAL,
                         self.mapping.date_attribute),),
        ) for source_id in ids)
        next_offset = offset + len(ids)
        terminal = next_offset >= len(records)
        return DiscoveryPage(references, None if terminal else f"cursor_{snapshot}_{next_offset}", terminal)

    async def fetch_document(self, context, reference):
        self._ensure(context)
        if reference.source_document_id not in self._records:
            raise ValueError("Document must be rediscovered before fetching")
        index, identity, issued = self._records[reference.source_document_id]
        if (reference.document_kind != DocumentKind.INVOICE
                or reference.scopes != (Scope(ScopeKind.INSTALLATION, identity[0]),)):
            raise ValueError("Document reference scope/kind mismatch")
        if self._location != self.mapping.documents_path:
            await self._navigate(context, self.mapping.documents_path)
        interaction = await self._interaction(context)
        if interaction:
            return interaction
        row = f"{self.mapping.document_rows} >> nth={index}"
        if await self._count(context, row) != 1:
            raise ValueError("Document row changed since discovery")
        current = await self._row_identity(context, row) + (await self._designation(context, row),)
        if current != identity or await self._attribute(context, row, self.mapping.date_attribute) != issued:
            raise ValueError("Document row changed since discovery")
        control = f"{row} >> {self.mapping.download}"
        if await self._count(context, control) != 1:
            raise ValueError("Invoice original download control missing or ambiguous")
        content = await self._browser(context, "download", selector=control)
        if type(content) is not bytes:
            raise RuntimeError("Original download failed")
        if len(content) > self.mapping.maximum_document_bytes:
            raise ValueError("Original exceeds download byte limit")
        if not content.startswith(b"%PDF-"):
            raise ValueError("Downloaded original is not a PDF")
        self._ensure(context)
        return await context.publish_artifact(
            artifact_id=reference.source_document_id,
            filename=reference.source_document_id + ".pdf",
            media_type="application/pdf", content=content)

    async def close(self):
        # The broker owns and disposes the browser; drop discovery state only.
        self._closed = True
        self._records = {}
        self._offline_browser = None


async def create_connector(options, resolver):
    """Plugin factory (``oekostrom_at.connector:create_connector`` in the wheel).

    Exactly one explicit mode is required:

    * ``{"offline_fixture": true}`` — offline, credential-free conformance over
      the packaged invented DOM. The resolver is discarded and never called.
    * ``{"portal_profile": "synthetic-invented-portal"}`` — drive the
      worker-supplied ``context.browser`` capability with that packaged profile.
      ``"oekostrom-live"`` is unreviewed and fails closed.
    """
    if type(options) is not dict or set(options) not in ({"offline_fixture"}, {"portal_profile"}):
        raise ValueError("Ökostrom plugin requires exactly one explicit mode option")
    if "offline_fixture" in options:
        if options["offline_fixture"] is not True:
            raise ValueError("Invalid offline fixture option")
        from .offline import InventedPortal, load_fixture
        fixture = load_fixture()
        mapping = load_profile(fixture["profile_id"])
        return BrowserConnector(mapping, None, offline_browser=InventedPortal(fixture, mapping.origin))
    return BrowserConnector(load_profile(options["portal_profile"]), resolver)
