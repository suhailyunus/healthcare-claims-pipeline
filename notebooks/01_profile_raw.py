# Databricks notebook source
# MAGIC %md
# MAGIC # 01 Profile raw files
# MAGIC Look at each file before deciding anything about it. Use the output to tick off the
# MAGIC confirmations in `docs/data_sources.md` and to fill in `docs/definitions.md`.

# COMMAND ----------

import os, sys
sys.path.insert(0, os.path.abspath("../src"))

from pyspark.sql import functions as F
from claims_pipeline import config
from claims_pipeline.ingest import read_raw

# COMMAND ----------

display(dbutils.fs.ls(config.LANDING_PATH))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Shape, columns, and sample rows
# MAGIC If a file shows a single wide column, `DELIMITER` in `config.py` is wrong.

# COMMAND ----------

raw = {name: read_raw(spark, pattern) for name, pattern in config.SOURCE_FILES.items()}

for name, df in raw.items():
    print(f"{name}: {df.count():,} rows, {len(df.columns)} columns")
    print("  " + ", ".join(df.columns[:25]) + (" ..." if len(df.columns) > 25 else ""))

# COMMAND ----------

display(raw["inpatient"].limit(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Null rate and distinct count per column
# MAGIC Columns with one distinct value per row are candidate keys. Columns that are always
# MAGIC null can be ignored.

# COMMAND ----------

def profile(df):
    total = df.count()
    stats = df.agg(
        *[F.sum(F.col(c).isNull().cast("int")).alias(f"{c}__nulls") for c in df.columns],
        *[F.approx_count_distinct(c).alias(f"{c}__distinct") for c in df.columns],
    ).first()
    rows = [
        (c, total, stats[f"{c}__nulls"], round(stats[f"{c}__nulls"] / total, 4), stats[f"{c}__distinct"])
        for c in df.columns
    ]
    return spark.createDataFrame(rows, "column string, row_count long, nulls long, null_rate double, approx_distinct long")

display(profile(raw["inpatient"]))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Grain check
# MAGIC Set `claim_key` to the claim ID column you found above. If rows > distinct claims,
# MAGIC the file is line-grain and row counts are not claim counts.

# COMMAND ----------

claim_key = "CLM_ID"  # CONFIRM from the column list above

for name in ("inpatient", "outpatient", "carrier"):
    df = raw[name]
    if claim_key in df.columns:
        rows, claims = df.count(), df.select(claim_key).distinct().count()
        print(f"{name}: {rows:,} rows, {claims:,} distinct claims, {rows / claims:.2f} rows per claim")
    else:
        print(f"{name}: no column named {claim_key}")
