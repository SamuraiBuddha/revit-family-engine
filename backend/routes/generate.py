"""POST /api/generate-code -- Revit API C# code generation."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ..models import CodeGenerationRequest, CodeGenerationResponse, VALID_DOMAINS

router = APIRouter(tags=["generate"])


@router.post("/api/generate-code", response_model=CodeGenerationResponse)
async def generate_code(
    body: CodeGenerationRequest, request: Request
) -> CodeGenerationResponse:
    if body.domain not in VALID_DOMAINS:
        raise HTTPException(400, f"Invalid domain '{body.domain}'")

    ollama = request.app.state.ollama
    if not await ollama.check_availability():
        raise HTTPException(503, "Ollama backend is not available")

    return await ollama.generate_code(body)
