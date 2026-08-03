def test_register_login_and_me_flow(client):
    register_payload = {
        "email": "founder@enginex.ai",
        "password": "Sup3rSecret1",
        "name": "Founder",
    }
    register_response = client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code == 201
    tokens = register_response.json()
    assert tokens["user"]["email"] == register_payload["email"]

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": register_payload["email"], "password": register_payload["password"]},
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    me_response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == register_payload["email"]


def test_duplicate_registration_rejected(client):
    payload = {"email": "dup@enginex.ai", "password": "Sup3rSecret1", "name": "Dup"}
    client.post("/api/v1/auth/register", json=payload)
    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409


def test_login_with_wrong_password_rejected(client):
    payload = {"email": "wrongpass@enginex.ai", "password": "Sup3rSecret1", "name": "User"}
    client.post("/api/v1/auth/register", json=payload)
    response = client.post(
        "/api/v1/auth/login", json={"email": payload["email"], "password": "incorrect"}
    )
    assert response.status_code == 401
