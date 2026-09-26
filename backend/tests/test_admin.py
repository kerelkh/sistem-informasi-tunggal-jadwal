from fastapi.testclient import TestClient

from tests.conftest import auth


def test_first_register_is_admin_then_closed(client: TestClient, admin):
	me = client.get("/api/v1/auth/me", headers=admin).json()
	assert me["role"] == "admin"
	res = client.post(
		"/api/v1/auth/register", json={"email": "x@situng.go.id", "password": "password123"}
	)
	assert res.status_code == 403


def test_regular_user_needs_unit(client: TestClient, admin):
	res = client.post(
		"/api/v1/users",
		json={"email": "u@situng.go.id", "full_name": "U", "password": "password123"},
		headers=admin,
	)
	assert res.status_code == 400


def test_admin_creates_user_in_unit(client: TestClient, admin, unit_id):
	res = client.post(
		"/api/v1/users",
		json={"email": "budi@situng.go.id", "full_name": "Budi", "password": "password123", "unit_id": unit_id},
		headers=admin,
	)
	assert res.status_code == 201
	assert res.json()["unit"] == {"id": unit_id, "name": "Biro Umum"}
	units = client.get("/api/v1/units", headers=admin).json()
	assert units[0]["member_count"] == 1


def test_user_cannot_administer(client: TestClient, make_user, unit_id):
	_, budi = make_user("Budi")
	assert client.post("/api/v1/units", json={"name": "X"}, headers=budi).status_code == 403
	assert client.get("/api/v1/users", headers=budi).status_code == 403
	# ...but can read units for filters
	assert client.get("/api/v1/units", headers=budi).status_code == 200


def test_unit_with_members_cannot_be_deleted(client: TestClient, admin, unit_id, make_user):
	make_user("Budi")
	assert client.delete(f"/api/v1/units/{unit_id}", headers=admin).status_code == 409


def test_admin_cannot_demote_self(client: TestClient, admin):
	me = client.get("/api/v1/auth/me", headers=admin).json()
	res = client.put(f"/api/v1/users/{me['id']}", json={"role": "user"}, headers=admin)
	assert res.status_code == 400


def test_deactivated_user_cannot_log_in(client: TestClient, admin, make_user):
	budi_id, _ = make_user("Budi")
	client.put(f"/api/v1/users/{budi_id}", json={"is_active": False}, headers=admin)
	res = client.post("/api/v1/auth/login", json={"email": "budi@situng.go.id", "password": "password123"})
	assert res.status_code == 403


def test_reset_password(client: TestClient, admin, make_user):
	budi_id, _ = make_user("Budi")
	res = client.post(
		f"/api/v1/users/{budi_id}/reset-password", json={"new_password": "newpassword1"}, headers=admin
	)
	assert res.status_code == 204
	auth(client, "budi@situng.go.id", "newpassword1")


def test_short_password_message(client: TestClient, admin, unit_id):
	res = client.post(
		"/api/v1/users",
		json={"email": "x@situng.go.id", "full_name": "X", "password": "short", "unit_id": unit_id},
		headers=admin,
	)
	assert res.json() == {"detail": "Kata sandi: minimal 8 karakter."}
