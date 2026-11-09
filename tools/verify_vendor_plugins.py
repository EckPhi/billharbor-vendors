"""Verify installed offline wheels in an isolated SDK-only Python environment.

Run with ``python -I tools/verify_vendor_plugins.py`` after installing the SDK,
the four prebuilt fixture wheels and the Ökostrom browser-rpc wheel. This
executes only invented packaged fixtures (the Ökostrom wheel through its
in-process invented portal, without a browser or credentials) and rejects an
environment containing application, aggregate/reference or Playwright packages.
"""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, timezone
import hashlib
import importlib
import importlib.util
import sys
from importlib.resources import files
import tomllib

from billharbor_sdk import ArtifactPublication, SessionState
from billharbor_sdk.validation import validate_object

VENDORS = ("drei_at", "lidl_connect_at", "netcup", "hornbach_at")
BROWSER_VENDORS = ("oekostrom_at",)


class FixtureContext:
    def __init__(self):
        self.artifacts = {}

    @property
    def deadline(self):
        return datetime.now(timezone.utc) + timedelta(minutes=1)

    def cancelled(self):
        return False

    async def emit_safe_event(self, code, **counters):
        return None

    async def publish_artifact(self, *, artifact_id, filename, media_type, content):
        assert content.startswith(b"%PDF-"), "Packaged original must be an invented PDF"
        self.artifacts[artifact_id] = bytes(content)
        return ArtifactPublication(artifact_id=artifact_id, filename=filename,
            media_type=media_type, byte_size=len(content),
            sha256=hashlib.sha256(content).hexdigest())


def reject_credentials():
    raise AssertionError("Offline conformance must not request credentials")


async def verify():
    for forbidden in ("billharbor", "billharbor_vendors", "billharbor_synthetic", "playwright"):
        assert importlib.util.find_spec(forbidden) is None, f"Unexpected runtime dependency: {forbidden}"
    for vendor in VENDORS + BROWSER_VENDORS:
        manifest = tomllib.loads(files(vendor).joinpath("data/vendor.toml").read_text())
        validate_object(manifest)
        browser = vendor in BROWSER_VENDORS
        assert manifest["id"] == vendor
        assert manifest["status"] == ("synthetic_verified" if browser else "design_only")
        options = {"offline_fixture": True} if browser else {}
        connector = await importlib.import_module(vendor + ".connector").create_connector(options, reject_credentials)
        context = FixtureContext()
        try:
            assert connector.capabilities().connector_id == vendor
            assert await connector.check_session(context) is SessionState.READY
            scopes = await connector.list_scopes(context)
            assert scopes
            checkpoint = None
            observed = set()
            seen_checkpoints = set()
            for _ in range(100):
                page = await connector.discover_page(context, starts_on=date(2026, 1, 1),
                    ends_on=date(2026, 12, 31), scopes=scopes, checkpoint_id=checkpoint)
                for document in page.documents:
                    assert document.source_document_id not in observed
                    observed.add(document.source_document_id)
                    artifact = await connector.fetch_document(context, document)
                    assert artifact.media_type == "application/pdf"
                    assert artifact.sha256 == hashlib.sha256(context.artifacts[artifact.artifact_id]).hexdigest()
                checkpoint = page.checkpoint_id
                if checkpoint is None:
                    break
                assert checkpoint not in seen_checkpoints, "Pagination did not advance"
                seen_checkpoints.add(checkpoint)
            else:
                raise AssertionError("Packaged fixture exceeded bounded page budget")
            if browser:
                assert len(observed) == sum(1 for item in connector._offline_browser.rows()
                                            if item["attributes"]["data-kind"] == "invoice")
            else:
                assert len(observed) == len(connector._fixture["documents"])
        finally:
            await connector.close()
        assert "playwright" not in sys.modules
        print(f"{vendor}: installed offline manifest/factory/discovery/PDF lifecycle passed")


if __name__ == "__main__":
    asyncio.run(verify())
