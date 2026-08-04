import io
import math

from tests.helpers import create_organization, create_project, register_user


def _setup_file(client, email):
    _, headers = register_user(client, email=email)
    org = create_organization(client, headers)
    project = create_project(client, headers, org["id"], type_="cad")
    upload = client.post(
        "/api/v1/files/upload",
        data={"project_id": project["id"]},
        files={"file": ("part.cad", io.BytesIO(b"seed"), "application/octet-stream")},
        headers=headers,
    )
    assert upload.status_code == 201, upload.text
    return headers, upload.json()


def _make_rectangle_sketch(client, headers, file_id, x0=0, y0=0, x1=10, y1=5):
    sketch = client.post(
        "/api/v1/cad/sketches", json={"file_id": file_id, "name": "rect"}, headers=headers
    ).json()
    sid = sketch["id"]

    def pt(x, y):
        return client.post(f"/api/v1/cad/sketches/{sid}/points", json={"x": x, "y": y}, headers=headers).json()["id"]

    p0, p1, p2, p3 = pt(x0, y0), pt(x1, y0), pt(x1, y1), pt(x0, y1)
    for a, b in [(p0, p1), (p1, p2), (p2, p3), (p3, p0)]:
        r = client.post(
            f"/api/v1/cad/sketches/{sid}/lines", json={"start_id": a, "end_id": b}, headers=headers
        )
        assert r.status_code == 200, r.text
    return sid


def test_sketch_geometry_and_solve(client):
    headers, file_obj = _setup_file(client, "sketch1@enginex.ai")
    sid = _make_rectangle_sketch(client, headers, file_obj["id"])

    solve_response = client.post(f"/api/v1/cad/sketches/{sid}/solve", headers=headers)
    assert solve_response.status_code == 200
    result = solve_response.json()
    # No dimensional/geometric constraints added yet, so it's mechanically
    # exact (each point is independently placed) but not "constrained" in
    # the parametric sense until horizontal/vertical/length constraints
    # are added — status just needs to be a valid, non-error outcome.
    assert result["status"] in ("solved", "under_constrained")


def test_sketch_with_constraints_solves_fully_constrained(client):
    headers, file_obj = _setup_file(client, "sketch2@enginex.ai")
    sketch = client.post(
        "/api/v1/cad/sketches", json={"file_id": file_obj["id"], "name": "rect"}, headers=headers
    ).json()
    sid = sketch["id"]

    def pt(x, y, fixed=False):
        return client.post(
            f"/api/v1/cad/sketches/{sid}/points", json={"x": x, "y": y, "fixed": fixed}, headers=headers
        ).json()["id"]

    # p0 is pinned — otherwise horizontal/vertical/length constraints fully
    # determine the rectangle's shape but leave it free to translate as a
    # rigid body (2 legitimate remaining DOF), which is correctly
    # under-constrained, not a solver bug.
    p0 = pt(0, 0, fixed=True)
    p1 = pt(9, 0.5)
    p2 = pt(9.5, 4.5)
    p3 = pt(0.3, 5.2)

    lines = {}
    for name, (a, b) in [("l0", (p0, p1)), ("l1", (p1, p2)), ("l2", (p2, p3)), ("l3", (p3, p0))]:
        r = client.post(f"/api/v1/cad/sketches/{sid}/lines", json={"start_id": a, "end_id": b}, headers=headers)
        lines[name] = r.json()["id"]

    for ctype, entities, value in [
        ("horizontal", [lines["l0"]], None),
        ("vertical", [lines["l1"]], None),
        ("horizontal", [lines["l2"]], None),
        ("vertical", [lines["l3"]], None),
        ("length", [lines["l0"]], 10),
        ("length", [lines["l1"]], 5),
    ]:
        r = client.post(
            f"/api/v1/cad/sketches/{sid}/constraints",
            json={"type": ctype, "entities": entities, "value": value},
            headers=headers,
        )
        assert r.status_code == 200, r.text

    solve_response = client.post(f"/api/v1/cad/sketches/{sid}/solve", headers=headers)
    result = solve_response.json()
    assert result["status"] == "solved"
    assert result["is_fully_constrained"] is True


def test_extrude_creates_real_solid_with_correct_volume(client):
    headers, file_obj = _setup_file(client, "extrude1@enginex.ai")
    sid = _make_rectangle_sketch(client, headers, file_obj["id"], 0, 0, 10, 5)

    body = client.post(
        "/api/v1/cad/bodies", json={"file_id": file_obj["id"], "name": "part"}, headers=headers
    ).json()

    extrude_response = client.post(
        f"/api/v1/cad/bodies/{body['id']}/extrude",
        json={"sketch_id": sid, "distance": 4},
        headers=headers,
    )
    assert extrude_response.status_code == 200, extrude_response.text
    assert extrude_response.json()["version_number"] == 2

    mesh_response = client.get(f"/api/v1/cad/bodies/{body['id']}/mesh", headers=headers)
    assert mesh_response.status_code == 200
    mesh = mesh_response.json()
    assert math.isclose(mesh["volume"], 200.0, rel_tol=1e-6)
    assert len(mesh["vertices"]) > 0
    assert len(mesh["triangles"]) > 0


def test_fillet_reduces_volume(client):
    headers, file_obj = _setup_file(client, "fillet1@enginex.ai")
    sid = _make_rectangle_sketch(client, headers, file_obj["id"], 0, 0, 10, 5)
    body = client.post(
        "/api/v1/cad/bodies", json={"file_id": file_obj["id"], "name": "part"}, headers=headers
    ).json()
    client.post(f"/api/v1/cad/bodies/{body['id']}/extrude", json={"sketch_id": sid, "distance": 4}, headers=headers)

    fillet_response = client.post(
        f"/api/v1/cad/bodies/{body['id']}/fillet", json={"radius": 0.5}, headers=headers
    )
    assert fillet_response.status_code == 200, fillet_response.text

    mesh = client.get(f"/api/v1/cad/bodies/{body['id']}/mesh", headers=headers).json()
    assert mesh["volume"] < 200.0


def test_invalid_fillet_returns_conflict_not_500(client):
    headers, file_obj = _setup_file(client, "fillet2@enginex.ai")
    sid = _make_rectangle_sketch(client, headers, file_obj["id"], 0, 0, 10, 5)
    body = client.post(
        "/api/v1/cad/bodies", json={"file_id": file_obj["id"], "name": "part"}, headers=headers
    ).json()
    client.post(f"/api/v1/cad/bodies/{body['id']}/extrude", json={"sketch_id": sid, "distance": 4}, headers=headers)

    response = client.post(f"/api/v1/cad/bodies/{body['id']}/fillet", json={"radius": 999}, headers=headers)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"

    # the bad feature must not have been persisted
    mesh = client.get(f"/api/v1/cad/bodies/{body['id']}/mesh", headers=headers).json()
    assert math.isclose(mesh["volume"], 200.0, rel_tol=1e-6)


def test_boolean_union_and_cut(client):
    headers, file_obj = _setup_file(client, "boolean1@enginex.ai")
    s1 = _make_rectangle_sketch(client, headers, file_obj["id"], 0, 0, 10, 10)
    s2 = _make_rectangle_sketch(client, headers, file_obj["id"], 5, 5, 15, 15)

    body1 = client.post(
        "/api/v1/cad/bodies", json={"file_id": file_obj["id"], "name": "b1"}, headers=headers
    ).json()
    client.post(f"/api/v1/cad/bodies/{body1['id']}/extrude", json={"sketch_id": s1, "distance": 2}, headers=headers)

    body2 = client.post(
        "/api/v1/cad/bodies", json={"file_id": file_obj["id"], "name": "b2"}, headers=headers
    ).json()
    client.post(f"/api/v1/cad/bodies/{body2['id']}/extrude", json={"sketch_id": s2, "distance": 2}, headers=headers)

    union_body = client.post(
        "/api/v1/cad/bodies", json={"file_id": file_obj["id"], "name": "u"}, headers=headers
    ).json()
    client.post(f"/api/v1/cad/bodies/{union_body['id']}/extrude", json={"sketch_id": s1, "distance": 2}, headers=headers)
    union_response = client.post(
        f"/api/v1/cad/bodies/{union_body['id']}/boolean/union",
        json={"other_body_id": body2["id"]},
        headers=headers,
    )
    assert union_response.status_code == 200, union_response.text
    union_mesh = client.get(f"/api/v1/cad/bodies/{union_body['id']}/mesh", headers=headers).json()
    assert math.isclose(union_mesh["volume"], 350.0, rel_tol=1e-6)

    cut_body = client.post(
        "/api/v1/cad/bodies", json={"file_id": file_obj["id"], "name": "c"}, headers=headers
    ).json()
    client.post(f"/api/v1/cad/bodies/{cut_body['id']}/extrude", json={"sketch_id": s1, "distance": 2}, headers=headers)
    cut_response = client.post(
        f"/api/v1/cad/bodies/{cut_body['id']}/boolean/cut",
        json={"other_body_id": body2["id"]},
        headers=headers,
    )
    assert cut_response.status_code == 200
    cut_mesh = client.get(f"/api/v1/cad/bodies/{cut_body['id']}/mesh", headers=headers).json()
    assert math.isclose(cut_mesh["volume"], 150.0, rel_tol=1e-6)


def test_export_step_stl_obj(client):
    headers, file_obj = _setup_file(client, "export1@enginex.ai")
    sid = _make_rectangle_sketch(client, headers, file_obj["id"], 0, 0, 10, 5)
    body = client.post(
        "/api/v1/cad/bodies", json={"file_id": file_obj["id"], "name": "part"}, headers=headers
    ).json()
    client.post(f"/api/v1/cad/bodies/{body['id']}/extrude", json={"sketch_id": sid, "distance": 4}, headers=headers)

    step_response = client.get(f"/api/v1/cad/export/step/{body['id']}", headers=headers)
    assert step_response.status_code == 200
    assert b"ISO-10303-21" in step_response.content
    assert "attachment" in step_response.headers["content-disposition"]

    stl_response = client.get(f"/api/v1/cad/export/stl/{body['id']}", headers=headers)
    assert stl_response.status_code == 200
    assert len(stl_response.content) > 0

    obj_response = client.get(f"/api/v1/cad/export/obj/{body['id']}", headers=headers)
    assert obj_response.status_code == 200
    assert obj_response.content.startswith(b"#")
    assert b"v " in obj_response.content
    assert b"f " in obj_response.content


def test_assembly_parts_constraints_and_collisions(client):
    headers, file_obj = _setup_file(client, "assembly1@enginex.ai")
    sid = _make_rectangle_sketch(client, headers, file_obj["id"], 0, 0, 4, 4)
    body = client.post(
        "/api/v1/cad/bodies", json={"file_id": file_obj["id"], "name": "part"}, headers=headers
    ).json()
    client.post(f"/api/v1/cad/bodies/{body['id']}/extrude", json={"sketch_id": sid, "distance": 2}, headers=headers)

    assembly = client.post(
        "/api/v1/cad/assemblies", json={"file_id": file_obj["id"], "name": "asm"}, headers=headers
    ).json()

    part1 = client.post(
        f"/api/v1/cad/assemblies/{assembly['id']}/parts",
        json={"body_id": body["id"], "name": "Part A", "position": [0, 0, 0]},
        headers=headers,
    ).json()
    part2 = client.post(
        f"/api/v1/cad/assemblies/{assembly['id']}/parts",
        json={"body_id": body["id"], "name": "Part B", "position": [1, 1, 0]},
        headers=headers,
    ).json()
    client.post(
        f"/api/v1/cad/assemblies/{assembly['id']}/parts",
        json={"body_id": body["id"], "name": "Part C (far away)", "position": [500, 500, 0]},
        headers=headers,
    )

    collisions_response = client.get(f"/api/v1/cad/assemblies/{assembly['id']}/collisions", headers=headers)
    assert collisions_response.status_code == 200
    pairs = collisions_response.json()["collisions"]
    assert any(set(pair) == {part1["instance_id"], part2["instance_id"]} for pair in pairs)

    constraint = client.post(
        f"/api/v1/cad/assemblies/{assembly['id']}/constraints",
        json={
            "type": "revolute",
            "part1_instance_id": part1["instance_id"],
            "part2_instance_id": part2["instance_id"],
            "axis_point": [0, 0, 0],
            "axis_dir": [0, 0, 1],
        },
        headers=headers,
    ).json()

    animate_response = client.post(
        f"/api/v1/cad/assemblies/{assembly['id']}/constraints/{constraint['id']}/animate",
        json={"parameter": math.pi / 2},
        headers=headers,
    )
    assert animate_response.status_code == 200
    new_position = animate_response.json()["position"]
    assert math.isclose(new_position[0], -1.0, abs_tol=1e-6)
    assert math.isclose(new_position[1], 1.0, abs_tol=1e-6)
