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
