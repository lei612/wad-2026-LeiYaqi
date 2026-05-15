from __future__ import annotations

from fastapi import APIRouter

from ..services.llm_usecases import get_llm_status


router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.get("/status")
async def llm_status() -> dict[str, object]:
    return await get_llm_status()
