import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.core.rate_limit import limiter
from app.database import Base, get_db
from app.main import app
from app.services.storage import get_storage


@pytest.fixture(autouse=True)
def isolated_storage(monkeypatch, tmp_path_factory):
    storage_root = tmp_path_factory.mktemp("storage")
    monkeypatch.setattr(settings, "storage_root", str(storage_root))
    get_storage.cache_clear()
    yield storage_root
    get_storage.cache_clear()


@pytest.fixture(autouse=True)
def reset_rate_limits():
    # The limiter's in-memory storage is a module-level singleton shared by
    # every test in the process, and Starlette's TestClient always connects
    # from the same pseudo-IP ("testclient") — without this, one test's
    # requests count against every other test's rate limit budget.
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
