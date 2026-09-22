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

## Publication blocker — 2026-09-17

Catalog changes are committed and pushed through
`2b9f92a624a3af250bd31f1c9d7e4db4f4bbb201`. Repository variable
`BILLHARBOR_REF` is correctly pinned to released BillHarbor commit
`99bb2e5146f25e87471ec4ccbcd0d59a1597b445`. Remote catalog CI correctly fails
closed at the private sibling checkout because required secret
`BILLHARBOR_READ_TOKEN` is absent. Do not substitute a broad operator token.
A `DOCKERHUB_TOKEN` secret exists in this catalog repository but is unrelated and
must not be used for source checkout.

No catalog `v0.1.0` tag or GitHub Release was created. After a fine-grained token
with contents-read access only to `EckPhi/billharbor` is stored under the required
secret name, rerun CI. Tag and release the catalog only after that run passes.

## Local connector v2 migration — 2026-09-18

The operator approved a major connector boundary correction. The local catalog is
now version 0.2.0 and requires BillHarbor 0.2.0, `vendor-definition/2` and
`billharbor-connector/2`. Both design-only connectors publish decoded synthetic
original bytes through the engine-owned context capability instead of discarding
them. Their invented fixture JSON is packaged as catalog data, so installed-wheel
entrypoints can initialize without a source checkout. Both vendor changelogs and
engine compatibility ranges were updated; neither package claims live support.

All 10 catalog tests pass, including both connectors running through BillHarbor's
durable engine into pending outbox events with exact stored-byte verification.
Both 0.2.0 wheels build and install together in isolation; default installed
connector construction finds the packaged fixtures. The local uncommitted catalog
wheel SHA-256 is
`840f48c73b351631538ba98b06d79b4795fd3fd0dd39013d23cedbf9d6878439`.
The pre-existing local edit to `docs/dependencies.md` was preserved and not
overwritten. Candidate hashes are not release pins.

Before publication, review/commit/push BillHarbor 0.2.0, update the catalog's
`BILLHARBOR_REF` to that exact commit, update dependency provenance for the
released 0.2.0 wheel, configure the still-missing fine-grained
`BILLHARBOR_READ_TOKEN`, obtain green remote CI, then deliberately tag the catalog
v0.2.0. No remote secret, release, live access or deployment was performed.

## v0.2.0 release preparation — 2026-09-21

BillHarbor `v0.2.0` is released at commit
`a69e7e59277183153232b6c57f1b7276d14751c4`. Its published wheel SHA-256 is
`734b5abce8b93ebf4077a1b94515e1074235597d7ec113b9522e3caccd7a988f`,
matching a clean local rebuild. The engine CI and release workflows passed.
`BILLHARBOR_READ_TOKEN` is now configured in the catalog repository; its value was
not read or copied. Next pin `BILLHARBOR_REF` to the above commit, publish this
catalog candidate, require green remote CI, then tag `v0.2.0`. No live vendor,
receiver, accounting, or application-deployment gate is opened by this release.

## v0.2.0 publication — 2026-09-21

Catalog commit `94d63cc1ecd11dd0fb837ca1a29c9415246e8cfa` was pushed to
`main` after `BILLHARBOR_REF` was pinned to released engine commit
`a69e7e59277183153232b6c57f1b7276d14751c4`. Remote cross-repository CI
passed. Annotated `v0.2.0` resolves to the catalog commit, and its release
workflow passed, publishing the catalog wheel with SHA-256
`840f48c73b351631538ba98b06d79b4795fd3fd0dd39013d23cedbf9d6878439`.
The published `BILLHARBOR-SDK` record contains the pinned engine commit and its
verified wheel digest
`734b5abce8b93ebf4077a1b94515e1074235597d7ec113b9522e3caccd7a988f`.
No live connector, vendor authentication, receiver operation, or application
deployment occurred. Future catalog changes must retain immutable engine pinning
and rerun cross-repository CI before a new tag.

## D4 synthetic vendor package candidate — 2026-09-22

The operator requested D4 and a commit. This local `0.3.0` candidate keeps
`vendor-definition/2`, connector SDK v2 and both `design_only` live gates. Invented
`vendor-synthetic/1` fixtures now cover two Amazon legal-entity shaped scopes,
including a repeated native invoice ID, and two Ökostrom installations with
invoice, credit note and feed-in settlement outputs. The shared fixture reader
validates typed scope membership and derives source IDs from scope, type and
native ID. Four typed observations per document retain source paths. No new
package, browser, secret, remote API or live selector was introduced.

Direct local lifecycle verification fetched all six invented originals and proved
unique scoped identities and per-type coverage. Python compilation and
`git diff --check` passed. Full pytest could not be certified here: collection
stalled in the local environment, while a clean uv cache required an unavailable
network fetch for the pinned build backend. CI must run the catalog and sibling
engine conformance suites before any version tag or release. This D4 work is
committed locally after verification; inspect `git status` and remote divergence
before publication. No push, tag, release, vendor access, receiver, deployment or
accounting action is implied. Next: resolve the test-environment issue, obtain
green cross-repository CI, review the immutable engine/catalog pin, then plan D5
only under its separate deployment scope. G1/G2 remain closed.

### D4 verification correction — 2026-09-22

The first pushed D4 commit used a PEP 440 development suffix in manifest versions;
`vendor-definition/2` correctly rejects that spelling. The candidate catalog,
manifest and package version is now `0.3.0` without changing the frozen schema.
The source-tree catalog test reads the source `pyproject.toml` version so an older
installed editable distribution cannot mask or falsely fail source conformance.
With pytest's local cache plugin disabled, the full catalog suite passes **12/12**;
`git diff --check` also passes. This correction must be committed and pushed
before D4 can be treated as the remote baseline. Wheel-only packaging and remote
cross-repository CI are still separate release gates; no release tag was made.
