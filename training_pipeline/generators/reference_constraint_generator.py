"""Training data generator: Revit reference planes, dimensions, and constraints.

Produces ~270 Alpaca-format training pairs covering reference planes, linear and
angular dimensions, equality and alignment constraints, FamilyLabel assignment,
parametric constraint workflows, and strong/weak reference patterns.
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


class ReferenceConstraintGenerator:
    """Generates training samples for Revit reference planes, dimensions, and constraints."""

    def generate(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []
        samples += self._reference_planes()
        samples += self._reference_lines()
        samples += self._linear_dimensions()
        samples += self._angular_dimensions()
        samples += self._equality_constraints()
        samples += self._alignment_constraints()
        samples += self._label_dimensions()
        samples += self._parametric_constraint_workflows()
        samples += self._strong_reference_patterns()
        return samples

    # ------------------------------------------------------------------
    # Reference planes
    # ------------------------------------------------------------------

    def _reference_planes(self) -> List[SAMPLE]:
        samples = []

        # Named planes at fixed offsets along X (Left/Right pairs)
        lr_cases = [
            (150, "Width_Left", "Width_Right", "Add left and right reference planes 150mm from center for a 300mm-wide family"),
            (300, "Left", "Right", "Add left and right reference planes 300mm from center"),
            (600, "Flange_Left", "Flange_Right", "Add flange reference planes 600mm from center"),
            (50,  "Edge_Left", "Edge_Right", "Add narrow edge reference planes 50mm from center"),
            (1000, "Limit_Left", "Limit_Right", "Add outer limit reference planes 1000mm from center"),
            (75,  "Web_Left", "Web_Right", "Add web reference planes 75mm from center for an I-beam family"),
            (225, "Column_Left", "Column_Right", "Add column bounding reference planes 225mm from center"),
            (400, "Beam_Left", "Beam_Right", "Add beam bounding reference planes 400mm from center"),
            (500, "Panel_Left", "Panel_Right", "Add panel reference planes 500mm from center"),
        ]
        for half_mm, left_name, right_name, instruction in lr_cases:
            half_ft = half_mm * MM_TO_FT
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;

// Reference planes must be created INSIDE a Transaction
using (Transaction tx = new Transaction(familyDoc, "Add Reference Planes"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;

    // Left plane at X = -{half_mm} mm = -{half_ft:.6f} ft
    ReferencePlane rpLeft = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(-{half_ft:.6f}, 0, 0),
        new XYZ(-{half_ft:.6f}, 1, 0),
        XYZ.BasisZ,
        activeView);
    rpLeft.Name = "{left_name}";

    // Right plane at X = +{half_mm} mm = +{half_ft:.6f} ft
    ReferencePlane rpRight = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ({half_ft:.6f}, 0, 0),
        new XYZ({half_ft:.6f}, 1, 0),
        XYZ.BasisZ,
        activeView);
    rpRight.Name = "{right_name}";

    tx.Commit();
}}"""))

        # Named planes at fixed offsets along Y (Front/Back pairs)
        fb_cases = [
            (100, "Front", "Back", "Add front and back reference planes 100mm from center"),
            (200, "Depth_Front", "Depth_Back", "Add depth reference planes 200mm from center along Y"),
            (75,  "Web_Front", "Web_Back", "Add web reference planes 75mm from center"),
            (150, "Flange_Front", "Flange_Back", "Add flange front and back reference planes 150mm from center"),
            (50,  "Face_Front", "Face_Back", "Add thin face reference planes 50mm from center"),
            (300, "Cladding_Front", "Cladding_Back", "Add cladding reference planes 300mm from center along Y"),
        ]
        for half_mm, front_name, back_name, instruction in fb_cases:
            half_ft = half_mm * MM_TO_FT
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Add Front/Back Reference Planes"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;

    // Front plane at Y = -{half_mm} mm
    ReferencePlane rpFront = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, -{half_ft:.6f}, 0),
        new XYZ(1, -{half_ft:.6f}, 0),
        XYZ.BasisZ,
        activeView);
    rpFront.Name = "{front_name}";

    // Back plane at Y = +{half_mm} mm
    ReferencePlane rpBack = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, {half_ft:.6f}, 0),
        new XYZ(1, {half_ft:.6f}, 0),
        XYZ.BasisZ,
        activeView);
    rpBack.Name = "{back_name}";

    tx.Commit();
}}"""))

        # Single named planes at specific offsets
        single_cases = [
            (0, "Center (Left/Right)", "XYZ.BasisY", "XYZ.BasisZ", "Create the center left/right reference plane at the family origin"),
            (0, "Center (Front/Back)", "XYZ.BasisX", "XYZ.BasisZ", "Create the center front/back reference plane at the family origin"),
        ]
        for offset_mm, plane_name, dir_vec, normal_vec, instruction in single_cases:
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Add Center Reference Plane"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;

    ReferencePlane rp = familyDoc.FamilyCreate.NewReferencePlane(
        XYZ.Zero,
        {dir_vec},
        {normal_vec},
        activeView);
    rp.Name = "{plane_name}";

    tx.Commit();
}}"""))

        # Offset planes (not symmetric)
        offset_cases = [
            (300,  "ShelfTop",    "Z", "Create a horizontal reference plane 300mm above the origin (shelf top)"),
            (1200, "DoorTop",     "Z", "Create a horizontal reference plane 1200mm above the origin (door top)"),
            (2100, "CeilingRef",  "Z", "Create a horizontal reference plane 2100mm above the origin (ceiling reference)"),
            (600,  "MidHeight",   "Z", "Create a horizontal reference plane at 600mm (mid-height marker)"),
            (900,  "WindowSill",  "Z", "Create a horizontal reference plane at 900mm (window sill height)"),
            (2400, "StoreyTop",   "Z", "Create a horizontal reference plane at 2400mm (storey top)"),
            (50,   "BasePlate",   "Z", "Create a horizontal reference plane at 50mm (base plate thickness)"),
            (450,  "HalfHeight",  "Z", "Create a horizontal reference plane at 450mm (quarter-height marker)"),
        ]
        for offset_mm, name, axis, instruction in offset_cases:
            offset_ft = offset_mm * MM_TO_FT
            if axis == "Z":
                p0 = f"new XYZ(0, 0, {offset_ft:.6f})"
                p1 = f"new XYZ(1, 0, {offset_ft:.6f})"
                cut_vec = "XYZ.BasisY"
            else:
                p0 = f"new XYZ({offset_ft:.6f}, 0, 0)"
                p1 = f"new XYZ({offset_ft:.6f}, 1, 0)"
                cut_vec = "XYZ.BasisZ"
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Add Reference Plane"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;

    ReferencePlane rp = familyDoc.FamilyCreate.NewReferencePlane(
        {p0},
        {p1},
        {cut_vec},
        activeView);
    rp.Name = "{name}";

    tx.Commit();
}}"""))

        # Four reference planes (full bounding box set)
        box_cases = [
            (300,  300,  "Create four reference planes forming a 300x300mm bounding box (Left, Right, Front, Back)"),
            (600,  200,  "Create four reference planes for a 600x200mm door opening (Left, Right, Front, Back)"),
            (450,  450,  "Create four reference planes forming a 450x450mm column bounding box"),
            (900,  300,  "Create four reference planes for a 900x300mm window unit"),
            (1200, 400,  "Create four reference planes for a 1200x400mm shelf family"),
            (200,  200,  "Create four reference planes for a 200x200mm square post"),
            (760,  760,  "Create four reference planes for a 760x760mm structural column"),
        ]
        for w_mm, d_mm, instruction in box_cases:
            hw = w_mm / 2 * MM_TO_FT
            hd = d_mm / 2 * MM_TO_FT
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;

// Four bounding-box reference planes: {w_mm} x {d_mm} mm
using (Transaction tx = new Transaction(familyDoc, "Add Bounding Box Reference Planes"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;

    // Left: X = -{w_mm/2} mm
    ReferencePlane rpLeft = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(-{hw:.6f}, 0, 0), new XYZ(-{hw:.6f}, 1, 0), XYZ.BasisZ, activeView);
    rpLeft.Name = "Left";

    // Right: X = +{w_mm/2} mm
    ReferencePlane rpRight = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ({hw:.6f}, 0, 0), new XYZ({hw:.6f}, 1, 0), XYZ.BasisZ, activeView);
    rpRight.Name = "Right";

    // Front: Y = -{d_mm/2} mm
    ReferencePlane rpFront = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, -{hd:.6f}, 0), new XYZ(1, -{hd:.6f}, 0), XYZ.BasisZ, activeView);
    rpFront.Name = "Front";

    // Back: Y = +{d_mm/2} mm
    ReferencePlane rpBack = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, {hd:.6f}, 0), new XYZ(1, {hd:.6f}, 0), XYZ.BasisZ, activeView);
    rpBack.Name = "Back";

    tx.Commit();
}}"""))

        # Rename existing reference plane
        samples.append(_s(
            "Rename the default unnamed reference plane found in a new family document",
            """\
using Autodesk.Revit.DB;
using System.Linq;

// Find the built-in reference plane and rename it
using (Transaction tx = new Transaction(familyDoc, "Rename Reference Plane"))
{
    tx.Start();

    ReferencePlane rp = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane))
        .Cast<ReferencePlane>()
        .FirstOrDefault(r => string.IsNullOrEmpty(r.Name));

    if (rp != null)
        rp.Name = "Center (Left/Right)";

    tx.Commit();
}"""))

        # Enumerate all reference planes
        samples.append(_s(
            "List all reference plane names in the current family document",
            """\
using Autodesk.Revit.DB;
using System.Linq;

// Read-only: no transaction needed
IList<ReferencePlane> planes = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(ReferencePlane))
    .Cast<ReferencePlane>()
    .ToList();

foreach (ReferencePlane rp in planes)
{
    string name = string.IsNullOrEmpty(rp.Name) ? "(unnamed)" : rp.Name;
    TaskDialog.Show("Reference Planes", $"Name: {name}  Normal: {rp.Normal}");
}"""))

        # Retrieve reference plane by name
        samples.append(_s(
            "Retrieve a reference plane named 'Width_Left' from the family document",
            """\
using Autodesk.Revit.DB;
using System.Linq;

ReferencePlane rpWidthLeft = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(ReferencePlane))
    .Cast<ReferencePlane>()
    .FirstOrDefault(rp => rp.Name == "Width_Left");

if (rpWidthLeft == null)
    throw new InvalidOperationException("Reference plane 'Width_Left' not found.");"""))

        return samples

    # ------------------------------------------------------------------
    # Reference lines
    # ------------------------------------------------------------------

    def _reference_lines(self) -> List[SAMPLE]:
        samples = []

        # Straight reference lines at various angles
        angle_cases = [
            (0,   500, "horizontal", "Create a horizontal reference line 500mm long along the X axis"),
            (45,  400, "diagonal",   "Create a 45-degree diagonal reference line 400mm long"),
            (90,  600, "vertical",   "Create a vertical reference line 600mm long along the Y axis"),
            (30,  300, "30-degree",  "Create a 30-degree reference line 300mm long"),
            (60,  350, "60-degree",  "Create a 60-degree reference line 350mm long"),
            (15,  250, "15-degree",  "Create a 15-degree reference line 250mm long for a shallow-angle brace"),
            (75,  280, "75-degree",  "Create a 75-degree reference line 280mm long for a steep brace"),
            (120, 320, "120-degree", "Create a 120-degree reference line 320mm long"),
            (135, 300, "135-degree", "Create a 135-degree reference line 300mm long for a chamfer guide"),
            (150, 400, "150-degree", "Create a 150-degree reference line 400mm long"),
        ]
        for angle_deg, length_mm, label, instruction in angle_cases:
            length_ft = length_mm * MM_TO_FT
            angle_rad = math.radians(angle_deg)
            ex = length_ft * math.cos(angle_rad)
            ey = length_ft * math.sin(angle_rad)
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;

// Reference line: {label}, {length_mm} mm, {angle_deg} degrees
using (Transaction tx = new Transaction(familyDoc, "Create Reference Line"))
{{
    tx.Start();

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // Start at origin, end at ({ex:.6f}, {ey:.6f}, 0) ft
    Line refLine = Line.CreateBound(
        XYZ.Zero,
        new XYZ({ex:.6f}, {ey:.6f}, 0));

    ReferenceLine rl = familyDoc.FamilyCreate.NewReferenceLine(
        refLine, sp);

    tx.Commit();
}}"""))

        # Arc reference line for angular constraint
        arc_cases = [
            (200, 0,  90,  "Create a quarter-circle (90-degree) arc reference line, radius 200mm"),
            (150, 0,  45,  "Create a 45-degree arc reference line, radius 150mm"),
            (300, 0,  180, "Create a semicircular arc reference line, radius 300mm"),
            (100, 0,  270, "Create a 270-degree arc reference line, radius 100mm"),
            (250, 45, 135, "Create a 90-degree arc reference line starting at 45 degrees, radius 250mm"),
            (400, 0,  360, "Create a full-circle arc reference line (360 degrees), radius 400mm"),
        ]
        for r_mm, start_deg, end_deg, instruction in arc_cases:
            r_ft = r_mm * MM_TO_FT
            start_rad = math.radians(start_deg)
            end_rad = math.radians(end_deg)
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;

// Arc reference line: radius {r_mm} mm, {start_deg}-{end_deg} degrees
using (Transaction tx = new Transaction(familyDoc, "Create Arc Reference Line"))
{{
    tx.Start();

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    Arc arc = Arc.Create(
        XYZ.Zero,            // center
        {r_ft:.6f},           // radius ({r_mm} mm)
        {start_rad:.6f},      // start angle ({start_deg} deg)
        {end_rad:.6f},        // end angle ({end_deg} deg)
        XYZ.BasisX,
        XYZ.BasisY);

    ReferenceLine rl = familyDoc.FamilyCreate.NewReferenceLine(arc, sp);

    tx.Commit();
}}"""))

        # Reference line from two points
        samples.append(_s(
            "Create a reference line between two specific points for an angular dimension anchor",
            f"""\
using Autodesk.Revit.DB;

// Reference line between two known points
using (Transaction tx = new Transaction(familyDoc, "Create Reference Line"))
{{
    tx.Start();

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    XYZ ptStart = new XYZ({_ft(200)}, 0, 0);   // 200 mm along X
    XYZ ptEnd   = new XYZ({_ft(200)}, {_ft(300)}, 0); // 300 mm along Y from ptStart

    Line lineGeom = Line.CreateBound(ptStart, ptEnd);
    ReferenceLine rl = familyDoc.FamilyCreate.NewReferenceLine(lineGeom, sp);

    tx.Commit();
}}"""))

        # Get geometry reference from a reference line
        samples.append(_s(
            "Get the geometry reference from a reference line to use in a dimension",
            """\
using Autodesk.Revit.DB;

// ReferenceLine.GeometryCurve.Reference gives a stable reference for dimensions
// (Read-only, no transaction needed if line already exists)

ReferenceLine rl = /* previously created reference line */;

Reference lineRef = rl.GeometryCurve.Reference;
// Use lineRef in NewLinearDimension or NewAngularDimension calls"""))

        return samples

    # ------------------------------------------------------------------
    # Linear dimensions
    # ------------------------------------------------------------------

    def _linear_dimensions(self) -> List[SAMPLE]:
        samples = []

        # Basic linear dimensions between two reference planes
        basic_cases = [
            (300,  "Width",      "Create a linear dimension measuring 300mm width between Left and Right reference planes"),
            (200,  "Depth",      "Create a linear dimension measuring 200mm depth between Front and Back reference planes"),
            (2400, "Height",     "Create a linear dimension measuring 2400mm height between Bottom and Top reference planes"),
            (600,  "Span",       "Create a linear dimension measuring 600mm span between two reference planes"),
            (150,  "Offset",     "Create a linear dimension measuring 150mm offset between a reference plane and an edge"),
            (900,  "DoorWidth",  "Create a linear dimension measuring 900mm door width between jamb reference planes"),
            (2100, "DoorHeight", "Create a linear dimension measuring 2100mm door height between sill and head reference planes"),
            (450,  "ColumnB",    "Create a linear dimension measuring 450mm column flange width"),
            (75,   "WebThick",   "Create a linear dimension measuring 75mm web thickness between web reference planes"),
            (1200, "WindowW",    "Create a linear dimension measuring 1200mm window width"),
            (1000, "WindowH",    "Create a linear dimension measuring 1000mm window height"),
            (25,   "Plate",      "Create a linear dimension measuring 25mm base plate thickness"),
            (3000, "BeamSpan",   "Create a linear dimension measuring 3000mm beam span"),
        ]
        for dist_mm, label, instruction in basic_cases:
            dist_ft = dist_mm * MM_TO_FT
            half_ft = dist_ft / 2
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;

// Linear dimension: {label} = {dist_mm} mm between two reference planes
using (Transaction tx = new Transaction(familyDoc, "Add Linear Dimension"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;

    // Retrieve the two bounding reference planes
    ReferencePlane rpA = /* left/front/bottom reference plane */;
    ReferencePlane rpB = /* right/back/top reference plane */;

    // Dimension line runs parallel to the planes being measured
    // For vertical planes (Left/Right): dim line is horizontal
    Line dimLine = Line.CreateBound(
        new XYZ(-{half_ft:.6f}, -{half_ft:.6f}, 0),
        new XYZ( {half_ft:.6f},  {half_ft:.6f}, 0));

    ReferenceArray refs = new ReferenceArray();
    refs.Append(rpA.GetReference());
    refs.Append(rpB.GetReference());

    Dimension dim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView, dimLine, refs);

    tx.Commit();
}}"""))

        # Dimension with explicit line direction (horizontal vs vertical)
        dir_cases = [
            ("horizontal", "XYZ.BasisX", 400, 0,
             "Create a horizontal linear dimension between two vertical reference planes 400mm apart"),
            ("vertical",   "XYZ.BasisY", 0,   600,
             "Create a vertical linear dimension between two horizontal reference planes 600mm apart"),
        ]
        for dir_label, basis, dx_mm, dy_mm, instruction in dir_cases:
            dx_ft = dx_mm * MM_TO_FT
            dy_ft = dy_mm * MM_TO_FT
            dist_mm = dx_mm if dx_mm > 0 else dy_mm
            dist_ft = dist_mm * MM_TO_FT
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;

// {dir_label.capitalize()} linear dimension: {dist_mm} mm
using (Transaction tx = new Transaction(familyDoc, "Add {dir_label.capitalize()} Dimension"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;

    ReferencePlane rpA = /* first reference plane */;
    ReferencePlane rpB = /* second reference plane */;

    // Dimension line direction: {dir_label}
    Line dimLine = Line.CreateBound(
        new XYZ(-{dist_ft:.6f}, -{dist_ft:.6f}, 0),
        new XYZ( {dist_ft:.6f},  {dist_ft:.6f}, 0));

    ReferenceArray refs = new ReferenceArray();
    refs.Append(rpA.GetReference());
    refs.Append(rpB.GetReference());

    Dimension dim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView, dimLine, refs);

    tx.Commit();
}}"""))

        # Multi-segment dimension (chain of 3+ reference planes)
        chain_cases = [
            ([100, 200, 100], "Create a chain dimension across three reference planes: 100mm, 200mm, 100mm spacing"),
            ([150, 150, 150], "Create an equal-spacing chain dimension with three 150mm segments"),
            ([200, 300, 200], "Create a chain dimension with segments 200mm, 300mm, 200mm"),
            ([300, 300, 300], "Create a chain dimension with three equal 300mm segments for a modular grid"),
            ([50, 100, 150, 100, 50], "Create a five-segment chain dimension: 50, 100, 150, 100, 50 mm"),
            ([600, 600], "Create a two-segment chain dimension, each segment 600mm"),
        ]
        for gaps_mm, instruction in chain_cases:
            positions_ft = []
            pos = 0.0
            for g in gaps_mm:
                pos += g * MM_TO_FT
                positions_ft.append(pos)
            total_ft = sum(g * MM_TO_FT for g in gaps_mm)
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;

// Chain dimension across {len(gaps_mm) + 1} reference planes
// Gaps: {gaps_mm} mm
using (Transaction tx = new Transaction(familyDoc, "Add Chain Dimension"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;

    // Place reference planes at cumulative positions
    double[] positions = {{ 0.0, {", ".join(f"{p:.6f}" for p in positions_ft)} }};
    ReferencePlane[] planes = new ReferencePlane[{len(gaps_mm) + 1}];

    for (int i = 0; i < positions.Length; i++)
    {{
        planes[i] = familyDoc.FamilyCreate.NewReferencePlane(
            new XYZ(positions[i], 0, 0),
            new XYZ(positions[i], 1, 0),
            XYZ.BasisZ,
            activeView);
        planes[i].Name = $"ChainPlane_{{i}}";
    }}

    // Build reference array (all planes in order)
    ReferenceArray refs = new ReferenceArray();
    foreach (ReferencePlane rp in planes)
        refs.Append(rp.GetReference());

    // Dim line offset above origin
    double midX = {total_ft / 2:.6f};
    Line dimLine = Line.CreateBound(
        new XYZ(0, {0.2:.6f}, 0),
        new XYZ({total_ft:.6f}, {0.2:.6f}, 0));

    Dimension chainDim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView, dimLine, refs);

    tx.Commit();
}}"""))

        # Dimension between extrusion face and reference plane
        samples.append(_s(
            "Create a linear dimension from an extrusion face reference to a reference plane",
            f"""\
using Autodesk.Revit.DB;

// Dimension from geometry face to reference plane
using (Transaction tx = new Transaction(familyDoc, "Dimension Face to Plane"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;

    // Assume extrusion and reference plane already exist
    Extrusion ext = /* previously created extrusion */;
    ReferencePlane rp  = /* target reference plane */;

    // Get face reference from the extrusion geometry
    Options geomOpts = new Options {{ ComputeReferences = true, View = activeView }};
    GeometryElement geomElem = ext.get_Geometry(geomOpts);

    Reference faceRef = null;
    foreach (GeometryObject obj in geomElem)
    {{
        Solid solid = obj as Solid;
        if (solid == null) continue;
        foreach (Face face in solid.Faces)
        {{
            // Pick the face whose normal points in -X direction (left face)
            if (face.ComputeNormal(new UV(0.5, 0.5)).IsAlmostEqualTo(-XYZ.BasisX))
            {{
                faceRef = face.Reference;
                break;
            }}
        }}
        if (faceRef != null) break;
    }}

    if (faceRef != null)
    {{
        ReferenceArray refs = new ReferenceArray();
        refs.Append(faceRef);
        refs.Append(rp.GetReference());

        Line dimLine = Line.CreateBound(
            new XYZ(-{_ft(400)}, {_ft(100)}, 0),
            new XYZ( {_ft(400)}, {_ft(100)}, 0));

        Dimension dim = familyDoc.FamilyCreate.NewLinearDimension(
            activeView, dimLine, refs);
    }}

    tx.Commit();
}}"""))

        # Dimension placement offset
        samples.append(_s(
            "Create a linear dimension and position the dimension line 50mm above the measured elements",
            f"""\
using Autodesk.Revit.DB;

// Dimension line is offset from geometry so text does not overlap
using (Transaction tx = new Transaction(familyDoc, "Offset Dimension Line"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;

    ReferencePlane rpLeft  = /* left reference plane */;
    ReferencePlane rpRight = /* right reference plane */;

    // Offset dimension line 50mm (= {_ft(50)} ft) above measured geometry
    double offsetFt = {_ft(50)}; // 50 mm
    Line dimLine = Line.CreateBound(
        new XYZ(-{_ft(500)}, offsetFt, 0),
        new XYZ( {_ft(500)}, offsetFt, 0));

    ReferenceArray refs = new ReferenceArray();
    refs.Append(rpLeft.GetReference());
    refs.Append(rpRight.GetReference());

    Dimension dim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView, dimLine, refs);

    tx.Commit();
}}"""))

        # Retrieve dimension value
        samples.append(_s(
            "Read the current value of an existing linear dimension in feet and convert to mm",
            """\
using Autodesk.Revit.DB;

// Dimension.Value returns feet; convert to mm for display
Dimension dim = /* previously created dimension */;

if (dim.Value.HasValue)
{
    double valueInFeet = dim.Value.Value;
    double valueInMm   = valueInFeet * 304.8;
    TaskDialog.Show("Dimension", $"Value: {valueInMm:F1} mm ({valueInFeet:F6} ft)");
}"""))

        # Delete a dimension
        samples.append(_s(
            "Delete a linear dimension element from the family document",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Delete Dimension"))
{
    tx.Start();

    Dimension dim = /* dimension to remove */;
    familyDoc.Delete(dim.Id);

    tx.Commit();
}"""))

        # Additional targeted linear dimension cases
        extra_linear = [
            ("top edge to head reference plane", "Top", "Dimension the top edge of an extrusion to the 'Top' reference plane to verify alignment"),
            ("bottom edge to Ref. Level", "Ref. Level", "Dimension the bottom edge of an extrusion to the 'Ref. Level' reference plane"),
            ("left edge to center plane", "Center (Left/Right)", "Dimension the left extrusion edge to the center reference plane for a half-width check"),
        ]
        for edge_desc, plane_name, instruction in extra_linear:
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;
using System.Linq;

// Linear dimension: {edge_desc} to '{plane_name}'
using (Transaction tx = new Transaction(familyDoc, "Dimension Edge to Plane"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    Extrusion ext = /* previously created extrusion */;
    ReferencePlane rp = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "{plane_name}");

    Options opts = new Options {{ ComputeReferences = true, View = activeView }};
    Reference edgeRef = null;
    foreach (GeometryObject obj in ext.get_Geometry(opts))
    {{
        Solid solid = obj as Solid;
        if (solid == null) continue;
        foreach (Face face in solid.Faces)
        {{
            XYZ n = face.ComputeNormal(new UV(0.5, 0.5));
            if (n.IsAlmostEqualTo(rp.Normal) || n.IsAlmostEqualTo(-rp.Normal))
            {{ edgeRef = face.Reference; break; }}
        }}
        if (edgeRef != null) break;
    }}

    if (edgeRef != null)
    {{
        ReferenceArray refs = new ReferenceArray();
        refs.Append(edgeRef);
        refs.Append(rp.GetReference());
        Line dimLine = Line.CreateBound(
            new XYZ(-{_ft(400)}, {_ft(80)}, 0),
            new XYZ( {_ft(400)}, {_ft(80)}, 0));
        familyDoc.FamilyCreate.NewLinearDimension(activeView, dimLine, refs);
    }}

    tx.Commit();
}}"""))

        # Dimension from a model line to a reference plane
        samples.append(_s(
            "Create a linear dimension from a model line to a reference plane in a family elevation view",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "Model Line to Plane Dim"))
{{
    tx.Start();

    View elevView = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(View))
        .Cast<View>()
        .FirstOrDefault(v => v.ViewType == ViewType.Elevation);
    if (elevView == null) {{ tx.Commit(); return; }}

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // Horizontal model line at 1500 mm
    ModelCurve mc = familyDoc.FamilyCreate.NewModelCurveArray(
        new CurveArray() {{ }}, sp) is ModelCurveArray mca ? null :
        familyDoc.FamilyCreate.NewModelCurve(
            Line.CreateBound(new XYZ(-{_ft(300)}, 0, {_ft(1500)}),
                             new XYZ( {_ft(300)}, 0, {_ft(1500)})), sp);

    ReferencePlane rpBase = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "Ref. Level");

    if (mc != null)
    {{
        ReferenceArray refs = new ReferenceArray();
        refs.Append(mc.GeometryCurve.Reference);
        refs.Append(rpBase.GetReference());
        Line dimLine = Line.CreateBound(
            new XYZ({_ft(60)}, 0, 0),
            new XYZ({_ft(60)}, 0, {_ft(1600)}));
        familyDoc.FamilyCreate.NewLinearDimension(elevView, dimLine, refs);
    }}

    tx.Commit();
}}"""))

        # Retrieve all unlabeled dimensions
        samples.append(_s(
            "List all unlabeled linear dimensions in the family document",
            """\
using Autodesk.Revit.DB;
using System.Linq;

IList<Dimension> unlabeled = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(Dimension))
    .Cast<Dimension>()
    .Where(d => d.FamilyLabel == null)
    .ToList();

TaskDialog.Show("Unlabeled Dims",
    $"Found {unlabeled.Count} unlabeled dimension(s).");"""))

        # Dimension using explicit ReferenceArray with three elements (overall + sub-dim)
        samples.append(_s(
            "Create a linear dimension that shows both overall width and the two half-width segments simultaneously",
            f"""\
using Autodesk.Revit.DB;

// Three-plane dimension: Left -- Center -- Right gives both halves + overall
using (Transaction tx = new Transaction(familyDoc, "Overall + Half Dims"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;

    ReferencePlane rpL = /* Width_Left reference plane */;
    ReferencePlane rpC = /* Center (Left/Right) reference plane */;
    ReferencePlane rpR = /* Width_Right reference plane */;

    ReferenceArray refs = new ReferenceArray();
    refs.Append(rpL.GetReference());
    refs.Append(rpC.GetReference());
    refs.Append(rpR.GetReference());

    // Dimension line offset above geometry
    Line dimLine = Line.CreateBound(
        new XYZ(-{_ft(500)}, {_ft(100)}, 0),
        new XYZ( {_ft(500)}, {_ft(100)}, 0));

    Dimension dim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView, dimLine, refs);
    // dim.Segments[0] = left half, dim.Segments[1] = right half
    // dim.Value = overall width

    tx.Commit();
}}"""))

        # Dimension type (DimensionType) assignment
        samples.append(_s(
            "Assign a specific DimensionType (dimension style) to a newly created linear dimension",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "Apply Dimension Style"))
{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    ReferencePlane rpA = /* first reference plane */;
    ReferencePlane rpB = /* second reference plane */;

    ReferenceArray refs = new ReferenceArray();
    refs.Append(rpA.GetReference());
    refs.Append(rpB.GetReference());

    Dimension dim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView,
        Line.CreateBound(new XYZ(-1, 0.1, 0), new XYZ(1, 0.1, 0)),
        refs);

    // Find a DimensionType by name and apply it
    DimensionType dimType = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(DimensionType))
        .Cast<DimensionType>()
        .FirstOrDefault(dt => dt.Name.Contains("Linear"));

    if (dim != null && dimType != null)
        dim.ChangeTypeId(dimType.Id);

    tx.Commit();
}"""))

        # Suppress a dimension (use in construction only)
        samples.append(_s(
            "Create a linear dimension marked as a 'reference dimension' (not for fabrication) using DimensionShape",
            """\
using Autodesk.Revit.DB;

// Reference dimensions are visual only and do not constrain geometry.
// In Revit API, all NewLinearDimension calls create reference dimensions by default
// in family editor context -- they do not add parametric constraints by themselves.
// To make them parametric, assign FamilyLabel.
//
// To create a truly non-constraining reference dim (for documentation only),
// simply do NOT assign FamilyLabel:

using (Transaction tx = new Transaction(familyDoc, "Reference Dimension"))
{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    ReferencePlane rpA = /* first reference plane */;
    ReferencePlane rpB = /* second reference plane */;

    ReferenceArray refs = new ReferenceArray();
    refs.Append(rpA.GetReference());
    refs.Append(rpB.GetReference());

    Dimension dim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView,
        Line.CreateBound(new XYZ(-1, 0.05, 0), new XYZ(1, 0.05, 0)),
        refs);

    // Do NOT set dim.FamilyLabel -- this is a reference-only dimension.

    tx.Commit();
}"""))

        # Dimension.NumberOfSegments property
        samples.append(_s(
            "Read the number of segments in a multi-reference dimension to determine if it is a chain dimension",
            """\
using Autodesk.Revit.DB;

Dimension dim = /* target dimension */;

int segCount = dim.NumberOfSegments;
if (segCount > 1)
{
    TaskDialog.Show("Chain Dim",
        $"This is a chain dimension with {segCount} segments.");

    // Iterate segment values
    DimensionSegmentArray segs = dim.Segments;
    for (int i = 0; i < segs.Size; i++)
    {
        double segMm = segs.get_Item(i).Value.GetValueOrDefault() * 304.8;
        TaskDialog.Show($"Segment {i}", $"Value: {segMm:F1} mm");
    }
}
else
{
    TaskDialog.Show("Single Dim",
        $"Single-segment dimension: {dim.Value.GetValueOrDefault() * 304.8:F1} mm");
}"""))

        # Dimension between two extrusion sketch lines
        extra_dim_cases = [
            ("front extrusion edge", "Front", "Dimension the front sketch edge of an extrusion to the 'Front' reference plane in a plan view"),
            ("right extrusion edge", "Right", "Dimension the right sketch edge of an extrusion to the 'Right' reference plane"),
            ("a void extrusion boundary", "Opening_Left", "Dimension the left boundary of a void extrusion to the 'Opening_Left' reference plane"),
        ]
        for edge_desc, plane_name, instruction in extra_dim_cases:
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;
using System.Linq;

// Dimension {edge_desc} to '{plane_name}' reference plane
using (Transaction tx = new Transaction(familyDoc, "Sketch Edge Dimension"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    Extrusion ext = /* target extrusion */;
    ReferencePlane rp = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "{plane_name}");

    Options opts = new Options {{ ComputeReferences = true, View = activeView }};
    Reference edgeRef = null;
    foreach (GeometryObject obj in ext.get_Geometry(opts))
    {{
        Solid s = obj as Solid; if (s == null) continue;
        foreach (Face face in s.Faces)
        {{
            XYZ n = face.ComputeNormal(new UV(0.5, 0.5));
            if (n.IsAlmostEqualTo(rp.Normal) || n.IsAlmostEqualTo(-rp.Normal))
            {{ edgeRef = face.Reference; break; }}
        }}
        if (edgeRef != null) break;
    }}

    if (edgeRef != null)
    {{
        ReferenceArray refs = new ReferenceArray();
        refs.Append(rp.GetReference());
        refs.Append(edgeRef);

        Line dimLine = Line.CreateBound(
            new XYZ(-{_ft(400)}, {_ft(80)}, 0),
            new XYZ( {_ft(400)}, {_ft(80)}, 0));
        familyDoc.FamilyCreate.NewLinearDimension(activeView, dimLine, refs);
    }}

    tx.Commit();
}}"""))

        # Dimension line position relative to geometry
        samples.append(_s(
            "Position a dimension line 100mm offset from the measured geometry to avoid overlapping with extrusion edges",
            f"""\
using Autodesk.Revit.DB;

// Dimension line offset: place dimLine 100mm (= {_ft(100)} ft) away from geometry
using (Transaction tx = new Transaction(familyDoc, "Offset Dim Line"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    ReferencePlane rpL = /* left reference plane */;
    ReferencePlane rpR = /* right reference plane */;

    double offsetFt = {_ft(100)}; // 100 mm

    ReferenceArray refs = new ReferenceArray();
    refs.Append(rpL.GetReference());
    refs.Append(rpR.GetReference());

    // Move dim line above the geometry by the offset amount
    Line dimLine = Line.CreateBound(
        new XYZ(-{_ft(600)}, offsetFt, 0),
        new XYZ( {_ft(600)}, offsetFt, 0));

    Dimension dim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView, dimLine, refs);

    tx.Commit();
}}"""))

        # Dimension suffix/prefix (DimensionType settings)
        samples.append(_s(
            "Set a dimension type prefix to 'W=' for all width dimensions in a family document",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "Set Dim Prefix"))
{
    tx.Start();

    // Find or create a DimensionType for width dimensions
    DimensionType widthType = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(DimensionType))
        .Cast<DimensionType>()
        .FirstOrDefault(dt => dt.Name == "Width_Style");

    if (widthType == null)
    {
        // Duplicate the default linear dimension type
        DimensionType defaultType = new FilteredElementCollector(familyDoc)
            .OfClass(typeof(DimensionType))
            .Cast<DimensionType>()
            .First();
        widthType = defaultType.Duplicate("Width_Style") as DimensionType;
    }

    // Set prefix parameter
    widthType.get_Parameter(BuiltInParameter.DIM_STYLE_DIM_LINE_EXTENSION)
        ?.Set(0); // example: no extension

    tx.Commit();
}"""))

        # Total sample count validation
        samples.append(_s(
            "List all dimensions in the family document grouped by whether they have a FamilyLabel",
            """\
using Autodesk.Revit.DB;
using System.Linq;

var allDims = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(Dimension))
    .Cast<Dimension>()
    .ToList();

var labeled   = allDims.Where(d => d.FamilyLabel != null).ToList();
var unlabeled = allDims.Where(d => d.FamilyLabel == null).ToList();

TaskDialog.Show("Dimension Audit",
    $"Total:     {allDims.Count}\\n" +
    $"Labeled:   {labeled.Count}\\n" +
    $"Unlabeled: {unlabeled.Count}\\n\\n" +
    string.Join("\\n", labeled.Select(d =>
        $"  {d.Id.IntegerValue}: {d.FamilyLabel.Definition.Name}")));"""))

        # Retrieve a specific dimension by its label parameter name
        samples.append(_s(
            "Find the dimension that is labeled with the 'Width' parameter",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth = famMgr.LookupParameter("Width");

Dimension widthDim = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(Dimension))
    .Cast<Dimension>()
    .FirstOrDefault(d => d.FamilyLabel != null &&
                         d.FamilyLabel.Id == pWidth?.Id);

if (widthDim != null)
    TaskDialog.Show("Found", $"Width dimension Id: {widthDim.Id.IntegerValue}");
else
    TaskDialog.Show("Not Found", "No dimension labeled 'Width' found.");"""))

        return samples

    # ------------------------------------------------------------------
    # Angular dimensions
    # ------------------------------------------------------------------

    def _angular_dimensions(self) -> List[SAMPLE]:
        samples = []

        # Basic angular dimension between two reference planes
        angle_cases = [
            (30,  "Create an angular dimension of 30 degrees between two reference planes"),
            (45,  "Create a 45-degree angular dimension between two angled reference planes"),
            (60,  "Create a 60-degree angular dimension between intersecting reference planes"),
            (90,  "Create a right-angle (90-degree) angular dimension between perpendicular planes"),
            (120, "Create a 120-degree angular dimension between reference planes"),
            (15,  "Create a 15-degree angular dimension for a shallow brace"),
            (22,  "Create a 22.5-degree angular dimension between two reference lines"),
            (135, "Create a 135-degree obtuse angular dimension between reference planes"),
            (150, "Create a 150-degree angular dimension for a shallow hip roof pitch"),
            (75,  "Create a 75-degree angular dimension between two steep reference lines"),
            (20,  "Create a 20-degree angular dimension for a sloped surface family"),
            (36,  "Create a 36-degree angular dimension for a pentagonal feature"),
        ]
        for angle_deg, instruction in angle_cases:
            angle_rad = math.radians(angle_deg)
            arm_ft = _ft(300)
            ex = 300 * math.cos(angle_rad) * MM_TO_FT
            ey = 300 * math.sin(angle_rad) * MM_TO_FT
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;

// Angular dimension: {angle_deg} degrees between two reference lines/planes
using (Transaction tx = new Transaction(familyDoc, "Add Angular Dimension"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // First arm: along X axis
    ReferenceLine rl1 = familyDoc.FamilyCreate.NewReferenceLine(
        Line.CreateBound(XYZ.Zero, new XYZ({arm_ft}, 0, 0)), sp);

    // Second arm: at {angle_deg} degrees from X axis
    ReferenceLine rl2 = familyDoc.FamilyCreate.NewReferenceLine(
        Line.CreateBound(XYZ.Zero, new XYZ({ex:.6f}, {ey:.6f}, 0)), sp);

    ReferenceArray refs = new ReferenceArray();
    refs.Append(rl1.GeometryCurve.Reference);
    refs.Append(rl2.GeometryCurve.Reference);

    // Arc for the dimension display, passing through the angle bisector
    double bisect = {math.radians(angle_deg / 2):.6f}; // {angle_deg / 2} deg
    double arcR   = {_ft(100)};
    Arc dimArc = Arc.Create(
        XYZ.Zero, arcR, 0, {angle_rad:.6f}, XYZ.BasisX, XYZ.BasisY);

    Dimension angDim = familyDoc.FamilyCreate.NewAngularDimension(
        activeView, dimArc, refs);

    tx.Commit();
}}"""))

        # Angular dimension between a reference plane and geometry edge
        samples.append(_s(
            "Create an angular dimension between a reference plane and an extrusion edge",
            f"""\
using Autodesk.Revit.DB;

// Angular dimension from ref plane to a geometry edge
using (Transaction tx = new Transaction(familyDoc, "Angular Dim Plane to Edge"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // Reference line representing the reference plane direction
    ReferenceLine rl = familyDoc.FamilyCreate.NewReferenceLine(
        Line.CreateBound(XYZ.Zero, new XYZ({_ft(400)}, 0, 0)), sp);

    // Get edge reference from extrusion geometry
    Extrusion ext = /* previously created extrusion */;
    Options opts = new Options {{ ComputeReferences = true }};
    Reference edgeRef = null;
    foreach (GeometryObject obj in ext.get_Geometry(opts))
    {{
        Solid s = obj as Solid;
        if (s == null) continue;
        foreach (Edge e in s.Edges)
        {{
            edgeRef = e.Reference;
            break;
        }}
        if (edgeRef != null) break;
    }}

    if (edgeRef != null)
    {{
        ReferenceArray refs = new ReferenceArray();
        refs.Append(rl.GeometryCurve.Reference);
        refs.Append(edgeRef);

        Arc dimArc = Arc.Create(XYZ.Zero, {_ft(150)},
            0, {math.radians(45):.6f}, XYZ.BasisX, XYZ.BasisY);

        Dimension angDim = familyDoc.FamilyCreate.NewAngularDimension(
            activeView, dimArc, refs);
    }}

    tx.Commit();
}}"""))

        # Angular dimension with label
        samples.append(_s(
            "Create an angular dimension and label it with an Angle family parameter",
            f"""\
using Autodesk.Revit.DB;

// Step 1: Add Angle parameter (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pAngle = famMgr.AddParameter(
    "Angle",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Angle,
    false); // type parameter

famMgr.Set(pAngle, {math.radians(45):.6f}); // 45 degrees default

// Step 2: Create reference lines and angular dimension
using (Transaction tx = new Transaction(familyDoc, "Labeled Angular Dim"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    ReferenceLine rl1 = familyDoc.FamilyCreate.NewReferenceLine(
        Line.CreateBound(XYZ.Zero, new XYZ({_ft(300)}, 0, 0)), sp);
    ReferenceLine rl2 = familyDoc.FamilyCreate.NewReferenceLine(
        Line.CreateBound(XYZ.Zero, new XYZ({300 * math.cos(math.radians(45)) * MM_TO_FT:.6f},
                                           {300 * math.sin(math.radians(45)) * MM_TO_FT:.6f}, 0)), sp);

    ReferenceArray refs = new ReferenceArray();
    refs.Append(rl1.GeometryCurve.Reference);
    refs.Append(rl2.GeometryCurve.Reference);

    Arc dimArc = Arc.Create(XYZ.Zero, {_ft(100)},
        0, {math.radians(45):.6f}, XYZ.BasisX, XYZ.BasisY);

    Dimension angDim = familyDoc.FamilyCreate.NewAngularDimension(
        activeView, dimArc, refs);

    // Label the dimension with the Angle parameter
    if (angDim != null && angDim.IsReferencesValidForLabel())
        angDim.FamilyLabel = pAngle;

    tx.Commit();
}}"""))

        # Read angular dimension value
        samples.append(_s(
            "Read the value of an angular dimension and convert from radians to degrees",
            """\
using Autodesk.Revit.DB;
using System;

// Angular dimension value is stored in radians
Dimension angDim = /* previously created angular dimension */;

if (angDim.Value.HasValue)
{
    double radians = angDim.Value.Value;
    double degrees = radians * (180.0 / Math.PI);
    TaskDialog.Show("Angle", $"Angle: {degrees:F2} degrees ({radians:F6} rad)");
}"""))

        # Multi-reference angular dimension (three reference lines = two angles)
        samples.append(_s(
            "Create an angular dimension across three reference lines to display two consecutive angle segments",
            f"""\
using Autodesk.Revit.DB;

// Three reference lines produce a two-segment angular dimension
using (Transaction tx = new Transaction(familyDoc, "Multi-Arm Angular Dim"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    ReferenceLine rl1 = familyDoc.FamilyCreate.NewReferenceLine(
        Line.CreateBound(XYZ.Zero, new XYZ({_ft(300)}, 0, 0)), sp);
    ReferenceLine rl2 = familyDoc.FamilyCreate.NewReferenceLine(
        Line.CreateBound(XYZ.Zero, new XYZ({300*math.cos(math.radians(45))*MM_TO_FT:.6f},
                                           {300*math.sin(math.radians(45))*MM_TO_FT:.6f}, 0)), sp);
    ReferenceLine rl3 = familyDoc.FamilyCreate.NewReferenceLine(
        Line.CreateBound(XYZ.Zero, new XYZ(0, {_ft(300)}, 0)), sp);

    ReferenceArray refs = new ReferenceArray();
    refs.Append(rl1.GeometryCurve.Reference);
    refs.Append(rl2.GeometryCurve.Reference);
    refs.Append(rl3.GeometryCurve.Reference);

    Arc dimArc = Arc.Create(XYZ.Zero, {_ft(120)}, 0, {math.radians(90):.6f}, XYZ.BasisX, XYZ.BasisY);
    Dimension angDim = familyDoc.FamilyCreate.NewAngularDimension(
        activeView, dimArc, refs);

    tx.Commit();
}}"""))

        # Angular dim for a hip roof pitch
        for pitch_deg, pitch_label in [(18, "low hip 18-degree pitch"), (30, "medium hip 30-degree pitch"), (45, "steep hip 45-degree pitch")]:
            pr = math.radians(pitch_deg)
            samples.append(_s(
                f"Create an angular dimension for a {pitch_label} between a horizontal reference line and a sloped reference line",
                f"""\
using Autodesk.Revit.DB;

// Angular dimension for roof pitch: {pitch_deg} degrees
using (Transaction tx = new Transaction(familyDoc, "Roof Pitch Angular Dim"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    // Horizontal eave line
    ReferenceLine eave = familyDoc.FamilyCreate.NewReferenceLine(
        Line.CreateBound(XYZ.Zero, new XYZ({_ft(600)}, 0, 0)), sp);

    // Sloped ridge line at {pitch_deg} degrees
    ReferenceLine ridge = familyDoc.FamilyCreate.NewReferenceLine(
        Line.CreateBound(XYZ.Zero, new XYZ({600*math.cos(pr)*MM_TO_FT:.6f}, 0,
                                           {600*math.sin(pr)*MM_TO_FT:.6f})), sp);

    ReferenceArray refs = new ReferenceArray();
    refs.Append(eave.GeometryCurve.Reference);
    refs.Append(ridge.GeometryCurve.Reference);

    Arc dimArc = Arc.Create(XYZ.Zero, {_ft(100)}, 0, {pr:.6f}, XYZ.BasisX, XYZ.BasisZ);
    Dimension pitchDim = familyDoc.FamilyCreate.NewAngularDimension(
        activeView, dimArc, refs);

    tx.Commit();
}}"""))

        # Delete an angular dimension
        samples.append(_s(
            "Delete an angular dimension that is no longer needed after constraints are established",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Delete Angular Dim"))
{
    tx.Start();

    Dimension angDim = /* angular dimension to remove */;
    familyDoc.Delete(angDim.Id);

    tx.Commit();
}"""))

        # Angular dim for a brace family
        samples.append(_s(
            "Create an angular dimension for a diagonal brace family at 60 degrees from horizontal, labeled with an 'Inclination' angle parameter",
            f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pAngle = famMgr.AddParameter(
    "Inclination",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Angle,
    false);
famMgr.Set(pAngle, {math.radians(60):.6f}); // 60 degrees

using (Transaction tx = new Transaction(familyDoc, "Brace Inclination Dim"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    double len = {_ft(500)};
    ReferenceLine horiz = familyDoc.FamilyCreate.NewReferenceLine(
        Line.CreateBound(XYZ.Zero, new XYZ(len, 0, 0)), sp);
    ReferenceLine brace = familyDoc.FamilyCreate.NewReferenceLine(
        Line.CreateBound(XYZ.Zero,
            new XYZ({500*math.cos(math.radians(60))*MM_TO_FT:.6f},
                    {500*math.sin(math.radians(60))*MM_TO_FT:.6f}, 0)), sp);

    ReferenceArray refs = new ReferenceArray();
    refs.Append(horiz.GeometryCurve.Reference);
    refs.Append(brace.GeometryCurve.Reference);

    Arc dimArc = Arc.Create(XYZ.Zero, {_ft(100)},
        0, {math.radians(60):.6f}, XYZ.BasisX, XYZ.BasisY);

    Dimension angDim = familyDoc.FamilyCreate.NewAngularDimension(
        activeView, dimArc, refs);

    if (angDim != null && angDim.IsReferencesValidForLabel())
        angDim.FamilyLabel = pAngle;

    tx.Commit();
}}"""))

        # Reference line with non-default sketch plane (vertical)
        samples.append(_s(
            "Create a reference line in a vertical sketch plane (Front elevation) for a height-related angular dimension",
            f"""\
using Autodesk.Revit.DB;

// Reference line in XZ plane (vertical) for elevation angular dims
using (Transaction tx = new Transaction(familyDoc, "Vertical Reference Line"))
{{
    tx.Start();

    // Sketch plane in XZ (normal = Y)
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    // 45-degree line rising from origin in elevation
    double len = {_ft(400)};
    double angle45 = {math.radians(45):.6f};
    ReferenceLine rl = familyDoc.FamilyCreate.NewReferenceLine(
        Line.CreateBound(XYZ.Zero, new XYZ(len * {math.cos(math.radians(45)):.6f}, 0,
                                           len * {math.sin(math.radians(45)):.6f})), sp);

    tx.Commit();
}}"""))

        # Duplicate reference line check
        samples.append(_s(
            "Check for duplicate reference lines at the same position before creating a new one",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

// Avoid duplicate reference lines by checking existing ones first
XYZ ptStart = XYZ.Zero;
XYZ ptEnd   = new XYZ({_ft(300)}, 0, 0);
double tol  = 0.001; // feet

bool alreadyExists = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(ReferenceLine))
    .Cast<ReferenceLine>()
    .Any(rl =>
    {{
        Line l = rl.GeometryCurve as Line;
        return l != null &&
               l.GetEndPoint(0).DistanceTo(ptStart) < tol &&
               l.GetEndPoint(1).DistanceTo(ptEnd)   < tol;
    }});

if (!alreadyExists)
{{
    using (Transaction tx = new Transaction(familyDoc, "Create Reference Line"))
    {{
        tx.Start();
        SketchPlane sp = SketchPlane.Create(familyDoc,
            Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
        familyDoc.FamilyCreate.NewReferenceLine(Line.CreateBound(ptStart, ptEnd), sp);
        tx.Commit();
    }}
}}"""))

        # Get all reference lines in document
        samples.append(_s(
            "Retrieve all reference lines in the family document and print their start/end points",
            """\
using Autodesk.Revit.DB;
using System.Linq;

IList<ReferenceLine> refLines = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(ReferenceLine))
    .Cast<ReferenceLine>()
    .ToList();

foreach (ReferenceLine rl in refLines)
{
    Line l = rl.GeometryCurve as Line;
    if (l != null)
    {
        XYZ s = l.GetEndPoint(0);
        XYZ e = l.GetEndPoint(1);
        TaskDialog.Show("Reference Line",
            $"Start: ({s.X:F4}, {s.Y:F4}, {s.Z:F4}) ft\\n" +
            $"End:   ({e.X:F4}, {e.Y:F4}, {e.Z:F4}) ft");
    }
}"""))

        return samples

    # ------------------------------------------------------------------
    # Equality constraints
    # ------------------------------------------------------------------

    def _equality_constraints(self) -> List[SAMPLE]:
        samples = []

        # Equal constraint on two reference planes via dimension
        equal_cases = [
            ("Left",       "Right",       "Center (Left/Right)",
             "Create an EqualConstraint so Left and Right reference planes remain equidistant from center"),
            ("Front",      "Back",        "Center (Front/Back)",
             "Create an EqualConstraint keeping Front and Back reference planes symmetric about center"),
            ("Flange_Left","Flange_Right","Center (Left/Right)",
             "Apply an EqualConstraint to keep flange reference planes symmetric"),
            ("Width_Left", "Width_Right", "Center (Left/Right)",
             "Apply EqualConstraint to Width_Left and Width_Right reference planes about center"),
            ("Door_Left",  "Door_Right",  "Door_Center",
             "Apply EqualConstraint to Door_Left and Door_Right planes about the door center"),
            ("Web_Left",   "Web_Right",   "Center (Left/Right)",
             "Apply EqualConstraint to Web_Left and Web_Right reference planes for an I-beam web"),
        ]
        for name_a, name_b, name_center, instruction in equal_cases:
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;
using System.Linq;

// EqualConstraint requires a dimension that spans center + both planes
using (Transaction tx = new Transaction(familyDoc, "Add Equal Constraint"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;

    // Retrieve the three reference planes
    ReferencePlane rpA = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "{name_a}");
    ReferencePlane rpB = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "{name_b}");
    ReferencePlane rpCenter = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "{name_center}");

    // Build 3-plane reference array: A -- Center -- B
    ReferenceArray refs = new ReferenceArray();
    refs.Append(rpA.GetReference());
    refs.Append(rpCenter.GetReference());
    refs.Append(rpB.GetReference());

    Line dimLine = Line.CreateBound(
        new XYZ(-{_ft(500)}, {_ft(50)}, 0),
        new XYZ( {_ft(500)}, {_ft(50)}, 0));

    Dimension dim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView, dimLine, refs);

    // Apply the equal constraint to the dimension segments
    if (dim != null)
        dim.AreSegmentsEqual = true;

    tx.Commit();
}}"""))

        # Equal constraint via EqualConstraint API
        samples.append(_s(
            "Use the EqualConstraint API to programmatically enforce equality between two dimension segments",
            """\
using Autodesk.Revit.DB;

// After creating a multi-segment dimension, enable equality
using (Transaction tx = new Transaction(familyDoc, "Enable EqualConstraint"))
{
    tx.Start();

    Dimension dim = /* 3-plane or multi-segment dimension */;

    // AreSegmentsEqual = true locks all segments to the same value
    if (dim.NumberOfSegments > 1)
        dim.AreSegmentsEqual = true;

    tx.Commit();
}"""))

        # Remove equality constraint
        samples.append(_s(
            "Remove an existing equal constraint from a dimension to allow asymmetric movement",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Remove Equal Constraint"))
{
    tx.Start();

    Dimension dim = /* dimension with equal constraint */;
    dim.AreSegmentsEqual = false; // removes the equal constraint

    tx.Commit();
}"""))

        # Grid of equal reference planes
        equal_grid_cases = [
            (3, 100, "Create three equally spaced reference planes 100mm apart using EqualConstraint"),
            (4, 150, "Create four reference planes equally spaced 150mm apart"),
            (5, 200, "Create five equally spaced reference planes, 200mm nominal spacing"),
            (3, 300, "Create three reference planes 300mm apart with equal constraint for shelf spacing"),
            (4, 600, "Create four reference planes 600mm apart for a modular panel grid"),
            (6, 50,  "Create six equally spaced reference planes 50mm apart for a fin array"),
            (3, 450, "Create three equally spaced reference planes 450mm apart for a triple bay"),
        ]
        for count, spacing_mm, instruction in equal_grid_cases:
            total_mm = (count - 1) * spacing_mm
            total_ft = total_mm * MM_TO_FT
            positions_ft = [i * spacing_mm * MM_TO_FT for i in range(count)]
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;

// {count} equally spaced reference planes, {spacing_mm} mm nominal spacing
using (Transaction tx = new Transaction(familyDoc, "Equal Grid Planes"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    double[] xPositions = {{ {", ".join(f"{p:.6f}" for p in positions_ft)} }};

    ReferencePlane[] planes = new ReferencePlane[{count}];
    ReferenceArray refs = new ReferenceArray();

    for (int i = 0; i < {count}; i++)
    {{
        planes[i] = familyDoc.FamilyCreate.NewReferencePlane(
            new XYZ(xPositions[i], 0, 0),
            new XYZ(xPositions[i], 1, 0),
            XYZ.BasisZ,
            activeView);
        planes[i].Name = $"GridPlane_{{i}}";
        refs.Append(planes[i].GetReference());
    }}

    // Single dimension spanning all planes
    Line dimLine = Line.CreateBound(
        new XYZ(0, {_ft(80)}, 0),
        new XYZ({total_ft:.6f}, {_ft(80)}, 0));

    Dimension gridDim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView, dimLine, refs);

    // Enforce equal spacing
    if (gridDim != null && gridDim.NumberOfSegments > 1)
        gridDim.AreSegmentsEqual = true;

    tx.Commit();
}}"""))

        # Equal constraint combined with a labeled dimension
        samples.append(_s(
            "Create symmetric reference planes with an equal constraint driven by a Width parameter",
            f"""\
using Autodesk.Revit.DB;

// Step 1: Add Width parameter (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth = famMgr.AddParameter(
    "Width",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length,
    false);
famMgr.Set(pWidth, {_ft(300)}); // 300 mm default

// Step 2: Create planes + dimension with equal constraint
using (Transaction tx = new Transaction(familyDoc, "Symmetric Equal Planes"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    double halfW = {_ft(150)}; // 150 mm

    ReferencePlane rpLeft = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(-halfW, 0, 0), new XYZ(-halfW, 1, 0), XYZ.BasisZ, activeView);
    rpLeft.Name = "Width_Left";

    ReferencePlane rpCenter = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "Center (Left/Right)");

    ReferencePlane rpRight = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(halfW, 0, 0), new XYZ(halfW, 1, 0), XYZ.BasisZ, activeView);
    rpRight.Name = "Width_Right";

    // 3-plane dimension: Left -- Center -- Right
    ReferenceArray refs = new ReferenceArray();
    refs.Append(rpLeft.GetReference());
    refs.Append(rpCenter.GetReference());
    refs.Append(rpRight.GetReference());

    Line dimLine = Line.CreateBound(
        new XYZ(-{_ft(400)}, {_ft(60)}, 0),
        new XYZ( {_ft(400)}, {_ft(60)}, 0));

    Dimension dim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView, dimLine, refs);

    if (dim != null)
    {{
        dim.AreSegmentsEqual = true; // enforce symmetry

        // Also label the overall dimension with Width parameter
        if (dim.IsReferencesValidForLabel())
            dim.FamilyLabel = pWidth;
    }}

    tx.Commit();
}}"""))

        # Check if equal constraint exists
        samples.append(_s(
            "Check whether a dimension has an active equal constraint",
            """\
using Autodesk.Revit.DB;

Dimension dim = /* target dimension */;

bool isEqual = dim.AreSegmentsEqual;
TaskDialog.Show("Constraint",
    isEqual ? "Equal constraint is active." : "No equal constraint.");"""))

        # Enumerate all equality constraints in the document
        samples.append(_s(
            "List all equality constraints (EqualConstraint elements) in the family document",
            """\
using Autodesk.Revit.DB;
using System.Linq;

IList<Element> equalConstraints = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(Dimension))
    .Cast<Dimension>()
    .Where(d => d.AreSegmentsEqual)
    .Cast<Element>()
    .ToList();

TaskDialog.Show("Equal Constraints",
    $"Found {equalConstraints.Count} equal-constrained dimension(s).");"""))

        # Toggle equality on / off based on a YesNo parameter
        samples.append(_s(
            "Toggle AreSegmentsEqual on a dimension based on a 'Symmetric' YesNo family parameter value",
            """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pSym = famMgr.AddParameter(
    "Symmetric",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.YesNo,
    false);
famMgr.Set(pSym, 1); // default symmetric

// Apply initial state to the existing dimension
using (Transaction tx = new Transaction(familyDoc, "Toggle Symmetry"))
{
    tx.Start();

    Dimension dim = /* 3-plane dimension */;
    bool isSymmetric = (famMgr.CurrentType.AsInteger(pSym) == 1);
    dim.AreSegmentsEqual = isSymmetric;

    tx.Commit();
}"""))

        # Equal constraint on a multi-bay grid
        samples.append(_s(
            "Apply AreSegmentsEqual to a 5-plane dimension to create an equal four-bay structural grid",
            f"""\
using Autodesk.Revit.DB;

// Equal four-bay grid: 5 planes, 4 equal segments
using (Transaction tx = new Transaction(familyDoc, "Equal Four-Bay Grid"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    double spacing = {_ft(600)};  // nominal 600 mm

    ReferencePlane[] planes = new ReferencePlane[5];
    ReferenceArray refs = new ReferenceArray();

    for (int i = 0; i < 5; i++)
    {{
        planes[i] = familyDoc.FamilyCreate.NewReferencePlane(
            new XYZ(i * spacing, 0, 0),
            new XYZ(i * spacing, 1, 0),
            XYZ.BasisZ,
            activeView);
        planes[i].Name = $"Bay_{{i}}";
        refs.Append(planes[i].GetReference());
    }}

    double totalFt = 4 * spacing;
    Line dimLine = Line.CreateBound(
        new XYZ(0, {_ft(80)}, 0),
        new XYZ(totalFt, {_ft(80)}, 0));

    Dimension bayDim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView, dimLine, refs);

    if (bayDim != null && bayDim.NumberOfSegments == 4)
        bayDim.AreSegmentsEqual = true;

    tx.Commit();
}}"""))

        # EqualConstraint preserved during regeneration
        samples.append(_s(
            "Verify that an equal constraint is preserved after changing a labeled Width parameter value",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

// After setting Width, regenerate and confirm AreSegmentsEqual is still true
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth = famMgr.LookupParameter("Width");

double[] testWidths = {{ {_ft(200)}, {_ft(400)}, {_ft(600)} }};

foreach (double w in testWidths)
{{
    using (Transaction tx = new Transaction(familyDoc, "Test Equal Constraint"))
    {{
        tx.Start();
        famMgr.Set(pWidth, w);
        familyDoc.Regenerate();

        Dimension dim = new FilteredElementCollector(familyDoc)
            .OfClass(typeof(Dimension))
            .Cast<Dimension>()
            .FirstOrDefault(d => d.AreSegmentsEqual);

        bool ok = dim != null && dim.AreSegmentsEqual;
        TaskDialog.Show("Equal Constraint",
            $"Width={{w * 304.8:F0}} mm  EqualConstraint={{ok}}");

        tx.Commit();
    }}
}}"""))

        # Equal constraint vs labeled dim difference
        samples.append(_s(
            "Explain the difference between AreSegmentsEqual and assigning a FamilyLabel on a dimension",
            """\
using Autodesk.Revit.DB;

// AreSegmentsEqual (EqualConstraint):
//   - Locks multiple dimension segments to the same value.
//   - Does NOT drive an absolute distance -- the family can still flex.
//   - Used for symmetry: forces left half = right half as a ratio.
//   - Cannot be combined with a FamilyLabel on the same multi-segment dimension
//     (the label goes on the outer dimension, the equal constraint on the segments).
//
// FamilyLabel:
//   - Links the dimension's absolute value to a specific FamilyParameter.
//   - The parameter controls the exact distance in feet/mm.
//   - Works on single-segment (2-reference) or overall (outer) dimensions.
//   - Requires IsReferencesValidForLabel() == true.
//
// Common pattern: 3-plane dimension (Left--Center--Right)
//   - AreSegmentsEqual = true  --> enforces Left half == Right half
//   - FamilyLabel = pWidth    --> the overall width drives the total span

Dimension dim = /* 3-plane dimension */;
FamilyParameter pWidth = /* Width parameter */;

using (Transaction tx = new Transaction(familyDoc, "Setup Symmetric Width"))
{
    tx.Start();
    dim.AreSegmentsEqual = true;          // symmetry
    if (dim.IsReferencesValidForLabel())
        dim.FamilyLabel = pWidth;         // absolute size
    tx.Commit();
}"""))

        return samples

    # ------------------------------------------------------------------
    # Alignment constraints
    # ------------------------------------------------------------------

    def _alignment_constraints(self) -> List[SAMPLE]:
        samples = []

        # Basic alignment and lock
        align_cases = [
            ("left face",   "Left",         "Align and lock the left face of an extrusion to the 'Left' reference plane"),
            ("right face",  "Right",        "Align and lock the right face of an extrusion to the 'Right' reference plane"),
            ("front face",  "Front",        "Align and lock the front face of an extrusion to the 'Front' reference plane"),
            ("back face",   "Back",         "Align and lock the back face of an extrusion to the 'Back' reference plane"),
            ("top face",    "Top",          "Align and lock the top face of an extrusion to the 'Top' reference plane"),
            ("bottom face", "Bottom",       "Align and lock the bottom face of an extrusion to the 'Bottom' reference plane"),
            ("left face",   "Width_Left",   "Align and lock the left face of an extrusion to the 'Width_Left' reference plane"),
            ("right face",  "Width_Right",  "Align and lock the right face of an extrusion to the 'Width_Right' reference plane"),
            ("front face",  "Depth_Front",  "Align and lock the front face of an extrusion to the 'Depth_Front' reference plane"),
            ("back face",   "Depth_Back",   "Align and lock the back face of an extrusion to the 'Depth_Back' reference plane"),
            ("top face",    "Door_Top",     "Align and lock the top face of a void extrusion to the 'Door_Top' reference plane"),
            ("left face",   "Door_Left",    "Align and lock the left face of a door void to the 'Door_Left' reference plane"),
        ]
        for face_desc, plane_name, instruction in align_cases:
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;
using System.Linq;

// Align extrusion {face_desc} to '{plane_name}' reference plane and lock
using (Transaction tx = new Transaction(familyDoc, "Align and Lock {face_desc.title()}"))
{{
    tx.Start();

    Extrusion ext = /* previously created extrusion */;
    ReferencePlane rp = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "{plane_name}");

    // Get the face reference from extrusion geometry
    Options opts = new Options {{ ComputeReferences = true }};
    Reference faceRef = null;
    foreach (GeometryObject obj in ext.get_Geometry(opts))
    {{
        Solid solid = obj as Solid;
        if (solid == null) continue;
        foreach (Face face in solid.Faces)
        {{
            // Match face by its normal direction
            XYZ normal = face.ComputeNormal(new UV(0.5, 0.5));
            if (normal.IsAlmostEqualTo(rp.Normal) || normal.IsAlmostEqualTo(-rp.Normal))
            {{
                faceRef = face.Reference;
                break;
            }}
        }}
        if (faceRef != null) break;
    }}

    if (faceRef != null)
    {{
        // Create alignment between face and reference plane
        Alignment alignment = familyDoc.FamilyCreate.NewAlignment(
            familyDoc.ActiveView,
            rp.GetReference(),
            faceRef);

        // Lock the alignment so the face tracks the reference plane
        if (alignment != null)
            alignment.IsLocked = true;
    }}

    tx.Commit();
}}"""))

        # Align all four side faces at once
        samples.append(_s(
            "Align and lock all four vertical faces of an extrusion to the Left, Right, Front, and Back reference planes",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;
using System.Collections.Generic;

using (Transaction tx = new Transaction(familyDoc, "Align All Faces"))
{{
    tx.Start();

    Extrusion ext = /* previously created extrusion */;
    View activeView = familyDoc.ActiveView;

    // Map normal direction -> reference plane name
    var normalToPlane = new Dictionary<string, string>
    {{
        {{ "-X", "Left"  }},
        {{ "+X", "Right" }},
        {{ "-Y", "Front" }},
        {{ "+Y", "Back"  }},
    }};

    Options opts = new Options {{ ComputeReferences = true }};
    foreach (GeometryObject obj in ext.get_Geometry(opts))
    {{
        Solid solid = obj as Solid;
        if (solid == null) continue;

        foreach (Face face in solid.Faces)
        {{
            XYZ n = face.ComputeNormal(new UV(0.5, 0.5));
            string key =
                n.IsAlmostEqualTo(-XYZ.BasisX) ? "-X" :
                n.IsAlmostEqualTo( XYZ.BasisX) ? "+X" :
                n.IsAlmostEqualTo(-XYZ.BasisY) ? "-Y" :
                n.IsAlmostEqualTo( XYZ.BasisY) ? "+Y" : null;

            if (key == null || !normalToPlane.ContainsKey(key)) continue;

            string planeName = normalToPlane[key];
            ReferencePlane rp = new FilteredElementCollector(familyDoc)
                .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
                .FirstOrDefault(r => r.Name == planeName);

            if (rp == null) continue;

            Alignment al = familyDoc.FamilyCreate.NewAlignment(
                activeView, rp.GetReference(), face.Reference);
            if (al != null) al.IsLocked = true;
        }}
    }}

    tx.Commit();
}}"""))

        # Unlock an alignment
        samples.append(_s(
            "Unlock an existing alignment constraint to allow the face to move freely",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "Unlock Alignment"))
{
    tx.Start();

    // Find all locked alignments and unlock them
    IList<Alignment> alignments = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Alignment))
        .Cast<Alignment>()
        .Where(a => a.IsLocked)
        .ToList();

    foreach (Alignment al in alignments)
        al.IsLocked = false;

    tx.Commit();
}"""))

        # Alignment between two reference planes
        samples.append(_s(
            "Align two reference planes to be co-planar using NewAlignment",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

// Co-planar alignment between two reference planes
using (Transaction tx = new Transaction(familyDoc, "Align Reference Planes"))
{{
    tx.Start();

    ReferencePlane rpSource = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "TempPlane");

    ReferencePlane rpTarget = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "Center (Left/Right)");

    Alignment al = familyDoc.FamilyCreate.NewAlignment(
        familyDoc.ActiveView,
        rpTarget.GetReference(),
        rpSource.GetReference());

    if (al != null) al.IsLocked = true;

    tx.Commit();
}}"""))

        # Check IsLocked
        samples.append(_s(
            "Check whether an alignment is currently locked",
            """\
using Autodesk.Revit.DB;
using System.Linq;

IList<Alignment> alignments = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(Alignment))
    .Cast<Alignment>()
    .ToList();

foreach (Alignment al in alignments)
{
    TaskDialog.Show("Alignment",
        $"Id={al.Id.IntegerValue}  IsLocked={al.IsLocked}");
}"""))

        # Alignment between a sweep path end and a reference plane
        samples.append(_s(
            "Align the start point of a sweep path to a reference plane and lock the alignment",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

// Align sweep path endpoint reference to a reference plane
using (Transaction tx = new Transaction(familyDoc, "Align Sweep Path"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;

    ReferencePlane rpStart = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "Left");

    // Get a model curve end reference
    ModelCurve mc = /* previously created model curve sweep path */;
    Reference endRef = mc.GeometryCurve.GetEndPointReference(0); // start point

    Alignment al = familyDoc.FamilyCreate.NewAlignment(
        activeView, rpStart.GetReference(), endRef);
    if (al != null) al.IsLocked = true;

    tx.Commit();
}}"""))

        # Align a blend top face
        samples.append(_s(
            "Align the top face of a blend to the 'Top' reference plane and lock it",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "Align Blend Top"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    Blend blend = /* previously created blend */;
    ReferencePlane rpTop = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "Top");

    Options opts = new Options {{ ComputeReferences = true }};
    Reference topFaceRef = null;
    foreach (GeometryObject obj in blend.get_Geometry(opts))
    {{
        Solid s = obj as Solid; if (s == null) continue;
        foreach (Face face in s.Faces)
        {{
            if (face.ComputeNormal(new UV(0.5, 0.5)).IsAlmostEqualTo(XYZ.BasisZ))
            {{ topFaceRef = face.Reference; break; }}
        }}
        if (topFaceRef != null) break;
    }}

    if (topFaceRef != null)
    {{
        Alignment al = familyDoc.FamilyCreate.NewAlignment(
            activeView, rpTop.GetReference(), topFaceRef);
        if (al != null) al.IsLocked = true;
    }}

    tx.Commit();
}}"""))

        # Align a revolution outer surface
        samples.append(_s(
            "Align the outer cylindrical face of a revolution to a 'Radius_Right' reference plane",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "Align Revolution Outer Face"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    Revolution rev = /* previously created revolution */;
    ReferencePlane rpR = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "Radius_Right");

    Options opts = new Options {{ ComputeReferences = true }};
    Reference outerRef = null;
    foreach (GeometryObject obj in rev.get_Geometry(opts))
    {{
        Solid s = obj as Solid; if (s == null) continue;
        // The cylindrical outer face normal points radially outward;
        // pick the face whose normal is closest to +X at (0.5, 0) UV.
        double bestDot = -1;
        foreach (Face face in s.Faces)
        {{
            XYZ n = face.ComputeNormal(new UV(0.5, 0.5));
            double dot = n.DotProduct(XYZ.BasisX);
            if (dot > bestDot) {{ bestDot = dot; outerRef = face.Reference; }}
        }}
        break;
    }}

    if (outerRef != null)
    {{
        Alignment al = familyDoc.FamilyCreate.NewAlignment(
            activeView, rpR.GetReference(), outerRef);
        if (al != null) al.IsLocked = true;
    }}

    tx.Commit();
}}"""))

        # Alignment with IsSuppressed check
        samples.append(_s(
            "Check whether each alignment is suppressed (soft constraint) or enforced (hard lock)",
            """\
using Autodesk.Revit.DB;
using System.Linq;

// Iterate alignments and report lock state
IList<Alignment> als = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(Alignment))
    .Cast<Alignment>()
    .ToList();

foreach (Alignment al in als)
{
    // IsLocked = true  --> hard lock; geometry cannot deviate from the reference plane.
    // IsLocked = false --> soft alignment; geometry may drift during flex.
    TaskDialog.Show("Alignment Status",
        $"Id={al.Id.IntegerValue}  IsLocked={al.IsLocked}");
}"""))

        # Delete all unlocked alignments
        samples.append(_s(
            "Delete all unlocked (non-enforced) alignments from the family document",
            """\
using Autodesk.Revit.DB;
using System.Linq;
using System.Collections.Generic;

using (Transaction tx = new Transaction(familyDoc, "Remove Unlocked Alignments"))
{
    tx.Start();

    IList<ElementId> toDelete = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Alignment))
        .Cast<Alignment>()
        .Where(a => !a.IsLocked)
        .Select(a => a.Id)
        .ToList();

    foreach (ElementId id in toDelete)
        familyDoc.Delete(id);

    tx.Commit();
}"""))

        # NewAlignment with model-line-based construction
        samples.append(_s(
            "Create an alignment between a model line's midpoint reference and a reference plane",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

// Align the midpoint reference of a model line to a center reference plane
using (Transaction tx = new Transaction(familyDoc, "Align Model Line Midpoint"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;

    ReferencePlane rpCenter = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "Center (Left/Right)");

    // Model line endpoint reference (index 0 = start, 1 = end)
    ModelCurve mc = /* model line whose midpoint should align to center */;
    // Note: midpoint is not directly available; use a reference point element
    // or ensure the model line is placed symmetrically via EqualConstraint.

    // For endpoint alignment:
    Reference startRef = mc.GeometryCurve.GetEndPointReference(0);
    Alignment al = familyDoc.FamilyCreate.NewAlignment(
        activeView, rpCenter.GetReference(), startRef);
    if (al != null) al.IsLocked = true;

    tx.Commit();
}}"""))

        # Count locked alignments
        samples.append(_s(
            "Count the number of locked alignment constraints in the family document",
            """\
using Autodesk.Revit.DB;
using System.Linq;

int lockedCount = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(Alignment))
    .Cast<Alignment>()
    .Count(a => a.IsLocked);

TaskDialog.Show("Alignments",
    $"Locked alignments: {lockedCount}");"""))

        # Alignment in elevation view vs plan view
        samples.append(_s(
            "Explain when to create alignment constraints in an elevation view versus a plan view",
            """\
using Autodesk.Revit.DB;

// Alignment constraints must be created in the view where the geometry
// and the reference plane are both visible.
//
// Plan view (XY plane):
//   - Use for aligning vertical faces (Left, Right, Front, Back).
//   - Reference planes defined with XYZ.BasisZ as the cutVector.
//
// Elevation / Front view (XZ plane):
//   - Use for aligning horizontal faces (Top, Bottom) and
//     height-related reference planes.
//   - Reference planes defined with XYZ.BasisY as the cutVector.
//
// If you call NewAlignment with a view where the reference plane is
// not visible, Revit will throw an Autodesk.Revit.Exceptions.ArgumentException.

// Example: align top face in an elevation view
View elevView = /* front elevation view */;

using (Transaction tx = new Transaction(familyDoc, "Align Top in Elevation"))
{
    tx.Start();

    ReferencePlane rpTop = /* Top reference plane */;
    Reference topFaceRef = /* top face reference from extrusion */;

    Alignment al = familyDoc.FamilyCreate.NewAlignment(
        elevView, rpTop.GetReference(), topFaceRef);
    if (al != null) al.IsLocked = true;

    tx.Commit();
}"""))

        return samples

    # ------------------------------------------------------------------
    # Label dimensions
    # ------------------------------------------------------------------

    def _label_dimensions(self) -> List[SAMPLE]:
        samples = []

        # Label a dimension with a single Length parameter
        label_cases = [
            ("Width",       300,  "Label a linear dimension with the 'Width' family parameter"),
            ("Depth",       200,  "Label a linear dimension with the 'Depth' family parameter"),
            ("Height",      2400, "Label a vertical linear dimension with the 'Height' family parameter"),
            ("Radius",      150,  "Label a radial dimension with the 'Radius' family parameter"),
            ("Offset",      50,   "Label an offset dimension with the 'Offset' family parameter"),
            ("DoorWidth",   900,  "Label a dimension with the 'DoorWidth' family parameter"),
            ("DoorHeight",  2100, "Label a vertical dimension with the 'DoorHeight' family parameter"),
            ("WindowWidth", 1200, "Label a dimension with the 'WindowWidth' family parameter"),
            ("Projection",  300,  "Label a horizontal dimension with the 'Projection' parameter"),
            ("Thickness",   25,   "Label a dimension with the 'Thickness' family parameter"),
            ("Span",        3000, "Label a dimension with the 'Span' family parameter"),
            ("FlangeWidth", 200,  "Label a dimension with the 'FlangeWidth' parameter for an I-beam family"),
            ("WebHeight",   400,  "Label a dimension with the 'WebHeight' parameter"),
            ("Diameter",    300,  "Label a dimension with the 'Diameter' family parameter"),
        ]
        for pname, default_mm, instruction in label_cases:
            default_ft = default_mm * MM_TO_FT
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;

// Step 1: Add '{pname}' parameter OUTSIDE Transaction
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter p{pname} = famMgr.AddParameter(
    "{pname}",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length,
    false); // type parameter
famMgr.Set(p{pname}, {default_ft:.6f}); // {default_mm} mm

// Step 2: Create reference planes and dimension, then label
using (Transaction tx = new Transaction(familyDoc, "Label {pname} Dimension"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;

    ReferencePlane rpA = /* first reference plane */;
    ReferencePlane rpB = /* second reference plane */;

    ReferenceArray refs = new ReferenceArray();
    refs.Append(rpA.GetReference());
    refs.Append(rpB.GetReference());

    Line dimLine = Line.CreateBound(
        new XYZ(-{_ft(500)}, {_ft(60)}, 0),
        new XYZ( {_ft(500)}, {_ft(60)}, 0));

    Dimension dim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView, dimLine, refs);

    // IsReferencesValidForLabel() must return true before assigning FamilyLabel
    if (dim != null && dim.IsReferencesValidForLabel())
        dim.FamilyLabel = p{pname};

    tx.Commit();
}}"""))

        # IsReferencesValidForLabel check
        samples.append(_s(
            "Explain why IsReferencesValidForLabel() must be called before assigning FamilyLabel",
            """\
using Autodesk.Revit.DB;

// IsReferencesValidForLabel() returns true only when:
//   1. The dimension references named reference planes (not free geometry)
//   2. The dimension is not already labeled
//   3. The parameter type matches the dimension type (Length for linear dims)
//
// Failure to check causes an InvalidOperationException when setting FamilyLabel.

Dimension dim = /* linear dimension */;
FamilyParameter pWidth = /* Width parameter */;

if (dim.IsReferencesValidForLabel())
{
    dim.FamilyLabel = pWidth;
}
else
{
    // Common fix: ensure references point to named reference planes,
    // not raw geometry edges or faces.
    TaskDialog.Show("Warning",
        "Dimension references are not valid for labeling. " +
        "Ensure references point to named reference planes.");
}"""))

        # Unlabel a dimension
        samples.append(_s(
            "Remove the FamilyLabel from a dimension to make it an unlabeled reference dimension",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Remove Dimension Label"))
{
    tx.Start();

    Dimension dim = /* labeled dimension */;
    dim.FamilyLabel = null; // removes the label

    tx.Commit();
}"""))

        # Retrieve currently labeled dimensions
        samples.append(_s(
            "Find all labeled dimensions in the family document",
            """\
using Autodesk.Revit.DB;
using System.Linq;

IList<Dimension> labeledDims = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(Dimension))
    .Cast<Dimension>()
    .Where(d => d.FamilyLabel != null)
    .ToList();

foreach (Dimension d in labeledDims)
{
    TaskDialog.Show("Labeled Dim",
        $"Dim Id={d.Id.IntegerValue}  Label='{d.FamilyLabel.Definition.Name}'");
}"""))

        # Label multiple dimensions
        multi_label = [
            ("Width", "Depth"),
            ("Width", "Height"),
            ("Depth", "Height"),
            ("FlangeWidth", "WebHeight"),
            ("DoorWidth", "DoorHeight"),
            ("WindowWidth", "WindowHeight"),
            ("Projection", "Thickness"),
        ]
        for p1, p2 in multi_label:
            samples.append(_s(
                f"Create two labeled dimensions: one for '{p1}' and one for '{p2}'",
                f"""\
using Autodesk.Revit.DB;

// Add both parameters OUTSIDE Transaction
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter p{p1} = famMgr.AddParameter("{p1}", BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length, false);
FamilyParameter p{p2} = famMgr.AddParameter("{p2}", BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length, false);
famMgr.Set(p{p1}, {_ft(300)});
famMgr.Set(p{p2}, {_ft(200)});

using (Transaction tx = new Transaction(familyDoc, "Two Labeled Dimensions"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;

    // {p1} dimension (horizontal)
    ReferencePlane rpL = /* left ref plane */;
    ReferencePlane rpR = /* right ref plane */;
    ReferenceArray refsW = new ReferenceArray();
    refsW.Append(rpL.GetReference());
    refsW.Append(rpR.GetReference());
    Dimension dim{p1} = familyDoc.FamilyCreate.NewLinearDimension(
        activeView,
        Line.CreateBound(new XYZ(-{_ft(500)}, {_ft(60)}, 0), new XYZ({_ft(500)}, {_ft(60)}, 0)),
        refsW);
    if (dim{p1} != null && dim{p1}.IsReferencesValidForLabel())
        dim{p1}.FamilyLabel = p{p1};

    // {p2} dimension (vertical)
    ReferencePlane rpF = /* front ref plane */;
    ReferencePlane rpB = /* back ref plane */;
    ReferenceArray refsD = new ReferenceArray();
    refsD.Append(rpF.GetReference());
    refsD.Append(rpB.GetReference());
    Dimension dim{p2} = familyDoc.FamilyCreate.NewLinearDimension(
        activeView,
        Line.CreateBound(new XYZ({_ft(60)}, -{_ft(500)}, 0), new XYZ({_ft(60)}, {_ft(500)}, 0)),
        refsD);
    if (dim{p2} != null && dim{p2}.IsReferencesValidForLabel())
        dim{p2}.FamilyLabel = p{p2};

    tx.Commit();
}}"""))

        # Label with instance parameter
        samples.append(_s(
            "Label a dimension with an instance (not type) Length parameter named 'CustomOffset'",
            f"""\
using Autodesk.Revit.DB;

// Instance parameter: isInstance = true
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pOffset = famMgr.AddParameter(
    "CustomOffset",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length,
    true); // true = instance parameter
famMgr.Set(pOffset, {_ft(50)}); // 50 mm default

using (Transaction tx = new Transaction(familyDoc, "Label Instance Dim"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    ReferencePlane rpA = /* first ref plane */;
    ReferencePlane rpB = /* second ref plane */;

    ReferenceArray refs = new ReferenceArray();
    refs.Append(rpA.GetReference());
    refs.Append(rpB.GetReference());

    Dimension dim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView,
        Line.CreateBound(new XYZ(-{_ft(300)}, {_ft(40)}, 0), new XYZ({_ft(300)}, {_ft(40)}, 0)),
        refs);

    if (dim != null && dim.IsReferencesValidForLabel())
        dim.FamilyLabel = pOffset;

    tx.Commit();
}}"""))

        # Label with YesNo visibility parameter
        samples.append(_s(
            "Create a YesNo parameter and label a dimension with it to toggle a feature",
            """\
using Autodesk.Revit.DB;

// YesNo parameter cannot label a LENGTH dimension directly.
// Use it with FamilyElementVisibility or a formula-driven approach.
// For a visibility toggle:

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pShow = famMgr.AddParameter(
    "ShowDetail",
    BuiltInParameterGroup.PG_VISIBILITY,
    ParameterType.YesNo,
    true); // instance
famMgr.Set(pShow, 1); // default: shown

// Apply to an element's visibility parameter
using (Transaction tx = new Transaction(familyDoc, "Set Visibility Formula"))
{
    tx.Start();
    // Element visibility is controlled by formula, not FamilyLabel:
    // famMgr.SetFormula(pShow, "Width > 300mm"); -- not valid for YesNo
    // Instead, link the IS_VISIBLE_PARAM directly in the family.
    tx.Commit();
}"""))

        # Retrieve FamilyLabel property
        samples.append(_s(
            "Check which FamilyParameter is currently assigned as the label of a dimension",
            """\
using Autodesk.Revit.DB;

Dimension dim = /* labeled dimension */;

FamilyParameter label = dim.FamilyLabel;
if (label != null)
{
    string paramName = label.Definition.Name;
    bool isInstance  = label.IsInstance;
    TaskDialog.Show("Label",
        $"Parameter: {paramName}  IsInstance: {isInstance}");
}
else
{
    TaskDialog.Show("Label", "This dimension has no FamilyLabel.");
}"""))

        # Label dimension with formula-driven parameter
        samples.append(_s(
            "Label a dimension with a parameter that has a formula 'Height = Width * 3' and verify the dimension updates",
            f"""\
using Autodesk.Revit.DB;

// STEP 1 -- Parameters with formula (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth  = famMgr.AddParameter("Width",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pHeight = famMgr.AddParameter("Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pWidth, {_ft(300)});
famMgr.SetFormula(pHeight, "Width * 3"); // Height = 900 mm when Width = 300 mm

// STEP 2 -- Reference planes + labeled dimension (INSIDE Transaction)
using (Transaction tx = new Transaction(familyDoc, "Formula-Driven Label"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    ReferencePlane rpBase = /* Ref. Level reference plane */;
    ReferencePlane rpTop  = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, 0, {_ft(900)}), new XYZ(1, 0, {_ft(900)}), XYZ.BasisY, activeView);
    rpTop.Name = "Top";

    ReferenceArray refs = new ReferenceArray();
    refs.Append(rpBase.GetReference());
    refs.Append(rpTop.GetReference());

    Dimension dim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView,
        Line.CreateBound(new XYZ({_ft(60)}, 0, 0), new XYZ({_ft(60)}, 0, {_ft(1000)})),
        refs);

    if (dim != null && dim.IsReferencesValidForLabel())
        dim.FamilyLabel = pHeight; // labeled with formula-driven Height

    tx.Commit();
}}"""))

        # Label check: parameter type mismatch
        samples.append(_s(
            "Show what happens when you try to label a linear dimension with a non-Length parameter (YesNo) -- and how to avoid it",
            """\
using Autodesk.Revit.DB;

// A linear dimension can only be labeled with a Length parameter.
// Attempting to assign a YesNo, Integer, or Angle parameter will throw.

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pLength = famMgr.AddParameter("Width",   BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pYesNo  = famMgr.AddParameter("Visible", BuiltInParameterGroup.PG_VISIBILITY, ParameterType.YesNo, true);

Dimension dim = /* linear dimension */;

// WRONG -- will throw InvalidOperationException:
// dim.FamilyLabel = pYesNo;

// CORRECT -- check parameter type before assigning:
if (pLength.Definition is InternalDefinition internalDef &&
    internalDef.ParameterType == ParameterType.Length)
{
    if (dim != null && dim.IsReferencesValidForLabel())
        dim.FamilyLabel = pLength;
}"""))

        # Retrieve FamilyLabel parameter name and print to dialog
        samples.append(_s(
            "Iterate all labeled dimensions and print each parameter name and current value",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;

IList<Dimension> labeled = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(Dimension))
    .Cast<Dimension>()
    .Where(d => d.FamilyLabel != null)
    .ToList();

foreach (Dimension d in labeled)
{
    FamilyParameter fp = d.FamilyLabel;
    string name = fp.Definition.Name;

    // Get current value from the current family type
    double valueFt = famMgr.CurrentType.AsDouble(fp);
    double valueMm = valueFt * 304.8;

    TaskDialog.Show("Labeled Dim",
        $"Param: {name}  Value: {valueMm:F1} mm ({valueFt:F6} ft)");
}"""))

        # Label dimension in an elevation view
        samples.append(_s(
            "Create a labeled 'Height' dimension in a front elevation view between 'Ref. Level' and 'Top' reference planes",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

// Height dimension is created in an elevation view, not plan
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pHeight = famMgr.AddParameter(
    "Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pHeight, {_ft(2400)});

using (Transaction tx = new Transaction(familyDoc, "Height Dim in Elevation"))
{{
    tx.Start();

    // Use the front elevation view for height dimensions
    View elevView = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(View))
        .Cast<View>()
        .FirstOrDefault(v => v.ViewType == ViewType.Elevation);

    if (elevView == null) {{ tx.Commit(); return; }}

    ReferencePlane rpBase = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "Ref. Level");
    ReferencePlane rpTop = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "Top");

    ReferenceArray refs = new ReferenceArray();
    refs.Append(rpBase.GetReference());
    refs.Append(rpTop.GetReference());

    // Vertical dimension line in elevation
    Line dimLine = Line.CreateBound(
        new XYZ({_ft(60)}, 0, 0),
        new XYZ({_ft(60)}, 0, {_ft(2500)}));

    Dimension dim = familyDoc.FamilyCreate.NewLinearDimension(
        elevView, dimLine, refs);

    if (dim != null && dim.IsReferencesValidForLabel())
        dim.FamilyLabel = pHeight;

    tx.Commit();
}}"""))

        # Label a shared parameter dimension
        samples.append(_s(
            "Add a shared parameter 'OverallLength' and label a linear dimension with it in a family",
            f"""\
using Autodesk.Revit.DB;
using System.IO;

// Shared parameters require a shared parameter file
string sharedParamFile = Path.Combine(
    Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),
    "RevitSharedParams.txt");

if (!File.Exists(sharedParamFile))
    File.WriteAllText(sharedParamFile, "# Revit Shared Parameter File\\n# Do not edit manually.\\n");

familyDoc.Application.SharedParametersFilename = sharedParamFile;
DefinitionFile defFile = familyDoc.Application.OpenSharedParameterFile();

// Create group and parameter if not present
DefinitionGroup grp = defFile.Groups.get_Item("Dimensions")
    ?? defFile.Groups.Create("Dimensions");

ExternalDefinition extDef = grp.Definitions.get_Item("OverallLength") as ExternalDefinition
    ?? grp.Definitions.Create(new ExternalDefinitionCreationOptions("OverallLength", SpecTypeId.Length)) as ExternalDefinition;

// Add shared parameter to family
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pLength = famMgr.AddParameter(
    extDef,
    BuiltInParameterGroup.PG_GEOMETRY,
    false); // type parameter
famMgr.Set(pLength, {_ft(1200)});

// Label the dimension
using (Transaction tx = new Transaction(familyDoc, "Label Shared Param Dim"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    ReferencePlane rpA = /* first ref plane */;
    ReferencePlane rpB = /* second ref plane */;

    ReferenceArray refs = new ReferenceArray();
    refs.Append(rpA.GetReference());
    refs.Append(rpB.GetReference());

    Dimension dim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView,
        Line.CreateBound(new XYZ(-{_ft(700)}, {_ft(60)}, 0), new XYZ({_ft(700)}, {_ft(60)}, 0)),
        refs);

    if (dim != null && dim.IsReferencesValidForLabel())
        dim.FamilyLabel = pLength;

    tx.Commit();
}}"""))

        # Verify IsReferencesValidForLabel returns false for geometry edges
        samples.append(_s(
            "Demonstrate that IsReferencesValidForLabel returns false when dimension references include raw geometry edges instead of named reference planes",
            """\
using Autodesk.Revit.DB;

// IsReferencesValidForLabel returns false if any reference is a raw geometry edge.
// Solution: align the edge to a named reference plane first, then dimension the planes.

Extrusion ext = /* target extrusion */;
View activeView = familyDoc.ActiveView;

// Get a raw face reference (NOT a reference plane reference)
Options opts = new Options { ComputeReferences = true };
Reference rawFaceRef = null;
foreach (GeometryObject obj in ext.get_Geometry(opts))
{
    Solid s = obj as Solid; if (s == null) continue;
    rawFaceRef = s.Faces.get_Item(0).Reference;
    break;
}

using (Transaction tx = new Transaction(familyDoc, "Test Label Validity"))
{
    tx.Start();

    ReferencePlane rp = /* named reference plane */;
    ReferenceArray refs = new ReferenceArray();
    refs.Append(rawFaceRef);   // raw edge -- makes label invalid
    refs.Append(rp.GetReference());

    Dimension dim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView,
        Line.CreateBound(new XYZ(-1, 0.1, 0), new XYZ(1, 0.1, 0)),
        refs);

    // This will be false because rawFaceRef is not a named reference plane
    bool canLabel = dim != null && dim.IsReferencesValidForLabel();
    TaskDialog.Show("Label Valid", canLabel ? "Valid" : "NOT valid -- use named reference planes instead.");

    tx.Commit();
}"""))

        # Change label on an existing dimension
        samples.append(_s(
            "Change the FamilyLabel of an existing dimension from 'Width' to 'FlangeWidth' without deleting the dimension",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pFlangeWidth = famMgr.LookupParameter("FlangeWidth");
if (pFlangeWidth == null)
    pFlangeWidth = famMgr.AddParameter("FlangeWidth",
        BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

using (Transaction tx = new Transaction(familyDoc, "Relabel Dimension"))
{
    tx.Start();

    // Find the dimension currently labeled 'Width'
    FamilyParameter pWidth = famMgr.LookupParameter("Width");
    Dimension dim = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Dimension))
        .Cast<Dimension>()
        .FirstOrDefault(d => d.FamilyLabel != null &&
                             d.FamilyLabel.Id == pWidth?.Id);

    if (dim != null && dim.IsReferencesValidForLabel())
        dim.FamilyLabel = pFlangeWidth; // reassign

    tx.Commit();
}"""))

        # Label dimension in a 3D view (not recommended, but possible)
        samples.append(_s(
            "Explain why labeled dimensions should be created in 2D plan or elevation views, not in 3D views",
            """\
using Autodesk.Revit.DB;

// Best practice: always create labeled dimensions in 2D views (Plan, Elevation, Section).
//
// Reasons:
//   1. Reference planes are only visible in their defining view type.
//      A vertical reference plane (normal to X) is visible in plan, not in elevation.
//   2. NewLinearDimension requires a View parameter. If the view is a 3D view,
//      the dimension may be created but will not display correctly.
//   3. IsReferencesValidForLabel() can return false if the view type
//      does not show the referenced elements.
//
// Correct approach:
//   - Width/Depth dimensions: create in a Plan view.
//   - Height dimensions: create in a Front or Side Elevation view.
//   - Angular dimensions: create in the view where both reference lines are visible.
//
// Example: use the active plan view for width/depth:
View planView = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(ViewPlan))
    .Cast<ViewPlan>()
    .FirstOrDefault();

// Then pass planView to NewLinearDimension:
// familyDoc.FamilyCreate.NewLinearDimension(planView, dimLine, refs);"""))

        # LookupParameter vs AddParameter when labeling
        samples.append(_s(
            "Use LookupParameter to retrieve an existing family parameter before labeling a dimension, avoiding duplicate parameter creation",
            """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;

// Prefer LookupParameter over AddParameter to avoid duplicates
FamilyParameter pWidth = famMgr.LookupParameter("Width");
if (pWidth == null)
{
    // Only add if not present
    pWidth = famMgr.AddParameter(
        "Width",
        BuiltInParameterGroup.PG_GEOMETRY,
        ParameterType.Length,
        false);
}

// Now label the dimension
Dimension dim = /* target dimension */;
if (dim != null && dim.IsReferencesValidForLabel())
    dim.FamilyLabel = pWidth;"""))

        return samples

    # ------------------------------------------------------------------
    # Parametric constraint workflows
    # ------------------------------------------------------------------

    def _parametric_constraint_workflows(self) -> List[SAMPLE]:
        samples = []

        # Full rectangular parametric family workflow
        samples.append(_s(
            "Create a fully parametric rectangular extrusion family with Width, Depth, and Height parameters, reference planes, labeled dimensions, and locked alignments",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

// ============================================================
// STEP 1 -- Parameters (OUTSIDE Transaction)
// ============================================================
FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter pWidth  = famMgr.AddParameter("Width",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pDepth  = famMgr.AddParameter("Depth",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pHeight = famMgr.AddParameter("Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pWidth,  {_ft(300)});  // 300 mm
famMgr.Set(pDepth,  {_ft(200)});  // 200 mm
famMgr.Set(pHeight, {_ft(1200)}); // 1200 mm

// ============================================================
// STEP 2 -- Reference planes + Extrusion + Dimensions (INSIDE Transaction)
// ============================================================
using (Transaction tx = new Transaction(familyDoc, "Parametric Box Family"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    double hw = {_ft(150)};  // half-width  (150 mm)
    double hd = {_ft(100)};  // half-depth  (100 mm)
    double ht = {_ft(1200)}; // full height (1200 mm)

    // --- Reference planes ---
    ReferencePlane rpLeft = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(-hw, 0, 0), new XYZ(-hw, 1, 0), XYZ.BasisZ, activeView);
    rpLeft.Name = "Width_Left";

    ReferencePlane rpRight = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ( hw, 0, 0), new XYZ( hw, 1, 0), XYZ.BasisZ, activeView);
    rpRight.Name = "Width_Right";

    ReferencePlane rpFront = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, -hd, 0), new XYZ(1, -hd, 0), XYZ.BasisZ, activeView);
    rpFront.Name = "Depth_Front";

    ReferencePlane rpBack = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, hd, 0), new XYZ(1, hd, 0), XYZ.BasisZ, activeView);
    rpBack.Name = "Depth_Back";

    ReferencePlane rpTop = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, 0, ht), new XYZ(1, 0, ht), XYZ.BasisY, activeView);
    rpTop.Name = "Top";

    ReferencePlane rpBottom = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "Ref. Level");

    // --- Extrusion ---
    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-hw, -hd, 0), new XYZ( hw, -hd, 0)));
    loop.Append(Line.CreateBound(new XYZ( hw, -hd, 0), new XYZ( hw,  hd, 0)));
    loop.Append(Line.CreateBound(new XYZ( hw,  hd, 0), new XYZ(-hw,  hd, 0)));
    loop.Append(Line.CreateBound(new XYZ(-hw,  hd, 0), new XYZ(-hw, -hd, 0)));
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    Extrusion ext = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, ht);

    // --- Width dimension (labeled) ---
    ReferenceArray wRefs = new ReferenceArray();
    wRefs.Append(rpLeft.GetReference());
    wRefs.Append(rpRight.GetReference());
    Dimension wDim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView,
        Line.CreateBound(new XYZ(-{_ft(400)}, {_ft(80)}, 0), new XYZ({_ft(400)}, {_ft(80)}, 0)),
        wRefs);
    if (wDim != null && wDim.IsReferencesValidForLabel())
        wDim.FamilyLabel = pWidth;

    // --- Depth dimension (labeled) ---
    ReferenceArray dRefs = new ReferenceArray();
    dRefs.Append(rpFront.GetReference());
    dRefs.Append(rpBack.GetReference());
    Dimension dDim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView,
        Line.CreateBound(new XYZ({_ft(80)}, -{_ft(400)}, 0), new XYZ({_ft(80)}, {_ft(400)}, 0)),
        dRefs);
    if (dDim != null && dDim.IsReferencesValidForLabel())
        dDim.FamilyLabel = pDepth;

    // --- Align and lock all faces ---
    Options opts = new Options {{ ComputeReferences = true }};
    foreach (GeometryObject obj in ext.get_Geometry(opts))
    {{
        Solid solid = obj as Solid;
        if (solid == null) continue;
        foreach (Face face in solid.Faces)
        {{
            XYZ n = face.ComputeNormal(new UV(0.5, 0.5));
            ReferencePlane target =
                n.IsAlmostEqualTo(-XYZ.BasisX) ? rpLeft  :
                n.IsAlmostEqualTo( XYZ.BasisX) ? rpRight :
                n.IsAlmostEqualTo(-XYZ.BasisY) ? rpFront :
                n.IsAlmostEqualTo( XYZ.BasisY) ? rpBack  :
                n.IsAlmostEqualTo( XYZ.BasisZ) ? rpTop   :
                n.IsAlmostEqualTo(-XYZ.BasisZ) ? rpBottom : null;

            if (target == null) continue;
            Alignment al = familyDoc.FamilyCreate.NewAlignment(
                activeView, target.GetReference(), face.Reference);
            if (al != null) al.IsLocked = true;
        }}
    }}

    tx.Commit();
}}"""))

        # Parametric column family with formula
        samples.append(_s(
            "Create a parametric column family where Height = 4 * Width using a formula, with reference planes and labeled dimensions",
            f"""\
using Autodesk.Revit.DB;

// STEP 1 -- Parameters with formula (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter pWidth  = famMgr.AddParameter("Width",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pHeight = famMgr.AddParameter("Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pWidth,  {_ft(300)});  // 300 mm default
famMgr.Set(pHeight, {_ft(1200)}); // 1200 mm default (4 * 300)

// Formula: Height = Width * 4
famMgr.SetFormula(pHeight, "Width * 4");

// STEP 2 -- Geometry + constraints (INSIDE Transaction)
using (Transaction tx = new Transaction(familyDoc, "Parametric Column"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    double hw = {_ft(150)};
    double ht = {_ft(1200)};

    ReferencePlane rpLeft  = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(-hw, 0, 0), new XYZ(-hw, 1, 0), XYZ.BasisZ, activeView);
    rpLeft.Name = "Width_Left";
    ReferencePlane rpRight = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ( hw, 0, 0), new XYZ( hw, 1, 0), XYZ.BasisZ, activeView);
    rpRight.Name = "Width_Right";
    ReferencePlane rpTop   = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, 0, ht), new XYZ(1, 0, ht), XYZ.BasisY, activeView);
    rpTop.Name = "Top";

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-hw, -hw, 0), new XYZ( hw, -hw, 0)));
    loop.Append(Line.CreateBound(new XYZ( hw, -hw, 0), new XYZ( hw,  hw, 0)));
    loop.Append(Line.CreateBound(new XYZ( hw,  hw, 0), new XYZ(-hw,  hw, 0)));
    loop.Append(Line.CreateBound(new XYZ(-hw,  hw, 0), new XYZ(-hw, -hw, 0)));
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    Extrusion ext = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, ht);

    // Width dimension with label + EqualConstraint (symmetric)
    ReferencePlane rpCenter = new System.Linq.Enumerable
        .Where(new FilteredElementCollector(familyDoc)
            .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>(),
            r => r.Name == "Center (Left/Right)").First();

    ReferenceArray wRefs = new ReferenceArray();
    wRefs.Append(rpLeft.GetReference());
    wRefs.Append(rpCenter.GetReference());
    wRefs.Append(rpRight.GetReference());

    Dimension wDim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView,
        Line.CreateBound(new XYZ(-{_ft(400)}, {_ft(60)}, 0), new XYZ({_ft(400)}, {_ft(60)}, 0)),
        wRefs);
    if (wDim != null)
    {{
        wDim.AreSegmentsEqual = true;
        if (wDim.IsReferencesValidForLabel())
            wDim.FamilyLabel = pWidth;
    }}

    tx.Commit();
}}"""))

        # Parametric door opening workflow
        samples.append(_s(
            "Create a parametric door opening with DoorWidth and DoorHeight parameters, reference planes, equality constraints, and labeled dimensions",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

// STEP 1 -- Parameters (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter pDoorWidth  = famMgr.AddParameter("DoorWidth",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pDoorHeight = famMgr.AddParameter("DoorHeight", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pDoorWidth,  {_ft(900)});  // 900 mm
famMgr.Set(pDoorHeight, {_ft(2100)}); // 2100 mm

// STEP 2 -- Reference planes (INSIDE Transaction)
using (Transaction tx = new Transaction(familyDoc, "Door Opening Planes"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;

    double hw   = {_ft(450)};  // half door width (450 mm)
    double dh   = {_ft(2100)}; // door height (2100 mm)

    ReferencePlane rpLeft = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(-hw, 0, 0), new XYZ(-hw, 1, 0), XYZ.BasisZ, activeView);
    rpLeft.Name = "Door_Left";

    ReferencePlane rpCenter = familyDoc.FamilyCreate.NewReferencePlane(
        XYZ.Zero, XYZ.BasisY, XYZ.BasisZ, activeView);
    rpCenter.Name = "Door_Center";

    ReferencePlane rpRight = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ( hw, 0, 0), new XYZ( hw, 1, 0), XYZ.BasisZ, activeView);
    rpRight.Name = "Door_Right";

    ReferencePlane rpTop = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, 0, dh), new XYZ(1, 0, dh), XYZ.BasisY, activeView);
    rpTop.Name = "Door_Top";

    // Width dimension with equality + label
    ReferenceArray wRefs = new ReferenceArray();
    wRefs.Append(rpLeft.GetReference());
    wRefs.Append(rpCenter.GetReference());
    wRefs.Append(rpRight.GetReference());

    Dimension wDim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView,
        Line.CreateBound(new XYZ(-{_ft(600)}, {_ft(60)}, 0), new XYZ({_ft(600)}, {_ft(60)}, 0)),
        wRefs);
    if (wDim != null)
    {{
        wDim.AreSegmentsEqual = true;
        if (wDim.IsReferencesValidForLabel())
            wDim.FamilyLabel = pDoorWidth;
    }}

    // Height dimension with label
    ReferencePlane rpBase = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "Ref. Level");

    ReferenceArray hRefs = new ReferenceArray();
    hRefs.Append(rpBase.GetReference());
    hRefs.Append(rpTop.GetReference());

    Dimension hDim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView,
        Line.CreateBound(new XYZ({_ft(80)}, 0, 0), new XYZ({_ft(80)}, 0, {_ft(2200)})),
        hRefs);
    if (hDim != null && hDim.IsReferencesValidForLabel())
        hDim.FamilyLabel = pDoorHeight;

    tx.Commit();
}}"""))

        # Shelf/bracket parametric workflow
        samples.append(_s(
            "Create a parametric shelf bracket family with Width and Projection parameters and a formula Angle = atan(Height / Projection)",
            f"""\
using Autodesk.Revit.DB;
using System;

// STEP 1 -- Parameters (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter pWidth      = famMgr.AddParameter("Width",      BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pProjection = famMgr.AddParameter("Projection", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pThickness  = famMgr.AddParameter("Thickness",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pWidth,      {_ft(600)});  // 600 mm
famMgr.Set(pProjection, {_ft(300)});  // 300 mm
famMgr.Set(pThickness,  {_ft(25)});   // 25 mm

// STEP 2 -- Geometry (INSIDE Transaction)
using (Transaction tx = new Transaction(familyDoc, "Shelf Bracket"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    double w  = {_ft(600)};
    double p  = {_ft(300)};
    double t  = {_ft(25)};

    // Horizontal shelf plate
    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(0, 0, 0),  new XYZ(w, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ(w, 0, 0),  new XYZ(w, p, 0)));
    loop.Append(Line.CreateBound(new XYZ(w, p, 0),  new XYZ(0, p, 0)));
    loop.Append(Line.CreateBound(new XYZ(0, p, 0),  new XYZ(0, 0, 0)));
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    Extrusion shelf = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, t);

    // Width reference planes + labeled dimension
    ReferencePlane rpW0 = familyDoc.FamilyCreate.NewReferencePlane(
        XYZ.Zero, XYZ.BasisY, XYZ.BasisZ, activeView);
    rpW0.Name = "Shelf_Start";
    ReferencePlane rpW1 = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(w, 0, 0), new XYZ(w, 1, 0), XYZ.BasisZ, activeView);
    rpW1.Name = "Shelf_End";

    ReferenceArray wRefs = new ReferenceArray();
    wRefs.Append(rpW0.GetReference());
    wRefs.Append(rpW1.GetReference());

    Dimension wDim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView,
        Line.CreateBound(new XYZ(0, {_ft(60)}, 0), new XYZ(w, {_ft(60)}, 0)),
        wRefs);
    if (wDim != null && wDim.IsReferencesValidForLabel())
        wDim.FamilyLabel = pWidth;

    tx.Commit();
}}"""))

        # Workflow: reference plane, dim, label, formula, type table
        samples.append(_s(
            "Build a family with a Width parameter that drives a formula 'Depth = Width / 2' and verify with a family type table",
            f"""\
using Autodesk.Revit.DB;

// STEP 1 -- Parameters (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter pWidth = famMgr.AddParameter("Width", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pDepth = famMgr.AddParameter("Depth", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pWidth, {_ft(400)}); // 400 mm
famMgr.SetFormula(pDepth, "Width / 2"); // Depth = 200 mm when Width = 400 mm

// STEP 2 -- Add types to verify formula behavior
using (Transaction tx = new Transaction(familyDoc, "Add Family Types"))
{{
    tx.Start();

    famMgr.NewType("Small");
    famMgr.Set(pWidth, {_ft(300)}); // Depth becomes 150 mm

    famMgr.NewType("Medium");
    famMgr.Set(pWidth, {_ft(600)}); // Depth becomes 300 mm

    famMgr.NewType("Large");
    famMgr.Set(pWidth, {_ft(900)}); // Depth becomes 450 mm

    tx.Commit();
}}

// STEP 3 -- Iterate types to verify
foreach (FamilyType ft in famMgr.Types)
{{
    double widthFt = ft.AsDouble(pWidth);
    double depthFt = ft.AsDouble(pDepth);
    TaskDialog.Show("Types",
        $"Type={{ft.Name}}  Width={{widthFt * 304.8:F0}} mm  Depth={{depthFt * 304.8:F0}} mm");
}}"""))

        # Parametric radius workflow
        samples.append(_s(
            "Create a parametric cylinder family with a Radius parameter controlling both the extrusion profile and a labeled radial dimension",
            f"""\
using Autodesk.Revit.DB;
using System;

// STEP 1 -- Parameter (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pRadius = famMgr.AddParameter(
    "Radius", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pRadius, {_ft(150)}); // 150 mm

// STEP 2 -- Circular extrusion + reference planes (INSIDE Transaction)
using (Transaction tx = new Transaction(familyDoc, "Parametric Cylinder"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    double r  = {_ft(150)};
    double ht = {_ft(600)};
    int    n  = 32;

    CurveArray loop = new CurveArray();
    for (int i = 0; i < n; i++)
    {{
        double a0 = 2 * Math.PI * i / n;
        double a1 = 2 * Math.PI * (i + 1) / n;
        loop.Append(Line.CreateBound(
            new XYZ(r * Math.Cos(a0), r * Math.Sin(a0), 0),
            new XYZ(r * Math.Cos(a1), r * Math.Sin(a1), 0)));
    }}
    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    Extrusion cyl = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, ht);

    // Diameter reference planes: Left and Right at +/- radius
    ReferencePlane rpLeft = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(-r, 0, 0), new XYZ(-r, 1, 0), XYZ.BasisZ, activeView);
    rpLeft.Name = "Radius_Left";
    ReferencePlane rpRight = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ( r, 0, 0), new XYZ( r, 1, 0), XYZ.BasisZ, activeView);
    rpRight.Name = "Radius_Right";
    ReferencePlane rpCenter = new System.Linq.Enumerable
        .Where(new FilteredElementCollector(familyDoc)
            .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>(),
            p => p.Name == "Center (Left/Right)").First();

    // 3-plane symmetric dim labeled with Radius
    ReferenceArray refs = new ReferenceArray();
    refs.Append(rpLeft.GetReference());
    refs.Append(rpCenter.GetReference());
    refs.Append(rpRight.GetReference());

    Dimension rDim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView,
        Line.CreateBound(new XYZ(-{_ft(300)}, {_ft(60)}, 0), new XYZ({_ft(300)}, {_ft(60)}, 0)),
        refs);
    if (rDim != null)
    {{
        rDim.AreSegmentsEqual = true;
        if (rDim.IsReferencesValidForLabel())
            rDim.FamilyLabel = pRadius;
    }}

    tx.Commit();
}}"""))

        # Workflow: window family with Width/Height and symmetric planes
        samples.append(_s(
            "Create a parametric window family with WindowWidth and WindowHeight parameters, symmetric reference planes, equality constraints, and labeled dimensions",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

// STEP 1 -- Parameters (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW = famMgr.AddParameter("WindowWidth",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pH = famMgr.AddParameter("WindowHeight", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pW, {_ft(1200)});
famMgr.Set(pH, {_ft(1000)});

// STEP 2 -- Geometry and constraints (INSIDE Transaction)
using (Transaction tx = new Transaction(familyDoc, "Window Frame"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    double hw = {_ft(600)};  // half width
    double ht = {_ft(1000)}; // full height

    ReferencePlane rpL = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(-hw, 0, 0), new XYZ(-hw, 1, 0), XYZ.BasisZ, activeView);
    rpL.Name = "Window_Left";
    rpL.IsReference = FamilyInstanceReferenceType.Left;

    ReferencePlane rpR = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ( hw, 0, 0), new XYZ( hw, 1, 0), XYZ.BasisZ, activeView);
    rpR.Name = "Window_Right";
    rpR.IsReference = FamilyInstanceReferenceType.Right;

    ReferencePlane rpT = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, 0, ht), new XYZ(1, 0, ht), XYZ.BasisY, activeView);
    rpT.Name = "Window_Top";
    rpT.IsReference = FamilyInstanceReferenceType.Top;

    ReferencePlane rpCLR = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "Center (Left/Right)");

    // Symmetric width dimension with equality and label
    ReferenceArray wRefs = new ReferenceArray();
    wRefs.Append(rpL.GetReference());
    wRefs.Append(rpCLR.GetReference());
    wRefs.Append(rpR.GetReference());
    Dimension wDim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView,
        Line.CreateBound(new XYZ(-{_ft(800)}, {_ft(60)}, 0), new XYZ({_ft(800)}, {_ft(60)}, 0)),
        wRefs);
    if (wDim != null) {{ wDim.AreSegmentsEqual = true; if (wDim.IsReferencesValidForLabel()) wDim.FamilyLabel = pW; }}

    // Height dimension with label
    ReferencePlane rpBase = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "Ref. Level");
    ReferenceArray hRefs = new ReferenceArray();
    hRefs.Append(rpBase.GetReference());
    hRefs.Append(rpT.GetReference());
    Dimension hDim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView,
        Line.CreateBound(new XYZ({_ft(80)}, 0, 0), new XYZ({_ft(80)}, 0, {_ft(1200)})),
        hRefs);
    if (hDim != null && hDim.IsReferencesValidForLabel()) hDim.FamilyLabel = pH;

    tx.Commit();
}}"""))

        # Workflow: I-beam family with FlangeWidth, WebHeight, Thickness
        samples.append(_s(
            "Create a parametric I-beam cross-section family with FlangeWidth, WebHeight, and Thickness parameters, reference planes, and labeled dimensions",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

// STEP 1 -- Parameters (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pFlange = famMgr.AddParameter("FlangeWidth", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pWeb    = famMgr.AddParameter("WebHeight",   BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pThick  = famMgr.AddParameter("Thickness",   BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pFlange, {_ft(200)});
famMgr.Set(pWeb,    {_ft(400)});
famMgr.Set(pThick,  {_ft(12)});

// STEP 2 -- Reference planes (INSIDE Transaction)
using (Transaction tx = new Transaction(familyDoc, "I-Beam Reference Planes"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    double hf = {_ft(100)}; // half flange
    double hw = {_ft(200)}; // half web height
    double t  = {_ft(12)};  // thickness

    ReferencePlane rpFL = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(-hf, 0, 0), new XYZ(-hf, 1, 0), XYZ.BasisZ, activeView);
    rpFL.Name = "Flange_Left"; rpFL.IsReference = FamilyInstanceReferenceType.Left;

    ReferencePlane rpFR = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ( hf, 0, 0), new XYZ( hf, 1, 0), XYZ.BasisZ, activeView);
    rpFR.Name = "Flange_Right"; rpFR.IsReference = FamilyInstanceReferenceType.Right;

    ReferencePlane rpBot = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, 0, -hw), new XYZ(1, 0, -hw), XYZ.BasisY, activeView);
    rpBot.Name = "Web_Bottom"; rpBot.IsReference = FamilyInstanceReferenceType.Bottom;

    ReferencePlane rpTop = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, 0,  hw), new XYZ(1, 0,  hw), XYZ.BasisY, activeView);
    rpTop.Name = "Web_Top"; rpTop.IsReference = FamilyInstanceReferenceType.Top;

    ReferencePlane rpCLR = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "Center (Left/Right)");

    // FlangeWidth dimension
    ReferenceArray fRefs = new ReferenceArray();
    fRefs.Append(rpFL.GetReference()); fRefs.Append(rpCLR.GetReference()); fRefs.Append(rpFR.GetReference());
    Dimension fDim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView,
        Line.CreateBound(new XYZ(-{_ft(300)}, {_ft(60)}, 0), new XYZ({_ft(300)}, {_ft(60)}, 0)),
        fRefs);
    if (fDim != null) {{ fDim.AreSegmentsEqual = true; if (fDim.IsReferencesValidForLabel()) fDim.FamilyLabel = pFlange; }}

    // WebHeight dimension
    ReferenceArray wRefs = new ReferenceArray();
    wRefs.Append(rpBot.GetReference()); wRefs.Append(rpTop.GetReference());
    Dimension wDim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView,
        Line.CreateBound(new XYZ({_ft(60)}, 0, -{_ft(300)}), new XYZ({_ft(60)}, 0, {_ft(300)})),
        wRefs);
    if (wDim != null && wDim.IsReferencesValidForLabel()) wDim.FamilyLabel = pWeb;

    tx.Commit();
}}"""))

        # Workflow: wall-hosted bracket with Offset and Projection
        samples.append(_s(
            "Create a wall-hosted bracket family with Offset (vertical position) and Projection (horizontal reach) parameters, labeled dimensions, and locked alignments",
            f"""\
using Autodesk.Revit.DB;

// STEP 1 -- Parameters (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pOffset     = famMgr.AddParameter("MountingHeight", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, true);  // instance
FamilyParameter pProjection = famMgr.AddParameter("Projection",     BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false); // type
famMgr.Set(pOffset,     {_ft(1200)});
famMgr.Set(pProjection, {_ft(300)});

// STEP 2 -- Reference planes + dimensions (INSIDE Transaction)
using (Transaction tx = new Transaction(familyDoc, "Bracket Family"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    double proj = {_ft(300)};
    double thk  = {_ft(20)};

    ReferencePlane rpWall = new System.Linq.Enumerable
        .Where(new FilteredElementCollector(familyDoc)
            .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>(),
            r => r.Name == "Wall Face").FirstOrDefault()
        ?? familyDoc.FamilyCreate.NewReferencePlane(XYZ.Zero, XYZ.BasisY, XYZ.BasisZ, activeView);
    rpWall.Name = "Wall Face";
    rpWall.IsReference = FamilyInstanceReferenceType.Back;

    ReferencePlane rpTip = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, proj, 0), new XYZ(1, proj, 0), XYZ.BasisZ, activeView);
    rpTip.Name = "Bracket_Tip";
    rpTip.IsReference = FamilyInstanceReferenceType.Front;

    // Projection dimension with label
    ReferenceArray pRefs = new ReferenceArray();
    pRefs.Append(rpWall.GetReference());
    pRefs.Append(rpTip.GetReference());
    Dimension pDim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView,
        Line.CreateBound(new XYZ({_ft(60)}, 0, 0), new XYZ({_ft(60)}, proj + {_ft(50)}, 0)),
        pRefs);
    if (pDim != null && pDim.IsReferencesValidForLabel())
        pDim.FamilyLabel = pProjection;

    tx.Commit();
}}"""))

        # Workflow: full parametric structural column with all six faces locked
        samples.append(_s(
            "Create a fully parametric structural column family: add Width and Depth parameters, four bounding reference planes with named IsReference types, symmetric equality constraints, labeled dimensions, and all extrusion faces locked to reference planes",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

// ===== STEP 1: Parameters =====
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW = famMgr.AddParameter("b", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pD = famMgr.AddParameter("d", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pW, {_ft(450)});
famMgr.Set(pD, {_ft(450)});

// ===== STEP 2: Planes, extrusion, dims, alignments =====
using (Transaction tx = new Transaction(familyDoc, "Structural Column"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    double hw = {_ft(225)}; // half-width
    double hd = {_ft(225)}; // half-depth
    double ht = {_ft(3000)}; // height 3000 mm

    // Reference planes
    var rps = new System.Collections.Generic.Dictionary<string, ReferencePlane>();
    rps["Left"]  = familyDoc.FamilyCreate.NewReferencePlane(new XYZ(-hw,  0, 0), new XYZ(-hw, 1, 0), XYZ.BasisZ, activeView);
    rps["Right"] = familyDoc.FamilyCreate.NewReferencePlane(new XYZ( hw,  0, 0), new XYZ( hw, 1, 0), XYZ.BasisZ, activeView);
    rps["Front"] = familyDoc.FamilyCreate.NewReferencePlane(new XYZ( 0, -hd, 0), new XYZ( 1,-hd, 0), XYZ.BasisZ, activeView);
    rps["Back"]  = familyDoc.FamilyCreate.NewReferencePlane(new XYZ( 0,  hd, 0), new XYZ( 1, hd, 0), XYZ.BasisZ, activeView);
    rps["Top"]   = familyDoc.FamilyCreate.NewReferencePlane(new XYZ( 0,   0, ht), new XYZ(1, 0, ht), XYZ.BasisY, activeView);

    rps["Left"].Name  = "b_Left";   rps["Left"].IsReference  = FamilyInstanceReferenceType.Left;
    rps["Right"].Name = "b_Right";  rps["Right"].IsReference = FamilyInstanceReferenceType.Right;
    rps["Front"].Name = "d_Front";  rps["Front"].IsReference = FamilyInstanceReferenceType.Front;
    rps["Back"].Name  = "d_Back";   rps["Back"].IsReference  = FamilyInstanceReferenceType.Back;
    rps["Top"].Name   = "Top";      rps["Top"].IsReference   = FamilyInstanceReferenceType.Top;

    ReferencePlane rpCLR = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "Center (Left/Right)");
    ReferencePlane rpCFB = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "Center (Front/Back)");

    // Extrusion
    CurveArrArray prof = new CurveArrArray();
    CurveArray lp = new CurveArray();
    lp.Append(Line.CreateBound(new XYZ(-hw,-hd,0), new XYZ( hw,-hd,0)));
    lp.Append(Line.CreateBound(new XYZ( hw,-hd,0), new XYZ( hw, hd,0)));
    lp.Append(Line.CreateBound(new XYZ( hw, hd,0), new XYZ(-hw, hd,0)));
    lp.Append(Line.CreateBound(new XYZ(-hw, hd,0), new XYZ(-hw,-hd,0)));
    prof.Append(lp);
    SketchPlane sp = SketchPlane.Create(familyDoc, Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    Extrusion ext = familyDoc.FamilyCreate.NewExtrusion(true, prof, sp, ht);

    // Width dim with equality + label
    ReferenceArray wr = new ReferenceArray();
    wr.Append(rps["Left"].GetReference()); wr.Append(rpCLR.GetReference()); wr.Append(rps["Right"].GetReference());
    Dimension wd = familyDoc.FamilyCreate.NewLinearDimension(activeView,
        Line.CreateBound(new XYZ(-{_ft(600)},{_ft(80)},0), new XYZ({_ft(600)},{_ft(80)},0)), wr);
    if (wd != null) {{ wd.AreSegmentsEqual = true; if (wd.IsReferencesValidForLabel()) wd.FamilyLabel = pW; }}

    // Depth dim with equality + label
    ReferenceArray dr = new ReferenceArray();
    dr.Append(rps["Front"].GetReference()); dr.Append(rpCFB.GetReference()); dr.Append(rps["Back"].GetReference());
    Dimension dd = familyDoc.FamilyCreate.NewLinearDimension(activeView,
        Line.CreateBound(new XYZ({_ft(80)}, -{_ft(600)}, 0), new XYZ({_ft(80)},{_ft(600)},0)), dr);
    if (dd != null) {{ dd.AreSegmentsEqual = true; if (dd.IsReferencesValidForLabel()) dd.FamilyLabel = pD; }}

    // Lock all faces to reference planes
    Options opts = new Options {{ ComputeReferences = true }};
    ReferencePlane rpBot = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "Ref. Level");
    foreach (GeometryObject obj in ext.get_Geometry(opts))
    {{
        Solid s = obj as Solid; if (s == null) continue;
        foreach (Face face in s.Faces)
        {{
            XYZ n = face.ComputeNormal(new UV(0.5, 0.5));
            ReferencePlane target =
                n.IsAlmostEqualTo(-XYZ.BasisX) ? rps["Left"]  :
                n.IsAlmostEqualTo( XYZ.BasisX) ? rps["Right"] :
                n.IsAlmostEqualTo(-XYZ.BasisY) ? rps["Front"] :
                n.IsAlmostEqualTo( XYZ.BasisY) ? rps["Back"]  :
                n.IsAlmostEqualTo( XYZ.BasisZ) ? rps["Top"]   :
                n.IsAlmostEqualTo(-XYZ.BasisZ) ? rpBot         : null;
            if (target == null) continue;
            Alignment al = familyDoc.FamilyCreate.NewAlignment(activeView, target.GetReference(), face.Reference);
            if (al != null) al.IsLocked = true;
        }}
    }}

    tx.Commit();
}}"""))

        # Workflow: flex test sequence for a parametric family
        samples.append(_s(
            "Write a flex-test loop that cycles through Small, Medium, and Large family types and verifies no ConstraintNotSatisfiedException is thrown",
            f"""\
using Autodesk.Revit.DB;
using System;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth = famMgr.LookupParameter("Width");

// Ensure the three types exist
string[] typeNames = {{ "Small", "Medium", "Large" }};
double[] widths    = {{ {_ft(200)}, {_ft(400)}, {_ft(600)} }};

foreach (string typeName in typeNames)
{{
    if (!famMgr.Types.Cast<FamilyType>().Any(t => t.Name == typeName))
    {{
        using (Transaction tx = new Transaction(familyDoc, $"Add Type {{typeName}}"))
        {{
            tx.Start();
            famMgr.NewType(typeName);
            tx.Commit();
        }}
    }}
}}

// Flex each type
for (int i = 0; i < typeNames.Length; i++)
{{
    using (Transaction tx = new Transaction(familyDoc, $"Flex {{typeNames[i]}}"))
    {{
        tx.Start();

        FamilyType ft = famMgr.Types.Cast<FamilyType>().First(t => t.Name == typeNames[i]);
        famMgr.CurrentType = ft;
        famMgr.Set(pWidth, widths[i]);

        try
        {{
            familyDoc.Regenerate();
            TaskDialog.Show("Flex OK", $"{{typeNames[i]}}: Width = {{widths[i] * 304.8:F0}} mm -- PASS");
        }}
        catch (Exception ex)
        {{
            TaskDialog.Show("Flex FAIL", $"{{typeNames[i]}}: {{ex.Message}}");
        }}

        tx.Commit();
    }}
}}"""))

        # Workflow: build constraint chain then verify alignment
        samples.append(_s(
            "Create reference planes, add a void extrusion for a door opening, align the void to the door reference planes, and label the width and height dimensions",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

// STEP 1 -- Parameters (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pDW = famMgr.AddParameter("OpeningWidth",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pDH = famMgr.AddParameter("OpeningHeight", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pDW, {_ft(900)});
famMgr.Set(pDH, {_ft(2100)});

// STEP 2 -- Reference planes + void extrusion + alignments (INSIDE Transaction)
using (Transaction tx = new Transaction(familyDoc, "Door Opening Void"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    double hw = {_ft(450)};
    double dh = {_ft(2100)};
    double depth = {_ft(400)};

    ReferencePlane rpOL = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(-hw, 0, 0), new XYZ(-hw, 1, 0), XYZ.BasisZ, activeView);
    rpOL.Name = "Opening_Left"; rpOL.IsReference = FamilyInstanceReferenceType.Left;

    ReferencePlane rpOR = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ( hw, 0, 0), new XYZ( hw, 1, 0), XYZ.BasisZ, activeView);
    rpOR.Name = "Opening_Right"; rpOR.IsReference = FamilyInstanceReferenceType.Right;

    ReferencePlane rpOT = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, 0, dh), new XYZ(1, 0, dh), XYZ.BasisY, activeView);
    rpOT.Name = "Opening_Top"; rpOT.IsReference = FamilyInstanceReferenceType.Top;

    // Void extrusion for door cut
    CurveArrArray prof = new CurveArrArray();
    CurveArray lp = new CurveArray();
    lp.Append(Line.CreateBound(new XYZ(-hw, 0, 0),  new XYZ( hw, 0, 0)));
    lp.Append(Line.CreateBound(new XYZ( hw, 0, 0),  new XYZ( hw, 0, dh)));
    lp.Append(Line.CreateBound(new XYZ( hw, 0, dh), new XYZ(-hw, 0, dh)));
    lp.Append(Line.CreateBound(new XYZ(-hw, 0, dh), new XYZ(-hw, 0, 0)));
    prof.Append(lp);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    Extrusion voidExt = familyDoc.FamilyCreate.NewExtrusion(false, prof, sp, depth);

    // Align void faces to reference planes
    Options opts = new Options {{ ComputeReferences = true }};
    foreach (GeometryObject obj in voidExt.get_Geometry(opts))
    {{
        Solid s = obj as Solid; if (s == null) continue;
        foreach (Face face in s.Faces)
        {{
            XYZ n = face.ComputeNormal(new UV(0.5, 0.5));
            ReferencePlane target =
                n.IsAlmostEqualTo(-XYZ.BasisX) ? rpOL :
                n.IsAlmostEqualTo( XYZ.BasisX) ? rpOR :
                n.IsAlmostEqualTo( XYZ.BasisZ) ? rpOT : null;
            if (target == null) continue;
            Alignment al = familyDoc.FamilyCreate.NewAlignment(activeView, target.GetReference(), face.Reference);
            if (al != null) al.IsLocked = true;
        }}
    }}

    // Labeled width dimension
    ReferencePlane rpCLR = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "Center (Left/Right)");
    ReferenceArray wr = new ReferenceArray();
    wr.Append(rpOL.GetReference()); wr.Append(rpCLR.GetReference()); wr.Append(rpOR.GetReference());
    Dimension wd = familyDoc.FamilyCreate.NewLinearDimension(activeView,
        Line.CreateBound(new XYZ(-{_ft(600)},{_ft(60)},0), new XYZ({_ft(600)},{_ft(60)},0)), wr);
    if (wd != null) {{ wd.AreSegmentsEqual = true; if (wd.IsReferencesValidForLabel()) wd.FamilyLabel = pDW; }}

    // Labeled height dimension
    ReferencePlane rpBase = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>()
        .First(r => r.Name == "Ref. Level");
    ReferenceArray hr = new ReferenceArray();
    hr.Append(rpBase.GetReference()); hr.Append(rpOT.GetReference());
    Dimension hd2 = familyDoc.FamilyCreate.NewLinearDimension(activeView,
        Line.CreateBound(new XYZ({_ft(80)},0,0), new XYZ({_ft(80)},0,{_ft(2300)})), hr);
    if (hd2 != null && hd2.IsReferencesValidForLabel()) hd2.FamilyLabel = pDH;

    tx.Commit();
}}"""))

        # Workflow: modular panel with Width, Height, and Thickness formula
        samples.append(_s(
            "Create a modular panel family where Thickness = max(Width, Height) / 40 using a formula, with reference planes and labeled dimensions",
            f"""\
using Autodesk.Revit.DB;

// STEP 1 -- Parameters with formula (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW = famMgr.AddParameter("PanelWidth",     BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pH = famMgr.AddParameter("PanelHeight",    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pT = famMgr.AddParameter("PanelThickness", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pW, {_ft(1200)});
famMgr.Set(pH, {_ft(2400)});
// Thickness formula: PanelHeight / 40 (simplified max rule)
famMgr.SetFormula(pT, "PanelHeight / 40");

// STEP 2 -- Geometry and constraints (INSIDE Transaction)
using (Transaction tx = new Transaction(familyDoc, "Modular Panel"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    double pw = {_ft(1200)};
    double ph = {_ft(2400)};
    double pt = {_ft(60)};  // PanelHeight/40 = 2400/40 = 60 mm

    ReferencePlane rpL = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, 0, 0), new XYZ(0, 1, 0), XYZ.BasisZ, activeView);
    rpL.Name = "Panel_Left"; rpL.IsReference = FamilyInstanceReferenceType.Left;

    ReferencePlane rpR = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(pw, 0, 0), new XYZ(pw, 1, 0), XYZ.BasisZ, activeView);
    rpR.Name = "Panel_Right"; rpR.IsReference = FamilyInstanceReferenceType.Right;

    ReferencePlane rpT = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, 0, ph), new XYZ(1, 0, ph), XYZ.BasisY, activeView);
    rpT.Name = "Panel_Top"; rpT.IsReference = FamilyInstanceReferenceType.Top;

    CurveArrArray prof = new CurveArrArray();
    CurveArray lp = new CurveArray();
    lp.Append(Line.CreateBound(new XYZ(0, 0, 0),  new XYZ(pw, 0, 0)));
    lp.Append(Line.CreateBound(new XYZ(pw, 0, 0), new XYZ(pw, 0, ph)));
    lp.Append(Line.CreateBound(new XYZ(pw, 0, ph),new XYZ(0,  0, ph)));
    lp.Append(Line.CreateBound(new XYZ(0,  0, ph),new XYZ(0,  0, 0)));
    prof.Append(lp);
    SketchPlane sp = SketchPlane.Create(familyDoc, Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    Extrusion panel = familyDoc.FamilyCreate.NewExtrusion(true, prof, sp, pt);

    // Width dim
    ReferenceArray wr = new ReferenceArray();
    wr.Append(rpL.GetReference()); wr.Append(rpR.GetReference());
    Dimension wd = familyDoc.FamilyCreate.NewLinearDimension(activeView,
        Line.CreateBound(new XYZ(0, {_ft(60)}, 0), new XYZ(pw, {_ft(60)}, 0)), wr);
    if (wd != null && wd.IsReferencesValidForLabel()) wd.FamilyLabel = pW;

    // Height dim
    ReferencePlane rpBase = new System.Linq.Enumerable
        .Where(new FilteredElementCollector(familyDoc)
            .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>(),
            r => r.Name == "Ref. Level").First();
    ReferenceArray hr = new ReferenceArray();
    hr.Append(rpBase.GetReference()); hr.Append(rpT.GetReference());
    Dimension hd2 = familyDoc.FamilyCreate.NewLinearDimension(activeView,
        Line.CreateBound(new XYZ({_ft(60)},0,0), new XYZ({_ft(60)},0,ph)), hr);
    if (hd2 != null && hd2.IsReferencesValidForLabel()) hd2.FamilyLabel = pH;

    tx.Commit();
}}"""))

        # Workflow: annotate existing geometry with running dims
        samples.append(_s(
            "Add running (cumulative) dimensions from the family origin to four reference planes at 100, 250, 400, and 600mm",
            f"""\
using Autodesk.Revit.DB;

// Running dimensions from origin to multiple reference planes
using (Transaction tx = new Transaction(familyDoc, "Running Dimensions"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    double[] positions = {{ {_ft(100)}, {_ft(250)}, {_ft(400)}, {_ft(600)} }};
    string[] names     = {{ "Rp100", "Rp250", "Rp400", "Rp600" }};

    ReferencePlane rpOrigin = familyDoc.FamilyCreate.NewReferencePlane(
        XYZ.Zero, XYZ.BasisY, XYZ.BasisZ, activeView);
    rpOrigin.Name = "Origin";

    ReferenceArray refs = new ReferenceArray();
    refs.Append(rpOrigin.GetReference());

    for (int i = 0; i < positions.Length; i++)
    {{
        ReferencePlane rp = familyDoc.FamilyCreate.NewReferencePlane(
            new XYZ(positions[i], 0, 0),
            new XYZ(positions[i], 1, 0),
            XYZ.BasisZ,
            activeView);
        rp.Name = names[i];
        refs.Append(rp.GetReference());
    }}

    // Single dimension with multiple references = running/chain dims
    Line dimLine = Line.CreateBound(
        new XYZ(0, {_ft(80)}, 0),
        new XYZ({_ft(700)}, {_ft(80)}, 0));

    Dimension runDim = familyDoc.FamilyCreate.NewLinearDimension(
        activeView, dimLine, refs);

    tx.Commit();
}}"""))

        # Workflow: step-by-step debug guide for a constraint not satisfied error
        samples.append(_s(
            "Diagnose and fix a ConstraintNotSatisfiedException thrown during family document regeneration after changing a parameter value",
            """\
using Autodesk.Revit.DB;
using System;
using System.Linq;

// ConstraintNotSatisfiedException: common causes and fixes
//
// Cause 1: Reference plane moved but extrusion faces not aligned to it.
//   Fix: Add NewAlignment between each face and its controlling reference plane.
//        Lock the alignment (IsLocked = true).
//
// Cause 2: Equal constraint (AreSegmentsEqual) on a dimension whose references
//          include a non-named reference plane.
//   Fix: Ensure all planes in the dimension are named reference planes, not
//        raw geometry edges or unnamed planes.
//
// Cause 3: Formula produces a value that violates a geometry constraint
//          (e.g., negative extrusion depth).
//   Fix: Guard the formula -- e.g., "if(Height > 0, Height, 0.001)".
//
// Diagnostic approach:

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth = famMgr.LookupParameter("Width");

using (Transaction tx = new Transaction(familyDoc, "Debug Constraint"))
{
    tx.Start();

    try
    {
        famMgr.Set(pWidth, 0.001 * (1.0 / 304.8)); // near-zero value to trigger constraint
        familyDoc.Regenerate();
        TaskDialog.Show("OK", "No constraint error.");
    }
    catch (Autodesk.Revit.Exceptions.InvalidOperationException ex)
      when (ex.Message.Contains("constraint"))
    {
        TaskDialog.Show("Constraint Error", ex.Message);
        // Rollback and investigate which alignment or dimension is broken.
    }

    tx.RollBack(); // always roll back a diagnostic transaction
}"""))

        # Workflow: add a reference plane at runtime from a parameter value
        samples.append(_s(
            "Dynamically create a reference plane at a position driven by the current value of a 'ShelfHeight' family parameter",
            f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pShelf = famMgr.LookupParameter("ShelfHeight");

if (pShelf == null)
{{
    pShelf = famMgr.AddParameter("ShelfHeight", BuiltInParameterGroup.PG_GEOMETRY,
        ParameterType.Length, true); // instance
    famMgr.Set(pShelf, {_ft(900)}); // 900 mm default
}}

double shelfFt = famMgr.CurrentType.AsDouble(pShelf);

using (Transaction tx = new Transaction(familyDoc, "Dynamic Shelf Plane"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;
    ReferencePlane rpShelf = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, 0, shelfFt),
        new XYZ(1, 0, shelfFt),
        XYZ.BasisY,
        activeView);
    rpShelf.Name = "Shelf_Level";
    rpShelf.IsReference = FamilyInstanceReferenceType.StrongReference;

    tx.Commit();
}}"""))

        # Workflow: ensure all dimensions are labeled before saving
        samples.append(_s(
            "Before saving a family, verify that every reference plane has at least one dimension that is either labeled or constrained",
            """\
using Autodesk.Revit.DB;
using System.Linq;
using System.Collections.Generic;

// Audit: every named reference plane should appear in at least one dimension reference
var namedPlanes = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(ReferencePlane))
    .Cast<ReferencePlane>()
    .Where(rp => !string.IsNullOrEmpty(rp.Name) &&
                 rp.Name != "Center (Left/Right)" &&
                 rp.Name != "Center (Front/Back)" &&
                 rp.Name != "Ref. Level")
    .ToList();

var allDims = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(Dimension))
    .Cast<Dimension>()
    .ToList();

// Collect all reference element IDs used by dimensions
var referencedIds = new HashSet<ElementId>();
foreach (Dimension d in allDims)
{
    foreach (Reference r in d.References)
    {
        if (r.ElementId != ElementId.InvalidElementId)
            referencedIds.Add(r.ElementId);
    }
}

foreach (ReferencePlane rp in namedPlanes)
{
    if (!referencedIds.Contains(rp.Id))
        TaskDialog.Show("Audit Warning",
            $"Reference plane '{rp.Name}' is not referenced by any dimension.");
}"""))

        # Quick pattern: two parameters + two reference planes + two labeled dims
        quick_cases = [
            ("TubeOD", "TubeID", 150, 100, "Create a hollow tube family with outer diameter TubeOD=150mm and inner diameter TubeID=100mm, symmetric reference planes, and labeled dimensions"),
            ("ShelfW", "ShelfD", 900, 350, "Create a shelf family with ShelfW=900mm and ShelfD=350mm parameters, bounding reference planes, and labeled dimensions"),
            ("ColumnB", "ColumnD", 300, 300, "Create a square column family with ColumnB=300mm and ColumnD=300mm parameters and labeled dimensions"),
        ]
        for pn1, pn2, v1, v2, instruction in quick_cases:
            v1ft, v2ft = _ft(v1), _ft(v2)
            hv1, hv2 = v1/2*MM_TO_FT, v2/2*MM_TO_FT
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;

// STEP 1 -- Parameters (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter p1 = famMgr.AddParameter("{pn1}", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter p2 = famMgr.AddParameter("{pn2}", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(p1, {v1ft}); // {v1} mm
famMgr.Set(p2, {v2ft}); // {v2} mm

// STEP 2 -- Reference planes + dimensions (INSIDE Transaction)
using (Transaction tx = new Transaction(familyDoc, "{pn1}/{pn2} Family"))
{{
    tx.Start();
    View activeView = familyDoc.ActiveView;

    ReferencePlane rpL = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(-{hv1:.6f}, 0, 0), new XYZ(-{hv1:.6f}, 1, 0), XYZ.BasisZ, activeView);
    rpL.Name = "{pn1}_Left"; rpL.IsReference = FamilyInstanceReferenceType.Left;

    ReferencePlane rpR = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ( {hv1:.6f}, 0, 0), new XYZ( {hv1:.6f}, 1, 0), XYZ.BasisZ, activeView);
    rpR.Name = "{pn1}_Right"; rpR.IsReference = FamilyInstanceReferenceType.Right;

    ReferencePlane rpF = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0, -{hv2:.6f}, 0), new XYZ(1, -{hv2:.6f}, 0), XYZ.BasisZ, activeView);
    rpF.Name = "{pn2}_Front"; rpF.IsReference = FamilyInstanceReferenceType.Front;

    ReferencePlane rpB = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0,  {hv2:.6f}, 0), new XYZ(1,  {hv2:.6f}, 0), XYZ.BasisZ, activeView);
    rpB.Name = "{pn2}_Back"; rpB.IsReference = FamilyInstanceReferenceType.Back;

    ReferencePlane rpCLR = new System.Linq.Enumerable
        .Where(new FilteredElementCollector(familyDoc)
            .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>(),
            r => r.Name == "Center (Left/Right)").First();
    ReferencePlane rpCFB = new System.Linq.Enumerable
        .Where(new FilteredElementCollector(familyDoc)
            .OfClass(typeof(ReferencePlane)).Cast<ReferencePlane>(),
            r => r.Name == "Center (Front/Back)").First();

    // {pn1} dimension
    ReferenceArray r1 = new ReferenceArray();
    r1.Append(rpL.GetReference()); r1.Append(rpCLR.GetReference()); r1.Append(rpR.GetReference());
    Dimension d1 = familyDoc.FamilyCreate.NewLinearDimension(activeView,
        Line.CreateBound(new XYZ(-{_ft(v1+100)}, {_ft(60)}, 0), new XYZ({_ft(v1+100)}, {_ft(60)}, 0)), r1);
    if (d1 != null) {{ d1.AreSegmentsEqual = true; if (d1.IsReferencesValidForLabel()) d1.FamilyLabel = p1; }}

    // {pn2} dimension
    ReferenceArray r2 = new ReferenceArray();
    r2.Append(rpF.GetReference()); r2.Append(rpCFB.GetReference()); r2.Append(rpB.GetReference());
    Dimension d2 = familyDoc.FamilyCreate.NewLinearDimension(activeView,
        Line.CreateBound(new XYZ({_ft(60)}, -{_ft(v2+100)}, 0), new XYZ({_ft(60)}, {_ft(v2+100)}, 0)), r2);
    if (d2 != null) {{ d2.AreSegmentsEqual = true; if (d2.IsReferencesValidForLabel()) d2.FamilyLabel = p2; }}

    tx.Commit();
}}"""))

        return samples

    # ------------------------------------------------------------------
    # Strong reference patterns
    # ------------------------------------------------------------------

    def _strong_reference_patterns(self) -> List[SAMPLE]:
        samples = []

        # Set IsReference on reference planes
        ref_strength_cases = [
            ("NotAReference",   "Set a reference plane as NotAReference (invisible to snapping)"),
            ("WeakReference",   "Set a reference plane as WeakReference (snap only, no label)"),
            ("StrongReference", "Set a reference plane as StrongReference (snap and dimension anchor)"),
            ("Left",            "Set a reference plane's IsReference to Left (standard family left edge)"),
            ("Right",           "Set a reference plane's IsReference to Right (standard family right edge)"),
            ("Front",           "Set a reference plane's IsReference to Front"),
            ("Back",            "Set a reference plane's IsReference to Back"),
            ("Bottom",          "Set a reference plane's IsReference to Bottom"),
            ("Top",             "Set a reference plane's IsReference to Top"),
            ("CenterLeftRight", "Set a reference plane as CenterLeftRight (the center symmetry plane)"),
            ("CenterElevation", "Set a reference plane as CenterElevation"),
        ]
        for ref_type, instruction in ref_strength_cases:
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Set Reference Strength"))
{{
    tx.Start();

    ReferencePlane rp = /* target reference plane */;

    // IsReference controls how the plane participates in snapping and dimensions
    rp.IsReference = FamilyInstanceReferenceType.{ref_type};

    tx.Commit();
}}"""))

        # Enumerate reference type of all planes
        samples.append(_s(
            "List the IsReference type of every reference plane in the family document",
            """\
using Autodesk.Revit.DB;
using System.Linq;

IList<ReferencePlane> planes = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(ReferencePlane))
    .Cast<ReferencePlane>()
    .ToList();

foreach (ReferencePlane rp in planes)
{
    string name = string.IsNullOrEmpty(rp.Name) ? "(unnamed)" : rp.Name;
    TaskDialog.Show("Reference Types",
        $"Name: {name}  IsReference: {rp.IsReference}");
}"""))

        # Strong reference planes for a structural column
        samples.append(_s(
            "Configure the six standard strong reference planes for a structural column family (Left, Right, Front, Back, Bottom, Top)",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

// Standard structural column reference plane setup
using (Transaction tx = new Transaction(familyDoc, "Set Column Reference Types"))
{{
    tx.Start();

    var planes = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane))
        .Cast<ReferencePlane>()
        .ToList();

    foreach (ReferencePlane rp in planes)
    {{
        switch (rp.Name)
        {{
            case "Width_Left":
                rp.IsReference = FamilyInstanceReferenceType.Left;
                break;
            case "Width_Right":
                rp.IsReference = FamilyInstanceReferenceType.Right;
                break;
            case "Depth_Front":
                rp.IsReference = FamilyInstanceReferenceType.Front;
                break;
            case "Depth_Back":
                rp.IsReference = FamilyInstanceReferenceType.Back;
                break;
            case "Ref. Level":
                rp.IsReference = FamilyInstanceReferenceType.Bottom;
                break;
            case "Top":
                rp.IsReference = FamilyInstanceReferenceType.Top;
                break;
            case "Center (Left/Right)":
                rp.IsReference = FamilyInstanceReferenceType.CenterLeftRight;
                break;
            case "Center (Front/Back)":
                rp.IsReference = FamilyInstanceReferenceType.CenterFrontBack;
                break;
        }}
    }}

    tx.Commit();
}}"""))

        # Why strong references matter
        samples.append(_s(
            "Explain the difference between StrongReference and WeakReference for a reference plane",
            """\
using Autodesk.Revit.DB;

// StrongReference vs WeakReference:
//
// StrongReference (FamilyInstanceReferenceType.StrongReference):
//   - Appears in the temporary dimension when selecting the placed instance.
//   - Visible in the "Align" and "Dimension" snap targets.
//   - Required for the reference to appear in the Tab-snap cycle.
//
// WeakReference (FamilyInstanceReferenceType.WeakReference):
//   - Only appears after pressing Tab during snap selection.
//   - Does not generate a temporary dimension on placement.
//   - Useful for interior construction planes not intended for user dimensioning.
//
// NotAReference (FamilyInstanceReferenceType.NotAReference):
//   - Completely invisible outside the family editor.
//   - Used for construction planes and reference lines that are for
//     family authoring only and should never appear to end users.
//
// Named types (Left, Right, Front, Back, Top, Bottom, CenterLeftRight, etc.):
//   - These are StrongReferences with semantic meaning.
//   - Revit uses them to orient the family on placement and to populate
//     the "Reference Planes" panel in the Properties dialog.
//
// Best practice: set at minimum Left, Right, Front, Back for any family
// that users will dimension or align in a project.

ReferencePlane rpLeft = /* left bounding plane */;
using (Transaction tx = new Transaction(familyDoc, "Configure References"))
{
    tx.Start();
    rpLeft.IsReference = FamilyInstanceReferenceType.Left;
    tx.Commit();
}"""))

        # GetReference from a reference plane
        samples.append(_s(
            "Get the geometry Reference object from a reference plane for use in NewLinearDimension",
            """\
using Autodesk.Revit.DB;

// ReferencePlane.GetReference() returns the Reference needed by dimension APIs
ReferencePlane rp = /* named reference plane */;

Reference rpRef = rp.GetReference();

// Use rpRef in a ReferenceArray for NewLinearDimension or NewAlignment:
ReferenceArray refs = new ReferenceArray();
refs.Append(rpRef);"""))

        # Verify strong references flex correctly
        samples.append(_s(
            "Flex a family to verify that strong reference planes drive geometry correctly when parameters change",
            f"""\
using Autodesk.Revit.DB;

// Flexing: change parameter values and regenerate to confirm alignment
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth = famMgr.LookupParameter("Width");

double[] testValues = {{ {_ft(200)}, {_ft(400)}, {_ft(600)} }};
// 200 mm, 400 mm, 600 mm

foreach (double testVal in testValues)
{{
    using (Transaction tx = new Transaction(familyDoc, "Flex Width"))
    {{
        tx.Start();

        famMgr.Set(pWidth, testVal);
        familyDoc.Regenerate();

        // Check that the extrusion moved with the reference planes
        // (no ConstraintNotSatisfiedException should be thrown)

        tx.Commit();
    }}

    double actualMm = testVal * 304.8;
    TaskDialog.Show("Flex", $"Width = {{actualMm:F0}} mm -- OK");
}}"""))

        # Strong references in a door family
        samples.append(_s(
            "Set up strong reference planes for a door family with the six standard named references",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

// Door family standard reference plane configuration
// Width center, Left/Right jamb edges, Front/Back face, Sill/Head

using (Transaction tx = new Transaction(familyDoc, "Door Reference Types"))
{{
    tx.Start();

    var lookup = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane))
        .Cast<ReferencePlane>()
        .ToDictionary(r => r.Name);

    if (lookup.ContainsKey("Door_Left"))
        lookup["Door_Left"].IsReference = FamilyInstanceReferenceType.Left;
    if (lookup.ContainsKey("Door_Right"))
        lookup["Door_Right"].IsReference = FamilyInstanceReferenceType.Right;
    if (lookup.ContainsKey("Center (Front/Back)"))
        lookup["Center (Front/Back)"].IsReference = FamilyInstanceReferenceType.CenterFrontBack;
    if (lookup.ContainsKey("Ref. Level"))
        lookup["Ref. Level"].IsReference = FamilyInstanceReferenceType.Bottom;
    if (lookup.ContainsKey("Door_Top"))
        lookup["Door_Top"].IsReference = FamilyInstanceReferenceType.Top;
    if (lookup.ContainsKey("Center (Left/Right)"))
        lookup["Center (Left/Right)"].IsReference = FamilyInstanceReferenceType.CenterLeftRight;

    tx.Commit();
}}"""))

        # Query reference type programmatically
        samples.append(_s(
            "Find all reference planes that are set to StrongReference or a named type (Left, Right, etc.)",
            """\
using Autodesk.Revit.DB;
using System.Linq;

var strongPlanes = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(ReferencePlane))
    .Cast<ReferencePlane>()
    .Where(rp =>
        rp.IsReference != FamilyInstanceReferenceType.NotAReference &&
        rp.IsReference != FamilyInstanceReferenceType.WeakReference)
    .ToList();

foreach (ReferencePlane rp in strongPlanes)
{
    TaskDialog.Show("Strong References",
        $"Name: {rp.Name}  Type: {rp.IsReference}");
}"""))

        # Batch-set all unnamed planes to NotAReference
        samples.append(_s(
            "Set all unnamed reference planes to NotAReference to hide them from snapping",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "Hide Unnamed Planes"))
{
    tx.Start();

    var unnamed = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane))
        .Cast<ReferencePlane>()
        .Where(rp => string.IsNullOrEmpty(rp.Name))
        .ToList();

    foreach (ReferencePlane rp in unnamed)
        rp.IsReference = FamilyInstanceReferenceType.NotAReference;

    tx.Commit();
}"""))

        # Check a specific reference plane's type and promote it
        samples.append(_s(
            "Check if a reference plane named 'Width_Left' is already a strong reference, and promote it to Left if not",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "Promote Reference"))
{
    tx.Start();

    ReferencePlane rp = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane))
        .Cast<ReferencePlane>()
        .FirstOrDefault(r => r.Name == "Width_Left");

    if (rp != null &&
        rp.IsReference != FamilyInstanceReferenceType.Left &&
        rp.IsReference != FamilyInstanceReferenceType.StrongReference)
    {
        rp.IsReference = FamilyInstanceReferenceType.Left;
    }

    tx.Commit();
}"""))

        # GetReference from reference line
        samples.append(_s(
            "Get a stable geometry Reference from a reference line to use in angular dimensions",
            """\
using Autodesk.Revit.DB;

// ReferenceLine.GeometryCurve gives the underlying curve.
// Its .Reference property is a stable, persistent reference for dimensions.

ReferenceLine rl = /* previously created reference line */;

// These two references both point to the reference line:
Reference curveRef = rl.GeometryCurve.Reference;

// Use in NewAngularDimension:
ReferenceArray refs = new ReferenceArray();
refs.Append(curveRef);
// refs.Append(secondRef);
// familyDoc.FamilyCreate.NewAngularDimension(view, arc, refs);"""))

        # Reference plane normal vs cut vector
        samples.append(_s(
            "Explain what the cutVector parameter means in NewReferencePlane and when it matters",
            """\
using Autodesk.Revit.DB;

// NewReferencePlane(bubbleEnd, freeEnd, cutVector, view)
//
// bubbleEnd : the end of the reference plane that shows the bubble (annotation end).
// freeEnd   : the other end, defines the plane's direction in the view.
// cutVector : a vector perpendicular to the bubble-to-free direction, lying in the plane.
//             It controls which side of the plane is 'positive' for dimension offsets.
//             For vertical planes in plan view, use XYZ.BasisZ (up).
//             For horizontal planes in elevation, use XYZ.BasisX or XYZ.BasisY.
//
// Example: vertical reference plane normal to X axis
using (Transaction tx = new Transaction(familyDoc, "New Reference Plane"))
{
    tx.Start();

    ReferencePlane rp = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(0.5, 0, 0),  // bubbleEnd  (right of origin)
        new XYZ(0.5, 1, 0),  // freeEnd    (extends in Y direction)
        XYZ.BasisZ,           // cutVector  (up = Z)
        familyDoc.ActiveView);

    tx.Commit();
}"""))

        # Move a reference plane by changing its geometry
        samples.append(_s(
            "Move an existing reference plane to a new offset position by modifying its geometry curves",
            f"""\
using Autodesk.Revit.DB;

// Reference planes do not expose a simple 'Offset' property.
// To move them, delete and recreate, or use ElementTransformUtils.
using (Transaction tx = new Transaction(familyDoc, "Move Reference Plane"))
{{
    tx.Start();

    ReferencePlane rp = /* target reference plane */;

    // Translate by 50mm in the X direction
    XYZ translation = new XYZ({_ft(50)}, 0, 0); // 50 mm
    ElementTransformUtils.MoveElement(familyDoc, rp.Id, translation);

    tx.Commit();
}}"""))

        # IsReference for MEP connector families
        samples.append(_s(
            "Set up strong reference planes for a round MEP connector family (CenterLeftRight, CenterFrontBack, Bottom, Top)",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "MEP Connector References"))
{
    tx.Start();

    var lookup = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane))
        .Cast<ReferencePlane>()
        .ToDictionary(r => r.Name);

    if (lookup.ContainsKey("Center (Left/Right)"))
        lookup["Center (Left/Right)"].IsReference = FamilyInstanceReferenceType.CenterLeftRight;
    if (lookup.ContainsKey("Center (Front/Back)"))
        lookup["Center (Front/Back)"].IsReference = FamilyInstanceReferenceType.CenterFrontBack;
    if (lookup.ContainsKey("Ref. Level"))
        lookup["Ref. Level"].IsReference = FamilyInstanceReferenceType.Bottom;
    if (lookup.ContainsKey("Top"))
        lookup["Top"].IsReference = FamilyInstanceReferenceType.Top;

    tx.Commit();
}"""))

        # Tab-snap cycle explanation
        samples.append(_s(
            "Explain the Tab-snap cycle order and how StrongReference vs WeakReference planes appear in it",
            """\
using Autodesk.Revit.DB;

// Tab-snap cycle in Revit:
//
// When the user moves the cursor near a placed family instance and presses Tab,
// Revit cycles through available snap targets in this order:
//
//   1. Named reference planes with Left/Right/Front/Back/Top/Bottom types
//      (these are always in the first cycle).
//   2. StrongReference planes (appear immediately on hover without Tab).
//   3. WeakReference planes (only available after pressing Tab once or twice).
//   4. NotAReference planes (never appear in snapping cycle).
//
// Practical rule for family authors:
//   - Use Left/Right/Front/Back for bounding edges -- they appear in temporary dims.
//   - Use CenterLeftRight / CenterFrontBack for symmetry planes.
//   - Use StrongReference for additional snap targets (e.g., a mid-shelf plane).
//   - Use WeakReference for subdivision planes the user rarely needs.
//   - Use NotAReference for all construction / authoring-only planes.

// No code required: this is a configuration-time decision.
// Set IsReference on each ReferencePlane inside a Transaction:
using (Transaction tx = new Transaction(familyDoc, "Configure References"))
{
    tx.Start();
    // rp.IsReference = FamilyInstanceReferenceType.StrongReference;
    tx.Commit();
}"""))

        # Strong reference and FamilyInstance.GetReferenceByName
        samples.append(_s(
            "Use FamilyInstance.GetReferenceByName to retrieve a strong reference plane reference in a project context",
            """\
using Autodesk.Revit.DB;

// In a project document (not the family editor), you can retrieve
// a reference plane of a placed family instance by its name.
// The name must match the ReferencePlane.Name set in the family.

FamilyInstance fi = /* placed family instance in project */;

Reference leftRef  = fi.GetReferenceByName("Width_Left");
Reference rightRef = fi.GetReferenceByName("Width_Right");

if (leftRef != null && rightRef != null)
{
    // Use in project-level NewLinearDimension
    ReferenceArray refs = new ReferenceArray();
    refs.Append(leftRef);
    refs.Append(rightRef);

    View activeView = /* project view */;
    Line dimLine = Line.CreateBound(
        new XYZ(-1, 0.1, 0), new XYZ(1, 0.1, 0));

    Dimension dim = activeView.Document.Create.NewDimension(
        activeView, dimLine, refs);
}"""))

        # CenterFrontBack reference type
        samples.append(_s(
            "Set the Center (Front/Back) reference plane's IsReference to CenterFrontBack for a symmetric family",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "Set Center Front/Back"))
{
    tx.Start();

    ReferencePlane rp = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane))
        .Cast<ReferencePlane>()
        .FirstOrDefault(r => r.Name == "Center (Front/Back)");

    if (rp != null)
        rp.IsReference = FamilyInstanceReferenceType.CenterFrontBack;

    tx.Commit();
}"""))

        # CenterElevation for curtain panels
        samples.append(_s(
            "Set a reference plane named 'Center' to CenterElevation for a curtain panel family",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "Set CenterElevation"))
{
    tx.Start();

    ReferencePlane rp = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane))
        .Cast<ReferencePlane>()
        .FirstOrDefault(r => r.Name == "Center");

    if (rp != null)
        rp.IsReference = FamilyInstanceReferenceType.CenterElevation;

    tx.Commit();
}"""))

        # Window family standard reference setup
        samples.append(_s(
            "Configure the standard reference plane types for a window family: Left, Right, Bottom, Top, CenterLeftRight, and CenterFrontBack",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "Window Reference Types"))
{
    tx.Start();

    var lookup = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane))
        .Cast<ReferencePlane>()
        .ToDictionary(r => r.Name);

    Action<string, FamilyInstanceReferenceType> setRef = (name, type) =>
    {
        if (lookup.ContainsKey(name))
            lookup[name].IsReference = type;
    };

    setRef("Window_Left",        FamilyInstanceReferenceType.Left);
    setRef("Window_Right",       FamilyInstanceReferenceType.Right);
    setRef("Ref. Level",         FamilyInstanceReferenceType.Bottom);
    setRef("Window_Top",         FamilyInstanceReferenceType.Top);
    setRef("Center (Left/Right)",FamilyInstanceReferenceType.CenterLeftRight);
    setRef("Center (Front/Back)",FamilyInstanceReferenceType.CenterFrontBack);

    tx.Commit();
}"""))

        # IsReference for a generic annotation family
        samples.append(_s(
            "Explain why reference planes in a Generic Annotation family should be set to NotAReference",
            """\
using Autodesk.Revit.DB;

// In Generic Annotation families:
//   - The elements are 2D symbols placed in views, not 3D geometry.
//   - Reference planes serve as construction guides during authoring.
//   - They should NOT appear as snapping targets in the project, because
//     annotations do not need to be dimensioned or aligned to in 3D context.
//
// Best practice: set all reference planes to NotAReference in annotation families.

using (Transaction tx = new Transaction(familyDoc, "Hide All Annotation Ref Planes"))
{
    tx.Start();

    var planes = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane))
        .Cast<ReferencePlane>()
        .ToList();

    foreach (ReferencePlane rp in planes)
        rp.IsReference = FamilyInstanceReferenceType.NotAReference;

    tx.Commit();
}"""))

        return samples
