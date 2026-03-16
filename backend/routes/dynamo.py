"""POST /api/generate-dynamo -- Dynamo script generation."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ..models import DynamoGenerationRequest, DynamoGenerationResponse

router = APIRouter(tags=["dynamo"])


@router.post("/api/generate-dynamo", response_model=DynamoGenerationResponse)
async def generate_dynamo(
    body: DynamoGenerationRequest, request: Request
) -> DynamoGenerationResponse:
    ollama = request.app.state.ollama
    if not await ollama.check_availability():
        raise HTTPException(503, "Ollama backend is not available")

    return await ollama.generate_dynamo(body)
