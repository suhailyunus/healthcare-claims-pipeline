"""Gold layer (Week 3): analysis-ready tables and reconciliation.

Planned tables:
  - claim_header: one row per claim, across claim types
  - member_month: enrollment spine, one row per member per month
  - cost_utilization_pmpm: paid amount and claim counts per member per month

Planned reconciliation checks:
  - bronze rows = silver rows + quarantined rows, per table
  - sum of line amounts = header amount, per claim (where both exist)
  - total paid in gold = total paid in silver
"""
