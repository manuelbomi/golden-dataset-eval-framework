"""Runtime configuration, read from environment variables.

DATABASE_URL defaults to a local SQLite file so `pytest` and a first-time
`uvicorn app.main:app` work with zero setup. Point it at Postgres for
anything beyond a laptop demo -- SQLite has no real concurrent-write story,
which is fine for a single annotator poking at the API but not for a team
of annotators hitting it at once. docker-compose.yml wires a real Postgres
container and sets this for you.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    agreement_threshold: float  # Cohen's kappa needed to finalize a golden example
    min_annotators_per_task: int


def get_settings() -> Settings:
    return Settings(
        database_url=os.environ.get(
            "DATABASE_URL", "sqlite:///./golden_dataset.db"
        ),
        agreement_threshold=float(os.environ.get("AGREEMENT_THRESHOLD", "0.6")),
        min_annotators_per_task=int(os.environ.get("MIN_ANNOTATORS_PER_TASK", "2")),
    )
