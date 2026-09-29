"""Production signal-distribution drift detection.

The golden set fixes what "OBJECTION", "BUYING_SIGNAL", etc. look like at
the moment it was built. Live traffic drifts: new products launch, sales
scripts change, a competitor's promotion floods calls with a new kind of
objection the golden set never saw. A model can keep passing the eval gate
(because the gate only re-runs it against the frozen golden set) while
quietly degrading in production, because production input no longer
resembles the golden set's input distribution.

This module compares two label-frequency distributions -- the golden set's
label mix vs. a live sample's label mix (as predicted, not annotated,
since live traffic isn't annotated) -- with two standard metrics:

- Population Stability Index (PSI): an industry-standard drift score from
  credit-risk modeling. Rule of thumb: PSI < 0.1 = no significant shift,
  0.1-0.25 = moderate shift worth watching, > 0.25 = major shift, treat the
  model's current calibration as suspect until re-validated.
- KL divergence: information-theoretic "how many extra bits does encoding
  the live distribution cost if you built your code assuming the golden
  distribution" -- more sensitive to small-probability categories than PSI.

Both need every category to have nonzero probability in both distributions
(otherwise PSI/KL blow up to infinity), so `_smooth` applies a small
additive (Laplace) smoothing constant first.
"""

from __future__ import annotations

import math
from collections import Counter


def _distribution(labels: list[str], categories: list[str], smoothing: float = 1e-4) -> dict[str, float]:
    counts = Counter(labels)
    total = len(labels) + smoothing * len(categories)
    return {c: (counts[c] + smoothing) / total for c in categories}


def population_stability_index(
    baseline_labels: list[str],
    current_labels: list[str],
    categories: list[str],
) -> float:
    baseline = _distribution(baseline_labels, categories)
    current = _distribution(current_labels, categories)
    return sum(
        (current[c] - baseline[c]) * math.log(current[c] / baseline[c])
        for c in categories
    )


def kl_divergence(
    baseline_labels: list[str],
    current_labels: list[str],
    categories: list[str],
) -> float:
    """KL(current || baseline): how surprised a model trained on `baseline`
    would be, on average, by draws from `current`."""
    baseline = _distribution(baseline_labels, categories)
    current = _distribution(current_labels, categories)
    return sum(current[c] * math.log(current[c] / baseline[c]) for c in categories)


def interpret_psi(psi: float) -> str:
    if psi < 0.1:
        return "stable -- no action needed"
    if psi < 0.25:
        return "moderate shift -- monitor, consider re-annotating a fresh sample"
    return "major shift -- treat current model calibration as unverified, re-validate against a fresh golden sample"
