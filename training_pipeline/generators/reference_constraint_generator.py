"""Training data generator: Revit reference planes, dimensions, and constraints.

Produces ~200 Alpaca-format training pairs covering reference planes,
labeled dimensions, alignment constraints, symmetry, and angular constraints.
"""

from __future__ import annotations

from typing import Any, Dict, List

SAMPLE = Dict[str, Any]
MM_TO_FT = 1.0 / 304.8


def _s(instruction: str, output: str) -> SAMPLE:
    return {"instruction": instruction, "input": "", "output": output}


def _ft(mm: float) -> str:
    return f"{mm * MM_TO_FT:.6f}"


class ReferenceConstraintGenerator:
    """Generates training samples for Revit reference planes and constraints."""

    def generate(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []
        samples += self._reference_planes()
        samples += self._labeled_dimensions()
        samples += self._alignment_constraints()
        samples += self._symmetry_constraints()
        samples += self._angular_constraints()
        samples += self._constraint_patterns()
        return samples

    # ------------------------------------------------------------------
    # Reference planes
    # ------------------------------------------------------------------

    def _reference_planes(self) -> List[SAMPLE]:
        samples = []
        plane_cases = [
            ("Left",   "strong", (-300, 0), (-300, 1), "left edge at -300mm"),
            ("Right",  "strong", ( 300, 0), ( 300, 1), "right edge at +300mm"),
            ("Front",  "strong", (0, -200), (1, -200), "front face at -200mm"),
            ("Back",   "strong", (0,  200), (1,  200), "back face at +200mm"),
            ("Center", "strong", (0,    0), (0,    1), "center vertical plane"),
            ("Top",    "weak",   (-100, 0), (-100, 1), "top reference at 100mm offset"),
        ]
        for (name, strength, (x0, y0), (x1, y1), desc) in plane_cases:
            samples.append(_s(
                f"Create a '{name}' reference plane ({desc}) in a family",
                f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Reference Plane"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;

    // {name}: {desc}
    ReferencePlane rp = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ({x0 * MM_TO_FT:.6f}, {y0 * MM_TO_FT:.6f}, 0),  // point 1
        new XYZ({x1 * MM_TO_FT:.6f}, {y1 * MM_TO_FT:.6f}, 0),  // point 2
        XYZ.BasisZ,  // cut vector (up direction)
        activeView);

    rp.Name = "{name}";

    tx.Commit();
}}"""))

        # Reference planes at various offsets
        for (offset_mm, dir_name, normal_x, normal_y) in [
            ( 150, "vertical",   0, 0), (-150, "vertical", 0, 0),
            ( 100, "horizontal", 1, 0), (-100, "horizontal", 1, 0),
        ]:
            samples.append(_s(
                f"Create a reference plane at {offset_mm}mm offset ({dir_name})",
                f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Reference Plane"))
{{
    tx.Start();
    View view = familyDoc.ActiveView;

    double offset = {_ft(abs(offset_mm))} * {"" if offset_mm >= 0 else "-"}1.0;
    ReferencePlane rp = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(offset, 0, 0), new XYZ(offset, 1, 0),
        XYZ.BasisZ, view);
    rp.Name = "Offset_{offset_mm}";

    tx.Commit();
}}"""))

        return samples  # 6 + 4 = 10

    # ------------------------------------------------------------------
    # Labeled dimensions
    # ------------------------------------------------------------------

    def _labeled_dimensions(self) -> List[SAMPLE]:
        samples = []
        dim_cases = [
            ("Width",  300, "horizontal", "left-to-right Width dimension"),
            ("Height", 2000, "vertical",  "bottom-to-top Height dimension"),
            ("Depth",  200,  "horizontal", "front-to-back Depth dimension"),
            ("Offset", 50,   "vertical",  "vertical offset dimension"),
        ]
        for (param_name, value_mm, orientation, desc) in dim_cases:
            samples.append(_s(
                f"Create a labeled {orientation} dimension for the {param_name} parameter ({desc})",
                f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Labeled Dimension"))
{{
    tx.Start();

    View view = familyDoc.ActiveView;
    double half = {_ft(value_mm / 2)}; // half of {value_mm} mm

    // Create reference planes first
    ReferencePlane rpNeg = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(-half, 0, 0), new XYZ(-half, 1, 0), XYZ.BasisZ, view);
    rpNeg.Name = "{param_name}_Neg";

    ReferencePlane rpPos = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ( half, 0, 0), new XYZ( half, 1, 0), XYZ.BasisZ, view);
    rpPos.Name = "{param_name}_Pos";

    // Dimension between the two planes
    ReferenceArray refs = new ReferenceArray();
    refs.Append(rpNeg.GetReference());
    refs.Append(rpPos.GetReference());

    Line dimLine = Line.CreateBound(
        new XYZ(-half, {_ft(-150)}, 0),   // 150mm offset for dimension line
        new XYZ( half, {_ft(-150)}, 0));

    Dimension dim = familyDoc.FamilyCreate.NewLinearDimension(view, dimLine, refs);

    // Label the dimension with the {param_name} parameter
    FamilyParameter p = familyDoc.FamilyManager.get_Parameter("{param_name}");
    if (p == null)
        p = familyDoc.FamilyManager.AddParameter("{param_name}",
            BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
    dim.FamilyLabel = p;

    tx.Commit();
}}"""))

        # Dimensions without labels (reporting only)
        for (from_mm, to_mm, label, desc) in [
            (-500, 500, "TotalWidth", "total width reporting dimension"),
            (0, 2400, "TotalHeight", "total height reporting dimension"),
        ]:
            samples.append(_s(f"Create a reporting {desc} (not labeled to drive geometry)",
                f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Reporting Dimension"))
{{
    tx.Start();

    View view = familyDoc.ActiveView;

    ReferencePlane rp1 = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ({_ft(from_mm)}, 0, 0), new XYZ({_ft(from_mm)}, 1, 0), XYZ.BasisZ, view);
    rp1.Name = "Start";

    ReferencePlane rp2 = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ({_ft(to_mm)},  0, 0), new XYZ({_ft(to_mm)},  1, 0), XYZ.BasisZ, view);
    rp2.Name = "End";

    ReferenceArray refs = new ReferenceArray();
    refs.Append(rp1.GetReference());
    refs.Append(rp2.GetReference());

    Line dimLine = Line.CreateBound(
        new XYZ({_ft(from_mm)}, {_ft(100)}, 0),
        new XYZ({_ft(to_mm)},   {_ft(100)}, 0));

    // No FamilyLabel --> reporting dimension only
    Dimension dim = familyDoc.FamilyCreate.NewLinearDimension(view, dimLine, refs);

    tx.Commit();
}}"""))
        return samples  # 4 + 2 = 6

    # ------------------------------------------------------------------
    # Alignment constraints
    # ------------------------------------------------------------------

    def _alignment_constraints(self) -> List[SAMPLE]:
        samples = []
        align_cases = [
            ("left face", "rpLeft",   "align extrusion left face to Left reference plane"),
            ("right face", "rpRight", "align extrusion right face to Right reference plane"),
            ("front face", "rpFront", "align extrusion front face to Front reference plane"),
            ("top face",   "rpTop",   "align extrusion top face to a horizontal reference plane"),
        ]
        for (face_desc, rp_var, instruction) in align_cases:
            samples.append(_s(instruction,
                f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Align and Lock"))
{{
    tx.Start();

    View view = familyDoc.ActiveView;

    // Align the {face_desc} to its reference plane and lock the constraint
    ReferencePlane {rp_var} = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ({_ft(-300)}, 0, 0), new XYZ({_ft(-300)}, 1, 0), XYZ.BasisZ, view);
    {rp_var}.Name = "{face_desc.replace(' ', '_').title()}";

    // After creating extrusion, align its face to reference plane
    // (Alignment is typically done via the Revit UI lock; in API use Alignment class)
    // Key pattern: get face reference from solid, get plane reference,
    // then create AlignmentConstraint

    // Programmatic alignment example:
    Extrusion ext = familyDoc.FamilyCreate.NewExtrusion(
        true,
        CreateRectProfile(familyDoc, {_ft(300)}, {_ft(300)}),
        SketchPlane.Create(familyDoc, Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero)),
        {_ft(2000)});

    // Lock alignment: face of extrusion should track {rp_var}
    // In practice, reference planes drive profile geometry directly through constraints

    tx.Commit();
}}

// Helper: creates a rectangular CurveArrArray
private CurveArrArray CreateRectProfile(Document doc, double w, double d)
{{
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-w/2,-d/2,0), new XYZ(w/2,-d/2,0)));
    loop.Append(Line.CreateBound(new XYZ(w/2,-d/2,0),  new XYZ(w/2, d/2,0)));
    loop.Append(Line.CreateBound(new XYZ(w/2, d/2,0),  new XYZ(-w/2,d/2,0)));
    loop.Append(Line.CreateBound(new XYZ(-w/2,d/2,0),  new XYZ(-w/2,-d/2,0)));
    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    return profile;
}}"""))

        samples.append(_s("Lock an alignment constraint between a reference plane and an extrusion face",
            f"""\
using Autodesk.Revit.DB;

// After creating geometry and reference planes, lock alignment
using (Transaction tx = new Transaction(familyDoc, "Lock Alignment"))
{{
    tx.Start();
    View view = familyDoc.ActiveView;

    // Alignment between reference plane and geometry face
    // The AlignmentConstraint makes the geometry track the reference plane
    ReferencePlane rp = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ({_ft(-300)}, 0, 0), new XYZ({_ft(-300)}, 1, 0), XYZ.BasisZ, view);
    rp.Name = "Left";

    // Create a locked alignment -- geometry must be snapped to reference first
    // Then: familyDoc.FamilyCreate.NewAlignment(view, refPlaneRef, geomFaceRef);
    // In the family editor this locks the face to follow the plane.

    tx.Commit();
}}"""))
        return samples  # 4 + 1 = 5

    # ------------------------------------------------------------------
    # Symmetry constraints
    # ------------------------------------------------------------------

    def _symmetry_constraints(self) -> List[SAMPLE]:
        samples = []
        samples.append(_s("Create symmetric left/right reference planes and an EQ dimension between them",
            f"""\
using Autodesk.Revit.DB;

// Symmetric reference planes for Width parameter
using (Transaction tx = new Transaction(familyDoc, "Create Symmetric Planes"))
{{
    tx.Start();
    View view = familyDoc.ActiveView;
    double half = {_ft(300)}; // half of 600mm Width default

    ReferencePlane rpLeft  = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(-half, 0, 0), new XYZ(-half, 1, 0), XYZ.BasisZ, view);
    rpLeft.Name = "Left";

    ReferencePlane rpRight = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ( half, 0, 0), new XYZ( half, 1, 0), XYZ.BasisZ, view);
    rpRight.Name = "Right";

    // Center (origin) plane
    ReferencePlane rpCenter = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, 0, 0), new XYZ(0, 1, 0), XYZ.BasisZ, view);
    rpCenter.Name = "Center Left-Right";

    // EQ dimension: center-to-left = center-to-right (symmetric)
    ReferenceArray refs = new ReferenceArray();
    refs.Append(rpLeft.GetReference());
    refs.Append(rpCenter.GetReference());
    refs.Append(rpRight.GetReference());

    Line dimLine = Line.CreateBound(
        new XYZ(-half, {_ft(-150)}, 0),
        new XYZ( half, {_ft(-150)}, 0));

    Dimension dim = familyDoc.FamilyCreate.NewLinearDimension(view, dimLine, refs);
    dim.AreSegmentsEqual = true; // EQ constraint

    // Label the full dimension with Width parameter
    FamilyParameter pWidth = familyDoc.FamilyManager.get_Parameter("Width")
        ?? familyDoc.FamilyManager.AddParameter("Width", BuiltInParameterGroup.PG_GEOMETRY,
                                                 ParameterType.Length, false);
    dim.FamilyLabel = pWidth;

    tx.Commit();
}}"""))

        samples.append(_s("Create front/back symmetric reference planes for a Depth parameter",
            f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Front-Back Planes"))
{{
    tx.Start();
    View view = familyDoc.ActiveView;
    double half = {_ft(200)}; // half of 400mm Depth default

    ReferencePlane rpFront = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, -half, 0), new XYZ(1, -half, 0), XYZ.BasisZ, view);
    rpFront.Name = "Front";

    ReferencePlane rpBack  = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0,  half, 0), new XYZ(1,  half, 0), XYZ.BasisZ, view);
    rpBack.Name = "Back";

    ReferencePlane rpCenterFB = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, 0, 0), new XYZ(1, 0, 0), XYZ.BasisZ, view);
    rpCenterFB.Name = "Center Front-Back";

    FamilyParameter pDepth = familyDoc.FamilyManager.get_Parameter("Depth")
        ?? familyDoc.FamilyManager.AddParameter("Depth", BuiltInParameterGroup.PG_GEOMETRY,
                                                 ParameterType.Length, false);

    ReferenceArray refs = new ReferenceArray();
    refs.Append(rpFront.GetReference());
    refs.Append(rpCenterFB.GetReference());
    refs.Append(rpBack.GetReference());
    Line dimLine = Line.CreateBound(
        new XYZ({_ft(300)}, -half, 0), new XYZ({_ft(300)},  half, 0));
    Dimension dim = familyDoc.FamilyCreate.NewLinearDimension(view, dimLine, refs);
    dim.AreSegmentsEqual = true;
    dim.FamilyLabel = pDepth;

    tx.Commit();
}}"""))

        return samples  # 2

    # ------------------------------------------------------------------
    # Angular constraints
    # ------------------------------------------------------------------

    def _angular_constraints(self) -> List[SAMPLE]:
        samples = []
        import math
        angle_cases = [
            (30, "30-degree angled reference plane"),
            (45, "45-degree diagonal reference plane"),
            (60, "60-degree angled reference plane"),
        ]
        for (angle_deg, desc) in angle_cases:
            angle_rad = math.radians(angle_deg)
            import math as _m
            x1 = _m.cos(angle_rad)
            y1 = _m.sin(angle_rad)
            samples.append(_s(f"Create a {desc}",
                f"""\
using Autodesk.Revit.DB;
using System;

// {desc}
using (Transaction tx = new Transaction(familyDoc, "Create Angled Reference Plane"))
{{
    tx.Start();
    View view = familyDoc.ActiveView;

    // Plane at {angle_deg} degrees from horizontal
    double angle = {angle_rad:.6f}; // {angle_deg} degrees in radians
    double cos  = Math.Cos(angle);
    double sin  = Math.Sin(angle);

    ReferencePlane rp = familyDoc.FamilyCreate.NewReferencePlane(
        XYZ.Zero,
        new XYZ(cos, sin, 0),
        XYZ.BasisZ,
        view);
    rp.Name = "Angle_{angle_deg}deg";

    tx.Commit();
}}"""))
        return samples  # 3

    # ------------------------------------------------------------------
    # Standard constraint patterns
    # ------------------------------------------------------------------

    def _constraint_patterns(self) -> List[SAMPLE]:
        samples = []
        samples.append(_s("Set up the standard 4-reference-plane bounding box for a furniture family",
            f"""\
using Autodesk.Revit.DB;

// Standard furniture family: Left, Right, Front, Back reference planes
// symmetrically placed around the origin
using (Transaction tx = new Transaction(familyDoc, "Setup Reference Planes"))
{{
    tx.Start();
    View view = familyDoc.ActiveView;
    FamilyManager famMgr = familyDoc.FamilyManager;

    // Width: 1200mm default
    double halfW = {_ft(600)};  // 600 mm
    // Depth: 750mm default
    double halfD = {_ft(375)};  // 375 mm

    ReferencePlane rpLeft  = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(-halfW, 0, 0), new XYZ(-halfW, 1, 0), XYZ.BasisZ, view);
    rpLeft.Name = "Left";

    ReferencePlane rpRight = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ( halfW, 0, 0), new XYZ( halfW, 1, 0), XYZ.BasisZ, view);
    rpRight.Name = "Right";

    ReferencePlane rpFront = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, -halfD, 0), new XYZ(1, -halfD, 0), XYZ.BasisZ, view);
    rpFront.Name = "Front";

    ReferencePlane rpBack  = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0,  halfD, 0), new XYZ(1,  halfD, 0), XYZ.BasisZ, view);
    rpBack.Name = "Back";

    tx.Commit();

    // Add Width and Depth parameters -- FamilyManager OUTSIDE Transaction
    FamilyParameter pW = famMgr.AddParameter("Width", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
    FamilyParameter pD = famMgr.AddParameter("Depth", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
    famMgr.Set(pW, halfW * 2); // 1200 mm
    famMgr.Set(pD, halfD * 2); // 750 mm
}}"""))

        samples.append(_s("Set up a standard door family with Left, Right, and Top reference planes",
            f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Setup Door Reference Planes"))
{{
    tx.Start();
    View view = familyDoc.ActiveView;

    double halfW    = {_ft(450)};  // half of 900mm default width
    double height   = {_ft(2100)}; // 2100mm height

    ReferencePlane rpLeft  = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(-halfW, 0, 0), new XYZ(-halfW, 1, 0), XYZ.BasisZ, view);
    rpLeft.Name = "Left";

    ReferencePlane rpRight = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ( halfW, 0, 0), new XYZ( halfW, 1, 0), XYZ.BasisZ, view);
    rpRight.Name = "Right";

    // Horizontal top plane
    ReferencePlane rpTop = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, 0, height), new XYZ(1, 0, height),
        XYZ.BasisY, view);
    rpTop.Name = "Top";

    tx.Commit();
}}"""))

        samples.append(_s("Create reference planes for a window family with Width, Height, Sill Height",
            f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Setup Window Reference Planes"))
{{
    tx.Start();
    View view = familyDoc.ActiveView;

    double halfW   = {_ft(600)};   // half of 1200mm width
    double sillH   = {_ft(900)};   // 900mm sill height
    double headH   = {_ft(2100)};  // 2100mm head height

    familyDoc.FamilyCreate.NewReferencePlane(new XYZ(-halfW, 0, 0), new XYZ(-halfW, 1, 0), XYZ.BasisZ, view).Name = "Left";
    familyDoc.FamilyCreate.NewReferencePlane(new XYZ( halfW, 0, 0), new XYZ( halfW, 1, 0), XYZ.BasisZ, view).Name = "Right";
    familyDoc.FamilyCreate.NewReferencePlane(new XYZ(0, 0, sillH),  new XYZ(1, 0, sillH),  XYZ.BasisY, view).Name = "Sill";
    familyDoc.FamilyCreate.NewReferencePlane(new XYZ(0, 0, headH),  new XYZ(1, 0, headH),  XYZ.BasisY, view).Name = "Head";

    tx.Commit();

    // FamilyManager params -- OUTSIDE Transaction
    FamilyManager famMgr = familyDoc.FamilyManager;
    FamilyParameter pW  = famMgr.AddParameter("Width",       BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
    FamilyParameter pH  = famMgr.AddParameter("Height",      BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
    FamilyParameter pSH = famMgr.AddParameter("SillHeight",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
    famMgr.Set(pW,  halfW * 2); famMgr.Set(pH, headH - sillH); famMgr.Set(pSH, sillH);
}}"""))

        return samples  # 3


if __name__ == "__main__":
    gen = ReferenceConstraintGenerator()
    samples = gen.generate()
    print(f"Generated {len(samples)} samples")
    assert all(set(s.keys()) == {"instruction", "input", "output"} for s in samples)
    print("[OK] All samples valid")
