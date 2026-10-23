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
from channel_store import build, validate_ledgers

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

    def test_publication_queue_retains_pending_pushes(self):
        root = Path(__file__).resolve().parents[1]
        for filename in ('release.yml', 'vendor-store-pages.yml'):
            source = (root / '.github/workflows' / filename).read_text()
            self.assertIn('  group: vendor-store-pages\n  cancel-in-progress: false\n  queue: max', source)
