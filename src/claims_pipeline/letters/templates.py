"""Letter layouts, each modeled on a real published notice format (Week 4).

For every template record: the real format it is based on, its difficulty tier, and
whether it is held out. Held-out templates are never looked at while developing the
extractor, so accuracy on them measures generalization to unseen layouts.
"""

DIFFICULTY_TIERS = ("clean", "messy", "degraded")
