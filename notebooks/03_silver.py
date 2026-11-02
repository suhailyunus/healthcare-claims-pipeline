# Databricks notebook source
# MAGIC %md
# MAGIC # 03 Silver
# MAGIC Types and validates each bronze table. Rows that fail any rule go to a `_quarantine`
# MAGIC table with the list of rules they failed. Beneficiary runs first because the claims
# MAGIC check every member ID against it.

# COMMAND ----------

import os, sys
sys.path.insert(0, os.path.abspath("../src"))

from claims_pipeline import config
from claims_pipeline.silver import build_silver

# COMMAND ----------

results = [build_silver(spark, "beneficiary")]
members = spark.table(f"{config.SILVER}.beneficiary")
for table in config.CLAIM_TABLES:
    results.append(build_silver(spark, table, members))

for r in results:
    print(f"{r['table']:<12} bronze {r['bronze']:>10,}  silver {r['silver']:>10,}  "
          f"quarantined {r['quarantined']:>8,}  {r['failures_by_rule'] or ''}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Quality log for this run
# MAGIC Every rule appears, including those with zero failures, so a clean result is
# MAGIC distinguishable from a rule that never ran.

# COMMAND ----------

display(spark.sql(f"""
    WITH latest AS (
        SELECT table_name, max(run_at) AS run_at FROM {config.QUALITY_LOG} GROUP BY table_name
    )
    SELECT table_name, rule, failed_rows, bronze_rows, silver_rows, quarantined_rows
    FROM {config.QUALITY_LOG} JOIN latest USING (table_name, run_at)
    ORDER BY table_name, failed_rows DESC
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Typed columns
# MAGIC Dates should show as `date`, amounts as `decimal(14,2)`, and IDs as `string`.

# COMMAND ----------

display(spark.table(f"{config.SILVER}.inpatient").select(
    "BENE_ID", "CLM_ID", "CLM_FROM_DT", "CLM_THRU_DT", "CLM_PMT_AMT").limit(10))
print(dict(spark.table(f"{config.SILVER}.inpatient").dtypes)["CLM_FROM_DT"])
