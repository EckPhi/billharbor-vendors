"""Offline publication invariants; no release download or deployment."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location("build_pages_store", TOOLS / "build_pages_store.py")
pages = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pages)
sys.path.pop(0)


class PagesStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = {"store_id": "billharbor-vendors", "releases": []}
        for version, current in [("0.1.0.dev0", False), ("0.1.0.dev1", True)]:
            name = f"billharbor_synthetic-{version}-py3-none-any.whl"
            wheel = self.root / name
            with zipfile.ZipFile(wheel, "w") as archive:
                archive.writestr("billharbor_synthetic/data/vendor.toml", 'id = "billharbor_synthetic"\nstatus = "design_only"\n' )
                archive.writestr(f"billharbor_synthetic-{version}.dist-info/METADATA",
                                 f"Name: billharbor-synthetic\nVersion: {version}\n")
            digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
            dest = self.root / "wheels" / digest
            dest.mkdir(parents=True)
            wheel.rename(dest / name)
            self.manifest["releases"].append({"tag": "v0.5.0.dev2", "filename": name,
                                             "sha256": digest, "current": current})

    def build(self, **kwargs):
        return pages.build_site(self.manifest, self.root / "wheels", self.root / "site",
                                "https://eckphi.github.io/billharbor-vendors", **kwargs)

    def test_retains_old_wheel_and_binds_current_index_exactly(self):
        index, digest = self.build(revision=2, now=100)
        self.assertEqual(index["expires_at"], 100 + 90 * 86400)
        self.assertEqual(len(index["releases"]), 1)
        self.assertEqual(index["releases"][0]["descriptor"]["version"], "0.1.0.dev1")
        self.assertEqual(digest, hashlib.sha256((self.root / "site/index.json").read_bytes()).hexdigest())
        for item in self.manifest["releases"]:
            self.assertEqual((self.root / "site/packages" / item["sha256"] / item["filename"]).read_bytes(),
                             (self.root / "wheels" / item["sha256"] / item["filename"]).read_bytes())
        self.assertIn("/packages/", index["releases"][0]["artifact"]["url"])

    def test_digest_mismatch_fails_before_output(self):
        item = self.manifest["releases"][0]
        (self.root / "wheels" / item["sha256"] / item["filename"]).write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            self.build(revision=1)
        self.assertFalse((self.root / "site").exists())

    def test_rejects_invalid_revision_lifetime_and_output_contamination(self):
        for kwargs in [{"revision": 0}, {"revision": 1, "lifetime_days": 91}]:
            with self.assertRaises(ValueError):
                self.build(**kwargs)
        (self.root / "site").mkdir()
        (self.root / "site/secret").write_text("invented")
        with self.assertRaisesRegex(ValueError, "empty"):
            self.build(revision=1)

    def test_manifest_rejects_traversal_duplicate_and_invalid_digest(self):
        for field, value in [("filename", "../bad.whl"), ("tag", "--help"), ("sha256", "bad")]:
            modified = json.loads(json.dumps(self.manifest))
            modified["releases"][0][field] = value
            path = self.root / "manifest.json"
            path.write_text(json.dumps(modified))
            with self.assertRaises(ValueError):
                pages.load_manifest(path)
        self.manifest["releases"].append(self.manifest["releases"][0])
        path.write_text(json.dumps(self.manifest))
        with self.assertRaises(ValueError):
            pages.load_manifest(path)


if __name__ == "__main__":
    unittest.main()
