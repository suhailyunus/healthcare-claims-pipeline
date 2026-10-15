# Data sources

## Claims: CMS Synthetic Medicare Claims PUFs (2023 release)

Full name: Synthetic Medicare Enrollment, Fee-for-Service Claims, and Prescription Drug
Event Data Public Use File. Published on data.cms.gov with a user guide (May 2023).

Use this release, not the older 2008-2010 DE-SynPUF. The older files use ICD-9 diagnosis
codes, which US healthcare stopped using in 2015.

Start with four file types:

| File | What it holds |
|---|---|
| Beneficiary (one per year) | Who is enrolled, demographics, coverage months |
| Inpatient | Hospital stay claims |
| Outpatient | Hospital outpatient claims |
| Carrier | Physician and professional claims |

Add the others (skilled nursing, home health, hospice, equipment, drug events) only if a
later phase needs them.

### Before writing silver logic, confirm from the user guide and `01_profile_raw`

- [ ] Delimiter (set `DELIMITER` in `config.py`)
- [ ] Exact file names (set `SOURCE_FILES` in `config.py`)
- [ ] Date format in the date columns
- [ ] Grain of each claims file: one row per claim, or one row per claim line
- [ ] Which column is the member key and which is the claim key

Nothing in the bronze layer depends on these answers. Everything in silver does.

## Denial codes: CARC and RARC

Claim Adjustment Reason Codes and Remittance Advice Remark Codes are the public,
industry-standard code sets for why a claim was adjusted or denied. Download the current
lists in Week 4 and store them as a reference table.

## Letter layouts

Base the templates on real published formats: the CMS Notice of Denial of Medical Coverage
(the Integrated Denial Notice), Medicare Summary Notices, and sample explanation-of-benefits
documents that payers publish. Record the source of each template in
`src/claims_pipeline/letters/templates.py`.
