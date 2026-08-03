class ProjectService:
    async def create_project(self, payload: dict) -> dict:
        return {"status": "created", **payload}
