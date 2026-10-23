"""Reconstruct channel indexes from immutable GitHub Release ledgers, never wheel code."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import re
import time
from urllib.parse import urlsplit
from build_synthetic_store import build_index, canonical


def ledger(tag, channel, sequence, wheels):
    if channel not in ('alpha', 'beta', 'stable') or sequence < 1:
        raise ValueError('Invalid channel/sequence')
    entries = []
    for wheel in sorted(Path(wheels).glob('*.whl')):
        if wheel.name.startswith(('billharbor_connector_sdk-', 'billharbor_vendors-')):
            continue
        entries.append(dict(filename=wheel.name, sha256=hashlib.sha256(wheel.read_bytes()).hexdigest()))
    if not entries:
        raise ValueError('No plugin wheels')
    return dict(tag=tag, channel=channel, sequence=sequence, issued_at=int(time.time()), wheels=entries)


def build(ledgers, wheels, output, base_url, seed, revision=None):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Output must be empty')
    validate_ledgers(ledgers)
    if not ledgers:
        raise ValueError("At least one successful release ledger is required")
    parsed = urlsplit(base_url)
    if parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment or re.search(r'[\s%\\]', base_url):
        raise ValueError('Public HTTPS base URL required')
    selected = {}
    retained = {}
    sequences = set()
    for entry in ledgers:
        if entry['channel'] not in ('alpha', 'beta', 'stable') or type(entry['sequence']) is not int or entry['sequence'] < 1 or entry['sequence'] in sequences:
            raise ValueError('Invalid or duplicate release sequence')
        sequences.add(entry['sequence'])
        previous = selected.get(entry['channel'])
        if previous is None or entry['sequence'] > previous['sequence']:
            selected[entry['channel']] = entry
        for item in entry['wheels']:
            key = item['filename']
            if key in retained and retained[key]['sha256'] != item['sha256']:
                raise ValueError('Immutable wheel filename changed')
            retained[key] = item
    for item in seed['releases']:
        if item['filename'] in retained and retained[item['filename']]['sha256'] != item['sha256']:
            raise ValueError('Historical wheel changed')
        retained[item['filename']] = item
    # Fail before any output, including on unsafe filename/digest or missing history.
    for item in retained.values():
        name, digest = item['filename'], item['sha256']
        if not re.fullmatch(r'[a-zA-Z0-9_.-]+\.whl', name) or not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError('Unsafe wheel entry')
        raw = (Path(wheels) / digest / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError('Wheel digest mismatch')
    revision = revision if revision is not None else time.time_ns() // 1000
    if type(revision) is not int or revision < 1:
        raise ValueError("Positive publication revision required")
    issued_at = revision // 1000000
    indexes = {}
    for channel, entry in selected.items():
        indexes[channel] = []
        for item in entry['wheels']:
            indexes[channel].append(build_index(Path(wheels) / item['sha256'] / item['filename'], base_url.rstrip('/') + '/packages/' + item['sha256'], store_id=seed['store_id'] if channel == 'beta' else seed['store_id'] + '-' + channel, revision=revision, python_version='3.13', lifetime=90 * 86400, now=issued_at))
    import shutil
    for item in retained.values():
        target = output / 'packages' / item['sha256'] / item['filename']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(wheels) / item['sha256'] / item['filename'], target)
    for channel, parts in indexes.items():
        index = parts[0]
        index['releases'] = [release for part in parts for release in part['releases']]
        raw = canonical(index)
        directory = output / channel
        directory.mkdir()
        (directory / 'index.json').write_bytes(raw)
        (directory / 'index.sha256').write_text(hashlib.sha256(raw).hexdigest() + '  index.json\n')
    # Legacy URL follows beta when available; initial alpha must not remove it.
    alias = 'beta' if 'beta' in indexes else ('stable' if 'stable' in indexes else None)
    if alias:
        index = json.loads((output / alias / 'index.json').read_bytes())
        index['store_id'] = seed['store_id']
        raw = canonical(index)
        (output / 'index.json').write_bytes(raw)
        (output / 'index.sha256').write_text(hashlib.sha256(raw).hexdigest() + '  index.json\n')
    else:
        parts = [build_index(Path(wheels) / i['sha256'] / i['filename'], base_url.rstrip('/') + '/packages/' + i['sha256'], store_id=seed['store_id'], revision=revision, python_version='3.13', lifetime=90 * 86400, now=issued_at) for i in seed['releases'] if i['current']]
        index = parts[0]
        index['releases'] = [r for part in parts for r in part['releases']]
        raw = canonical(index)
        (output / 'index.json').write_bytes(raw)
        (output / 'index.sha256').write_text(hashlib.sha256(raw).hexdigest() + '  index.json\n')
    return selected


def validate_ledgers(ledgers):
    from prepare_release import TAG
    for entry in ledgers:
        if entry.get('channel') not in ('alpha', 'beta', 'stable') or type(entry.get('sequence')) is not int or entry['sequence'] < 1:
            raise ValueError('Invalid channel sequence')
        if not isinstance(entry.get('tag'), str) or not TAG.fullmatch(entry['tag']):
            raise ValueError('Invalid ledger tag')
        if type(entry.get('issued_at')) is not int or entry['issued_at'] < 1:
            raise ValueError('Invalid ledger issue time')
        if not entry.get('wheels'):
            raise ValueError('Empty ledger')
        for item in entry['wheels']:
            if not re.fullmatch(r'[a-zA-Z0-9_.-]+\.whl', item['filename']) or not re.fullmatch(r'[0-9a-f]{64}', item['sha256']):
                raise ValueError('Unsafe wheel entry')


def gh(*args):
    return subprocess.check_output(['gh', *args])

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    create = sub.add_parser('ledger')
    for name in ('tag', 'channel', 'wheels', 'output'):
        create.add_argument('--' + name, required=True)
    create.add_argument('--sequence', type=int, required=True)
    site = sub.add_parser('site')
    for name in ('repository', 'wheels', 'output', 'base-url'):
        site.add_argument('--' + name, required=True)
    a = p.parse_args()
    if a.command == 'ledger':
        Path(a.output).write_bytes(canonical(ledger(a.tag, a.channel, a.sequence, a.wheels)))
    else:
        pages = json.loads(gh('api', '--paginate', '--slurp', f'repos/{a.repository}/releases?per_page=100'))
        ledgers = []
        for release in [r for page in pages for r in page if not r['draft']]:
            if any(asset['name'] == 'store-release.json' for asset in release['assets']):
                from prepare_release import TAG
                if not TAG.fullmatch(release['tag_name']):
                    raise ValueError('Unsafe release tag')
                data = gh('release', 'download', release['tag_name'], '--repo', a.repository, '--pattern', 'store-release.json', '--output', '-')
                entry = json.loads(data)
                if entry['tag'] != release['tag_name']:
                    raise ValueError('Release ledger tag mismatch')
                ledgers.append(entry)
        from build_pages_store import load_manifest
        seed = load_manifest('.github/vendor-store.json')
        validate_ledgers(ledgers)
        downloads = [(e['tag'], w) for e in ledgers for w in e['wheels']] + [(i['tag'], i) for i in seed['releases']]
        for tag, item in downloads:
            target = Path(a.wheels) / item['sha256']
            target.mkdir(parents=True, exist_ok=True)
            if not (target / item['filename']).exists():
                subprocess.run(['gh', 'release', 'download', tag, '--repo', a.repository, '--pattern', item['filename'], '--dir', str(target)], check=True)
        build(ledgers, a.wheels, a.output, a.base_url, seed)
