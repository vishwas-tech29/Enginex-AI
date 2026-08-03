from tests.helpers import register_user


def test_not_found_error_has_structured_code(client):
    import uuid

    _, headers = register_user(client, email="err404@enginex.ai")
    response = client.get(f"/api/v1/projects/{uuid.uuid4()}", headers=headers)
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert "not found" in body["error"]["message"]


def test_forbidden_error_has_structured_code(client):
    from tests.helpers import create_organization, create_project

    _, owner_headers = register_user(client, email="err403owner@enginex.ai")
    org = create_organization(client, owner_headers)
    project = create_project(client, owner_headers, org["id"])

    _, other_headers = register_user(client, email="err403intruder@enginex.ai")
    response = client.get(f"/api/v1/projects/{project['id']}", headers=other_headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
