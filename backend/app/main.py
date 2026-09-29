from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import annotations, documents, golden
from app.db import Base, engine
from app.taxonomy import SIGNAL_DESCRIPTIONS, SIGNAL_LABELS


@asynccontextmanager
async def lifespan(app: FastAPI):
    # create_all is fine for the SQLite dev default and for tests; a real
    # Postgres deployment should use the Alembic migrations in alembic/
    # instead (create_all doesn't know how to evolve an existing schema).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Golden Dataset & Evaluation Framework", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tutorial default -- lock this down in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(annotations.router)
app.include_router(golden.router)


@app.get("/taxonomy")
def get_taxonomy():
    return {"labels": SIGNAL_LABELS, "descriptions": SIGNAL_DESCRIPTIONS}


@app.get("/health")
def health():
    return {"status": "ok"}
