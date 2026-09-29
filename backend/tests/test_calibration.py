from __future__ import annotations

import pytest

from app.metrics.calibration import compute_calibration


def test_perfect_calibration_zero_ece():
    # Every prediction is correct AND stated confidence 1.0 -- bin accuracy
    # (1.0) exactly matches bin mean confidence (1.0), so the gap is zero.
    correct = [True] * 10
    confidences = [1.0] * 10
    report = compute_calibration(correct, confidences, n_bins=10)
    assert report.ece == pytest.approx(0.0, abs=1e-9)


def test_hand_computed_two_bin_example():
    """Hand-computed example with 2 bins for a traceable worked check:

    4 predictions at confidence 0.9: 3 correct, 1 wrong -> bin accuracy 0.75,
      gap = |0.9 - 0.75| = 0.15, weight = 4/8 = 0.5
    4 predictions at confidence 0.4: 1 correct, 3 wrong -> bin accuracy 0.25,
      gap = |0.4 - 0.25| = 0.15, weight = 4/8 = 0.5

    ECE = 0.5*0.15 + 0.5*0.15 = 0.15
    """
    confidences = [0.9, 0.9, 0.9, 0.9, 0.4, 0.4, 0.4, 0.4]
    correct = [True, True, True, False, True, False, False, False]
    report = compute_calibration(correct, confidences, n_bins=2)
    assert report.ece == pytest.approx(0.15, abs=1e-9)


def test_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        compute_calibration([True], [0.5, 0.6])


def test_rejects_out_of_range_confidence():
    with pytest.raises(ValueError):
        compute_calibration([True], [1.5])


def test_confidence_of_exactly_one_lands_in_last_bin():
    report = compute_calibration([True], [1.0], n_bins=10)
    assert report.bins[-1].count == 1
