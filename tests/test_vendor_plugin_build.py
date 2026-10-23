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
