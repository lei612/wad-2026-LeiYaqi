from __future__ import annotations

from functools import lru_cache

import httpx

from ..settings import get_settings


@lru_cache(maxsize=1)
def _get_llm():
    s = get_settings()
    if not s.llm_model_path:
        return None
    try:
        from llama_cpp import Llama
    except Exception:
        return None
    return Llama(model_path=s.llm_model_path, n_ctx=512, n_threads=4)


def _ollama_answer(messages: list[dict[str, str]]) -> str:
    s = get_settings()
    if not s.ollama_url:
        raise RuntimeError("ollama_not_configured")
    def pick_model() -> str | None:
        try:
            with httpx.Client(timeout=5, trust_env=False) as c:
                r = c.get(f"{s.ollama_url}/api/tags")
                r.raise_for_status()
                data = r.json()
                models = data.get("models") or []
                if not models:
                    return None
                return str(models[0].get("name") or models[0].get("model") or "").strip() or None
        except Exception:
            return None
    model0 = (s.ollama_model or "").strip() or pick_model()
    if not model0:
        raise RuntimeError("ollama_no_models")
    with httpx.Client(timeout=180, trust_env=False) as c:
        def call(model: str) -> httpx.Response:
            return c.post(
                f"{s.ollama_url}/api/chat",
                json={"model": model, "messages": messages, "stream": False},
            )

        model = model0
        r = call(model)
        if not r.is_success:
            alt = pick_model()
            if alt and alt != model:
                r = call(alt)
        r.raise_for_status()
        data = r.json()
        msg = (data.get("message") or {}).get("content")
        if not msg:
            raise RuntimeError("ollama_bad_response")
        return str(msg).strip()


def _openai_answer(messages: list[dict[str, str]]) -> str:
    s = get_settings()
    if not s.openai_api_key:
        raise RuntimeError("openai_not_configured")
    base = s.openai_base_url or "https://api.openai.com"
    model = s.openai_model or "gpt-4o-mini"
    with httpx.Client(timeout=30, trust_env=False) as c:
        r = c.post(
            f"{base}/v1/chat/completions",
            headers={"Authorization": f"Bearer {s.openai_api_key}"},
            json={"model": model, "messages": messages, "temperature": 0.7},
        )
        r.raise_for_status()
        data = r.json()
        content = (((data.get("choices") or [{}])[0].get("message") or {}).get("content")) or ""
        if not content:
            raise RuntimeError("openai_bad_response")
        return str(content).strip()


def answer(prompt: str) -> str:
    llm = _get_llm()
    messages = [{"role": "user", "content": prompt}]
    try:
        return _openai_answer(messages)
    except Exception:
        pass
    try:
        return _ollama_answer(messages)
    except Exception:
        pass
    if llm is None:
        return "LLM is not configured. Set OPENAI_API_KEY or run Ollama and set OLLAMA_URL/OLLAMA_MODEL (default: http://127.0.0.1:11434, llama3)."
    result = llm(f"User: {prompt}\nAssistant:", max_tokens=200, stream=False)
    text = result["choices"][0]["text"]
    return str(text).strip()


def answer_chat(messages: list[dict[str, str]]) -> str:
    llm = _get_llm()
    openai_err: str | None = None
    ollama_err: str | None = None
    try:
        return _openai_answer(messages)
    except Exception as e:
        openai_err = type(e).__name__
    try:
        return _ollama_answer(messages)
    except Exception as e:
        ollama_err = type(e).__name__
    if llm is None:
        if ollama_err and ollama_err != "RuntimeError":
            return f"Ollama error: {ollama_err}"
        if ollama_err == "RuntimeError":
            return "Ollama is configured but not ready (model missing or startup). Check /api/llm/status."
        if openai_err and openai_err != "RuntimeError":
            return f"OpenAI error: {openai_err}"
        return "LLM is not configured. Set OPENAI_API_KEY or run Ollama and set OLLAMA_URL/OLLAMA_MODEL."
    prompt = "\n".join([f"{m.get('role','user').title()}: {m.get('content','')}" for m in messages[-12:]])
    result = llm(f"{prompt}\nAssistant:", max_tokens=200, stream=False)
    text = result["choices"][0]["text"]
    return str(text).strip()
