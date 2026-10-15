"""Bronze layer: land raw files as Delta tables without interpreting them.

Every column is read as a string so that nothing is silently coerced or dropped.
Typing and validation happen in silver, where failures can be quarantined and counted.
"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from claims_pipeline import config


def read_raw(spark: SparkSession, file_pattern: str) -> DataFrame:
    """Read one source file (or glob) from the landing volume, all columns as strings."""
    return (
        spark.read.option("header", True)
        .option("sep", config.DELIMITER)
        .option("inferSchema", False)
        .csv(f"{config.LANDING_PATH}/{file_pattern}")
    )


def add_load_metadata(df: DataFrame) -> DataFrame:
    """Record where and when each row was loaded, for lineage and reconciliation."""
    return df.withColumn("_source_file", F.col("_metadata.file_path")).withColumn(
        "_loaded_at", F.current_timestamp()
    )


def ingest_to_bronze(spark: SparkSession, table: str, file_pattern: str) -> int:
    """Load one source into its bronze table and return the row count written."""
    df = add_load_metadata(read_raw(spark, file_pattern))
    target = f"{config.BRONZE}.{table}"
    df.write.format("delta").mode("overwrite").option("overwriteSchema", True).saveAsTable(
        target
    )
    return spark.table(target).count()
