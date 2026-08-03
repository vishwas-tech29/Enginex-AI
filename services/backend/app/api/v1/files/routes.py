from fastapi import APIRouter

router = APIRouter(prefix="/files", tags=["Files"])

@router.get("")
async def list_files():
    return []
