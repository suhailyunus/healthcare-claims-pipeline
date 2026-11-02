# Definitions

What each term means in this project and how it is counted. Updated when the data proves
a definition wrong. Status: CONFIRMED (checked against the raw profile), CHECK IN GOLD (to
verify when building gold tables), or OPEN.

| Term | Definition in this project | How it is counted | Status |
|---|---|---|---|
| Member (beneficiary) | A person enrolled in Medicare in a given year | Distinct `BENE_ID` | CONFIRMED |
| Member-year | One member's enrollment record for one year | One beneficiary row: grain is `BENE_ID` + `BENE_ENROLLMT_REF_YR` | CONFIRMED |
| Member month | One member enrolled for one calendar month | From the monthly coverage indicators on the member-year row | CHECK IN GOLD |
| Claim | One bill from one provider for one member covering a date range | Distinct `CLM_ID`, never row count | CONFIRMED |
| Claim line | One service or revenue-center item within a claim | One row in a claims file | CONFIRMED |
| Service dates | When care happened, not when the claim was processed | `CLM_FROM_DT`, `CLM_THRU_DT` | CONFIRMED |
| Paid amount | What Medicare paid the provider for the claim | `CLM_PMT_AMT`, a claim-level field | CHECK IN GOLD |
| Billed / allowed amount | What the provider asked for / what the payer deemed payable | Carrier: `NCH_CARR_CLM_SBMTD_CHRG_AMT`, `NCH_CARR_CLM_ALOWD_AMT` | CHECK IN GOLD |
| Denied claim | A claim or line the payer declined to pay | Not present in this data; assigned by the letter generator | CONFIRMED (absent) |
| Inpatient stay | A hospital admission | One inpatient claim; interim bills could split a stay | CHECK IN GOLD |

## Grain, from the raw profile

| File | Rows | Distinct claims | Rows per claim |
|---|---:|---:|---:|
| inpatient | 58,066 | 20,867 | 2.78 |
| outpatient | 575,092 | 402,653 | 1.43 |
| carrier | 1,121,004 | 90,705 | 12.36 |
| beneficiary (11 yearly files) | 86,917 | n/a | one row per member-year |

Counting carrier rows as claims would overstate claim volume more than twelvefold.

**The CMS user guide makes this mistake.** Its "Profile of Synthetic Claims Data" table
labels figures as claim counts (inpatient 58,030, carrier 1,120,655) that are within a
fraction of a percent of our row counts, while distinct `CLM_ID` counts are far lower. The
guide describes an earlier version of the release, but the figures are clearly line counts.

## Ways these numbers get counted wrong

1. **Counting rows as claims.** All three claims files are line-grain (table above).
2. **Summing claim-level amounts across lines.** If `CLM_PMT_AMT` repeats on every line of
   a claim, a plain sum multiplies it by the number of lines. Check before building gold.
3. **Mixing billed and paid.** A cost metric must say which amount it uses.
4. **Counting members without enrollment.** Per-member rates need member months as the
   denominator, not a count of people who happened to have claims.
5. **Casting IDs to numbers.** IDs are long negative numbers here (for example
   `-10000010254618`). Codes elsewhere carry leading zeros. All IDs and codes stay strings.

## Data facts that shape the pipeline

- Pipe-delimited, header row, dates as text in `dd-MMM-yyyy` form (`25-Mar-2015`).
- Release covers 2015 to 2025 (newer than the May 2023 user guide, which says 2015-2023).
- Some columns are always empty (inpatient `FI_CLM_PROC_DT`: 100% null). Some are partly
  empty (inpatient `PRVDR_NUM`: 4.9% null), which a gold model must handle.
- Per the user guide, denial fields are placeholders (`CARR_CLM_PMT_DNL_CD` fixed at 1,
  `CLM_MDCR_NON_PMT_RSN_CD` blank) and no payment is negative, so the data has no real
  denials or adjustments.

## Open questions

- Does `CLM_PMT_AMT` repeat on every line of a claim, or appear once? (Decides trap 2.)
- Are adjusted or replacement claims present? The guide suggests not; confirm in gold.
