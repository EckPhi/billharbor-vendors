# Lidl Connect Austria

Status: `design_only`. Included in the aggregate development catalog only; no
independent installable store plugin or live support is claimed. The connector
reads invented offline fixtures; browser capability describes the intended
transport and does not launch a browser. Invoice is the synthetic target kind,
and PDF is the invented fixture format; neither establishes live coverage.

Official FAQ lists top-up invoices under Mein Konto. This is the Austrian Lidl Connect service requested as lidl-mobile; other national Lidl services are excluded.

Public evidence checked 2026-10-23: [official source](https://www.lidl-connect.at/faq-category/mein-konto/).
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
