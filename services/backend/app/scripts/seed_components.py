"""Seed a starter component library (symbols, footprints, components).

Run with: python -m app.scripts.seed_components

Idempotent — skips components whose part_number already exists.
"""
from datetime import datetime, timezone

from app.database import SessionLocal
from app.models.component import Component, Footprint, Symbol

FOOTPRINTS = [
    {"name": "0805", "package_type": "0805", "pads": [{"pad": 1, "x": -1, "y": 0}, {"pad": 2, "x": 1, "y": 0}]},
    {"name": "DIP-8", "package_type": "DIP-8", "pads": [{"pad": i, "x": 0, "y": i} for i in range(1, 9)]},
    {"name": "SOT-23", "package_type": "SOT-23", "pads": [{"pad": i, "x": i, "y": 0} for i in range(1, 4)]},
]

SYMBOLS = [
    {"name": "Resistor", "library": "Enginex Standard", "pins": [{"name": "1", "x": -10, "y": 0}, {"name": "2", "x": 10, "y": 0}]},
    {"name": "Capacitor", "library": "Enginex Standard", "pins": [{"name": "1", "x": -10, "y": 0}, {"name": "2", "x": 10, "y": 0}]},
    {"name": "IC-8Pin", "library": "Enginex Standard", "pins": [{"name": str(i), "x": 0, "y": i} for i in range(1, 9)]},
]

COMPONENTS = [
    {"name": "10k Resistor", "category": "resistor", "manufacturer": "Yageo", "part_number": "RC0805FR-0710KL", "symbol": "Resistor", "footprint": "0805"},
    {"name": "100nF Capacitor", "category": "capacitor", "manufacturer": "Murata", "part_number": "GRM188R71H104KA93D", "symbol": "Capacitor", "footprint": "0805"},
    {"name": "NE555 Timer", "category": "ic", "manufacturer": "Texas Instruments", "part_number": "NE555P", "symbol": "IC-8Pin", "footprint": "DIP-8"},
    {"name": "1N4148 Diode", "category": "diode", "manufacturer": "ON Semiconductor", "part_number": "1N4148", "symbol": "Resistor", "footprint": "SOT-23"},
]


def seed() -> None:
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        footprints_by_name = {}
        for fp in FOOTPRINTS:
            existing = db.query(Footprint).filter(Footprint.name == fp["name"]).first()
            if not existing:
                existing = Footprint(
                    name=fp["name"],
                    package_type=fp["package_type"],
                    pads=fp["pads"],
                    courtyard=[],
                    silkscreen=[],
                    created_at=now,
                )
                db.add(existing)
                db.flush()
            footprints_by_name[fp["name"]] = existing

        symbols_by_name = {}
        for sym in SYMBOLS:
            existing = db.query(Symbol).filter(Symbol.name == sym["name"]).first()
            if not existing:
                existing = Symbol(
                    name=sym["name"],
                    library=sym["library"],
                    svg_data="",
                    pins=sym["pins"],
                    meta={},
                    created_at=now,
                )
                db.add(existing)
                db.flush()
            symbols_by_name[sym["name"]] = existing

        created = 0
        for comp in COMPONENTS:
            if db.query(Component).filter(Component.part_number == comp["part_number"]).first():
                continue
            db.add(
                Component(
                    name=comp["name"],
                    category=comp["category"],
                    manufacturer=comp["manufacturer"],
                    part_number=comp["part_number"],
                    symbol_id=symbols_by_name[comp["symbol"]].id,
                    footprint_id=footprints_by_name[comp["footprint"]].id,
                    meta={},
                    created_at=now,
                )
            )
            created += 1

        db.commit()
        print(f"Seeded {len(FOOTPRINTS)} footprints, {len(SYMBOLS)} symbols, {created} new components.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
