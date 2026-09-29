# ADR 0001: Use chance-corrected kappa, not raw percent agreement

## Status
Accepted

## Context
The obvious way to report "how well do our annotators agree" is percent
agreement: the fraction of items where two (or more) annotators picked the
same label. It's intuitive and trivial to compute.

The problem is that percent agreement is inflated by however skewed the
label distribution is. In this repo's taxonomy, NEUTRAL is expected to be
the majority class in most real conversation data. Two annotators who both
default to NEUTRAL whenever they're unsure will show high percent
agreement purely from that shared bias, without the taxonomy or the
annotators actually distinguishing OBJECTION from BUYING_SIGNAL reliably.

## Decision
Report Cohen's kappa (2 annotators) or Fleiss' kappa (3+) for
dataset-level annotation-process quality, and use the related
per-item pairwise agreement rate (not chance-corrected, since chance
correction needs frequencies estimated across many items) to decide
whether a single task's labels are consistent enough to finalize as a
golden example. See `app/metrics/agreement.py` for both implementations
and `app/api/annotations.py` for where the per-item version is used.

## Consequences
- Kappa is harder to explain to non-technical stakeholders than "percent
  agreement" -- the README and code comments spell out the intuition
  (subtracting out chance) rather than assuming familiarity.
- A single global kappa number can mask per-class disagreement (raters
  might agree well on OBJECTION but poorly on ACTION_ITEM vs QUESTION).
  For that reason, `eval_gate.py`'s thresholds operate per-class, not just
  on one aggregate score.
