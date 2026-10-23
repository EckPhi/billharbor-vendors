# Vendor stores on GitHub Pages

Successful release builds construct and publish the complete retained store in
the same workflow. Push `develop` for alpha, `main` for beta, or a supported
canonical version tag for an explicit release. Plain `vMAJOR.MINOR.PATCH` is
stable; `.postN` is unsupported by the engine plugin parser and rejected.
Local implementation and tests do not publish anything.

## Setup and acceptance

1. Push reviewed changes under publication authorization and require successful
   cross-repository tests against the committed immutable SDK pin. The existing
   read-only SDK checkout token remains necessary; no token values belong in Git.
2. Set **Settings → Pages → Build and deployment → Source: GitHub Actions**.
   Confirm public distribution of these proprietary fixture wheels is permitted.
   A private repository requires a plan supporting Pages; repository privacy does
   not make its public Pages site private. Use HTTPS.
3. Permit the pinned checkout/upload/deploy actions and allow `develop`, `main`
   and approved version tags in the `github-pages` environment. A main-only rule
   blocks alpha/tag releases. Required reviewers may pause publication.
4. Keep all GitHub Release wheels and `store-release.json` ledgers permanently.
   The seed `.github/vendor-store.json` also retains the original synthetic wheel
   and its reviewed digest. Missing or changed historical assets fail closed.
5. After release publication, inspect the run summary's index digest and fetch
   the desired index using `Accept-Encoding: identity`. Verify its exact bytes,
   direct wheel URLs and application compatibility. Pages success alone does not
   prove BillHarbor acceptance. Approve the new exact digest in BillHarbor before
   installing a plugin; publication never changes instance trust automatically.

Default feeds are:

| Feed | URL | Store ID |
|---|---|---|
| Alpha | `https://eckphi.github.io/billharbor-vendors/alpha/index.json` | `billharbor-vendors-alpha` |
| Beta | `https://eckphi.github.io/billharbor-vendors/beta/index.json` | `billharbor-vendors` |
| Stable | `https://eckphi.github.io/billharbor-vendors/stable/index.json` | `billharbor-vendors-stable` |

A channel exists once its first release succeeds. Legacy `/index.json` is
byte-identical to beta once beta exists. Before beta it exposes stable under the
legacy store ID, or the seeded synthetic release before stable exists. Separate
channel store IDs allow side-by-side subscriptions. Approved publisher remains
`billharbor`, approved origin `https://eckphi.github.io`, target runtime Python
`3.13`. Custom domains/repository renames require reviewed base URL/trust changes.

## Retention, renewal and recovery

Every release includes an immutable ledger with channel, ordering sequence and
wheel filenames/digests. Publication paginates release history, verifies every
retained wheel, and copies it to `packages/<sha256>/<filename>`. The highest
release sequence wins per channel, so delayed older builds cannot replace newer
packages. Never replace bytes under an existing distribution/version or delete
historical release assets. Enable GitHub immutable releases where available.

Release and manual workflows share one serialized non-cancelling concurrency
group with `queue: max`, which retains pending runs. Each publication captures a
UTC-microsecond revision once and derives index timestamps from it, with a 90-day
validity. This assumes GitHub-hosted runner clocks do not regress between runs.
Every reconstruction changes the index digest and requires trust review.

For recovery or renewal, run **Publish synthetic vendor store** on `main` after
at least one successful ledger-bearing release. It takes no revision/lifetime
inputs and reconstructs all channels without discarding historical wheels. A
failed Pages step can be recovered this way after its release assets succeeded.
Never overwrite an existing release to recover a Pages failure.

Rollback uses earlier reviewed installation locks explicitly; existing executions
retain their original provenance. Disable publication to stop future changes,
while preserving historical assets and URLs. Vendor activation, live access and
application deployment remain separately gated.

## Local verification

Offline helper tests cover branch identities, stale release selection, distinct
channel IDs, root compatibility, revisions, retained bytes and path/digest safety:

```sh
python3 -m unittest discover -s tests -p test_channel_release.py -v
python3 -m unittest discover -s tests -p test_pages_store.py -v
```

No new dependency, action pin or PAT is adopted by this release-channel change.
See [CI/CD](ci-cd.md) and [dependency decisions](dependencies.md).

Official references: [custom Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages),
[Pages visibility](https://docs.github.com/en/pages/getting-started-with-github-pages/about-github-pages),
[workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency?apiVersion=2022-11-28).
