"""GET /api/reference -- Revit API method reference lookup."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..models import APIReferenceEntry

router = APIRouter(tags=["reference"])

_REFERENCE: dict[str, APIReferenceEntry] = {
    entry.method.lower(): entry
    for entry in [
        APIReferenceEntry(
            method="NewExtrusion",
            namespace="Autodesk.Revit.DB",
            signature="Extrusion FamilyItemFactory.NewExtrusion(bool isSolid, CurveArrArray profile, SketchPlane sketchPlane, double end)",
            description="Creates a solid or void extrusion in the family document.",
            example="Extrusion ext = familyDoc.FamilyCreate.NewExtrusion(true, profile, sketchPlane, 1.0);",
            revit_versions=["2020", "2021", "2022", "2023", "2024", "2025", "2026"],
        ),
        APIReferenceEntry(
            method="NewRevolution",
            namespace="Autodesk.Revit.DB",
            signature="Revolution FamilyItemFactory.NewRevolution(bool isSolid, CurveArrArray profile, SketchPlane sketchPlane, Line axis, double startAngle, double endAngle)",
            description="Creates a solid or void revolution around a specified axis.",
            example="Revolution rev = familyDoc.FamilyCreate.NewRevolution(true, profile, sketchPlane, axis, 0, Math.PI * 2);",
            revit_versions=["2020", "2021", "2022", "2023", "2024", "2025", "2026"],
        ),
        APIReferenceEntry(
            method="NewBlend",
            namespace="Autodesk.Revit.DB",
            signature="Blend FamilyItemFactory.NewBlend(bool isSolid, CurveArray topProfile, CurveArray baseProfile, SketchPlane sketchPlane)",
            description="Creates a solid or void blend (loft) between two profiles.",
            example="Blend blend = familyDoc.FamilyCreate.NewBlend(true, topProfile, bottomProfile, sketchPlane);",
            revit_versions=["2020", "2021", "2022", "2023", "2024", "2025", "2026"],
        ),
        APIReferenceEntry(
            method="NewSweep",
            namespace="Autodesk.Revit.DB",
            signature="Sweep FamilyItemFactory.NewSweep(bool isSolid, ReferenceArrayArray profileLoops, SweepProfile profile, int profileIndex, ProfilePlaneLocation profilePlaneLocation)",
            description="Creates a solid or void sweep along a path.",
            example="Sweep sweep = familyDoc.FamilyCreate.NewSweep(true, path, profile, 0, ProfilePlaneLocation.Start);",
            revit_versions=["2020", "2021", "2022", "2023", "2024", "2025", "2026"],
        ),
        APIReferenceEntry(
            method="AddParameter",
            namespace="Autodesk.Revit.DB",
            signature="FamilyParameter FamilyManager.AddParameter(string parameterName, BuiltInParameterGroup parameterGroup, ParameterType parameterType, bool isInstance)",
            description="Adds a new family parameter. Must be called outside a Transaction.",
            example='FamilyParameter p = famMgr.AddParameter("Width", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);',
            revit_versions=["2020", "2021", "2022", "2023", "2024", "2025", "2026"],
        ),
        APIReferenceEntry(
            method="NewReferencePlane",
            namespace="Autodesk.Revit.DB",
            signature="ReferencePlane FamilyItemFactory.NewReferencePlane(XYZ bubbleEnd, XYZ freeEnd, XYZ thirdPnt, View view)",
            description="Creates a reference plane in the family editor.",
            example="ReferencePlane rp = familyDoc.FamilyCreate.NewReferencePlane(new XYZ(0,0,0), new XYZ(0,1,0), XYZ.BasisZ, activeView);",
            revit_versions=["2020", "2021", "2022", "2023", "2024", "2025", "2026"],
        ),
        APIReferenceEntry(
            method="NewLinearDimension",
            namespace="Autodesk.Revit.DB",
            signature="Dimension FamilyItemFactory.NewLinearDimension(View view, Line dimensionLine, ReferenceArray references)",
            description="Creates a linear dimension between two references.",
            example="Dimension dim = familyDoc.FamilyCreate.NewLinearDimension(view, dimLine, refArr);",
            revit_versions=["2020", "2021", "2022", "2023", "2024", "2025", "2026"],
        ),
    ]
}


@router.get("/api/reference", tags=["reference"])
async def list_references() -> list[str]:
    return [e.method for e in _REFERENCE.values()]


@router.get("/api/reference/{method}", response_model=APIReferenceEntry, tags=["reference"])
async def get_reference(method: str) -> APIReferenceEntry:
    entry = _REFERENCE.get(method.lower())
    if entry is None:
        raise HTTPException(404, f"No reference entry for method '{method}'")
    return entry
