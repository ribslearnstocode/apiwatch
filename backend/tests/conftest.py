import os
import tempfile
from pathlib import Path

import pytest

# A fresh SQLite file or a unique schema in a dedicated PostgreSQL test database.
_test_directory = tempfile.TemporaryDirectory(prefix="apiwatch-tests-")
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "sqlite:///" + (Path(_test_directory.name) / "test.db").as_posix())
os.environ["SCHEDULER_ENABLED"] = "false"

from fastapi.testclient import TestClient
from sqlalchemy import text
from app.main import app
from app.database import Base, SessionLocal, engine
from app.services.monitoring import running_checks
from app.services import monitors as monitor_services
from unittest.mock import AsyncMock


@pytest.fixture(scope="session", autouse=True)
def isolated_schema():
    if engine.dialect.name == "postgresql":
        import uuid
        from sqlalchemy import event
        schema = "test_" + uuid.uuid4().hex
        with engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine.dispose()

        @event.listens_for(engine, "connect")
        def set_schema(connection, _):
            with connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO "{schema}"')
            connection.commit()

        yield
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        engine.dispose()
    else:
        yield
        engine.dispose()


@pytest.fixture
def client(monkeypatch):
    # Keep registration deterministic; DNS/security behavior has dedicated tests.
    monkeypatch.setattr(monitor_services, "pinned_target", AsyncMock(return_value=("example.com", "93.184.216.34")))
    Base.metadata.drop_all(engine)
    running_checks.clear()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db(client):
    with SessionLocal() as session:
        yield session


@pytest.fixture
def monitor(client):
    return client.post("/api/monitors", json={"name": "Example API", "url": "https://httpbin.org/status/200", "check_interval": 60}).json()
