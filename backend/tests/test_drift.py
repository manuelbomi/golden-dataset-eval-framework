from __future__ import annotations

import pytest

from app.drift import interpret_psi, kl_divergence, population_stability_index

CATEGORIES = ["A", "B", "C"]


def test_identical_distributions_have_near_zero_psi_and_kl():
    baseline = ["A"] * 50 + ["B"] * 30 + ["C"] * 20
    current = ["A"] * 50 + ["B"] * 30 + ["C"] * 20
    assert population_stability_index(baseline, current, CATEGORIES) == pytest.approx(
        0.0, abs=1e-3
    )
    assert kl_divergence(baseline, current, CATEGORIES) == pytest.approx(0.0, abs=1e-3)


def test_shifted_distribution_has_positive_psi():
    baseline = ["A"] * 50 + ["B"] * 30 + ["C"] * 20
    current = ["A"] * 10 + ["B"] * 10 + ["C"] * 80  # C now dominates
    psi = population_stability_index(baseline, current, CATEGORIES)
    assert psi > 0.25
    assert "major shift" in interpret_psi(psi)


def test_kl_divergence_is_nonnegative():
    baseline = ["A"] * 40 + ["B"] * 40 + ["C"] * 20
    current = ["A"] * 20 + ["B"] * 60 + ["C"] * 20
    assert kl_divergence(baseline, current, CATEGORIES) >= 0
