"""Emit an offline store index from an already-built reviewed standalone plugin wheel.

This never publishes, fetches packages, imports vendor code or starts a server.
The operator reviews the printed index digest before configuring a store.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit
import zipfile


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def build_index(wheel, base_url, *, store_id="synthetic", revision=1, python_version=None,
                now=None, lifetime=86400):
    wheel = Path(wheel)
    parsed = urlsplit(base_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.query or parsed.fragment:
        raise ValueError("An absolute artifact base URL without query/fragment is required.")
    if revision < 1 or lifetime < 1:
        raise ValueError("Positive revision and lifetime required.")
    raw = wheel.read_bytes()
    known = {"billharbor-synthetic": ("billharbor_synthetic", "synthetic")}
    known.update({"billharbor-" + name.replace("_", "-"): (name, name.replace("_", "-"))
                  for name in ("drei_at", "lidl_connect_at", "netcup", "hornbach_at")})
    with zipfile.ZipFile(wheel) as archive:
        metadata_names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(metadata_names) != 1:
            raise ValueError("Exactly one plugin distribution required.")
        from email.parser import BytesParser
        metadata = BytesParser().parsebytes(archive.read(metadata_names[0]))
        if metadata["Name"] not in known:
            raise ValueError("Only reviewed offline plugins are supported.")
        connector_id, plugin_name = known[metadata["Name"]]
        manifest_path = connector_id + "/data/vendor.toml"
        manifest = archive.read(manifest_path)
        import tomllib
        parsed_manifest = tomllib.loads(manifest.decode())
        if parsed_manifest["id"] != connector_id or parsed_manifest["status"] != "design_only":
            raise ValueError("Expected matching design-only manifest.")
    descriptor = {
        "schema": "vendor-plugin/1", "publisher": "billharbor", "name": plugin_name,
        "version": metadata["Version"], "connector_id": connector_id,
        "manifest": {"path": manifest_path, "sha256": hashlib.sha256(manifest).hexdigest()},
        "entrypoint": connector_id + ".connector:create_connector",
        "sdk_version": "0.1.0", "engine_compatibility": ">=0.5.0.dev0,<0.6.0",
        "runtime_profile": {"python": python_version or f"{sys.version_info.major}.{sys.version_info.minor}",
                            "platform": "any", "dependencies": {"billharbor-connector-sdk": "0.1.0"}},
        "license": "Proprietary", "maintainer": "BillHarbor catalog maintainers",
        "maintenance": ("Synthetic-only reference maintained with BillHarbor; no live vendor support."
                        if connector_id == "billharbor_synthetic" else
                        "Offline invented fixtures maintained with BillHarbor; no live vendor support."),
        "changelog": ("First independent plugin package; unchanged invented document identities."
                      if connector_id == "billharbor_synthetic" else
                      "Independent offline plugin package; preserved invented document identities."),
        "conformance": {"options": {}, "fixture_path": connector_id + "/data/fixture.json"},
        "rollback": {"checkpoint_compatible": True},
    }
    now = int(time.time() if now is None else now)
    return {"schema": "vendor-store/1", "store_id": store_id, "revision": revision,
            "issued_at": now, "expires_at": now + lifetime, "revoked": [],
            "releases": [{"descriptor": descriptor,
                          "descriptor_sha256": hashlib.sha256(canonical(descriptor)).hexdigest(),
                          "artifact": {"filename": wheel.name, "url": base_url.rstrip("/") + "/" + wheel.name,
                                       "size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}}]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--store-id", default="synthetic")
    parser.add_argument("--revision", type=int, default=1)
    parser.add_argument("--python", default=None, help="Target reviewed runtime minor, e.g. 3.13")
    args = parser.parse_args()
    index = build_index(args.wheel, args.base_url, store_id=args.store_id,
                        revision=args.revision, python_version=args.python)
    raw = canonical(index)
    args.output.write_bytes(raw)
    print(f"index_sha256={hashlib.sha256(raw).hexdigest()}")


if __name__ == "__main__":
    main()
