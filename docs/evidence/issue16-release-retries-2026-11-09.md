# Issue 16 catalog release retry preparation — 2026-11-09

Scope: invented synthetic fixtures and offline publication command tests. Based
on catalog develop commit `a27a91c9b4a1896595a336ef8a72669e48f171df`. No release,
tag, Pages dispatch, vendor access or deployment was performed by these tests.

The release uploader now verifies exact source/tag identity, retains a source
marker and compares existing assets before missing-only upload. Partial upload
failure and successful retry, immutable conflicts, wrong/missing markers,
annotated tags and non-404 metadata failures have synthetic regression coverage.
Explicit-tag ledgers derive issue time from the source commit and preserve the
run sequence across attempts; branch attempts remain separately versioned.
Ledgers publish last, after all referenced wheels. Pages-only recovery continues
to reconstruct retained releases without replacing assets.

Local verification: 11 release-asset tests, 6 channel-release tests and 4 Pages
store tests passed using Python's standard library. Tests use fake API responses
and invented wheel bytes, not credentials or real release assets. Existing
coverage retains historical wheel hashes/URLs, rejects altered bytes before
output, chooses the highest sequence and preserves separate channel identities.

Remote acceptance remains open in engine issue
[EckPhi/billharbor#16](https://github.com/EckPhi/billharbor/issues/16): native GitHub
execution, Pages branch/tag protections, published HTTP origin/expiry/digests,
SDK wheel equality and approved alpha/beta/stable publication/recovery need exact
run/artifact URLs. The engine task's metadata inspection found `github-pages`
restricted to main; this change does not alter remote environment settings.

No new dependency/action pin/license or credential scope. Existing pinned SDK
source and frozen runtime dependencies remain unchanged. Public synthetic
wheel/source metadata uses the existing Release/Pages data flow. Rollback
restores prior tooling while retaining immutable artifacts and installation
locks. Git/publication state and PR/run links belong in the PR handoff; do not
interpret local tests as successful remote publication.
