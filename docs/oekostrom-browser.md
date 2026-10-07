# Ökostrom browser implementation candidate

The catalog now contains `oekostrom_at.browser.BrowserConnector`, implementing
SDK v2, and `async create_browser_connector(mapping, credential_resolver=None)`.
The worker injects a `PortalMapping` and a synchronous, execution-bound resolver
returning `{"username": ..., "password": ...}`. The factory starts a fresh,
headless Chromium context with service workers blocked and no retained profile,
recording or screenshots. `close()` disposes the context, browser and driver.
Credentials are resolved only when a login form is needed, never stored on the
connector or included in diagnostic messages. The engine must adapt its private
credential bundle at the worker boundary.

**No live profile exists.** Mapping construction permits only explicit HTTP
127.0.0.1 origins and `synthetic=True`. Selectors in tests belong solely to the
invented portal. The released catalog manifest and default connector entrypoint
remain unchanged and `design_only`. A separate packaged `oekostrom_browser_synthetic.toml`
profile declares invoice-only invented-portal behavior for SDK/engine integration
tests; it also remains `design_only`. This separate implementation cannot be
selected for real Ökostrom access simply by supplying a production URL.

The browser implementation supports explicit installation enumeration,
inclusive issue-date filtering (invented fixture semantics), exact Bezeichnung hashes scoped by installation and kind (account scoping is engine-owned), bounded combined-view snapshots and snapshot/query-bound continuation.
It rejects duplicate identities, undiscovered fetches, changed row identities,
unknown installations and newly appearing pagination controls. Only invoice rows
are supported; unsupported credit/PV/deposit kinds are excluded. A session/challenge
state returns a manual interaction request without retrying authentication.
Session failure during scope enumeration raises a safe code because SDK v2 does
not permit interaction results from that method.

All routed requests, including redirected requests and subresources, consume
engine request budget and must match the configured exact origin. WebSockets are
closed. The guard complements, but does not replace, worker/container network
isolation: browser process traffic is not an OS security boundary. The worker
must impose filesystem/tmpfs and process limits. Original downloads are checked
against the configured maximum size **after browser download completion**, before
reading bytes into memory, checked for the PDF signature, published through the
engine context, and deleted from browser download storage in a finally block.
A malicious oversized response can therefore fill temporary storage up to the
worker's disk quota; this implementation does not promise streaming byte limits.

## Validation

Actual Chromium tests use a threaded invented loopback portal. One test also
runs the candidate through the durable engine, retaining two original PDFs and
pending outbox deliveries. They cover login,
installation enumeration, scope identity, exact original byte publication,
query-bound checkpoints, restart continuation, terminal empty ranges, changed
filters, duplicate identities, unsupported reference kinds, malformed originals,
manual challenges, unsupported pagination, foreign subresources and byte limits.
Tests skip when the optional Playwright Python module is absent; a browser-enabled
release lane must run them explicitly and must not interpret skipped tests as
browser verification. With Playwright installed, absent browser binaries fail.

Example in a browser-enabled environment:

```sh
python -m pytest -q tests/test_oekostrom_browser.py
```

## Remaining live acceptance

A separately authorized session must establish the chosen exact Bezeichnung policy across
sessions/revisions, the meaning of `Datum`, completeness of combined installation
results, pagination/late-document behavior, actual login/challenge flow, original
PDF controls, exact redirects and permitted automation. Real selectors must come
from sanitized authorized evidence, not the invented fixture. Review a versioned
live mapping and implement its distinct extraction semantics before removing the
loopback restriction. No boolean operator setting substitutes for this review.
Then validate interrupted/repeated runs through the durable engine using the
approved account, kinds, budgets and destinations. Credit notes and PV settlements
remain unsupported until separately established. The synthetic tests do not close
D6 or authorize live access, callbacks, recurring automation or deployment.


## Exact Bezeichnung policy — 2026-10-08

The operator chose the exact visible designation, not AdoId or the printed invoice
number. `oekostrom-label/1` encodes installation kind, installation ID, document
kind and exact label in canonical JSON before SHA-256. Account binding remains an
engine identity boundary. Whitespace/case/Unicode are not normalized. Duplicate
keys in the selected installation snapshot fail before date filtering or output;
renamed labels create different keys and require operator reconciliation. The
`oekostrom_label_v1_` prefix separates this policy from historical synthetic and
native-ID identities; no automatic migration or aliasing is provided.

The default legacy fixture connector stays unchanged. `LabelConnector` accepts
only explicit `oekostrom-label-synthetic/1` fixtures with an invented `designation`.
The imported browser candidate now reads a configured designation locator and
rechecks its exact text before clicking the original download control. These
selectors are solely invented and live origins remain rejected. The browser
foundation was imported from recorded commit
`58b7af2fc22b5a6bdbcfd0a68c48e7ac3f4b99ed`, without switching checkout or adopting
new dependencies. This local candidate is not a published catalog release.
