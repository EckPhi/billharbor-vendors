# CI/CD

GitHub Actions tests the catalog's frozen lock, builds both repositories and
validates the packaged catalog against the packaged BillHarbor schema. Pull
requests and pushes to `main` retain both wheels and checksums for 14 days as
build evidence.

Because both repositories are private, configure:

- repository variable `BILLHARBOR_REF`: the exact 40-character commit SHA of the
  reviewed BillHarbor SDK/schema release;
- repository secret `BILLHARBOR_READ_TOKEN`: a fine-grained read-only token with
  contents access to `EckPhi/billharbor` and no other permission.

The workflow verifies the checkout resolves exactly to `BILLHARBOR_REF`; it never
follows BillHarbor `main`. Rotate or revoke the token through GitHub. Never put its
value in this repository, logs or workflow inputs.

Pushing a tag matching `v<project.version>` creates a GitHub Release containing
only the catalog wheel, its checksum and `BILLHARBOR-SDK` provenance containing
the reviewed engine commit and locally rebuilt wheel digest. It does not publish
to PyPI, deploy a worker, install a live connector or access a vendor. The tag
workflow alone receives `contents: write` for the current catalog repository.

Actions are pinned to immutable release commits. uv is pinned to 0.7.19 to match
the lock evidence. Dependency upgrades require reviewed locks and workflow
changes in both repositories.
