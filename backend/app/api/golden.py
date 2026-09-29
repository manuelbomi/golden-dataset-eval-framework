from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db

router = APIRouter(prefix="/golden", tags=["golden"])


@router.get("", response_model=list[schemas.GoldenExampleOut])
def list_golden_examples(db: Session = Depends(get_db)):
    return (
        db.query(models.GoldenExample)
        .order_by(models.GoldenExample.created_at.desc())
        .all()
    )
