import logging
import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.ai.orchestrator import AIOrchestrator, DailyCostLimitExceededError
from app.ai.setup import get_orchestrator
from app.api.v1.ai.service import AIService
from app.core.exceptions import EngineXException
from app.database import get_db
from app.websockets.auth import authenticate_websocket

logger = logging.getLogger("enginex.ai.streaming")

router = APIRouter()


@router.websocket("/ws/ai/chats/{chat_id}")
async def ai_chat_streaming_endpoint(
    websocket: WebSocket,
    chat_id: uuid.UUID,
    db: Session = Depends(get_db),
    orchestrator: AIOrchestrator = Depends(get_orchestrator),
):
    """Streams agent reasoning/tool-call/response events for a chat.

    Message shapes:
      Client -> Server: {"id": "...", "message": "..."}
      Server -> Client:
        {"type": "ack", "message_id": "..."}
        {"type": "thinking" | "intent_classified" | "agent_started" |
                  "tool_called" | "tool_result" | "agent_completed", ...}
        {"type": "response", "content": ..., "tokens_used": ..., "cost": ...}
        {"type": "done"}
        {"type": "error", "message": ...}
    """
    user = await authenticate_websocket(websocket, db)
    if user is None:
        return

    service = AIService(db)
    try:
        service.get_chat(chat_id, user)
    except EngineXException as exc:
        await websocket.close(code=4403 if exc.status_code == 403 else 4404)
        return

    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message")
            if not message:
                continue

            await websocket.send_json({"type": "ack", "message_id": data.get("id")})

            async def stream_callback(event: dict) -> None:
                await websocket.send_json(event)

            try:
                messages = await service.post_message(
                    chat_id, message, user, orchestrator, on_event=stream_callback
                )
                assistant_message = messages[-1]
                await websocket.send_json(
                    {
                        "type": "response",
                        "content": assistant_message.content,
                        "tokens_used": assistant_message.tokens_used,
                        "cost": float(assistant_message.cost_usd),
                    }
                )
            except DailyCostLimitExceededError as exc:
                await websocket.send_json({"type": "error", "message": str(exc)})
            except Exception as exc:  # noqa: BLE001 — keep the socket alive for the next message
                logger.exception("ai_streaming_error")
                await websocket.send_json({"type": "error", "message": str(exc)})

            await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        logger.info("ai_chat_disconnected", extra={"chat_id": str(chat_id)})
