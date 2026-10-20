# BillHarbor synthetic reference vendor

No real vendor exists. This offline reference reads explicitly invented, digest-pinned
fixtures using connector v2. Stable ID: `billharbor_synthetic`; it never impersonates
a real vendor and never authorizes live access. `design_only` is retained because
the frozen manifest requires reviewed network origins for higher maturity.

Two installation scopes contain four distinct invented originals (invoice, credit
note and settlement). Dates are inclusive; use page size one to exercise pagination.
The shared connector binds checkpoints to scopes/date filters, rejects duplicates and
invalid PDF signatures, respects cancellation and preserves original bytes. Existing
engine deduplication/revalidation handles repeat and changed-byte conflict proofs.

Synthetic credentials in BillHarbor's UI exercise custody only: this offline source
does not authenticate them or contact a portal. No account values belong here.
A separate browser proof must exercise actual synthetic login/session recovery.

No dependencies are added: reuse the catalog's exact pinned BillHarbor SDK/runtime
and build/test dependencies. License: Proprietary, matching the containing package.
Maintenance: BillHarbor catalog maintainers. Data flows from packaged fixture to
bounded artifact publication and BillHarbor's durable outbox; receiver simulation
belongs outside this package. Rollback selects the prior immutable catalog artifact;
do not change existing reference identities or erase retained originals/deliveries.
