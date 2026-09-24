# BillHarbor Vendors

Separately versioned vendor definitions and connector packages for BillHarbor.
Initial targets: Amazon Business and oekostrom.at.

Status: local v0.2 connector-SDK migration and packaged synthetic fixtures are
implemented for conformance; no live-verified connector, vendor access or
deployment yet.

Ökostrom is the operator-selected first D6 candidate. Its package remains
`design_only`: public pages advertise invoice PDF/CSV downloads, multiple Anlagen
and PV feed-in PDFs. The operator confirmed personal-project use is permitted and
manually authenticated to their own account. A bounded observation showed eight
installations and 222 documents in the combined view; no underlying completeness,
stable native identity, supported API or automation permission is established.
One invoice PDF was previously verified and remains outside Git. The catalog
stays `design_only`; see BillHarbor's
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
