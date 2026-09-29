"""Exercises eval_gate.py as a real CLI (subprocess), the same way CI does,
so a bug in argument parsing or exit-code plumbing shows up here instead of
only in a live pipeline run."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
FIXTURES = BACKEND_DIR / "tests" / "fixtures"


def run_gate(fixture_name: str, *extra_args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(BACKEND_DIR / "eval_gate.py"), str(FIXTURES / fixture_name), *extra_args],
        capture_output=True,
        text=True,
        cwd=BACKEND_DIR,
    )


def test_passing_predictions_exit_zero():
    result = run_gate("passing_predictions.json", "--min-macro-f1", "0.5", "--max-ece", "0.5")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "GATE PASSED" in result.stdout


def test_failing_predictions_exit_nonzero():
    result = run_gate("failing_predictions.json")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "GATE FAILED" in result.stderr


def test_missing_file_exits_two():
    result = run_gate("does_not_exist.json")
    assert result.returncode == 2


def test_per_class_recall_threshold_can_fail_gate_even_with_good_macro_f1():
    # passing_predictions.json has COMPLIANCE_RISK correct 2/2 (recall 1.0),
    # so demanding recall > 1.0 must fail the gate even though the rest passes.
    result = run_gate(
        "passing_predictions.json",
        "--min-macro-f1", "0.1",
        "--max-ece", "0.9",
        "--min-per-class-recall", "COMPLIANCE_RISK=1.01",
    )
    assert result.returncode == 1
    assert "COMPLIANCE_RISK" in result.stderr
