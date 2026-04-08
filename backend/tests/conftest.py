from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import create_application


@pytest.fixture()
def db_session_factory(tmp_path: Path):
    db_file = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)
    try:
        yield TestingSessionLocal
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session_factory) -> Generator[TestClient, None, None]:
    app = create_application()

    def override_get_db() -> Generator[Session, None, None]:
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        register_response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "admin@soar.local",
                "password": "ChangeMe123!",
                "full_name": "Test Admin",
                "role": "admin",
            },
        )
        assert register_response.status_code == 201

        login_response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@soar.local",
                "password": "ChangeMe123!",
            },
        )
        assert login_response.status_code == 200

        access_token = login_response.json()["data"]["access_token"]
        test_client.headers.update({"Authorization": f"Bearer {access_token}"})

        yield test_client

    app.dependency_overrides.clear()
