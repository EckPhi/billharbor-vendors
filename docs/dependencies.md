# Dependency decisions

Recorded 2026-09-17 for the synthetic D1 catalog foundation. No dependency in
this file authorizes live vendor access, deployment or runtime installation from
an unreviewed source.

| Package | Pin | License | Purpose and data flow | Rollback |
|---|---:|---|---|---|
| BillHarbor | `0.1.0` | Apache-2.0 | Connector SDK values and manifest validation. Synthetic fixtures and public manifests only; no network flow. The local uv source is for sibling-checkout conformance and is not a publication source. | Restore the preceding catalog lock and matching immutable BillHarbor artifact; no persistent-state migration. |
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
