## Browser candidate and engine integration — 2026-09-30

The operator authorized implementation and a local commit. A Playwright SDK-v2
browser candidate now handles an invented loopback Ökostrom-shaped portal,
including credential injection, account scope checks, issue-date filtering,
checkpointed discovery, original PDF publication, exact-origin request budgets,
challenge signaling and browser cleanup. The original `design_only` vendor
manifest remains unchanged. A separate packaged invoice-only synthetic browser
profile supports the engine proof; it is also `design_only`. No real portal
selectors, native document ID or completeness assumption entered source.

The full catalog suite passed 21 tests, including five actual Chromium tests. A
browser candidate run through the durable engine retained two invented PDFs and
pending outbox deliveries. The candidate catalog wheel built locally, and one
packaged catalog fixture ran through BillHarbor's spawned worker. No live vendor,
real documents/credentials or deployment occurred. The browser's post-download
byte check still requires a worker tmpfs/disk limit. D6 G1/G2, automation terms,
real mapping/identity/completeness, recovery and reviewed live profile remain
open. Git state: committed locally on branch `codex/first-release-foundation`
at operator request; nothing was pushed or tagged.

# Vendor catalog handoff — 2026-09-17

## Release hardening — 2026-09-25

### v0.4.0.dev0 publication

Catalog commit `cd3245973968bb17e09cba1eeeb6b45dd9da69bc` was pushed
after repository variable `BILLHARBOR_REF` was pinned to released engine commit
`38aa403393d502b6d6a42424162b9625f77115f8`. Cross-repository CI run
`36123749836` passed. Annotated tag `v0.4.0.dev0` triggered release run
`36123807672`, which passed frozen tests and paired wheel-only verification. The
GitHub release is marked as a prerelease. Published catalog wheel SHA-256 is
`e34dba0c998a967fdd8fa410c6ad2adc3da06accb71c09e160c4729536caf37d`;
the published provenance asset records engine wheel SHA-256
`6aac950e3fa759ae1eb05c8de6fc91cddeee596f738737b7227dcd0586dd6529`.
No live connector, vendor access, callback or deployment was enabled.

An isolated install of both downloaded release wheels ran the packaged Amazon and
Ökostrom synthetic connectors through the released engine, producing six pending
deliveries with successful executions and a clean artifact audit. Downloaded
wheel hashes matched the published checksums; no callback was sent.

The synthetic connector now accepts legacy `offset_N` checkpoints so an
interrupted 0.3 catalog execution can finish after a connector upgrade; all new
checkpoints remain bound to the normalized scope/date query digest. Pagination
coverage now asserts the exact deterministic cursor instead of only its suffix.
The frozen offline suite passes 16 tests; Python compilation, `git diff --check`
and Git integrity checks pass. Paired wheel-only installation and manifest/
entrypoint validation succeeds. Candidate catalog wheel SHA-256 is
`e34dba0c998a967fdd8fa410c6ad2adc3da06accb71c09e160c4729536caf37d`;
it is local evidence only until published.

BillHarbor `v0.4.0.dev0` is now released from commit
`38aa403393d502b6d6a42424162b9625f77115f8`; its wheel SHA-256 is
`6aac950e3fa759ae1eb05c8de6fc91cddeee596f738737b7227dcd0586dd6529`.
The catalog package/lock target that exact prerelease, while catalog and connector
manifest versions use schema-valid `0.4.0`. Local and remote paired-wheel
compatibility are verified. Next run synthetic smoke tests from the published
artifacts and collect feedback before any release-candidate/final promotion. No
live gate is opened; both manifests remain `design_only`.

## Ökostrom D6 continuation — 2026-09-24

Supersedes the historical “awaiting sign-in” record below. The operator manually
signed into their personal account, selected the `Alle Anlagen` view, and the
portal showed eight installations plus a combined invoice overview. After
clarifying that marked export is only a payment list, the operator authorized
individual invoice downloads. Six distinct PDFs and two duplicate copies were
downloaded for operator inspection and remain outside this catalog repository;
they do not establish connector completeness.

On 2026-09-24, the operator clarified that G2 has no time expiry; its caps remain
40 requests/navigation steps, 25 pages, up to ten invoice PDFs total at 25 MiB
each / 250 MiB aggregate,
the same personal account and aggregate installation scope, the observed portal
origin only, and no screenshots/callbacks/ingestion. The authenticated combined
view reports eight installations and 222 documents in a single accessible table,
with no visible pagination. An exact-day range test returned eight matching rows.
These observations do not prove underlying completeness, date semantics, stable
vendor-native identity, API availability or automation permission. No additional
PDF was downloaded. Keep the manifest `design_only`; no live transport
implementation exists. See sibling
`billharbor/docs/contracts/d6-oekostrom-readiness.md`.

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

## 0.3.0 engine compatibility preparation — 2026-09-23

Aligned the catalog package dependency, frozen lock and exported `__version__`
with BillHarbor 0.3.0. The 12-test frozen catalog suite passes locally against
engine commit `44c6dd8b2b75e282c16feaf53c808c80f1c5d580`. Before tagging, require that
engine commit's green CI and immutable v0.3.0 release, set repository variable
`BILLHARBOR_REF` to the full engine commit, then require green cross-repository
catalog CI. No live vendor, credential, document, deployment or receiver action
occurred; G1/G2 remain closed.

## v0.3.0 publication — 2026-09-23

Catalog commit `2b55e5720a6078c60d49a0f828f9410f9a3035a9` passed pinned
cross-repository CI run `35870502057` against released BillHarbor commit
`44c6dd8b2b75e282c16feaf53c808c80f1c5d580`. Annotated tag `v0.3.0` resolves
to that catalog commit; release run `35870777091` passed and published wheel
SHA-256 `364dece35ea8083ac7a7e6a9180a11be4d1ab398f2bdd4d9e22665010fc8cba5`.
The catalog remains synthetic and `design_only`. No vendor access, credential,
real document, callback or deployment occurred; G1/G2 remain closed.

## Ökostrom D6 readiness — 2026-09-23

The operator selected Ökostrom as the first D6 candidate. The catalog package and
manifest remain `design_only`; connector code still reads invented fixtures only.
Official public pages advertise invoice PDF/CSV downloads, switching among
multiple installations and downloadable PV feed-in statements. No authenticated
portal behavior, selector, origin or API was tested. The portal requires customer
registration/activation and credentials, so it is not an unauthenticated route.

The operator confirmed that the intended personal-project use is permitted; the
own-purpose G1 decision is recorded. The operator approved the proposed five-
minute, no-download session check for one personal account. The official login
page is open at `https://mein.oekostrom.at/`; the operator is entering credentials
directly and the authenticated check has not started. Installation enumeration
and operator selection are the stop point. The catalog remains `design_only`. A
vendor inquiry draft is in the sibling BillHarbor D6 readiness record; it has not
been sent. No documents, callback, deployment or accounting action occurred.

## Synthetic discovery conformance — 2026-09-24

Fixture connectors retain the released connector-v2 signature and inclusive
issue-date filtering. Opaque checkpoints now bind the selected scopes and date
window; changed-filter replay fails rather than skipping records. Added replay and
empty-terminal-page coverage. Kind filtering stays engine-side until a deliberate
connector/manifest v3. The catalog remains `design_only`.

Python compilation passes. Focused pytest was blocked by sandbox denial of uv's
global cache. Git reports `2ecb6ab`, six commits ahead, plus a truncated-pack
warning; no history was rewritten, no commit was created and nothing was pushed.

## Browser implementation candidate — 2026-09-30

Added the separate SDK v2 `oekostrom_at.browser.BrowserConnector` and asynchronous
isolated Playwright factory. Reviewed behavior and integration contracts are in
`docs/oekostrom-browser.md`. Browser selectors and login data are entirely invented;
constructor accepts only explicit loopback profiles. Default manifest/entrypoint
remain fixture-only and `design_only`. No authenticated access, real invoice,
secret, callback, deployment, commit, push or release occurred.

Actual Chromium synthetic integration coverage now exercises login, scopes,
original PDF bytes, inclusive date filtering, continuation/restart, malformed
originals, duplicates, unsupported pagination, challenge handling, origin guard
and download limits. Downloads are size-checked after completion: a worker disk
quota remains necessary. D6 still requires evidence-backed identity, date meaning,
completeness, actual selectors, automation permission and live acceptance. The
existing historical release pins are unchanged; new implementation is uncommitted.

Verification: full catalog suite **20 passed**, including four actual Chromium
browser tests with Playwright 1.63.0; `git diff --check` passed. Browser binaries
were downloaded into `/tmp/billharbor-playwright` for invented-loopback tests.
