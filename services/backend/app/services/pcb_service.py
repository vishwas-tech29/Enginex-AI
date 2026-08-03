class PCBService:
    async def create_board(self, project_id: str, payload: dict) -> dict:
        return {"project_id": project_id, "status": "board-created", **payload}
