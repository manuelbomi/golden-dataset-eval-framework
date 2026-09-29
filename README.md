# Golden Dataset & Evaluation Framework for Conversational AI

A human-in-the-loop pipeline for turning raw conversation snippets into a
**golden dataset** (labels multiple people agree on, not just one person's
opinion), plus a **model evaluation harness** and a **CI-usable eval gate**
that blocks a model or prompt version from shipping if it regresses against
that golden set.

This repo exists to make two ideas concrete rather than just describe them:

1. **"Agreement" and "calibration" are measurable, not vibes.** Inter-annotator
   agreement (Cohen's/Fleiss' kappa) and model confidence calibration
   (Expected Calibration Error) are both implemented from scratch here, with
   the math commented inline and cross-checked against `scikit-learn` /
   `statsmodels` in tests -- so you can read exactly what "our annotators
   agree well" or "the model is well-calibrated" actually means arithmetically,
   not just accept a library's black-box number.
2. **An eval gate should be a real, runnable thing, not a policy document.**
   `eval_gate.py` is a CLI with a real exit code, exercised in CI against a
   fixture engineered to pass and a fixture engineered to fail -- see
   [`.github/workflows/ci.yml`](.github/workflows/ci.yml)'s `eval-gate-demo`
   job.

## Why agreement and calibration, not just "accuracy"?

If you only ever ask "is annotator B right?", you need a ground truth to
compare against -- but for a brand-new taxonomy, there IS no ground truth
yet; agreement between independent annotators is the closest available
proxy for "is this taxonomy usable and are people applying it consistently."
And if you only ever report a model's accuracy, you learn nothing about
whether its *confidence scores* can be trusted -- which matters enormously
the moment a downstream system uses confidence to decide "auto-apply this
prediction" vs. "route it to a human." See
[`docs/adr/0001-kappa-over-percent-agreement.md`](docs/adr/0001-kappa-over-percent-agreement.md)
and
[`docs/adr/0002-ece-over-accuracy.md`](docs/adr/0002-ece-over-accuracy.md)
for the full reasoning.

## The pipeline

```mermaid
flowchart LR
    doc[Document\nconversation snippet] --> task[Annotation Task]
    task --> ann1[Annotator A\nlabels]
    task --> ann2[Annotator B\nlabels]
    ann1 --> agree{Agreement\n>= threshold?}
    ann2 --> agree
    agree -- yes --> golden[(Golden Example)]
    agree -- no --> adjudicate[Adjudication\nside-by-side review]
    adjudicate --> golden
    golden --> gate[eval_gate.py\nprecision/recall/F1 + ECE]
    gate -- pass --> promote[Promote model/prompt version]
    gate -- fail --> block[Block promotion]
```

- **Annotate** -- annotators pick one or more labels from a fixed taxonomy
  (`app/taxonomy.py`: `OBJECTION`, `BUYING_SIGNAL`, `COMPLIANCE_RISK`,
  `QUESTION`, `ACTION_ITEM`, `NEUTRAL`) for each conversation snippet.
- **Agree / adjudicate** -- once enough annotators have labeled a task, the
  per-item rater-pair agreement rate decides whether the task's label is
  finalized as a golden example or routed to adjudication for a human to
  resolve the disagreement directly (see `AdjudicationView` in the frontend).
- **Golden set** -- the frozen, agreed-upon dataset every future model or
  prompt version is measured against.
- **Eval gate** -- `eval_gate.py` runs a candidate model's predictions
  against the golden set and fails the build if macro F1, calibration
  (ECE), or a specific class's recall regress past configured thresholds.

## Real numbers from this repo (not hypothetical)

These were computed by actually running the code in this repo, not written
by hand. Reproduce them with the commands shown.

**Inter-annotator agreement at different simulated annotator skill levels**
(`scripts/simulate_annotators.py` generates synthetic multi-annotator labels
with a controllable "skill" -- the probability each simulated annotator
picks the true label -- so you can see kappa respond to annotation quality
directly; this is a demonstration of the math on synthetic data, not a
claim about any real annotator team):

| Command | Fleiss' kappa | Interpretation |
|---|---|---|
| `--skill 0.55 --n-items 300 --n-raters 3` | 0.2233 | fair |
| `--skill 0.85 --n-items 300 --n-raters 3` | 0.6717 | substantial |
| `--skill 0.95 --n-items 300 --n-raters 3` | 0.8812 | almost perfect |

**`eval_gate.py` against the two fixtures in `backend/tests/fixtures/`**
(`passing_predictions.json` and `failing_predictions.json` -- 12 hand-built
prediction records each, used both as a CI demonstration and as the source
of these numbers):

```
$ python eval_gate.py tests/fixtures/passing_predictions.json --min-macro-f1 0.5 --max-ece 0.5
n_examples      : 12
overall_accuracy: 0.8333
macro_f1        : 0.8222
ece             : 0.2258
GATE PASSED

$ python eval_gate.py tests/fixtures/failing_predictions.json
n_examples      : 12
overall_accuracy: 0.0833
macro_f1        : 0.0556
ece             : 0.4783
GATE FAILED:
  - macro F1 0.0556 is below required minimum 0.7000
  - ECE 0.4783 exceeds allowed maximum 0.1500
  - recall for COMPLIANCE_RISK is 0.0000, below required minimum 0.9000
```

Backend test suite: **36 passed** (`pytest -q`), including hand-verified
worked examples for Cohen's kappa, Fleiss' kappa, and ECE, plus
cross-checks against `scikit-learn.metrics.cohen_kappa_score` and
`statsmodels.stats.inter_rater.fleiss_kappa` (these two run when those
optional packages are installed; they're skipped, not faked, otherwise).
Frontend: `npm run build` succeeds, producing a 171 KB (56 KB gzipped) JS
bundle.

## Repo layout

```
backend/
  app/
    taxonomy.py        # the fixed label set, single source of truth
    models.py           # SQLAlchemy: documents -> tasks -> annotations -> golden_examples
    metrics/
      agreement.py       # Cohen's kappa, Fleiss' kappa, per-item agreement -- from scratch
      calibration.py      # Expected Calibration Error -- from scratch
    eval/harness.py     # precision/recall/F1/confusion-matrix/ECE over predictions
    drift.py             # PSI / KL-divergence for production drift monitoring
    api/                 # FastAPI routers: documents, annotations, golden
  eval_gate.py          # CI-usable CLI wrapping the harness with pass/fail thresholds
  scripts/
    simulate_annotators.py  # generates the kappa numbers above
    seed_demo.py              # seeds demo documents against a running API
  tests/                 # pytest, incl. tests/fixtures/ used by eval_gate demos
  alembic/                # Postgres migrations (SQLite dev DB uses create_all instead)
frontend/
  src/
    components/          # TaskQueue, LabelPicker, AdjudicationView
    pages/                # QueuePage (annotate), AdjudicationPage, GoldenPage
docs/
  PRODUCTION.md          # promotion pipeline, drift monitoring, scaling, governance
  adr/                    # why kappa, why ECE, why gate-in-CI
docker-compose.yml
.github/workflows/ci.yml
```

## Setup & run

### Quickest: Docker Compose (Postgres + backend + frontend)

```bash
docker compose up --build
# backend:  http://localhost:8000  (docs at /docs)
# frontend: http://localhost:8080
python backend/scripts/seed_demo.py --base-url http://localhost:8000
```

### Local dev (SQLite, no Docker)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload   # creates ./golden_dataset.db automatically
```

```bash
cd frontend
npm install
npm run dev   # proxies /documents, /tasks, etc. to localhost:8000, see vite.config.ts
```

### Running the tests and demos yourself

```bash
cd backend
pytest -q
python scripts/simulate_annotators.py --skill 0.85 --n-items 300 --n-raters 3
python eval_gate.py tests/fixtures/passing_predictions.json --min-macro-f1 0.5 --max-ece 0.5
python eval_gate.py tests/fixtures/failing_predictions.json   # exits 1 on purpose
```

### Postgres migrations

```bash
cd backend
DATABASE_URL=postgresql+psycopg2://golden:golden@localhost:5432/golden_dataset alembic upgrade head
```

## Production

See [`docs/PRODUCTION.md`](docs/PRODUCTION.md) for: wiring `eval_gate.py`
into a model/prompt promotion pipeline as a required check (with a
complete example GitHub Actions job), monitoring production drift between
golden-set refreshes with `app/drift.py`, scaling annotation operations
(task assignment, annotator throughput/quality tracking), and data
governance (golden-set versioning, PII scrubbing before data leaves a
secure perimeter).

See [`docs/adr/`](docs/adr/) for the three design decisions worth
understanding before changing the metrics: kappa over percent agreement,
ECE over accuracy alone, and enforcing the gate in CI rather than relying
on manual sign-off.

## License

MIT -- see [LICENSE](./LICENSE).

---


### Thank you for reading

#### Please consider giving a star if you find the repo useful. Thank you.

---

### **AUTHOR'S BACKGROUND**
### Author's Name:  Emmanuel Oyekanlu
```
Skillset:   I have experience spanning several years in data science, enterprise AI architecture and solutions, developing scalable enterprise data pipelines,
enterprise solution architecture, architecting enterprise systems data and AI applications,
software and AI solution design and deployments, data engineering, industrial intelligent vision systems, high performance computing (GPU, CUDA), machine learning,
NLP, Agentic-AI and LLM applications as well as deploying scalable solutions (apps) on-prem and in the cloud.

I can be reached through: manuelbomi@yahoo.com

Publications:  https://scholar.google.com/citations?user=S-jTMfkAAAAJ&hl=en
LinkedIn:  https://www.linkedin.com/in/emmanuel-oyekanlu-6ba98616
Github:  https://github.com/manuelbomi

```
[![Icons](https://skillicons.dev/icons?i=aws,azure,gcp,scala,mongodb,redis,cassandra,kafka,anaconda,matlab,nodejs,django,py,c,anaconda,git,github,mysql,docker,kubernetes&theme=dark)](https://skillicons.dev)
