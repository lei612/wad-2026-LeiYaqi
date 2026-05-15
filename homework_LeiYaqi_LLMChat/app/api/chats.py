from __future__ import annotations

from fastapi import APIRouter, Depends

from ..deps import get_current_user
from ..schemas import ChatCreateIn, ChatOut, ChatWithMessagesOut, LlmAnswerOut, SendMessageIn
from ..services import chats_usecases


router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.get("", response_model=list[ChatOut])
async def list_my_chats(user=Depends(get_current_user)) -> list[ChatOut]:
    return await chats_usecases.list_my_chats(str(user["_id"]))


@router.post("", response_model=ChatOut)
async def create_chat(payload: ChatCreateIn, user=Depends(get_current_user)) -> ChatOut:
    return await chats_usecases.create_chat(payload, str(user["_id"]))


@router.get("/{chat_id}", response_model=ChatWithMessagesOut)
async def get_chat(chat_id: str, user=Depends(get_current_user)) -> ChatWithMessagesOut:
    return await chats_usecases.get_chat(chat_id, str(user["_id"]))


@router.post("/{chat_id}/messages", response_model=LlmAnswerOut)
async def send_message(chat_id: str, payload: SendMessageIn, user=Depends(get_current_user)) -> LlmAnswerOut:
    return await chats_usecases.send_message(chat_id, payload, str(user["_id"]))


@router.delete("/{chat_id}")
async def delete_chat(chat_id: str, user=Depends(get_current_user)) -> dict[str, bool]:
    return await chats_usecases.delete_chat(chat_id, str(user["_id"]))
