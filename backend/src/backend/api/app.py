from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import health, lp
from backend.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.api_title, version=settings.api_version)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allow_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(lp.router)
    return app


app = create_app()
