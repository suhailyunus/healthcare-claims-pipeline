# Definitions

Written before the code, and updated when the data proves a definition wrong. Each entry
says what the term means in this project and how it is counted.

Entries marked CONFIRM are starting definitions from general claims knowledge. Check each
against the CMS user guide and the raw profile, then remove the mark.

| Term | Definition in this project | How it is counted | Status |
|---|---|---|---|
| Member (beneficiary) | A person enrolled in Medicare in a given year | Distinct member key in the beneficiary file | CONFIRM |
| Member month | One member enrolled for one calendar month | From the monthly coverage indicators in the beneficiary file | CONFIRM |
| Claim | One bill from one provider for one member covering a date range | Distinct claim key, not row count | CONFIRM |
| Claim line | One service or revenue-center item within a claim | One row where the file is line-grain | CONFIRM |
| Service dates | The from and through dates of the care, not the date the claim was processed | Claim from date and through date | CONFIRM |
| Billed (charge) amount | What the provider asked for | Total charge column | CONFIRM |
| Allowed amount | What the payer considers payable under its rules | To be located in the data | CONFIRM |
| Paid amount | What Medicare paid the provider | Claim payment column | CONFIRM |
| Denied claim | A claim or line the payer declined to pay | To be defined: see open questions | OPEN |
| Inpatient stay | A hospital admission | One inpatient claim; transfers and interim bills may split a stay | CONFIRM |

## Ways these numbers get counted wrong

1. **Counting rows as claims.** If a file is line-grain, row count overstates claim volume.
2. **Summing header amounts across lines.** If claim-level amounts repeat on every line,
   a plain sum multiplies the paid amount by the number of lines.
3. **Mixing billed and paid.** Billed amounts are often several times paid amounts.
   A "cost" metric must say which one it uses.
4. **Counting members without enrollment.** Per-member rates need member months as the
   denominator, not a count of people who happened to have claims.

## Open questions

- How does this dataset represent a denial: a denial indicator, a zero payment, or neither?
  If the claims carry no usable denial signal, denials are assigned in Week 4 by the letter
  generator, and that choice is documented as a limitation.
- Are adjusted or replacement claims present, and if so which version counts?
