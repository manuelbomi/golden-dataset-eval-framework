# ADR 0002: Track calibration (ECE), not just accuracy

## Status
Accepted

## Context
A model evaluation that only reports accuracy tells you nothing about
whether the model's CONFIDENCE scores can be trusted. In a human-in-the-
loop system, confidence is often used operationally -- e.g. "auto-apply
predictions above 0.9 confidence, route everything else to a human." If a
model claims 0.9 confidence but is actually right only 65% of the time at
that confidence level, that operational threshold silently lets bad
predictions through unreviewed.

## Decision
Compute Expected Calibration Error (ECE) alongside accuracy/precision/
recall/F1 in every evaluation run (`app/eval/harness.py`), and let
`eval_gate.py` fail a build on excessive ECE (`--max-ece`), independent of
whether accuracy/F1 thresholds pass. See `app/metrics/calibration.py` for
the implementation and `tests/test_calibration.py` for a hand-verified
worked example.

## Consequences
- ECE is sensitive to bin count and to how much data lands in each bin;
  we default to 10 fixed-width bins, which is a common but not unique
  choice -- a very small eval set will produce noisy per-bin accuracy
  estimates. Treat ECE on small eval sets as directional, not exact.
- ECE alone doesn't say WHICH direction the miscalibration runs
  (overconfident vs. underconfident); the reliability-diagram bin data
  returned by `compute_calibration` is meant to be plotted, not just
  reduced to the single ECE number, when someone is actually debugging a
  calibration problem.
