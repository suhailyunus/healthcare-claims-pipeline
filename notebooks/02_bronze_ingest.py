# Databricks notebook source
# MAGIC %md
# MAGIC # 02 Bronze ingest
# MAGIC Lands each raw file as a Delta table, unchanged, with load metadata.

# COMMAND ----------

import os, sys
sys.path.insert(0, os.path.abspath("../src"))

from claims_pipeline import config
from claims_pipeline.ingest import ingest_to_bronze

# COMMAND ----------

for table, pattern in config.SOURCE_FILES.items():
    rows = ingest_to_bronze(spark, table, pattern)
    print(f"{config.BRONZE}.{table}: {rows:,} rows")
