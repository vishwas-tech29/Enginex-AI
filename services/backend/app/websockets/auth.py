import uuid

from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.models.user import User
from app.utils.security import decode_token


async def authenticate_websocket(websocket: WebSocket, db: Session) -> User | None:
    """Shared WS auth: browsers can't set custom headers, so the access
    token travels as a query param (`?token=...`) instead."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return None
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("wrong token type")
        user_id = uuid.UUID(payload["sub"])
    except Exception:
        await websocket.close(code=4401)
        return None

    user = db.get(User, user_id)
    if not user:
        await websocket.close(code=4401)
        return None
    return user
