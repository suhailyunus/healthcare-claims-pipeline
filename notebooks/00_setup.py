# Databricks notebook source
# MAGIC %md
# MAGIC # 00 Setup
# MAGIC Creates the schemas and the landing volume. Safe to re-run.

# COMMAND ----------

import os, sys
sys.path.insert(0, os.path.abspath("../src"))

from claims_pipeline import config

# COMMAND ----------

for schema in config.SCHEMAS:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema}")

spark.sql(f"CREATE VOLUME IF NOT EXISTS {config.LANDING_VOLUME}")

print(f"Upload the CMS files to: {config.LANDING_PATH}")
