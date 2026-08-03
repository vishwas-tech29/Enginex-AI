from fastapi import APIRouter

router = APIRouter(prefix="/pcb", tags=["PCB"])

@router.post("/board")
async def create_board():
    return {"status": "board-created"}
