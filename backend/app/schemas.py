from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.taxonomy import is_valid_label


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    text: str
    source: str
    created_at: datetime.datetime


class DocumentCreate(BaseModel):
    text: str
    source: str = "synthetic"


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    document_id: str
    status: str
    created_at: datetime.datetime


class TaskWithDocument(TaskOut):
    document: DocumentOut


class AnnotationCreate(BaseModel):
    annotator_id: str
    labels: list[str]
    note: str | None = None

    @field_validator("labels")
    @classmethod
    def labels_must_be_known(cls, labels: list[str]) -> list[str]:
        if not labels:
            raise ValueError("at least one label is required")
        bad = [label for label in labels if not is_valid_label(label)]
        if bad:
            raise ValueError(f"unknown label(s): {bad}")
        return labels


class AnnotationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    task_id: str
    annotator_id: str
    labels: list[str]
    note: str | None
    created_at: datetime.datetime

    @field_validator("labels", mode="before")
    @classmethod
    def split_labels(cls, v: object) -> list[str]:
        if isinstance(v, str):
            return [label for label in v.split(",") if label]
        return v  # already a list (e.g. constructed directly in tests)


class GoldenExampleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    document_id: str
    labels: list[str]
    agreement_score: float
    finalized_by: str
    version: str

    @field_validator("labels", mode="before")
    @classmethod
    def split_labels(cls, v: object) -> list[str]:
        if isinstance(v, str):
            return [label for label in v.split(",") if label]
        return v
