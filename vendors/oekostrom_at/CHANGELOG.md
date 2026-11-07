# Changelog

## 0.6.0 — 2026-11-07

- Port the browser connector to the broker-owned `browser-rpc/1` capability; remove
  plugin-owned Playwright launch and loopback mappings.
- Add data-only `oekostrom-portal-mapping/1` profiles: invented
  `synthetic-invented-portal` (`https://portal.oekostrom-invented.test`) and a
  fail-closed `unreviewed` `oekostrom-live` placeholder.
- Add `create_connector(options, resolver)` with explicit `offline_fixture` or
  `portal_profile` modes and an invented in-process portal for offline conformance.
- Synthetic browser manifest becomes `synthetic_verified` with the exact invented
  HTTPS origin; real manifest stays `design_only` and is narrowed to invoices only
  (credit notes, settlements, PV and deposits excluded).
- Build an independent SDK-only `billharbor-oekostrom-at` plugin wheel.
- `oekostrom-label/1` identities and checkpoint format are unchanged.

## 0.2.0 — 2026-09-18

- Adopt connector SDK v2 artifact-byte publication using packaged synthetic fixtures.

## 0.1.0 — 2026-09-17

- Add design-only manifest and synthetic SDK contract fixture.
