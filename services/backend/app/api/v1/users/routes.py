from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me")
async def get_current_user():
    return {"name": "Enginex User"}
