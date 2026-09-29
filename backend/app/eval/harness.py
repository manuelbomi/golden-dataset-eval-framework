"""Evaluate a model/prompt version against the golden set.

The harness takes a list of (golden_label, predicted_label, confidence)
records -- one per golden example the candidate model was run against --
and produces a report with per-class precision/recall/F1, a confusion
matrix, and calibration (via app.metrics.calibration). `eval_gate.py`
wraps this report with pass/fail thresholds so it can be used as an
automated CI gate; this module stays threshold-free and side-effect-free
so it's also usable interactively (a notebook, a one-off script) without
dragging in exit-code semantics.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.metrics.calibration import CalibrationReport, compute_calibration


@dataclass
class PredictionRecord:
    golden_label: str
    predicted_label: str
    confidence: float


@dataclass
class ClassReport:
    label: str
    precision: float
    recall: float
    f1: float
    support: int  # number of golden examples with this true label


@dataclass
class EvalReport:
    overall_accuracy: float
    macro_f1: float
    per_class: list[ClassReport]
    confusion_matrix: dict[str, dict[str, int]]  # confusion[true][pred] = count
    calibration: CalibrationReport
    n_examples: int


def evaluate(records: list[PredictionRecord], labels: list[str]) -> EvalReport:
    if not records:
        raise ValueError("cannot evaluate on zero records")

    confusion: dict[str, dict[str, int]] = {t: {p: 0 for p in labels} for t in labels}
    for r in records:
        if r.golden_label not in labels:
            raise ValueError(f"unknown golden label {r.golden_label!r}")
        if r.predicted_label not in labels:
            raise ValueError(f"unknown predicted label {r.predicted_label!r}")
        confusion[r.golden_label][r.predicted_label] += 1

    per_class: list[ClassReport] = []
    f1_sum = 0.0
    for label in labels:
        true_positive = confusion[label][label]
        predicted_positive = sum(confusion[t][label] for t in labels)
        actual_positive = sum(confusion[label][p] for p in labels)

        precision = true_positive / predicted_positive if predicted_positive else 0.0
        recall = true_positive / actual_positive if actual_positive else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        per_class.append(
            ClassReport(
                label=label,
                precision=precision,
                recall=recall,
                f1=f1,
                support=actual_positive,
            )
        )
        f1_sum += f1

    correct = sum(r.golden_label == r.predicted_label for r in records)
    overall_accuracy = correct / len(records)
    macro_f1 = f1_sum / len(labels)

    calibration = compute_calibration(
        correct=[r.golden_label == r.predicted_label for r in records],
        confidences=[r.confidence for r in records],
    )

    return EvalReport(
        overall_accuracy=overall_accuracy,
        macro_f1=macro_f1,
        per_class=per_class,
        confusion_matrix=confusion,
        calibration=calibration,
        n_examples=len(records),
    )
