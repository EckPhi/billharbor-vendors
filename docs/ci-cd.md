# CI/CD

GitHub Actions tests the catalog's frozen lock, builds the independent SDK,
synthetic plugin and optional aggregate catalog wheels, then validates packaged
metadata and imports. A clean wheel-only proof installs SDK + synthetic plugin
without application/catalog distributions. Pull
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

Pushing a tag matching `v<project.version>` creates a GitHub Release containing
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
