"""Revit Family Engine -- FastAPI backend entry point."""

from __future__ import annotations

import logging
import os
import socket
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .ollama_backend import OllamaBackend
from .routes import dynamo, generate, parameters, reference

logger = logging.getLogger(__name__)

_PORT_FILE = Path.home() / ".rfe-port"


def _detect_port() -> int | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]
    except Exception:
        return None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    model = os.environ.get("RFE_MODEL", "revit-family-32b")
    ollama_url = os.environ.get("RFE_OLLAMA_URL", "http://localhost:11434")
    backend = OllamaBackend(model_name=model, base_url=ollama_url)
    app.state.ollama = backend

    available = await backend.check_availability()
    if available:
        logger.info("[OK] Ollama backend reachable, model=%s", model)
    else:
        logger.warning("[WARN] Ollama backend not reachable at %s", ollama_url)

    port = _detect_port()
    if port:
        _PORT_FILE.write_text(str(port))

    yield

    await backend.aclose()
    _PORT_FILE.unlink(missing_ok=True)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Revit Family Engine",
        description="AI-powered Revit family creation via local fine-tuned LLM",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(generate.router)
    app.include_router(parameters.router)
    app.include_router(reference.router)
    app.include_router(dynamo.router)

    @app.get("/", tags=["meta"])
    async def root() -> dict:
        return {"service": "Revit Family Engine", "status": "running"}

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        ollama_ok = await app.state.ollama.check_availability()
        return {
            "service": "Revit Family Engine",
            "status": "healthy" if ollama_ok else "degraded",
            "ollama_available": ollama_ok,
            "model": app.state.ollama.model_name,
        }

    return app


app = create_app()
