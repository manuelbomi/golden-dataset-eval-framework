from __future__ import annotations

import pytest

from app.eval.harness import PredictionRecord, evaluate

LABELS = ["A", "B"]


def test_perfect_predictions():
    records = [
        PredictionRecord("A", "A", 0.9),
        PredictionRecord("B", "B", 0.9),
        PredictionRecord("A", "A", 0.9),
    ]
    report = evaluate(records, LABELS)
    assert report.overall_accuracy == pytest.approx(1.0)
    assert report.macro_f1 == pytest.approx(1.0)
    for c in report.per_class:
        assert c.precision == pytest.approx(1.0)
        assert c.recall == pytest.approx(1.0)


def test_confusion_matrix_and_precision_recall():
    # 2 true A (1 predicted A, 1 predicted B); 2 true B (both predicted B)
    records = [
        PredictionRecord("A", "A", 0.6),
        PredictionRecord("A", "B", 0.6),
        PredictionRecord("B", "B", 0.6),
        PredictionRecord("B", "B", 0.6),
    ]
    report = evaluate(records, LABELS)
    assert report.confusion_matrix["A"]["A"] == 1
    assert report.confusion_matrix["A"]["B"] == 1
    assert report.confusion_matrix["B"]["B"] == 2

    class_a = next(c for c in report.per_class if c.label == "A")
    class_b = next(c for c in report.per_class if c.label == "B")

    assert class_a.recall == pytest.approx(0.5)  # 1 of 2 true A's found
    assert class_a.precision == pytest.approx(1.0)  # every predicted-A was right
    assert class_b.recall == pytest.approx(1.0)
    assert class_b.precision == pytest.approx(2 / 3)


def test_rejects_unknown_label():
    with pytest.raises(ValueError):
        evaluate([PredictionRecord("A", "Z", 0.5)], LABELS)


def test_rejects_empty_records():
    with pytest.raises(ValueError):
        evaluate([], LABELS)
