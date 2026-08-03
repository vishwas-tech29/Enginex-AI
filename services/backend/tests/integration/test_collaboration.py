import io
import json
import uuid

import y_py as Y

from tests.helpers import create_organization, create_project, register_user


def _upload_file(client, headers, project_id, filename="sketch.cad"):
    response = client.post(
        "/api/v1/files/upload",
        data={"project_id": project_id},
        files={"file": (filename, io.BytesIO(b"seed"), "application/octet-stream")},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _yjs_update_setting(key: str, value: str) -> bytes:
    """Build a standalone Yjs update that sets `key` in the doc's top-level map."""
    doc = Y.YDoc()
    ymap = doc.get_map("canvas")
    with doc.begin_transaction() as txn:
        ymap.set(txn, key, value)
    return Y.encode_state_as_update(doc)


def test_two_clients_sync_and_merge_without_conflict(client):
    owner, owner_headers = register_user(client, email="owner@collab.ai")
    org = create_organization(client, owner_headers)
    project = create_project(client, owner_headers, org["id"])
    file_obj = _upload_file(client, owner_headers, project["id"])

    editor, editor_headers = register_user(client, email="editor@collab.ai")
    client.post(
        f"/api/v1/projects/{project['id']}/share",
        json={"user_id": editor["id"], "role": "editor"},
        headers=owner_headers,
    )

    owner_token = owner_headers["Authorization"].split(" ")[1]
    editor_token = editor_headers["Authorization"].split(" ")[1]
    ws_path = f"/ws/files/{file_obj['id']}"

    with client.websocket_connect(f"{ws_path}?token={owner_token}") as ws1:
        init1 = ws1.receive_json()
        assert init1["type"] == "init"
        assert len(init1["presence"]) == 1

        # Connecting always triggers a self-presence broadcast right after
        # `init` — drain it before opening the second connection.
        own_presence_echo = ws1.receive_json()
        assert own_presence_echo["type"] == "presence"
        assert len(own_presence_echo["presence"]) == 1

        with client.websocket_connect(f"{ws_path}?token={editor_token}") as ws2:
            init2 = ws2.receive_json()
            assert init2["type"] == "init"
            assert len(init2["presence"]) == 2

            # ws1 gets a presence broadcast now that ws2 has joined.
            presence_update = ws1.receive_json()
            assert presence_update["type"] == "presence"
            assert len(presence_update["presence"]) == 2

            # ws2 also receives that same broadcast (sent to all connections).
            presence_echo = ws2.receive_json()
            assert presence_echo["type"] == "presence"

            # Owner draws a rectangle; editor should receive the update.
            rect_update = _yjs_update_setting("rect_1", "rectangle")
            ws1.send_json({"type": "update", "update": rect_update.hex()})
            received = ws2.receive_json()
            assert received["type"] == "update"
            assert bytes.fromhex(received["update"]) == rect_update

            # Editor draws a circle concurrently; owner should receive it.
            circle_update = _yjs_update_setting("circle_1", "circle")
            ws2.send_json({"type": "update", "update": circle_update.hex()})
            received_back = ws1.receive_json()
            assert received_back["type"] == "update"

            # Cursor movement propagates as a presence update to the peer.
            ws1.send_json({"type": "cursor", "position": {"x": 42, "y": 7}})
            cursor_broadcast_to_2 = ws2.receive_json()
            assert cursor_broadcast_to_2["type"] == "presence"
            owner_presence = next(
                p for p in cursor_broadcast_to_2["presence"] if p["user_id"] == str(owner["id"])
            )
            assert owner_presence["cursor"] == {"x": 42, "y": 7}

            # ws1 also gets the echoed presence broadcast.
            ws1.receive_json()


def test_ydoc_state_persists_after_all_clients_disconnect(client, db_session):
    from app.models.collab import YDocSnapshot

    owner, owner_headers = register_user(client, email="persist@collab.ai")
    org = create_organization(client, owner_headers)
    project = create_project(client, owner_headers, org["id"])
    file_obj = _upload_file(client, owner_headers, project["id"], filename="board.pcb")

    owner_token = owner_headers["Authorization"].split(" ")[1]
    ws_path = f"/ws/files/{file_obj['id']}"

    update = _yjs_update_setting("trace_1", "copper")
    with client.websocket_connect(f"{ws_path}?token={owner_token}") as ws:
        ws.receive_json()  # init
        ws.send_json({"type": "update", "update": update.hex()})

    # Connection closed -> room should have persisted its merged state.
    snapshot = db_session.get(YDocSnapshot, uuid.UUID(file_obj["id"]))
    assert snapshot is not None

    restored = Y.YDoc()
    Y.apply_update(restored, snapshot.state)
    restored_map = restored.get_map("canvas")
    assert json.loads(restored_map.to_json())["trace_1"] == "copper"

    # Reconnecting should rehydrate from that persisted snapshot.
    with client.websocket_connect(f"{ws_path}?token={owner_token}") as ws2:
        init = ws2.receive_json()
        rehydrated = Y.YDoc()
        Y.apply_update(rehydrated, bytes.fromhex(init["state"]))
        assert json.loads(rehydrated.get_map("canvas").to_json())["trace_1"] == "copper"


def test_websocket_rejects_unauthenticated_connection(client):
    owner, owner_headers = register_user(client, email="noauth@collab.ai")
    org = create_organization(client, owner_headers)
    project = create_project(client, owner_headers, org["id"])
    file_obj = _upload_file(client, owner_headers, project["id"])

    try:
        with client.websocket_connect(f"/ws/files/{file_obj['id']}") as ws:
            ws.receive_json()
        assert False, "expected the connection to be closed"
    except Exception:
        pass


def test_websocket_rejects_user_without_project_access(client):
    owner, owner_headers = register_user(client, email="owner4@collab.ai")
    org = create_organization(client, owner_headers)
    project = create_project(client, owner_headers, org["id"])
    file_obj = _upload_file(client, owner_headers, project["id"])

    _, intruder_headers = register_user(client, email="outsider@collab.ai")
    intruder_token = intruder_headers["Authorization"].split(" ")[1]

    try:
        with client.websocket_connect(f"/ws/files/{file_obj['id']}?token={intruder_token}") as ws:
            ws.receive_json()
        assert False, "expected the connection to be closed"
    except Exception:
        pass
