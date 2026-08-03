"""Export the live FastAPI OpenAPI schema to docs/architecture/api-spec.yaml.

Run with: python -m app.scripts.export_openapi

This keeps the spec accurate by construction — it's the same schema FastAPI
serves at /openapi.json, not a hand-maintained document that can drift from
the implementation.
"""
from pathlib import Path

import yaml

from app.main import app

OUTPUT_PATH = Path(__file__).resolve().parents[4] / "docs" / "architecture" / "api-spec.yaml"


def export() -> None:
    schema = app.openapi()
    schema["servers"] = [
        {"url": "http://localhost:8000", "description": "Local development"},
        {"url": "https://api.enginex.ai", "description": "Production (placeholder)"},
    ]
    schema["info"]["description"] = (
        "Auto-generated from the FastAPI app (see "
        "app/scripts/export_openapi.py) — this is the same schema served "
        "live at /openapi.json. WebSocket endpoints (/ws/files/{file_id}) "
        "aren't representable in OpenAPI 3.0 and are documented separately "
        "in docs/architecture/complete-architecture.md and "
        "services/backend/app/websockets/manager.py."
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        yaml.dump(schema, f, sort_keys=False, allow_unicode=True, width=100)

    print(f"Wrote {OUTPUT_PATH} ({len(schema.get('paths', {}))} paths)")


if __name__ == "__main__":
    export()
