"""
Simulated multi-source connectors.

Each module in this package returns a deterministic list of
`SourceRecord` objects for one external system (ERP, purchase orders,
invoices, logistics, warehouse, telemetry, financing).

Design rule (09_RECONCILIATION_ENGINE.md):
"For the hackathon, simulate these sources with deterministic
JSON/CSV datasets."

All datasets here reference the shared demo asset ID(s) below so they
can be reconciled against one another. AST-1001 is used as the primary
demo asset since the docs don't specify another canonical ID
(16_SOURCE_INDEX.md instructs us to state this as an implementation
decision, not an official requirement).
"""

DEMO_ASSET_ID = "AST-1001"

# A second asset is included purely so tests/fixtures can prove that
# reconciliation is asset-scoped and doesn't leak across assets.
SECONDARY_DEMO_ASSET_ID = "AST-1002"
