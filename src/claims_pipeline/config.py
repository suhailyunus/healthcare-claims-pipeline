"""Single place for names and paths. Notebooks and modules import from here."""

# Unity Catalog locations. "workspace" is the default catalog on Databricks Free Edition;
# change CATALOG if yours differs.
CATALOG = "workspace"
BRONZE = f"{CATALOG}.claims_bronze"
SILVER = f"{CATALOG}.claims_silver"
GOLD = f"{CATALOG}.claims_gold"
SCHEMAS = [BRONZE, SILVER, GOLD]

# Raw files are uploaded here by hand in Week 1.
LANDING_VOLUME = f"{BRONZE}.landing"
LANDING_PATH = f"/Volumes/{CATALOG}/claims_bronze/landing"

# CONFIRM against the CMS user guide and the files you downloaded.
DELIMITER = "|"

# Bronze table name -> file name or glob inside LANDING_PATH.
# CONFIRM the file names after download. Globs let one table take several yearly files.
SOURCE_FILES = {
    "beneficiary": "beneficiary_*.csv",
    "inpatient": "inpatient.csv",
    "outpatient": "outpatient.csv",
    "carrier": "carrier.csv",
}

QUARANTINE_SUFFIX = "_quarantine"
