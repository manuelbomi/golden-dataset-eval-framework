"""Alembic migration environment.

Production deployments (Postgres, via docker-compose or a managed DB) run
`alembic upgrade head` as a release step -- see docs/PRODUCTION.md. Local
dev and tests use `Base.metadata.create_all()` (in app.main's lifespan /
conftest.py) for zero-friction setup; that's fine for a throwaway SQLite
file but doesn't know how to evolve an existing schema, which is exactly
what Alembic is for once there's real data to preserve.

DATABASE_URL (same env var the app reads, see app.config) overrides
alembic.ini's sqlalchemy.url so one source of truth drives both.
"""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import Base
from app.models import (  # noqa: F401 -- import registers models on Base.metadata
    AnnotationTask,
    Annotation,
    Document,
    GoldenExample,
)

config = context.config

database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
