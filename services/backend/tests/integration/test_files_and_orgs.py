import io

from tests.helpers import create_organization, create_project, register_user


def test_organization_and_project_lifecycle(client):
    _, headers = register_user(client, email="owner@enginex.ai")
    org = create_organization(client, headers)
    project = create_project(client, headers, org["id"])

    response = client.get("/api/v1/projects", headers=headers)
    assert response.status_code == 200
    assert any(p["id"] == project["id"] for p in response.json())


def test_second_user_cannot_access_others_project(client):
    _, owner_headers = register_user(client, email="owner2@enginex.ai")
    org = create_organization(client, owner_headers)
    project = create_project(client, owner_headers, org["id"])

    _, other_headers = register_user(client, email="intruder@enginex.ai")
    response = client.get(f"/api/v1/projects/{project['id']}", headers=other_headers)
    assert response.status_code == 403


def test_share_project_grants_access(client):
    _, owner_headers = register_user(client, email="owner3@enginex.ai")
    org = create_organization(client, owner_headers)
    project = create_project(client, owner_headers, org["id"])

    other_user, other_headers = register_user(client, email="collaborator@enginex.ai")

    share_response = client.post(
        f"/api/v1/projects/{project['id']}/share",
        json={"user_id": other_user["id"], "role": "editor"},
        headers=owner_headers,
    )
    assert share_response.status_code == 200
    roles = {m["user_id"]: m["role"] for m in share_response.json()}
    assert roles[other_user["id"]] == "editor"

    access_response = client.get(f"/api/v1/projects/{project['id']}", headers=other_headers)
    assert access_response.status_code == 200

    # Viewer role added via editor grant should now allow this second user to
    # update the project too (editor >= editor requirement).
    update_response = client.patch(
        f"/api/v1/projects/{project['id']}",
        json={"name": "Renamed by collaborator"},
        headers=other_headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Renamed by collaborator"


def test_file_upload_download_version_and_revert(client):
    _, headers = register_user(client, email="filer@enginex.ai")
    org = create_organization(client, headers)
    project = create_project(client, headers, org["id"])

    upload_v1 = client.post(
        "/api/v1/files/upload",
        data={"project_id": project["id"]},
        files={"file": ("part.step", io.BytesIO(b"version-one-bytes"), "application/octet-stream")},
        headers=headers,
    )
    assert upload_v1.status_code == 201, upload_v1.text
    file_obj = upload_v1.json()
    assert file_obj["version_number"] == 1

    upload_v2 = client.post(
        "/api/v1/files/upload",
        data={"project_id": project["id"]},
        files={"file": ("part.step", io.BytesIO(b"version-two-bytes-longer"), "application/octet-stream")},
        headers=headers,
    )
    assert upload_v2.status_code == 201
    assert upload_v2.json()["id"] == file_obj["id"]
    assert upload_v2.json()["version_number"] == 2

    versions_response = client.get(f"/api/v1/files/{file_obj['id']}/versions", headers=headers)
    assert versions_response.status_code == 200
    versions = versions_response.json()
    assert len(versions) == 2
    assert versions[0]["version_number"] == 2

    download_latest = client.get(f"/api/v1/files/{file_obj['id']}/download", headers=headers)
    assert download_latest.status_code == 200
    assert download_latest.content == b"version-two-bytes-longer"

    v1_id = versions[1]["id"]
    download_v1 = client.get(
        f"/api/v1/files/{file_obj['id']}/download",
        params={"version_id": v1_id},
        headers=headers,
    )
    assert download_v1.status_code == 200
    assert download_v1.content == b"version-one-bytes"

    revert_response = client.post(
        f"/api/v1/files/{file_obj['id']}/revert-to/{v1_id}", headers=headers
    )
    assert revert_response.status_code == 200
    assert revert_response.json()["version_number"] == 3

    download_after_revert = client.get(
        f"/api/v1/files/{file_obj['id']}/download", headers=headers
    )
    assert download_after_revert.content == b"version-one-bytes"


def test_concurrent_uploads_get_unique_files(client):
    _, headers = register_user(client, email="concurrent@enginex.ai")
    org = create_organization(client, headers)
    project = create_project(client, headers, org["id"])

    uploaded_ids = set()
    for i in range(5):
        response = client.post(
            "/api/v1/files/upload",
            data={"project_id": project["id"]},
            files={"file": (f"file{i}.cad", io.BytesIO(f"data-{i}".encode()), "application/octet-stream")},
            headers=headers,
        )
        assert response.status_code == 201
        uploaded_ids.add(response.json()["id"])

    assert len(uploaded_ids) == 5

    list_response = client.get(f"/api/v1/projects/{project['id']}/files", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 5


def test_file_upload_too_large_is_rejected(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "max_upload_size_bytes", 10)

    _, headers = register_user(client, email="bigfile@enginex.ai")
    org = create_organization(client, headers)
    project = create_project(client, headers, org["id"])

    response = client.post(
        "/api/v1/files/upload",
        data={"project_id": project["id"]},
        files={"file": ("big.bin", io.BytesIO(b"x" * 1000), "application/octet-stream")},
        headers=headers,
    )
    assert response.status_code == 413
