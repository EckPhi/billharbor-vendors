# Agent instructions

Read README.md, NEXT_STEPS.md and the linked design documents before planning or
editing implementation. Preserve the separate engine/catalog/receiver boundaries.
Current work is design and file organization only; runtime implementation has not
started. Use invented synthetic fixtures when implementation is authorized.
No authenticated vendor/API access, real financial/personal documents, credential
access, production deployment or accounting writes without an explicit applicable
gate. Public documentation research is allowed. Never commit secrets, sessions,
real documents or unsanitized captures. Recording is off by default.
Record dependency versions, licenses, maintenance, data flow and rollback before
adoption. Update NEXT_STEPS.md with verified state, blockers and Git/publication
state at handoff. Do not modify concurrent bookkeeping receipt-processing work.

Read docs/vendor-definition.md. Catalog packages are executable dependencies;
review and pin immutable releases. Never embed tenant, company or credential
values. Synthetic fixture verification is not proof of live vendor support.

Commit completed work at handoff. Do not create manual development tags: branch
push workflows own versioned alpha/beta builds. Create explicit version tags for
release builds only when separately requested. Do not push or publish unless
separately requested. Preserve unrelated concurrent changes outside the commit.
