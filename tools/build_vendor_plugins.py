"""Build SDK-only offline vendor wheels in disposable projects, without source edits.

The reviewed fixture helper is bundled into each fixture wheel; no catalog or
reference plugin runtime dependency is introduced. The Ökostrom browser-rpc wheel
bundles its connector, identity policy, packaged mapping profiles, invented DOM
fixture and synthetic browser manifest. No network or vendor access is needed.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
VENDORS = ("drei_at", "lidl_connect_at", "netcup", "hornbach_at")
# Browser-rpc plugins built from reviewed source files, not the fixture helper.
BROWSER_VENDORS = ("oekostrom_at",)
OEKOSTROM_FILES = ("browser.py", "offline.py", "identity.py", "data/fixture.json",
                   "data/profiles/synthetic-invented-portal.toml", "data/profiles/oekostrom-live.toml")
VERSION = re.compile(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:(?:a|b|rc)(?:0|[1-9]\d*)|\.dev(?:0|[1-9]\d*))?\Z")


def _pyproject(vendor, version, description):
    return f'''[build-system]
requires = ["hatchling==1.32.0"]
build-backend = "hatchling.build"

[project]
name = "billharbor-{vendor.replace('_', '-')}"
version = "{version}"
description = "{description}"
readme = "README.md"
requires-python = ">=3.11"
license = {{ text = "Proprietary" }}
dependencies = ["billharbor-connector-sdk==0.1.0"]

[tool.hatch.build.targets.wheel]
packages = ["src/{vendor}"]
'''


def prepare_oekostrom_project(version, destination):
    """Independent browser-rpc wheel; legacy fixture connector.py is not shipped."""
    vendor = "oekostrom_at"
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    source = ROOT / "vendors" / vendor
    package = destination / "src" / vendor
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        '"""Ökostrom browser-rpc plugin; invented .test portal profile only, no live support."""\n')
    (package / "connector.py").write_text(
        '"""Plugin entrypoint; the broker owns the browser and the live profile fails closed."""\n'
        "from .browser import create_connector\n\n__all__ = [\"create_connector\"]\n")
    for name in OEKOSTROM_FILES:
        target = package / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / "src" / vendor / name, target)
    # The synthetic browser manifest is this plugin's reviewed vendor definition.
    shutil.copyfile(source / "browser-synthetic.toml", package / "data/vendor.toml")
    shutil.copyfile(source / "README.md", destination / "README.md")
    (destination / "pyproject.toml").write_text(_pyproject(
        vendor, version, "Synthetic-verified browser-rpc plugin for an invented oekostrom portal"))
    return destination


def prepare_project(vendor, version, destination):
    if vendor not in VENDORS + BROWSER_VENDORS or not VERSION.fullmatch(version):
        raise ValueError("Known offline vendor and canonical release version required.")
    if vendor in BROWSER_VENDORS:
        return prepare_oekostrom_project(version, destination)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    source = ROOT / "vendors" / vendor
    package = destination / "src" / vendor
    package.mkdir(parents=True)
    (package / "__init__.py").write_text('"""Design-only offline vendor plugin; no live support."""\n')
    helper = ROOT / "vendors/billharbor_synthetic/src/billharbor_synthetic"
    shutil.copyfile(helper / "synthetic.py", package / "synthetic.py")
    connector = (source / "src" / vendor / "connector.py").read_text()
    connector = connector.replace("from billharbor_vendors.synthetic import SyntheticConnector", "from .synthetic import SyntheticConnector")
    connector = connector.replace(f'    connector_id = "{vendor}"', f'    connector_id = "{vendor}"\n    fixture_package = "{vendor}"')
    factory = (helper / "connector.py").read_text().split("async def create_connector", 1)[1]
    (package / "connector.py").write_text(connector + "\n\nasync def create_connector" + factory)
    data = package / "data"
    data.mkdir()
    shutil.copyfile(source / "vendor.toml", data / "vendor.toml")
    shutil.copyfile(source / "tests/fixtures/synthetic_catalog.json", data / "fixture.json")
    shutil.copyfile(source / "README.md", destination / "README.md")
    (destination / "pyproject.toml").write_text(_pyproject(
        vendor, version, f"Design-only invented offline fixture plugin for {vendor}"))
    return destination


def build_plugins(version, output_dir):
    output_dir = Path(output_dir).resolve()
    if not VERSION.fullmatch(version):
        raise ValueError("Canonical release version required.")
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="billharbor-plugins-") as temporary:
        for vendor in VENDORS + BROWSER_VENDORS:
            project = prepare_project(vendor, version, Path(temporary) / vendor)
            subprocess.run([sys.executable, "-m", "hatchling", "build", "-t", "wheel", "-d", str(output_dir)], cwd=project, check=True)
    return sorted(output_dir.glob(f"billharbor_*-{version}-py3-none-any.whl"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    build_plugins(args.version, args.output_dir)


if __name__ == "__main__":
    main()
