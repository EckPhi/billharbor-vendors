"""Catalog loading without runtime downloads or dynamic installation."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from billharbor.validation import validate_manifest


def load_manifest(path: Path) -> dict[str, Any]:
    return validate_manifest(path.read_bytes())


def validate_catalog(root: Path) -> tuple[dict[str, Any], ...]:
    with (root / "catalog.toml").open("rb") as handle:
        catalog = tomllib.load(handle)
    if catalog.get("schema") != "vendor-catalog/1":
        raise ValueError("catalog schema must be 'vendor-catalog/1'")

    manifests = []
    seen: set[str] = set()
    for record in catalog.get("vendors", []):
        manifest_path = root / record["manifest"]
        manifest = load_manifest(manifest_path)
        if manifest["id"] in seen:
            raise ValueError(f"duplicate connector id: {manifest['id']}")
        if (record["id"], record["version"], record["status"]) != (
            manifest["id"],
            manifest["version"],
            manifest["status"],
        ):
            raise ValueError(f"catalog record does not match {manifest_path}")
        seen.add(manifest["id"])
        manifests.append(manifest)
    if not manifests:
        raise ValueError("catalog must contain at least one vendor")
    return tuple(manifests)
