import io

from tests.helpers import create_organization, create_project, register_user


def _upload_file(client, headers, project_id, filename="part.cad"):
    response = client.post(
        "/api/v1/files/upload",
        data={"project_id": project_id},
        files={"file": (filename, io.BytesIO(b"seed"), "application/octet-stream")},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_cad_sketch_crud(client):
    _, headers = register_user(client, email="cad@enginex.ai")
    org = create_organization(client, headers)
    project = create_project(client, headers, org["id"], type_="cad")
    file_obj = _upload_file(client, headers, project["id"])

    create_response = client.post(
        "/api/v1/cad/sketches",
        json={"file_id": file_obj["id"], "name": "Base Sketch", "data": {"lines": []}},
        headers=headers,
    )
    assert create_response.status_code == 201, create_response.text
    sketch = create_response.json()
    assert sketch["object_type"] == "sketch"
    assert sketch["version_number"] == 1

    get_response = client.get(f"/api/v1/cad/sketches/{sketch['id']}", headers=headers)
    assert get_response.status_code == 200

    update_response = client.put(
        f"/api/v1/cad/sketches/{sketch['id']}",
        json={"name": "Renamed Sketch"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["version_number"] == 2

    delete_response = client.delete(f"/api/v1/cad/sketches/{sketch['id']}", headers=headers)
    assert delete_response.status_code == 204


def test_pcb_board_and_component_crud(client):
    _, headers = register_user(client, email="pcb@enginex.ai")
    org = create_organization(client, headers)
    project = create_project(client, headers, org["id"], type_="pcb")
    file_obj = _upload_file(client, headers, project["id"], filename="board.pcb")

    board_response = client.post(
        "/api/v1/pcb/boards",
        json={"file_id": file_obj["id"], "name": "Main Board", "width_mm": 50, "height_mm": 30},
        headers=headers,
    )
    assert board_response.status_code == 201
    board = board_response.json()

    component_response = client.post(
        "/api/v1/pcb/components",
        json={"board_id": board["id"], "reference_designator": "R1", "position_x": 1, "position_y": 2},
        headers=headers,
    )
    assert component_response.status_code == 201
    component = component_response.json()
    assert component["reference_designator"] == "R1"

    update_response = client.put(
        f"/api/v1/pcb/components/{component['id']}",
        json={"reference_designator": "R2"},
        headers=headers,
    )
    assert update_response.json()["reference_designator"] == "R2"

    drc_response = client.post(f"/api/v1/pcb/boards/{board['id']}/drc", headers=headers)
    assert drc_response.status_code == 501

    delete_response = client.delete(f"/api/v1/pcb/components/{component['id']}", headers=headers)
    assert delete_response.status_code == 204


def test_ai_chat_message_roundtrip_and_agents_list(client):
    _, headers = register_user(client, email="ai@enginex.ai")

    chat_response = client.post("/api/v1/ai/chats", json={"title": "Design help"}, headers=headers)
    assert chat_response.status_code == 201
    chat = chat_response.json()

    message_response = client.post(
        f"/api/v1/ai/chats/{chat['id']}/messages",
        json={"content": "How do I extrude this sketch?"},
        headers=headers,
    )
    assert message_response.status_code == 201
    messages = message_response.json()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"

    list_response = client.get(f"/api/v1/ai/chats/{chat['id']}/messages", headers=headers)
    assert len(list_response.json()) == 2

    providers_response = client.get("/api/v1/ai/providers", headers=headers)
    assert providers_response.status_code == 200
    assert any(p["name"] == "anthropic" for p in providers_response.json())

    configure_response = client.post(
        "/api/v1/ai/providers/configure",
        json={"provider": "anthropic", "api_key": "sk-test"},
        headers=headers,
    )
    assert configure_response.status_code == 501

    agents_response = client.get("/api/v1/ai/agents", headers=headers)
    assert agents_response.status_code == 200


def test_ai_chat_isolated_between_users(client):
    _, headers_a = register_user(client, email="chatuser_a@enginex.ai")
    _, headers_b = register_user(client, email="chatuser_b@enginex.ai")

    chat = client.post("/api/v1/ai/chats", json={"title": "Private"}, headers=headers_a).json()

    response = client.get(f"/api/v1/ai/chats/{chat['id']}", headers=headers_b)
    assert response.status_code == 403
