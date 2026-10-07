"""Only invented labels; no vendor account data."""
import json
from pathlib import Path

import pytest

from oekostrom_at.identity import source_id
from oekostrom_at.connector import Connector, LabelConnector

ROOT = Path(__file__).parents[1]


def test_exact_label_identity_separates_scope_kind_and_text():
    key = source_id('installation', 'invented-a', 'invoice', 'Invented invoice 2026/09')
    assert key == source_id('installation', 'invented-a', 'invoice', 'Invented invoice 2026/09')
    assert len(key) < 100
    variants = [
        ('installation', 'invented-b', 'invoice', 'Invented invoice 2026/09'),
        ('installation', 'invented-a', 'credit_note', 'Invented invoice 2026/09'),
        ('installation', 'invented-a', 'invoice', 'Invented invoice 2026/09 '),
        ('installation', 'invented-a', 'invoice', 'invented invoice 2026/09'),
    ]
    assert all(source_id(*parts) != key for parts in variants)
    with pytest.raises(ValueError, match='Bezeichnung'):
        source_id('installation', 'invented-a', 'invoice', ' ')


def label_fixture():
    fixture = json.loads((ROOT / 'vendors/oekostrom_at/tests/fixtures/synthetic_catalog.json').read_text())
    fixture['fixture_version'] = 'oekostrom-label-synthetic/1'
    for index, item in enumerate(fixture['documents']):
        item['designation'] = f'Invented designation {index}'
    return fixture


def test_duplicate_label_fails_even_when_native_id_and_date_differ(tmp_path):
    fixture = label_fixture()
    duplicate = dict(fixture['documents'][0], native_id='different-invented-id', issue_date='2030-01-01')
    fixture['documents'].append(duplicate)
    path = tmp_path / 'invented.json'
    path.write_text(json.dumps(fixture))
    with pytest.raises(ValueError, match='duplicate'):
        LabelConnector(path, page_size=1)


def test_new_policy_does_not_silently_change_legacy_identity(tmp_path):
    fixture = label_fixture()
    path = tmp_path / 'invented.json'
    path.write_text(json.dumps(fixture))
    connector = LabelConnector(path)
    item = fixture['documents'][0]
    assert connector._source_id(item) != Connector._source_id(item)
    with pytest.raises(ValueError, match='version'):
        Connector(path)
