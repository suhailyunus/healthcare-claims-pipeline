# Healthcare Claims Pipeline with LLM Denial-Letter Extraction

A medallion-architecture pipeline on Databricks over CMS synthetic Medicare claims, with an
LLM step that extracts structured fields from denial letters and an evaluation report that
measures how often that step is right.

**Status:** Week 1 of 6 (foundations). See the roadmap below.

## Why this project

Most healthcare AI work stalls on data, not models. This project shows the full path:
reliable claims data, one AI step on unstructured documents, and a measured answer to
"how much should we trust it?"

## Architecture

```
CMS synthetic claims (CSV)
        |
     BRONZE   raw, all strings, load metadata           src/claims_pipeline/ingest.py
        |
     SILVER   typed, validated; failures -> quarantine  src/claims_pipeline/silver.py, quality.py
        |
      GOLD    cost and utilization per member-month     src/claims_pipeline/gold.py
        |                                   ^
        v                                   | join on claim ID
 letter generator -> PDFs -> degrade -> OCR -> LLM extraction -> extracted_denials
 (answer key kept)                                   |
                                                     v
                                          evaluation vs answer key
```

## Roadmap

| Week | Focus | Output |
|---|---|---|
| 1 | Foundations | Data loaded to a volume, raw profile, `docs/definitions.md` |
| 2 | Ingest and clean | Bronze and silver tables, quality rules, quarantine table |
| 3 | Model and reconcile | Gold tables, reconciliation checks |
| 4 | AI step | Letter generator, OCR, LLM extraction table |
| 5 | Evaluate | Field-level accuracy by difficulty tier, failure analysis |
| 6 | Package | Final README, diagram, findings and limitations |

## Repo layout

- `docs/` definitions, data sources, weekly checklists
- `notebooks/` Databricks notebooks (source format), numbered in run order
- `src/claims_pipeline/` importable pipeline code
- `tests/` unit tests for logic that runs without Spark

## Running it

1. In Databricks, add this repo as a Git folder.
2. Run `notebooks/00_setup` to create the schemas and the landing volume.
3. Upload the CMS files to the landing volume (see `docs/data_sources.md`).
4. Run the remaining notebooks in number order.

Local tests: `pip install -r requirements.txt && pytest`

## Limitations (kept current as the project grows)

- The claims are synthetic. They mirror real file structure, but no conclusions about real
  Medicare patients can be drawn from them.
- The denial letters are generated, modeled on real notice formats and public denial code
  sets. Accuracy on them is an upper bound on accuracy on real letters.
