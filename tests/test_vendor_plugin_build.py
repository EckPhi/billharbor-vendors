"""Generated independent offline projects retain reviewed source and resources."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]

def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.mark.parametrize("vendor", load("build_vendor_plugins").VENDORS)
def test_project_and_factory_are_independent(vendor, tmp_path):
    builder = load("build_vendor_plugins")
    project = builder.prepare_project(vendor, "0.5.0a123", tmp_path / vendor)
    source = project / "src"
    code = f'''
import asyncio, importlib, sys
sys.path.insert(0, {str(source)!r})
sys.path.insert(0, {str(ROOT.parent / "billharbor/packages/connector-sdk/src")!r})
module = importlib.import_module({vendor + '.connector'!r})
def reject_credentials():
    raise AssertionError("Credentials must never be resolved")
async def verify():
    connector = await module.create_connector({{}}, reject_credentials)
    assert connector.capabilities().connector_id == {vendor!r}
    assert connector._fixture["synthetic"] is True
    assert connector._fixture["documents"]
    await connector.close()
    try:
        await module.create_connector({{"fixture_sha256": "bad"}}, reject_credentials)
    except ValueError:
        pass
    else:
        raise AssertionError("Orphan digest accepted")
asyncio.run(verify())
assert not any(name.startswith("billharbor_vendors") or name.startswith("billharbor_synthetic") for name in sys.modules)
'''
    subprocess.run([sys.executable, "-I", "-c", code], check=True)
    text = (project / "pyproject.toml").read_text()
    assert 'dependencies = ["billharbor-connector-sdk==0.1.0"]' in text
    assert (source / vendor / "data/fixture.json").read_bytes() == (ROOT / "vendors" / vendor / "tests/fixtures/synthetic_catalog.json").read_bytes()


def test_unknown_vendor_and_noncanonical_version_fail_before_writes(tmp_path):
    builder = load("build_vendor_plugins")
    for vendor, version in [("unreviewed", "1.0.0"), ("drei_at", "1.0.0+local"), ("drei_at", "1.0.0.post1")]:
        with pytest.raises(ValueError):
            builder.prepare_project(vendor, version, tmp_path / "no-output")
        assert not (tmp_path / "no-output").exists()

@pytest.mark.parametrize("vendor", load("build_vendor_plugins").VENDORS)
def test_store_descriptor_uses_individual_manifest_and_entrypoint(vendor, tmp_path):
    builder = load("build_vendor_plugins")
    store = load("build_synthetic_store")
    project = builder.prepare_project(vendor, "0.5.0b7", tmp_path / vendor)
    wheel = tmp_path / f"billharbor_{vendor}-0.5.0b7-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.write(project / "src" / vendor / "data/vendor.toml", f"{vendor}/data/vendor.toml")
        archive.writestr(f"billharbor_{vendor}-0.5.0b7.dist-info/METADATA",
            f"Metadata-Version: 2.3\nName: billharbor-{vendor.replace('_', '-')}\nVersion: 0.5.0b7\n")
    index = store.build_index(wheel, "https://example.invalid/packages", now=100, python_version="3.12")
    descriptor = index["releases"][0]["descriptor"]
    assert descriptor["connector_id"] == vendor
    assert descriptor["entrypoint"] == f"{vendor}.connector:create_connector"
    assert descriptor["manifest"]["path"] == f"{vendor}/data/vendor.toml"
    assert descriptor["conformance"]["fixture_path"] == f"{vendor}/data/fixture.json"
    assert descriptor["runtime_profile"]["dependencies"] == {"billharbor-connector-sdk": "0.1.0"}


def _oekostrom_wheel(builder, tmp_path, version="0.6.0b3"):
    project = builder.prepare_project("oekostrom_at", version, tmp_path / "oekostrom_at")
    wheel = tmp_path / f"billharbor_oekostrom_at-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        for path in sorted((project / "src").rglob("*")):
            if path.is_file():
                archive.write(path, str(path.relative_to(project / "src")))
        archive.writestr(f"billharbor_oekostrom_at-{version}.dist-info/METADATA",
            f"Metadata-Version: 2.3\nName: billharbor-oekostrom-at\nVersion: {version}\n"
            "Requires-Dist: billharbor-connector-sdk==0.1.0\n")
    return project, wheel


def test_oekostrom_project_is_independent_browser_rpc_plugin(tmp_path):
    builder = load("build_vendor_plugins")
    assert "oekostrom_at" in builder.BROWSER_VENDORS and "oekostrom_at" not in builder.VENDORS
    project = builder.prepare_project("oekostrom_at", "0.6.0a1", tmp_path / "oekostrom_at")
    package = project / "src/oekostrom_at"
    source = ROOT / "vendors/oekostrom_at"
    assert (package / "data/vendor.toml").read_bytes() == (source / "browser-synthetic.toml").read_bytes()
    assert (package / "data/fixture.json").read_bytes() == (source / "src/oekostrom_at/data/fixture.json").read_bytes()
    for name in builder.OEKOSTROM_FILES:
        assert (package / name).read_bytes() == (source / "src/oekostrom_at" / name).read_bytes()
    assert "billharbor_vendors" not in (package / "connector.py").read_text()
    text = (project / "pyproject.toml").read_text()
    assert 'name = "billharbor-oekostrom-at"' in text
    assert 'dependencies = ["billharbor-connector-sdk==0.1.0"]' in text
    code = f'''
import asyncio, importlib, sys
from datetime import date, datetime, timedelta, timezone
import hashlib
sys.path.insert(0, {str(project / "src")!r})
sys.path.insert(1, {str(ROOT.parent / "billharbor/packages/connector-sdk/src")!r})
from billharbor_sdk import ArtifactPublication, SessionState
module = importlib.import_module("oekostrom_at.connector")
def reject():
    raise AssertionError("Credentials must never be resolved")
class Context:
    deadline = datetime.now(timezone.utc) + timedelta(minutes=1)
    def cancelled(self): return False
    async def publish_artifact(self, *, artifact_id, filename, media_type, content):
        return ArtifactPublication(artifact_id, filename, media_type, len(content), hashlib.sha256(content).hexdigest())
async def verify():
    for options in ({{}}, {{"portal_profile": "oekostrom-live"}}):
        try:
            await module.create_connector(options, reject)
        except ValueError:
            pass
        else:
            raise AssertionError("Unsafe options accepted")
    c = await module.create_connector({{"offline_fixture": True}}, reject)
    context = Context()
    assert await c.check_session(context) is SessionState.READY
    scopes = await c.list_scopes(context)
    checkpoint, count = None, 0
    while True:
        page = await c.discover_page(context, starts_on=date(2000, 1, 1), ends_on=date(2100, 1, 1), scopes=scopes, checkpoint_id=checkpoint)
        for ref in page.documents:
            await c.fetch_document(context, ref); count += 1
        if page.terminal: break
        checkpoint = page.checkpoint_id
    assert count == 5
    await c.close()
asyncio.run(verify())
assert not any(n.startswith(("billharbor_vendors", "billharbor_synthetic", "playwright")) for n in sys.modules)
'''
    subprocess.run([sys.executable, "-I", "-c", code], check=True)


def test_oekostrom_descriptor_and_browser_live_policy_eligibility(tmp_path):
    builder = load("build_vendor_plugins")
    store = load("build_synthetic_store")
    project, wheel = _oekostrom_wheel(builder, tmp_path)
    index = store.build_index(wheel, "https://example.invalid/packages", now=100, python_version="3.13")
    release = index["releases"][0]
    descriptor = release["descriptor"]
    assert descriptor["connector_id"] == "oekostrom_at" and descriptor["name"] == "oekostrom-at"
    assert descriptor["entrypoint"] == "oekostrom_at.connector:create_connector"
    assert descriptor["manifest"]["path"] == "oekostrom_at/data/vendor.toml"
    assert descriptor["conformance"] == {"options": {"offline_fixture": True},
                                         "fixture_path": "oekostrom_at/data/fixture.json"}
    assert descriptor["runtime_profile"]["dependencies"] == {"billharbor-connector-sdk": "0.1.0"}
    import tomllib
    manifest = tomllib.loads((project / "src/oekostrom_at/data/vendor.toml").read_text())
    from billharbor.plugins import descriptor as validate_descriptor
    validate_descriptor(descriptor)
    from billharbor.browser_policy import BrowserPolicy
    origins = tuple(sorted(set(manifest["network"]["origins"]) | set(manifest["network"]["redirect_origins"])))
    policy = BrowserPolicy("invented-tenant", "invented-account", release["artifact"]["sha256"], origins,
        "sha256:" + "0" * 64, version="browser-live/1", manifest_sha256=descriptor["manifest"]["sha256"],
        descriptor_sha256=release["descriptor_sha256"])
    policy.validate_installation(manifest, descriptor, release["artifact"]["sha256"])
    real = tomllib.loads((ROOT / "vendors/oekostrom_at/vendor.toml").read_text())
    with pytest.raises(ValueError):
        policy.validate_installation(real, descriptor, release["artifact"]["sha256"])
    # A design-only fixture plugin cannot masquerade as the browser plugin.
    tampered = dict(manifest, status="design_only")
    with pytest.raises(ValueError):
        policy.validate_installation(tampered, descriptor, release["artifact"]["sha256"])
