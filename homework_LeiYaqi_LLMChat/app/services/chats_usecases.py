from __future__ import annotations

from fastapi import HTTPException

from ..schemas import ChatCreateIn, ChatOut, ChatWithMessagesOut, LlmAnswerOut, MessageOut, SendMessageIn
from . import chats as chat_store
from .llm import answer_chat


async def list_my_chats(user_id: str) -> list[ChatOut]:
    chats = await chat_store.list_chats(user_id)
    return [ChatOut(**c) for c in chats]


async def create_chat(payload: ChatCreateIn, user_id: str) -> ChatOut:
    c = await chat_store.create_chat(user_id, payload.title)
    return ChatOut(**c)


async def get_chat(chat_id: str, user_id: str) -> ChatWithMessagesOut:
    c = await chat_store.get_chat(user_id, chat_id)
    if c is None:
        raise HTTPException(status_code=404, detail="chat_not_found")
    msgs = await chat_store.list_messages(user_id, chat_id)
    return ChatWithMessagesOut(
        id=str(c["_id"]),
        title=str(c.get("title", "")),
        created_at=str(c.get("created_at", "")),
        messages=[MessageOut(**m) for m in msgs],
    )


async def send_message(chat_id: str, payload: SendMessageIn, user_id: str) -> LlmAnswerOut:
    c = await chat_store.get_chat(user_id, chat_id)
    if c is None:
        raise HTTPException(status_code=404, detail="chat_not_found")

    user_msg = await chat_store.add_message(chat_id, user_id, role="user", content=payload.content)
    history = await chat_store.list_messages(user_id, chat_id)
    llm_text = await answer_chat([{"role": str(m.get("role", "user")), "content": str(m.get("content", ""))} for m in history][-12:])
    assistant_msg = await chat_store.add_message(chat_id, user_id, role="assistant", content=llm_text)
    return LlmAnswerOut(user_message=MessageOut(**user_msg), assistant_message=MessageOut(**assistant_msg))


async def delete_chat(chat_id: str, user_id: str) -> dict[str, bool]:
    ok = await chat_store.delete_chat(user_id, chat_id)
    if not ok:
        raise HTTPException(status_code=404, detail="chat_not_found")
    return {"ok": True}

