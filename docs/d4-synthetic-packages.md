# D4 synthetic vendor packages

The 0.3.0 catalog candidate keeps both packages `design_only`. Their
`vendor-definition/2` manifests remain the versioned configuration boundary;
empty reviewed origins and unresolved discovery fields forbid live execution.
The connectors read only packaged `vendor-synthetic/1` JSON and do not call an
Amazon API or open the Ökostrom portal. No new runtime dependency was adopted.

| Package | Invented scope and document coverage |
|---|---|
| Amazon Business DE | Two legal-entity shaped organization scopes; invoice and credit note; the same native invoice ID in both scopes |
| Ökostrom AT | Two installation scopes; supply invoice, credit note and feed-in settlement |

The fixture reader validates the fixture version, typed scope membership,
document kind and uniqueness of `(scope kind, scope ID, kind, native ID)`.
It derives the SDK source identity from that full tuple, so a repeated vendor ID
under another entity cannot alias an original or outbox document. Discovery is
restricted to explicit known scopes and issue-date windows. Every document has
typed amount, currency, invoice-number and date observations with source paths;
the original is a distinct invented PDF byte string. The amount sign remains
an observation, not an accounting instruction.

Local direct lifecycle verification on 2026-09-22 discovered and fetched 3/3
Amazon and 3/3 Ökostrom documents with unique source identities and the expected
per-type coverage. Python compilation and whitespace validation passed. The
pytest suite could not finish in this sandbox: collection stalled, while a fresh
uv cache could not fetch build requirements because network DNS was unavailable.
Run the complete catalog and cross-repository suites in a normal CI environment
before release. Do not infer API eligibility, portal selectors or real document
coverage from these fixtures.
