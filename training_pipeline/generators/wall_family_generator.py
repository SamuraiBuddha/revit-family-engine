"""Training data generator: wall-hosted Revit family patterns.

Produces ~200 Alpaca-format training pairs covering face-based/wall-hosted
templates, void openings, electrical boxes, plumbing penetrations, wall-mounted
fixtures, curtain wall panels, reveal profiles, embedded structural elements,
and 2D symbolic line representation.
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


class WallFamilyGenerator:
    """Generates training samples for wall-hosted Revit family patterns."""

    def generate(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []
        samples += self._wall_hosted_basic()
        samples += self._wall_opening_cuts()
        samples += self._wall_hosted_electrical()
        samples += self._wall_hosted_plumbing()
        samples += self._wall_mounted_fixtures()
        samples += self._wall_panel_patterns()
        samples += self._wall_reveal_profiles()
        samples += self._wall_embedded_elements()
        samples += self._symbolic_lines()
        return samples

    # ------------------------------------------------------------------
    # Wall-hosted basic templates
    # ------------------------------------------------------------------

    def _wall_hosted_basic(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        # Face-based family template setup
        samples.append(_s(
            "Set up a face-based (wall-hosted) family template with the correct work plane",
            f"""\
using Autodesk.Revit.DB;

// Face-based families use a generic model face-based template.
// The hosting face defines the work plane; geometry projects from it.
// Key: set the family's hosting requirement to wall face.

// This code runs at family document load / setup time (no Transaction needed
// for document property changes in the family editor).
FamilyManager famMgr = familyDoc.FamilyManager;

// Confirm the template supports face-based hosting
// (check via familyDoc.FamilyPlacementType)
FamilyPlacementType placementType = familyDoc.FamilyPlacementType;
// Expected: FamilyPlacementType.OneLevelBasedHosted or WorkPlaneBased

// Add a standard Depth parameter to control projection from wall face
using (Transaction tx = new Transaction(familyDoc, "Setup Face-Based Parameters"))
{{
    tx.Start();

    // Reference plane parallel to the hosting face (at projection depth)
    View activeView = familyDoc.ActiveView;
    ReferencePlane frontPlane = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, {_ft(100)}, 0),  // 100 mm from face
        new XYZ(1, {_ft(100)}, 0),
        XYZ.BasisZ,
        activeView);
    frontPlane.Name = "Front";

    tx.Commit();
}}

// Add Depth parameter (outside Transaction)
FamilyParameter depthParam = famMgr.AddParameter(
    "Depth",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length,
    false);
famMgr.Set(depthParam, {_ft(100)}); // default 100 mm""",
        ))

        # Work-plane-based wall family
        samples.append(_s(
            "Create a work-plane-based family that can be placed on a wall face",
            f"""\
using Autodesk.Revit.DB;

// Work-plane-based families attach to any named reference plane or face.
// Set the family category and confirm placement type.

// Verify placement type is WorkPlaneBased
// (set in the family template; cannot be changed via API after creation)

FamilyManager famMgr = familyDoc.FamilyManager;

// Standard geometry parameters
FamilyParameter pWidth = famMgr.AddParameter(
    "Width", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pHeight = famMgr.AddParameter(
    "Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pDepth = famMgr.AddParameter(
    "Depth", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pWidth,  {_ft(300)});  // 300 mm
famMgr.Set(pHeight, {_ft(200)});  // 200 mm
famMgr.Set(pDepth,  {_ft(50)});   // 50 mm

using (Transaction tx = new Transaction(familyDoc, "Create Wall Plate Geometry"))
{{
    tx.Start();

    double w = {_ft(300)};
    double h = {_ft(200)};
    double d = {_ft(50)};

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-w/2, 0,    0), new XYZ( w/2, 0,    0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, 0,    0), new XYZ( w/2, 0,    h)));
    loop.Append(Line.CreateBound(new XYZ( w/2, 0,    h), new XYZ(-w/2, 0,    h)));
    loop.Append(Line.CreateBound(new XYZ(-w/2, 0,    h), new XYZ(-w/2, 0,    0)));
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    Extrusion ext = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, d);

    tx.Commit();
}}""",
        ))

        # Hosted family with shared hosting parameters
        samples.append(_s(
            "Add standard wall-hosted family parameters: Width, Height, Elevation from Host",
            f"""\
using Autodesk.Revit.DB;

// Standard parameter set for wall-hosted families
FamilyManager famMgr = familyDoc.FamilyManager;

// Geometry parameters
FamilyParameter pWidth = famMgr.AddParameter(
    "Width",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pHeight = famMgr.AddParameter(
    "Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pElevation = famMgr.AddParameter(
    "Elevation from Host",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, true); // instance

famMgr.Set(pWidth,     {_ft(600)});  // 600 mm
famMgr.Set(pHeight,    {_ft(400)});  // 400 mm
famMgr.Set(pElevation, {_ft(900)});  // 900 mm AFF (above finish floor)

// Keep geometry parameters as type (false) for standard sizes
// Make elevation instance (true) so placement height varies per instance""",
        ))

        # Face-based extrusion projecting from wall
        cases = [
            (200, 150, 80,  "wall bracket 200x150mm, 80mm projection"),
            (400, 300, 120, "wall panel 400x300mm, 120mm projection"),
            (100, 100, 60,  "wall box 100x100mm, 60mm projection"),
        ]
        for w, h, proj, desc in cases:
            samples.append(_s(
                f"Create a face-based solid extrusion projecting from wall face: {desc}",
                f"""\
using Autodesk.Revit.DB;

// Face-based extrusion: profile lies in wall face plane (XZ plane at Y=0),
// extrusion extends in +Y (away from wall).
using (Transaction tx = new Transaction(familyDoc, "Create Wall-Face Extrusion"))
{{
    tx.Start();

    double w    = {_ft(w)};     // {w} mm width
    double h    = {_ft(h)};     // {h} mm height
    double proj = {_ft(proj)};  // {proj} mm projection from wall face

    // Profile in the wall face plane (normal = Y axis)
    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-w/2, 0, 0),    new XYZ( w/2, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, 0, 0),    new XYZ( w/2, 0, h)));
    loop.Append(Line.CreateBound(new XYZ( w/2, 0, h),    new XYZ(-w/2, 0, h)));
    loop.Append(Line.CreateBound(new XYZ(-w/2, 0, h),    new XYZ(-w/2, 0, 0)));
    profile.Append(loop);

    // Sketch plane: wall face (normal = BasisY)
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    // Extrude in +Y direction (away from wall)
    Extrusion ext = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, proj);

    tx.Commit();
}}""",
            ))

        # Flip control reference planes for wall-hosted families
        samples.append(_s(
            "Add flip controls to a wall-hosted family using reference planes named 'Front' and 'Back'",
            f"""\
using Autodesk.Revit.DB;

// Flip controls require two reference planes on opposite sides.
// Named 'Front' and 'Back' (or 'Left'/'Right') -- Revit recognises these
// names to generate the flip arrows in the host.
using (Transaction tx = new Transaction(familyDoc, "Add Flip Reference Planes"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;

    // Front plane: at Y=0 (wall face)
    ReferencePlane front = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, 0, 0), new XYZ(1, 0, 0), XYZ.BasisZ, activeView);
    front.Name = "Front";

    // Back plane: at Y = projection depth
    double depth = {_ft(100)};  // 100 mm
    ReferencePlane back = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, depth, 0), new XYZ(1, depth, 0), XYZ.BasisZ, activeView);
    back.Name = "Back";

    // Center (Left/Right) for horizontal flip
    ReferencePlane centerLR = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, 0, 0), new XYZ(0, 1, 0), XYZ.BasisZ, activeView);
    centerLR.Name = "Center (Left/Right)";

    tx.Commit();
}}""",
        ))

        # Hosted family with connector origin at wall face
        samples.append(_s(
            "Set the insertion point of a wall-hosted family at the wall face center",
            f"""\
using Autodesk.Revit.DB;

// The insertion point for a wall-hosted family is defined by where the
// family origin (0,0,0) sits relative to the hosting face.
// Convention: origin at the center of the face footprint, Y=0 on the wall face.

using (Transaction tx = new Transaction(familyDoc, "Set Insertion Origin"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;

    // Origin reference planes (all pass through 0,0,0)
    ReferencePlane refX = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, -1, 0), new XYZ(0, 1, 0), XYZ.BasisZ, activeView);
    refX.Name = "Center (Front/Back)";

    ReferencePlane refZ = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(-1, 0, 0), new XYZ(1, 0, 0), XYZ.BasisZ, activeView);
    refZ.Name = "Center (Left/Right)";

    // The origin point (0,0,0) is the insertion point Revit uses
    // when snapping to the wall face during placement.

    tx.Commit();
}}""",
        ))

        # Multiple face-based sizes
        for (label, w, h, proj) in [
            ("small",  150, 100,  40),
            ("medium", 300, 200,  80),
            ("large",  600, 400, 120),
        ]:
            samples.append(_s(
                f"Create {label} wall-hosted plate ({w}x{h}mm, {proj}mm deep) as a family type",
                f"""\
using Autodesk.Revit.DB;

// Add a '{label.capitalize()}' type to the wall-hosted family
FamilyManager famMgr = familyDoc.FamilyManager;

// Parameters must already exist; just set values for the new type.
FamilyType newType = famMgr.NewType("{label.capitalize()}");
famMgr.CurrentType = newType;

// Set dimensions for this type (all in feet)
FamilyParameter pW = famMgr.get_Parameter("Width");
FamilyParameter pH = famMgr.get_Parameter("Height");
FamilyParameter pD = famMgr.get_Parameter("Depth");

if (pW != null) famMgr.Set(pW, {_ft(w)});   // {w} mm
if (pH != null) famMgr.Set(pH, {_ft(h)});   // {h} mm
if (pD != null) famMgr.Set(pD, {_ft(proj)}); // {proj} mm""",
            ))

        # Subcategory for wall families
        samples.append(_s(
            "Create a subcategory 'Body' under the Specialty Equipment category for a wall-hosted family",
            """\
using Autodesk.Revit.DB;

// Subcategories organise geometry visibility and appearance.
// Create under the family's own category (e.g., Specialty Equipment).
using (Transaction tx = new Transaction(familyDoc, "Create Subcategory"))
{
    tx.Start();

    Category parentCat = familyDoc.Settings.Categories
        .get_Item(BuiltInCategory.OST_SpecialityEquipment);

    Category bodySubCat = familyDoc.Settings.Categories.NewSubcategory(
        parentCat, "Body");
    bodySubCat.LineColor  = new Color(0, 0, 0);      // black
    bodySubCat.LineWeight = 2;                         // medium weight

    Category symbolSubCat = familyDoc.Settings.Categories.NewSubcategory(
        parentCat, "Symbol");
    symbolSubCat.LineColor  = new Color(128, 128, 128); // grey
    symbolSubCat.LineWeight = 1;

    tx.Commit();
}""",
        ))

        # Shared parameter for wall families
        samples.append(_s(
            "Add a shared parameter 'Manufacturer' to a wall-hosted family for schedule reporting",
            """\
using Autodesk.Revit.DB;
using System.IO;

// Shared parameters enable cross-family scheduling.
// They must be defined in a shared parameter file first.
string sharedParamFile = @"C:\\RevitSharedParams\\WallFamily.txt";

// Set the shared parameter file on the application
familyDoc.Application.SharedParametersFilename = sharedParamFile;
DefinitionFile defFile = familyDoc.Application.OpenSharedParameterFile();

// Get or create the group
DefinitionGroup group = defFile.Groups.get_Item("Identity Data")
    ?? defFile.Groups.Create("Identity Data");

// Get or create the definition
ExternalDefinition def = group.Definitions.get_Item("Manufacturer")
    as ExternalDefinition;
if (def == null)
{
    ExternalDefinitionCreationOptions opts =
        new ExternalDefinitionCreationOptions("Manufacturer", ParameterType.Text);
    def = group.Definitions.Create(opts) as ExternalDefinition;
}

// Bind to the family
FamilyManager famMgr = familyDoc.FamilyManager;
famMgr.AddParameter(def,
    BuiltInParameterGroup.PG_IDENTITY_DATA,
    true); // instance parameter""",
        ))

        # Elevation-driven placement
        samples.append(_s(
            "Set a wall-hosted family instance's elevation offset from the host wall's base",
            f"""\
using Autodesk.Revit.DB;

// After placing a wall-hosted family instance, set its elevation offset.
// The 'Elevation from Host' parameter controls height on the wall.
using (Transaction tx = new Transaction(doc, "Set Hosted Family Elevation"))
{{
    tx.Start();

    // Assume 'instance' is a placed FamilyInstance hosted on a wall
    FamilyInstance instance = /* ... */ null;

    Parameter elevParam = instance?.get_Parameter(
        BuiltInParameter.INSTANCE_ELEVATION_PARAM);

    if (elevParam != null && !elevParam.IsReadOnly)
    {{
        elevParam.Set({_ft(1200)});  // 1200 mm AFF
    }}

    tx.Commit();
}}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # Wall opening cuts (void extrusions)
    # ------------------------------------------------------------------

    def _wall_opening_cuts(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        # Rectangular opening
        rect_cases = [
            (900,  2100, "standard door opening 900x2100mm"),
            (600,  1200, "window opening 600x1200mm"),
            (300,   300, "small access panel 300x300mm"),
            (1200, 2400, "wide opening 1200x2400mm"),
            (100,   200, "cable pass-through 100x200mm"),
        ]
        for w, h, desc in rect_cases:
            samples.append(_s(
                f"Create a rectangular void cut through a wall for a {desc}",
                f"""\
using Autodesk.Revit.DB;

// Rectangular void extrusion cuts the host wall when the family is placed.
// Profile in XZ plane; extrusion depth must exceed wall thickness.
using (Transaction tx = new Transaction(familyDoc, "Create Rectangular Wall Opening"))
{{
    tx.Start();

    double w       = {_ft(w)};     // {w} mm width
    double h       = {_ft(h)};     // {h} mm height
    double cutDepth = {_ft(600)};  // 600 mm -- exceeds any typical wall thickness

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    // Profile in the wall face plane (normal = BasisY), centred at origin
    loop.Append(Line.CreateBound(new XYZ(-w/2, 0, 0),  new XYZ( w/2, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, 0, 0),  new XYZ( w/2, 0, h)));
    loop.Append(Line.CreateBound(new XYZ( w/2, 0, h),  new XYZ(-w/2, 0, h)));
    loop.Append(Line.CreateBound(new XYZ(-w/2, 0, h),  new XYZ(-w/2, 0, 0)));
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    // isSolid = false → void; extrude through wall in -Y and +Y
    Extrusion voidExt = familyDoc.FamilyCreate.NewExtrusion(
        false, profile, sp, cutDepth);
    voidExt.StartOffset = -{_ft(300)};  // 300 mm behind face
    voidExt.get_Parameter(BuiltInParameter.EXTRUSION_END_PARAM)?.Set(cutDepth);

    tx.Commit();
}}""",
            ))

        # Arched opening
        arch_cases = [
            (900,  2100, 450, "arched door opening 900 wide, 450mm radius arch"),
            (600,  1200, 300, "arched window opening 600 wide, 300mm radius arch"),
        ]
        for w, rect_h, r, desc in arch_cases:
            samples.append(_s(
                f"Create an arched void cut for a {desc}",
                f"""\
using Autodesk.Revit.DB;
using System;

// Arched opening: rectangular base + semicircular top
// Total height = rect_h (to spring line) + r (arch radius)
using (Transaction tx = new Transaction(familyDoc, "Create Arched Wall Opening"))
{{
    tx.Start();

    double w      = {_ft(w)};       // {w} mm width
    double rectH  = {_ft(rect_h)};  // {rect_h} mm to spring line
    double r      = {_ft(r)};       // {r} mm arch radius
    double depth  = {_ft(600)};     // cut depth through wall

    // Spring line Y coordinate (top of rectangular portion)
    double spring = rectH;
    // Arch centre at mid-width, at spring line height
    XYZ archCtr = new XYZ(0, 0, spring);

    CurveArray loop = new CurveArray();

    // Bottom horizontal
    loop.Append(Line.CreateBound(new XYZ(-w/2, 0, 0),     new XYZ( w/2, 0, 0)));
    // Right vertical (up to spring line)
    loop.Append(Line.CreateBound(new XYZ( w/2, 0, 0),     new XYZ( w/2, 0, spring)));
    // Semicircular arch (right to left, 32 segments)
    int n = 32;
    XYZ prev = new XYZ(w/2, 0, spring);
    for (int i = 1; i <= n; i++)
    {{
        double angle = Math.PI * i / n; // 0 → PI (right to left)
        XYZ next = new XYZ(r * Math.Cos(Math.PI - angle), 0, spring + r * Math.Sin(Math.PI - angle));
        // Simpler: go from 0 to PI
        double a0 = Math.PI - Math.PI * (i - 1) / n;
        double a1 = Math.PI - Math.PI * i / n;
        XYZ p0 = new XYZ(r * Math.Cos(a0), 0, spring + r * Math.Sin(a0));
        XYZ p1 = new XYZ(r * Math.Cos(a1), 0, spring + r * Math.Sin(a1));
        loop.Append(Line.CreateBound(p0, p1));
    }}
    // Left vertical (down from spring line)
    loop.Append(Line.CreateBound(new XYZ(-w/2, 0, spring), new XYZ(-w/2, 0, 0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    Extrusion voidExt = familyDoc.FamilyCreate.NewExtrusion(
        false, profile, sp, depth);

    tx.Commit();
}}""",
            ))

        # Circular opening
        circ_cases = [
            (150, "pipe sleeve 150mm diameter"),
            (300, "round porthole 300mm diameter"),
            (100, "cable knockout 100mm diameter"),
        ]
        for dia, desc in circ_cases:
            r = dia / 2
            samples.append(_s(
                f"Create a circular void cut through a wall for a {desc}",
                f"""\
using Autodesk.Revit.DB;
using System;

// Circular void: 32-segment polygon approximation
using (Transaction tx = new Transaction(familyDoc, "Create Circular Wall Opening"))
{{
    tx.Start();

    double r     = {_ft(r)};      // {r} mm radius ({dia} mm diameter)
    double depth = {_ft(600)};    // cut depth through wall
    int n = 32;

    CurveArray loop = new CurveArray();
    for (int i = 0; i < n; i++)
    {{
        double a0 = 2 * Math.PI * i / n;
        double a1 = 2 * Math.PI * (i + 1) / n;
        XYZ p0 = new XYZ(r * Math.Cos(a0), 0, r + r * Math.Sin(a0));
        XYZ p1 = new XYZ(r * Math.Cos(a1), 0, r + r * Math.Sin(a1));
        loop.Append(Line.CreateBound(p0, p1));
    }}

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    Extrusion voidExt = familyDoc.FamilyCreate.NewExtrusion(
        false, profile, sp, depth);

    tx.Commit();
}}""",
            ))

        # Parametric void with Width/Height parameters
        samples.append(_s(
            "Create a parametric rectangular wall opening void driven by Width and Height family parameters",
            f"""\
using Autodesk.Revit.DB;

// Parametric void: width and height are family type parameters.
// The void extrusion references dimensions labelled with these parameters.
FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter pW = famMgr.AddParameter(
    "Opening Width",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pH = famMgr.AddParameter(
    "Opening Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pW, {_ft(900)});   // default 900 mm
famMgr.Set(pH, {_ft(2100)});  // default 2100 mm

using (Transaction tx = new Transaction(familyDoc, "Create Parametric Void"))
{{
    tx.Start();

    double w = {_ft(900)};
    double h = {_ft(2100)};
    double d = {_ft(600)};

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-w/2, 0, 0), new XYZ( w/2, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, 0, 0), new XYZ( w/2, 0, h)));
    loop.Append(Line.CreateBound(new XYZ( w/2, 0, h), new XYZ(-w/2, 0, h)));
    loop.Append(Line.CreateBound(new XYZ(-w/2, 0, h), new XYZ(-w/2, 0, 0)));
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    Extrusion voidExt = familyDoc.FamilyCreate.NewExtrusion(false, profile, sp, d);

    // Create reference planes for dimension labels
    View v = familyDoc.ActiveView;
    ReferencePlane rpLeft  = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(-w/2, 0, 0), new XYZ(-w/2, 1, 0), XYZ.BasisZ, v);
    ReferencePlane rpRight = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ( w/2, 0, 0), new XYZ( w/2, 1, 0), XYZ.BasisZ, v);
    rpLeft.Name  = "Opening Left";
    rpRight.Name = "Opening Right";

    ReferenceArray widthRefs = new ReferenceArray();
    widthRefs.Append(rpLeft.GetReference());
    widthRefs.Append(rpRight.GetReference());
    Dimension widthDim = familyDoc.FamilyCreate.NewLinearDimension(
        v,
        Line.CreateBound(new XYZ(-1, 0, -0.5), new XYZ(1, 0, -0.5)),
        widthRefs);
    if (widthDim?.IsReferencesValidForLabel() == true)
        widthDim.FamilyLabel = pW;

    tx.Commit();
}}""",
        ))

        # Sill height offset for opening void
        samples.append(_s(
            "Create a wall opening void with a configurable sill height (bottom of opening raised from floor)",
            f"""\
using Autodesk.Revit.DB;

// Opening with sill height: the void bottom is at z = sillHeight, not z = 0.
FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter pSill = famMgr.AddParameter(
    "Sill Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pOpenH = famMgr.AddParameter(
    "Opening Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pOpenW = famMgr.AddParameter(
    "Opening Width",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pSill,  {_ft(900)});   // 900 mm sill height
famMgr.Set(pOpenH, {_ft(1200)});  // 1200 mm opening height
famMgr.Set(pOpenW, {_ft(600)});   // 600 mm opening width

using (Transaction tx = new Transaction(familyDoc, "Create Sill Void"))
{{
    tx.Start();

    double sill  = {_ft(900)};
    double openH = {_ft(1200)};
    double openW = {_ft(600)};
    double depth = {_ft(600)};

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    // Bottom of void at sill height
    loop.Append(Line.CreateBound(new XYZ(-openW/2, 0, sill),
                                  new XYZ( openW/2, 0, sill)));
    loop.Append(Line.CreateBound(new XYZ( openW/2, 0, sill),
                                  new XYZ( openW/2, 0, sill + openH)));
    loop.Append(Line.CreateBound(new XYZ( openW/2, 0, sill + openH),
                                  new XYZ(-openW/2, 0, sill + openH)));
    loop.Append(Line.CreateBound(new XYZ(-openW/2, 0, sill + openH),
                                  new XYZ(-openW/2, 0, sill)));
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    Extrusion voidExt = familyDoc.FamilyCreate.NewExtrusion(false, profile, sp, depth);

    tx.Commit();
}}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # Wall-hosted electrical boxes
    # ------------------------------------------------------------------

    def _wall_hosted_electrical(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        samples.append(_s(
            "Create a wall-hosted electrical outlet box family (single-gang, 115x70x55mm)",
            """\
using Autodesk.Revit.DB;

// Single-gang outlet box: 115mm wide, 70mm tall, 55mm deep in wall
FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter pElevation = famMgr.AddParameter(
    "Elevation from Host", BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length, true);
famMgr.Set(pElevation, 1.312336);  // 400 mm AFF

using (Transaction tx = new Transaction(familyDoc, "Create Outlet Box"))
{{
    tx.Start();

    double bw = 0.377297;  // 115 mm
    double bh = 0.229659;   // 70 mm
    double bd = 0.180446;   // 55 mm

    CurveArrArray boxProfile = new CurveArrArray();
    CurveArray boxLoop = new CurveArray();
    boxLoop.Append(Line.CreateBound(new XYZ(-bw/2, 0, 0),   new XYZ( bw/2, 0, 0)));
    boxLoop.Append(Line.CreateBound(new XYZ( bw/2, 0, 0),   new XYZ( bw/2, 0, bh)));
    boxLoop.Append(Line.CreateBound(new XYZ( bw/2, 0, bh),  new XYZ(-bw/2, 0, bh)));
    boxLoop.Append(Line.CreateBound(new XYZ(-bw/2, 0, bh),  new XYZ(-bw/2, 0, 0)));
    boxProfile.Append(boxLoop);

    SketchPlane spFace = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    Extrusion boxBody = familyDoc.FamilyCreate.NewExtrusion(true, boxProfile, spFace, -bd);

    double margin = 0.016404;
    double vw = bw + 2 * margin;
    double vh = bh + 2 * margin;
    CurveArrArray voidProfile = new CurveArrArray();
    CurveArray voidLoop = new CurveArray();
    voidLoop.Append(Line.CreateBound(new XYZ(-vw/2, 0, -margin),     new XYZ( vw/2, 0, -margin)));
    voidLoop.Append(Line.CreateBound(new XYZ( vw/2, 0, -margin),     new XYZ( vw/2, 0, vh - margin)));
    voidLoop.Append(Line.CreateBound(new XYZ( vw/2, 0, vh - margin), new XYZ(-vw/2, 0, vh - margin)));
    voidLoop.Append(Line.CreateBound(new XYZ(-vw/2, 0, vh - margin), new XYZ(-vw/2, 0, -margin)));
    voidProfile.Append(voidLoop);
    Extrusion roughIn = familyDoc.FamilyCreate.NewExtrusion(false, voidProfile, spFace, -(bd + 0.032808));

    tx.Commit();
}}""",
        ))

        samples.append(_s(
            "Create a wall-hosted light switch plate family (single-gang, 86x86mm, surface-mounted)",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Switch Plate"))
{{
    tx.Start();

    double pw = 0.282152;   // 86 mm
    double ph = 0.282152;   // 86 mm
    double pt = 0.026247;    // 8 mm thickness

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-pw/2, 0, 0),  new XYZ( pw/2, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ( pw/2, 0, 0),  new XYZ( pw/2, 0, ph)));
    loop.Append(Line.CreateBound(new XYZ( pw/2, 0, ph), new XYZ(-pw/2, 0, ph)));
    loop.Append(Line.CreateBound(new XYZ(-pw/2, 0, ph), new XYZ(-pw/2, 0, 0)));
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    Extrusion plate = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, pt);

    // Rocker void (20x40mm)
    double rw = 0.065617;
    double rh = 0.131234;
    CurveArrArray vProf = new CurveArrArray();
    CurveArray vLoop = new CurveArray();
    vLoop.Append(Line.CreateBound(new XYZ(-rw/2, 0, (ph-rh)/2), new XYZ( rw/2, 0, (ph-rh)/2)));
    vLoop.Append(Line.CreateBound(new XYZ( rw/2, 0, (ph-rh)/2), new XYZ( rw/2, 0, (ph+rh)/2)));
    vLoop.Append(Line.CreateBound(new XYZ( rw/2, 0, (ph+rh)/2), new XYZ(-rw/2, 0, (ph+rh)/2)));
    vLoop.Append(Line.CreateBound(new XYZ(-rw/2, 0, (ph+rh)/2), new XYZ(-rw/2, 0, (ph-rh)/2)));
    vProf.Append(vLoop);
    Extrusion rockerVoid = familyDoc.FamilyCreate.NewExtrusion(false, vProf, sp, pt);

    tx.Commit();
}}""",
        ))

        samples.append(_s(
            "Create a double-gang electrical outlet box family (200x70x55mm) wall-hosted",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Double-Gang Outlet"))
{{
    tx.Start();

    double bw = 0.656168;
    double bh = 0.229659;
    double bd = 0.180446;

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2, 0, 0),  new XYZ( bw/2, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, 0, 0),  new XYZ( bw/2, 0, bh)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, 0, bh), new XYZ(-bw/2, 0, bh)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2, 0, bh), new XYZ(-bw/2, 0, 0)));
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    Extrusion body  = familyDoc.FamilyCreate.NewExtrusion(true,  profile, sp, -bd);
    Extrusion plate = familyDoc.FamilyCreate.NewExtrusion(true,  profile, sp,  0.006562);

    tx.Commit();
}}""",
        ))

        samples.append(_s(
            "Create a wall-hosted data outlet (RJ45) plate family with port count parameter",
            """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pPorts = famMgr.AddParameter(
    "Port Count", BuiltInParameterGroup.PG_DATA, ParameterType.Integer, false);
famMgr.Set(pPorts, 2);

using (Transaction tx = new Transaction(familyDoc, "Create Data Outlet"))
{{
    tx.Start();

    double pw = 0.282152;
    double ph = 0.282152;
    double pt = 0.032808;

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-pw/2, 0, 0),  new XYZ( pw/2, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ( pw/2, 0, 0),  new XYZ( pw/2, 0, ph)));
    loop.Append(Line.CreateBound(new XYZ( pw/2, 0, ph), new XYZ(-pw/2, 0, ph)));
    loop.Append(Line.CreateBound(new XYZ(-pw/2, 0, ph), new XYZ(-pw/2, 0, 0)));
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    Extrusion plate = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, pt);

    tx.Commit();
}}""",
        ))

        samples.append(_s(
            "Create a wall-recessed electrical distribution panel family (400x600mm, 100mm deep recess)",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Electrical Panel"))
{{
    tx.Start();

    double pw = 1.312336;
    double ph = 1.968504;
    double pd = 0.328084;
    double ft_val = 0.009843;

    SketchPlane spFace = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    CurveArrArray voidProf = new CurveArrArray();
    CurveArray voidLoop = new CurveArray();
    voidLoop.Append(Line.CreateBound(new XYZ(-pw/2, 0, 0),  new XYZ( pw/2, 0, 0)));
    voidLoop.Append(Line.CreateBound(new XYZ( pw/2, 0, 0),  new XYZ( pw/2, 0, ph)));
    voidLoop.Append(Line.CreateBound(new XYZ( pw/2, 0, ph), new XYZ(-pw/2, 0, ph)));
    voidLoop.Append(Line.CreateBound(new XYZ(-pw/2, 0, ph), new XYZ(-pw/2, 0, 0)));
    voidProf.Append(voidLoop);
    Extrusion recess = familyDoc.FamilyCreate.NewExtrusion(false, voidProf, spFace, -pd);

    CurveArrArray doorProf = new CurveArrArray();
    CurveArray doorLoop = new CurveArray();
    doorLoop.Append(Line.CreateBound(new XYZ(-pw/2, 0, 0),  new XYZ( pw/2, 0, 0)));
    doorLoop.Append(Line.CreateBound(new XYZ( pw/2, 0, 0),  new XYZ( pw/2, 0, ph)));
    doorLoop.Append(Line.CreateBound(new XYZ( pw/2, 0, ph), new XYZ(-pw/2, 0, ph)));
    doorLoop.Append(Line.CreateBound(new XYZ(-pw/2, 0, ph), new XYZ(-pw/2, 0, 0)));
    doorProf.Append(doorLoop);
    Extrusion door = familyDoc.FamilyCreate.NewExtrusion(true, doorProf, spFace, ft_val);

    tx.Commit();
}}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # Wall-hosted plumbing penetrations and sleeves
    # ------------------------------------------------------------------

    def _wall_hosted_plumbing(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        pipe_cases = [
            (50,  110, "50mm pipe (110mm sleeve OD)"),
            (100, 160, "100mm pipe (160mm sleeve OD)"),
            (150, 220, "150mm pipe (220mm sleeve OD)"),
            (32,  75,  "32mm pipe (75mm sleeve OD)"),
        ]
        for pipe_dia, sleeve_od, desc in pipe_cases:
            pipe_r_ft   = f"{pipe_dia / 2 * MM_TO_FT:.6f}"
            sleeve_r_ft = f"{sleeve_od / 2 * MM_TO_FT:.6f}"
            samples.append(_s(
                f"Create a wall-hosted pipe sleeve family: {desc}",
                f"""\
using Autodesk.Revit.DB;
using System;

// Pipe sleeve: void cuts wall; annular sleeve solid sits in void.
// Pipe bore = {pipe_dia}mm, sleeve OD = {sleeve_od}mm
using (Transaction tx = new Transaction(familyDoc, "Create Pipe Sleeve"))
{{
    tx.Start();

    double pipeR   = {pipe_r_ft};
    double sleeveR = {sleeve_r_ft};
    double wallT   = 1.968504;
    int n = 24;

    SketchPlane spFace = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    CurveArray voidLoop = new CurveArray();
    for (int i = 0; i < n; i++)
    {{
        double a0 = 2 * Math.PI * i / n;
        double a1 = 2 * Math.PI * (i + 1) / n;
        XYZ p0 = new XYZ(sleeveR * Math.Cos(a0), 0, sleeveR + sleeveR * Math.Sin(a0));
        XYZ p1 = new XYZ(sleeveR * Math.Cos(a1), 0, sleeveR + sleeveR * Math.Sin(a1));
        voidLoop.Append(Line.CreateBound(p0, p1));
    }}
    CurveArrArray voidProf = new CurveArrArray();
    voidProf.Append(voidLoop);
    Extrusion wallVoid = familyDoc.FamilyCreate.NewExtrusion(false, voidProf, spFace, -wallT);

    CurveArray outerLoop = new CurveArray();
    CurveArray innerLoop = new CurveArray();
    for (int i = 0; i < n; i++)
    {{
        double a0 = 2 * Math.PI * i / n;
        double a1 = 2 * Math.PI * (i + 1) / n;
        XYZ po0 = new XYZ(sleeveR * Math.Cos(a0), 0, sleeveR + sleeveR * Math.Sin(a0));
        XYZ po1 = new XYZ(sleeveR * Math.Cos(a1), 0, sleeveR + sleeveR * Math.Sin(a1));
        XYZ pi0 = new XYZ(pipeR   * Math.Cos(a0), 0, sleeveR + pipeR   * Math.Sin(a0));
        XYZ pi1 = new XYZ(pipeR   * Math.Cos(a1), 0, sleeveR + pipeR   * Math.Sin(a1));
        outerLoop.Append(Line.CreateBound(po0, po1));
        innerLoop.Append(Line.CreateBound(pi0, pi1));
    }}
    CurveArrArray sleeveProf = new CurveArrArray();
    sleeveProf.Append(outerLoop);
    sleeveProf.Append(innerLoop);
    Extrusion sleeve = familyDoc.FamilyCreate.NewExtrusion(true, sleeveProf, spFace, -wallT);

    tx.Commit();
}}""",
            ))

        samples.append(_s(
            "Create a wall-hosted fire-rated intumescent pipe collar (110mm pipe, 250mm collar OD, 40mm thick)",
            """\
using Autodesk.Revit.DB;
using System;

using (Transaction tx = new Transaction(familyDoc, "Create Fire Collar"))
{{
    tx.Start();

    double pipeR   = 0.180446;
    double collarR = 0.410105;
    double collarT = 0.131234;
    double wallT   = 1.968504;
    int n = 24;

    SketchPlane spFace = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    CurveArray voidLoop = new CurveArray();
    for (int i = 0; i < n; i++)
    {{
        double a0 = 2 * Math.PI * i / n;
        double a1 = 2 * Math.PI * (i + 1) / n;
        XYZ p0 = new XYZ(pipeR * Math.Cos(a0), 0, collarR + pipeR * Math.Sin(a0));
        XYZ p1 = new XYZ(pipeR * Math.Cos(a1), 0, collarR + pipeR * Math.Sin(a1));
        voidLoop.Append(Line.CreateBound(p0, p1));
    }}
    CurveArrArray voidProf = new CurveArrArray();
    voidProf.Append(voidLoop);
    Extrusion wallVoid = familyDoc.FamilyCreate.NewExtrusion(false, voidProf, spFace, -wallT);

    CurveArray outerLoop = new CurveArray();
    CurveArray innerLoop = new CurveArray();
    for (int i = 0; i < n; i++)
    {{
        double a0 = 2 * Math.PI * i / n;
        double a1 = 2 * Math.PI * (i + 1) / n;
        XYZ co0 = new XYZ(collarR * Math.Cos(a0), 0, collarR + collarR * Math.Sin(a0));
        XYZ co1 = new XYZ(collarR * Math.Cos(a1), 0, collarR + collarR * Math.Sin(a1));
        XYZ ci0 = new XYZ(pipeR   * Math.Cos(a0), 0, collarR + pipeR   * Math.Sin(a0));
        XYZ ci1 = new XYZ(pipeR   * Math.Cos(a1), 0, collarR + pipeR   * Math.Sin(a1));
        outerLoop.Append(Line.CreateBound(co0, co1));
        innerLoop.Append(Line.CreateBound(ci0, ci1));
    }}
    CurveArrArray collarProf = new CurveArrArray();
    collarProf.Append(outerLoop);
    collarProf.Append(innerLoop);
    Extrusion collar = familyDoc.FamilyCreate.NewExtrusion(true, collarProf, spFace, collarT);

    tx.Commit();
}}""",
        ))

        samples.append(_s(
            "Create a wall-hosted vent grille family (400x200mm louvre frame, wall void for airflow)",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Vent Grille"))
{{
    tx.Start();

    double fw     = 1.312336;
    double fh     = 0.656168;
    double ftk    = 0.049213;
    double border = 0.065617;
    double wallT  = 0.984252;

    SketchPlane spFace = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    CurveArray outerLoop = new CurveArray();
    outerLoop.Append(Line.CreateBound(new XYZ(-fw/2, 0, 0),  new XYZ( fw/2, 0, 0)));
    outerLoop.Append(Line.CreateBound(new XYZ( fw/2, 0, 0),  new XYZ( fw/2, 0, fh)));
    outerLoop.Append(Line.CreateBound(new XYZ( fw/2, 0, fh), new XYZ(-fw/2, 0, fh)));
    outerLoop.Append(Line.CreateBound(new XYZ(-fw/2, 0, fh), new XYZ(-fw/2, 0, 0)));
    double iw = fw - 2 * border;
    double ih = fh - 2 * border;
    CurveArray innerLoop = new CurveArray();
    innerLoop.Append(Line.CreateBound(new XYZ(-iw/2, 0, border),      new XYZ( iw/2, 0, border)));
    innerLoop.Append(Line.CreateBound(new XYZ( iw/2, 0, border),      new XYZ( iw/2, 0, border+ih)));
    innerLoop.Append(Line.CreateBound(new XYZ( iw/2, 0, border+ih),   new XYZ(-iw/2, 0, border+ih)));
    innerLoop.Append(Line.CreateBound(new XYZ(-iw/2, 0, border+ih),   new XYZ(-iw/2, 0, border)));
    CurveArrArray frameProf = new CurveArrArray();
    frameProf.Append(outerLoop);
    frameProf.Append(innerLoop);
    Extrusion frame = familyDoc.FamilyCreate.NewExtrusion(true, frameProf, spFace, ftk);

    CurveArrArray voidProf = new CurveArrArray();
    CurveArray voidLoop = new CurveArray();
    voidLoop.Append(Line.CreateBound(new XYZ(-iw/2, 0, border),    new XYZ( iw/2, 0, border)));
    voidLoop.Append(Line.CreateBound(new XYZ( iw/2, 0, border),    new XYZ( iw/2, 0, border+ih)));
    voidLoop.Append(Line.CreateBound(new XYZ( iw/2, 0, border+ih), new XYZ(-iw/2, 0, border+ih)));
    voidLoop.Append(Line.CreateBound(new XYZ(-iw/2, 0, border+ih), new XYZ(-iw/2, 0, border)));
    voidProf.Append(voidLoop);
    Extrusion airVoid = familyDoc.FamilyCreate.NewExtrusion(false, voidProf, spFace, -wallT);

    tx.Commit();
}}""",
        ))

        samples.append(_s(
            "Create a wall-hosted rectangular cable tray wall penetration sleeve family (300x100mm tray)",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Cable Tray Penetration"))
{{
    tx.Start();

    double tw    = 0.984252;
    double th    = 0.328084;
    double wallT = 0.984252;
    double mat   = 0.032808;
    double margin = 0.016404;

    SketchPlane spFace = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    CurveArrArray voidProf = new CurveArrArray();
    CurveArray voidLoop = new CurveArray();
    voidLoop.Append(Line.CreateBound(new XYZ(-(tw+margin)/2, 0, -margin), new XYZ((tw+margin)/2, 0, -margin)));
    voidLoop.Append(Line.CreateBound(new XYZ( (tw+margin)/2, 0, -margin), new XYZ((tw+margin)/2, 0, th+margin)));
    voidLoop.Append(Line.CreateBound(new XYZ( (tw+margin)/2, 0, th+margin), new XYZ(-(tw+margin)/2, 0, th+margin)));
    voidLoop.Append(Line.CreateBound(new XYZ(-(tw+margin)/2, 0, th+margin), new XYZ(-(tw+margin)/2, 0, -margin)));
    voidProf.Append(voidLoop);
    Extrusion wallVoid = familyDoc.FamilyCreate.NewExtrusion(false, voidProf, spFace, -wallT);

    double ow = tw + 2 * mat;
    double oh = th + 2 * mat;
    CurveArray outerLoop = new CurveArray();
    outerLoop.Append(Line.CreateBound(new XYZ(-ow/2, 0, -mat),   new XYZ( ow/2, 0, -mat)));
    outerLoop.Append(Line.CreateBound(new XYZ( ow/2, 0, -mat),   new XYZ( ow/2, 0, oh-mat)));
    outerLoop.Append(Line.CreateBound(new XYZ( ow/2, 0, oh-mat), new XYZ(-ow/2, 0, oh-mat)));
    outerLoop.Append(Line.CreateBound(new XYZ(-ow/2, 0, oh-mat), new XYZ(-ow/2, 0, -mat)));
    CurveArray innerLoop = new CurveArray();
    innerLoop.Append(Line.CreateBound(new XYZ(-tw/2, 0, 0),  new XYZ( tw/2, 0, 0)));
    innerLoop.Append(Line.CreateBound(new XYZ( tw/2, 0, 0),  new XYZ( tw/2, 0, th)));
    innerLoop.Append(Line.CreateBound(new XYZ( tw/2, 0, th), new XYZ(-tw/2, 0, th)));
    innerLoop.Append(Line.CreateBound(new XYZ(-tw/2, 0, th), new XYZ(-tw/2, 0, 0)));
    CurveArrArray sleeveProf = new CurveArrArray();
    sleeveProf.Append(outerLoop);
    sleeveProf.Append(innerLoop);
    Extrusion sleeve = familyDoc.FamilyCreate.NewExtrusion(true, sleeveProf, spFace, -wallT);

    tx.Commit();
}}""",
        ))

        samples.append(_s(
            "Create a wall-hosted plumbing cleanout access panel family (200x200mm, flush-mounted)",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Cleanout Panel"))
{{
    tx.Start();

    double pw = 0.656168;
    double ph = 0.656168;
    double pd = 0.492126;
    double ft_val = 0.009843;

    SketchPlane spFace = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-pw/2, 0, 0),  new XYZ( pw/2, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ( pw/2, 0, 0),  new XYZ( pw/2, 0, ph)));
    loop.Append(Line.CreateBound(new XYZ( pw/2, 0, ph), new XYZ(-pw/2, 0, ph)));
    loop.Append(Line.CreateBound(new XYZ(-pw/2, 0, ph), new XYZ(-pw/2, 0, 0)));
    profile.Append(loop);

    Extrusion recess = familyDoc.FamilyCreate.NewExtrusion(false, profile, spFace, -pd);
    Extrusion door   = familyDoc.FamilyCreate.NewExtrusion(true,  profile, spFace,  ft_val);

    tx.Commit();
}}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # Wall-mounted fixtures
    # ------------------------------------------------------------------

    def _wall_mounted_fixtures(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        shelf_cases = [
            (600,  250, 30,  "small floating shelf 600x250mm, 30mm thick"),
            (1200, 300, 40,  "medium floating shelf 1200x300mm, 40mm thick"),
            (1800, 350, 50,  "large floating shelf 1800x350mm, 50mm thick"),
        ]
        for w, d, t, desc in shelf_cases:
            w_ft = f"{w * MM_TO_FT:.6f}"
            d_ft = f"{d * MM_TO_FT:.6f}"
            t_ft = f"{t * MM_TO_FT:.6f}"
            samples.append(_s(
                f"Create a wall-mounted {desc}",
                f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Floating Shelf"))
{{
    tx.Start();

    double sw = {w_ft};
    double sd = {d_ft};
    double st = {t_ft};

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-sw/2, 0, 0),  new XYZ( sw/2, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ( sw/2, 0, 0),  new XYZ( sw/2, 0, st)));
    loop.Append(Line.CreateBound(new XYZ( sw/2, 0, st), new XYZ(-sw/2, 0, st)));
    loop.Append(Line.CreateBound(new XYZ(-sw/2, 0, st), new XYZ(-sw/2, 0, 0)));
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    Extrusion shelf = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, sd);

    tx.Commit();
}}""",
            ))

        samples.append(_s(
            "Create a wall-mounted L-bracket support family (80x80mm, 5mm thick)",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create L-Bracket"))
{{
    tx.Start();

    double legL = 0.262467;
    double legT = 0.016404;
    double legW = 0.131234;

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    CurveArrArray vProf = new CurveArrArray();
    CurveArray vLoop = new CurveArray();
    vLoop.Append(Line.CreateBound(new XYZ(-legW/2, 0, 0),    new XYZ( legW/2, 0, 0)));
    vLoop.Append(Line.CreateBound(new XYZ( legW/2, 0, 0),    new XYZ( legW/2, 0, legL)));
    vLoop.Append(Line.CreateBound(new XYZ( legW/2, 0, legL), new XYZ(-legW/2, 0, legL)));
    vLoop.Append(Line.CreateBound(new XYZ(-legW/2, 0, legL), new XYZ(-legW/2, 0, 0)));
    vProf.Append(vLoop);
    Extrusion vertLeg = familyDoc.FamilyCreate.NewExtrusion(true, vProf, sp, legT);

    SketchPlane spTop = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, new XYZ(0, legT, 0)));
    CurveArrArray hProf = new CurveArrArray();
    CurveArray hLoop = new CurveArray();
    hLoop.Append(Line.CreateBound(new XYZ(-legW/2, legT, legL-legT), new XYZ( legW/2, legT, legL-legT)));
    hLoop.Append(Line.CreateBound(new XYZ( legW/2, legT, legL-legT), new XYZ( legW/2, legT, legL)));
    hLoop.Append(Line.CreateBound(new XYZ( legW/2, legT, legL),      new XYZ(-legW/2, legT, legL)));
    hLoop.Append(Line.CreateBound(new XYZ(-legW/2, legT, legL),      new XYZ(-legW/2, legT, legL-legT)));
    hProf.Append(hLoop);
    Extrusion horizLeg = familyDoc.FamilyCreate.NewExtrusion(true, hProf, spTop, legL);

    tx.Commit();
}}""",
        ))

        samples.append(_s(
            "Create a wall-mounted signage board family (600x200mm, 20mm standoff from wall)",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Signage Board"))
{{
    tx.Start();

    double sw  = 1.968504;
    double sh  = 0.656168;
    double st  = 0.016404;
    double sof = 0.065617;

    CurveArrArray signProf = new CurveArrArray();
    CurveArray signLoop = new CurveArray();
    signLoop.Append(Line.CreateBound(new XYZ(-sw/2, sof, 0),  new XYZ( sw/2, sof, 0)));
    signLoop.Append(Line.CreateBound(new XYZ( sw/2, sof, 0),  new XYZ( sw/2, sof, sh)));
    signLoop.Append(Line.CreateBound(new XYZ( sw/2, sof, sh), new XYZ(-sw/2, sof, sh)));
    signLoop.Append(Line.CreateBound(new XYZ(-sw/2, sof, sh), new XYZ(-sw/2, sof, 0)));
    signProf.Append(signLoop);

    SketchPlane spBoard = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, new XYZ(0, sof, 0)));
    Extrusion sign = familyDoc.FamilyCreate.NewExtrusion(true, signProf, spBoard, st);

    double postW = 0.032808;
    SketchPlane spFace = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    foreach (double px in new double[] { -sw/2 + postW, sw/2 - postW })
    {{
        CurveArrArray postProf = new CurveArrArray();
        CurveArray postLoop = new CurveArray();
        postLoop.Append(Line.CreateBound(new XYZ(px-postW/2, 0, sh/2-postW/2), new XYZ(px+postW/2, 0, sh/2-postW/2)));
        postLoop.Append(Line.CreateBound(new XYZ(px+postW/2, 0, sh/2-postW/2), new XYZ(px+postW/2, 0, sh/2+postW/2)));
        postLoop.Append(Line.CreateBound(new XYZ(px+postW/2, 0, sh/2+postW/2), new XYZ(px-postW/2, 0, sh/2+postW/2)));
        postLoop.Append(Line.CreateBound(new XYZ(px-postW/2, 0, sh/2+postW/2), new XYZ(px-postW/2, 0, sh/2-postW/2)));
        postProf.Append(postLoop);
        Extrusion post = familyDoc.FamilyCreate.NewExtrusion(true, postProf, spFace, sof);
    }}

    tx.Commit();
}}""",
        ))

        samples.append(_s(
            "Create a wall-mounted handrail bracket family (80mm arm projection, 40mm rail support)",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Handrail Bracket"))
{{
    tx.Start();

    double baseW = 0.196850;
    double baseH = 0.262467;
    double baseT = 0.019685;
    double armL  = 0.262467;
    double armR  = 0.049213;

    SketchPlane spFace = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    CurveArrArray baseProf = new CurveArrArray();
    CurveArray baseLoop = new CurveArray();
    baseLoop.Append(Line.CreateBound(new XYZ(-baseW/2, 0, 0),     new XYZ( baseW/2, 0, 0)));
    baseLoop.Append(Line.CreateBound(new XYZ( baseW/2, 0, 0),     new XYZ( baseW/2, 0, baseH)));
    baseLoop.Append(Line.CreateBound(new XYZ( baseW/2, 0, baseH), new XYZ(-baseW/2, 0, baseH)));
    baseLoop.Append(Line.CreateBound(new XYZ(-baseW/2, 0, baseH), new XYZ(-baseW/2, 0, 0)));
    baseProf.Append(baseLoop);
    Extrusion basePlate = familyDoc.FamilyCreate.NewExtrusion(true, baseProf, spFace, baseT);

    double armH = 2 * armR;
    double armZ = baseH / 2 - armR;
    SketchPlane spArm = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, new XYZ(0, baseT, 0)));
    CurveArrArray armProf = new CurveArrArray();
    CurveArray armLoop = new CurveArray();
    armLoop.Append(Line.CreateBound(new XYZ(-armR, baseT, armZ),        new XYZ( armR, baseT, armZ)));
    armLoop.Append(Line.CreateBound(new XYZ( armR, baseT, armZ),        new XYZ( armR, baseT, armZ + armH)));
    armLoop.Append(Line.CreateBound(new XYZ( armR, baseT, armZ + armH), new XYZ(-armR, baseT, armZ + armH)));
    armLoop.Append(Line.CreateBound(new XYZ(-armR, baseT, armZ + armH), new XYZ(-armR, baseT, armZ)));
    armProf.Append(armLoop);
    Extrusion arm = familyDoc.FamilyCreate.NewExtrusion(true, armProf, spArm, armL);

    tx.Commit();
}}""",
        ))

        samples.append(_s(
            "Create a wall-mounted fire extinguisher bracket family (holds 9kg cylinder, 180mm diameter)",
            """\
using Autodesk.Revit.DB;
using System;

using (Transaction tx = new Transaction(familyDoc, "Create Extinguisher Bracket"))
{{
    tx.Start();

    double cylR   = 0.295276;
    double cylH   = 1.640420;
    double plateW = 0.721785;
    double plateH = 1.804462;
    double plateT = 0.009843;
    int n = 20;

    SketchPlane spFace = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    CurveArrArray plateProf = new CurveArrArray();
    CurveArray plateLoop = new CurveArray();
    plateLoop.Append(Line.CreateBound(new XYZ(-plateW/2, 0, 0),      new XYZ( plateW/2, 0, 0)));
    plateLoop.Append(Line.CreateBound(new XYZ( plateW/2, 0, 0),      new XYZ( plateW/2, 0, plateH)));
    plateLoop.Append(Line.CreateBound(new XYZ( plateW/2, 0, plateH), new XYZ(-plateW/2, 0, plateH)));
    plateLoop.Append(Line.CreateBound(new XYZ(-plateW/2, 0, plateH), new XYZ(-plateW/2, 0, 0)));
    plateProf.Append(plateLoop);
    Extrusion plate = familyDoc.FamilyCreate.NewExtrusion(true, plateProf, spFace, plateT);

    SketchPlane spBase = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, new XYZ(0, cylR + plateT, 0)));
    CurveArray cylLoop = new CurveArray();
    for (int i = 0; i < n; i++)
    {{
        double a0 = 2 * Math.PI * i / n;
        double a1 = 2 * Math.PI * (i + 1) / n;
        XYZ p0 = new XYZ(cylR * Math.Cos(a0), cylR + plateT + cylR * Math.Sin(a0), 0);
        XYZ p1 = new XYZ(cylR * Math.Cos(a1), cylR + plateT + cylR * Math.Sin(a1), 0);
        cylLoop.Append(Line.CreateBound(p0, p1));
    }}
    CurveArrArray cylProf = new CurveArrArray();
    cylProf.Append(cylLoop);
    Extrusion cylinder = familyDoc.FamilyCreate.NewExtrusion(true, cylProf, spBase, cylH);

    tx.Commit();
}}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # Curtain wall panel patterns
    # ------------------------------------------------------------------

    def _wall_panel_patterns(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        samples.append(_s(
            "Create a curtain wall panel family: flat rectangular glass panel with aluminium frame",
            """using Autodesk.Revit.DB;

// Curtain panel: glass infill + aluminium frame
// Nominal 1000x2400mm for authoring; flexes with curtain grid in practice.
using (Transaction tx = new Transaction(familyDoc, "Create Curtain Panel"))
{
    tx.Start();

    double pw     = 3.280840; // 1000 mm
    double ph     = 7.874016; // 2400 mm
    double pt     = 0.039370; // 12 mm glass
    double border = 0.164042; // 50 mm frame border

    SketchPlane spFace = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    double iw = pw - 2 * border;
    double ih = ph - 2 * border;

    // Glass infill
    CurveArray glassLoop = new CurveArray();
    glassLoop.Append(Line.CreateBound(new XYZ(border,    0, border),    new XYZ(border+iw, 0, border)));
    glassLoop.Append(Line.CreateBound(new XYZ(border+iw, 0, border),    new XYZ(border+iw, 0, border+ih)));
    glassLoop.Append(Line.CreateBound(new XYZ(border+iw, 0, border+ih), new XYZ(border,    0, border+ih)));
    glassLoop.Append(Line.CreateBound(new XYZ(border,    0, border+ih), new XYZ(border,    0, border)));
    CurveArrArray glassProf = new CurveArrArray();
    glassProf.Append(glassLoop);
    Extrusion glass = familyDoc.FamilyCreate.NewExtrusion(true, glassProf, spFace, pt);

    // Frame (annular solid)
    CurveArray outerLoop = new CurveArray();
    outerLoop.Append(Line.CreateBound(new XYZ(0, 0, 0),  new XYZ(pw, 0, 0)));
    outerLoop.Append(Line.CreateBound(new XYZ(pw, 0, 0), new XYZ(pw, 0, ph)));
    outerLoop.Append(Line.CreateBound(new XYZ(pw, 0, ph), new XYZ(0, 0, ph)));
    outerLoop.Append(Line.CreateBound(new XYZ(0, 0, ph), new XYZ(0, 0, 0)));
    CurveArray innerLoop = new CurveArray();
    innerLoop.Append(Line.CreateBound(new XYZ(border,    0, border),    new XYZ(border+iw, 0, border)));
    innerLoop.Append(Line.CreateBound(new XYZ(border+iw, 0, border),    new XYZ(border+iw, 0, border+ih)));
    innerLoop.Append(Line.CreateBound(new XYZ(border+iw, 0, border+ih), new XYZ(border,    0, border+ih)));
    innerLoop.Append(Line.CreateBound(new XYZ(border,    0, border+ih), new XYZ(border,    0, border)));
    CurveArrArray frameProf = new CurveArrArray();
    frameProf.Append(outerLoop);
    frameProf.Append(innerLoop);
    Extrusion frame = familyDoc.FamilyCreate.NewExtrusion(true, frameProf, spFace, 0.131234); // 40mm

    tx.Commit();
}""",
        ))

        samples.append(_s(
            "Create a curtain wall spandrel panel family (opaque, 1000x600mm, 100mm total thickness)",
            """using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Spandrel Panel"))
{
    tx.Start();

    double pw = 3.280840; // 1000 mm
    double ph = 1.968504; // 600 mm

    SketchPlane spFace = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    CurveArrArray prof = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(0, 0, 0),  new XYZ(pw, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ(pw, 0, 0), new XYZ(pw, 0, ph)));
    loop.Append(Line.CreateBound(new XYZ(pw, 0, ph), new XYZ(0, 0, ph)));
    loop.Append(Line.CreateBound(new XYZ(0, 0, ph), new XYZ(0, 0, 0)));
    prof.Append(loop);

    // Outer cladding (10mm)
    Extrusion cladding = familyDoc.FamilyCreate.NewExtrusion(true, prof, spFace, 0.032808);

    // Insulation (80mm behind cladding)
    SketchPlane spInsul = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, new XYZ(0, 0.032808, 0)));
    Extrusion insulation = familyDoc.FamilyCreate.NewExtrusion(true, prof, spInsul, 0.262467);

    // Backing panel (10mm)
    SketchPlane spBack = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, new XYZ(0, 0.295276, 0)));
    Extrusion backing = familyDoc.FamilyCreate.NewExtrusion(true, prof, spBack, 0.032808);

    tx.Commit();
}""",
        ))

        samples.append(_s(
            "Create a curtain wall louvred panel family (horizontal aluminium blades, 1000x600mm)",
            """using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Louvred Panel"))
{
    tx.Start();

    double pw         = 3.280840; // 1000 mm
    double ph         = 1.968504; // 600 mm
    double frameB     = 0.065617; // 20 mm border
    double bladeT     = 0.016404; // 5 mm blade
    double bladePitch = 0.098425; // 30 mm pitch
    double bladeDepth = 0.196850; // 60 mm blade depth
    int bladeCount    = (int)((ph - 2 * frameB) / bladePitch);

    SketchPlane spFace = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    // Frame
    double iw = pw - 2 * frameB;
    double ih = ph - 2 * frameB;
    CurveArray outer = new CurveArray();
    outer.Append(Line.CreateBound(new XYZ(0, 0, 0),  new XYZ(pw, 0, 0)));
    outer.Append(Line.CreateBound(new XYZ(pw, 0, 0), new XYZ(pw, 0, ph)));
    outer.Append(Line.CreateBound(new XYZ(pw, 0, ph), new XYZ(0, 0, ph)));
    outer.Append(Line.CreateBound(new XYZ(0, 0, ph), new XYZ(0, 0, 0)));
    CurveArray inner = new CurveArray();
    inner.Append(Line.CreateBound(new XYZ(frameB, 0, frameB),       new XYZ(frameB+iw, 0, frameB)));
    inner.Append(Line.CreateBound(new XYZ(frameB+iw, 0, frameB),    new XYZ(frameB+iw, 0, frameB+ih)));
    inner.Append(Line.CreateBound(new XYZ(frameB+iw, 0, frameB+ih), new XYZ(frameB, 0, frameB+ih)));
    inner.Append(Line.CreateBound(new XYZ(frameB, 0, frameB+ih),    new XYZ(frameB, 0, frameB)));
    CurveArrArray frameProf = new CurveArrArray();
    frameProf.Append(outer);
    frameProf.Append(inner);
    Extrusion frame = familyDoc.FamilyCreate.NewExtrusion(true, frameProf, spFace, 0.131234);

    // Blades
    for (int b = 0; b < bladeCount; b++)
    {
        double z = frameB + b * bladePitch;
        CurveArrArray bp = new CurveArrArray();
        CurveArray bl = new CurveArray();
        bl.Append(Line.CreateBound(new XYZ(frameB, 0, z),         new XYZ(frameB+iw, 0, z)));
        bl.Append(Line.CreateBound(new XYZ(frameB+iw, 0, z),      new XYZ(frameB+iw, 0, z+bladeT)));
        bl.Append(Line.CreateBound(new XYZ(frameB+iw, 0, z+bladeT), new XYZ(frameB, 0, z+bladeT)));
        bl.Append(Line.CreateBound(new XYZ(frameB, 0, z+bladeT),  new XYZ(frameB, 0, z)));
        bp.Append(bl);
        Extrusion blade = familyDoc.FamilyCreate.NewExtrusion(true, bp, spFace, bladeDepth);
    }

    tx.Commit();
}""",
        ))

        samples.append(_s(
            "Create a parametric curtain wall panel family using built-in Width and Height parameters",
            """using Autodesk.Revit.DB;

// In curtain panel templates, Width and Height already exist as built-in params.
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth  = famMgr.get_Parameter("Width");
FamilyParameter pHeight = famMgr.get_Parameter("Height");

using (Transaction tx = new Transaction(familyDoc, "Create Parametric Panel"))
{
    tx.Start();

    double w = 3.280840; // 1000 mm (flexes with grid)
    double h = 7.874016; // 2400 mm (flexes with grid)
    double t = 0.039370; // 12 mm

    CurveArrArray prof = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(0, 0, 0), new XYZ(w, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ(w, 0, 0), new XYZ(w, 0, h)));
    loop.Append(Line.CreateBound(new XYZ(w, 0, h), new XYZ(0, 0, h)));
    loop.Append(Line.CreateBound(new XYZ(0, 0, h), new XYZ(0, 0, 0)));
    prof.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    Extrusion panel = familyDoc.FamilyCreate.NewExtrusion(true, prof, sp, t);

    tx.Commit();
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # Wall reveal profiles and wall sweeps
    # ------------------------------------------------------------------

    def _wall_reveal_profiles(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        reveal_cases = [
            (25, 15, "narrow reveal 25mm wide, 15mm deep"),
            (50, 25, "standard reveal 50mm wide, 25mm deep"),
            (75, 40, "deep reveal 75mm wide, 40mm deep"),
        ]
        for w, d, desc in reveal_cases:
            w_ft = f"{w * MM_TO_FT:.6f}"
            d_ft = f"{d * MM_TO_FT:.6f}"
            samples.append(_s(
                f"Create a wall reveal profile family: {desc}",
                f"""\
using Autodesk.Revit.DB;

// Wall reveal cross-section profile: rectangular channel.
// Origin at face centre; positive Y = into wall.
using (Transaction tx = new Transaction(familyDoc, "Create Reveal Profile"))
{{{{
    tx.Start();

    double rw = {w_ft};  // {w} mm
    double rd = {d_ft};  // {d} mm

    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-rw/2, 0,  0),  new XYZ( rw/2, 0,  0)));
    loop.Append(Line.CreateBound(new XYZ( rw/2, 0,  0),  new XYZ( rw/2, rd, 0)));
    loop.Append(Line.CreateBound(new XYZ( rw/2, rd, 0),  new XYZ(-rw/2, rd, 0)));
    loop.Append(Line.CreateBound(new XYZ(-rw/2, rd, 0),  new XYZ(-rw/2, 0,  0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewModelCurveArray(profile, sp);

    tx.Commit();
}}}}""",
            ))

        samples.append(_s(
            "Create a wall sweep chair rail profile family (50mm tall, 30mm projection)",
            """using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Chair Rail Profile"))
{
    tx.Start();

    double h  = 0.164042; // 50 mm
    double w  = 0.098425; // 30 mm
    double ch = 0.019685; // 6 mm chamfer

    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(0, 0, 0),      new XYZ(w, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ(w, 0, 0),      new XYZ(w, 0, h - ch)));
    loop.Append(Line.CreateBound(new XYZ(w, 0, h - ch), new XYZ(w - ch, 0, h)));
    loop.Append(Line.CreateBound(new XYZ(w - ch, 0, h), new XYZ(0, 0, h)));
    loop.Append(Line.CreateBound(new XYZ(0, 0, h),      new XYZ(0, 0, 0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewModelCurveArray(profile, sp);

    tx.Commit();
}""",
        ))

        samples.append(_s(
            "Create a wall sweep skirting board profile family (90mm tall, 18mm thick, floor rebate)",
            """using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Skirting Profile"))
{
    tx.Start();

    double h    = 0.295276; // 90 mm
    double t    = 0.059055; // 18 mm
    double reb  = 0.016404; // 5 mm rebate depth
    double rebH = 0.032808; // 10 mm rebate height

    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(0,   0, 0),    new XYZ(reb, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ(reb, 0, 0),    new XYZ(reb, 0, rebH)));
    loop.Append(Line.CreateBound(new XYZ(reb, 0, rebH), new XYZ(t,   0, rebH)));
    loop.Append(Line.CreateBound(new XYZ(t,   0, rebH), new XYZ(t,   0, h)));
    loop.Append(Line.CreateBound(new XYZ(t,   0, h),    new XYZ(0,   0, h)));
    loop.Append(Line.CreateBound(new XYZ(0,   0, h),    new XYZ(0,   0, 0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewModelCurveArray(profile, sp);

    tx.Commit();
}""",
        ))

        samples.append(_s(
            "Create a wall sweep cornice profile family (150mm tall, 100mm projection, stepped)",
            """using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Cornice Profile"))
{
    tx.Start();

    double h  = 0.492126; // 150 mm
    double w  = 0.328084; // 100 mm
    double s1 = 0.098425; // 30 mm step
    double s2 = 0.098425; // 30 mm step

    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(0,    0, 0),     new XYZ(w,    0, 0)));
    loop.Append(Line.CreateBound(new XYZ(w,    0, 0),     new XYZ(w,    0, s1)));
    loop.Append(Line.CreateBound(new XYZ(w,    0, s1),    new XYZ(w-s1, 0, s1)));
    loop.Append(Line.CreateBound(new XYZ(w-s1, 0, s1),   new XYZ(w-s1, 0, h-s2)));
    loop.Append(Line.CreateBound(new XYZ(w-s1, 0, h-s2), new XYZ(s2,   0, h-s2)));
    loop.Append(Line.CreateBound(new XYZ(s2,   0, h-s2), new XYZ(s2,   0, h)));
    loop.Append(Line.CreateBound(new XYZ(s2,   0, h),    new XYZ(0,    0, h)));
    loop.Append(Line.CreateBound(new XYZ(0,    0, h),    new XYZ(0,    0, 0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewModelCurveArray(profile, sp);

    tx.Commit();
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # Wall embedded structural elements
    # ------------------------------------------------------------------

    def _wall_embedded_elements(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        lintel_cases = [
            (900,  200, 100, 8,  "steel angle lintel 900mm span, 200x100x8mm"),
            (1200, 250, 100, 10, "steel angle lintel 1200mm span, 250x100x10mm"),
            (1800, 300, 150, 12, "heavy angle lintel 1800mm span, 300x150x12mm"),
        ]
        for span, h, w, t, desc in lintel_cases:
            span_ft = f"{span * MM_TO_FT:.6f}"
            h_ft    = f"{h   * MM_TO_FT:.6f}"
            w_ft    = f"{w   * MM_TO_FT:.6f}"
            t_ft    = f"{t   * MM_TO_FT:.6f}"
            samples.append(_s(
                f"Create a wall-embedded steel lintel family: {desc}",
                f"""\
using Autodesk.Revit.DB;

// Steel angle lintel: L-section, vertical leg supports masonry above opening.
using (Transaction tx = new Transaction(familyDoc, "Create Steel Lintel"))
{{
    tx.Start();

    double span = {span_ft};
    double h    = {h_ft};
    double w    = {w_ft};
    double t    = {t_ft};

    // L-section profile in XZ plane
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(0, 0, 0),   new XYZ(w, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ(w, 0, 0),   new XYZ(w, 0, t)));
    loop.Append(Line.CreateBound(new XYZ(w, 0, t),   new XYZ(t, 0, t)));
    loop.Append(Line.CreateBound(new XYZ(t, 0, t),   new XYZ(t, 0, h)));
    loop.Append(Line.CreateBound(new XYZ(t, 0, h),   new XYZ(0, 0, h)));
    loop.Append(Line.CreateBound(new XYZ(0, 0, h),   new XYZ(0, 0, 0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    Extrusion lintel = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, span);

    tx.Commit();
}}""",
            ))

        samples.append(_s(
            "Create a precast concrete window sill family (150mm projection, 50mm tall, drip groove)",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Concrete Sill"))
{{
    tx.Start();

    double sw   = 0.492126;   // 150 mm projection
    double sh   = 0.164042;    // 50 mm height
    double dripW = 0.032808;   // 10 mm drip width
    double dripD = 0.016404;    // 5 mm drip depth

    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(0,  0, 0),  new XYZ(sw, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ(sw, 0, 0),  new XYZ(sw, 0, sh)));
    loop.Append(Line.CreateBound(new XYZ(sw, 0, sh), new XYZ(0,  0, sh)));
    loop.Append(Line.CreateBound(new XYZ(0,  0, sh), new XYZ(0,  0, 0)));
    CurveArrArray prof = new CurveArrArray();
    prof.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    Extrusion sill = familyDoc.FamilyCreate.NewExtrusion(true, prof, sp, 1.0);

    // Drip groove void on soffit near front
    CurveArray dripLoop = new CurveArray();
    dripLoop.Append(Line.CreateBound(new XYZ(sw-dripW*2, 0, 0),      new XYZ(sw-dripW, 0, 0)));
    dripLoop.Append(Line.CreateBound(new XYZ(sw-dripW,   0, 0),      new XYZ(sw-dripW, 0, dripD)));
    dripLoop.Append(Line.CreateBound(new XYZ(sw-dripW,   0, dripD),  new XYZ(sw-dripW*2, 0, dripD)));
    dripLoop.Append(Line.CreateBound(new XYZ(sw-dripW*2, 0, dripD),  new XYZ(sw-dripW*2, 0, 0)));
    CurveArrArray dripProf = new CurveArrArray();
    dripProf.Append(dripLoop);
    Extrusion drip = familyDoc.FamilyCreate.NewExtrusion(false, dripProf, sp, 1.0);

    tx.Commit();
}}""",
        ))

        samples.append(_s(
            "Create a wall-embedded timber wall plate family (100x50mm, runs along top of masonry)",
            f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pSpan = famMgr.AddParameter(
    "Span", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pSpan, 9.842520);

using (Transaction tx = new Transaction(familyDoc, "Create Wall Plate"))
{{
    tx.Start();

    double w    = 0.328084;
    double h    = 0.164042;
    double span = 9.842520;

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-w/2, 0, 0),  new XYZ( w/2, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, 0, 0),  new XYZ( w/2, 0, h)));
    loop.Append(Line.CreateBound(new XYZ( w/2, 0, h),  new XYZ(-w/2, 0, h)));
    loop.Append(Line.CreateBound(new XYZ(-w/2, 0, h),  new XYZ(-w/2, 0, 0)));
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    Extrusion plate = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, span);

    tx.Commit();
}}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # Symbolic lines for 2D plan/elevation representation
    # ------------------------------------------------------------------

    def _symbolic_lines(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        samples.append(_s(
            "Create symbolic lines for a wall-hosted family: door swing arc in plan view",
            """using Autodesk.Revit.DB;
using System;

using (Transaction tx = new Transaction(familyDoc, "Create Door Swing Symbol"))
{
    tx.Start();

    double dw = 2.952756; // 900 mm door width
    double dt = 0.131234; // 40 mm thickness in plan

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // Door leaf
    CurveArray leaf = new CurveArray();
    leaf.Append(Line.CreateBound(new XYZ(0,  0, 0), new XYZ(dw, 0, 0)));
    leaf.Append(Line.CreateBound(new XYZ(dw, 0, 0), new XYZ(dw, dt, 0)));
    leaf.Append(Line.CreateBound(new XYZ(dw, dt, 0), new XYZ(0, dt, 0)));
    leaf.Append(Line.CreateBound(new XYZ(0, dt, 0), new XYZ(0, 0, 0)));
    familyDoc.FamilyCreate.NewSymbolicCurveArray(leaf, sp);

    // Swing arc (quarter circle, 12 segments)
    int n = 12;
    CurveArray arc = new CurveArray();
    for (int i = 0; i < n; i++)
    {
        double a0 = Math.PI * 0.5 * i / n;
        double a1 = Math.PI * 0.5 * (i + 1) / n;
        XYZ p0 = new XYZ(dw * Math.Cos(a0), dw * Math.Sin(a0), 0);
        XYZ p1 = new XYZ(dw * Math.Cos(a1), dw * Math.Sin(a1), 0);
        arc.Append(Line.CreateBound(p0, p1));
    }
    familyDoc.FamilyCreate.NewSymbolicCurveArray(arc, sp);

    tx.Commit();
}""",
        ))

        samples.append(_s(
            "Create symbolic lines for an electrical outlet: circle with two horizontal lines",
            """using Autodesk.Revit.DB;
using System;

using (Transaction tx = new Transaction(familyDoc, "Create Outlet Symbol"))
{
    tx.Start();

    double r    = 0.032808; // 10 mm radius
    double lineL = 0.032808;
    int n = 16;

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    CurveArray circle = new CurveArray();
    for (int i = 0; i < n; i++)
    {
        double a0 = 2 * Math.PI * i / n;
        double a1 = 2 * Math.PI * (i + 1) / n;
        XYZ p0 = new XYZ(r * Math.Cos(a0), r * Math.Sin(a0), 0);
        XYZ p1 = new XYZ(r * Math.Cos(a1), r * Math.Sin(a1), 0);
        circle.Append(Line.CreateBound(p0, p1));
    }
    familyDoc.FamilyCreate.NewSymbolicCurveArray(circle, sp);

    CurveArray lines = new CurveArray();
    lines.Append(Line.CreateBound(new XYZ(-lineL, r * 0.3, 0), new XYZ(lineL, r * 0.3, 0)));
    lines.Append(Line.CreateBound(new XYZ(-lineL, -r * 0.3, 0), new XYZ(lineL, -r * 0.3, 0)));
    familyDoc.FamilyCreate.NewSymbolicCurveArray(lines, sp);

    tx.Commit();
}""",
        ))

        samples.append(_s(
            "Create symbolic lines for a vent grille: hatched rectangle in plan",
            """using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Vent Grille Symbol"))
{
    tx.Start();

    double gw = 1.312336; // 400 mm
    double gh = 0.656168; // 200 mm
    int diags = 5;

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    CurveArray rect = new CurveArray();
    rect.Append(Line.CreateBound(new XYZ(-gw/2, -gh/2, 0), new XYZ( gw/2, -gh/2, 0)));
    rect.Append(Line.CreateBound(new XYZ( gw/2, -gh/2, 0), new XYZ( gw/2,  gh/2, 0)));
    rect.Append(Line.CreateBound(new XYZ( gw/2,  gh/2, 0), new XYZ(-gw/2,  gh/2, 0)));
    rect.Append(Line.CreateBound(new XYZ(-gw/2,  gh/2, 0), new XYZ(-gw/2, -gh/2, 0)));
    familyDoc.FamilyCreate.NewSymbolicCurveArray(rect, sp);

    for (int i = 0; i <= diags; i++)
    {
        double t = (double)i / diags;
        double x = -gw/2 + t * gw;
        CurveArray hatch = new CurveArray();
        hatch.Append(Line.CreateBound(new XYZ(x, -gh/2, 0), new XYZ(x - gh/4, gh/2, 0)));
        familyDoc.FamilyCreate.NewSymbolicCurveArray(hatch, sp);
    }

    tx.Commit();
}""",
        ))

        samples.append(_s(
            "Create symbolic lines for a wall switch: IEC 60617 circle with angled line and tick",
            """using Autodesk.Revit.DB;
using System;

using (Transaction tx = new Transaction(familyDoc, "Create Switch Symbol"))
{
    tx.Start();

    double r    = 0.032808; // 10 mm
    double lineL = 0.049213; // 15 mm
    int n = 16;

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    CurveArray circle = new CurveArray();
    for (int i = 0; i < n; i++)
    {
        double a0 = 2 * Math.PI * i / n;
        double a1 = 2 * Math.PI * (i + 1) / n;
        circle.Append(Line.CreateBound(
            new XYZ(r * Math.Cos(a0), r * Math.Sin(a0), 0),
            new XYZ(r * Math.Cos(a1), r * Math.Sin(a1), 0)));
    }
    familyDoc.FamilyCreate.NewSymbolicCurveArray(circle, sp);

    double angle = Math.PI / 4;
    XYZ start = new XYZ(r * Math.Cos(angle), r * Math.Sin(angle), 0);
    XYZ end   = new XYZ(start.X + lineL * Math.Cos(angle), start.Y + lineL * Math.Sin(angle), 0);
    double tickL = 0.016404;
    double perpA = angle + Math.PI / 2;
    XYZ tickEnd = new XYZ(end.X + tickL * Math.Cos(perpA), end.Y + tickL * Math.Sin(perpA), 0);

    CurveArray arm = new CurveArray();
    arm.Append(Line.CreateBound(start, end));
    arm.Append(Line.CreateBound(end, tickEnd));
    familyDoc.FamilyCreate.NewSymbolicCurveArray(arm, sp);

    tx.Commit();
}""",
        ))

        samples.append(_s(
            "Create symbolic lines for a generic wall-hosted box: rectangle with centrelines in plan",
            """using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Box Symbol Lines"))
{
    tx.Start();

    double bw = 0.377297; // 115 mm
    double bd = 0.180446; // 55 mm

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    CurveArray rect = new CurveArray();
    rect.Append(Line.CreateBound(new XYZ(-bw/2, 0,   0), new XYZ( bw/2, 0,   0)));
    rect.Append(Line.CreateBound(new XYZ( bw/2, 0,   0), new XYZ( bw/2, bd,  0)));
    rect.Append(Line.CreateBound(new XYZ( bw/2, bd,  0), new XYZ(-bw/2, bd,  0)));
    rect.Append(Line.CreateBound(new XYZ(-bw/2, bd,  0), new XYZ(-bw/2, 0,   0)));
    familyDoc.FamilyCreate.NewSymbolicCurveArray(rect, sp);

    CurveArray centres = new CurveArray();
    centres.Append(Line.CreateBound(new XYZ(0,    0,    0), new XYZ(0,    bd,   0)));
    centres.Append(Line.CreateBound(new XYZ(-bw/2, bd/2, 0), new XYZ(bw/2, bd/2, 0)));
    familyDoc.FamilyCreate.NewSymbolicCurveArray(centres, sp);

    tx.Commit();
}""",
        ))

        samples.append(_s(
            "Set detail level visibility: hide 3D body in coarse, show symbolic lines in all detail levels",
            """using Autodesk.Revit.DB;

// Control element visibility by detail level
using (Transaction tx = new Transaction(familyDoc, "Set Detail Level Visibility"))
{
    tx.Start();

    // 3D body: hidden in coarse only
    FamilyElementVisibility solidVis = new FamilyElementVisibility(
        FamilyElementVisibilityType.Model);
    solidVis.IsShownInCoarse  = false;
    solidVis.IsShownInMedium  = true;
    solidVis.IsShownInFine    = true;
    // bodyExtrusion.SetVisibility(solidVis);

    // Symbolic lines: visible in all levels
    FamilyElementVisibility symVis = new FamilyElementVisibility(
        FamilyElementVisibilityType.Model);
    symVis.IsShownInCoarse = true;
    symVis.IsShownInMedium = true;
    symVis.IsShownInFine   = true;
    // symbolicLine.SetVisibility(symVis);

    tx.Commit();
}""",
        ))

        samples.append(_s(
            "Create symbolic lines for a pipe sleeve in elevation view: circle and centre cross",
            """using Autodesk.Revit.DB;
using System;

using (Transaction tx = new Transaction(familyDoc, "Create Pipe Symbol Lines"))
{
    tx.Start();

    double r = 0.180446; // 55 mm
    int n = 24;

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    CurveArray circle = new CurveArray();
    for (int i = 0; i < n; i++)
    {
        double a0 = 2 * Math.PI * i / n;
        double a1 = 2 * Math.PI * (i + 1) / n;
        XYZ p0 = new XYZ(r * Math.Cos(a0), 0, r + r * Math.Sin(a0));
        XYZ p1 = new XYZ(r * Math.Cos(a1), 0, r + r * Math.Sin(a1));
        circle.Append(Line.CreateBound(p0, p1));
    }
    familyDoc.FamilyCreate.NewSymbolicCurveArray(circle, sp);

    CurveArray cross = new CurveArray();
    cross.Append(Line.CreateBound(new XYZ(-r * 0.7, 0, r),        new XYZ(r * 0.7, 0, r)));
    cross.Append(Line.CreateBound(new XYZ(0, 0, r - r * 0.7),     new XYZ(0, 0, r + r * 0.7)));
    familyDoc.FamilyCreate.NewSymbolicCurveArray(cross, sp);

    tx.Commit();
}""",
        ))

        return samples
