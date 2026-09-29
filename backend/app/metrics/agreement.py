"""Inter-annotator agreement metrics, implemented from scratch.

Why not just report "percent agreement" (the fraction of items where
annotators picked the same label)?  Because percent agreement is inflated
by chance whenever one label dominates.  If 90% of conversation snippets
are NEUTRAL, two annotators who each guess NEUTRAL at random 90% of the
time will "agree" ~82% of the time on NEUTRAL alone, without having learned
anything about the taxonomy.  Cohen's and Fleiss' kappa both subtract out
the agreement you'd expect from chance, so a kappa near 0 means "no better
than guessing" even if percent agreement looks high.

These are implemented directly (rather than only calling a library) because
the formulas are short enough to read end-to-end and this repo's whole
point is to make the math inspectable, not just invoke a black box. Each
function is cross-checked in tests/test_agreement.py against known
textbook worked examples, and against `sklearn.metrics.cohen_kappa_score`
when scikit-learn is installed.
"""

from __future__ import annotations

from collections import Counter


def cohen_kappa(rater_a: list[str], rater_b: list[str]) -> float:
    """Cohen's kappa for two raters labeling the same N items.

    kappa = (p_o - p_e) / (1 - p_e)

    p_o (observed agreement) is just the fraction of items where the two
    raters picked the same label.

    p_e (expected agreement) is the agreement two raters would show by
    chance, GIVEN each rater's own marginal label frequencies: for each
    label k, the chance both raters independently pick k is
    P(rater_a picks k) * P(rater_b picks k); sum that product over all
    labels k to get the total chance-agreement probability.
    """
    if len(rater_a) != len(rater_b):
        raise ValueError("rater_a and rater_b must have the same length")
    n = len(rater_a)
    if n == 0:
        raise ValueError("cannot compute kappa on zero items")

    observed_agreement = sum(a == b for a, b in zip(rater_a, rater_b)) / n

    labels = sorted(set(rater_a) | set(rater_b))
    freq_a = Counter(rater_a)
    freq_b = Counter(rater_b)
    expected_agreement = sum(
        (freq_a[label] / n) * (freq_b[label] / n) for label in labels
    )

    if expected_agreement == 1.0:
        # Both raters always picked the same single label -- agreement was
        # never in question, so kappa is undefined by the formula (0/0).
        # By convention we treat perfect, trivial agreement as kappa = 1.0.
        return 1.0

    return (observed_agreement - expected_agreement) / (1 - expected_agreement)


def fleiss_kappa(annotations: list[list[str]]) -> float:
    """Fleiss' kappa for N >= 2 raters labeling the same set of items.

    `annotations` is one list per item, each containing the labels every
    rater assigned to that item (raters need not be the same people across
    items, and each item's list can have a different number of raters --
    the formula only needs *how many* raters, not *who*).

    For each item i, let n_i be the number of raters on that item and
    n_ik the count of raters who picked label k. The per-item agreement
    rate P_i is the fraction of all rater PAIRS on that item that agree:

        P_i = (sum_k n_ik * (n_ik - 1)) / (n_i * (n_i - 1))

    P_bar is the mean of P_i across items (observed agreement).

    P_bar_e (expected agreement by chance) uses the overall proportion
    p_k of all ratings that went to label k, across the whole dataset:

        P_bar_e = sum_k p_k^2

    kappa = (P_bar - P_bar_e) / (1 - P_bar_e), same shape as Cohen's kappa.
    """
    if not annotations:
        raise ValueError("cannot compute Fleiss' kappa on zero items")

    labels = sorted({label for item in annotations for label in item})
    if not labels:
        raise ValueError("no labels found in annotations")

    n_items = len(annotations)
    total_ratings = 0
    label_totals = {label: 0 for label in labels}
    per_item_agreement: list[float] = []

    for item in annotations:
        n_i = len(item)
        if n_i < 2:
            raise ValueError("every item needs at least 2 raters for Fleiss' kappa")
        counts = Counter(item)
        for label in labels:
            label_totals[label] += counts[label]
        total_ratings += n_i

        pair_agreements = sum(c * (c - 1) for c in counts.values())
        possible_pairs = n_i * (n_i - 1)
        per_item_agreement.append(pair_agreements / possible_pairs)

    p_bar = sum(per_item_agreement) / n_items
    p_bar_e = sum((label_totals[label] / total_ratings) ** 2 for label in labels)

    if p_bar_e == 1.0:
        return 1.0

    return (p_bar - p_bar_e) / (1 - p_bar_e)


def item_pairwise_agreement(labels: list[str]) -> float:
    """Raw agreement rate among raters on a SINGLE item: the fraction of all
    rater pairs that picked the same label. This is exactly the per-item
    P_i term inside Fleiss' kappa (see `fleiss_kappa` above) -- but on its
    own, for one item, it is NOT chance-corrected, because chance-correction
    needs label-frequency marginals estimated across many items. Use this
    for a live "do these N annotators agree on THIS item" check (e.g. to
    decide whether to finalize a golden example); use `cohen_kappa` /
    `fleiss_kappa` for "how good is agreement across the whole dataset",
    which is what actually needs the chance-correction.
    """
    n = len(labels)
    if n < 2:
        raise ValueError("need at least 2 raters to compute agreement")
    counts = Counter(labels)
    pair_agreements = sum(c * (c - 1) for c in counts.values())
    possible_pairs = n * (n - 1)
    return pair_agreements / possible_pairs


def interpret_kappa(kappa: float) -> str:
    """Landis & Koch (1977) benchmark scale -- a convention, not a law of
    nature, but the one most commonly cited when reporting kappa."""
    if kappa < 0:
        return "poor (worse than chance)"
    if kappa < 0.20:
        return "slight"
    if kappa < 0.40:
        return "fair"
    if kappa < 0.60:
        return "moderate"
    if kappa < 0.80:
        return "substantial"
    return "almost perfect"
