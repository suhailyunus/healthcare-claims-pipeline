"""The fields the extractor must return for each denied claim in a letter."""

# Field name -> how the evaluator compares extracted and true values.
#   exact  : string match after trimming and upper-casing
#   amount : numeric match to the cent
#   date   : same calendar date, any input format normalized to YYYY-MM-DD upstream
EXTRACTION_FIELDS = {
    "claim_id": "exact",
    "member_id": "exact",
    "denial_reason_code": "exact",
    "denied_amount": "amount",
    "service_from_date": "date",
    "service_through_date": "date",
    "letter_date": "date",
}
