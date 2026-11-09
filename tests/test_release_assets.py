"""Exercise retries against an invented GitHub release, with no network."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("release_assets", Path(__file__).resolve().parents[1] / "tools/release_assets.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
SHA = "a" * 40
TAG = "v1.2.3rc1"


class ReleaseAssetsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.wheel = Path(self.directory.name) / "invented.whl"
        self.wheel.write_bytes(b"synthetic-wheel")
        self.publisher = MODULE.Publisher("synthetic/repository", TAG, SHA, "refs/tags/" + TAG)
        self.remote = {"release-source.json": (json.dumps({"release_tag": TAG, "source_commit": SHA}, sort_keys=True) + "\n").encode()}
        self.calls = []
        self.exists = True
        self.tag_target = {"type": "commit", "sha": SHA}
        self.api_patch = patch.object(self.publisher, "api", side_effect=self.api)
        self.command_patch = patch.object(self.publisher, "command", side_effect=self.command)
        self.api_patch.start()
        self.command_patch.start()
        self.addCleanup(self.api_patch.stop)
        self.addCleanup(self.command_patch.stop)

    def api(self, endpoint, *, missing=False):
        if endpoint.startswith("releases/tags/"):
            if not self.exists:
                return None
            return {"id": 1, "tag_name": TAG, "draft": False}
        if endpoint.startswith("git/ref/"):
            return {"object": self.tag_target}
        if endpoint.startswith("git/tags/"):
            return {"object": {"type": "commit", "sha": SHA}}
        if endpoint.startswith("releases/1/assets?"):
            return [{"name": name, "id": name} for name in self.remote]
        raise AssertionError(endpoint)

    def command(self, *args):
        self.calls.append(args)
        if args[0] == "api":
            return self.remote[args[1].rsplit("/", 1)[1]]
        if args[:2] == ("release", "create"):
            self.exists = True
        elif args[:2] == ("release", "upload"):
            path = Path(args[3])
            self.remote[path.name] = path.read_bytes()
        return b""

    def mutations(self):
        return [call for call in self.calls if call[0] == "release"]

    def test_partial_upload_resumes_and_second_retry_is_read_only(self):
        self.publisher.publish([self.wheel])
        self.assertEqual(self.remote[self.wheel.name], self.wheel.read_bytes())
        self.assertEqual(len(self.mutations()), 1)
        self.calls.clear()
        self.publisher.publish([self.wheel])
        self.assertEqual(self.mutations(), [])

    def test_conflict_prevents_all_uploads(self):
        other = Path(self.directory.name) / "checksum.txt"
        other.write_bytes(b"new")
        self.remote[self.wheel.name] = b"tampered"
        with self.assertRaisesRegex(ValueError, "asset differs"):
            self.publisher.publish([other, self.wheel])
        self.assertEqual(self.mutations(), [])

    def test_source_marker_and_tag_must_match(self):
        for marker in (None, b"wrong"):
            with self.subTest(marker=marker):
                if marker is None:
                    self.remote.pop("release-source.json", None)
                else:
                    self.remote["release-source.json"] = marker
                with self.assertRaisesRegex(ValueError, "source marker"):
                    self.publisher.publish([self.wheel])
        self.tag_target = {"type": "commit", "sha": "b" * 40}
        with self.assertRaisesRegex(ValueError, "triggering source"):
            self.publisher.publish([self.wheel])
        self.assertEqual(self.mutations(), [])

    def test_annotated_tag_resolves_to_source(self):
        self.tag_target = {"type": "tag", "sha": "b" * 40}
        self.publisher.publish([self.wheel])
        self.assertEqual(len(self.mutations()), 1)

    def test_create_preserves_flags_and_never_clobbers(self):
        self.exists = False
        self.publisher.publish([self.wheel], create=True)
        create, upload = self.mutations()
        self.assertIn("--verify-tag", create)
        self.assertIn("--prerelease", create)
        self.assertIn("--latest=false", create)
        self.assertNotIn("--clobber", upload)

    def test_metadata_errors_never_trigger_creation(self):
        self.api_patch.stop()
        with patch.object(MODULE.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, b"HTTP/2.0 403 Forbidden\r\n\r\n{}", b"")):
            with self.assertRaisesRegex(RuntimeError, "metadata"):
                self.publisher.publish([self.wheel], create=True)
        self.assertEqual(self.mutations(), [])

    def test_only_confirmed_404_means_absent(self):
        self.api_patch.stop()
        for output, expected in ((b"HTTP/2.0 404 Not Found\r\n\r\n{}", None), (b"network failure", "error")):
            with self.subTest(output=output), patch.object(MODULE.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, output, b"")):
                if expected is None:
                    self.assertIsNone(self.publisher.api("releases/tags/missing", missing=True))
                else:
                    with self.assertRaises(RuntimeError):
                        self.publisher.api("releases/tags/missing", missing=True)

    def test_upload_failure_leaves_prior_assets_and_retry_resumes(self):
        original = self.command
        def failing(*args):
            if args[:2] == ("release", "upload"):
                raise RuntimeError("invented upload failure")
            return original(*args)
        self.command_patch.stop()
        with patch.object(self.publisher, "command", side_effect=failing):
            with self.assertRaises(RuntimeError):
                self.publisher.publish([self.wheel])
        self.assertNotIn(self.wheel.name, self.remote)
        with patch.object(self.publisher, "command", side_effect=original):
            self.publisher.publish([self.wheel])
        self.assertEqual(self.remote[self.wheel.name], self.wheel.read_bytes())
