# Dependency decisions

Recorded 2026-09-17 for the synthetic D1 catalog foundation. No dependency in
this file authorizes live vendor access, deployment or runtime installation from
an unreviewed source.

| Package | Pin | License | Purpose and data flow | Rollback |
|---|---:|---|---|---|
| BillHarbor | `0.4.0.dev0` prerelease | Apache-2.0 | Connector SDK values, durable synthetic runner and manifest validation. Synthetic fixtures and public manifests only; no network flow. The local uv source is for sibling-checkout conformance and is not a publication source. | Restore the preceding catalog lock and matching immutable BillHarbor artifact; unfinished 0.3 engine executions must finish on 0.3 or restart on 0.4. |
| Hatchling | `1.32.0` | MIT | Build backend only; no runtime data flow. Matches the engine D1 build pin. | Build the preceding source revision with its frozen lock. |
| pytest | `9.1.1` | MIT | Test runner for synthetic catalog, manifest and connector fixtures only; no runtime dependency or network flow. | Run the preceding frozen test environment; no runtime or persistent-state impact. |
| actions/checkout | `v7.0.1` (`3d3c42e…`) | MIT | Checks out the catalog and exact private BillHarbor commit. The second checkout receives a fine-grained read-only token through GitHub Secrets. | Pin the preceding reviewed release commit; revoke the token to disable cross-repository CI. |
| astral-sh/setup-uv | `v10.1.0` (`bec219d…`) with uv `0.7.19` | MIT / Apache-2.0 or MIT | Installs pinned uv and may cache packages in GitHub Actions. Synthetic code/packages only; no vendor data. | Pin the preceding reviewed versions; the catalog lock remains authoritative. |
| actions/upload-artifact | `v6.0.0` (`b7c566a…`) | MIT | Node-24 artifact action retaining locally built wheels and checksums for 14 days. No secrets, sessions or documents are included. | Remove evidence upload or pin the preceding reviewed release. |

`uv.lock` freezes the development/test environment. During local cross-repository
work it resolves BillHarbor from the sibling checkout so one authoritative schema
and SDK are exercised. This mutable path is deliberately not sufficient for a
catalog release. Before publishing the catalog, replace or override it with an
independently released BillHarbor `0.1.0` artifact, record that artifact's SHA-256
and verify the wheel contains the frozen schemas. Catalog installation must occur
during image construction; no runtime Git or package installation is permitted.

BillHarbor `v0.1.0` is released at commit
`99bb2e5146f25e87471ec4ccbcd0d59a1597b445`. Its published wheel
`billharbor-0.1.0-py3-none-any.whl` has SHA-256
`c66548b576c21b7e2c30de1cba2fe4ebc5fbdfe72c443e54b345e5ba23d406e5`.
GitHub reports the same digest, and a clean local rebuild reproduced it exactly.
The catalog candidate wheel built against that release has SHA-256
`5be0a755a54baa0b9549ffe6d1afd57e19af2216d01a513a5e477bd382027523`.

## Local 0.2.0 candidate — 2026-09-18

The local catalog now targets BillHarbor `0.2.0` and connector SDK v2 so original
bytes cross the engine-owned artifact publication capability. BillHarbor remains
Apache-2.0 while this catalog distribution's package metadata remains Proprietary;
data flow remains synthetic fixture bytes into local durable test
storage with no network, credentials or live vendor data. Rollback is the paired
catalog/BillHarbor 0.1.0 release; do not mix a v2 catalog with the v1 engine.

The reviewed BillHarbor `v0.2.0` release is commit
`a69e7e59277183153232b6c57f1b7276d14751c4`; GitHub reports its published
wheel SHA-256 as
`734b5abce8b93ebf4077a1b94515e1074235597d7ec113b9522e3caccd7a988f`.
A clean local rebuild reproduced that digest. The released catalog wheel SHA-256 is
`840f48c73b351631538ba98b06d79b4795fd3fd0dd39013d23cedbf9d6878439`
for billharbor-vendors 0.2.0; the catalog release workflow independently rebuilt
and published that matching wheel. Its `BILLHARBOR-SDK` provenance record pins
the engine commit and wheel digest above.

## 0.3.0 release candidate — 2026-09-23

The catalog 0.3.0 candidate requires BillHarbor 0.3.0 and retains connector SDK
v2 plus `vendor-definition/2`. Local frozen conformance passed 12 tests against
engine commit `44c6dd8b2b75e282c16feaf53c808c80f1c5d580`. Publication requires that
exact engine commit to pass CI and become the immutable v0.3.0 release, followed
by catalog CI with `BILLHARBOR_REF` pinned to it. The release wheel digest replaces
this candidate reference after publication. No vendor, credential or document
network flow is introduced.

Publication completed from catalog commit
`2b55e5720a6078c60d49a0f828f9410f9a3035a9`. Released catalog wheel SHA-256 is
`364dece35ea8083ac7a7e6a9180a11be4d1ab398f2bdd4d9e22665010fc8cba5`.
The pinned BillHarbor release commit is
`44c6dd8b2b75e282c16feaf53c808c80f1c5d580`; its released wheel SHA-256 is
`d8682b44275f0012951cd7c6da5c42e82795d3935ea857f608b01a0509169018`.

## 0.4.0.dev0 prerelease — 2026-09-25

The catalog prerelease requires BillHarbor `0.4.0.dev0`, released from commit
`38aa403393d502b6d6a42424162b9625f77115f8`. Its published wheel SHA-256 is
`6aac950e3fa759ae1eb05c8de6fc91cddeee596f738737b7227dcd0586dd6529`.
The catalog remains synthetic and `design_only`; this update adds bound checkpoint
compatibility and no vendor, credential, document or network data flow. Roll back
as the matched catalog/engine 0.3.0 pair; do not mix catalog 0.4 with engine 0.3.

## 0.4.0.dev1 browser and label candidate — 2026-10-08

The catalog requires the separately released BillHarbor `0.4.0.dev1`. Its exact
commit and published wheel digest must be recorded before catalog publication;
`BILLHARBOR_REF` is the immutable cross-repository CI pin. No dependency upgrade
is introduced by this version bump.

Browser CI installs the engine's reviewed Playwright Python `1.63.0`
(Apache-2.0, Microsoft-maintained), greenlet `3.5.6` (MIT) and pyee `13.0.1` (MIT)
in the disposable test environment and installs its matching Chromium. These
are test-only additions to the frozen catalog environment, not catalog runtime
requirements. Runtime browser provisioning remains engine-owned. See the engine
[dependency evidence](../../billharbor/docs/dependencies.md) for browser revision,
image digest and maintenance evidence. Invented loopback HTML/PDF data flows
through the isolated browser into local engine artifacts; no live documents,
sessions, screenshots or credentials are retained by this change. Rollback uses
the preceding immutable engine/catalog pair and discards ephemeral browser state;
never alias existing source IDs across label/native policies automatically.

## Independent SDK and synthetic plugin — 2026-10-20

The `0.5.0.dev0` optional catalog utility depends on
`billharbor-connector-sdk==0.1.0` and `billharbor-synthetic==0.1.0.dev0`, rather
than the BillHarbor application. The synthetic distribution depends only on the
SDK. Both distributions require Python >=3.11; the reviewed service profile is
Python 3.13. SDK source is maintained by BillHarbor under Apache-2.0, with the
existing exact `jsonschema[format-nongpl]==4.26.0` validator dependency (MIT and
its existing reviewed transitive format validators). No new third-party library
is adopted. Package-level distribution versions are separate from frozen
connector SDK protocol versions (`billharbor-connector/1` and `/2`).

The proprietary synthetic plugin is maintained with this repository. Its data
flow is packaged invented JSON/PDF bytes → bounded SDK context → engine original
storage. It has no network origin, live vendor, credential resolution, session,
callback destination or account data. Source aliases preserve old public imports
while one implementation owns each SDK class. The catalog compatibility helper
subclasses the synthetic helper and selects catalog-owned legacy fixtures;
independent plugin imports never load the aggregate catalog or engine.

Installation requires reviewed immutable SDK/plugin wheel hashes and the exact
index/descriptor/artifact pins. `tools/build_synthetic_store.py` emits metadata
only and prints the generated index hash; running it grants no trust or live
permission. Rebuild artifacts and record hashes at the final release boundary.
Keep the previous image, immutable install locks and source fixture versions for
rollback. Existing immutable document identities are preserved; moved helper
sources change executable source-tree provenance, so historical execution and
checkpoint digests must not be rewritten or silently resumed as the new build.

## GitHub Pages store distribution — 2026-10-21

No Python/runtime dependency is adopted. `tools/build_pages_store.py` uses the
Python standard library and existing index builder; GitHub-hosted Ubuntu provides
Python and the GitHub CLI as build tools. They download only current-repository
reviewed release wheels into ephemeral runner storage, never execute them, and
publish only hash-verified synthetic wheel bytes plus index/checksum metadata.
The current-repository short-lived `GITHUB_TOKEN` has read-only contents access
in this job; no new PAT or private SDK checkout is needed.

| Action | Reviewed pin | License / maintenance | Flow and rollback |
|---|---|---|---|
| actions/upload-pages-artifact | v4.0.0 `7b1f4a764d45c48632c6b24a0339c27f5614fb0b` | MIT; GitHub Actions maintained | Packages the explicit site directory, excluding the checkout, into an ephemeral Pages artifact. Its nested upload-artifact is pinned to v4.6.2 `ea165f8d65b6e75b540449e92b4886f43607fa02`. Remove the manual workflow or restore the preceding reviewed pin to stop uploads. |
| actions/deploy-pages | v4.0.5 `d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e` | MIT; GitHub Actions maintained | Uses scoped Pages write and OIDC permissions to publish the prepared artifact. Disable publication or issue a higher reviewed index revision selecting retained prior wheels; never roll back to an expired index. |

Pins were checked against official [upload release](https://github.com/actions/upload-pages-artifact/releases/tag/v4.0.0)
and [deployment release](https://github.com/actions/deploy-pages/releases/tag/v4.0.5)
commit links on 2026-10-21. This is a reviewed version choice, not a claim that
these are the newest releases. Existing checkout pin is reused unchanged.
The manual workflow is inert until pushed and explicitly dispatched; public
publication of the proprietary synthetic wheel requires operator authorization.

## Four independent offline design-only plugins — 2026-10-23

`tools/build_vendor_plugins.py` builds Drei Austria, Lidl Connect Austria, netcup
and HORNBACH Austria in disposable projects using existing pinned Hatchling
1.32.0 (MIT, PyPA maintained). Each wheel bundles an exact copy of the existing
reviewed synthetic fixture helper and its vendor's frozen manifest/invented fixture;
no package is downloaded or source metadata modified. The only runtime dependency
is the existing `billharbor-connector-sdk==0.1.0`. Distribution code remains
Proprietary, matching the reviewed helper; the vendor manifest's Apache-2.0 field
continues to describe that definition, not a relicensing of the bundled helper.
BillHarbor catalog maintainers own all five offline packages. Generated package
versions follow the release input independently of frozen manifest versions.

Factories reject unknown options and unbound fixture digests, and never resolve
credentials. Input is packaged invented JSON (or an explicitly digest-bound local
synthetic fixture); output is neutral SDK observations and invented PDF bytes.
There is no network transport, credential flow, live support or additional runtime
dependency. Store generation reads wheel metadata/resources without importing code
and only admits the five reviewed plugin distribution/connector identities.

Retain prior immutable wheels and installation locks for rollback; select a prior
reviewed lock explicitly for new runs. Existing executions retain their source
provenance and must not resume under moved helper code. Revert the build/store
change or omit these four wheels to stop offering them; never replace bytes under
an existing published plugin version. Live vendor support remains separately gated.

## Release-channel automation — 2026-10-23

No dependency or action version was added. Standard-library release/store helpers
are maintained with this proprietary catalog. They reuse the recorded pinned
Hatchling/uv, checkout and Pages upload/deploy actions (GitHub-maintained, MIT).
Build inputs are immutable reviewed SDK source plus synthetic fixture source;
GitHub Release APIs supply immutable plugin wheels and JSON ledgers, which are
hashed before public Pages copying. Release ledgers and wheel metadata are read
as data; package code is not imported by the publisher. The existing scoped
GitHub token writes repository releases and Pages only; the existing fine-grained
SDK token remains checkout-only. Automatic alpha/beta publication broadens trigger
scope, not vendor/credential data access. Maintenance requires reviewing the
release workflows and retained ledgers together. Rollback disables automatic
publication, preserves all historical assets/URLs, and explicitly installs a prior
reviewed lock; never retag or overwrite published wheel bytes.
