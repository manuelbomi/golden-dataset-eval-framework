from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=schemas.DocumentOut)
def create_document(payload: schemas.DocumentCreate, db: Session = Depends(get_db)):
    doc = models.Document(text=payload.text, source=payload.source)
    task = models.AnnotationTask(document=doc)
    db.add(doc)
    db.add(task)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("", response_model=list[schemas.DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    return db.query(models.Document).order_by(models.Document.created_at.desc()).all()
