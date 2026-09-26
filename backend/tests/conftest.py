from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401 — registers every table
from app.core.db import get_session
from app.core.limiter import limiter
from app.main import app


@pytest.fixture
def session() -> Generator[Session, None, None]:
	engine = create_engine(
		"sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
	)
	SQLModel.metadata.create_all(engine)
	with Session(engine) as session:
		yield session


@pytest.fixture
def client(session: Session) -> Generator[TestClient, None, None]:
	app.dependency_overrides[get_session] = lambda: session
	limiter.enabled = False
	with TestClient(app) as client:
		yield client
	app.dependency_overrides.clear()
	limiter.enabled = True


def auth(client: TestClient, email: str, password: str = "password123") -> dict[str, str]:
	res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
	assert res.status_code == 200, res.text
	return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
def admin(client: TestClient) -> dict[str, str]:
	res = client.post(
		"/api/v1/auth/register",
		json={"email": "admin@situng.go.id", "full_name": "Admin", "password": "password123"},
	)
	assert res.status_code == 201, res.text
	return auth(client, "admin@situng.go.id")


@pytest.fixture
def unit_id(client: TestClient, admin: dict[str, str]) -> int:
	res = client.post("/api/v1/units", json={"name": "Biro Umum"}, headers=admin)
	assert res.status_code == 201, res.text
	return res.json()["id"]


@pytest.fixture
def make_user(client: TestClient, admin: dict[str, str], unit_id: int) -> Callable[[str], tuple[int, dict[str, str]]]:
	def _make(name: str) -> tuple[int, dict[str, str]]:
		email = f"{name.lower()}@situng.go.id"
		res = client.post(
			"/api/v1/users",
			json={"email": email, "full_name": name, "password": "password123", "unit_id": unit_id},
			headers=admin,
		)
		assert res.status_code == 201, res.text
		return res.json()["id"], auth(client, email)

	return _make
