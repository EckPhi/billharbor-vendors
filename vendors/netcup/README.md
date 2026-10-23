# netcup

Status: `design_only`. Independent offline fixture wheels can be generated and
verified by the release pipeline, alongside the aggregate catalog. No publication
or live support is claimed. The connector
reads invented offline fixtures; browser capability describes the intended
transport and does not launch a browser. Invoice is the synthetic target kind,
and PDF is the invented fixture format; neither establishes live coverage.

Official information places invoice management in the Customer Control Panel (CCP). Hosting/server administration APIs do not establish invoice API coverage.

Public evidence checked 2026-10-23: [official source](https://www.netcup.com/de/ueber-netcup/zahlungsmethoden).
Public site URLs are identity references, not approved runtime origins. Network
origins remain empty. Authentication fields, selectors, account/contract scope,
dates, pagination, identity, download links and automation terms require separate
authorized verification. No credentials, sessions, real documents or live calls
are included. A future credential UI must follow BillHarbor ADR 0002.

No dependencies added. Existing pinned SDK/synthetic helper is reused; catalog
maintainers own this design-only definition. Data flows only from invented local
JSON/PDF into the SDK test context. Roll back using the preceding immutable
catalog build; do not alter historical source identities or resume old cursors
under changed connector provenance.
