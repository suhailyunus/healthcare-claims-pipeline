"""Field-level accuracy for extracted records versus the answer key.

Pure Python so it can be unit tested without Spark. Each field is scored as one of:
  correct       extracted value matches the true value
  wrong         a value was extracted and it does not match
  missing       the true value exists and nothing was extracted
  hallucinated  nothing exists in the letter and a value was extracted anyway

Splitting "wrong" from "hallucinated" matters in healthcare: an invented denial code is
a different and worse failure than a misread digit.
"""

from collections import Counter
from decimal import Decimal, InvalidOperation

OUTCOMES = ("correct", "wrong", "missing", "hallucinated")


def _is_blank(value) -> bool:
    return value is None or str(value).strip() == ""


def _same_amount(a, b) -> bool:
    try:
        clean = lambda v: Decimal(str(v).replace("$", "").replace(",", "").strip())
        return clean(a).quantize(Decimal("0.01")) == clean(b).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return False


def values_match(expected, extracted, kind: str = "exact") -> bool:
    if kind == "amount":
        return _same_amount(expected, extracted)
    return str(expected).strip().upper() == str(extracted).strip().upper()


def score_field(expected, extracted, kind: str = "exact") -> str | None:
    """Score one field. Returns None when both sides are blank (nothing to score)."""
    if _is_blank(expected) and _is_blank(extracted):
        return None
    if _is_blank(expected):
        return "hallucinated"
    if _is_blank(extracted):
        return "missing"
    return "correct" if values_match(expected, extracted, kind) else "wrong"


def score_record(expected: dict, extracted: dict, fields: dict[str, str]) -> dict[str, str]:
    """Score every field of one record. `fields` maps field name -> comparison kind."""
    scores = {}
    for name, kind in fields.items():
        outcome = score_field(expected.get(name), extracted.get(name), kind)
        if outcome is not None:
            scores[name] = outcome
    return scores


def summarize(scored_records: list[dict[str, str]]) -> dict[str, dict]:
    """Per-field outcome counts and accuracy across many scored records."""
    counts: dict[str, Counter] = {}
    for record in scored_records:
        for name, outcome in record.items():
            counts.setdefault(name, Counter())[outcome] += 1
    summary = {}
    for name, c in counts.items():
        total = sum(c.values())
        summary[name] = {
            **{o: c.get(o, 0) for o in OUTCOMES},
            "total": total,
            "accuracy": round(c.get("correct", 0) / total, 4) if total else None,
        }
    return summary
