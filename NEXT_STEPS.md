# Vendor catalog handoff — 2026-09-17

The operator selected a separate billharbor-vendors project. Read AGENTS.md,
README.md, docs/vendor-definition.md and the sibling BillHarbor architecture.
The manifest specification is a design, not an implemented schema. Next coordinate
SDK/schema version 1 with BillHarbor, scaffold packaging/validation and invented
fixtures for Amazon Business DE and oekostrom.at when implementation is requested.

Do not invent live selectors or claim actual account/API compatibility. API versus
browser transport, per-account/subaccount identity, metadata provenance, bounded
pagination, original downloads and manual authentication challenges are required.
No secret values, sessions or real documents in catalog/tests. No live access or
production gate opened. No installation, Git initialization, commit, remote, push
or deployment occurred during this transfer. Runtime files remain to be created.

## Repository publication — 2026-09-17

The operator authorized initializing Git and publishing this project privately
to `EckPhi/billharbor-vendors`. Main contains the design documents and a
.gitignore excluding local secrets/runtime files. The publication command pushes
this commit to origin/main; verify remote visibility and HEAD when resuming.
No runtime implementation or deployment is included.

Remote publication was verified on 2026-09-17: local `main`, `origin/main` and
remote `HEAD` all resolve to commit
`cc358faa13e875f6e524c0454febf6016110cc5a`, with remote `HEAD` targeting `main`.
The worktree was clean before the D1 continuation described below.

## D1 continuation — 2026-09-17

Added design-only `vendor-definition/1` fixtures for `amazon_business_de` and
`oekostrom_at`. BillHarbor owns the frozen schema and validator. Empty network origins and
`requires_verification` identity/discovery fields deliberately make both packages
ineligible for live execution. No connector code or live selectors were invented.

The catalog scaffolding changed concurrently while the engine schema was being
frozen, so cross-repository catalog-suite conformance must be rerun after that
worktree settles. BillHarbor's own eight-test suite uses an engine-owned golden
manifest and passes independently; do not treat that as catalog package acceptance.

Next: package the catalog against a pinned BillHarbor SDK release/digest and add
negative manifest fixtures. Connector scaffolding and invented API/browser fixtures
follow only after the cross-repository release boundary is selected. No vendor
access, credentials, real documents, browser dependency, deployment, commit or
push occurred.

Implementation then continued with catalog packaging, validation, fixture-only
SDK connectors and invented local document bytes. Five connector tests pass.
Three catalog manifest tests remain blocked because overlapping BillHarbor work
removed the authoritative `schemas/vendor-definition-1.schema.json` during the
verification run. Reconcile and restore that engine-owned schema, rerun both test
suites and wheel builds, and keep both vendors `design_only`. No live transport,
selectors, credentials, sessions, real documents, deployment, commit or push.
