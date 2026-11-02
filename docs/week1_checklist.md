# Week 1 checklist: foundations

Goal: data in Databricks, a raw profile you have read, and a definitions document you can
defend. No transformation logic yet.

## Setup
- [x] Create a Databricks workspace (Free Edition is enough) and connect it to GitHub
- [x] Create the GitHub repo and push this scaffold
- [x] Add the repo to Databricks as a Git folder
- [x] Run `notebooks/00_setup`

## Data
- [x] Download the CMS synthetic claims files and the user guide (`docs/data_sources.md`)
- [x] Upload beneficiary, inpatient, outpatient, and carrier files to the landing volume
- [x] Update `SOURCE_FILES` and `DELIMITER` in `src/claims_pipeline/config.py`
- [x] Run `notebooks/01_profile_raw` and read the output for every file
- [x] Run `notebooks/02_bronze_ingest`

## Domain
- [ ] Read the CMS user guide sections on file structure and data format
- [x] Tick off the five confirmations in `docs/data_sources.md`
- [x] Resolve every CONFIRM in `docs/definitions.md`
- [ ] Answer the two open questions in `docs/definitions.md`

## Self-test before moving to Week 2
- [ ] Explain, without notes, how a hospital stay becomes a paid claim
- [ ] Name three ways a claims count or dollar total could be wrong in this dataset
- [ ] State the grain of each of the four files

## Outreach
- [ ] Send the follow-up note to the Microsoft manager
- [ ] List five healthcare data people to ask for a 20-minute conversation
