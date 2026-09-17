# Amazon Business DE

Status: `design_only`. The connector class reads invented local fixtures only; it
does not implement Amazon authentication, API calls, browser behavior or downloads.

The intended transport is the official buyer Document and Reconciliation APIs
when the specific account is eligible. Marketplace, legal-entity scope and issuer
identity remain distinct. No browser fallback is implied. Exact roles, credentials,
origins, pagination, dates and document identity require authorized verification.

