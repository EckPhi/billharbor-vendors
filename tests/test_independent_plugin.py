"""The reference plugin uses SDK-only values and owns its fixtures."""
import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile

import pytest

from billharbor_synthetic.connector import Connector, create_connector
from billharbor_sdk import DocumentKind

ROOT = Path(__file__).resolve().parents[1]


def test_factory_uses_packaged_synthetic_records_without_catalog_or_credentials():
    def no_credentials():
        raise AssertionError("offline reference must not resolve credentials")

    async def verify():
        connector = await create_connector({}, no_credentials)
        assert connector.capabilities().connector_id == "billharbor_synthetic"
        assert connector.document_kinds == (DocumentKind.INVOICE, DocumentKind.CREDIT_NOTE, DocumentKind.SETTLEMENT)
        assert connector.fixture_package == "billharbor_synthetic"
        assert len(connector._fixture["documents"]) == 4
        await connector.close()
    asyncio.run(verify())


def test_optional_fixture_requires_exact_digest(tmp_path):
    source = ROOT / "vendors/billharbor_synthetic/tests/fixtures/synthetic_catalog.json"
    fixture = tmp_path / "invented.json"
    fixture.write_bytes(source.read_bytes())

    async def verify():
        with pytest.raises(ValueError, match="digest"):
            await create_connector({"fixture_path": str(fixture)}, lambda: None)
        connector = await create_connector({"fixture_path": str(fixture),
            "fixture_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest()}, lambda: None)
        assert connector.capabilities().connector_id == "billharbor_synthetic"
        await connector.close()
        with pytest.raises(ValueError, match="Unsupported"):
            await create_connector({"arbitrary": True}, lambda: None)
    asyncio.run(verify())


def test_source_split_preserves_invented_bytes_and_source_identity():
    old = json.loads((ROOT / "vendors/billharbor_synthetic/tests/fixtures/synthetic_catalog.json").read_bytes())
    new = Connector()._fixture
    assert new == old
    for record in old["documents"]:
        parts = [record[key] for key in ("scope_kind", "scope_id", "document_kind", "native_id")]
        expected = "synthetic_" + hashlib.sha256(json.dumps(parts, separators=(",", ":")).encode()).hexdigest()
        assert Connector._source_id(record) == expected


def test_store_generator_binds_exact_wheel_and_manifest(tmp_path):
    spec = importlib.util.spec_from_file_location("build_synthetic_store", ROOT / "tools/build_synthetic_store.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    wheel = tmp_path / "billharbor_synthetic-0.1.0.dev0-py3-none-any.whl"
    manifest = (ROOT / "vendors/billharbor_synthetic/vendor.toml").read_bytes()
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("billharbor_synthetic/data/vendor.toml", manifest)
        archive.writestr("billharbor_synthetic-0.1.0.dev0.dist-info/METADATA",
            "Metadata-Version: 2.3\nName: billharbor-synthetic\nVersion: 0.1.0.dev0\n")
    index = module.build_index(wheel, "http://127.0.0.1:8123", now=100, python_version="3.13")
    release = index["releases"][0]
    assert release["artifact"]["sha256"] == hashlib.sha256(wheel.read_bytes()).hexdigest()
    assert release["descriptor"]["manifest"]["sha256"] == hashlib.sha256(manifest).hexdigest()
    assert release["descriptor_sha256"] == hashlib.sha256(module.canonical(release["descriptor"])).hexdigest()
    assert index["expires_at"] == 86500


def test_original_published_synthetic_descriptor_identity_is_preserved(tmp_path):
    spec = importlib.util.spec_from_file_location("build_synthetic_store", ROOT / "tools/build_synthetic_store.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    wheel = tmp_path / "billharbor_synthetic-0.1.0.dev0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("billharbor_synthetic/data/vendor.toml",
            (ROOT / "vendors/billharbor_synthetic/vendor.toml").read_bytes())
        archive.writestr("billharbor_synthetic-0.1.0.dev0.dist-info/METADATA",
            "Metadata-Version: 2.3\nName: billharbor-synthetic\nVersion: 0.1.0.dev0\n")
    index = module.build_index(wheel, "https://example.invalid/packages", now=100, python_version="3.13")
    assert index["releases"][0]["descriptor_sha256"] == "db788b458ff962936e30a9857382bd5223989760f45775d1aef40e83ce024e96"
