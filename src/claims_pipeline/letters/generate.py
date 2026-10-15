"""Turn claims into denial letters plus an answer key (Week 4).

For each sampled claim: pick a template and a CARC/RARC reason, render the letter, and
write the true field values to the answer-key table keyed by letter ID.

Use a different model for writing letter prose than the one used for extraction, so the
extractor is not tested on its own writing style. Fix a random seed so the letter set is
reproducible.

Messiness to include: several claims in one letter; billed, allowed, and denied amounts
all present; missing fields; several dates; key details on page two.
"""
