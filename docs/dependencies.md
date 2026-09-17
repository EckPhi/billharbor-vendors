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
| actions/upload-artifact | `v4.6.2` (`ea165f8…`) | MIT | Retains locally built wheels and checksums for 14 days. No secrets, sessions or documents are included. | Remove evidence upload or pin the preceding reviewed release. |

`uv.lock` freezes the development/test environment. During local cross-repository
work it resolves BillHarbor from the sibling checkout so one authoritative schema
and SDK are exercised. This mutable path is deliberately not sufficient for a
catalog release. Before publishing the catalog, replace or override it with an
independently released BillHarbor `0.1.0` artifact, record that artifact's SHA-256
and verify the wheel contains the frozen schemas. Catalog installation must occur
during image construction; no runtime Git or package installation is permitted.
