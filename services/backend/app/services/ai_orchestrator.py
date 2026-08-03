class AIOrchestratorService:
    async def process_request(self, request: str) -> dict:
        return {"request": request, "status": "queued"}
