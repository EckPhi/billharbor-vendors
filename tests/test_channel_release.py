"""Offline release identity, stale-selection and retained-byte proofs."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from release_context import resolve
from channel_store import build, canonical, ledger, validate_ledgers

class ReleaseTests(unittest.TestCase):
    def test_branch_identity_and_final(self):
        self.assertEqual(resolve('refs/heads/develop', '1.2.3.dev1', 42, 2)['tag'], 'v1.2.3a42002')
        self.assertEqual(resolve('refs/heads/main', '1.2.3', 42, 1)['channel'], 'beta')
        self.assertEqual(resolve('refs/tags/v2.0.0', '1.2.3', 42, 1)['prerelease'], 'false')
        for ref in ('refs/heads/feature', 'refs/tags/v01.2.3', 'refs/tags/v1.2.3.post1'):
            with self.assertRaises(ValueError): resolve(ref, '1.2.3', 42, 1)
        with self.assertRaises(ValueError): resolve('refs/heads/main', '1.2.3', 42, 1000)

    def test_retention_stale_release_and_publication_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entries = []
            for n in (1, 2, 3):
                raw = str(n).encode()
                item = dict(filename=f'plugin-{n}.whl', sha256=hashlib.sha256(raw).hexdigest())
                folder = root / 'wheels' / item['sha256']; folder.mkdir(parents=True)
                (folder / item['filename']).write_bytes(raw)
                entries.append(item)
            ledgers = [dict(tag=f'v1.0.0b{n}', channel='beta', sequence=n, issued_at=100, wheels=[entries[n-1]]) for n in (2,1)]
            seed = dict(store_id='test', releases=[dict(entries[2], current=True)])
            def index(wheel, url, **kw):
                return dict(store_id=kw['store_id'], revision=kw['revision'], issued_at=kw['now'], releases=[dict(filename=wheel.name)])
            with patch('channel_store.build_index', side_effect=index):
                chosen = build(ledgers, root/'wheels', root/'one', 'https://example.test/store', seed, revision=100000001)
                build(list(reversed(ledgers)), root/'wheels', root/'two', 'https://example.test/store', seed, revision=100000002)
            with patch('channel_store.build_index', side_effect=index):
                channels = [dict(ledgers[0], channel='alpha', sequence=4), dict(ledgers[0], channel='stable', sequence=5)]
                build(channels, root/'wheels', root/'channels', 'https://example.test/store', seed, revision=100000003)
            self.assertEqual(json.loads((root/'channels/alpha/index.json').read_bytes())['store_id'], 'test-alpha')
            self.assertEqual(json.loads((root/'channels/stable/index.json').read_bytes())['store_id'], 'test-stable')
            self.assertEqual(json.loads((root/'channels/index.json').read_bytes())['store_id'], 'test')
            self.assertEqual(chosen['beta']['sequence'], 2)
            first = json.loads((root/'one/index.json').read_bytes())
            second = json.loads((root/'two/index.json').read_bytes())
            self.assertGreater(second['revision'], first['revision'])
            self.assertEqual(first['store_id'], 'test')
            self.assertEqual((root/'one/index.json').read_bytes(), (root/'one/beta/index.json').read_bytes())
            self.assertEqual(first['releases'], [dict(filename='plugin-2.whl')])
            self.assertEqual(len(list((root/'one/packages').rglob('*.whl'))), 3)
            (root/'wheels'/entries[0]['sha256']/entries[0]['filename']).write_bytes(b'tamper')
            with self.assertRaises(ValueError): build(ledgers, root/'wheels', root/'bad', 'https://example.test/store', seed)
            self.assertFalse((root/'bad').exists())

    def test_paths_fail_before_download(self):
        for key, bad in [('filename', '../bad.whl'), ('sha256', '../bad')]:
            item = dict(filename='plugin.whl', sha256='a'*64); item[key] = bad
            with self.assertRaises(ValueError):
                validate_ledgers([dict(tag='v1.2.3', channel='beta', sequence=1, issued_at=1, wheels=[item])])

    def test_retry_ledger_has_identical_bytes_and_excludes_nonplugins(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'billharbor_synthetic-1.0.0-py3-none-any.whl').write_bytes(b'invented-plugin')
            (root / 'billharbor_connector_sdk-0.1.0-py3-none-any.whl').write_bytes(b'invented-sdk')
            (root / 'billharbor_vendors-1.0.0-py3-none-any.whl').write_bytes(b'invented-aggregate')
            first = ledger('v1.0.0', 'stable', 42001, root, issued_at=1700000000)
            with patch('channel_store.time.time', return_value=1800000000):
                retry = ledger('v1.0.0', 'stable', 42001, root, issued_at=1700000000)
            self.assertEqual(canonical(first), canonical(retry))
            self.assertEqual(len(first['wheels']), 1)
            for invalid in (0, -1, True):
                with self.assertRaises(ValueError):
                    ledger('v1.0.0', 'stable', 42001, root, issued_at=invalid)

    def test_release_upload_is_missing_only_and_ledger_is_last(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / '.github/workflows/release.yml').read_text()
        publication = source.split('      - name: Publish immutable GitHub release assets', 1)[1]
        publication = publication.split('      - name: Reconstruct', 1)[0]
        self.assertIn('python3 tools/release_assets.py --create', publication)
        self.assertNotIn('gh release create', publication)
        self.assertNotIn('--clobber', source)
        self.assertIn('if [[ "$PUSH_REF" == refs/tags/* ]]; then ATTEMPT=1; fi', publication)
        self.assertIn('ISSUED_AT=$(git show -s --format=%ct "$RELEASE_SHA")', publication)
        self.assertTrue(publication.rstrip().endswith('"$DIST_DIR"/store-release.json'))

    def test_publication_queue_retains_pending_pushes(self):
        root = Path(__file__).resolve().parents[1]
        for filename in ('release.yml', 'vendor-store-pages.yml'):
            source = (root / '.github/workflows' / filename).read_text()
            self.assertIn('  group: vendor-store-pages\n  cancel-in-progress: false\n  queue: max', source)
