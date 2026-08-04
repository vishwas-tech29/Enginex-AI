import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from app.api.v1.files.service import FileService
from app.database import get_db
from app.websockets.auth import authenticate_websocket
from app.websockets.manager import manager

router = APIRouter()


@router.websocket("/ws/files/{file_id}")
async def file_collaboration_endpoint(
    websocket: WebSocket,
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    user = await authenticate_websocket(websocket, db)
    if user is None:
        return

    try:
        FileService(db).get(file_id, user)
    except HTTPException as exc:
        await websocket.close(code=4403 if exc.status_code == 403 else 4404)
        return

    await manager.connect(file_id, websocket, user, db)
    try:
        while True:
            message = await websocket.receive_json()
            await manager.handle_message(file_id, websocket, message)
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(file_id, websocket, db)
