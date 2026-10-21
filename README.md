# BillHarbor Vendors

Separately versioned vendor definitions and connector packages for BillHarbor.
Reference vendor: `billharbor_synthetic`, an entirely invented offline source for
completing the application. Amazon Business and oekostrom.at remain deferred real
vendor targets. See [synthetic reference](vendors/billharbor_synthetic/README.md).

Status: v0.3.0 synthetic connector packages are released; local 0.4 discovery
hardening is in progress. A loopback-only browser candidate and exact-label identity policy are verified
with invented fixtures. No live-verified connector or deployment exists yet.

Ökostrom is the operator-selected first D6 candidate. Its package remains
`design_only`: public pages advertise invoice PDF/CSV downloads, multiple Anlagen
and PV feed-in PDFs. The operator confirmed personal-project use is permitted and
manually authenticated to their own account. A bounded observation showed eight
installations and 222 documents in the combined view; no underlying completeness,
stable native identity, supported API or automation permission is established.
Six distinct PDFs and two duplicate copies were downloaded for operator inspection
and remain outside Git; they do not prove connector completeness. The catalog
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

The synthetic reference now has an independently installable wheel depending only
on `billharbor-connector-sdk==0.1.0`. The optional aggregate catalog utility no
longer depends on the BillHarbor application; engine integration imports exist
only in cross-boundary tests. Amazon and Ökostrom remain deferred.

Each vendor package contains TOML metadata, small typed Python connectors,
operator instructions and invented fixtures. Credentials, account bindings,
browser sessions and downloaded documents never belong in this repository.
Engine SDK/schema versions will be pinned; catalog content will be reviewed and
installed during builds rather than fetched/executed dynamically during a run.

Ökostrom uses a versioned exact `Bezeichnung` source key scoped by installation
and kind; the engine adds account binding scope. Duplicate labels fail closed.
Legacy synthetic connector identities remain unchanged. See
[browser candidate](docs/oekostrom-browser.md) for limitations and rollback.

## Optional vendor store hosting

A manual GitHub Pages workflow is prepared for the synthetic store. See
[Pages setup and BillHarbor registration](docs/vendor-store-pages.md) for GitHub
settings, reviewed release prerequisites, public distribution, renewal and rollback.
No site has been published by this local implementation.
