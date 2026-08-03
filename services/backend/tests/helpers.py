def register_user(client, email="user@example.com", password="Sup3rSecret1", name="Test User"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "name": name},
    )
    assert response.status_code == 201, response.text
    tokens = response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    return tokens["user"], headers


def create_organization(client, headers, name="Acme Org"):
    response = client.post(
        "/api/v1/organizations", json={"name": name}, headers=headers
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_project(client, headers, organization_id, name="Test Project", type_="mixed"):
    response = client.post(
        "/api/v1/projects",
        json={"organization_id": organization_id, "name": name, "type": type_},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()
