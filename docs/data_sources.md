# Data sources

## Claims: CMS Synthetic Medicare Claims PUFs (2023 release)

Full name: Synthetic Medicare Enrollment, Fee-for-Service Claims, and Prescription Drug
Event Data Public Use File. Published on data.cms.gov with a user guide (May 2023).

Use this release, not the older 2008-2010 DE-SynPUF. The older files use ICD-9 diagnosis
codes, which US healthcare stopped using in 2015.

Downloaded from the collection's per-file links. Start with four file types:

| File | What it holds |
|---|---|
| Beneficiary (one per year) | Who is enrolled, demographics, coverage months |
| Inpatient | Hospital stay claims |
| Outpatient | Hospital outpatient claims |
| Carrier | Physician and professional claims |

Add the others (skilled nursing, home health, hospice, equipment, drug events) only if a
later phase needs them.

### Confirmed from the raw profile (Oct 2026)

- [x] Delimiter: pipe `|`
- [x] File names: `beneficiary_2015.csv` to `beneficiary_2025.csv`, `inpatient.csv`,
      `outpatient.csv`, `carrier.csv`
- [x] Date format: `dd-MMM-yyyy`, e.g. `25-Mar-2015`
- [x] Grain: all three claims files are line-grain; beneficiary is one row per member-year
- [x] Keys: `BENE_ID` (member), `CLM_ID` (claim)

The release on data.cms.gov now covers 2015 to 2025, two years beyond the user guide.
Row counts and grain are recorded in `docs/definitions.md`.

## Denial codes: CARC and RARC

Claim Adjustment Reason Codes and Remittance Advice Remark Codes are the public,
industry-standard code sets for why a claim was adjusted or denied. Download the current
lists in Week 4 and store them as a reference table.

## Letter layouts

Base the templates on real published formats: the CMS Notice of Denial of Medical Coverage
(the Integrated Denial Notice), Medicare Summary Notices, and sample explanation-of-benefits
documents that payers publish. Record the source of each template in
`src/claims_pipeline/letters/templates.py`.
