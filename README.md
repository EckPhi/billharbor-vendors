# BillHarbor Vendors

Separately versioned vendor definitions and connector packages for BillHarbor.
Initial targets: Amazon Business and oekostrom.at.

Status: D1 packaged catalog and fixture-only connectors implemented for synthetic
conformance; no live-verified connector, vendor access or deployment yet.

- [Vendor-definition specification](docs/vendor-definition.md)
- [Dependency decisions](docs/dependencies.md)
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
