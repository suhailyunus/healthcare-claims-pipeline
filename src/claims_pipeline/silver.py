"""Silver layer (Week 2): typed, validated tables. Failures go to quarantine.

Write this only after the Week 1 confirmations in docs/data_sources.md are ticked off:
column names, date format, and file grain all come from the raw profile.

Planned rules per claims table (see quality.Rule):
  - claim key and member key are present
  - member key exists in the beneficiary table
  - from date <= through date, and both parse
  - payment and charge amounts parse as numbers and are not negative
  - no duplicate (claim key, line number)
"""
