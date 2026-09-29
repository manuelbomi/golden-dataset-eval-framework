# Running this in production

This document covers the four things that turn "an annotation tool with an
eval script" into an operational quality-control system: wiring the gate
into a promotion pipeline, monitoring for drift between golden-set and
live-traffic distributions, scaling the annotation operation itself, and
data governance for the golden set.

## 1. Wiring `eval_gate.py` into promotion as a required check

The gate is a plain CLI with a real exit code (0 = pass, 1 = threshold
failure, 2 = bad input) -- see `.github/workflows/ci.yml`'s
`eval-gate-demo` job for a live demonstration that it actually enforces
its thresholds, not just a description of what it's supposed to do.

A model/prompt-promotion pipeline wires it as a required job. Example
(adapt the "generate predictions" step to however your candidate model
actually runs inference against the golden set's documents):

```yaml
# .github/workflows/promote-model.yml
name: Promote model version
on:
  workflow_dispatch:
    inputs:
      model_version:
        required: true

jobs:
  eval-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r backend/requirements.txt
      # Runs the candidate model version against every document in the
      # current golden set, writing (golden_label, predicted_label,
      # confidence) triples -- this step is specific to your model-serving
      # setup and lives outside this repo.
      - name: Generate predictions against golden set
        run: |
          python scripts/run_candidate_model.py \
            --model-version "${{ inputs.model_version }}" \
            --golden-set backend/tests/fixtures/current_golden_set.json \
            --out predictions.json
      - name: Evaluate against golden set (required check)
        working-directory: backend
        run: |
          python eval_gate.py ../predictions.json \
            --min-macro-f1 0.75 \
            --max-ece 0.10 \
            --min-per-class-recall COMPLIANCE_RISK=0.95
      - name: Promote
        if: success()
        run: python scripts/promote_model.py --model-version "${{ inputs.model_version }}"
```

Because the promotion step only runs `if: success()`, a threshold failure
in `eval_gate.py` blocks promotion automatically -- no one has to remember
to check a dashboard first.

## 2. Monitoring production drift between golden-set refreshes

The eval gate only tells you the model still matches the golden set as of
the last time that golden set was built. Live conversation content shifts
underneath a static golden set: new products, new sales scripts, seasonal
patterns, a competitor's promotion changing what objections sound like.
`app/drift.py` implements two standard drift metrics against the model's
*predicted* label distribution on a live sample (predictions, not human
labels, since live traffic isn't annotated in real time):

```python
from app.drift import population_stability_index, interpret_psi

golden_label_distribution = [...]     # golden set's true labels
live_predicted_labels = [...]         # model's predictions on a recent live sample

psi = population_stability_index(golden_label_distribution, live_predicted_labels, categories=SIGNAL_LABELS)
print(interpret_psi(psi))
```

Operational rule of thumb (from credit-risk modeling, where PSI
originates): PSI < 0.1 is stable, 0.1-0.25 is a moderate shift worth
watching, > 0.25 is a major shift -- at that point, treat the model's
current calibration as unverified and prioritize a fresh golden-set sample
over trusting the existing eval-gate pass. Schedule this as a recurring
job (e.g. daily) over a rolling window of live predictions, alerting when
PSI crosses 0.25.

## 3. Scaling the annotation operation

Beyond a handful of annotators, three things need explicit tracking that
this repo's schema already supports but a production deployment should
build dashboards around:

- **Task assignment**: extend `AnnotationTask` with an `assigned_to` /
  `assigned_at` pair and a claim-expiry sweep (a task claimed but not
  completed within N hours returns to the pool) so tasks don't silently
  stall with one annotator.
- **Annotator throughput and quality**: aggregate `Annotation.annotator_id`
  by count-per-day (throughput) and, more importantly, by that
  annotator's rate of being on the *minority* side of an adjudicated
  disagreement (quality) -- a consistently-outlier annotator needs
  retraining on the taxonomy, not just more tasks.
- **Inter-annotator agreement trends over time**: run
  `scripts/simulate_annotators.py`'s underlying `fleiss_kappa` call
  against real completed-task data on a schedule, and alert if kappa
  drops -- a falling kappa usually means the taxonomy has started to
  drift from what the domain actually needs (see ADR 0001), which is a
  taxonomy-design problem, not something more annotation volume fixes.

## 4. Data governance

- **Golden-set versioning**: `GoldenExample.version` exists so a
  golden-set refresh doesn't silently overwrite history -- eval reports
  should always record which golden-set version they ran against, so a
  metric change is attributable to "the model changed" vs. "the golden
  set changed" (these require very different responses).
- **PII scrubbing before data leaves a secure perimeter**: this repo's
  demo data is entirely synthetic. A real deployment ingesting real
  conversation snippets must run PII/PHI scrubbing (name, account number,
  phone number redaction) inside the secure environment where the raw
  conversation data lives, BEFORE any snippet is written to
  `documents.text` in a system annotators (who may not all hold the same
  data-access clearance as the original conversation) can read. Treat the
  scrubbing step as part of the ingestion boundary, not as a
  nice-to-have cleanup pass.
- **Retention and access**: golden examples derived from real customer
  conversations inherit whatever retention and access-control
  requirements applied to the source data; a golden set does not become
  "just training data" free of those obligations merely because it's been
  relabeled.
