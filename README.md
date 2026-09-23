# BillHarbor Vendors

Separately versioned vendor definitions and connector packages for BillHarbor.
Initial targets: Amazon Business and oekostrom.at.

Status: local v0.2 connector-SDK migration and packaged synthetic fixtures are
implemented for conformance; no live-verified connector, vendor access or
deployment yet.

Ökostrom is the operator-selected first D6 candidate. Its package remains
`design_only`: public pages advertise invoice PDF/CSV downloads, multiple Anlagen
and PV feed-in PDFs, but the authenticated portal has not been observed. G1 is
blocked pending a documented terms decision because the current portal terms
restrict use to the user's own purposes, prohibit commercial use/data sharing with
third parties and require credential secrecy. See BillHarbor's
[Ökostrom D6 readiness record](../billharbor/docs/contracts/d6-oekostrom-readiness.md).

- [Vendor-definition specification](docs/vendor-definition.md)
- [Dependency decisions](docs/dependencies.md)
- [D4 synthetic vendor packages](docs/d4-synthetic-packages.md)
- [CI/CD](docs/ci-cd.md)
- [Next steps](NEXT_STEPS.md)
- [BillHarbor engine and integration design](../billharbor/README.md)

Frozen design-only manifest fixtures live under `vendors/`. Empty network origins
and `requires_verification` fields make them ineligible for live runs.

Each future vendor package contains TOML metadata, small typed Python connectors,
operator instructions and invented fixtures. Credentials, account bindings,
browser sessions and downloaded documents never belong in this repository.
Engine SDK/schema versions will be pinned; catalog content will be reviewed and
installed during builds rather than fetched/executed dynamically during a run.
