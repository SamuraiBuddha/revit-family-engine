"""Ollama backend integration for Revit Family Engine.

Domain-specific system prompts route requests to the fine-tuned
revit-family-32b model (Qwen2.5-Coder-32B base).
"""

from __future__ import annotations

import re
from typing import Optional

import httpx

from .models import (
    CodeGenerationRequest,
    CodeGenerationResponse,
    DynamoGenerationRequest,
    DynamoGenerationResponse,
)

_DOMAIN_PROMPTS: dict[str, str] = {
    "family_geometry": (
        "You are a Revit Family Editor geometry expert. Generate precise, compilable C# code "
        "using Revit API FamilyCreate methods: NewExtrusion, NewRevolution, NewBlend, NewSweep, "
        "NewSweptBlend. Always use Revit internal units (feet = mm/304.8, radians for angles). "
        "Wrap all geometry creation in Transaction blocks. Return only C# code in fenced blocks."
    ),
    "family_parameters": (
        "You are a Revit FamilyManager parameter expert. Generate C# code for FamilyParameter "
        "and FamilyType management using famMgr.AddParameter(), famMgr.NewType(), famMgr.Set(). "
        "FamilyManager operations must occur OUTSIDE Transaction blocks. Use correct "
        "BuiltInParameterGroup and ParameterType enums. Units: feet for length, radians for angles."
    ),
    "constraints": (
        "You are a Revit parametric constraint expert. Generate C# code for ReferencePlane, "
        "NewLinearDimension, EqualConstraint, and FamilyLabel assignment. Reference planes must "
        "be created before dimensions. Use IsReferencesValidForLabel() before assigning labels. "
        "Wrap geometry work in Transactions; dimension/label work can be outside."
    ),
    "family_types": (
        "You are a Revit family type catalog expert. Generate C# code for FamilyTypeTable "
        "iteration, nested family loading (LoadFamily), and type catalog CSV generation. "
        "Use famMgr.Types to iterate existing types. When creating type catalogs, output "
        "valid CSV with ##Revit header syntax."
    ),
    "gdt": (
        "You are a GD&T annotation expert for Revit. Generate C# code applying ASME Y14.5-2018 "
        "geometric tolerances through Revit DimensionType. Set ToleranceType, ToleranceValue, "
        "ToleranceUpperValue, ToleranceLowerValue via BuiltInParameter. Map geometric "
        "characteristics (flatness, perpendicularity, position, etc.) to appropriate Revit "
        "annotation categories. Units in feet (mm/304.8)."
    ),
    "dynamo": (
        "You are a Dynamo scripting expert for parametric Revit family automation. Generate "
        "Python-based Dynamo node scripts using ProtoGeometry (import Autodesk.DesignScript.Geometry) "
        "and RevitNodes. Use IN[] for inputs and OUT for outputs. Keep nodes focused on single "
        "operations. Reference the dynamo-node-search service for node discovery when needed."
    ),
    "building_code": (
        "You are a building code compliance expert for Revit. Generate C# code that validates "
        "family parameters against IBC/NFPA requirements. Use FilteredElementCollector for "
        "element queries. Raise warnings via TaskDialog when parameters fall outside code limits. "
        "Reference ICC and NFPA standard values numerically in comments."
    ),
}

_CSHARP_SIGNALS = [
    r"\busing\s+Autodesk",
    r"\bTransaction\b",
    r"\bFamilyCreate\b",
    r"\bFamilyManager\b",
    r"\bFamilyParameter\b",
    r"\bReferencePlane\b",
    r"\bExtrusion\b",
    r"\bRevolution\b",
    r"\bnew\s+XYZ\b",
    r"\bElementId\b",
    r"\.Commit\(\)",
    r"famMgr\.",
]


class OllamaBackend:
    def __init__(
        self,
        model_name: str = "revit-family-32b",
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
    ) -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def check_availability(self) -> bool:
        try:
            r = await self._client.get("/api/tags")
            return r.status_code == 200
        except Exception:
            return False

    async def aclose(self) -> None:
        await self._client.aclose()

    async def generate_code(self, request: CodeGenerationRequest) -> CodeGenerationResponse:
        system_prompt = _DOMAIN_PROMPTS.get(request.domain, _DOMAIN_PROMPTS["family_geometry"])

        user_parts = [request.prompt]
        if request.context:
            user_parts.append(f"\nRevit context:\n{request.context}")
        if not request.include_comments:
            user_parts.append("\nDo not include inline comments in the code.")
        user_parts.append(f"\nTarget Revit version: {request.revit_version}")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n".join(user_parts)},
        ]

        model = request.model or self.model_name
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.15, "top_p": 0.9},
        }

        try:
            resp = await self._client.post("/api/chat", json=payload)
            resp.raise_for_status()
            raw = resp.json()["message"]["content"]
        except Exception as exc:
            return CodeGenerationResponse(
                code="",
                explanation=f"Ollama request failed: {exc}",
                parameters_used=[],
                confidence=0.0,
                warnings=[str(exc)],
            )

        code, explanation = self._extract_code(raw)
        warnings = self._extract_warnings(code)
        confidence = self._score_confidence(code)

        return CodeGenerationResponse(
            code=code,
            explanation=explanation,
            parameters_used=self._extract_api_refs(code),
            confidence=confidence,
            warnings=warnings,
        )

    async def generate_dynamo(self, request: DynamoGenerationRequest) -> DynamoGenerationResponse:
        system_prompt = _DOMAIN_PROMPTS["dynamo"]
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.prompt},
        ]
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.2, "top_p": 0.9},
        }
        try:
            resp = await self._client.post("/api/chat", json=payload)
            resp.raise_for_status()
            raw = resp.json()["message"]["content"]
        except Exception as exc:
            return DynamoGenerationResponse(
                script="", node_suggestions=[], explanation=str(exc),
                confidence=0.0, warnings=[str(exc)],
            )

        script, explanation = self._extract_code(raw, lang="python")
        node_suggestions = re.findall(r"(?:node|Node):\s*([A-Za-z][A-Za-z0-9. ]+)", raw)
        confidence = min(1.0, 0.3 + 0.5 * bool(script))

        return DynamoGenerationResponse(
            script=script,
            node_suggestions=node_suggestions[:10],
            explanation=explanation,
            confidence=confidence,
            warnings=[],
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @classmethod
    def _extract_code(cls, raw: str, lang: str = "csharp") -> tuple[str, str]:
        # Strategy 1: fenced blocks
        pattern = rf"```(?:{lang}|cs|c#|python|py)?\s*(.*?)```"
        blocks = re.findall(pattern, raw, re.DOTALL | re.IGNORECASE)
        if blocks:
            code = max(blocks, key=len).strip()
            explanation = re.sub(pattern, "", raw, flags=re.DOTALL | re.IGNORECASE).strip()
            return code, explanation

        # Strategy 2: heuristic -- count C# signals
        signal_count = sum(1 for sig in _CSHARP_SIGNALS if re.search(sig, raw))
        if signal_count >= 3:
            return raw.strip(), ""

        # Strategy 3: no code detected
        return "", raw.strip()

    @classmethod
    def _extract_warnings(cls, code: str) -> list[str]:
        warnings = []
        if code and "Transaction" not in code and "FamilyManager" not in code:
            warnings.append(
                "No Transaction or FamilyManager found -- verify geometry is wrapped correctly."
            )
        if re.search(r"\b\d{3,}\.\d+\b", code):
            # Large raw numbers -- might be mm instead of feet
            warnings.append(
                "Large numeric literals detected -- confirm units are in feet (mm / 304.8)."
            )
        return warnings

    @classmethod
    def _score_confidence(cls, code: str) -> float:
        if not code:
            return 0.0
        signal_count = sum(1 for sig in _CSHARP_SIGNALS if re.search(sig, code))
        return min(1.0, 0.2 + 0.1 * signal_count)

    @classmethod
    def _extract_api_refs(cls, code: str) -> list[str]:
        refs = re.findall(r"\bFamilyCreate\.\w+|\bfamMgr\.\w+|\bnew\s+[A-Z][A-Za-z]+\b", code)
        return list(dict.fromkeys(refs))[:10]
