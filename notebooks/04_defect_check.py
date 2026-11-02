# Databricks notebook source
# MAGIC %md
# MAGIC # 04 Defect check
# MAGIC The synthetic claims are cleaner than real data, so a clean silver run proves little.
# MAGIC This notebook breaks about 1% of inpatient rows on purpose, in seven known ways, runs
# MAGIC the same silver rules, and reports how many of each defect were caught.
# MAGIC Nothing here writes to the silver tables.

# COMMAND ----------

import os, sys
sys.path.insert(0, os.path.abspath("../src"))

from claims_pipeline import config, defects, silver

# COMMAND ----------

bronze = spark.table(f"{config.BRONZE}.inpatient")
members = spark.table(f"{config.SILVER}.beneficiary")

dirty = defects.inject(bronze, rate=0.01, seed=42).cache()
prepared, rules = silver.prepare_claims(dirty, members)
valid, quarantined = silver.split(prepared, rules)
quarantined = quarantined.cache()

print(f"rows after injection: {dirty.count():,}  "
      f"silver: {valid.count():,}  quarantined: {quarantined.count():,}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Recall per defect type
# MAGIC `recall` is caught / injected. The last row counts clean rows that were quarantined
# MAGIC anyway; on this data it should match the inpatient quarantine count from notebook 03.

# COMMAND ----------

display(defects.recall_report(quarantined, dirty))
