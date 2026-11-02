"""Inject known defects into clean claims data and measure how many the rules catch.

The synthetic claims are cleaner than production data: no duplicates, no orphans, no
malformed dates. To show the silver rules work, we break a small, known share of rows on
purpose, run the same validation, and report recall per defect type.

Each injected row carries `_injected_defect`. Columns starting with "_" are ignored by
the duplicate hash, so the label does not stop a copied row from matching its original.
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from claims_pipeline import config

LABEL = "_injected_defect"

# Defect name -> the rule that should catch it.
EXPECTED_RULE = {
    "missing_member_key": "member_key_present",
    "unknown_member": "member_known",
    "missing_claim_key": "claim_key_present",
    "malformed_date": "dates_parse",
    "dates_reversed": "service_dates_ordered",
    "malformed_amount": "amounts_parse",
    "duplicate_row": "not_duplicate_row",
}
DEFECTS = list(EXPECTED_RULE)


def inject(df: DataFrame, rate: float = 0.01, seed: int = 42) -> DataFrame:
    """Return df with roughly `rate` of rows defective, one defect type per chosen row.

    Duplicates are added as extra copies; every other defect modifies the row in place.
    """
    fmt = config.DATE_FORMAT
    picked = df.withColumn("_r", F.rand(seed)).withColumn(
        "_k", F.floor(F.rand(seed + 1) * len(DEFECTS)).cast("int")
    )
    chosen = F.col("_r") < rate
    is_ = lambda name: chosen & (F.col("_k") == DEFECTS.index(name))

    thru = F.expr(f"try_to_timestamp(CLM_THRU_DT, '{fmt}')")
    later = F.date_format(F.date_add(thru, 30), fmt)

    broken = (
        picked.withColumn(
            config.MEMBER_KEY,
            F.when(is_("missing_member_key"), F.lit(None))
            .when(is_("unknown_member"), F.lit("-99999999999999"))
            .otherwise(F.col(config.MEMBER_KEY)),
        )
        .withColumn(
            config.CLAIM_KEY,
            F.when(is_("missing_claim_key"), F.lit(None)).otherwise(F.col(config.CLAIM_KEY)),
        )
        .withColumn(
            "CLM_FROM_DT",
            F.when(is_("malformed_date"), F.lit("2015-13-45"))
            .when(is_("dates_reversed"), later)
            .otherwise(F.col("CLM_FROM_DT")),
        )
        .withColumn(
            "CLM_PMT_AMT",
            F.when(is_("malformed_amount"), F.lit("12,3O.00")).otherwise(F.col("CLM_PMT_AMT")),
        )
        .withColumn(
            LABEL,
            F.when(chosen & ~is_("duplicate_row"), F.element_at(
                F.array(*[F.lit(d) for d in DEFECTS]), F.col("_k") + 1
            )),
        )
    )
    copies = picked.filter(is_("duplicate_row")).withColumn(LABEL, F.lit("duplicate_row"))
    return broken.unionByName(copies).drop("_r", "_k")


def recall_report(quarantined: DataFrame, all_rows: DataFrame) -> DataFrame:
    """Per defect type: rows injected, rows caught by the expected rule, recall.

    For duplicates, either copy may be the one quarantined, so they are counted by the
    number of rows failing the duplicate rule rather than by label.
    """
    spark = all_rows.sparkSession
    injected = {r[LABEL]: r["count"] for r in
                all_rows.filter(F.col(LABEL).isNotNull()).groupBy(LABEL).count().collect()}
    rows = []
    for defect, rule in EXPECTED_RULE.items():
        n = int(injected.get(defect, 0))
        if defect == "duplicate_row":
            caught = quarantined.filter(F.array_contains("_failed_rules", rule)).count()
        else:
            caught = quarantined.filter(
                (F.col(LABEL) == defect) & F.array_contains("_failed_rules", rule)
            ).count()
        rows.append((defect, rule, n, caught, round(caught / n, 4) if n else None))
    false_alarms = quarantined.filter(F.col(LABEL).isNull() & ~F.array_contains(
        "_failed_rules", "not_duplicate_row")).count()
    rows.append(("(none: clean rows quarantined)", "any", 0, false_alarms, None))
    return spark.createDataFrame(
        rows, "defect string, expected_rule string, injected long, caught long, recall double"
    )
