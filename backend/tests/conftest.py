"""Shared pytest fixtures. Every test runs against a dedicated throwaway
SQLite file (never the real dev database), wiped and rebuilt fresh before
each test — cheap enough at this table count that a clean schema per test
is simpler than manually deleting rows."""
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

# Must happen BEFORE any `app.*` import: app.config.get_settings() is
# cached on first call, so this is the only chance to point it at the test
# database instead of the real one.
TEST_DB_PATH = BACKEND_DIR / "test_fragility_passport.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

import pytest  # noqa: E402

import app.models  # noqa: E402,F401  (registers every model on Base.metadata)
from app.database.base import Base  # noqa: E402
from app.database.database import SessionLocal, engine, get_db  # noqa: E402


@pytest.fixture()
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    """A TestClient wired so every route uses the SAME session object as the
    test's own assertions (avoids SQLite visibility issues between two
    separate Session instances pointed at one file)."""
    from fastapi.testclient import TestClient

    from app.main import app

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
