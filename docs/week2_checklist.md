# Week 2 checklist: silver and data quality

Goal: every bronze row accounted for, in silver or in quarantine with a reason, and proof
that the rules catch the defects they claim to.

## Build
- [ ] Pull the latest code into the Databricks Git folder
- [ ] Run `notebooks/03_silver` and read the quality log it prints
- [ ] Run `notebooks/04_defect_check` and confirm recall is 1.0 for every defect type
- [ ] Record the real quarantine counts and anything surprising in `docs/definitions.md`

## Understand (be able to explain without notes)
- [ ] Why the duplicate check hashes whole rows instead of checking `CLM_ID`
- [ ] Why negative amounts are allowed through
- [ ] Why quarantined rows keep their original text values
- [ ] What "bronze = silver + quarantine" protects against

## Domain
- [ ] Answer: does `CLM_PMT_AMT` repeat on every line of a claim?
- [ ] Read about claim types: institutional (inpatient, outpatient) vs professional (carrier)
- [ ] Learn the difference between billed, allowed, and paid amounts

## Outreach
- [ ] Send the follow-up note to the Microsoft manager, if not sent yet
- [ ] Book the first of three conversations with a healthcare data practitioner
