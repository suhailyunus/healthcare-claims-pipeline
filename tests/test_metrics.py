from claims_pipeline.evaluation.metrics import score_field, score_record, summarize
from claims_pipeline.extraction.schema import EXTRACTION_FIELDS


def test_exact_match_ignores_case_and_whitespace():
    assert score_field("CO-97", " co-97 ") == "correct"


def test_amount_match_ignores_formatting():
    assert score_field("1250.5", "$1,250.50", "amount") == "correct"
    assert score_field("1250.50", "1250.05", "amount") == "wrong"


def test_unparseable_amount_is_wrong_not_an_error():
    assert score_field("100.00", "one hundred", "amount") == "wrong"


def test_missing_and_hallucinated_are_distinguished():
    assert score_field("CO-97", None) == "missing"
    assert score_field(None, "CO-97") == "hallucinated"
    assert score_field(None, "") is None


def test_score_record_and_summary():
    truth = {"claim_id": "A1", "denied_amount": "200.00", "denial_reason_code": "CO-50"}
    good = {"claim_id": "A1", "denied_amount": "$200", "denial_reason_code": "CO-50"}
    bad = {"claim_id": "A1", "denied_amount": "20.00", "denial_reason_code": None}
    scored = [score_record(truth, r, EXTRACTION_FIELDS) for r in (good, bad)]
    summary = summarize(scored)
    assert summary["claim_id"]["accuracy"] == 1.0
    assert summary["denied_amount"]["wrong"] == 1
    assert summary["denial_reason_code"]["missing"] == 1
    assert "letter_date" not in summary  # blank on both sides is not scored
