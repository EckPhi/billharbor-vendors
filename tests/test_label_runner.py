"""Invented label policy through durable acquisition; no vendor connection."""
import asyncio
import copy
import json
import tomllib
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from billharbor.engine import DurableStore, RunnerConfig, RunnerContext, run_connector
from oekostrom_at.connector import LabelConnector

ROOT = Path(__file__).resolve().parents[1]


class CountingConnector(LabelConnector):
    fetches = 0

    async def fetch_document(self, context, reference):
        self.fetches += 1
        return await super().fetch_document(context, reference)


def test_label_acquisition_reopen_skip_and_account_isolation(tmp_path):
    fixture = json.loads((ROOT / 'vendors/oekostrom_at/tests/fixtures/synthetic_catalog.json').read_text())
    fixture['fixture_version'] = 'oekostrom-label-synthetic/1'
    original = copy.deepcopy(fixture['documents'][0])
    original['designation'] = 'Invented monthly invoice 2026/09'
    original['observations'] = []
    second = copy.deepcopy(original)
    second['scope_id'] = 'installation_invented_second'
    fixture['scopes'].append({'kind': second['scope_kind'], 'id': second['scope_id']})
    fixture['documents'] = [original, second]
    fixture_path = tmp_path / 'invented.json'
    fixture_path.write_text(json.dumps(fixture))
    manifest = tomllib.loads((ROOT / 'vendors/oekostrom_at/vendor.toml').read_text())

    async def exercise():
        for number, account, expected in ((1, 'account_a', 2), (2, 'account_a', 0), (3, 'account_b', 2)):
            # Reopening the database and artifact store each time models restart.
            store = DurableStore(tmp_path / 'state.sqlite3', tmp_path / 'artifacts')
            now = datetime.now(timezone.utc)
            execution = f'run_{number}'
            store.create_execution('tenant', execution, execution, {}, now=now)
            lease = store.claim_execution('tenant', execution, lease_for=timedelta(minutes=2), now=now)
            connector = CountingConnector(fixture_path, page_size=1)
            config = RunnerConfig(tenant_id='tenant', account_binding_id=account,
                destination_binding_id='destination', destination_revision=1,
                connector_manifest=manifest, starts_on=date(2026, 1, 1), ends_on=date(2026, 12, 31))
            deliveries = await run_connector(store, lease, connector,
                RunnerContext(deadline=now + timedelta(minutes=1)), config)
            assert connector.fetches == expected
            assert len(deliveries) == expected
            assert store.execution('tenant', execution)['discovery_complete'] == 1
            assert store.audit_artifacts('tenant').missing == ()
    asyncio.run(exercise())
