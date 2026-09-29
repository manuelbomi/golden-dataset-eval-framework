"""Expected Calibration Error (ECE) and reliability-diagram data, from scratch.

A model can have great accuracy and still be dangerous in a human-in-the-
loop system if its CONFIDENCE is untrustworthy: a model that says "92%
confident" should be right about 92% of the time it says that, averaged
over many predictions. If it's actually right only 60% of the time when
it claims 92% confidence, a downstream system (or a human) that trusts
that confidence score to decide "auto-apply vs. route to a human" will
mis-route constantly. ECE measures exactly that gap between stated
confidence and actual correctness.

Method: bin predictions by their confidence score into fixed-width bins
(e.g. [0.0-0.1), [0.1-0.2), ... [0.9-1.0]). Within each bin, compare the
bin's mean confidence to the bin's actual accuracy (fraction correct).
ECE is the weighted average of |confidence - accuracy| across bins,
weighted by how many predictions fell in each bin.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CalibrationBin:
    bin_lower: float
    bin_upper: float
    count: int
    mean_confidence: float
    accuracy: float

    @property
    def gap(self) -> float:
        return abs(self.mean_confidence - self.accuracy)


@dataclass
class CalibrationReport:
    ece: float
    bins: list[CalibrationBin]


def compute_calibration(
    correct: list[bool],
    confidences: list[float],
    n_bins: int = 10,
) -> CalibrationReport:
    """`correct[i]` is whether prediction i matched the golden label;
    `confidences[i]` is the model's stated confidence (0.0-1.0) for that
    prediction. Returns the overall ECE plus per-bin detail suitable for
    plotting a reliability diagram (confidence on x, accuracy on y --
    a perfectly calibrated model traces the y=x diagonal).
    """
    if len(correct) != len(confidences):
        raise ValueError("correct and confidences must have the same length")
    n = len(correct)
    if n == 0:
        raise ValueError("cannot compute calibration on zero predictions")
    if any(not (0.0 <= c <= 1.0) for c in confidences):
        raise ValueError("confidences must all be in [0.0, 1.0]")

    edges = [i / n_bins for i in range(n_bins + 1)]
    bins: list[CalibrationBin] = []
    ece_sum = 0.0

    for b in range(n_bins):
        lower, upper = edges[b], edges[b + 1]
        # The top bin's upper edge is inclusive so a confidence of exactly
        # 1.0 lands in the last bin instead of falling out of every bin.
        in_bin = [
            i
            for i in range(n)
            if (lower <= confidences[i] < upper)
            or (b == n_bins - 1 and confidences[i] == upper)
        ]
        count = len(in_bin)
        if count == 0:
            bins.append(CalibrationBin(lower, upper, 0, 0.0, 0.0))
            continue

        mean_confidence = sum(confidences[i] for i in in_bin) / count
        accuracy = sum(correct[i] for i in in_bin) / count
        bins.append(CalibrationBin(lower, upper, count, mean_confidence, accuracy))
        ece_sum += (count / n) * abs(mean_confidence - accuracy)

    return CalibrationReport(ece=ece_sum, bins=bins)
