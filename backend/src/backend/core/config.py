from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    """Central place for API metadata and CORS allowlists used by the FastAPI app."""

    api_title: str = "LP Tutor API"
    api_version: str = "0.1.0"
    cors_allow_origins: tuple[str, ...] = (
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
    )


settings = Settings()
