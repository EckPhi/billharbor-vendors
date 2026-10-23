"""Resolve immutable release identity from a GitHub push (standard library only)."""
import argparse
import json
import re
import tomllib
from pathlib import Path
from prepare_release import TAG


def resolve(ref, source_version, run_number, attempt):
    if ref.startswith('refs/tags/'):
        tag = ref.removeprefix('refs/tags/')
        if not TAG.fullmatch(tag):
            raise ValueError('Noncanonical release tag')
        if '.post' in tag:
            raise ValueError('Unsupported plugin version: .postN tags are not supported by the engine')
        version = tag[1:]
        channel = 'stable' if re.fullmatch(r'\d+\.\d+\.\d+', version) else ('alpha' if re.search(r'(?:a\d+|\.dev\d+)$', version) else 'beta')
    else:
        branch = ref.removeprefix('refs/heads/')
        if branch not in ('develop', 'main') or min(run_number, attempt) < 1 or attempt >= 1000:
            raise ValueError('Expected develop/main and positive run identity (attempt <1000)')
        base = re.match(r'\d+\.\d+\.\d+', source_version)
        if not base:
            raise ValueError('Invalid source version')
        channel = 'alpha' if branch == 'develop' else 'beta'
        version = base[0] + ('a' if channel == 'alpha' else 'b') + str(run_number * 1000 + attempt)
        tag = 'v' + version
    return dict(tag=tag, version=version, channel=channel, prerelease=str(channel != 'stable').lower())

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ref', required=True)
    p.add_argument('--run-number', type=int, required=True)
    p.add_argument('--attempt', type=int, required=True)
    a = p.parse_args()
    source = tomllib.loads(Path('pyproject.toml').read_text())['project']['version']
    for key, value in resolve(a.ref, source, a.run_number, a.attempt).items():
        print(f'{key}={value}')
