import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.ai.schemas import (
    AgentOut,
    ChatOut,
    CreateChatRequest,
    CreateMessageRequest,
    MessageOut,
    ProviderOut,
)
from app.api.v1.ai.service import AIService
from app.api.v1.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["AI"])


class ConfigureProviderRequest(BaseModel):
    provider: str
    api_key: str


@router.post("/chats", response_model=ChatOut, status_code=201)
def create_chat(
    payload: CreateChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AIService(db).create_chat(payload, current_user)


@router.get("/chats/{chat_id}", response_model=ChatOut)
def get_chat(
    chat_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AIService(db).get_chat(chat_id, current_user)


@router.delete("/chats/{chat_id}", status_code=204)
def delete_chat(
    chat_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    AIService(db).delete_chat(chat_id, current_user)
    return None


@router.post("/chats/{chat_id}/messages", response_model=list[MessageOut], status_code=201)
def post_message(
    chat_id: uuid.UUID,
    payload: CreateMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AIService(db).post_message(chat_id, payload.content, current_user)


@router.get("/chats/{chat_id}/messages", response_model=list[MessageOut])
def list_messages(
    chat_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AIService(db).list_messages(chat_id, current_user)


@router.get("/agents", response_model=list[AgentOut])
def list_agents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AIService(db).list_agents()


@router.get("/providers", response_model=list[ProviderOut])
def list_providers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AIService(db).list_providers()


@router.post("/providers/configure")
def configure_provider(
    payload: ConfigureProviderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    AIService(db).configure_provider(payload.provider, payload.api_key)
