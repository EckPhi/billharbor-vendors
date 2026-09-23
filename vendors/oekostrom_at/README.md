# oekostrom.at

Status: `design_only`. The connector class reads invented local fixtures only; it
does not implement portal login, selectors, browser actions, API calls or downloads.

The operator selected this vendor as the first D6 candidate. Public portal
materials advertise invoice filtering and PDF/CSV downloads, multiple installation
selection, and PV feed-in settlement PDFs. These claims are not authenticated
verification. Portal access requires customer registration/activation and
credentials. G1 remains blocked until the account holder's own-purpose use and
document handling through BillHarbor are explicitly resolved under the current
portal terms. See the [D6 readiness record](../../../billharbor/docs/contracts/d6-oekostrom-readiness.md).

The intended initial transport is browser-based only after authorized discovery.
Each installation or contract is an explicit scope. Supply invoices and PV
feed-in settlements retain distinct document kinds. Exact origins, authentication,
MFA, selectors, pagination, dates and document identity remain unverified.
