"""Point the app at a fresh in-memory SQLite DB for every test function, and
override FastAPI's `get_db` dependency to use that same DB -- otherwise
TestClient requests would go through app.db.SessionLocal, which is bound to
whatever DATABASE_URL was set at import time (the on-disk dev DB), and tests
would pollute (and be polluted by) real dev data.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    # StaticPool keeps a single underlying connection alive for the engine's
    # lifetime. Without it, SQLAlchemy's default pool opens a NEW connection
    # per checkout, and "sqlite:///:memory:" hands each new connection a
    # brand-new, empty database -- so a request's INSERT would land in a
    # different in-memory DB than the one create_all() just populated.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
