"""Invented portal only. These tests establish no real vendor compatibility.

The connector is exercised through an in-process fake of the broker-owned
``browser-rpc/1`` capability; no browser, network or credential is used.
"""
import ast
import asyncio
import copy
import hashlib
import subprocess
import sys
import tomllib
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from billharbor_sdk import (
    ArtifactPublication, DocumentKind, InteractionKind, InteractionRequest, Scope,
    ScopeKind, SessionState,
)
from billharbor_sdk.validation import validate_object
import oekostrom_at.browser as browser_module
from oekostrom_at.browser import BrowserConnector, create_connector, load_profile
from oekostrom_at.identity import source_id
from oekostrom_at.offline import InventedPortal, load_fixture

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "vendors/oekostrom_at/src/oekostrom_at"
ORIGIN = "https://portal.oekostrom-invented.test"
USER, SECRET = "invented-user-17", "invented-secret-never-logged"
NORD, SUED = (Scope(ScopeKind.INSTALLATION, "anlage-invented-nord"),
              Scope(ScopeKind.INSTALLATION, "anlage-invented-sued"))
YEAR = dict(starts_on=date(2026, 1, 1), ends_on=date(2026, 12, 31))


class Context:
    def __init__(self, browser=None):
        self.deadline = datetime.now(timezone.utc) + timedelta(minutes=5)
        self.published = {}
        if browser is not None:
            self.browser = browser

    def cancelled(self):
        return False

    async def consume_request(self):
        return None

    async def emit_safe_event(self, code, **counters):
        return None

    async def publish_artifact(self, *, artifact_id, filename, media_type, content):
        self.published[artifact_id] = bytes(content)
        return ArtifactPublication(artifact_id, filename, media_type, len(content),
                                   hashlib.sha256(content).hexdigest())


def portal(*, signed_in=True):
    value = InventedPortal(load_fixture(), ORIGIN, credentials=(USER, SECRET))
    value.authenticated = signed_in
    return value


def connector(resolver=None, mapping=None):
    return BrowserConnector(mapping or load_profile("synthetic-invented-portal"), resolver)


def resolver_for(calls):
    def resolve():
        calls.append(1)
        return {"username": USER, "password": SECRET}
    return resolve


async def discover_all(subject, context, scopes=(NORD, SUED), **window):
    window = window or YEAR
    references, checkpoint = [], None
    for _ in range(50):
        page = await subject.discover_page(context, scopes=scopes, checkpoint_id=checkpoint, **window)
        assert not isinstance(page, InteractionRequest)
        references.extend(page.documents)
        if page.terminal:
            assert page.checkpoint_id is None
            return references
        checkpoint = page.checkpoint_id
    raise AssertionError("pagination did not terminate")


def invoice_ids(*rows):
    return {source_id("installation", scope, "invoice", label) for scope, label in rows}


# Profiles and mapping -------------------------------------------------------

def test_synthetic_profile_is_exact_invented_https_origin():
    mapping = load_profile("synthetic-invented-portal")
    assert mapping.origin == ORIGIN and mapping.profile_id == "synthetic-invented-portal"
    assert mapping.url(mapping.login_path) == ORIGIN + "/anmelden"
    assert mapping.url(mapping.documents_path) == ORIGIN + "/rechnungen"
    with pytest.raises(ValueError, match="outside the mapping"):
        mapping.url("/other")


def test_unreviewed_live_profile_and_unknown_ids_fail_closed():
    with pytest.raises(ValueError, match="unreviewed"):
        load_profile("oekostrom-live")
    for value in ("unknown", "../profiles/oekostrom-live", "synthetic-invented-portal.toml",
                  "https://mein.oekostrom.at", None, 1):
        with pytest.raises(ValueError, match="Unknown"):
            load_profile(value)
    live = tomllib.loads((PACKAGE / "data/profiles/oekostrom-live.toml").read_text())
    assert live["status"] == "unreviewed" and live["origin"] == ""
    assert not any(live["selectors"].values()) and not any(live["attributes"].values())

    async def factories():
        for options in ({"portal_profile": "oekostrom-live"}, {"portal_profile": "https://mein.oekostrom.at"},
                        {"origin": "https://mein.oekostrom.at"}, {}, {"offline_fixture": False},
                        {"offline_fixture": True, "portal_profile": "synthetic-invented-portal"},
                        {"portal_profile": "synthetic-invented-portal", "origin": ORIGIN}):
            with pytest.raises(ValueError):
                await create_connector(options, lambda: pytest.fail("credentials resolved"))
    asyncio.run(factories())


@pytest.mark.parametrize("origin", [
    "https://mein.oekostrom.at", "https://oekostrom.at", "http://portal.oekostrom-invented.test",
    "https://portal.oekostrom-invented.test:443", "https://portal.oekostrom-invented.test:8443",
    "https://portal.oekostrom-invented.test/", "https://portal.oekostrom-invented.test/path",
    "https://user@portal.oekostrom-invented.test", "https://portal.oekostrom-invented.test?x=1",
    "https://127.0.0.1", "https://PORTAL.oekostrom-invented.test", "https://test",
])
def test_mapping_rejects_live_and_noncanonical_origins(origin):
    with pytest.raises(ValueError):
        replace(load_profile("synthetic-invented-portal"), origin=origin)


@pytest.mark.parametrize("field, value", [
    ("login_path", "//evil.test/x"), ("login_path", "relative"), ("documents_path", "/a/../b"),
    ("documents_path", "/a?b=1"), ("ready", "js=document.body"), ("ready", "#a >> javascript=1"),
    ("download", "a >> nth=0"), ("next_page", ""), ("kind_attribute", "on click"),
    ("page_size", 0), ("page_size", 101), ("maximum_document_bytes", 20 * 1024 * 1024 + 1),
])
def test_mapping_rejects_unsafe_fields(field, value):
    with pytest.raises(ValueError):
        replace(load_profile("synthetic-invented-portal"), **{field: value})


@pytest.mark.parametrize("change", ["status_reviewed", "live_host", "extra_key", "missing_selector",
                                    "wrong_id", "wrong_schema"])
def test_tampered_packaged_profile_fails_closed(change, tmp_path, monkeypatch):
    profile = tomllib.loads((PACKAGE / "data/profiles/synthetic-invented-portal.toml").read_text())
    if change == "status_reviewed":
        profile["status"] = "reviewed"
    elif change == "live_host":
        profile["origin"] = "https://mein.oekostrom.at"
    elif change == "extra_key":
        profile["origin_override"] = ORIGIN
    elif change == "missing_selector":
        del profile["selectors"]["ready"]
    elif change == "wrong_id":
        profile["profile_id"] = "oekostrom-live"
    else:
        profile["schema"] = "oekostrom-portal-mapping/2"
    lines = [f'{key} = "{item}"' if isinstance(item, str) else f"{key} = {item}"
             for key, item in profile.items() if not isinstance(item, dict)]
    for key, item in profile.items():
        if isinstance(item, dict):
            lines.append(f"[{key}]")
            lines.extend(f"{name} = '{text}'" for name, text in item.items())
    target = tmp_path / "data/profiles"
    target.mkdir(parents=True)
    (target / "synthetic-invented-portal.toml").write_text("\n".join(lines))
    monkeypatch.setattr(browser_module, "files", lambda package: tmp_path)
    with pytest.raises(ValueError):
        load_profile("synthetic-invented-portal")


# Session handling ------------------------------------------------------------

def test_login_uses_resolver_only_when_form_present_and_keeps_no_credentials():
    async def run():
        calls = []
        site = portal(signed_in=False)
        subject = connector(resolver_for(calls))
        context = Context(site)
        assert await subject.check_session(context) is SessionState.READY
        assert calls == [1] and site.authenticated
        # A ready session never resolves credentials again.
        assert await subject.check_session(context) is SessionState.READY
        assert calls == [1]
        assert SECRET not in repr(vars(subject)) and USER not in repr(vars(subject))
        assert all(SECRET not in repr(entry) for entry in site.operations)
    asyncio.run(run())


def test_login_failure_challenge_and_missing_ready_marker():
    async def run():
        wrong = portal(signed_in=False)
        wrong.credentials = ("someone", "else")
        result = await connector(resolver_for([])).check_session(Context(wrong))
        assert result.kind is InteractionKind.SESSION_EXPIRED
        assert result.safe_message_code == "oekostrom_session_expired"

        calls = []
        manual = await connector(None).check_session(Context(portal(signed_in=False)))
        assert manual.safe_message_code == "oekostrom_manual_login" and calls == []

        challenged = portal(signed_in=False)
        challenged.challenge_after_sign_in = True
        result = await connector(resolver_for(calls)).check_session(Context(challenged))
        assert result.kind is InteractionKind.MFA
        assert result.safe_message_code == "oekostrom_manual_challenge"

        pending = portal()
        pending.challenge = True
        calls.clear()
        result = await connector(resolver_for(calls)).check_session(Context(pending))
        assert result.kind is InteractionKind.MFA and calls == []
        page = await connector().discover_page(Context(pending), scopes=(NORD,), checkpoint_id=None, **YEAR)
        assert page.safe_message_code == "oekostrom_manual_challenge"

        expired = portal(signed_in=False)
        page = await connector().discover_page(Context(expired), scopes=(NORD,), checkpoint_id=None, **YEAR)
        assert page.kind is InteractionKind.SESSION_EXPIRED
        with pytest.raises(RuntimeError, match="^oekostrom_session_expired$"):
            await connector().list_scopes(Context(expired))
    asyncio.run(run())


def test_credentials_never_appear_in_error_messages():
    class FailingFill:
        def __init__(self, inner):
            self.inner = inner

        async def __call__(self, operation, **arguments):
            if operation == "fill" and arguments.get("value") == SECRET:
                raise RuntimeError("Browser operation failed.")
            return await self.inner(operation, **arguments)

    async def run():
        failures = []
        for browser, resolve in (
                (FailingFill(portal(signed_in=False)), lambda: {"username": USER, "password": SECRET}),
                (portal(signed_in=False), lambda: {"username": SECRET, "password": 5}),
                (portal(signed_in=False), lambda: [SECRET])):
            with pytest.raises(Exception) as caught:
                await connector(resolve).check_session(Context(browser))
            failures.append(caught.value)
        for failure in failures:
            chain = [failure, failure.__cause__, failure.__context__]
            assert all(SECRET not in str(item) and SECRET not in repr(item) for item in chain if item)
            assert USER not in str(failure)
    asyncio.run(run())


# Discovery -------------------------------------------------------------------

def test_multi_installation_combined_view_with_inclusive_date_ends():
    async def run():
        context = Context(portal())
        subject = connector()
        assert await subject.list_scopes(context) == (NORD, SUED)
        found = await discover_all(subject, context, starts_on=date(2026, 2, 20), ends_on=date(2026, 5, 2))
        assert {item.source_document_id for item in found} == invoice_ids(
            ("anlage-invented-sued", "Invented Rechnung Februar 2026 Anlage Sued"),
            ("anlage-invented-nord", "Invented Rechnung Maerz 2026 Anlage Nord"),
            ("anlage-invented-sued", "Invented Rechnung Mai 2026 Anlage Sued"))
        assert all(item.document_kind is DocumentKind.INVOICE and len(item.scopes) == 1 for item in found)
        assert {item.observations[0].value for item in found} == {"2026-02-20", "2026-03-31", "2026-05-02"}
        # Moving either end by one day drops the boundary document.
        narrower = await discover_all(subject, context, starts_on=date(2026, 2, 21), ends_on=date(2026, 5, 1))
        assert len(narrower) == 1
        nord = await discover_all(subject, context, scopes=(NORD,))
        assert {item.scopes for item in nord} == {(NORD,)} and len(nord) == 3
    asyncio.run(run())


def test_terminal_empty_range_and_invalid_windows():
    async def run():
        context = Context(portal())
        page = await connector().discover_page(context, scopes=(NORD, SUED), checkpoint_id=None,
                                               starts_on=date(2026, 7, 1), ends_on=date(2026, 7, 31))
        assert page.terminal and page.documents == () and page.checkpoint_id is None
        for scopes, window in (((NORD,), dict(starts_on=date(2026, 2, 1), ends_on=date(2026, 1, 1))),
                               ((), YEAR), ((NORD, NORD), YEAR),
                               ((Scope(ScopeKind.CONTRACT, "anlage-invented-nord"),), YEAR)):
            with pytest.raises(ValueError, match="Invalid discovery"):
                await connector().discover_page(context, scopes=scopes, checkpoint_id=None, **window)
    asyncio.run(run())


def test_checkpoint_continuation_restart_and_filter_change_rejection():
    async def run():
        context = Context(portal())
        first = await connector().discover_page(context, scopes=(NORD, SUED), checkpoint_id=None, **YEAR)
        assert not first.terminal and len(first.documents) == 2
        # A new connector (process restart) continues from an unchanged snapshot.
        second = await connector().discover_page(Context(portal()), scopes=(NORD, SUED),
                                                 checkpoint_id=first.checkpoint_id, **YEAR)
        assert len(second.documents) == 2
        assert not ({d.source_document_id for d in first.documents}
                    & {d.source_document_id for d in second.documents})
        with pytest.raises(ValueError, match="filters or portal snapshot"):
            await connector().discover_page(context, scopes=(NORD,), checkpoint_id=first.checkpoint_id, **YEAR)
        with pytest.raises(ValueError, match="filters or portal snapshot"):
            await connector().discover_page(context, scopes=(NORD, SUED), checkpoint_id=first.checkpoint_id,
                                            starts_on=date(2026, 1, 2), ends_on=date(2026, 12, 31))
        prefix = first.checkpoint_id.rsplit("_", 1)[0] + "_"
        for bad in (prefix + "x", prefix + "1", prefix + "0", prefix + "02", prefix + "100"):
            with pytest.raises(ValueError):
                await connector().discover_page(context, scopes=(NORD, SUED), checkpoint_id=bad, **YEAR)
        # A newly appearing in-range invoice changes the snapshot.
        changed = portal()
        late = copy.deepcopy(changed.rows()[0])
        late["children"][0]["text"] = "Invented late invoice"
        changed.view_root()["children"][1]["children"].append(late)
        with pytest.raises(ValueError, match="filters or portal snapshot"):
            await connector().discover_page(Context(changed), scopes=(NORD, SUED),
                                            checkpoint_id=first.checkpoint_id, **YEAR)
    asyncio.run(run())


def test_duplicate_identity_rejected_before_date_filtering():
    async def run():
        site = portal()
        duplicate = copy.deepcopy(site.rows()[0])
        duplicate["attributes"]["data-issued"] = "2030-01-01"  # Outside the tested window.
        site.view_root()["children"][1]["children"].append(duplicate)
        with pytest.raises(ValueError, match="Duplicate document identity"):
            await connector().discover_page(Context(site), scopes=(NORD,), checkpoint_id=None,
                                            starts_on=date(2026, 6, 1), ends_on=date(2026, 6, 30))
        twin = portal()
        installations = twin.view_root()["children"][0]["children"]
        installations.append(copy.deepcopy(installations[0]))
        with pytest.raises(ValueError, match="Duplicate installation"):
            await connector().list_scopes(Context(twin))
    asyncio.run(run())


def test_unknown_installation_and_unexpected_pagination_control():
    async def run():
        with pytest.raises(ValueError, match="Unknown installation"):
            await connector().discover_page(Context(portal()), checkpoint_id=None, **YEAR,
                                            scopes=(Scope(ScopeKind.INSTALLATION, "anlage-invented-west"),))
        site = portal()
        site.view_root()["children"].append({"tag": "button", "attributes": {"class": "invented-next-page"},
                                             "text": "Mehr", "children": []})
        with pytest.raises(RuntimeError, match="pagination"):
            await connector().discover_page(Context(site), scopes=(NORD,), checkpoint_id=None, **YEAR)
        assert site.downloads == []
    asyncio.run(run())


def test_malformed_rows_fail_closed():
    async def run():
        for mutate, message in (
                (lambda row: row["children"].pop(0), "Bezeichnung"),
                (lambda row: row["children"].append(copy.deepcopy(row["children"][0])), "Bezeichnung"),
                (lambda row: row["children"][0].update(text="   "), "Bezeichnung identity"),
                (lambda row: row["attributes"].update({"data-issued": "15.01.2026"}), "issue date"),
                (lambda row: row["attributes"].pop("data-issued"), "issue date"),
                (lambda row: row["children"][1]["children"].clear(), "download control")):
            site = portal()
            mutate(site.rows()[0])
            with pytest.raises(ValueError, match=message):
                await connector().discover_page(Context(site), scopes=(NORD,), checkpoint_id=None, **YEAR)
    asyncio.run(run())


# Fetch -----------------------------------------------------------------------

def test_invoice_only_lifecycle_never_reads_or_downloads_excluded_rows():
    async def run():
        site = portal()
        context = Context(site)
        subject = connector()
        checkpoint = None
        while True:
            page = await subject.discover_page(context, scopes=(NORD, SUED), checkpoint_id=checkpoint, **YEAR)
            for reference in page.documents:
                publication = await subject.fetch_document(context, reference)
                assert publication.media_type == "application/pdf"
            if page.terminal:
                break
            checkpoint = page.checkpoint_id
        assert len(context.published) == 5
        assert sorted(site.downloads) == sorted(key for key in site.originals if key.startswith("invoice-"))
        kinds = [row["attributes"]["data-kind"] for row in site.rows()]
        assert set(kinds) >= {"deposit", "credit_note", "settlement", "pv_settlement"}
        excluded = [index for index, kind in enumerate(kinds) if kind != "invoice"]
        touched = [selector for operation, selector in site.operations
                   if operation in {"text", "download"} or "invented-designation" in str(selector)]
        assert touched and not any(f"nth={index} " in selector for index in excluded for selector in touched)
        assert all(content.startswith(b"%PDF-") for content in context.published.values())
    asyncio.run(run())


def test_fetch_requires_rediscovery_and_unchanged_row():
    async def run():
        site = portal()
        context = Context(site)
        subject = connector()
        page = await subject.discover_page(context, scopes=(NORD,), checkpoint_id=None, **YEAR)
        reference = page.documents[0]
        with pytest.raises(ValueError, match="rediscovered"):
            await connector().fetch_document(context, reference)
        with pytest.raises(ValueError, match="scope/kind"):
            await subject.fetch_document(context, replace(reference, document_kind=DocumentKind.CREDIT_NOTE))
        with pytest.raises(ValueError, match="scope/kind"):
            await subject.fetch_document(context, replace(reference, scopes=(SUED,)))
        index = subject._records[reference.source_document_id][0]
        row = site.rows()[index]
        label = row["children"][0]
        original = label["text"]
        label["text"] = original + " renamed"
        with pytest.raises(ValueError, match="row changed"):
            await subject.fetch_document(context, reference)
        label["text"] = original
        row["attributes"]["data-issued"] = "2026-12-30"
        with pytest.raises(ValueError, match="row changed"):
            await subject.fetch_document(context, reference)
        row["attributes"]["data-issued"] = reference.observations[0].value
        row["attributes"]["data-kind"] = "credit_note"
        with pytest.raises(ValueError, match="row changed"):
            await subject.fetch_document(context, reference)
        assert site.downloads == []
        row["attributes"]["data-kind"] = "invoice"
        assert (await subject.fetch_document(context, reference)).byte_size > 0
        # A removed row cannot be matched by index either.
        site.view_root()["children"][1]["children"].clear()
        with pytest.raises(ValueError, match="row changed"):
            await subject.fetch_document(context, reference)
    asyncio.run(run())


def test_non_pdf_and_oversized_originals_are_rejected_on_returned_bytes():
    async def run():
        site = portal()
        for key in site.originals:
            site.originals[key] = b"<html>Invented error page</html>"
        context = Context(site)
        subject = connector()
        page = await subject.discover_page(context, scopes=(NORD,), checkpoint_id=None, **YEAR)
        with pytest.raises(ValueError, match="not a PDF"):
            await subject.fetch_document(context, page.documents[0])
        site = portal()
        context = Context(site)
        small = connector(mapping=replace(load_profile("synthetic-invented-portal"), maximum_document_bytes=16))
        page = await small.discover_page(context, scopes=(NORD,), checkpoint_id=None, **YEAR)
        with pytest.raises(ValueError, match="byte limit"):
            await small.fetch_document(context, page.documents[0])
        assert context.published == {} and len(site.downloads) == 1
    asyncio.run(run())


def test_navigation_never_leaves_the_mapping_origin():
    async def run():
        site = portal(signed_in=False)
        context = Context(site)
        subject = connector(resolver_for([]))
        assert await subject.check_session(context) is SessionState.READY
        page = await subject.discover_page(context, scopes=(NORD, SUED), checkpoint_id=None, **YEAR)
        for reference in page.documents:
            await subject.fetch_document(context, reference)
        await subject.list_scopes(context)
        assert site.navigations
        assert set(site.navigations) <= {ORIGIN + "/anmelden", ORIGIN + "/rechnungen"}
        assert {operation for operation, _ in site.operations} <= {
            "navigate", "fill", "click", "text", "attribute", "count", "download"}
    asyncio.run(run())


def test_browser_failure_is_terminal_and_closed_connector_refuses_work():
    async def run():
        site = portal()
        site.failed = True
        subject = connector()
        with pytest.raises(RuntimeError, match="Browser operation failed"):
            await subject.list_scopes(Context(site))
        await subject.close()
        with pytest.raises(RuntimeError, match="unavailable"):
            await subject.check_session(Context(portal()))
    asyncio.run(run())


def test_offline_portal_models_strict_single_element_operations():
    async def run():
        site = portal()
        await site("navigate", url=ORIGIN + "/rechnungen")
        assert await site("count", selector="tr.invented-document") == 9
        assert await site("attribute", selector="tr.invented-document >> nth=1", name="data-kind") == "deposit"
        with pytest.raises(RuntimeError):
            await site("text", selector="tr.invented-document")  # Strict: nine matches.
        with pytest.raises(RuntimeError):
            await site("count", selector="tr")  # Any failure is terminal, like the broker.
        for url in ("https://mein.oekostrom.at/rechnungen", ORIGIN + "/redirect",
                    "http://portal.oekostrom-invented.test/rechnungen"):
            with pytest.raises(RuntimeError):
                await portal()("navigate", url=url)
        with pytest.raises(RuntimeError):
            await portal()("count", selector="js=document")
    asyncio.run(run())


# Factory and packaging -------------------------------------------------------

def test_offline_factory_passes_conformance_shape_without_browser_or_credentials():
    """Mirrors the application's offline Registry conformance loop."""
    async def run():
        subject = await create_connector({"offline_fixture": True},
                                         lambda: pytest.fail("conformance resolved credentials"))
        context = Context()  # Conformance contexts have no browser capability.
        assert subject.capabilities().connector_id == "oekostrom_at"
        assert subject.credential_resolver is None
        assert await subject.check_session(context) is SessionState.READY
        scopes = await subject.list_scopes(context)
        assert scopes and len(scopes) <= 100
        checkpoint, documents = None, 0
        for _ in range(20):
            page = await subject.discover_page(context, starts_on=date(2000, 1, 1), ends_on=date(2100, 1, 1),
                                               scopes=scopes, checkpoint_id=checkpoint)
            for reference in page.documents:
                documents += 1
                await subject.fetch_document(context, reference)
            if page.terminal:
                break
            assert page.checkpoint_id and page.checkpoint_id != checkpoint
            checkpoint = page.checkpoint_id
        else:
            raise AssertionError("page bound")
        assert documents == len(context.published) == 5
        await subject.close()

        live = await create_connector({"portal_profile": "synthetic-invented-portal"}, lambda: None)
        with pytest.raises(RuntimeError, match="capability unavailable"):
            await live.check_session(Context())
    asyncio.run(run())


def test_plugin_never_imports_or_launches_playwright():
    forbidden = {"playwright", "billharbor_vendors", "billharbor_synthetic", "billharbor", "subprocess", "socket"}
    for path in PACKAGE.rglob("*.py"):
        if path.name == "connector.py":
            continue  # Legacy aggregate fixture connector; not shipped in the plugin wheel.
        for node in ast.walk(ast.parse(path.read_text())):
            names = ([alias.name for alias in node.names] if isinstance(node, ast.Import)
                     else [node.module or ""] if isinstance(node, ast.ImportFrom) and not node.level else [])
            assert not any(name.split(".")[0] in forbidden for name in names), path
        assert "chromium" not in path.read_text().lower()
    sdk = ROOT.parent / "billharbor/packages/connector-sdk/src"
    code = f"""
import asyncio, sys
sys.path.insert(0, {str(PACKAGE.parent)!r})
sys.path.insert(1, {str(sdk)!r})
from oekostrom_at.browser import create_connector
async def main():
    connector = await create_connector({{"offline_fixture": True}}, lambda: None)
    await connector.close()
asyncio.run(main())
assert "playwright" not in sys.modules
assert not any(name.startswith(("billharbor_vendors", "billharbor_synthetic")) for name in sys.modules)
"""
    subprocess.run([sys.executable, "-I", "-c", code], check=True)


def test_synthetic_manifest_satisfies_browser_live_eligibility():
    """Mirrors billharbor.browser_policy live installation checks."""
    manifest = tomllib.loads((ROOT / "vendors/oekostrom_at/browser-synthetic.toml").read_text())
    validate_object(manifest)
    mapping = load_profile("synthetic-invented-portal")
    assert manifest["status"] in {"synthetic_verified", "account_verified"}
    assert manifest["entrypoint"] == "oekostrom_at.connector:create_connector"
    assert manifest["transport"]["preferred"] == "browser" and manifest["transport"]["supported"] == ["browser"]
    network = manifest["network"]
    assert network["origins"] == [ORIGIN] and network["redirect_origins"] == [ORIGIN]
    assert not network.get("unresolved")
    assert set(network["origins"]) | set(network["redirect_origins"]) == {mapping.origin}
    assert all(origin.endswith(".test") and "/" not in origin[8:] and ":" not in origin[8:]
               for origin in network["origins"])
    assert manifest["coverage"]["document_kinds"] == ["invoice"]
    assert {"deposit", "credit_note", "settlement", "PV"} <= {
        word for text in manifest["coverage"]["known_exclusions"] for word in text.split()}
    capabilities = connector().capabilities()
    assert {kind.value for kind in capabilities.document_kinds} <= set(manifest["coverage"]["document_kinds"])
    assert capabilities.transports == ("browser",)
    assert bool(manifest["authentication"]["manual_challenges"]) is capabilities.supports_interaction
    assert mapping.page_size <= manifest["limits"]["maximum_documents_per_page"]
    assert mapping.maximum_document_bytes <= manifest["limits"]["maximum_document_bytes"]
    assert manifest["verification"]["live_verified"] is False

    real = tomllib.loads((ROOT / "vendors/oekostrom_at/vendor.toml").read_text())
    validate_object(real)
    assert real["status"] == "design_only" and real["network"]["origins"] == []
    assert real["coverage"]["document_kinds"] == ["invoice"]
    assert real["entrypoint"] == "oekostrom_at.connector:Connector"


def test_runs_through_durable_engine_with_browser_capability(tmp_path):
    """Invented account proof across the real runner and outbox boundaries."""
    from billharbor.engine.runner import RunnerConfig, RunnerContext, run_connector
    from billharbor.engine.store import DurableStore

    manifest = tomllib.loads((ROOT / "vendors/oekostrom_at/browser-synthetic.toml").read_text())
    # The in-process runner's synthetic mode only admits design_only manifests;
    # synthetic_verified execution requires the application's live-validation
    # grant path. This test-local copy exercises the runner/outbox only.
    manifest["status"] = "design_only"
    store = DurableStore(tmp_path / "state.db", tmp_path / "artifacts")
    store.create_execution("synthetic_tenant", "run", "key", {})
    lease = store.claim_execution("synthetic_tenant", "run", lease_for=timedelta(minutes=5))
    config = RunnerConfig("synthetic_tenant", "synthetic_account", "synthetic_destination", 1,
                          manifest, date(2026, 1, 1), date(2026, 12, 31), document_kinds=("invoice",),
                          selected_scopes=(("installation", NORD.id), ("installation", SUED.id)))
    site = portal(signed_in=False)

    async def run():
        context = RunnerContext(datetime.now(timezone.utc) + timedelta(minutes=3))
        context.browser = site
        return await run_connector(store, lease, connector(lambda: {"username": USER, "password": SECRET}),
                                   context, config)

    deliveries = asyncio.run(run())
    assert len(deliveries) == 5
    assert store.execution("synthetic_tenant", "run")["state"] == "succeeded"
    payloads = {store.delivery_payload("synthetic_tenant", delivery)[1] for delivery in deliveries}
    assert payloads == {site.originals[key] for key in site.originals if key.startswith("invoice-")}
    assert not any(key.startswith("excluded-") for key in site.downloads)
    assert not store.audit_artifacts("synthetic_tenant").missing


def test_captcha_is_distinct_from_mfa_and_pauses_without_credentials():
    async def run():
        for signed_in in (False, True):
            site = portal(signed_in=signed_in)
            site.captcha = True
            calls = []
            subject = connector(resolver_for(calls))
            context = Context(site)
            result = await subject.check_session(context)
            assert result.kind is InteractionKind.CAPTCHA
            assert result.safe_message_code == "oekostrom_manual_captcha"
            assert calls == []
            page = await subject.discover_page(context, scopes=(NORD,), checkpoint_id=None, **YEAR)
            assert page.kind is InteractionKind.CAPTCHA
            assert not context.published and not site.downloads
            site.captcha = False
            assert await subject.check_session(context) is SessionState.READY
    asyncio.run(run())


def test_checkpoint_survives_reordering_and_out_of_window_insertions():
    async def run():
        first = await connector().discover_page(Context(portal()), scopes=(NORD, SUED),
                                                 checkpoint_id=None, **YEAR)
        changed = portal()
        rows = changed.view_root()["children"][1]["children"]
        outside = copy.deepcopy(rows[0])
        outside["attributes"]["data-issued"] = "2030-01-01"
        outside["children"][0]["text"] = "Invented future invoice"
        rows.reverse()
        rows.insert(0, outside)
        context = Context(changed)
        subject = connector()
        rest, checkpoint = [], first.checkpoint_id
        while checkpoint:
            page = await subject.discover_page(context, scopes=(NORD, SUED),
                                                checkpoint_id=checkpoint, **YEAR)
            rest.extend(page.documents)
            for reference in page.documents:
                await subject.fetch_document(context, reference)
            checkpoint = page.checkpoint_id
        all_ids = {d.source_document_id for d in first.documents + tuple(rest)}
        assert len(all_ids) == 5 and len(rest) == 3
        assert len(context.published) == 3
    asyncio.run(run())


def test_kaution_excluded_but_installment_and_annual_invoices_remain_in_scope():
    async def run():
        site = portal()
        deposits = [row for row in site.rows() if row["attributes"]["data-kind"] == "deposit"]
        assert all("Kaution" in row["children"][0]["text"] for row in deposits)
        invoices = [row for row in site.rows() if row["attributes"]["data-kind"] == "invoice"]
        labels = ("Invented Teilbetragsrechnung", "Invented Abrechnung")
        for row, label in zip(invoices, labels):
            row["children"][0]["text"] = label
        found = await discover_all(connector(), Context(site))
        ids = {reference.source_document_id for reference in found}
        for row, label in zip(invoices, labels):
            assert source_id("installation", row["attributes"]["data-installation"], "invoice", label) in ids
        for name in ("vendor.toml", "browser-synthetic.toml"):
            manifest = tomllib.loads((ROOT / "vendors/oekostrom_at" / name).read_text())
            exclusions = " ".join(manifest["coverage"]["known_exclusions"])
            assert "Kaution" in exclusions and "Teilbetragsrechnung" in exclusions and "Abrechnung" in exclusions
            assert "deposit (Teilbetrag)" not in exclusions
    asyncio.run(run())
