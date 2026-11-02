"""Single place for names and paths. Notebooks and modules import from here."""

# Unity Catalog locations. "workspace" is the default catalog on Databricks Free Edition.
CATALOG = "workspace"
BRONZE = f"{CATALOG}.claims_bronze"
SILVER = f"{CATALOG}.claims_silver"
GOLD = f"{CATALOG}.claims_gold"
SCHEMAS = [BRONZE, SILVER, GOLD]

# Raw files are uploaded here by hand.
LANDING_VOLUME = f"{BRONZE}.landing"
LANDING_PATH = f"/Volumes/{CATALOG}/claims_bronze/landing"

# Confirmed from the raw profile (Oct 2026 release, 2015-2025).
DELIMITER = "|"
DATE_FORMAT = "dd-MMM-yyyy"  # e.g. 25-Mar-2015

# Bronze table name -> file name or glob inside LANDING_PATH.
SOURCE_FILES = {
    "beneficiary": "beneficiary_*.csv",  # 11 yearly files, 2015-2025
    "inpatient": "inpatient.csv",
    "outpatient": "outpatient.csv",
    "carrier": "carrier.csv",
}
CLAIM_TABLES = ("inpatient", "outpatient", "carrier")

# Keys. IDs are long negative numbers in this synthetic data: keep them as strings.
MEMBER_KEY = "BENE_ID"
CLAIM_KEY = "CLM_ID"
BENE_YEAR = "BENE_ENROLLMT_REF_YR"

# Columns typed in silver, chosen by suffix. Everything else stays a string, because
# codes (ZIP, diagnosis, provider, state) carry meaning in leading zeros and letters.
DATE_SUFFIX = "_DT"
AMOUNT_SUFFIX = "_AMT"
AMOUNT_TYPE = "decimal(14,2)"

QUARANTINE_SUFFIX = "_quarantine"
QUALITY_LOG = f"{SILVER}.quality_log"
