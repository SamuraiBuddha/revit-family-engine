"""POST /api/resolve-parameters -- parameter space resolution to C# code."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from parameterization import PREDEFINED_SPACES, ParameterResolver
from ..models import ParameterResolveRequest, ParameterResolveResponse

router = APIRouter(tags=["parameters"])
_resolver = ParameterResolver()


@router.post("/api/resolve-parameters", response_model=ParameterResolveResponse)
async def resolve_parameters(body: ParameterResolveRequest) -> ParameterResolveResponse:
    space = PREDEFINED_SPACES.get(body.parameter_space_name)
    if space is None:
        raise HTTPException(404, f"Parameter space '{body.parameter_space_name}' not found")

    errors: list[str] = []
    from parameterization import ParameterAssignment
    assignment = ParameterAssignment(parameter_space=space, values={})

    for name, value in body.assignments.items():
        ok, err = space.validate_assignment(name, value)
        if not ok:
            errors.append(err)
        else:
            assignment.values[name] = value

    # Fill defaults for missing params
    for name, param in space.parameters.items():
        if name not in assignment.values:
            assignment.values[name] = param.default_value

    code = _resolver.resolve(assignment)

    return ParameterResolveResponse(
        generated_code=code,
        parameter_space=body.parameter_space_name,
        assignments_used=assignment.to_dict(),
        validation_errors=errors,
    )


@router.get("/api/parameter-spaces", tags=["parameters"])
async def list_parameter_spaces() -> list[str]:
    return list(PREDEFINED_SPACES.keys())
