"""Silver rules and defect injection, run on a local Spark session.

Skipped automatically when pyspark is not installed. To run:
    pip install pyspark==4.0.1 && pytest tests/test_silver.py
"""

import pytest

pyspark = pytest.importorskip("pyspark")

from pyspark.sql import SparkSession  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402

from claims_pipeline import defects, silver  # noqa: E402
from claims_pipeline.quality import summarize_failures  # noqa: E402

CLAIM_COLS = ["BENE_ID", "CLM_ID", "CLM_FROM_DT", "CLM_THRU_DT", "CLM_PMT_AMT", "PRVDR_NUM",
              "_source_file"]


@pytest.fixture(scope="module")
def spark():
    s = (SparkSession.builder.master("local[1]").appName("tests")
         .config("spark.sql.ansi.enabled", "true")  # Databricks serverless runs with ANSI on
         .config("spark.sql.shuffle.partitions", "2").getOrCreate())
    yield s
    s.stop()


@pytest.fixture
def members(spark):
    return spark.createDataFrame(
        [("-10000010254618",), ("-10000010254653",)], "BENE_ID string")


def claims(spark, rows):
    return spark.createDataFrame(rows, ", ".join(f"{c} string" for c in CLAIM_COLS))


CLEAN = [
    ("-10000010254618", "-1001", "25-Mar-2015", "25-Mar-2015", "1200.50", "123456", "f"),
    ("-10000010254618", "-1001", "25-Mar-2015", "25-Mar-2015", "1200.50", "123457", "f"),
    ("-10000010254653", "-1002", "24-Sep-2015", "27-Sep-2015", "-35.00", None, "f"),
]


def run(spark, df, members):
    prepared, rules = silver.prepare_claims(df, members)
    return silver.split(prepared, rules)


def test_clean_lines_pass_and_are_typed(spark, members):
    valid, quarantined = run(spark, claims(spark, CLEAN), members)
    assert valid.count() == 3 and quarantined.count() == 0
    types = dict(valid.dtypes)
    assert types["CLM_FROM_DT"] == "date"
    assert types["CLM_PMT_AMT"] == "decimal(14,2)"
    assert types["BENE_ID"] == "string"  # negative IDs stay strings
    assert not [c for c in valid.columns if c.startswith("__")]


def test_negative_amount_is_allowed(spark, members):
    valid, _ = run(spark, claims(spark, CLEAN), members)
    assert valid.filter(F.col("CLM_PMT_AMT") < 0).count() == 1


def test_each_rule_catches_its_defect(spark, members):
    bad = CLEAN + [
        (None, "-2001", "25-Mar-2015", "25-Mar-2015", "1.00", "1", "f"),
        ("-999", "-2002", "25-Mar-2015", "25-Mar-2015", "1.00", "1", "f"),
        ("-10000010254618", None, "25-Mar-2015", "25-Mar-2015", "1.00", "1", "f"),
        ("-10000010254618", "-2004", "2015-13-45", "25-Mar-2015", "1.00", "1", "f"),
        ("-10000010254618", "-2005", "30-Mar-2015", "25-Mar-2015", "1.00", "1", "f"),
        ("-10000010254618", "-2006", "25-Mar-2015", "25-Mar-2015", "12,3O.00", "1", "f"),
        CLEAN[0],  # exact duplicate row
    ]
    valid, quarantined = run(spark, claims(spark, bad), members)
    assert valid.count() + quarantined.count() == len(bad)
    counts = {r["rule"]: r["count"] for r in summarize_failures(quarantined).collect()}
    for rule in ["member_key_present", "member_known", "claim_key_present", "dates_parse",
                 "service_dates_ordered", "amounts_parse", "not_duplicate_row"]:
        assert counts.get(rule, 0) >= 1, rule
    assert quarantined.filter(F.col("CLM_FROM_DT") == "2015-13-45").count() == 1  # raw kept


def test_beneficiary_rules(spark):
    cols = "BENE_ID string, BENE_ENROLLMT_REF_YR string, BENE_BIRTH_DT string, BENE_DEATH_DT string"
    df = spark.createDataFrame([
        ("-1", "2015", "01-Jan-1950", None),
        ("-1", "2016", "01-Jan-1950", None),
        ("-1", "2016", "01-Jan-1950", None),          # second row for same member-year
        ("-2", "2015", "01-Jan-1950", "01-Jan-1940"),  # died before birth
        ("-3", "abc", "01-Jan-1950", None),            # bad year
    ], cols)
    prepared, rules = silver.prepare_beneficiary(df)
    valid, quarantined = silver.split(prepared, rules)
    assert valid.count() == 2
    assert dict(valid.dtypes)["BENE_ENROLLMT_REF_YR"] == "int"
    counts = {r["rule"]: r["count"] for r in summarize_failures(quarantined).collect()}
    assert counts == {"one_row_per_member_year": 1, "birth_before_death": 1, "year_valid": 1}


def test_injected_defects_are_all_caught(spark, members):
    base = claims(spark, [
        ("-10000010254618" if i % 2 else "-10000010254653", f"-{i}", "25-Mar-2015",
         "26-Mar-2015", f"{i}.00", str(i), "f")
        for i in range(400)
    ])
    dirty = defects.inject(base, rate=0.2, seed=7)
    prepared, rules = silver.prepare_claims(dirty, members)
    _, quarantined = silver.split(prepared, rules)
    report = {r["defect"]: r for r in defects.recall_report(quarantined, dirty).collect()}
    for name in defects.DEFECTS:
        assert report[name]["injected"] > 0, name
        assert report[name]["recall"] == 1.0, (name, report[name])
    assert report["(none: clean rows quarantined)"]["caught"] == 0
