from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RegisterIn(BaseModel):
    login: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=200)


class LoginIn(BaseModel):
    login: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=200)


class TokensOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=512)


class UserOut(BaseModel):
    id: str
    login: str


class ChatCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200, default="New chat")


class ChatOut(BaseModel):
    id: str
    title: str
    created_at: str


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class ChatWithMessagesOut(ChatOut):
    messages: list[MessageOut]


class SendMessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class LlmAnswerOut(BaseModel):
    user_message: MessageOut
    assistant_message: MessageOut


class EditorJsContent(BaseModel):
    time: int = 0
    blocks: list[dict[str, Any]] = []
    version: str = "2"

