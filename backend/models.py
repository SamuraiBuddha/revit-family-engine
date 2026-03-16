"""Pydantic request/response models for the Revit Family Engine backend."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, field_validator

VALID_DOMAINS = {
    "family_geometry",
    "family_parameters",
    "constraints",
    "family_types",
    "gdt",
    "dynamo",
    "building_code",
}


class CodeGenerationRequest(BaseModel):
    prompt: str
    domain: str = "family_geometry"
    context: Optional[str] = None
    include_comments: bool = True
    model: Optional[str] = None
    revit_version: str = "2026"

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        if v not in VALID_DOMAINS:
            raise ValueError(f"Invalid domain '{v}'. Must be one of: {sorted(VALID_DOMAINS)}")
        return v


class CodeGenerationResponse(BaseModel):
    code: str
    explanation: str
    parameters_used: List[str]
    confidence: float
    warnings: List[str]


class ParameterResolveRequest(BaseModel):
    parameter_space_name: str
    assignments: Dict[str, Any]


class ParameterResolveResponse(BaseModel):
    generated_code: str
    parameter_space: str
    assignments_used: Dict[str, Any]
    validation_errors: List[str]


class DynamoGenerationRequest(BaseModel):
    prompt: str
    context: Optional[str] = None
    revit_version: str = "2026"


class DynamoGenerationResponse(BaseModel):
    script: str
    node_suggestions: List[str]
    explanation: str
    confidence: float
    warnings: List[str]


class APIReferenceEntry(BaseModel):
    method: str
    namespace: str
    signature: str
    description: str
    example: str
    revit_versions: List[str]
