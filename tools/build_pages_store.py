"""Build a public synthetic store from reviewed, locally downloaded release wheels."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import urlsplit

from build_synthetic_store import build_index, canonical


def load_manifest(path):
    manifest = json.loads(Path(path).read_bytes())
    releases = manifest["releases"]
    if not releases or not any(item["current"] for item in releases):
        raise ValueError("At least one current release is required")
    seen = set()
    for item in releases:
        if not re.fullmatch(r"v[0-9][A-Za-z0-9.]*", item["tag"]):
            raise ValueError("Invalid release tag")
        if not re.fullmatch(r"billharbor_synthetic-[A-Za-z0-9.]+-py3-none-any\.whl", item["filename"]):
            raise ValueError("Invalid synthetic wheel filename")
        if not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
            raise ValueError("Invalid wheel SHA-256")
        if type(item["current"]) is not bool or item["filename"] in seen:
            raise ValueError("Duplicate wheel filename or invalid current flag")
        seen.add(item["filename"])
    return manifest


def build_site(manifest, wheels, output, base_url, revision, lifetime_days=90, now=None):
    parsed = urlsplit(base_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment or re.search(r"[\s%\\]", base_url):
        raise ValueError("A public HTTPS base URL is required")
    if type(revision) is not int or revision < 1 or not 1 <= lifetime_days <= 90:
        raise ValueError("Positive revision and lifetime of 1–90 days required")
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output must be empty; never mix unreviewed files into the public site")
    # Validate every wheel before writing anything, including retained historical files.
    for item in manifest["releases"]:
        raw = (Path(wheels) / item["sha256"] / item["filename"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError("Wheel digest mismatch: " + item["filename"])
    indexes = []
    for item in manifest["releases"]:
        wheel = Path(wheels) / item["sha256"] / item["filename"]
        index = build_index(wheel, base_url.rstrip("/") + "/packages/" + item["sha256"],
                            store_id=manifest["store_id"], revision=revision, python_version="3.13",
                            lifetime=lifetime_days * 86400, now=now)
        if item["current"]:
            indexes.append(index)
    index = indexes[0]
    index["releases"] = [release for current in indexes for release in current["releases"]]
    for item in manifest["releases"]:
        target = output / "packages" / item["sha256"] / item["filename"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(wheels) / item["sha256"] / item["filename"], target)
    raw = canonical(index)
    output.mkdir(parents=True, exist_ok=True)
    (output / "index.json").write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    (output / "index.sha256").write_text(digest + "  index.json\n")
    return index, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=".github/vendor-store.json")
    parser.add_argument("--wheels", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--revision", type=int, required=True)
    parser.add_argument("--lifetime-days", type=int, default=90)
    parser.add_argument("--download-repository", help="Download reviewed assets with gh; CI current repository only")
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    if args.download_repository:
        for item in manifest["releases"]:
            target = args.wheels / item["sha256"]
            target.mkdir(parents=True, exist_ok=True)
            subprocess.run(["gh", "release", "download", item["tag"], "--repo", args.download_repository,
                            "--pattern", item["filename"], "--dir", str(target)], check=True)
    index, digest = build_site(manifest, args.wheels, args.output, args.base_url,
                               args.revision, args.lifetime_days)
    print(f"Index URL: {args.base_url.rstrip('/')}/index.json\nStore ID: {index['store_id']}\n"
          f"Revision: {index['revision']}\nExpires at (Unix UTC): {index['expires_at']}\n"
          f"Reviewed index SHA-256: {digest}\nApproved publisher: billharbor\n"
          f"Approved origin: https://{urlsplit(args.base_url).netloc}")


if __name__ == "__main__":
    main()
