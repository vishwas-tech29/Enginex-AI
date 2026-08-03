from fastapi import APIRouter

router = APIRouter(prefix="/ai", tags=["AI"])

@router.get("/agents")
async def list_agents():
    return []
