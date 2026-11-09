"""Publish missing release assets; existing source identity and bytes must agree.

Uses only GitHub's scoped gh authentication. Never prints tokens or asset contents.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import quote


class Publisher:
    def __init__(self, repository: str, tag: str, source: str, ref: str):
        if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is None:
            raise ValueError("Expected owner/repository")
        if re.fullmatch(r"[0-9a-f]{40}", source) is None:
            raise ValueError("Expected full source commit SHA")
        if re.fullmatch(r"v[0-9][A-Za-z0-9.]*", tag) is None:
            raise ValueError("Expected version tag")
        self.repository, self.tag, self.source, self.ref = repository, tag, source, ref

    def command(self, *args: str) -> bytes:
        result = subprocess.run(["gh", *args], capture_output=True)
        if result.returncode:
            raise RuntimeError(f"GitHub command failed: {args[0]}")
        return result.stdout

    def api(self, endpoint: str, *, missing: bool = False):
        result = subprocess.run(["gh", "api", "--include", f"repos/{self.repository}/{endpoint}"], capture_output=True)
        # --include emits the HTTP status even for errors. A 403/network failure
        # must never be interpreted as permission to create a release.
        header, separator, body = result.stdout.replace(b"\r\n", b"\n").partition(b"\n\n")
        status = re.search(rb"^HTTP/\S+ (\d{3})\b", header)
        if missing and status and status.group(1) == b"404":
            return None
        if result.returncode or not separator or not status or status.group(1) != b"200":
            raise RuntimeError("GitHub metadata request failed")
        return json.loads(body)

    def verify_tag(self, *, missing: bool = False):
        reference = self.api(f"git/ref/tags/{quote(self.tag, safe='')}", missing=missing)
        if reference is None:
            return
        target = reference["object"]
        seen = set()
        while target["type"] == "tag":
            if target["sha"] in seen or len(seen) >= 16:
                raise ValueError("Invalid annotated tag chain")
            seen.add(target["sha"])
            target = self.api(f"git/tags/{target['sha']}")["object"]
        if target["type"] != "commit" or target["sha"] != self.source:
            raise ValueError("Release tag does not resolve to triggering source commit")

    def asset_bytes(self, asset):
        return self.command("api", f"repos/{self.repository}/releases/assets/{asset['id']}", "-H", "Accept: application/octet-stream")

    def publish(self, files: list[Path], *, create: bool = False):
        names = [path.name for path in files]
        if not files or len(names) != len(set(names)) or "release-source.json" in names:
            raise ValueError("Provide unique asset basenames, excluding release-source.json")
        payloads = {path.name: path.read_bytes() for path in files}
        marker = (json.dumps({"release_tag": self.tag, "source_commit": self.source}, sort_keys=True) + "\n").encode()
        release = self.api(f"releases/tags/{quote(self.tag, safe='')}", missing=create)
        if release is None:
            if not create:
                raise ValueError("Release does not exist")
            # A branch-generated tag may be absent, but an existing tag must
            # agree before creating any visible release or uploading a marker.
            self.verify_tag(missing=not self.ref.startswith("refs/tags/"))
            with tempfile.TemporaryDirectory() as directory:
                marker_path = Path(directory) / "release-source.json"
                marker_path.write_bytes(marker)
                flags = ["--generate-notes"]
                if self.ref.startswith("refs/tags/"):
                    flags += ["--verify-tag"]
                else:
                    flags += ["--target", self.source]
                flags += ["--latest"] if re.fullmatch(r"v\d+\.\d+\.\d+", self.tag) else ["--prerelease", "--latest=false"]
                self.command("release", "create", self.tag, str(marker_path), "--repo", self.repository, *flags)
            release = self.api(f"releases/tags/{quote(self.tag, safe='')}")
        self.verify_tag()
        if release["tag_name"] != self.tag or release.get("draft"):
            raise ValueError("Release metadata disagrees with requested identity")
        # Paginate because a retained release may have more than 30 assets.
        assets = []
        page = 1
        while True:
            batch = self.api(f"releases/{release['id']}/assets?per_page=100&page={page}")
            assets.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        by_name = {asset["name"]: asset for asset in assets}
        if len(by_name) != len(assets):
            raise ValueError("Duplicate remote asset names")
        if "release-source.json" not in by_name or self.asset_bytes(by_name["release-source.json"]) != marker:
            raise ValueError("Missing or conflicting release source marker")
        # Compare every existing requested asset before any upload occurs.
        for name, data in payloads.items():
            if name in by_name and self.asset_bytes(by_name[name]) != data:
                raise ValueError(f"Immutable release asset differs: {name}")
        for path in files:
            if path.name not in by_name:
                self.command("release", "upload", self.tag, str(path), "--repo", self.repository)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--create", action="store_true")
    parser.add_argument("assets", nargs="+", type=Path)
    args = parser.parse_args()
    Publisher(os.environ.get("GH_REPO") or os.environ["GITHUB_REPOSITORY"], os.environ["RELEASE_TAG"], os.environ["GITHUB_SHA"], os.environ["GITHUB_REF"]).publish(args.assets, create=args.create)


if __name__ == "__main__":
    main()
