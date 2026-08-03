from fastapi import APIRouter

router = APIRouter(prefix="/cad", tags=["CAD"])

@router.post("/sketch")
async def create_sketch():
    return {"status": "sketch-created"}
