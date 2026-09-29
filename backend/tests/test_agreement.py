"""Cross-checked against known textbook worked examples so a bug in the
from-scratch math (app.metrics.agreement) can't hide behind "it ran without
crashing." Sources are cited per test.
"""

from __future__ import annotations

import pytest

from app.metrics.agreement import (
    cohen_kappa,
    fleiss_kappa,
    interpret_kappa,
    item_pairwise_agreement,
)


def test_cohen_kappa_perfect_agreement():
    a = ["yes", "no", "yes", "no", "yes"]
    b = ["yes", "no", "yes", "no", "yes"]
    assert cohen_kappa(a, b) == pytest.approx(1.0)


def test_cohen_kappa_textbook_example():
    """Classic worked example (two raters, two categories) with a known
    kappa of 0.4 -- widely reproduced, e.g. in Fleiss, Levin & Paik,
    'Statistical Methods for Rates and Proportions', 3rd ed., the 2x2
    psychiatric-diagnosis table with cell counts (a=20, b=5, c=10, d=15,
    n=50) reduces to kappa = 0.4 by hand calculation:
      p_o = (20+15)/50 = 0.70
      p_e = (25/50 * 30/50) + (25/50 * 20/50) = 0.30 + 0.20 = 0.50
      kappa = (0.70 - 0.50) / (1 - 0.50) = 0.40
    """
    rater_a = ["yes"] * 25 + ["no"] * 25
    # Construct rater_b so the 2x2 confusion table is a=20 (yes/yes),
    # b=5 (yes/no), c=10 (no/yes), d=15 (no/no):
    rater_b = ["yes"] * 20 + ["no"] * 5 + ["yes"] * 10 + ["no"] * 15
    assert cohen_kappa(rater_a, rater_b) == pytest.approx(0.4, abs=1e-9)


def test_cohen_kappa_matches_sklearn_when_available():
    sklearn_metrics = pytest.importorskip("sklearn.metrics")
    a = ["A", "B", "C", "A", "B", "C", "A", "A", "B", "C"]
    b = ["A", "B", "B", "A", "B", "C", "C", "A", "B", "A"]
    ours = cohen_kappa(a, b)
    theirs = sklearn_metrics.cohen_kappa_score(a, b)
    assert ours == pytest.approx(theirs, abs=1e-9)


def test_fleiss_kappa_hand_computed_example():
    """3 items, 3 raters, 2 categories -- small enough to verify by hand:

    item1 = [A,A,A]: 3 agreeing pairs out of 3 possible -> P_1 = 1
    item2 = [A,A,B]: 1 agreeing pair (the two A's) out of 3 possible -> P_2 = 1/3
    item3 = [B,B,B]: P_3 = 1

    P_bar = (1 + 1/3 + 1) / 3 = 7/9

    Label totals across all 9 ratings: A=5, B=4 -> p_A=5/9, p_B=4/9
    P_bar_e = p_A^2 + p_B^2 = 25/81 + 16/81 = 41/81

    kappa = (P_bar - P_bar_e) / (1 - P_bar_e)
          = (7/9 - 41/81) / (1 - 41/81)
          = (22/81) / (40/81) = 22/40 = 0.55
    """
    annotations = [["A", "A", "A"], ["A", "A", "B"], ["B", "B", "B"]]
    assert fleiss_kappa(annotations) == pytest.approx(0.55, abs=1e-9)


def test_fleiss_kappa_matches_statsmodels_when_available():
    sm = pytest.importorskip("statsmodels.stats.inter_rater")
    import numpy as np

    # 4 items x 3 raters x 3 categories (A, B, C), built so every item has
    # exactly 3 raters (statsmodels' fleiss_kappa expects a fixed n_i table).
    annotations = [
        ["A", "A", "B"],
        ["B", "C", "C"],
        ["A", "B", "C"],
        ["C", "C", "C"],
    ]
    categories = ["A", "B", "C"]
    table = np.array(
        [[row.count(c) for c in categories] for row in annotations]
    )
    theirs = sm.fleiss_kappa(table, method="fleiss")
    ours = fleiss_kappa(annotations)
    assert ours == pytest.approx(theirs, abs=1e-9)


def test_item_pairwise_agreement_unanimous():
    assert item_pairwise_agreement(["A", "A", "A"]) == pytest.approx(1.0)


def test_item_pairwise_agreement_two_raters_split():
    assert item_pairwise_agreement(["A", "B"]) == pytest.approx(0.0)


def test_item_pairwise_agreement_three_raters_majority():
    # pairs: (A,A) agree, (A,B) disagree, (A,B) disagree -> 1/3 pairs agree
    assert item_pairwise_agreement(["A", "A", "B"]) == pytest.approx(1 / 3)


@pytest.mark.parametrize(
    "kappa,expected",
    [
        (-0.1, "poor"),
        (0.1, "slight"),
        (0.3, "fair"),
        (0.5, "moderate"),
        (0.7, "substantial"),
        (0.9, "almost perfect"),
    ],
)
def test_interpret_kappa(kappa, expected):
    assert expected in interpret_kappa(kappa)


def test_cohen_kappa_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        cohen_kappa(["A"], ["A", "B"])


def test_fleiss_kappa_requires_at_least_two_raters_per_item():
    with pytest.raises(ValueError):
        fleiss_kappa([["A"]])
