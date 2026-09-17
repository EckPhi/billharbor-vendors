# BillHarbor vendor definitions

Design specification moved from IEF Bookkeeping on 2026-09-17.
Status: proposed; no connectors or executable schema exist yet.

## 3. Three different kinds of configuration

1. **Vendor definition (public, versioned):** capabilities, supported regions,
   transports, auth requirements, entrypoints, defaults and compatibility.
2. **Account binding (private, runtime):** selected marketplace/account/contract
   scope, tenant/source IDs, destination bindings, secret references and pinned connector version.
   Recipient company/issuer mappings belong to the receiving integration.
   These are potentially personal metadata even without passwords; keep outside Git.
3. **Execution request (immutable):** account binding revision, date window,
   budgets, idempotency key, optional opaque continuation and debug mode.

Neither the public catalog nor the execution request contains passwords, OAuth
refresh tokens, cookies, OTPs or signed document URLs. Secret references resolve
inside the runner. Multiple required secrets may be fields of one external
secret bundle so the existing wire's single `secret_reference` remains usable.
A public vendor package never hard-codes an internal company or issuer ID.

## 4. Vendor-definition fields

| Section | Required semantics |
|---|---|
| Identity | Stable namespaced connector ID, display name, vendor site, maintainer, license, package version and changelog |
| Compatibility | Manifest schema, SDK major/range, engine range, tested runtime/browser matrix and wire adapters |
| Maturity | `design_only`, `synthetic_verified`, `account_verified`, `disabled`; supported/tested capabilities distinguished |
| Coverage | Marketplace/country/language/timezone, account types, document kinds and known exclusions |
| Transports | API/browser/hybrid, preferred method, allowed alternatives and explicit selection rules |
| Network | HTTPS origins for auth/API/portal/download, redirects, required methods and any separately reviewed CDN exceptions |
| Authentication | OAuth/secret bundle/interactive login, required roles/scopes, external secret field names, session expiry and MFA/manual recovery |
| Account hierarchy | Accounts, organizations, billing groups, contracts/sites/meters; enumeration and selected scope |
| Discovery | Time-filter meaning, date inclusivity, pagination, ordering, lookback, late availability, empty-result/completeness semantics |
| Document identity | Native invoice/document ID, subaccount/issuer/type scope, revision policy and stable encoding |
| Download | PDF/XML/other formats, MIME/signature verification, link expiry, polling/download mechanism, limits and expected evidence |
| Metadata | Typed observations and source paths, document kind, invoice/due date, amount/currency, references and issuer evidence |
| Operations | Timeouts, request/page/document/byte/runtime budgets, throttling/backoff, concurrency and classified failures |
| Interaction | MFA/CAPTCHA/session-expiry detectors, resumable pause, account lease, permitted human actions and timeout |
| Diagnostics | Safe step names and counters; capture disabled by default; optional protected retention policy |
| Verification | Synthetic fixtures, supported scope, last verification date/version, known gaps, drift indicators and recovery instructions |

Limits come from the minimum of engine policy, manifest and requested budgets.
A definition cannot widen deployment egress or increase operator permissions.
Selectors and field mappings may be declarative data; control flow remains code.
No arbitrary shell, eval expressions or fetched JavaScript in manifest fields.

Illustrative non-executable TOML (not a claim about observed portal behavior):

```toml
schema = "vendor-definition/1"
id = "oekostrom_at"
display_name = "oekostrom.at"
version = "0.1.0"
status = "design_only"
entrypoint = "oekostrom_at.connector:Connector"
sdk = ">=1,<2"

[coverage]
country = "AT"
locales = ["de-AT"]
timezone = "Europe/Vienna"
document_kinds = ["invoice"]

[transport]
preferred = "browser"
api_status = "not_publicly_documented"
# Exact auth/download origins require later authorized discovery.

[authentication]
mode = "interactive_or_secret_bundle"
secret_fields = ["username", "password"]
session_scope = "account"
manual_challenges = ["mfa", "captcha", "session_expired"]

[discovery]
subaccount_kind = "anlage"
date_basis = "requires_verification"
identity_strategy = "requires_verification"

[limits]
concurrent_sessions_per_account = 1
maximum_documents_per_page = 100
maximum_document_bytes = 26214400
maximum_execution_seconds = 300

[diagnostics]
capture_default = "off"
```

A `design_only` package with unresolved origins/identity/date semantics cannot be
enabled for live runs. It is useful for planning and synthetic tests. Amazon's
manifest would declare API preference and DE marketplace support separately from
account eligibility; it must not promise an Austrian marketplace or universal
invoice coverage. Actual roles/auth fields follow verified onboarding evidence.


## Engine integration

See the [BillHarbor architecture](../../billharbor/docs/architecture/vendor-fetcher-design.md)
for the SDK, lifecycle, delivery contract and vendor research.
