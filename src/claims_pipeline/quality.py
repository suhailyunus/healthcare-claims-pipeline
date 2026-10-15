"""Data quality rules that split a DataFrame into valid rows and quarantined rows.

A rule is a name plus a SQL expression that is TRUE when the row is acceptable.
Rows failing any rule go to quarantine with the list of rules they failed, so bad data
is counted and explainable instead of dropped.
"""

from dataclasses import dataclass

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


@dataclass(frozen=True)
class Rule:
    name: str
    passes_when: str  # SQL expression, TRUE means the row is acceptable


def apply_rules(df: DataFrame, rules: list[Rule]) -> tuple[DataFrame, DataFrame]:
    """Return (valid, quarantined). Quarantined rows carry a `_failed_rules` array."""
    if not rules:
        return df, df.limit(0).withColumn("_failed_rules", F.array().cast("array<string>"))

    # A NULL result (for example a comparison against a NULL column) counts as a failure.
    failed = F.array(
        *[
            F.when(F.coalesce(F.expr(r.passes_when), F.lit(False)), F.lit(None)).otherwise(
                F.lit(r.name)
            )
            for r in rules
        ]
    )
    checked = df.withColumn("_failed_rules", F.array_compact(failed))
    valid = checked.filter(F.size("_failed_rules") == 0).drop("_failed_rules")
    quarantined = checked.filter(F.size("_failed_rules") > 0)
    return valid, quarantined


def summarize_failures(quarantined: DataFrame) -> DataFrame:
    """Row count per failed rule, for the quality report."""
    return (
        quarantined.select(F.explode("_failed_rules").alias("rule"))
        .groupBy("rule")
        .count()
        .orderBy(F.desc("count"))
    )
