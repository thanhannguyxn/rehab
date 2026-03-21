from routers.auth import create_token


def test_login_success(client, seed_patient):
    response = client.post(
        "/api/auth/login",
        json={"username": seed_patient.username, "password": "patient123", "role": "patient"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user"]["username"] == seed_patient.username
    assert data["user"]["role"] == "patient"


def test_login_wrong_role_returns_403(client, seed_patient):
    response = client.post(
        "/api/auth/login",
        json={"username": seed_patient.username, "password": "patient123", "role": "doctor"},
    )
    assert response.status_code == 403
    assert "Tài khoản này là tài khoản" in response.json()["detail"]


def test_register_success(client):
    response = client.post(
        "/api/auth/register",
        json={
            "username": "new_patient",
            "password": "newpass123",
            "full_name": "New Patient",
            "role": "patient",
            "gender": "male",
            "age": 60,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["username"] == "new_patient"
    assert payload["user"]["role"] == "patient"
    assert payload["token"]


def test_verify_token_on_protected_route(client, seed_patient):
    token = create_token(seed_patient.id, seed_patient.username, "patient")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/sessions/my-history", headers=headers)
    assert response.status_code == 200
    assert "sessions" in response.json()

