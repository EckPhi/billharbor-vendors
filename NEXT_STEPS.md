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

## D1 toolchain lock continuation — 2026-09-17

The authoritative sibling schema is restored and reconciled with the documented
rich manifests. All eight catalog tests pass against it; both vendors remain
`design_only`, with empty reviewed origins and no live compatibility claim.

Pinned the synthetic catalog toolchain to BillHarbor 0.1.0, Hatchling 1.32.0 and
pytest 9.1.1, with license, data-flow and rollback notes in
`docs/dependencies.md`. The uv sibling-path source is development-only: it enables
cross-repository conformance but is mutable and therefore cannot satisfy the
release digest requirement. Generate and commit the frozen lock, then verify both
wheel builds. Before any catalog publication, BillHarbor's current D1 correction
must be committed/released and its wheel SHA-256 recorded; replace or override
the sibling source with that immutable artifact for release verification.

No network, browser, live vendor/API, credential, real document, receiver,
deployment or accounting action occurred. At entry the catalog was clean at
published commit `f00b9c3`; the dependency/toolchain edits are local and
uncommitted. BillHarbor has separate local uncommitted D1 conformance corrections
on top of published commit `73acc6e`.

The catalog lock was then generated offline with uv 0.7.19 and resolves 28
packages. `uv run --frozen --group test pytest -q` built both sibling projects and
passed all eight tests. Offline wheel builds also succeeded. Local candidate
SHA-256 values are
`2d5c3c04bd08c501947b24216d2ace42a79f25be5e1f4db162acb41678f422ae`
for BillHarbor and
`6d99ba988d716b68d68d11ac1b3c52440893146fea350fbcd06e39f28553cdf0`
for the catalog. A project-independent, wheel-only install validated the packaged
Amazon manifest through BillHarbor's packaged schema. These hashes describe local
uncommitted source and are not release pins. The immutable SDK release/digest gate
therefore remains open; the test/build toolchain lock itself is complete.

## CI/CD foundation — 2026-09-17

Added least-privilege GitHub Actions CI and release workflows. They test the
frozen catalog, build both wheels, verify wheel-only compatibility and retain
checksums/build evidence. A matching `v<project.version>` tag publishes only the
catalog wheel, checksum and a `BILLHARBOR-SDK` provenance record to GitHub Releases;
there is no PyPI publication, deployment or vendor access.

The private cross-repository boundary fails closed until repository variable
`BILLHARBOR_REF` contains the exact reviewed 40-character BillHarbor commit and
secret `BILLHARBOR_READ_TOKEN` contains a fine-grained contents-read token for
`EckPhi/billharbor`. The workflow verifies the checkout SHA and never follows
`main`. Action/uv pins, permissions, data flow and rollback are documented in
`docs/dependencies.md` and `docs/ci-cd.md`.

Workflow YAML parses locally and the underlying frozen test/build/wheel-only
commands pass. No workflow has run remotely; changes are uncommitted/unpushed and
the GitHub variable/secret have not been configured. Do not create a release tag
until BillHarbor's current D1 changes are reviewed, committed and pushed, then set
the variable to that exact commit.
