# Ökostrom browser-rpc connector (synthetic)

`oekostrom_at.browser.BrowserConnector` implements SDK v2 over the application's
broker-owned `browser-rpc/1` capability (BillHarbor issue #11,
`docs/operations/gated-live-validation.md`). The plugin never imports, launches or
initializes a browser; there is no Playwright import anywhere in the package and
no plugin dependency beyond `billharbor-connector-sdk==0.1.0`. Every interaction
is `await context.browser(operation, **arguments)` with only `navigate`, `fill`,
`click`, `text`, `attribute`, `count` and `download`. The worker performs
`initialize`; the gateway enforces HTTPS:443, the exact reviewed origin set and
rejects every 3xx. The connector additionally navigates only to
`mapping.origin + login_path` and `mapping.origin + documents_path`.

The previous plugin-owned Chromium path (`create_browser_connector`, loopback
`http://127.0.0.1` mappings, request routing) was removed together with its
Playwright loopback tests; browser-rpc forbids plugin-owned launch.

## Factory and options contract

Descriptor entrypoint `oekostrom_at.connector:create_connector(options, resolver)`
requires exactly one explicit mode; anything else (including `{}`) is rejected:

| `options` | Behaviour |
| --- | --- |
| `{"offline_fixture": true}` | Offline, credential-free conformance against the packaged invented DOM (`data/fixture.json`) through an in-process fake of the seven operations. The resolver is discarded and never called. Acquisition must reject this reserved conformance option in the application before factory creation; both conformance and acquisition worker contexts may expose browser capabilities. This is the descriptor's `conformance.options`. |
| `{"portal_profile": "synthetic-invented-portal"}` | Drive the worker-supplied `context.browser` with the synthetic mapping. Credentials are resolved only when the login form is present. |
| `{"portal_profile": "oekostrom-live"}` | Always fails closed (unreviewed placeholder). |

## Mapping profiles

`PortalMapping` is a data-only profile (schema `oekostrom-portal-mapping/1`)
loaded from reviewed package data under `data/profiles/` by an explicit id from a
fixed table; ids are never paths. The loader requires exact keys, the matching
`profile_id` and `status = "synthetic"`. Origins must be exactly
`https://<lowercase-host>` (no port, path, query or userinfo) and, because no
live profile is reviewed, the host must end in `.test`. Selectors may not use
`js=`/`javascript=` engines or `>>`; the connector composes only
`<rows> >> nth=<i> >> <child>`. Paths are plain absolute paths.

- `synthetic-invented-portal`: `https://portal.oekostrom-invented.test`,
  `/anmelden` and `/rechnungen`, invented selectors, page size 2.
- `oekostrom-live`: `status = "unreviewed"`, empty origin/selectors; loading
  raises. Supplying a URL or other options cannot select a live portal.

## Behaviour retained

Login only when the login form is present (credentials are type-checked, used for
two `fill` calls and deleted; never stored or placed in messages); challenge →
`InteractionRequest(MFA, "oekostrom_manual_challenge")`; a separate CAPTCHA selector →
`InteractionRequest(CAPTCHA, "oekostrom_manual_captcha")`; missing ready marker →
`SESSION_EXPIRED`; `list_scopes` raises the safe code on interaction. Installations
are enumerated by count plus nth attribute. Discovery covers the combined view,
rejects unknown installations, duplicate installations, duplicate
`oekostrom-label/1` identities (before date filtering) and a newly appearing
pagination control. Issue dates are filtered inclusively. Only `invoice` rows are
read; deposit, credit-note, settlement, PV and any other kinds are skipped and
never downloaded. Kaution rows are deposits; Teilbetragsrechnung and Abrechnung are invoices.
Checkpoints bind the exact query and selected invoice identities/dates, excluding
transient row indices; reorderings and out-of-window insertions survive rediscovery.
An in-range invoice set/date/identity change still requires a fresh run. Fetch requires
rediscovery, rechecks the row's installation, kind, Bezeichnung and date, then
checks the PDF signature and per-document byte limit on the returned bytes and
publishes via `context.publish_artifact`.

## Manifests

`browser-synthetic.toml` (packaged in the plugin wheel as
`oekostrom_at/data/vendor.toml`, and in the aggregate wheel as
`billharbor_vendors/data/oekostrom_browser_synthetic.toml`) is `synthetic_verified`
with browser as the sole preferred/supported transport, `origins` and
`redirect_origins` exactly the invented origin, no unresolved dependencies and
`document_kinds = ["invoice"]`. Tests mirror `browser_policy` live eligibility and
call the application's `BrowserPolicy.validate_installation` on the built
descriptor. The real `vendor.toml` stays `design_only` with empty origins and is
now invoices-only by operator decision. The aggregate fixture
`Connector`/`LabelConnector` and their invented fixture also expose invoices only;
runner integration tests exercise the shipped manifest without widening it.

## Limitations of browser-rpc observed

- Gateway rejects every 3xx and non-2xx response; a real login that redirects
  after POST cannot work without a reviewed redirect-free flow.
- Single-element operations are strict and any broker failure closes the browser
  for the execution, so the connector always counts before `text`/`attribute`.
- Each `discover_page` rereads the whole combined view (about six RPC calls per
  row); the remote proxy caps 100,000 callbacks per connector, so a live profile
  needs a large page size (the observed 222-document view at page size 1 would
  exceed it).
- `download` buffers whole files up to 20 MiB; the byte limit is checked after
  transfer, but the broker wire limit bounds it.

## Verification and remaining live gates

Tests use the in-process invented portal only (`tests/test_oekostrom_browser.py`,
`tests/test_vendor_plugin_build.py`), including a durable runner/outbox run with a
test-local `design_only` copy. They prove nothing about the real portal. Before a
reviewed live profile: exact origins via operator-led origin-only observation,
sanitized selectors and identity/date/pagination evidence under G1/G2, actual key
custody (#10), and the application live-validation proof. Rollback: reinstall the
previous plugin/catalog release and restart incomplete acquisitions (snapshot
hashes from older wheels are rejected); checkpoints use the unchanged
`cursor_<snapshot>_<offset>` form and `oekostrom-label/1` identities are unchanged.

No new dependency is introduced.

## Exact Bezeichnung policy — 2026-10-08

The operator chose the exact visible designation, not AdoId or the printed invoice
number. `oekostrom-label/1` encodes installation kind, installation ID, document
kind and exact label in canonical JSON before SHA-256. Account binding remains an
engine identity boundary. Whitespace/case/Unicode are not normalized. Duplicate
keys in the selected installation snapshot fail before date filtering or output;
renamed labels create different keys and require operator reconciliation. The
`oekostrom_label_v1_` prefix separates this policy from historical synthetic and
native-ID identities; no automatic migration or aliasing is provided.
