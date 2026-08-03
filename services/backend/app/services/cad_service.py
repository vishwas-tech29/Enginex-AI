class CADService:
    async def create_sketch(self, project_id: str, payload: dict) -> dict:
        return {"project_id": project_id, "status": "sketch-created", **payload}
