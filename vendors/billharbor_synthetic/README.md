# BillHarbor synthetic reference vendor

No real vendor exists. This offline reference reads explicitly invented, digest-pinned
fixtures using connector v2. Stable ID: `billharbor_synthetic`; it never impersonates
a real vendor and never authorizes live access. `design_only` is retained because
the frozen manifest requires reviewed network origins for higher maturity.

Two installation scopes contain four distinct invented originals (invoice, credit
note and settlement). Dates are inclusive; use page size one to exercise pagination.
The shared connector binds checkpoints to scopes/date filters, rejects duplicates and
invalid PDF signatures, respects cancellation and preserves original bytes. Existing
engine deduplication/revalidation handles repeat and changed-byte conflict proofs.

Synthetic credentials in BillHarbor's UI exercise custody only: this offline source
does not authenticate them or contact a portal. No account values belong here.
A separate browser proof must exercise actual synthetic login/session recovery.

No dependencies are added: reuse the catalog's exact pinned BillHarbor SDK/runtime
and build/test dependencies. License: Proprietary, matching the containing package.
Maintenance: BillHarbor catalog maintainers. Data flows from packaged fixture to
bounded artifact publication and BillHarbor's durable outbox; receiver simulation
belongs outside this package. Rollback selects the prior immutable catalog artifact;
do not change existing reference identities or erase retained originals/deliveries.

## Independent package

Build this directory as `billharbor-synthetic==0.1.0.dev0`. Its only runtime
dependency is `billharbor-connector-sdk==0.1.0`; neither the application nor
`billharbor-vendors` is required. The asynchronous factory is
`billharbor_synthetic.connector:create_connector(options, resolver)`. Empty
options load the packaged invented fixture, without calling `resolver`.

From the catalog root, generate a reviewable local store index after building:

```console
uv build --wheel --out-dir /tmp/billharbor-dists vendors/billharbor_synthetic
python tools/build_synthetic_store.py /tmp/billharbor-dists/billharbor_synthetic-0.1.0.dev0-py3-none-any.whl /tmp/billharbor-dists/index.json --base-url http://127.0.0.1:8123 --python 3.13
```

The index expiry is one day; the printed SHA-256 must be explicitly reviewed by
a deployment administrator. HTTP loopback is for the offline synthetic policy
only; public stores require HTTPS. Generating an index does not publish or
install code, enable an account, or authorize a live run.
