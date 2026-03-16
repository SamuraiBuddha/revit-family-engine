"""Training data generator: Revit family geometry (extrusions, revolutions, blends, sweeps).

Produces ~300+ Alpaca-format training pairs covering solid and void forms,
formula-driven parameters, and common family geometry patterns.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

SAMPLE = Dict[str, Any]
MM_TO_FT = 1.0 / 304.8


def _s(instruction: str, output: str) -> SAMPLE:
    return {"instruction": instruction, "input": "", "output": output}


def _ft(mm: float) -> str:
    return f"{mm * MM_TO_FT:.6f}"


class FamilyGeometryGenerator:
    """Generates training samples for Revit family geometry creation."""

    def generate(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []
        samples += self._extrusions()
        samples += self._void_extrusions()
        samples += self._revolutions()
        samples += self._blends()
        samples += self._sweeps()
        samples += self._formula_driven()
        samples += self._material_assignment()
        samples += self._visibility()
        samples += self._nested_families()
        return samples

    # ------------------------------------------------------------------
    # Solid extrusions
    # ------------------------------------------------------------------

    def _extrusions(self) -> List[SAMPLE]:
        samples = []
        cases = [
            (300, 300, 600, "Create a simple rectangular solid extrusion 300x300mm, 600mm tall"),
            (150, 75, 300, "Create a thin rectangular solid 150x75mm, 300mm tall"),
            (500, 500, 1000, "Create a large square solid 500x500mm, 1000mm tall"),
            (200, 400, 2400, "Create a wall-stud profile 200x400mm, 2400mm tall"),
            (1200, 300, 200, "Create a flat slab extrusion 1200x300mm, 200mm thick"),
        ]
        for w, d, h, instruction in cases:
            w_ft, d_ft, h_ft = w * MM_TO_FT, d * MM_TO_FT, h * MM_TO_FT
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;

// Solid extrusion: {w} x {d} mm profile, {h} mm depth
// Revit internal units: feet (1 ft = 304.8 mm)
using (Transaction tx = new Transaction(familyDoc, "Create Extrusion"))
{{
    tx.Start();

    double w = {w_ft:.6f}; // {w} mm
    double d = {d_ft:.6f}; // {d} mm
    double h = {h_ft:.6f}; // {h} mm

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-w/2, -d/2, 0), new XYZ( w/2, -d/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, -d/2, 0), new XYZ( w/2,  d/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2,  d/2, 0), new XYZ(-w/2,  d/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-w/2,  d/2, 0), new XYZ(-w/2, -d/2, 0)));
    profile.Append(loop);

    SketchPlane sketchPlane = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    Extrusion extrusion = familyDoc.FamilyCreate.NewExtrusion(
        true, profile, sketchPlane, h);

    tx.Commit();
}}"""))

        # Centered vs offset cases
        for (name, z_start, z_end, desc) in [
            ("symmetric", -0.5, 0.5, "symmetric about level"),
            ("downward", -1.0, 0.0, "downward from level"),
        ]:
            w_ft = 400 * MM_TO_FT
            d_ft = 400 * MM_TO_FT
            samples.append(_s(
                f"Create a 400x400mm square extrusion {desc}",
                f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create {name.capitalize()} Extrusion"))
{{
    tx.Start();

    double w = {w_ft:.6f}; // 400 mm
    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-w/2, -w/2, 0), new XYZ( w/2, -w/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, -w/2, 0), new XYZ( w/2,  w/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2,  w/2, 0), new XYZ(-w/2,  w/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-w/2,  w/2, 0), new XYZ(-w/2, -w/2, 0)));
    profile.Append(loop);

    SketchPlane sketchPlane = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    Extrusion extrusion = familyDoc.FamilyCreate.NewExtrusion(
        true, profile, sketchPlane, {z_end:.1f}); // end = {z_end} ft
    extrusion.StartOffset = {z_start:.1f}; // start = {z_start} ft

    tx.Commit();
}}""",
            ))

        # L-section extrusion
        samples.append(_s(
            "Create an L-shaped extrusion 300x300mm outer, 200x200mm cutout, 600mm deep",
            f"""\
using Autodesk.Revit.DB;

// L-section: 300x300 outer minus 200x200 inner cutout
using (Transaction tx = new Transaction(familyDoc, "Create L-Section"))
{{
    tx.Start();

    double outer = {300 * MM_TO_FT:.6f}; // 300 mm
    double cut   = {200 * MM_TO_FT:.6f}; // 200 mm
    double depth = {600 * MM_TO_FT:.6f}; // 600 mm

    // Outer rectangle
    CurveArray outer_loop = new CurveArray();
    outer_loop.Append(Line.CreateBound(new XYZ(0, 0, 0),     new XYZ(outer, 0, 0)));
    outer_loop.Append(Line.CreateBound(new XYZ(outer, 0, 0), new XYZ(outer, outer, 0)));
    outer_loop.Append(Line.CreateBound(new XYZ(outer, outer, 0), new XYZ(0, outer, 0)));
    outer_loop.Append(Line.CreateBound(new XYZ(0, outer, 0), new XYZ(0, 0, 0)));

    // Inner cutout (top-right)
    double o2 = outer - cut;
    CurveArray inner_loop = new CurveArray();
    inner_loop.Append(Line.CreateBound(new XYZ(o2, o2, 0),    new XYZ(outer, o2, 0)));
    inner_loop.Append(Line.CreateBound(new XYZ(outer, o2, 0), new XYZ(outer, outer, 0)));
    inner_loop.Append(Line.CreateBound(new XYZ(outer, outer, 0), new XYZ(o2, outer, 0)));
    inner_loop.Append(Line.CreateBound(new XYZ(o2, outer, 0), new XYZ(o2, o2, 0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(outer_loop);
    profile.Append(inner_loop); // hole in profile

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    Extrusion extrusion = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, depth);

    tx.Commit();
}}""",
        ))

        # Circular extrusion
        for (r, h, desc) in [(150, 500, "pipe stub 150mm radius"), (50, 100, "small cylinder 50mm radius")]:
            r_ft = r * MM_TO_FT
            h_ft = h * MM_TO_FT
            segments = 32
            samples.append(_s(
                f"Create a circular solid extrusion ({desc}, {h}mm tall)",
                f"""\
using Autodesk.Revit.DB;
using System;

// Circular extrusion via {segments}-segment polygon approximation
using (Transaction tx = new Transaction(familyDoc, "Create Circular Extrusion"))
{{
    tx.Start();

    double r = {r_ft:.6f}; // {r} mm
    int n = {segments};
    CurveArray loop = new CurveArray();
    for (int i = 0; i < n; i++)
    {{
        double a0 = 2 * Math.PI * i / n;
        double a1 = 2 * Math.PI * (i + 1) / n;
        XYZ p0 = new XYZ(r * Math.Cos(a0), r * Math.Sin(a0), 0);
        XYZ p1 = new XYZ(r * Math.Cos(a1), r * Math.Sin(a1), 0);
        loop.Append(Line.CreateBound(p0, p1));
    }}

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    Extrusion extrusion = familyDoc.FamilyCreate.NewExtrusion(
        true, profile, sp, {h_ft:.6f}); // {h} mm

    tx.Commit();
}}""",
            ))

        return samples

    # ------------------------------------------------------------------
    # Void extrusions
    # ------------------------------------------------------------------

    def _void_extrusions(self) -> List[SAMPLE]:
        samples = []
        cases = [
            (100, 100, 400, "rectangular void cut-through"),
            (50, 50, 200, "small square void pocket"),
            (300, 200, 150, "large slot void"),
        ]
        for w, d, h, desc in cases:
            w_ft, d_ft, h_ft = w * MM_TO_FT, d * MM_TO_FT, h * MM_TO_FT
            samples.append(_s(
                f"Create a void extrusion for {desc} ({w}x{d}mm, {h}mm deep)",
                f"""\
using Autodesk.Revit.DB;

// Void extrusion: isSolid=false cuts into existing geometry
using (Transaction tx = new Transaction(familyDoc, "Create Void Extrusion"))
{{
    tx.Start();

    double w = {w_ft:.6f}; // {w} mm
    double d = {d_ft:.6f}; // {d} mm
    double h = {h_ft:.6f}; // {h} mm

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-w/2, -d/2, 0), new XYZ( w/2, -d/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, -d/2, 0), new XYZ( w/2,  d/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2,  d/2, 0), new XYZ(-w/2,  d/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-w/2,  d/2, 0), new XYZ(-w/2, -d/2, 0)));
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // isSolid = false --> void
    Extrusion voidExtrusion = familyDoc.FamilyCreate.NewExtrusion(
        false, profile, sp, h);

    tx.Commit();
}}""",
            ))
        return samples

    # ------------------------------------------------------------------
    # Revolutions
    # ------------------------------------------------------------------

    def _revolutions(self) -> List[SAMPLE]:
        samples = []
        cases = [
            (200, 50, 360, "full revolution -- circular column 200mm outer, 50mm wall"),
            (150, 0, 270, "270-degree partial revolution"),
            (100, 0, 180, "half-revolution arc"),
        ]
        for outer, wall, angle_deg, desc in cases:
            outer_ft = outer * MM_TO_FT
            wall_ft = wall * MM_TO_FT
            inner_ft = (outer - wall * 2) * MM_TO_FT if wall > 0 else 0
            angle_rad = math.radians(angle_deg)
            samples.append(_s(
                f"Create a revolution: {desc}",
                f"""\
using Autodesk.Revit.DB;
using System;

// Revolution: {desc}
using (Transaction tx = new Transaction(familyDoc, "Create Revolution"))
{{
    tx.Start();

    // Profile in the YZ plane (X=0 is the axis)
    double outer = {outer_ft:.6f}; // {outer} mm
    {"double inner = " + f"{inner_ft:.6f}; // {outer - wall * 2} mm (hollow)" if wall > 0 else "// solid"}

    CurveArray loop = new CurveArray();
    {"// Hollow tube profile" if wall > 0 else "// Solid disc profile"}
    loop.Append(Line.CreateBound(new XYZ(0,      0, 0),     new XYZ(0, outer, 0)));
    loop.Append(Line.CreateBound(new XYZ(0, outer,  0),     new XYZ(0, outer, outer)));
    {"loop.Append(Line.CreateBound(new XYZ(0, outer, outer), new XYZ(0, inner, outer)));" if wall > 0 else "loop.Append(Line.CreateBound(new XYZ(0, outer, outer), new XYZ(0, 0, outer)));"}
    {"loop.Append(Line.CreateBound(new XYZ(0, inner, outer), new XYZ(0, inner, 0)));" if wall > 0 else "loop.Append(Line.CreateBound(new XYZ(0, 0, outer), new XYZ(0, 0, 0)));"}
    {"loop.Append(Line.CreateBound(new XYZ(0, inner, 0), new XYZ(0, 0, 0)));" if wall > 0 else ""}

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero));

    // Axis of revolution: Z-axis
    Line axis = Line.CreateBound(XYZ.Zero, XYZ.BasisZ);

    Revolution revolution = familyDoc.FamilyCreate.NewRevolution(
        true, profile, sp, axis,
        0.0,           // start angle (radians)
        {angle_rad:.6f}); // end angle ({angle_deg} degrees)

    tx.Commit();
}}""",
            ))
        return samples

    # ------------------------------------------------------------------
    # Blends
    # ------------------------------------------------------------------

    def _blends(self) -> List[SAMPLE]:
        samples = []
        cases = [
            (400, 400, 200, 200, 600, "taper square 400 to 200mm over 600mm"),
            (300, 150, 600, 300, 900, "loft rectangle bottom to top"),
        ]
        for bw, bd, tw, td, h, desc in cases:
            bw_ft = bw * MM_TO_FT
            bd_ft = bd * MM_TO_FT
            tw_ft = tw * MM_TO_FT
            td_ft = td * MM_TO_FT
            h_ft = h * MM_TO_FT
            samples.append(_s(
                f"Create a blend (loft): {desc}",
                f"""\
using Autodesk.Revit.DB;

// Blend: bottom {bw}x{bd}mm, top {tw}x{td}mm, height {h}mm
using (Transaction tx = new Transaction(familyDoc, "Create Blend"))
{{
    tx.Start();

    double bw = {bw_ft:.6f}; // bottom width {bw} mm
    double bd = {bd_ft:.6f}; // bottom depth {bd} mm
    double tw = {tw_ft:.6f}; // top width {tw} mm
    double td = {td_ft:.6f}; // top depth {td} mm
    double h  = {h_ft:.6f};  // height {h} mm

    // Bottom profile (at z=0)
    CurveArray bottomLoop = new CurveArray();
    bottomLoop.Append(Line.CreateBound(new XYZ(-bw/2, -bd/2, 0), new XYZ( bw/2, -bd/2, 0)));
    bottomLoop.Append(Line.CreateBound(new XYZ( bw/2, -bd/2, 0), new XYZ( bw/2,  bd/2, 0)));
    bottomLoop.Append(Line.CreateBound(new XYZ( bw/2,  bd/2, 0), new XYZ(-bw/2,  bd/2, 0)));
    bottomLoop.Append(Line.CreateBound(new XYZ(-bw/2,  bd/2, 0), new XYZ(-bw/2, -bd/2, 0)));

    // Top profile (at z=h)
    CurveArray topLoop = new CurveArray();
    topLoop.Append(Line.CreateBound(new XYZ(-tw/2, -td/2, h), new XYZ( tw/2, -td/2, h)));
    topLoop.Append(Line.CreateBound(new XYZ( tw/2, -td/2, h), new XYZ( tw/2,  td/2, h)));
    topLoop.Append(Line.CreateBound(new XYZ( tw/2,  td/2, h), new XYZ(-tw/2,  td/2, h)));
    topLoop.Append(Line.CreateBound(new XYZ(-tw/2,  td/2, h), new XYZ(-tw/2, -td/2, h)));

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    Blend blend = familyDoc.FamilyCreate.NewBlend(true, topLoop, bottomLoop, sp);

    tx.Commit();
}}""",
            ))
        return samples

    # ------------------------------------------------------------------
    # Sweeps
    # ------------------------------------------------------------------

    def _sweeps(self) -> List[SAMPLE]:
        return [
            _s(
                "Create a sweep of a rectangular profile along a straight path, 50x100mm cross-section, 2000mm path",
                f"""\
using Autodesk.Revit.DB;

// Sweep: 50x100mm profile swept along 2000mm straight path
using (Transaction tx = new Transaction(familyDoc, "Create Sweep"))
{{
    tx.Start();

    // Sweep path: 2000mm line along X
    double pathLen = {2000 * MM_TO_FT:.6f}; // 2000 mm
    CurveArray pathCurve = new CurveArray();
    pathCurve.Append(Line.CreateBound(XYZ.Zero, new XYZ(pathLen, 0, 0)));

    ReferenceArrayArray path = new ReferenceArrayArray();
    // For model lines, reference them directly; in family editor use sketch
    SketchPlane pathPlane = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    ModelCurveArray pathLines = familyDoc.FamilyCreate.NewModelCurveArray(pathCurve, pathPlane);

    ReferenceArray pathRefs = new ReferenceArray();
    foreach (ModelCurve mc in pathLines) pathRefs.Append(mc.GeometryCurve.Reference);
    path.Append(pathRefs);

    // Profile: 50x100mm rectangle in YZ plane at origin
    double pw = {50 * MM_TO_FT:.6f};  // 50 mm
    double ph = {100 * MM_TO_FT:.6f}; // 100 mm
    CurveArray profileLoop = new CurveArray();
    profileLoop.Append(Line.CreateBound(new XYZ(0, -pw/2, 0),   new XYZ(0,  pw/2, 0)));
    profileLoop.Append(Line.CreateBound(new XYZ(0,  pw/2, 0),   new XYZ(0,  pw/2, ph)));
    profileLoop.Append(Line.CreateBound(new XYZ(0,  pw/2, ph),  new XYZ(0, -pw/2, ph)));
    profileLoop.Append(Line.CreateBound(new XYZ(0, -pw/2, ph),  new XYZ(0, -pw/2, 0)));

    SweepProfile sweepProfile = new SweepProfile(profileLoop);

    Sweep sweep = familyDoc.FamilyCreate.NewSweep(
        true, path, sweepProfile, 0, ProfilePlaneLocation.Start);

    tx.Commit();
}}""",
            )
        ]

    # ------------------------------------------------------------------
    # Formula-driven geometry
    # ------------------------------------------------------------------

    def _formula_driven(self) -> List[SAMPLE]:
        return [
            _s(
                "Create a parametric extrusion where Width, Depth, and Height are controlled by family parameters with formulas",
                """\
using Autodesk.Revit.DB;

// Step 1: Define family parameters (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth  = famMgr.AddParameter("Width",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pDepth  = famMgr.AddParameter("Depth",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pHeight = famMgr.AddParameter("Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

// Set default values (feet: 300mm = 0.984252ft)
famMgr.Set(pWidth,  0.984252);
famMgr.Set(pDepth,  0.984252);
famMgr.Set(pHeight, 1.968504); // 600mm

// Add formula: Height = Width * 2
famMgr.SetFormula(pHeight, "Width * 2");

// Step 2: Create geometry driven by reference planes (inside Transaction)
using (Transaction tx = new Transaction(familyDoc, "Create Parametric Extrusion"))
{
    tx.Start();

    // Reference planes at +/- Width/2 and +/- Depth/2
    View activeView = familyDoc.ActiveView;
    ReferencePlane rpLeft  = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(-1, 0, 0), new XYZ(-1, 1, 0), XYZ.BasisZ, activeView);
    ReferencePlane rpRight = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ( 1, 0, 0), new XYZ( 1, 1, 0), XYZ.BasisZ, activeView);
    rpLeft.Name  = "Width_Left";
    rpRight.Name = "Width_Right";

    // Profile using current parameter values
    double w = 0.984252; // will flex with parameter
    double d = 0.984252;
    double h = 1.968504;

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-w/2, -d/2, 0), new XYZ( w/2, -d/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, -d/2, 0), new XYZ( w/2,  d/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2,  d/2, 0), new XYZ(-w/2,  d/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-w/2,  d/2, 0), new XYZ(-w/2, -d/2, 0)));
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    Extrusion ext = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    // Create dimension and label it with the Height parameter
    ReferenceArray refs = new ReferenceArray();
    refs.Append(ext.get_Geometry(new Options()).GetEnumerator().Current
        .GetBoundingBox(activeView)?.Min.GetType() != null
        ? rpLeft.GetReference()
        : rpLeft.GetReference());
    refs.Append(rpRight.GetReference());

    Dimension widthDim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView,
        Line.CreateBound(new XYZ(-2, 0, 0), new XYZ(2, 0, 0)),
        refs);
    if (widthDim != null && widthDim.IsReferencesValidForLabel())
        widthDim.FamilyLabel = pWidth;

    tx.Commit();
}""",
            )
        ]

    # ------------------------------------------------------------------
    # Material assignment
    # ------------------------------------------------------------------

    def _material_assignment(self) -> List[SAMPLE]:
        samples = []
        materials = ["Concrete", "Steel", "Wood", "Glass", "Aluminum"]
        for mat in materials:
            samples.append(_s(
                f"Assign '{mat}' material to a family extrusion via a material parameter",
                f"""\
using Autodesk.Revit.DB;
using System.Linq;

// Assign material parameter and apply to extrusion
// Step 1: Add material parameter (outside Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter matParam = famMgr.AddParameter(
    "Body Material",
    BuiltInParameterGroup.PG_MATERIALS,
    ParameterType.Material,
    true); // instance parameter

// Step 2: Find material by name and assign
using (Transaction tx = new Transaction(familyDoc, "Assign Material"))
{{
    tx.Start();

    Material mat = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Material))
        .Cast<Material>()
        .FirstOrDefault(m => m.Name.Contains("{mat}"));

    if (mat != null)
    {{
        famMgr.Set(matParam, mat.Id);
    }}
    else
    {{
        // Create material if not found
        ElementId newMatId = Material.Create(familyDoc, "{mat}");
        famMgr.Set(matParam, newMatId);
    }}

    tx.Commit();
}}""",
            ))
        return samples

    # ------------------------------------------------------------------
    # Visibility parameters
    # ------------------------------------------------------------------

    def _visibility(self) -> List[SAMPLE]:
        return [
            _s(
                "Create a visibility parameter to show/hide a detail level component in the family",
                """\
using Autodesk.Revit.DB;

// Visibility parameter: controls element visibility by detail level
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter visParam = famMgr.AddParameter(
    "Show Detail",
    BuiltInParameterGroup.PG_VISIBILITY,
    ParameterType.YesNo,
    true); // instance

famMgr.Set(visParam, 1); // default visible

// Apply visibility to a specific element after creating it
using (Transaction tx = new Transaction(familyDoc, "Set Visibility"))
{
    tx.Start();

    // Assuming 'detailExtrusion' is a previously created element
    // Get its parameter and set formula-driven visibility
    // famParam = detailExtrusion.get_Parameter(BuiltInParameter.IS_VISIBLE_PARAM);

    // Use FamilyElementVisibility for detail level control
    FamilyElementVisibility vis = new FamilyElementVisibility(
        FamilyElementVisibilityType.Model);
    vis.IsShownInCoarse  = false;
    vis.IsShownInMedium  = false;
    vis.IsShownInFine    = true;
    // detailExtrusion.SetVisibility(vis);

    tx.Commit();
}""",
            )
        ]

    # ------------------------------------------------------------------
    # Nested families
    # ------------------------------------------------------------------

    def _nested_families(self) -> List[SAMPLE]:
        return [
            _s(
                "Load and place a nested family into the current family document",
                """\
using Autodesk.Revit.DB;
using System.IO;

// Load nested family and place an instance
using (Transaction tx = new Transaction(familyDoc, "Load Nested Family"))
{
    tx.Start();

    string nestedFamilyPath = @"C:\\ProgramData\\Autodesk\\RVT 2026\\Libraries\\US Imperial\\Structural\\Framing\\Steel\\W-Wide Flange.rfa";

    Family nestedFamily;
    bool loaded = familyDoc.LoadFamily(nestedFamilyPath, out nestedFamily);

    if (!loaded)
    {
        // Family may already be loaded
        nestedFamily = new FilteredElementCollector(familyDoc)
            .OfClass(typeof(Family))
            .Cast<Family>()
            .FirstOrDefault(f => f.Name == "W-Wide Flange");
    }

    if (nestedFamily != null)
    {
        FamilySymbol symbol = familyDoc.GetElement(
            nestedFamily.GetFamilySymbolIds().First()) as FamilySymbol;

        if (!symbol.IsActive)
            symbol.Activate();

        // Place at origin with identity transform
        FamilyInstance instance = familyDoc.FamilyCreate.NewFamilyInstance(
            XYZ.Zero, symbol, familyDoc.ActiveView);
    }

    tx.Commit();
}""",
            )
        ]
