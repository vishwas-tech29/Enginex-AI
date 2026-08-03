from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register")
async def register():
    return {"status": "registered"}

@router.post("/login")
async def login():
    return {"status": "logged-in"}
