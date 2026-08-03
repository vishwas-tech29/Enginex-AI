from datetime import datetime, timezone

from app.models.component import Component, Footprint, Symbol
from tests.helpers import register_user


def _seed_component(db_session, name="10k Resistor", part_number="RC0805-10K", category="resistor"):
    now = datetime.now(timezone.utc)
    symbol = Symbol(name="Resistor", library="Enginex Standard", svg_data="", pins=[], meta={}, created_at=now)
    footprint = Footprint(name="0805", package_type="0805", pads=[], courtyard=[], silkscreen=[], created_at=now)
    db_session.add_all([symbol, footprint])
    db_session.flush()

    component = Component(
        name=name,
        category=category,
        manufacturer="Yageo",
        part_number=part_number,
        datasheet_url="https://example.com/datasheet.pdf",
        symbol_id=symbol.id,
        footprint_id=footprint.id,
        meta={},
        created_at=now,
    )
    db_session.add(component)
    db_session.commit()
    db_session.refresh(component)
    return component


def test_component_search_matches_name_and_part_number(client, db_session):
    _, headers = register_user(client, email="engineer@enginex.ai")
    component = _seed_component(db_session)

    by_name = client.get("/api/v1/components/search", params={"q": "resistor"}, headers=headers)
    assert by_name.status_code == 200
    assert any(c["id"] == component.id.hex or c["id"] == str(component.id) for c in by_name.json())

    by_part_number = client.get(
        "/api/v1/components/search", params={"q": "RC0805-10K"}, headers=headers
    )
    assert len(by_part_number.json()) == 1

    no_match = client.get("/api/v1/components/search", params={"q": "no-such-part"}, headers=headers)
    assert no_match.json() == []


def test_component_datasheet_redirects(client, db_session):
    _, headers = register_user(client, email="datasheet@enginex.ai")
    component = _seed_component(db_session, part_number="RC0805-20K")

    response = client.get(
        f"/api/v1/components/{component.id}/datasheet", headers=headers, follow_redirects=False
    )
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "https://example.com/datasheet.pdf"


def test_create_symbol_and_footprint(client):
    _, headers = register_user(client, email="librarian@enginex.ai")

    symbol_response = client.post(
        "/api/v1/symbols",
        json={"name": "Custom IC", "library": "Custom", "pins": [{"name": "1", "x": 0, "y": 0}]},
        headers=headers,
    )
    assert symbol_response.status_code == 201
    assert symbol_response.json()["name"] == "Custom IC"

    footprint_response = client.post(
        "/api/v1/footprints",
        json={"name": "QFN-32", "package_type": "QFN-32", "pads": []},
        headers=headers,
    )
    assert footprint_response.status_code == 201

    list_response = client.get("/api/v1/symbols", headers=headers)
    assert any(s["name"] == "Custom IC" for s in list_response.json())
