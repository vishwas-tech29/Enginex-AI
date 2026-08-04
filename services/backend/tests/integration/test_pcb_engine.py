import io
from datetime import datetime, timezone

from app.models.component import Component, Footprint
from tests.helpers import create_organization, create_project, register_user


def _seed_footprint(db_session, pads, courtyard=None):
    footprint = Footprint(
        name="TEST-FP",
        package_type="TEST",
        pads=pads,
        courtyard=courtyard or [],
        silkscreen=[],
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(footprint)
    db_session.commit()
    db_session.refresh(footprint)
    return footprint


def _seed_library_component(db_session, category="ic", part_number="MCU-1"):
    component = Component(
        name="Test part",
        category=category,
        manufacturer="Acme",
        part_number=part_number,
        meta={},
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(component)
    db_session.commit()
    db_session.refresh(component)
    return component


def _two_pin_pads():
    return [
        {"id": "1", "name": "1", "x": 0.0, "y": 0.0, "shape": "circle", "width": 0.6, "height": 0.6, "layers": ["top_copper"]},
        {"id": "2", "name": "2", "x": 2.0, "y": 0.0, "shape": "circle", "width": 0.6, "height": 0.6, "layers": ["top_copper"]},
    ]


def _setup_board(client, headers, width_mm=50, height_mm=50):
    org = create_organization(client, headers)
    project = create_project(client, headers, org["id"], type_="pcb")
    upload = client.post(
        "/api/v1/files/upload",
        data={"project_id": project["id"]},
        files={"file": ("board.pcb", io.BytesIO(b"seed"), "application/octet-stream")},
        headers=headers,
    )
    assert upload.status_code == 201, upload.text
    file_id = upload.json()["id"]

    board = client.post(
        "/api/v1/pcb/boards",
        json={"file_id": file_id, "name": "Board", "width_mm": width_mm, "height_mm": height_mm},
        headers=headers,
    )
    assert board.status_code == 201, board.text
    return board.json()


def test_list_boards_by_file(client):
    _, headers = register_user(client, email="pcb_list@enginex.ai")
    board = _setup_board(client, headers)

    response = client.get("/api/v1/pcb/boards", params={"file_id": board["file_id"]}, headers=headers)
    assert response.status_code == 200
    assert any(b["id"] == board["id"] for b in response.json())


def test_manual_trace_and_via_roundtrip(client):
    _, headers = register_user(client, email="pcb_manual@enginex.ai")
    board = _setup_board(client, headers)

    trace = client.post(
        f"/api/v1/pcb/boards/{board['id']}/traces",
        json={
            "layer": "top_copper", "start": {"x": 0, "y": 0}, "end": {"x": 10, "y": 0},
            "net": "SIG", "width": 0.3,
        },
        headers=headers,
    )
    assert trace.status_code == 201, trace.text
    assert trace.json()["net"] == "SIG"

    via = client.post(
        f"/api/v1/pcb/boards/{board['id']}/vias",
        json={
            "position": {"x": 10, "y": 0}, "from_layer": "top_copper", "to_layer": "bottom_copper", "net": "SIG",
        },
        headers=headers,
    )
    assert via.status_code == 201, via.text

    refreshed = client.get(f"/api/v1/pcb/boards/{board['id']}", headers=headers).json()
    assert len(refreshed["data"]["traces"]) == 1
    assert len(refreshed["data"]["vias"]) == 1


def test_drc_flags_narrow_trace_and_clearance_violation(client):
    _, headers = register_user(client, email="pcb_drc@enginex.ai")
    board = _setup_board(client, headers)

    # Below the 0.254mm default minimum trace width.
    client.post(
        f"/api/v1/pcb/boards/{board['id']}/traces",
        json={"layer": "top_copper", "start": {"x": 0, "y": 0}, "end": {"x": 5, "y": 0}, "net": "A", "width": 0.1},
        headers=headers,
    )
    # A second, different-net trace running right alongside the first — clearance violation.
    client.post(
        f"/api/v1/pcb/boards/{board['id']}/traces",
        json={"layer": "top_copper", "start": {"x": 0, "y": 0.05}, "end": {"x": 5, "y": 0.05}, "net": "B", "width": 0.3},
        headers=headers,
    )

    drc = client.post(f"/api/v1/pcb/boards/{board['id']}/drc", headers=headers)
    assert drc.status_code == 200
    rules = {v["rule"] for v in drc.json()["violations"]}
    assert "min_trace_width" in rules
    assert "trace_clearance" in rules


def test_erc_floating_net_and_undriven_signal(client, db_session):
    _, headers = register_user(client, email="pcb_erc@enginex.ai")
    board = _setup_board(client, headers)
    footprint = _seed_footprint(db_session, _two_pin_pads())
    resistor = _seed_library_component(db_session, category="resistor", part_number="R-1")

    r1 = client.post(
        "/api/v1/pcb/components",
        json={
            "board_id": board["id"], "reference_designator": "R1",
            "footprint_id": str(footprint.id), "library_entry_id": str(resistor.id),
            "position_x": 0, "position_y": 0,
            "data": {"net_map": {"1": "SIG", "2": "SIG"}},
        },
        headers=headers,
    )
    assert r1.status_code == 201, r1.text

    r2 = client.post(
        "/api/v1/pcb/components",
        json={
            "board_id": board["id"], "reference_designator": "R2",
            "footprint_id": str(footprint.id), "library_entry_id": str(resistor.id),
            "position_x": 10, "position_y": 0,
            "data": {"net_map": {"1": "LONELY"}},
        },
        headers=headers,
    )
    assert r2.status_code == 201, r2.text

    erc = client.post(f"/api/v1/pcb/boards/{board['id']}/erc", headers=headers)
    assert erc.status_code == 200
    violations = erc.json()["violations"]

    floating = [v for v in violations if v["rule"] == "floating_net"]
    assert any(v["net"] == "LONELY" for v in floating)

    undriven = [v for v in violations if v["rule"] == "undriven_signal"]
    assert any(v["net"] == "SIG" for v in undriven)  # only resistors on this net, no driver


def test_erc_short_circuit_not_flagged_for_correctly_wired_net(client, db_session):
    _, headers = register_user(client, email="pcb_erc_short@enginex.ai")
    board = _setup_board(client, headers)
    footprint = _seed_footprint(db_session, _two_pin_pads())

    client.post(
        "/api/v1/pcb/components",
        json={
            "board_id": board["id"], "reference_designator": "U1", "footprint_id": str(footprint.id),
            "position_x": 0, "position_y": 0, "data": {"net_map": {"1": "SIG", "2": "SIG"}},
        },
        headers=headers,
    )
    client.post(
        f"/api/v1/pcb/boards/{board['id']}/traces",
        json={"layer": "top_copper", "start": {"x": 0, "y": 0}, "end": {"x": 2, "y": 0}, "net": "SIG", "width": 0.3},
        headers=headers,
    )

    erc = client.post(f"/api/v1/pcb/boards/{board['id']}/erc", headers=headers)
    shorts = [v for v in erc.json()["violations"] if v["rule"] == "short_circuit"]
    assert shorts == []


def test_auto_route_connects_two_pin_net(client, db_session):
    _, headers = register_user(client, email="pcb_autoroute@enginex.ai")
    board = _setup_board(client, headers)
    footprint = _seed_footprint(db_session, _two_pin_pads())

    client.post(
        "/api/v1/pcb/components",
        json={
            "board_id": board["id"], "reference_designator": "U1", "footprint_id": str(footprint.id),
            "position_x": 5, "position_y": 5, "data": {"net_map": {"1": "SIG"}},
        },
        headers=headers,
    )
    client.post(
        "/api/v1/pcb/components",
        json={
            "board_id": board["id"], "reference_designator": "U2", "footprint_id": str(footprint.id),
            "position_x": 30, "position_y": 30, "data": {"net_map": {"1": "SIG"}},
        },
        headers=headers,
    )

    response = client.post(
        f"/api/v1/pcb/boards/{board['id']}/auto-route", json={"layer": "top_copper"}, headers=headers
    )
    assert response.status_code == 200, response.text
    traces = response.json()["traces"]
    assert len(traces) > 0
    assert all(t["net"] == "SIG" for t in traces)


def test_optimize_traces_removes_redundant_collinear_segment(client):
    _, headers = register_user(client, email="pcb_optimize@enginex.ai")
    board = _setup_board(client, headers)

    for end_x in (5, 10):
        client.post(
            f"/api/v1/pcb/boards/{board['id']}/traces",
            json={"layer": "top_copper", "start": {"x": 0, "y": 0}, "end": {"x": end_x, "y": 0}, "net": "SIG", "width": 0.3},
            headers=headers,
        )

    response = client.post(
        f"/api/v1/pcb/boards/{board['id']}/optimize-traces", json={"net": "SIG"}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["removed"] == 1


def test_export_endpoints_return_downloadable_files(client, db_session):
    _, headers = register_user(client, email="pcb_export@enginex.ai")
    board = _setup_board(client, headers)
    footprint = _seed_footprint(db_session, _two_pin_pads())

    client.post(
        "/api/v1/pcb/components",
        json={
            "board_id": board["id"], "reference_designator": "R1", "footprint_id": str(footprint.id),
            "position_x": 0, "position_y": 0, "data": {"net_map": {"1": "SIG"}, "value": "10k"},
        },
        headers=headers,
    )

    for fmt, path in [
        ("gerber", "gerber"), ("drill", "drill"), ("netlist", "netlist"),
        ("bom", "bom"), ("step", "step"),
    ]:
        response = client.get(f"/api/v1/pcb/export/{path}/{board['id']}", headers=headers)
        assert response.status_code == 200, f"{fmt}: {response.text}"
        assert "Content-Disposition" in response.headers
        assert len(response.content) > 0


def test_board_mesh_is_a_real_extruded_solid(client):
    _, headers = register_user(client, email="pcb_mesh@enginex.ai")
    board = _setup_board(client, headers, width_mm=40, height_mm=20)

    response = client.get(f"/api/v1/pcb/boards/{board['id']}/mesh", headers=headers)
    assert response.status_code == 200, response.text
    mesh = response.json()
    assert len(mesh["vertices"]) > 0
    assert len(mesh["triangles"]) > 0
    assert mesh["volume"] > 0
