"""Silver layer: typed, validated tables. Rows that fail a rule go to quarantine.

Every bronze row ends up in exactly one place, the silver table or its quarantine table,
so bronze rows = silver rows + quarantined rows. `build_silver` checks that before writing.

Design choices, each traceable to the raw profile:
  - Claims files are line-grain (several rows per CLM_ID), so the duplicate check is on
    whole rows, not on the claim key. A repeated claim ID is normal; a repeated row is not.
  - Dates arrive as text like 25-Mar-2015. A date that is present but does not parse is a
    failure; a date that is blank is not (most date columns are optional).
  - Negative amounts are allowed. In real claims they are legitimate adjustments and
    reversals, so rejecting them would discard valid data.
  - Rules are written against the raw strings, so quarantined rows keep the original value
    that failed, which is what someone fixing the source needs to see.
"""

from datetime import datetime, timezone

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

from claims_pipeline import config
from claims_pipeline.quality import Rule, apply_rules, summarize_failures

HELPER_PREFIX = "__"  # temporary columns used by rules, dropped before writing


# ---------- expression helpers (SQL text, evaluated against raw string columns) ----------

def _q(col: str) -> str:
    return f"`{col}`"


def _parsed_date(col: str) -> str:
    return f"try_to_timestamp({_q(col)}, '{config.DATE_FORMAT}')"


def _present(col: str) -> str:
    return f"({_q(col)} IS NOT NULL AND trim({_q(col)}) <> '')"


def _all_parse(cols: list[str], parsed) -> str:
    """TRUE when every column that has a value also parses."""
    if not cols:
        return "TRUE"
    return " AND ".join(f"NOT ({_present(c)} AND {parsed(c)} IS NULL)" for c in cols)


def date_columns(df: DataFrame) -> list[str]:
    return [c for c in df.columns if c.endswith(config.DATE_SUFFIX)]


def amount_columns(df: DataFrame) -> list[str]:
    return [c for c in df.columns if c.endswith(config.AMOUNT_SUFFIX)]


def business_columns(df: DataFrame) -> list[str]:
    """Columns from the source file, excluding load metadata and helper columns."""
    return [c for c in df.columns if not c.startswith("_")]


# ---------- rule sets ----------

def claim_rules(df: DataFrame) -> list[Rule]:
    amt = lambda c: f"try_cast({_q(c)} AS {config.AMOUNT_TYPE})"
    return [
        Rule("member_key_present", _present(config.MEMBER_KEY)),
        Rule("claim_key_present", _present(config.CLAIM_KEY)),
        Rule("member_known", f"{HELPER_PREFIX}member_known"),
        Rule("dates_parse", _all_parse(date_columns(df), _parsed_date)),
        Rule("amounts_parse", _all_parse(amount_columns(df), amt)),
        Rule(
            "service_dates_ordered",
            f"{_parsed_date('CLM_FROM_DT')} <= {_parsed_date('CLM_THRU_DT')}",
        ),
        Rule("not_duplicate_row", f"{HELPER_PREFIX}dup_rank = 1"),
    ]


def beneficiary_rules(df: DataFrame) -> list[Rule]:
    rules = [
        Rule("member_key_present", _present(config.MEMBER_KEY)),
        Rule("year_valid", f"try_cast({_q(config.BENE_YEAR)} AS int) BETWEEN 2000 AND 2100"),
        Rule("dates_parse", _all_parse(date_columns(df), _parsed_date)),
        Rule("one_row_per_member_year", f"{HELPER_PREFIX}dup_rank = 1"),
    ]
    if "BENE_DEATH_DT" in df.columns and "BENE_BIRTH_DT" in df.columns:
        rules.append(
            Rule(
                "birth_before_death",
                f"NOT {_present('BENE_DEATH_DT')} OR "
                f"{_parsed_date('BENE_BIRTH_DT')} <= {_parsed_date('BENE_DEATH_DT')}",
            )
        )
    return rules


# ---------- helper columns ----------

def add_row_hash(df: DataFrame) -> DataFrame:
    """Hash of all business columns, so exact duplicate rows share a hash."""
    cols = [F.coalesce(F.col(c).cast("string"), F.lit("∅")) for c in business_columns(df)]
    return df.withColumn(f"{HELPER_PREFIX}row_hash", F.sha2(F.concat_ws("\u0001", *cols), 256))


def add_dup_rank(df: DataFrame, partition_cols: list[str]) -> DataFrame:
    """1 for the first row of each group, 2+ for repeats. Order is deterministic."""
    order = [F.col(c).asc_nulls_last() for c in sorted(business_columns(df))]
    w = Window.partitionBy(*partition_cols).orderBy(*order)
    return df.withColumn(f"{HELPER_PREFIX}dup_rank", F.row_number().over(w))


def add_member_known(df: DataFrame, members: DataFrame) -> DataFrame:
    known = (
        members.select(config.MEMBER_KEY)
        .distinct()
        .withColumn(f"{HELPER_PREFIX}member_known", F.lit(True))
    )
    return df.join(known, on=config.MEMBER_KEY, how="left").fillna(
        {f"{HELPER_PREFIX}member_known": False}
    )


def drop_helpers(df: DataFrame) -> DataFrame:
    return df.drop(*[c for c in df.columns if c.startswith(HELPER_PREFIX)])


# ---------- typing ----------

def apply_types(df: DataFrame) -> DataFrame:
    """Cast dates and amounts. Only called on rows that passed the parse rules."""
    out = df
    for c in date_columns(df):
        out = out.withColumn(c, F.expr(f"CAST({_parsed_date(c)} AS DATE)"))
    for c in amount_columns(df):
        out = out.withColumn(c, F.expr(f"try_cast({_q(c)} AS {config.AMOUNT_TYPE})"))
    if config.BENE_YEAR in df.columns:
        out = out.withColumn(config.BENE_YEAR, F.expr(f"try_cast({_q(config.BENE_YEAR)} AS int)"))
    return out


# ---------- preparation per table type ----------

def prepare_claims(df: DataFrame, members: DataFrame) -> tuple[DataFrame, list[Rule]]:
    df = add_member_known(df, members)
    df = add_row_hash(df)
    df = add_dup_rank(df, [f"{HELPER_PREFIX}row_hash"])
    return df, claim_rules(df)


def prepare_beneficiary(df: DataFrame) -> tuple[DataFrame, list[Rule]]:
    df = df.withColumn(f"{HELPER_PREFIX}year", F.expr(f"try_cast({_q(config.BENE_YEAR)} AS int)"))
    df = add_dup_rank(df, [config.MEMBER_KEY, f"{HELPER_PREFIX}year"])
    return df, beneficiary_rules(df)


def split(df: DataFrame, rules: list[Rule]) -> tuple[DataFrame, DataFrame]:
    """Return (typed valid rows, quarantined raw rows), helper columns removed."""
    valid, quarantined = apply_rules(df, rules)
    return apply_types(drop_helpers(valid)), drop_helpers(quarantined)


# ---------- orchestration ----------

def build_silver(spark: SparkSession, table: str, members: DataFrame | None = None) -> dict:
    """Validate one bronze table, write silver + quarantine, and log the counts."""
    bronze = spark.table(f"{config.BRONZE}.{table}")
    if table == "beneficiary":
        prepared, rules = prepare_beneficiary(bronze)
    else:
        if members is None:
            members = spark.table(f"{config.SILVER}.beneficiary")
        prepared, rules = prepare_claims(bronze, members)

    valid, quarantined = split(prepared, rules)

    target = f"{config.SILVER}.{table}"
    q_target = f"{target}{config.QUARANTINE_SUFFIX}"
    for frame, name in ((valid, target), (quarantined, q_target)):
        frame.write.format("delta").mode("overwrite").option("overwriteSchema", True).saveAsTable(name)

    bronze_rows = bronze.count()
    valid_rows = spark.table(target).count()
    q_rows = spark.table(q_target).count()
    if bronze_rows != valid_rows + q_rows:
        raise AssertionError(
            f"{table}: bronze {bronze_rows:,} != silver {valid_rows:,} + quarantine {q_rows:,}"
        )

    by_rule = {r["rule"]: r["count"] for r in summarize_failures(spark.table(q_target)).collect()}
    log_run(spark, table, bronze_rows, valid_rows, q_rows, by_rule, [r.name for r in rules])
    return {"table": table, "bronze": bronze_rows, "silver": valid_rows,
            "quarantined": q_rows, "failures_by_rule": by_rule}


def log_run(spark, table, bronze_rows, valid_rows, q_rows, by_rule, rule_names) -> None:
    """Append one row per rule to the quality log, including rules with zero failures."""
    run_at = datetime.now(timezone.utc)
    rows = [(run_at, table, bronze_rows, valid_rows, q_rows, name, int(by_rule.get(name, 0)))
            for name in rule_names]
    schema = ("run_at timestamp, table_name string, bronze_rows long, silver_rows long, "
              "quarantined_rows long, rule string, failed_rows long")
    spark.createDataFrame(rows, schema).write.format("delta").mode("append").saveAsTable(
        config.QUALITY_LOG
    )
