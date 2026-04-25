from __future__ import annotations

import httpx
from fastapi import APIRouter

from ..settings import get_settings


router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.get("/status")
def llm_status() -> dict[str, object]:
    s = get_settings()

    openai = bool(s.openai_api_key)

    ollama_ok = False
    ollama_error: str | None = None
    ollama_models: list[str] = []
    ollama_model_found = False
    if s.ollama_url:
        try:
            with httpx.Client(timeout=1.5, trust_env=False) as c:
                r = c.get(f"{s.ollama_url}/api/tags")
                if r.status_code == 200:
                    data = r.json()
                    models = data.get("models") or []
                    ollama_models = [str(m.get("name") or m.get("model") or "") for m in models if (m.get("name") or m.get("model"))]
                    desired = (s.ollama_model or "").strip()
                    if desired:
                        ollama_model_found = any((m == desired or m.startswith(desired + ":")) for m in ollama_models)
                    ollama_ok = bool(ollama_models)
        except Exception:
            ollama_ok = False
            ollama_error = "unreachable"

    llama_cpp_ok = False
    if s.llm_model_path:
        try:
            from llama_cpp import Llama  # type: ignore

            llama_cpp_ok = bool(Llama)
        except Exception:
            llama_cpp_ok = False

    configured = openai or ollama_ok or llama_cpp_ok
    return {
        "configured": configured,
        "openai": openai,
        "ollama": ollama_ok,
        "ollama_error": ollama_error,
        "ollama_models": ollama_models,
        "ollama_model_found": ollama_model_found,
        "llama_cpp": llama_cpp_ok,
        "ollama_url": s.ollama_url,
        "ollama_model": s.ollama_model,
        "openai_model": s.openai_model,
    }
