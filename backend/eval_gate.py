#!/usr/bin/env python
"""CI-usable evaluation gate: run a candidate model's predictions against
the golden set and exit non-zero if it regresses past configured
thresholds. Meant to be wired into a pipeline as a required check --
see docs/PRODUCTION.md for a GitHub Actions job that runs this before a
model/prompt version is allowed to be promoted.

Input format: a JSON file that is a list of objects:
    {"golden_label": "OBJECTION", "predicted_label": "OBJECTION", "confidence": 0.87}

Usage:
    python eval_gate.py predictions.json
    python eval_gate.py predictions.json --min-macro-f1 0.75 --max-ece 0.10
    python eval_gate.py predictions.json --min-per-class-recall COMPLIANCE_RISK=0.95

Exit code 0 = pass, 1 = fail (thresholds not met), 2 = bad input.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.eval.harness import EvalReport, PredictionRecord, evaluate
from app.taxonomy import SIGNAL_LABELS


def load_records(path: Path) -> list[PredictionRecord]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        PredictionRecord(
            golden_label=r["golden_label"],
            predicted_label=r["predicted_label"],
            confidence=float(r["confidence"]),
        )
        for r in raw
    ]


def check_thresholds(
    report: EvalReport,
    min_macro_f1: float,
    max_ece: float,
    min_per_class_recall: dict[str, float],
) -> list[str]:
    """Returns a list of human-readable failure reasons; empty = pass."""
    failures: list[str] = []

    if report.macro_f1 < min_macro_f1:
        failures.append(
            f"macro F1 {report.macro_f1:.4f} is below required minimum {min_macro_f1:.4f}"
        )
    if report.calibration.ece > max_ece:
        failures.append(
            f"ECE {report.calibration.ece:.4f} exceeds allowed maximum {max_ece:.4f}"
        )
    for label, required_recall in min_per_class_recall.items():
        class_report = next((c for c in report.per_class if c.label == label), None)
        if class_report is None:
            failures.append(f"threshold given for unknown label {label!r}")
            continue
        if class_report.recall < required_recall:
            failures.append(
                f"recall for {label} is {class_report.recall:.4f}, "
                f"below required minimum {required_recall:.4f}"
            )
    return failures


def _parse_per_class_recall(pairs: list[str]) -> dict[str, float]:
    result: dict[str, float] = {}
    for pair in pairs:
        label, _, value = pair.partition("=")
        if not value:
            raise argparse.ArgumentTypeError(
                f"expected LABEL=THRESHOLD, got {pair!r}"
            )
        result[label] = float(value)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("predictions", type=Path, help="path to predictions JSON")
    parser.add_argument("--min-macro-f1", type=float, default=0.70)
    parser.add_argument("--max-ece", type=float, default=0.15)
    parser.add_argument(
        "--min-per-class-recall",
        action="append",
        default=["COMPLIANCE_RISK=0.90"],
        metavar="LABEL=THRESHOLD",
        help="repeatable; defaults to requiring 0.90 recall on COMPLIANCE_RISK "
        "since a missed compliance-risk snippet is the costliest error class",
    )
    args = parser.parse_args(argv)

    if not args.predictions.exists():
        print(f"error: {args.predictions} does not exist", file=sys.stderr)
        return 2

    try:
        records = load_records(args.predictions)
    except (KeyError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: malformed predictions file: {exc}", file=sys.stderr)
        return 2

    report = evaluate(records, labels=SIGNAL_LABELS)
    per_class_recall = _parse_per_class_recall(args.min_per_class_recall)
    failures = check_thresholds(
        report,
        min_macro_f1=args.min_macro_f1,
        max_ece=args.max_ece,
        min_per_class_recall=per_class_recall,
    )

    print(f"n_examples      : {report.n_examples}")
    print(f"overall_accuracy: {report.overall_accuracy:.4f}")
    print(f"macro_f1        : {report.macro_f1:.4f}")
    print(f"ece             : {report.calibration.ece:.4f}")
    for c in report.per_class:
        print(
            f"  {c.label:<17} precision={c.precision:.3f} recall={c.recall:.3f} "
            f"f1={c.f1:.3f} support={c.support}"
        )

    if failures:
        print("\nGATE FAILED:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print("\nGATE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
