"""SQLAlchemy models for the annotation pipeline:

  documents ---1:N--- annotation_tasks ---1:N--- annotations
                              |
                              +--(once agreement threshold met)--> golden_examples
                              +--(else)--------------------------> adjudications
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class Document(Base):
    """A raw conversation snippet awaiting annotation.

    `text` holds a short, self-contained excerpt (not a full transcript) --
    annotation quality drops fast on long spans because annotators start
    skimming, so this pipeline is built around short, focused snippets.
    """

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String, default="synthetic")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=_now)

    tasks: Mapped[list["AnnotationTask"]] = relationship(back_populates="document")


class AnnotationTask(Base):
    """One document queued for annotation. Kept separate from Document so
    the same document could in principle be re-queued for a second annotation
    round (e.g. after the taxonomy changes) without losing the first round's
    history."""

    __tablename__ = "annotation_tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"))
    status: Mapped[str] = mapped_column(
        String, default="pending"
    )  # pending | in_review | golden | adjudication
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=_now)

    document: Mapped["Document"] = relationship(back_populates="tasks")
    annotations: Mapped[list["Annotation"]] = relationship(back_populates="task")


class Annotation(Base):
    """One annotator's label pick(s) for one task. `labels` is stored as a
    comma-joined string (SQLite has no native array type and this repo
    targets both SQLite-for-dev and Postgres-for-prod); Postgres deployments
    could switch this column to ARRAY(String) -- see docs/adr/."""

    __tablename__ = "annotations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    task_id: Mapped[str] = mapped_column(ForeignKey("annotation_tasks.id"))
    annotator_id: Mapped[str] = mapped_column(String, nullable=False)
    labels: Mapped[str] = mapped_column(String, nullable=False)  # comma-joined
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=_now)

    task: Mapped["AnnotationTask"] = relationship(back_populates="annotations")

    @property
    def label_list(self) -> list[str]:
        return [label for label in self.labels.split(",") if label]


class GoldenExample(Base):
    """A finalized, agreed-upon label for a document -- the actual training
    and evaluation asset this whole pipeline exists to produce."""

    __tablename__ = "golden_examples"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"))
    task_id: Mapped[str] = mapped_column(ForeignKey("annotation_tasks.id"))
    labels: Mapped[str] = mapped_column(String, nullable=False)
    agreement_score: Mapped[float] = mapped_column(Float, nullable=False)
    finalized_by: Mapped[str] = mapped_column(String, default="agreement")  # agreement | adjudication
    version: Mapped[str] = mapped_column(String, default="v1")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=_now)

    @property
    def label_list(self) -> list[str]:
        return [label for label in self.labels.split(",") if label]
