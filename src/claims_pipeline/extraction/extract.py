"""Call the LLM on OCR text and return fields matching schema.EXTRACTION_FIELDS (Week 4).

Requirements:
  - return null for a field that is not in the letter; never guess
  - return one record per denied claim when a letter covers several
  - keep the raw model response alongside the parsed fields for failure analysis
  - records that fail parsing or validation go to a review table, not the main table
"""
