#!/usr/bin/env python
"""Demonstrate the agreement metrics on real, computed numbers.

This generates a synthetic "true" label per item from the taxonomy, then
simulates N annotators independently labeling each item: each annotator
picks the true label with probability `skill`, and a uniformly random
OTHER label otherwise. `--skill` controls how good the simulated annotators
are, so you can see kappa respond to it directly:

    python scripts/simulate_annotators.py --skill 0.95 --n-items 300 --n-raters 3
    python scripts/simulate_annotators.py --skill 0.55 --n-items 300 --n-raters 3

This is synthetic data for demonstrating the MATH, not a claim about how
well any real model or human annotator team performs -- the README states
this explicitly next to the numbers this script prints.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

# Allow running as `python scripts/simulate_annotators.py` from backend/
# without needing PYTHONPATH set -- backend/ (the parent of scripts/) has
# the `app` package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.metrics.agreement import fleiss_kappa, interpret_kappa
from app.taxonomy import SIGNAL_LABELS


def simulate(
    n_items: int, n_raters: int, skill: float, seed: int
) -> list[list[str]]:
    rng = random.Random(seed)
    annotations: list[list[str]] = []
    for _ in range(n_items):
        true_label = rng.choice(SIGNAL_LABELS)
        raters_labels = []
        for _ in range(n_raters):
            if rng.random() < skill:
                raters_labels.append(true_label)
            else:
                other_labels = [l for l in SIGNAL_LABELS if l != true_label]
                raters_labels.append(rng.choice(other_labels))
        annotations.append(raters_labels)
    return annotations


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-items", type=int, default=300)
    parser.add_argument("--n-raters", type=int, default=3)
    parser.add_argument(
        "--skill",
        type=float,
        default=0.85,
        help="probability each simulated annotator picks the 'true' label",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    annotations = simulate(args.n_items, args.n_raters, args.skill, args.seed)
    kappa = fleiss_kappa(annotations)

    print(f"n_items={args.n_items} n_raters={args.n_raters} skill={args.skill} seed={args.seed}")
    print(f"Fleiss' kappa = {kappa:.4f} ({interpret_kappa(kappa)})")


if __name__ == "__main__":
    main()
