from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    mongo_uri: str
    mongo_db: str
    redis_url: str
    jwt_secret: str
    access_token_ttl_seconds: int
    refresh_ttl_seconds: int
    github_client_id: str | None
    github_client_secret: str | None
    base_url: str
    llm_model_path: str | None
    ollama_url: str | None
    ollama_model: str | None
    openai_api_key: str | None
    openai_base_url: str | None
    openai_model: str | None


def _load_dotenv(dotenv_path: Path) -> None:
    if not dotenv_path.exists() or not dotenv_path.is_file():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        if key not in os.environ:
            os.environ[key] = value


def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[1]
    _load_dotenv(project_root / ".env")

    jwt_secret = os.getenv("JWT_SECRET", "").strip()

    return Settings(
        mongo_uri=os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
        mongo_db=os.getenv("MONGODB_DB", "wad_homework_2"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        jwt_secret=jwt_secret,
        access_token_ttl_seconds=int(os.getenv("ACCESS_TTL_SECONDS", "900")),
        refresh_ttl_seconds=int(os.getenv("REFRESH_TTL_SECONDS", str(30 * 24 * 60 * 60))),
        github_client_id=os.getenv("GITHUB_CLIENT_ID") or None,
        github_client_secret=os.getenv("GITHUB_CLIENT_SECRET") or None,
        base_url=os.getenv("BASE_URL", "http://127.0.0.1:8000"),
        llm_model_path=os.getenv("MODEL_PATH") or None,
        ollama_url=os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/") or None,
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3") or None,
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com").rstrip("/") or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini") or None,
    )
