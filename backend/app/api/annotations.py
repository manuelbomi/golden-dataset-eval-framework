"""Submitting an annotation and the resulting finalize-or-adjudicate logic.

This is the one place the annotation pipeline actually *uses* the agreement
metrics in `app.metrics.agreement` for something consequential: once a task
has `MIN_ANNOTATORS_PER_TASK` annotations, we compute the raw per-item
rater-pair agreement rate (`item_pairwise_agreement`) over the primary label
each annotator picked, and either finalize a GoldenExample (agreement >=
threshold) or flag the task for human adjudication (agreement < threshold).

Note this is deliberately NOT the chance-corrected Cohen's/Fleiss' kappa --
kappa needs label-frequency marginals estimated across many items, which a
single task doesn't have. Dataset-level, chance-corrected kappa (the number
that actually answers "how good is our annotation process overall") is
computed across the whole golden set in scripts/simulate_annotators.py and
is what you should report externally, e.g. in a data card.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import get_settings
from app.db import get_db
from app.metrics.agreement import item_pairwise_agreement

router = APIRouter(tags=["annotations"])
settings = get_settings()


def _primary_label(annotation: models.Annotation) -> str:
    """Agreement metrics need one label per rater per item. Annotators can
    multi-select (e.g. both BUYING_SIGNAL and QUESTION), so we compare
    agreement on each annotator's first-listed ("primary") label -- the
    label list order is meaningful UI-side (see frontend LabelPicker)."""
    return annotation.label_list[0]


@router.post("/tasks/{task_id}/annotations", response_model=schemas.AnnotationOut)
def submit_annotation(
    task_id: str, payload: schemas.AnnotationCreate, db: Session = Depends(get_db)
):
    task = db.get(models.AnnotationTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")

    annotation = models.Annotation(
        task_id=task_id,
        annotator_id=payload.annotator_id,
        labels=",".join(payload.labels),
        note=payload.note,
    )
    db.add(annotation)
    db.flush()  # populate annotation.id / task.annotations without a full commit yet

    all_annotations = (
        db.query(models.Annotation).filter(models.Annotation.task_id == task_id).all()
    )

    if len(all_annotations) >= settings.min_annotators_per_task:
        primary_labels = [_primary_label(a) for a in all_annotations]
        agreement = item_pairwise_agreement(primary_labels)

        if agreement >= settings.agreement_threshold:
            golden = models.GoldenExample(
                document_id=task.document_id,
                task_id=task_id,
                labels=",".join(sorted(set(primary_labels))),
                agreement_score=agreement,
                finalized_by="agreement",
            )
            task.status = "golden"
            db.add(golden)
        else:
            task.status = "adjudication"

    db.commit()
    db.refresh(annotation)
    return annotation


@router.get("/tasks/{task_id}/annotations", response_model=list[schemas.AnnotationOut])
def list_task_annotations(task_id: str, db: Session = Depends(get_db)):
    return (
        db.query(models.Annotation).filter(models.Annotation.task_id == task_id).all()
    )


@router.get("/tasks", response_model=list[schemas.TaskWithDocument])
def list_tasks(status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.AnnotationTask)
    if status:
        q = q.filter(models.AnnotationTask.status == status)
    return q.order_by(models.AnnotationTask.created_at.desc()).all()
