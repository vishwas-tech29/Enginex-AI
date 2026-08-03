from fastapi import APIRouter

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("")
async def list_projects():
    return []
