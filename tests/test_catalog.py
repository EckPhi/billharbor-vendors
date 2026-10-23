from __future__ import annotations

import copy
import tomllib
from pathlib import Path

import pytest

from billharbor_sdk.validation import validate_object
from billharbor_vendors.catalog import validate_catalog

ROOT = Path(__file__).resolve().parents[1]


def test_catalog_contains_seven_valid_design_only_manifests() -> None:
    manifests = validate_catalog(ROOT)
    with (ROOT / "catalog.toml").open("rb") as handle:
        catalog = tomllib.load(handle)
    assert {manifest["id"] for manifest in manifests} == {
        "amazon_business_de",
        "oekostrom_at",
        "billharbor_synthetic",
        "drei_at",
        "lidl_connect_at",
        "netcup",
        "hornbach_at",
    }
    assert {manifest["status"] for manifest in manifests} == {"design_only"}
    assert all(manifest["verification"]["live_verified"] is False for manifest in manifests)
    assert all(manifest["schema"] == "vendor-definition/2" for manifest in manifests)
    assert all(manifest["sdk"] == ">=2,<3" for manifest in manifests)
    assert all(
        manifest["compatibility"]["engine"] == ">=0.5.0.dev0,<0.6"
        for manifest in manifests
    )
    # Frozen catalog/manifest versions are independent of distribution releases.
    assert {manifest["version"] for manifest in manifests} == {"0.5.0", "0.1.0"}
    assert catalog["version"] == "0.5.0"


def test_non_design_manifest_cannot_omit_reviewed_origins() -> None:
    with (ROOT / "vendors/oekostrom_at/vendor.toml").open("rb") as handle:
        manifest = tomllib.load(handle)
    candidate = copy.deepcopy(manifest)
    candidate["status"] = "synthetic_verified"

    with pytest.raises(ValueError):
        validate_object(candidate)


def test_capture_must_default_off() -> None:
    with (ROOT / "vendors/amazon_business_de/vendor.toml").open("rb") as handle:
        manifest = tomllib.load(handle)
    candidate = copy.deepcopy(manifest)
    candidate["diagnostics"]["capture_default"] = "on"

    with pytest.raises(ValueError, match="capture_default"):
        validate_object(candidate)
