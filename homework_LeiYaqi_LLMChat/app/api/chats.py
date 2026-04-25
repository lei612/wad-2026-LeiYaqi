from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_current_user
from ..schemas import ChatCreateIn, ChatOut, ChatWithMessagesOut, LlmAnswerOut, MessageOut, SendMessageIn
from ..services import chats as chat_store
from ..services.llm import answer_chat


router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.get("", response_model=list[ChatOut])
def list_my_chats(user=Depends(get_current_user)) -> list[ChatOut]:
    chats = chat_store.list_chats(str(user["_id"]))
    return [ChatOut(**c) for c in chats]


@router.post("", response_model=ChatOut)
def create_chat(payload: ChatCreateIn, user=Depends(get_current_user)) -> ChatOut:
    c = chat_store.create_chat(str(user["_id"]), payload.title)
    return ChatOut(**c)


@router.get("/{chat_id}", response_model=ChatWithMessagesOut)
def get_chat(chat_id: str, user=Depends(get_current_user)) -> ChatWithMessagesOut:
    c = chat_store.get_chat(str(user["_id"]), chat_id)
    if c is None:
        raise HTTPException(status_code=404, detail="chat_not_found")
    msgs = chat_store.list_messages(str(user["_id"]), chat_id)
    out = ChatWithMessagesOut(
        id=str(c["_id"]),
        title=str(c.get("title", "")),
        created_at=str(c.get("created_at", "")),
        messages=[MessageOut(**m) for m in msgs],
    )
    return out


@router.post("/{chat_id}/messages", response_model=LlmAnswerOut)
def send_message(chat_id: str, payload: SendMessageIn, user=Depends(get_current_user)) -> LlmAnswerOut:
    c = chat_store.get_chat(str(user["_id"]), chat_id)
    if c is None:
        raise HTTPException(status_code=404, detail="chat_not_found")

    user_msg = chat_store.add_message(chat_id, str(user["_id"]), role="user", content=payload.content)
    history = chat_store.list_messages(str(user["_id"]), chat_id)
    llm_text = answer_chat([{"role": str(m.get("role", "user")), "content": str(m.get("content", ""))} for m in history][-12:])
    assistant_msg = chat_store.add_message(chat_id, str(user["_id"]), role="assistant", content=llm_text)
    return LlmAnswerOut(user_message=MessageOut(**user_msg), assistant_message=MessageOut(**assistant_msg))


@router.delete("/{chat_id}")
def delete_chat(chat_id: str, user=Depends(get_current_user)) -> dict[str, bool]:
    ok = chat_store.delete_chat(str(user["_id"]), chat_id)
    if not ok:
        raise HTTPException(status_code=404, detail="chat_not_found")
    return {"ok": True}
