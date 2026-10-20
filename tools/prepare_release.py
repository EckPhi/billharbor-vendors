"""Stamp aggregate-only release metadata in a disposable release checkout."""
from __future__ import annotations

import argparse
import re
import tomllib
from pathlib import Path

# Canonical supported PEP 440 release forms; reject normalization and local labels.
TAG = re.compile(r"v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:(?:a|b|rc)(?:0|[1-9]\d*)|\.(?:dev|post)(?:0|[1-9]\d*))?", re.ASCII)


def prepare(root: Path, tag: str) -> str:
    if TAG.fullmatch(tag) is None:
        raise ValueError("Expected canonical vMAJOR.MINOR.PATCH[ aN | bN | rcN | .devN | .postN ] tag")
    version = tag[1:]
    project_path = root / "pyproject.toml"
    export_path = root / "src/billharbor_vendors/__init__.py"
    lock_path = root / "uv.lock"
    project = project_path.read_text()
    export = export_path.read_text()
    lock = lock_path.read_text()
    metadata = tomllib.loads(project)["project"]
    if metadata["name"] != "billharbor-vendors":
        raise ValueError("Not the aggregate catalog project")
    old = metadata["version"]
    packages = [p for p in tomllib.loads(lock)["package"] if p["name"] == metadata["name"]]
    if len(packages) != 1 or packages[0]["version"] != old:
        raise ValueError("Aggregate lock version must agree with project version")
    replacements = [
        (project_path, project, rf'(?m)^version = "{re.escape(old)}"$', f'version = "{version}"'),
        (export_path, export, rf'(?m)^__version__ = "{re.escape(old)}"$', f'__version__ = "{version}"'),
        (lock_path, lock, rf'(?m)^(name = "billharbor-vendors"\n)version = "{re.escape(old)}"$', rf'\g<1>version = "{version}"'),
    ]
    prepared = []
    for path, source, pattern, replacement in replacements:
        changed, count = re.subn(pattern, replacement, source)
        if count != 1:
            raise ValueError(f"Expected exactly one matching version in {path.name}")
        prepared.append((path, changed))
    for path, changed in prepared:
        path.write_text(changed)
    return version


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag")
    args = parser.parse_args()
    print(prepare(Path(__file__).resolve().parents[1], args.tag))
