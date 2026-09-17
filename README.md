# BillHarbor Vendors

Separately versioned vendor definitions and connector packages for BillHarbor.
Initial targets: Amazon Business and oekostrom.at.

Status: design only. No live-verified connector, runtime package or schema yet.

- [Vendor-definition specification](docs/vendor-definition.md)
- [Next steps](NEXT_STEPS.md)
- [BillHarbor engine and integration design](../billharbor/README.md)

Each future vendor package contains TOML metadata, small typed Python connectors,
operator instructions and invented fixtures. Credentials, account bindings,
browser sessions and downloaded documents never belong in this repository.
Engine SDK/schema versions will be pinned; catalog content will be reviewed and
installed during builds rather than fetched/executed dynamically during a run.
