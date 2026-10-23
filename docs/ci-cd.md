# CI/CD

GitHub Actions tests the catalog's frozen lock, builds the independent SDK,
synthetic plugin and optional aggregate catalog wheels, then validates packaged
metadata and imports. A clean wheel-only proof installs SDK + synthetic plugin
without application/catalog distributions. Wheel-only Python checks use `-I`
to exclude the workspace and `PYTHONPATH`: uv environment isolation alone does
not prevent sibling checkout directories from appearing as namespace packages.
The application/catalog absence assertions remain mandatory. Pull
requests and pushes to `main` retain both wheels and checksums for 14 days as
build evidence.

Because both repositories are private, configure:

- committed `.github/billharbor-sdk-ref`: one exact 40-character reviewed
  engine-repository commit containing `packages/connector-sdk`;
- repository secret `BILLHARBOR_READ_TOKEN`: a fine-grained read-only token with
  contents access to `EckPhi/billharbor` and no other permission.

The workflow validates the committed SHA and verifies the checkout resolves
exactly to it; it never
follows BillHarbor `main`. Rotate or revoke the token through GitHub. Never put its
value in this repository, logs or workflow inputs.

The release tag is authoritative for the aggregate package version. Before frozen
installation/testing, `tools/prepare_release.py` stamps project metadata, exported
`__version__` and only the aggregate lock self-entry in the disposable Actions
checkout. The committed `0.5.0.dev2` remains the local/non-release fallback. No
version-bump commit or rewritten tag is required; preserve all existing tags.
Supported canonical tags are `vMAJOR.MINOR.PATCH` with optional `aN`, `bN`, `rcN`,
or `.devN`; leading zeros, normalization aliases, local labels and combined
suffixes are rejected. The release wheel's metadata and exported version must
match the tag before publication. Reproducing a tagged artifact locally requires
running the same preparation command in a disposable checkout first.

SDK and reference synthetic plugin versions/dependencies remain independent and
unchanged; the four new fixture wheels use their release version.
Frozen catalog/manifest versions and engine compatibility ranges also remain
unchanged; choosing a release version does not imply a compatibility change.
This uses Python's standard library only, with no dependency adoption, credentials
or additional network/data flow. Rollback restores the preceding workflow/source
and immutable artifacts; never retag published source.

Pushing a supported release tag creates a GitHub Release containing
the aggregate catalog wheel, independent synthetic plugin wheel, checksums and
`BILLHARBOR-SDK` provenance containing the reviewed source commit and rebuilt SDK
wheel digest. The SDK wheel is independently distributed in the engine release;
it does not require installing or synchronizing the application version. It does not publish
to PyPI, deploy a worker, install a live connector or access a vendor. The tag
workflow alone receives `contents: write` for the current catalog repository.

Actions are pinned to immutable release commits. uv is pinned to 0.7.19 to match
the lock evidence. Dependency upgrades require reviewed locks and workflow
changes in both repositories.

For the 0.4.0.dev1 candidate, CI and release jobs install the exact reviewed
browser test pins into the frozen environment, install matching Chromium, and
require zero skipped tests in the JUnit report. Wheel-only verification also
imports the packaged browser/identity modules and validates the separate
synthetic browser manifest. That profile remains `design_only` and rejects live
origins. Release sequencing is engine release first, then the reviewed committed SDK source ref,
green catalog CI, then matching catalog prerelease tag.


The source pin is reviewed repository content, not a mutable repository variable.
A new application version alone does not require a plugin rebuild: compatibility
is declared by the plugin's SDK pin and engine range. Update the SDK source pin
only after reviewing the SDK source/artifact and running catalog conformance.
The existing read-only private checkout token remains a CI build input; plugin
runtime artifacts contain no token, checkout, application wheel or Git source.

## Public vendor store

Release builds publish channel indexes and all retained plugin wheels to Pages
in the same workflow. The manual Pages action reconstructs those channels for
recovery or renewal; it takes no revision/lifetime inputs. See
[setup, renewal and rollback](vendor-store-pages.md). Nothing is published by
local implementation or verification alone.

## Automatic alpha, beta and final releases

Pushes to `develop` produce alpha prereleases; pushes to `main` produce beta
prereleases. Both use the source `MAJOR.MINOR.PATCH` base and suffix `aN` / `bN`,
where `N = github.run_number * 1000 + github.run_attempt` (attempts 1–999).
The exact push SHA is the release target. Explicit canonical `v*` tags (excluding `.postN`) retain
their version; only plain `vMAJOR.MINOR.PATCH` is stable/latest. `.postN` is rejected before building because the engine plugin version parser
does not support it. Other supported tag suffixes remain prereleases and never replace GitHub's latest stable release.
These builds stamp only disposable aggregate metadata, never commit version bumps.
The independent four fixture plugins get the release version; synthetic and SDK
versions remain independent. All five plugin wheels accompany the catalog release.

The release workflow builds/tests, creates the GitHub Release and reconstructs /
publishes Pages in the same run: `GITHUB_TOKEN` release/tag events do not trigger
a second workflow. Release and manual Pages runs share one non-cancelling
concurrency group covering build and deployment, with `queue: max` retaining
pending pushes rather than replacing an older pending run. Pages environment rules must
allow `develop`, `main` and approved version tags; restricting that environment to
`main` blocks the other release channels. Required environment reviewers remain
an operator setting. Publication failures leave immutable release assets available
for manual Pages reconstruction; existing releases are never overwritten.

Each release includes an immutable `store-release.json` recording channel,
sequence and plugin filenames/digests. Store reconstruction paginates GitHub's
release list, verifies all retained assets plus the legacy reviewed manifest,
and selects the largest sequence per channel. A delayed older release cannot
promote older packages. All wheel URLs retain digest-addressed Pages paths.
The source run ID times 1000 plus attempt orders release selection independently
of completion order; publication revisions use UTC microseconds captured once
inside the serialized publisher, with all index timestamps derived from that
revision. This assumes GitHub-hosted runners' UTC clocks do not regress between
serialized runs. Every reconstruction, including manual recovery, has a new
revision/digest. No package code is executed to construct store metadata.

The separate alpha/beta/stable feeds use `/alpha/index.json`, `/beta/index.json`
and `/stable/index.json` when those channels exist. Legacy `/index.json` follows
beta once available (stable fallback before the first beta; seeded synthetic
fallback before either). A stable tag never silently switches the legacy beta
subscription. Exact index trust approval, plugin installation, instance deployment,
and live vendor activation remain explicit operator actions. A successful release
does not update an instance's reviewed index digest.
