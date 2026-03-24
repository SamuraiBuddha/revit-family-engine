"""Training data generator: structural Revit families (columns, beams, braces, connections).

Produces ~250 Alpaca-format training pairs covering:
- Rectangular and circular concrete columns
- Steel wide-flange (W-shape) beams
- Steel HSS rectangular and round sections
- Steel angle profiles (equal and unequal leg)
- Concrete beams (rectangular, T-beam, L-beam)
- Diagonal brace families with gusset plates
- Column base plates with anchor bolt patterns
- Structural beam-to-column connections
- Reinforcement void patterns with clear cover

All lengths in Revit internal units (feet).  1 ft = 304.8 mm.
FamilyManager operations are placed OUTSIDE Transaction blocks.
Geometry creation is placed INSIDE Transaction blocks.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

SAMPLE = Dict[str, Any]
MM_TO_FT = 1.0 / 304.8


def _s(instruction: str, output: str) -> SAMPLE:
    return {"instruction": instruction, "input": "", "output": output}


def _ft(mm: float) -> str:
    """Convert mm to feet and return a 6-decimal string."""
    return f"{mm * MM_TO_FT:.6f}"


class StructuralFamilyGenerator:
    """Generates training samples for structural Revit family creation."""

    def generate(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []
        samples += self._rectangular_columns()
        samples += self._circular_columns()
        samples += self._steel_wide_flange()
        samples += self._steel_hss()
        samples += self._steel_angles()
        samples += self._concrete_beams()
        samples += self._braces()
        samples += self._base_plates()
        samples += self._structural_connections()
        samples += self._reinforcement_voids()
        return samples

    # ------------------------------------------------------------------
    # 1. Rectangular concrete columns  (~30 samples)
    # ------------------------------------------------------------------

    def _rectangular_columns(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        # (b_mm, d_mm, h_mm, description)
        cases = [
            (250, 250, 2700, "250x250mm square column, 2.7 m tall"),
            (250, 350, 2700, "250x350mm rectangular column, 2.7 m tall"),
            (300, 300, 3000, "300x300mm square column, 3 m tall"),
            (300, 400, 3000, "300x400mm rectangular column, 3 m tall"),
            (300, 450, 3000, "300x450mm rectangular column, 3 m tall"),
            (350, 350, 3300, "350x350mm square column, 3.3 m tall"),
            (350, 500, 3300, "350x500mm rectangular column, 3.3 m tall"),
            (400, 400, 3600, "400x400mm square column, 3.6 m tall"),
            (400, 550, 3600, "400x550mm rectangular column, 3.6 m tall"),
            (400, 600, 3600, "400x600mm rectangular column, 3.6 m tall"),
            (450, 450, 4000, "450x450mm square column, 4 m tall"),
            (450, 650, 4000, "450x650mm rectangular column, 4 m tall"),
            (500, 500, 4000, "500x500mm square column, 4 m tall"),
            (500, 700, 4000, "500x700mm rectangular column, 4 m tall"),
            (500, 750, 4500, "500x750mm rectangular column, 4.5 m tall"),
            (600, 600, 4500, "600x600mm square column, 4.5 m tall"),
            (600, 800, 4500, "600x800mm rectangular column, 4.5 m tall"),
            (600, 900, 5000, "600x900mm rectangular column, 5 m tall"),
            (700, 700, 5000, "700x700mm square column, 5 m tall"),
            (750, 750, 5000, "750x750mm square column, 5 m tall"),
            (800, 800, 5500, "800x800mm square column, 5.5 m tall"),
            (800, 1000, 5500, "800x1000mm rectangular column, 5.5 m tall"),
            (900, 900, 6000, "900x900mm square column, 6 m tall"),
            (1000, 1000, 6000, "1000x1000mm square column, 6 m tall"),
        ]

        for b, d, h, desc in cases:
            b_ft = b * MM_TO_FT
            d_ft = d * MM_TO_FT
            h_ft = h * MM_TO_FT
            samples.append(_s(
                f"Create a parametric concrete rectangular column family: {desc}. "
                "Include 'b' (width) and 'd' (depth) length parameters.",
                f"""\
using Autodesk.Revit.DB;

// Rectangular concrete column: {b} x {d} mm cross-section, {h} mm height
// Parameters are added OUTSIDE transactions per Revit API rules.
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pB = famMgr.AddParameter(
    "b", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pD = famMgr.AddParameter(
    "d", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pH = famMgr.AddParameter(
    "Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pB, {b_ft:.6f}); // {b} mm
famMgr.Set(pD, {d_ft:.6f}); // {d} mm
famMgr.Set(pH, {h_ft:.6f}); // {h} mm

using (Transaction tx = new Transaction(familyDoc, "Create Rectangular Column"))
{{
    tx.Start();

    double b = {b_ft:.6f}; // {b} mm
    double d = {d_ft:.6f}; // {d} mm
    double h = {h_ft:.6f}; // {h} mm

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-b/2, -d/2, 0), new XYZ( b/2, -d/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( b/2, -d/2, 0), new XYZ( b/2,  d/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( b/2,  d/2, 0), new XYZ(-b/2,  d/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-b/2,  d/2, 0), new XYZ(-b/2, -d/2, 0)));
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    Extrusion col = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    // Assign concrete material parameter
    FamilyParameter matParam = famMgr.AddParameter(
        "Structural Material",
        BuiltInParameterGroup.PG_MATERIALS,
        ParameterType.Material,
        true);

    tx.Commit();
}}""",
            ))

        # Additional samples: chamfered corner column
        samples.append(_s(
            "Create a 500x500mm concrete column with 50mm chamfered corners, 4 m tall",
            f"""\
using Autodesk.Revit.DB;

// Chamfered corner column: 500x500mm with 50mm chamfers
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pB = famMgr.AddParameter(
    "b", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pB, {500 * MM_TO_FT:.6f}); // 500 mm

using (Transaction tx = new Transaction(familyDoc, "Create Chamfered Column"))
{{
    tx.Start();

    double b  = {500 * MM_TO_FT:.6f}; // 500 mm
    double c  = {50  * MM_TO_FT:.6f}; // 50 mm chamfer
    double h  = {4000 * MM_TO_FT:.6f}; // 4000 mm

    // 8-point octagon-like profile
    CurveArray loop = new CurveArray();
    double h2 = b / 2;
    loop.Append(Line.CreateBound(new XYZ(-(h2-c), -h2,    0), new XYZ( (h2-c), -h2,    0)));
    loop.Append(Line.CreateBound(new XYZ(  h2-c,  -h2,    0), new XYZ(  h2,   -(h2-c), 0)));
    loop.Append(Line.CreateBound(new XYZ(  h2,   -(h2-c), 0), new XYZ(  h2,    (h2-c), 0)));
    loop.Append(Line.CreateBound(new XYZ(  h2,    (h2-c), 0), new XYZ(  h2-c,   h2,    0)));
    loop.Append(Line.CreateBound(new XYZ(  h2-c,   h2,    0), new XYZ(-(h2-c),  h2,    0)));
    loop.Append(Line.CreateBound(new XYZ(-(h2-c),  h2,    0), new XYZ( -h2,    (h2-c), 0)));
    loop.Append(Line.CreateBound(new XYZ( -h2,    (h2-c), 0), new XYZ( -h2,   -(h2-c), 0)));
    loop.Append(Line.CreateBound(new XYZ( -h2,   -(h2-c), 0), new XYZ(-(h2-c), -h2,    0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    Extrusion col = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    tx.Commit();
}}""",
        ))

        # Hollow rectangular column (box column)
        for (b, d, t, h, desc) in [
            (500, 500, 75, 4000, "500x500mm box column 75mm wall"),
            (600, 600, 100, 5000, "600x600mm box column 100mm wall"),
        ]:
            b_ft = b * MM_TO_FT
            d_ft = d * MM_TO_FT
            t_ft = t * MM_TO_FT
            h_ft = h * MM_TO_FT
            samples.append(_s(
                f"Create a hollow rectangular (box) concrete column: {desc}, {h} mm tall",
                f"""\
using Autodesk.Revit.DB;

// Hollow box column: {b}x{d}mm outer, {t}mm wall thickness, {h}mm height
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pB = famMgr.AddParameter(
    "b", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pD = famMgr.AddParameter(
    "d", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pT = famMgr.AddParameter(
    "WallThickness", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pB, {b_ft:.6f}); // {b} mm
famMgr.Set(pD, {d_ft:.6f}); // {d} mm
famMgr.Set(pT, {t_ft:.6f}); // {t} mm

using (Transaction tx = new Transaction(familyDoc, "Create Box Column"))
{{
    tx.Start();

    double b  = {b_ft:.6f}; // {b} mm
    double d  = {d_ft:.6f}; // {d} mm
    double t  = {t_ft:.6f}; // {t} mm wall
    double h  = {h_ft:.6f}; // {h} mm height
    double bi = b - 2 * t;   // inner width
    double di = d - 2 * t;   // inner depth

    // Outer loop
    CurveArray outerLoop = new CurveArray();
    outerLoop.Append(Line.CreateBound(new XYZ(-b/2, -d/2, 0), new XYZ( b/2, -d/2, 0)));
    outerLoop.Append(Line.CreateBound(new XYZ( b/2, -d/2, 0), new XYZ( b/2,  d/2, 0)));
    outerLoop.Append(Line.CreateBound(new XYZ( b/2,  d/2, 0), new XYZ(-b/2,  d/2, 0)));
    outerLoop.Append(Line.CreateBound(new XYZ(-b/2,  d/2, 0), new XYZ(-b/2, -d/2, 0)));

    // Inner void loop (counter-clockwise winding for hole)
    CurveArray innerLoop = new CurveArray();
    innerLoop.Append(Line.CreateBound(new XYZ(-bi/2, -di/2, 0), new XYZ(-bi/2,  di/2, 0)));
    innerLoop.Append(Line.CreateBound(new XYZ(-bi/2,  di/2, 0), new XYZ( bi/2,  di/2, 0)));
    innerLoop.Append(Line.CreateBound(new XYZ( bi/2,  di/2, 0), new XYZ( bi/2, -di/2, 0)));
    innerLoop.Append(Line.CreateBound(new XYZ( bi/2, -di/2, 0), new XYZ(-bi/2, -di/2, 0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(outerLoop);
    profile.Append(innerLoop); // inner loop creates the hollow void

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    Extrusion col = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    tx.Commit();
}}""",
            ))

        return samples

    # ------------------------------------------------------------------
    # 2. Circular concrete columns  (~25 samples)
    # ------------------------------------------------------------------

    def _circular_columns(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        # (diameter_mm, h_mm, description)
        cases = [
            (250, 2700, "250mm diameter round column, 2.7 m tall"),
            (300, 3000, "300mm diameter round column, 3 m tall"),
            (350, 3500, "350mm diameter round column, 3.5 m tall"),
            (400, 3600, "400mm diameter round column, 3.6 m tall"),
            (450, 4000, "450mm diameter round column, 4 m tall"),
            (500, 4000, "500mm diameter round column, 4 m tall"),
            (550, 4500, "550mm diameter round column, 4.5 m tall"),
            (600, 4500, "600mm diameter round column, 4.5 m tall"),
            (650, 5000, "650mm diameter round column, 5 m tall"),
            (700, 5000, "700mm diameter round column, 5 m tall"),
            (750, 5500, "750mm diameter round column, 5.5 m tall"),
            (800, 5500, "800mm diameter round column, 5.5 m tall"),
            (900, 6000, "900mm diameter round column, 6 m tall"),
            (1000, 6000, "1000mm diameter round column, 6 m tall"),
            (1200, 7000, "1200mm diameter pile cap column, 7 m tall"),
        ]

        for dia, h, desc in cases:
            r = dia / 2
            r_ft = r * MM_TO_FT
            h_ft = h * MM_TO_FT
            dia_ft = dia * MM_TO_FT
            samples.append(_s(
                f"Create a parametric circular concrete column family: {desc}. "
                "Include a 'Diameter' length parameter.",
                f"""\
using Autodesk.Revit.DB;
using System;

// Circular column via revolution: diameter {dia} mm, height {h} mm
// Revolution approach: revolve a rectangular profile 360 degrees around Z-axis
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pDia = famMgr.AddParameter(
    "Diameter", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pH = famMgr.AddParameter(
    "Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pDia, {dia_ft:.6f}); // {dia} mm
famMgr.Set(pH,   {h_ft:.6f});   // {h} mm

using (Transaction tx = new Transaction(familyDoc, "Create Circular Column"))
{{
    tx.Start();

    double r = {r_ft:.6f}; // radius = {r} mm
    double h = {h_ft:.6f}; // height = {h} mm

    // Profile in the XZ plane: rectangle from (0,0,0) to (r,0,h)
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(0, 0, 0), new XYZ(r, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ(r, 0, 0), new XYZ(r, 0, h)));
    loop.Append(Line.CreateBound(new XYZ(r, 0, h), new XYZ(0, 0, h)));
    loop.Append(Line.CreateBound(new XYZ(0, 0, h), new XYZ(0, 0, 0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    // Axis of revolution: Z-axis
    Line axis = Line.CreateBound(XYZ.Zero, new XYZ(0, 0, 1));

    Revolution col = familyDoc.FamilyCreate.NewRevolution(
        true, profile, sp, axis,
        0.0,                          // start angle
        2.0 * Math.PI);               // end angle: full 360 degrees

    tx.Commit();
}}""",
            ))

        # Hollow circular column (pipe pile / circular shell)
        for (dia, t, h, desc) in [
            (600, 80, 4500, "600mm dia hollow 80mm wall"),
            (800, 100, 6000, "800mm dia hollow 100mm wall"),
        ]:
            r_outer = dia / 2
            r_inner = r_outer - t
            ro_ft = r_outer * MM_TO_FT
            ri_ft = r_inner * MM_TO_FT
            h_ft = h * MM_TO_FT
            samples.append(_s(
                f"Create a hollow circular concrete column (pipe pile): {desc}, {h} mm tall",
                f"""\
using Autodesk.Revit.DB;
using System;

// Hollow circular column via revolution of annular profile
// Outer diameter {dia} mm, wall thickness {t} mm, height {h} mm
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pOD = famMgr.AddParameter(
    "OuterDiameter", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pWT = famMgr.AddParameter(
    "WallThickness",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pOD, {dia * MM_TO_FT:.6f}); // {dia} mm
famMgr.Set(pWT, {t   * MM_TO_FT:.6f}); // {t} mm

using (Transaction tx = new Transaction(familyDoc, "Create Hollow Circular Column"))
{{
    tx.Start();

    double ro = {ro_ft:.6f}; // outer radius {r_outer} mm
    double ri = {ri_ft:.6f}; // inner radius {r_inner} mm
    double h  = {h_ft:.6f};  // height {h} mm

    // Annular profile: outer rect minus inner rect, same height
    CurveArray loop = new CurveArray();
    // Clockwise outer, counter-clockwise inner in same loop (annular ring)
    loop.Append(Line.CreateBound(new XYZ(ri, 0, 0), new XYZ(ro, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ(ro, 0, 0), new XYZ(ro, 0, h)));
    loop.Append(Line.CreateBound(new XYZ(ro, 0, h), new XYZ(ri, 0, h)));
    loop.Append(Line.CreateBound(new XYZ(ri, 0, h), new XYZ(ri, 0, 0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    Line axis = Line.CreateBound(XYZ.Zero, new XYZ(0, 0, 1));

    Revolution col = familyDoc.FamilyCreate.NewRevolution(
        true, profile, sp, axis, 0.0, 2.0 * Math.PI);

    tx.Commit();
}}""",
            ))

        # Polygon approximation variant
        samples.append(_s(
            "Create a 500mm diameter circular column using a 32-segment polygon extrusion",
            f"""\
using Autodesk.Revit.DB;
using System;

// 32-segment polygon approximation for circular column
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pDia = famMgr.AddParameter(
    "Diameter", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pDia, {500 * MM_TO_FT:.6f}); // 500 mm

using (Transaction tx = new Transaction(familyDoc, "Create Polygon Column"))
{{
    tx.Start();

    double r = {250 * MM_TO_FT:.6f}; // 250 mm radius
    double h = {4000 * MM_TO_FT:.6f}; // 4000 mm height
    int n = 32; // segments

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

    Extrusion col = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    tx.Commit();
}}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # 3. Steel wide-flange (W-shape) beams  (~30 samples)
    # ------------------------------------------------------------------

    def _steel_wide_flange(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        # (designation, d_mm, bf_mm, tf_mm, tw_mm, description)
        # AISC standard W-shapes (metric equivalents)
        cases = [
            ("W150x13",   150, 100, 7.1,  4.9,  "W150x13 light beam"),
            ("W150x22",   152, 152, 6.6,  5.8,  "W150x22 square light beam"),
            ("W200x19",   203, 102, 7.7,  5.8,  "W200x19 light beam"),
            ("W200x36",   201, 165, 10.2, 6.2,  "W200x36 medium beam"),
            ("W200x52",   206, 204, 12.6, 7.9,  "W200x52 wide-flange column"),
            ("W250x28",   260, 102, 9.7,  6.1,  "W250x28 light beam"),
            ("W250x58",   252, 203, 13.5, 8.0,  "W250x58 medium beam"),
            ("W250x89",   260, 256, 17.3, 10.7, "W250x89 heavy column"),
            ("W310x39",   315, 165, 9.7,  5.8,  "W310x39 medium beam"),
            ("W310x74",   310, 205, 16.3, 9.4,  "W310x74 heavy beam"),
            ("W310x118",  314, 307, 18.7, 11.9, "W310x118 heavy column section"),
            ("W360x51",   355, 171, 11.6, 7.2,  "W360x51 medium beam"),
            ("W360x91",   353, 254, 16.4, 9.5,  "W360x91 heavy beam"),
            ("W360x134",  356, 369, 18.0, 11.2, "W360x134 heavy column"),
            ("W410x46",   403, 140, 11.2, 6.9,  "W410x46 medium beam"),
            ("W410x85",   417, 181, 18.2, 10.9, "W410x85 heavy beam"),
            ("W410x132",  420, 261, 20.6, 12.8, "W410x132 very heavy beam"),
            ("W460x52",   450, 152, 10.8, 7.6,  "W460x52 medium beam"),
            ("W460x97",   466, 193, 19.0, 11.4, "W460x97 heavy beam"),
            ("W460x158",  476, 284, 23.9, 15.0, "W460x158 very heavy beam"),
            ("W530x66",   525, 165, 11.4, 8.9,  "W530x66 medium beam"),
            ("W530x109",  539, 182, 18.8, 11.6, "W530x109 heavy beam"),
            ("W610x82",   599, 178, 12.8, 10.0, "W610x82 long-span beam"),
            ("W610x140",  617, 230, 22.2, 13.1, "W610x140 heavy long-span beam"),
            ("W690x125",  678, 253, 16.3, 11.7, "W690x125 deep beam"),
            ("W760x147",  753, 265, 17.0, 13.2, "W760x147 very deep beam"),
            ("W840x176",  835, 292, 18.8, 14.0, "W840x176 transfer girder"),
            ("W920x201",  903, 304, 20.1, 15.2, "W920x201 heavy transfer girder"),
            ("W1000x222", 970, 300, 21.1, 16.0, "W1000x222 bridge girder"),
            ("W1100x314",1090, 400, 26.9, 19.0, "W1100x314 heavy bridge girder"),
        ]

        for desig, d, bf, tf, tw, desc in cases:
            d_ft  = d  * MM_TO_FT
            bf_ft = bf * MM_TO_FT
            tf_ft = tf * MM_TO_FT
            tw_ft = tw * MM_TO_FT
            web_h = d - 2 * tf  # clear web height
            wh_ft = web_h * MM_TO_FT
            samples.append(_s(
                f"Create a parametric steel wide-flange beam family for {desig} ({desc}). "
                "Include bf (flange width), d (depth), tf (flange thickness), tw (web thickness) parameters.",
                f"""\
using Autodesk.Revit.DB;

// Steel W-shape: {desig}
// d={d}mm  bf={bf}mm  tf={tf}mm  tw={tw}mm
// Profile centred on origin, swept along beam length
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pD  = famMgr.AddParameter(
    "d",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pBf = famMgr.AddParameter(
    "bf", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pTf = famMgr.AddParameter(
    "tf", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pTw = famMgr.AddParameter(
    "tw", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pL  = famMgr.AddParameter(
    "Length", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pD,  {d_ft:.6f});  // {d} mm
famMgr.Set(pBf, {bf_ft:.6f}); // {bf} mm
famMgr.Set(pTf, {tf_ft:.6f}); // {tf} mm
famMgr.Set(pTw, {tw_ft:.6f}); // {tw} mm
famMgr.Set(pL,  {6000 * MM_TO_FT:.6f}); // default 6000 mm span

using (Transaction tx = new Transaction(familyDoc, "Create W-Shape Profile"))
{{
    tx.Start();

    double d  = {d_ft:.6f};  // {d} mm
    double bf = {bf_ft:.6f}; // {bf} mm
    double tf = {tf_ft:.6f}; // {tf} mm
    double tw = {tw_ft:.6f}; // {tw} mm
    double wh = {wh_ft:.6f}; // web height = {web_h:.1f} mm

    // I-section profile in YZ plane (X=0), beam runs along X
    // Points defined bottom-flange -> web -> top-flange, clockwise
    CurveArray loop = new CurveArray();

    // Bottom flange (at z = -d/2)
    loop.Append(Line.CreateBound(new XYZ(0, -bf/2, -d/2),       new XYZ(0,  bf/2, -d/2)));
    loop.Append(Line.CreateBound(new XYZ(0,  bf/2, -d/2),       new XYZ(0,  bf/2, -d/2 + tf)));
    loop.Append(Line.CreateBound(new XYZ(0,  bf/2, -d/2 + tf),  new XYZ(0,  tw/2, -d/2 + tf)));
    // Web right side
    loop.Append(Line.CreateBound(new XYZ(0,  tw/2, -d/2 + tf),  new XYZ(0,  tw/2,  d/2 - tf)));
    // Top flange right
    loop.Append(Line.CreateBound(new XYZ(0,  tw/2,  d/2 - tf),  new XYZ(0,  bf/2,  d/2 - tf)));
    loop.Append(Line.CreateBound(new XYZ(0,  bf/2,  d/2 - tf),  new XYZ(0,  bf/2,  d/2)));
    loop.Append(Line.CreateBound(new XYZ(0,  bf/2,  d/2),       new XYZ(0, -bf/2,  d/2)));
    // Top flange left
    loop.Append(Line.CreateBound(new XYZ(0, -bf/2,  d/2),       new XYZ(0, -bf/2,  d/2 - tf)));
    loop.Append(Line.CreateBound(new XYZ(0, -bf/2,  d/2 - tf),  new XYZ(0, -tw/2,  d/2 - tf)));
    // Web left side
    loop.Append(Line.CreateBound(new XYZ(0, -tw/2,  d/2 - tf),  new XYZ(0, -tw/2, -d/2 + tf)));
    // Bottom flange left
    loop.Append(Line.CreateBound(new XYZ(0, -tw/2, -d/2 + tf),  new XYZ(0, -bf/2, -d/2 + tf)));
    loop.Append(Line.CreateBound(new XYZ(0, -bf/2, -d/2 + tf),  new XYZ(0, -bf/2, -d/2)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    double L = {6000 * MM_TO_FT:.6f}; // 6000 mm span

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero));

    Extrusion beam = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, L);

    tx.Commit();
}}""",
            ))

        return samples

    # ------------------------------------------------------------------
    # 4. Steel HSS sections  (~25 samples)
    # ------------------------------------------------------------------

    def _steel_hss(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        # HSS rectangular: (H_mm, B_mm, t_mm, description)
        rect_cases = [
            (75,  75,  4,  "HSS 75x75x4 light square tube"),
            (100, 50,  4,  "HSS 100x50x4 flat rectangular tube"),
            (100, 100, 5,  "HSS 100x100x5 square tube"),
            (125, 75,  5,  "HSS 125x75x5 rectangular tube"),
            (150, 100, 6,  "HSS 150x100x6 rectangular tube"),
            (150, 150, 6,  "HSS 150x150x6 square tube"),
            (175, 100, 6,  "HSS 175x100x6 rectangular tube"),
            (175, 175, 8,  "HSS 175x175x8 square tube"),
            (200, 100, 8,  "HSS 200x100x8 rectangular tube"),
            (200, 150, 8,  "HSS 200x150x8 rectangular tube"),
            (200, 200, 10, "HSS 200x200x10 square tube"),
            (250, 125, 10, "HSS 250x125x10 rectangular tube"),
            (250, 150, 10, "HSS 250x150x10 rectangular tube"),
            (250, 250, 12, "HSS 250x250x12 square tube"),
            (300, 150, 12, "HSS 300x150x12 rectangular tube"),
            (300, 200, 12, "HSS 300x200x12 rectangular tube"),
            (300, 300, 16, "HSS 300x300x16 square tube"),
            (350, 250, 16, "HSS 350x250x16 rectangular tube"),
            (400, 300, 16, "HSS 400x300x16 rectangular tube"),
            (400, 400, 20, "HSS 400x400x20 heavy square tube"),
        ]

        for H, B, t, desc in rect_cases:
            H_ft = H * MM_TO_FT
            B_ft = B * MM_TO_FT
            t_ft = t * MM_TO_FT
            Hi = H - 2 * t
            Bi = B - 2 * t
            Hi_ft = Hi * MM_TO_FT
            Bi_ft = Bi * MM_TO_FT
            samples.append(_s(
                f"Create a parametric steel HSS rectangular section family: {desc}. "
                "Include H (height), B (width), t (wall thickness) parameters.",
                f"""\
using Autodesk.Revit.DB;

// Steel HSS Rectangular: {H}x{B}x{t} mm
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pH = famMgr.AddParameter(
    "H", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pB = famMgr.AddParameter(
    "B", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pT = famMgr.AddParameter(
    "t", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pL = famMgr.AddParameter(
    "Length", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pH, {H_ft:.6f}); // {H} mm
famMgr.Set(pB, {B_ft:.6f}); // {B} mm
famMgr.Set(pT, {t_ft:.6f}); // {t} mm
famMgr.Set(pL, {6000 * MM_TO_FT:.6f}); // 6000 mm default span

using (Transaction tx = new Transaction(familyDoc, "Create HSS Rect Section"))
{{
    tx.Start();

    double H  = {H_ft:.6f}; // {H} mm
    double B  = {B_ft:.6f}; // {B} mm
    double t  = {t_ft:.6f}; // {t} mm wall
    double Hi = {Hi_ft:.6f}; // inner height {Hi} mm
    double Bi = {Bi_ft:.6f}; // inner width {Bi} mm
    double L  = {6000 * MM_TO_FT:.6f}; // 6000 mm

    // Outer rectangle (CW)
    CurveArray outerLoop = new CurveArray();
    outerLoop.Append(Line.CreateBound(new XYZ(0, -B/2, -H/2), new XYZ(0,  B/2, -H/2)));
    outerLoop.Append(Line.CreateBound(new XYZ(0,  B/2, -H/2), new XYZ(0,  B/2,  H/2)));
    outerLoop.Append(Line.CreateBound(new XYZ(0,  B/2,  H/2), new XYZ(0, -B/2,  H/2)));
    outerLoop.Append(Line.CreateBound(new XYZ(0, -B/2,  H/2), new XYZ(0, -B/2, -H/2)));

    // Inner rectangle (CCW creates void/hole in profile)
    CurveArray innerLoop = new CurveArray();
    innerLoop.Append(Line.CreateBound(new XYZ(0, -Bi/2, -Hi/2), new XYZ(0, -Bi/2,  Hi/2)));
    innerLoop.Append(Line.CreateBound(new XYZ(0, -Bi/2,  Hi/2), new XYZ(0,  Bi/2,  Hi/2)));
    innerLoop.Append(Line.CreateBound(new XYZ(0,  Bi/2,  Hi/2), new XYZ(0,  Bi/2, -Hi/2)));
    innerLoop.Append(Line.CreateBound(new XYZ(0,  Bi/2, -Hi/2), new XYZ(0, -Bi/2, -Hi/2)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(outerLoop);
    profile.Append(innerLoop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero));

    Extrusion hss = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, L);

    tx.Commit();
}}""",
            ))

        # HSS round: (OD_mm, t_mm, description)
        round_cases = [
            (60,   4,  "HSS 60x4 light round tube"),
            (76,   4,  "HSS 76x4 round tube"),
            (89,   5,  "HSS 89x5 round tube"),
            (114,  6,  "HSS 114x6 round tube"),
            (139,  6,  "HSS 139x6 round tube"),
            (141,  8,  "HSS 141x8 round tube"),
            (168,  8,  "HSS 168x8 round tube"),
            (168,  10, "HSS 168x10 round tube"),
            (193,  10, "HSS 193x10 round tube"),
            (219,  10, "HSS 219x10 round tube"),
            (219,  12, "HSS 219x12 round tube"),
            (273,  12, "HSS 273x12 round tube"),
            (273,  16, "HSS 273x16 round tube"),
            (323,  16, "HSS 323x16 heavy round tube"),
            (355,  20, "HSS 355x20 very heavy round tube"),
        ]

        for OD, t, desc in round_cases:
            OD_ft = OD * MM_TO_FT
            t_ft  = t  * MM_TO_FT
            r_o   = OD / 2
            r_i   = r_o - t
            ro_ft = r_o * MM_TO_FT
            ri_ft = r_i * MM_TO_FT
            samples.append(_s(
                f"Create a parametric steel round HSS section family: {desc}. "
                "Include OD (outer diameter) and t (wall thickness) parameters.",
                f"""\
using Autodesk.Revit.DB;
using System;

// Steel HSS Round: OD={OD}mm  t={t}mm
// Created via revolution of annular profile 360 degrees
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pOD = famMgr.AddParameter(
    "OD", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pT  = famMgr.AddParameter(
    "t",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pL  = famMgr.AddParameter(
    "Length", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pOD, {OD_ft:.6f}); // {OD} mm
famMgr.Set(pT,  {t_ft:.6f});  // {t} mm
famMgr.Set(pL,  {6000 * MM_TO_FT:.6f}); // 6000 mm

using (Transaction tx = new Transaction(familyDoc, "Create HSS Round"))
{{
    tx.Start();

    double ro = {ro_ft:.6f}; // outer radius {r_o} mm
    double ri = {ri_ft:.6f}; // inner radius {r_i} mm
    double L  = {6000 * MM_TO_FT:.6f}; // beam length 6000 mm

    // Annular profile in XZ plane revolved around X-axis
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(0,  ri, 0), new XYZ(0,  ro, 0)));
    loop.Append(Line.CreateBound(new XYZ(0,  ro, 0), new XYZ(L,  ro, 0)));
    loop.Append(Line.CreateBound(new XYZ(L,  ro, 0), new XYZ(L,  ri, 0)));
    loop.Append(Line.CreateBound(new XYZ(L,  ri, 0), new XYZ(0,  ri, 0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // Revolve about X-axis
    Line axis = Line.CreateBound(XYZ.Zero, new XYZ(L, 0, 0));

    Revolution hss = familyDoc.FamilyCreate.NewRevolution(
        true, profile, sp, axis, 0.0, 2.0 * Math.PI);

    tx.Commit();
}}""",
            ))

        return samples

    # ------------------------------------------------------------------
    # 5. Steel angle profiles  (~20 samples)
    # ------------------------------------------------------------------

    def _steel_angles(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        # Equal leg angles: (leg_mm, t_mm, description)
        equal_cases = [
            (50,  5,  "L50x50x5 equal angle"),
            (65,  6,  "L65x65x6 equal angle"),
            (75,  6,  "L75x75x6 equal angle"),
            (75,  8,  "L75x75x8 equal angle"),
            (90,  8,  "L90x90x8 equal angle"),
            (100, 10, "L100x100x10 equal angle"),
            (125, 12, "L125x125x12 equal angle"),
            (150, 16, "L150x150x16 equal angle"),
        ]

        for leg, t, desc in equal_cases:
            leg_ft = leg * MM_TO_FT
            t_ft   = t   * MM_TO_FT
            samples.append(_s(
                f"Create a parametric steel equal-leg angle family: {desc}. "
                "Include leg length and thickness parameters.",
                f"""\
using Autodesk.Revit.DB;

// Steel equal-leg angle: {desc}
// Leg={leg}mm  t={t}mm
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pLeg = famMgr.AddParameter(
    "LegLength", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pT   = famMgr.AddParameter(
    "Thickness",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pL   = famMgr.AddParameter(
    "Length",     BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pLeg, {leg_ft:.6f}); // {leg} mm
famMgr.Set(pT,   {t_ft:.6f});   // {t} mm
famMgr.Set(pL,   {3000 * MM_TO_FT:.6f}); // 3000 mm default

using (Transaction tx = new Transaction(familyDoc, "Create Equal Angle"))
{{
    tx.Start();

    double a = {leg_ft:.6f}; // leg length {leg} mm
    double t = {t_ft:.6f};   // thickness {t} mm
    double L = {3000 * MM_TO_FT:.6f}; // 3000 mm length

    // L-shape profile in YZ plane, corner at origin
    // Horizontal leg along +Y, vertical leg along +Z
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(0, 0,   0), new XYZ(0, a,   0)));   // outer bottom
    loop.Append(Line.CreateBound(new XYZ(0, a,   0), new XYZ(0, a,   t)));   // bottom flange tip
    loop.Append(Line.CreateBound(new XYZ(0, a,   t), new XYZ(0, t,   t)));   // bottom top face
    loop.Append(Line.CreateBound(new XYZ(0, t,   t), new XYZ(0, t,   a)));   // web horizontal
    loop.Append(Line.CreateBound(new XYZ(0, t,   a), new XYZ(0, 0,   a)));   // vertical leg tip
    loop.Append(Line.CreateBound(new XYZ(0, 0,   a), new XYZ(0, 0,   0)));   // back to origin

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero));

    Extrusion angle = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, L);

    tx.Commit();
}}""",
            ))

        # Unequal leg angles: (leg1_mm, leg2_mm, t_mm, description)
        unequal_cases = [
            (75,  50, 6,  "L75x50x6 unequal angle"),
            (100, 65, 8,  "L100x65x8 unequal angle"),
            (100, 75, 8,  "L100x75x8 unequal angle"),
            (125, 75, 10, "L125x75x10 unequal angle"),
            (150, 90, 12, "L150x90x12 unequal angle"),
            (200, 100, 16, "L200x100x16 unequal angle"),
        ]

        for a1, a2, t, desc in unequal_cases:
            a1_ft = a1 * MM_TO_FT
            a2_ft = a2 * MM_TO_FT
            t_ft  = t  * MM_TO_FT
            samples.append(_s(
                f"Create a parametric steel unequal-leg angle family: {desc}. "
                "Include LongLeg, ShortLeg, and Thickness parameters.",
                f"""\
using Autodesk.Revit.DB;

// Steel unequal-leg angle: {desc}
// LongLeg={a1}mm  ShortLeg={a2}mm  t={t}mm
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pA1 = famMgr.AddParameter(
    "LongLeg",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pA2 = famMgr.AddParameter(
    "ShortLeg", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pT  = famMgr.AddParameter(
    "Thickness", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pL  = famMgr.AddParameter(
    "Length",    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pA1, {a1_ft:.6f}); // {a1} mm
famMgr.Set(pA2, {a2_ft:.6f}); // {a2} mm
famMgr.Set(pT,  {t_ft:.6f});  // {t} mm
famMgr.Set(pL,  {3000 * MM_TO_FT:.6f}); // 3000 mm

using (Transaction tx = new Transaction(familyDoc, "Create Unequal Angle"))
{{
    tx.Start();

    double a1 = {a1_ft:.6f}; // long leg {a1} mm
    double a2 = {a2_ft:.6f}; // short leg {a2} mm
    double t  = {t_ft:.6f};  // thickness {t} mm
    double L  = {3000 * MM_TO_FT:.6f}; // 3000 mm

    // Unequal L-profile: long leg along Z, short leg along Y
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(0,  0,   0),  new XYZ(0, a2,   0)));  // base bottom
    loop.Append(Line.CreateBound(new XYZ(0, a2,   0),  new XYZ(0, a2,   t)));  // short tip
    loop.Append(Line.CreateBound(new XYZ(0, a2,   t),  new XYZ(0,  t,   t)));  // top of short leg
    loop.Append(Line.CreateBound(new XYZ(0,  t,   t),  new XYZ(0,  t,  a1)));  // web up
    loop.Append(Line.CreateBound(new XYZ(0,  t,  a1),  new XYZ(0,  0,  a1)));  // long tip
    loop.Append(Line.CreateBound(new XYZ(0,  0,  a1),  new XYZ(0,  0,   0)));  // back edge

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero));

    Extrusion angle = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, L);

    tx.Commit();
}}""",
            ))

        return samples

    # ------------------------------------------------------------------
    # 6. Concrete beams  (~30 samples)
    # ------------------------------------------------------------------

    def _concrete_beams(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        # Rectangular beams: (b_mm, h_mm, L_mm, description)
        rect_cases = [
            (200, 350,  3500, "200x350mm rectangular beam"),
            (200, 400,  4000, "200x400mm rectangular beam"),
            (250, 400,  4000, "250x400mm rectangular beam"),
            (250, 500,  5000, "250x500mm rectangular beam"),
            (300, 450,  4500, "300x450mm rectangular beam"),
            (300, 500,  5000, "300x500mm rectangular beam"),
            (300, 600,  6000, "300x600mm rectangular beam"),
            (350, 550,  5500, "350x550mm rectangular beam"),
            (350, 600,  6000, "350x600mm rectangular beam"),
            (350, 700,  7000, "350x700mm rectangular beam"),
            (400, 650,  6500, "400x650mm rectangular beam"),
            (400, 700,  7000, "400x700mm rectangular beam"),
            (400, 800,  8000, "400x800mm rectangular beam"),
            (450, 750,  7500, "450x750mm rectangular beam"),
            (450, 800,  8000, "450x800mm rectangular beam"),
            (500, 900,  9000, "500x900mm rectangular beam"),
            (500, 1000, 10000, "500x1000mm deep beam"),
            (600, 1200, 12000, "600x1200mm transfer beam"),
        ]

        for b, h, L, desc in rect_cases:
            b_ft = b * MM_TO_FT
            h_ft = h * MM_TO_FT
            L_ft = L * MM_TO_FT
            samples.append(_s(
                f"Create a parametric concrete rectangular beam family: {desc}, {L} mm span. "
                "Include b (width) and h (depth) parameters.",
                f"""\
using Autodesk.Revit.DB;

// Concrete rectangular beam: {b}x{h}mm cross-section, {L}mm span
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pB = famMgr.AddParameter(
    "b", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pH = famMgr.AddParameter(
    "h", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pL = famMgr.AddParameter(
    "Length", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pB, {b_ft:.6f}); // {b} mm
famMgr.Set(pH, {h_ft:.6f}); // {h} mm
famMgr.Set(pL, {L_ft:.6f}); // {L} mm

using (Transaction tx = new Transaction(familyDoc, "Create Concrete Beam"))
{{
    tx.Start();

    double b = {b_ft:.6f}; // {b} mm
    double h = {h_ft:.6f}; // {h} mm
    double L = {L_ft:.6f}; // {L} mm

    // Rectangular profile in YZ plane, beam runs along X
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(0, -b/2, -h),   new XYZ(0,  b/2, -h)));
    loop.Append(Line.CreateBound(new XYZ(0,  b/2, -h),   new XYZ(0,  b/2,  0)));
    loop.Append(Line.CreateBound(new XYZ(0,  b/2,  0),   new XYZ(0, -b/2,  0)));
    loop.Append(Line.CreateBound(new XYZ(0, -b/2,  0),   new XYZ(0, -b/2, -h)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero));

    Extrusion beam = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, L);

    tx.Commit();
}}""",
            ))

        # T-beams: (bw_mm, hw_mm, bf_mm, hf_mm, L_mm, description)
        t_cases = [
            (250, 450,  700, 120, 5000, "T-beam 250x450 web, 700x120 flange"),
            (300, 500,  800, 150, 6000, "T-beam 300x500 web, 800x150 flange"),
            (300, 600,  900, 150, 6000, "T-beam 300x600 web, 900x150 flange"),
            (350, 600, 1000, 180, 7000, "T-beam 350x600 web, 1000x180 flange"),
            (400, 700, 1200, 200, 8000, "T-beam 400x700 web, 1200x200 flange"),
            (450, 800, 1400, 220, 9000, "T-beam 450x800 web, 1400x220 flange"),
        ]

        for bw, hw, bf, hf, L, desc in t_cases:
            bw_ft = bw * MM_TO_FT
            hw_ft = hw * MM_TO_FT
            bf_ft = bf * MM_TO_FT
            hf_ft = hf * MM_TO_FT
            L_ft  = L  * MM_TO_FT
            samples.append(_s(
                f"Create a concrete T-beam family: {desc}, {L} mm span. "
                "Include bw (web width), hw (web depth), bf (flange width), hf (flange thickness) parameters.",
                f"""\
using Autodesk.Revit.DB;

// Concrete T-beam: web {bw}x{hw}mm, flange {bf}x{hf}mm, span {L}mm
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pBw = famMgr.AddParameter(
    "bw", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pHw = famMgr.AddParameter(
    "hw", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pBf = famMgr.AddParameter(
    "bf", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pHf = famMgr.AddParameter(
    "hf", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pL  = famMgr.AddParameter(
    "Length", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pBw, {bw_ft:.6f}); // {bw} mm
famMgr.Set(pHw, {hw_ft:.6f}); // {hw} mm
famMgr.Set(pBf, {bf_ft:.6f}); // {bf} mm
famMgr.Set(pHf, {hf_ft:.6f}); // {hf} mm
famMgr.Set(pL,  {L_ft:.6f});  // {L} mm

using (Transaction tx = new Transaction(familyDoc, "Create T-Beam"))
{{
    tx.Start();

    double bw = {bw_ft:.6f}; // web width {bw} mm
    double hw = {hw_ft:.6f}; // web depth {hw} mm
    double bf = {bf_ft:.6f}; // flange width {bf} mm
    double hf = {hf_ft:.6f}; // flange thickness {hf} mm
    double L  = {L_ft:.6f};  // span {L} mm

    // T-section profile: flange at top (z=0), web hanging down
    double totalH = hw + hf;
    CurveArray loop = new CurveArray();
    // Flange top edge (z = 0)
    loop.Append(Line.CreateBound(new XYZ(0, -bf/2, 0),       new XYZ(0,  bf/2, 0)));
    // Right side of flange
    loop.Append(Line.CreateBound(new XYZ(0,  bf/2, 0),       new XYZ(0,  bf/2, -hf)));
    // Step in to web right
    loop.Append(Line.CreateBound(new XYZ(0,  bf/2, -hf),     new XYZ(0,  bw/2, -hf)));
    // Web right side
    loop.Append(Line.CreateBound(new XYZ(0,  bw/2, -hf),     new XYZ(0,  bw/2, -totalH)));
    // Web bottom
    loop.Append(Line.CreateBound(new XYZ(0,  bw/2, -totalH), new XYZ(0, -bw/2, -totalH)));
    // Web left side
    loop.Append(Line.CreateBound(new XYZ(0, -bw/2, -totalH), new XYZ(0, -bw/2, -hf)));
    // Step out to flange left
    loop.Append(Line.CreateBound(new XYZ(0, -bw/2, -hf),     new XYZ(0, -bf/2, -hf)));
    // Left side of flange
    loop.Append(Line.CreateBound(new XYZ(0, -bf/2, -hf),     new XYZ(0, -bf/2, 0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero));

    Extrusion beam = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, L);

    tx.Commit();
}}""",
            ))

        # L-beams (spandrel / edge beams): (b_mm, d_mm, bf_mm, df_mm, L_mm, description)
        l_cases = [
            (250, 500, 150, 120, 4500, "L-beam spandrel 250x500 web, 150x120 ledge"),
            (300, 600, 200, 150, 5000, "L-beam spandrel 300x600 web, 200x150 ledge"),
            (350, 700, 250, 200, 6000, "L-beam spandrel 350x700 web, 250x200 ledge"),
            (400, 800, 300, 200, 7000, "L-beam spandrel 400x800 web, 300x200 ledge"),
        ]

        for b, d, bf, df, L, desc in l_cases:
            b_ft  = b  * MM_TO_FT
            d_ft  = d  * MM_TO_FT
            bf_ft = bf * MM_TO_FT
            df_ft = df * MM_TO_FT
            L_ft  = L  * MM_TO_FT
            samples.append(_s(
                f"Create a concrete L-beam (spandrel beam) family: {desc}, {L} mm span.",
                f"""\
using Autodesk.Revit.DB;

// Concrete L-beam (spandrel): {desc}
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pB  = famMgr.AddParameter(
    "b",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pD  = famMgr.AddParameter(
    "d",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pBf = famMgr.AddParameter(
    "bf", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pDf = famMgr.AddParameter(
    "df", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pL  = famMgr.AddParameter(
    "Length", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pB,  {b_ft:.6f});  // {b} mm
famMgr.Set(pD,  {d_ft:.6f});  // {d} mm
famMgr.Set(pBf, {bf_ft:.6f}); // {bf} mm
famMgr.Set(pDf, {df_ft:.6f}); // {df} mm
famMgr.Set(pL,  {L_ft:.6f});  // {L} mm

using (Transaction tx = new Transaction(familyDoc, "Create L-Beam"))
{{
    tx.Start();

    double b  = {b_ft:.6f};  // main web width {b} mm
    double d  = {d_ft:.6f};  // total depth {d} mm
    double bf = {bf_ft:.6f}; // ledge width {bf} mm
    double df = {df_ft:.6f}; // ledge depth {df} mm
    double L  = {L_ft:.6f};  // span {L} mm

    // L-section: web on one side, ledge on bottom right
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(0, 0,    0),         new XYZ(0, b,    0)));     // top
    loop.Append(Line.CreateBound(new XYZ(0, b,    0),         new XYZ(0, b,   -d)));     // right side
    loop.Append(Line.CreateBound(new XYZ(0, b,   -d),         new XYZ(0, b+bf,-d)));     // ledge bottom
    loop.Append(Line.CreateBound(new XYZ(0, b+bf,-d),         new XYZ(0, b+bf,-(d-df)))); // ledge outer
    loop.Append(Line.CreateBound(new XYZ(0, b+bf,-(d-df)),    new XYZ(0, 0,   -(d-df)))); // not needed
    loop.Append(Line.CreateBound(new XYZ(0, 0,   -(d-df)),    new XYZ(0, 0,    0)));     // left side

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero));

    Extrusion beam = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, L);

    tx.Commit();
}}""",
            ))

        return samples

    # ------------------------------------------------------------------
    # 7. Brace families  (~20 samples)
    # ------------------------------------------------------------------

    def _braces(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        # Diagonal brace HSS sections: (H_mm, B_mm, t_mm, angle_deg, L_mm, description)
        brace_cases = [
            (150, 150, 8,  45, 4243, "HSS 150x150x8 diagonal at 45 deg"),
            (200, 150, 10, 45, 4243, "HSS 200x150x10 diagonal at 45 deg"),
            (200, 200, 10, 45, 5657, "HSS 200x200x10 diagonal at 45 deg"),
            (150, 150, 8,  30, 3464, "HSS 150x150x8 diagonal at 30 deg"),
            (200, 200, 10, 60, 4619, "HSS 200x200x10 diagonal at 60 deg"),
            (250, 150, 12, 45, 4950, "HSS 250x150x12 diagonal brace"),
            (100, 100, 6,  45, 2828, "HSS 100x100x6 light diagonal brace"),
            (125, 125, 8,  45, 3536, "HSS 125x125x8 diagonal brace"),
            (175, 175, 8,  45, 4950, "HSS 175x175x8 diagonal brace"),
            (250, 250, 12, 45, 7071, "HSS 250x250x12 heavy diagonal brace"),
            (300, 200, 12, 45, 6364, "HSS 300x200x12 wide diagonal brace"),
            (300, 300, 16, 45, 8485, "HSS 300x300x16 heavy diagonal brace"),
            (150, 100, 8,  45, 3536, "HSS 150x100x8 eccentric brace"),
            (200, 150, 10, 53, 5000, "HSS 200x150x10 brace at 53 deg"),
            (125, 125, 6,  30, 2887, "HSS 125x125x6 shallow diagonal brace"),
        ]

        for H, B, t, angle, L, desc in brace_cases:
            H_ft  = H * MM_TO_FT
            B_ft  = B * MM_TO_FT
            t_ft  = t * MM_TO_FT
            L_ft  = L * MM_TO_FT
            Hi = H - 2 * t
            Bi = B - 2 * t
            Hi_ft = Hi * MM_TO_FT
            Bi_ft = Bi * MM_TO_FT
            samples.append(_s(
                f"Create a steel HSS diagonal brace family: {desc}. "
                "The brace is oriented along its local X-axis at the specified angle. "
                "Include H, B, t (wall thickness), and Length parameters.",
                f"""\
using Autodesk.Revit.DB;

// Steel HSS diagonal brace: {desc}
// H={H}mm  B={B}mm  t={t}mm  Angle={angle} deg  Length={L}mm
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pH = famMgr.AddParameter(
    "H", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pB = famMgr.AddParameter(
    "B", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pT = famMgr.AddParameter(
    "t", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pL = famMgr.AddParameter(
    "Length", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pH, {H_ft:.6f}); // {H} mm
famMgr.Set(pB, {B_ft:.6f}); // {B} mm
famMgr.Set(pT, {t_ft:.6f}); // {t} mm
famMgr.Set(pL, {L_ft:.6f}); // {L} mm

using (Transaction tx = new Transaction(familyDoc, "Create Brace HSS"))
{{
    tx.Start();

    double H  = {H_ft:.6f};  // {H} mm
    double B  = {B_ft:.6f};  // {B} mm
    double t  = {t_ft:.6f};  // {t} mm wall
    double Hi = {Hi_ft:.6f}; // inner height {Hi} mm
    double Bi = {Bi_ft:.6f}; // inner width {Bi} mm
    double L  = {L_ft:.6f};  // brace length {L} mm

    // Outer rectangle profile at start face (XY plane)
    CurveArray outerLoop = new CurveArray();
    outerLoop.Append(Line.CreateBound(new XYZ(0, -B/2, -H/2), new XYZ(0,  B/2, -H/2)));
    outerLoop.Append(Line.CreateBound(new XYZ(0,  B/2, -H/2), new XYZ(0,  B/2,  H/2)));
    outerLoop.Append(Line.CreateBound(new XYZ(0,  B/2,  H/2), new XYZ(0, -B/2,  H/2)));
    outerLoop.Append(Line.CreateBound(new XYZ(0, -B/2,  H/2), new XYZ(0, -B/2, -H/2)));

    // Inner rectangle (void)
    CurveArray innerLoop = new CurveArray();
    innerLoop.Append(Line.CreateBound(new XYZ(0, -Bi/2, -Hi/2), new XYZ(0, -Bi/2,  Hi/2)));
    innerLoop.Append(Line.CreateBound(new XYZ(0, -Bi/2,  Hi/2), new XYZ(0,  Bi/2,  Hi/2)));
    innerLoop.Append(Line.CreateBound(new XYZ(0,  Bi/2,  Hi/2), new XYZ(0,  Bi/2, -Hi/2)));
    innerLoop.Append(Line.CreateBound(new XYZ(0,  Bi/2, -Hi/2), new XYZ(0, -Bi/2, -Hi/2)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(outerLoop);
    profile.Append(innerLoop);

    // Brace runs along X-axis; family is placed at angle by Revit host
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero));

    Extrusion brace = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, L);

    tx.Commit();
}}""",
            ))

        # Gusset plate for brace connection
        gusset_cases = [
            (300, 300, 12, "300x300mm gusset plate 12mm thick"),
            (400, 400, 16, "400x400mm gusset plate 16mm thick"),
            (500, 500, 20, "500x500mm gusset plate 20mm thick"),
            (600, 400, 20, "600x400mm gusset plate 20mm thick"),
            (600, 500, 25, "600x500mm gusset plate 25mm thick"),
            (700, 600, 25, "700x600mm gusset plate 25mm thick"),
        ]

        for W, H, t, desc in gusset_cases:
            W_ft = W * MM_TO_FT
            H_ft = H * MM_TO_FT
            t_ft = t * MM_TO_FT
            samples.append(_s(
                f"Create a steel gusset plate family for a brace connection: {desc}. "
                "Include Width, Height, and Thickness parameters.",
                f"""\
using Autodesk.Revit.DB;

// Steel gusset plate: {W}x{H}mm, {t}mm thick
// Used to connect diagonal brace to beam/column node
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW = famMgr.AddParameter(
    "Width",     BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pH = famMgr.AddParameter(
    "Height",    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pT = famMgr.AddParameter(
    "Thickness", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pW, {W_ft:.6f}); // {W} mm
famMgr.Set(pH, {H_ft:.6f}); // {H} mm
famMgr.Set(pT, {t_ft:.6f}); // {t} mm

using (Transaction tx = new Transaction(familyDoc, "Create Gusset Plate"))
{{
    tx.Start();

    double W = {W_ft:.6f}; // {W} mm
    double H = {H_ft:.6f}; // {H} mm
    double t = {t_ft:.6f}; // {t} mm

    // Flat plate profile in XY plane
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-W/2, -H/2, 0), new XYZ( W/2, -H/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( W/2, -H/2, 0), new XYZ( W/2,  H/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( W/2,  H/2, 0), new XYZ(-W/2,  H/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-W/2,  H/2, 0), new XYZ(-W/2, -H/2, 0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // Plate thickness extruded in Z direction
    Extrusion plate = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, t);

    tx.Commit();
}}""",
            ))

        return samples

    # ------------------------------------------------------------------
    # 8. Column base plates  (~20 samples)
    # ------------------------------------------------------------------

    def _base_plates(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        # (PL_W_mm, PL_D_mm, PL_t_mm, bolt_rows, bolt_cols, bolt_dia_mm, bolt_edge_mm, description)
        cases = [
            (250, 250, 16, 2, 2, 20, 50,  "250x250x16 base plate, 2x2 anchor bolts M20"),
            (300, 300, 20, 2, 2, 24, 60,  "300x300x20 base plate, 2x2 anchor bolts M24"),
            (350, 350, 20, 2, 2, 24, 70,  "350x350x20 base plate, 2x2 anchor bolts M24"),
            (400, 400, 25, 2, 2, 27, 75,  "400x400x25 base plate, 2x2 anchor bolts M27"),
            (450, 450, 25, 2, 2, 27, 80,  "450x450x25 base plate, 2x2 anchor bolts M27"),
            (500, 500, 30, 2, 2, 30, 90,  "500x500x30 base plate, 2x2 anchor bolts M30"),
            (500, 500, 30, 2, 4, 24, 70,  "500x500x30 base plate, 2x4 anchor bolts M24"),
            (600, 600, 32, 2, 4, 30, 80,  "600x600x32 base plate, 2x4 anchor bolts M30"),
            (600, 400, 25, 2, 2, 24, 70,  "600x400x25 base plate, 2x2 anchor bolts M24"),
            (700, 500, 32, 2, 4, 27, 75,  "700x500x32 base plate, 2x4 anchor bolts M27"),
            (700, 700, 40, 4, 4, 30, 80,  "700x700x40 base plate, 4x4 anchor bolts M30"),
            (750, 750, 40, 2, 4, 30, 80,  "750x750x40 base plate, 2x4 anchor bolts M30"),
            (800, 800, 40, 4, 4, 36, 90,  "800x800x40 base plate, 4x4 anchor bolts M36"),
            (900, 900, 50, 4, 4, 36, 100, "900x900x50 base plate, 4x4 anchor bolts M36"),
            (1000,1000,50, 4, 4, 42, 100, "1000x1000x50 base plate, 4x4 anchor bolts M42"),
        ]

        for PW, PD, PT, rows, cols, bolt_d, edge, desc in cases:
            PW_ft    = PW    * MM_TO_FT
            PD_ft    = PD    * MM_TO_FT
            PT_ft    = PT    * MM_TO_FT
            bolt_ft  = bolt_d * MM_TO_FT
            edge_ft  = edge  * MM_TO_FT
            # Bolt spacing
            sp_x = (PW - 2 * edge) / max(cols - 1, 1)
            sp_z = (PD - 2 * edge) / max(rows - 1, 1)
            sp_x_ft = sp_x * MM_TO_FT
            sp_z_ft = sp_z * MM_TO_FT
            samples.append(_s(
                f"Create a steel column base plate family: {desc}. "
                "Include PlateWidth, PlateDepth, PlateThickness, BoltDiameter, EdgeDistance parameters. "
                "Place anchor bolt void cylinders in the correct pattern.",
                f"""\
using Autodesk.Revit.DB;
using System;

// Column base plate: {PW}x{PD}x{PT}mm, {rows}x{cols} M{bolt_d} anchor bolts
// Edge distance = {edge}mm
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pPW = famMgr.AddParameter(
    "PlateWidth",     BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pPD = famMgr.AddParameter(
    "PlateDepth",     BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pPT = famMgr.AddParameter(
    "PlateThickness", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pBD = famMgr.AddParameter(
    "BoltDiameter",   BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pED = famMgr.AddParameter(
    "EdgeDistance",   BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pPW, {PW_ft:.6f});   // {PW} mm
famMgr.Set(pPD, {PD_ft:.6f});   // {PD} mm
famMgr.Set(pPT, {PT_ft:.6f});   // {PT} mm
famMgr.Set(pBD, {bolt_ft:.6f}); // {bolt_d} mm bolt diameter
famMgr.Set(pED, {edge_ft:.6f}); // {edge} mm edge distance

using (Transaction tx = new Transaction(familyDoc, "Create Base Plate"))
{{
    tx.Start();

    double PW   = {PW_ft:.6f};   // plate width {PW} mm
    double PD   = {PD_ft:.6f};   // plate depth {PD} mm
    double PT   = {PT_ft:.6f};   // plate thickness {PT} mm
    double bdR  = {(bolt_d / 2) * MM_TO_FT:.6f}; // bolt radius {bolt_d / 2} mm
    double edge = {edge_ft:.6f}; // edge distance {edge} mm
    int rows    = {rows};
    int cols    = {cols};

    // --- Steel plate (solid extrusion) ---
    CurveArray plateLoop = new CurveArray();
    plateLoop.Append(Line.CreateBound(new XYZ(-PW/2, -PD/2, 0), new XYZ( PW/2, -PD/2, 0)));
    plateLoop.Append(Line.CreateBound(new XYZ( PW/2, -PD/2, 0), new XYZ( PW/2,  PD/2, 0)));
    plateLoop.Append(Line.CreateBound(new XYZ( PW/2,  PD/2, 0), new XYZ(-PW/2,  PD/2, 0)));
    plateLoop.Append(Line.CreateBound(new XYZ(-PW/2,  PD/2, 0), new XYZ(-PW/2, -PD/2, 0)));

    CurveArrArray plateProfile = new CurveArrArray();
    plateProfile.Append(plateLoop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    Extrusion plate = familyDoc.FamilyCreate.NewExtrusion(
        true, plateProfile, sp, -PT); // extrude downward

    // --- Anchor bolt void cylinders ({rows}x{cols} pattern) ---
    double spX = {sp_x_ft:.6f}; // bolt spacing X = {sp_x:.1f} mm
    double spZ = {sp_z_ft:.6f}; // bolt spacing Z = {sp_z:.1f} mm
    int n      = 32; // polygon segments per bolt hole

    double x0  = -PW/2 + edge;
    double z0  = -PD/2 + edge;

    for (int row = 0; row < rows; row++)
    {{
        for (int col = 0; col < cols; col++)
        {{
            double cx = x0 + col * spX;
            double cz = z0 + row * spZ;

            CurveArray boltLoop = new CurveArray();
            for (int i = 0; i < n; i++)
            {{
                double a0 = 2 * Math.PI * i / n;
                double a1 = 2 * Math.PI * (i + 1) / n;
                XYZ p0 = new XYZ(cx + bdR * Math.Cos(a0), cz + bdR * Math.Sin(a0), 0);
                XYZ p1 = new XYZ(cx + bdR * Math.Cos(a1), cz + bdR * Math.Sin(a1), 0);
                boltLoop.Append(Line.CreateBound(p0, p1));
            }}

            CurveArrArray boltProfile = new CurveArrArray();
            boltProfile.Append(boltLoop);

            // Void cut through plate thickness
            Extrusion boltVoid = familyDoc.FamilyCreate.NewExtrusion(
                false, boltProfile, sp, -PT); // isSolid=false
        }}
    }}

    tx.Commit();
}}""",
            ))

        return samples

    # ------------------------------------------------------------------
    # 9. Structural connections  (~25 samples)
    # ------------------------------------------------------------------

    def _structural_connections(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        # Shear tab (single plate) beam-to-column connection
        tab_cases = [
            (150, 100, 8,  2, "Shear tab 150x100x8mm, 2 bolts"),
            (200, 150, 10, 3, "Shear tab 200x150x10mm, 3 bolts"),
            (250, 150, 12, 3, "Shear tab 250x150x12mm, 3 bolts"),
            (300, 150, 12, 4, "Shear tab 300x150x12mm, 4 bolts"),
            (350, 150, 16, 4, "Shear tab 350x150x16mm, 4 bolts"),
            (400, 150, 16, 5, "Shear tab 400x150x16mm, 5 bolts"),
            (450, 175, 20, 6, "Shear tab 450x175x20mm, 6 bolts"),
            (500, 175, 20, 6, "Shear tab 500x175x20mm, 6 bolts"),
            (550, 200, 25, 7, "Shear tab 550x200x25mm, 7 bolts"),
        ]

        for H, W, t, n_bolts, desc in tab_cases:
            H_ft = H * MM_TO_FT
            W_ft = W * MM_TO_FT
            t_ft = t * MM_TO_FT
            bolt_sp = (H - 2 * 40) / max(n_bolts - 1, 1)  # 40mm edge dist
            bolt_sp_ft = bolt_sp * MM_TO_FT
            samples.append(_s(
                f"Create a steel shear tab (single-plate) beam-to-column connection family: {desc}. "
                "Include Height, Width, Thickness, and bolt hole parameters.",
                f"""\
using Autodesk.Revit.DB;
using System;

// Shear tab connection plate: {H}x{W}x{t}mm, {n_bolts} bolt holes
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pH = famMgr.AddParameter(
    "Height",    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pW = famMgr.AddParameter(
    "Width",     BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pT = famMgr.AddParameter(
    "Thickness", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pNB = famMgr.AddParameter(
    "BoltCount", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Integer, false);

famMgr.Set(pH, {H_ft:.6f}); // {H} mm
famMgr.Set(pW, {W_ft:.6f}); // {W} mm
famMgr.Set(pT, {t_ft:.6f}); // {t} mm
famMgr.Set(pNB, {n_bolts});

using (Transaction tx = new Transaction(familyDoc, "Create Shear Tab"))
{{
    tx.Start();

    double H  = {H_ft:.6f}; // {H} mm
    double W  = {W_ft:.6f}; // {W} mm
    double t  = {t_ft:.6f}; // {t} mm
    double e  = {40 * MM_TO_FT:.6f}; // 40 mm edge distance
    double bs = {bolt_sp_ft:.6f};    // bolt spacing {bolt_sp:.1f} mm
    double bR = {11 * MM_TO_FT:.6f}; // bolt hole radius (22mm bolt, 2mm clearance)
    int nb    = {n_bolts};
    int seg   = 16; // polygon segments per hole

    // Main plate profile
    CurveArray plateLoop = new CurveArray();
    plateLoop.Append(Line.CreateBound(new XYZ(0, 0, 0), new XYZ(0, W, 0)));
    plateLoop.Append(Line.CreateBound(new XYZ(0, W, 0), new XYZ(0, W, H)));
    plateLoop.Append(Line.CreateBound(new XYZ(0, W, H), new XYZ(0, 0, H)));
    plateLoop.Append(Line.CreateBound(new XYZ(0, 0, H), new XYZ(0, 0, 0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(plateLoop);

    // Bolt holes (void circles along vertical centreline)
    for (int i = 0; i < nb; i++)
    {{
        double cy = W / 2;
        double cz = e + i * bs;

        CurveArray holeLoop = new CurveArray();
        for (int j = 0; j < seg; j++)
        {{
            double a0 = 2 * Math.PI * j / seg;
            double a1 = 2 * Math.PI * (j + 1) / seg;
            XYZ p0 = new XYZ(0, cy + bR * Math.Cos(a0), cz + bR * Math.Sin(a0));
            XYZ p1 = new XYZ(0, cy + bR * Math.Cos(a1), cz + bR * Math.Sin(a1));
            holeLoop.Append(Line.CreateBound(p0, p1));
        }}
        profile.Append(holeLoop); // each hole is a void loop in the profile
    }}

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero));

    Extrusion tab = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, t);

    tx.Commit();
}}""",
            ))

        # Clip angle connection
        clip_cases = [
            (75,  75,  6,  "L75x75x6 clip angle"),
            (100, 100, 8,  "L100x100x8 clip angle pair"),
            (100, 75,  8,  "L100x75x8 clip angle"),
            (125, 75,  10, "L125x75x10 clip angle"),
            (150, 90,  12, "L150x90x12 clip angle"),
            (150, 100, 12, "L150x100x12 clip angle"),
            (200, 100, 16, "L200x100x16 heavy clip angle"),
        ]

        for leg1, leg2, t, desc in clip_cases:
            l1_ft = leg1 * MM_TO_FT
            l2_ft = leg2 * MM_TO_FT
            t_ft  = t    * MM_TO_FT
            samples.append(_s(
                f"Create a steel clip angle connection family: {desc}. "
                "The horizontal leg bolts to the beam web; the vertical leg bolts to the column flange.",
                f"""\
using Autodesk.Revit.DB;

// Clip angle: {desc}
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pL1 = famMgr.AddParameter(
    "OutstandingLeg", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pL2 = famMgr.AddParameter(
    "ConnectedLeg",   BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pT  = famMgr.AddParameter(
    "Thickness",      BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pH  = famMgr.AddParameter(
    "AngleLength",    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pL1, {l1_ft:.6f}); // {leg1} mm
famMgr.Set(pL2, {l2_ft:.6f}); // {leg2} mm
famMgr.Set(pT,  {t_ft:.6f});  // {t} mm
famMgr.Set(pH,  {200 * MM_TO_FT:.6f}); // 200 mm default length

using (Transaction tx = new Transaction(familyDoc, "Create Clip Angle"))
{{
    tx.Start();

    double l1 = {l1_ft:.6f}; // outstanding leg {leg1} mm
    double l2 = {l2_ft:.6f}; // connected leg {leg2} mm
    double t  = {t_ft:.6f};  // thickness {t} mm
    double L  = {200 * MM_TO_FT:.6f}; // 200 mm

    // L-shape profile in YZ plane
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(0, 0,  0),    new XYZ(0, l1,  0)));
    loop.Append(Line.CreateBound(new XYZ(0, l1, 0),    new XYZ(0, l1,  t)));
    loop.Append(Line.CreateBound(new XYZ(0, l1, t),    new XYZ(0, t,   t)));
    loop.Append(Line.CreateBound(new XYZ(0, t,  t),    new XYZ(0, t,   l2)));
    loop.Append(Line.CreateBound(new XYZ(0, t,  l2),   new XYZ(0, 0,   l2)));
    loop.Append(Line.CreateBound(new XYZ(0, 0,  l2),   new XYZ(0, 0,   0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero));

    Extrusion angle = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, L);

    tx.Commit();
}}""",
            ))

        # End plate connection
        endplate_cases = [
            (200, 180, 12, "flush end plate 200x180x12mm"),
            (250, 200, 16, "flush end plate 250x200x16mm"),
            (300, 200, 20, "extended end plate 300x200x20mm"),
            (350, 250, 20, "extended end plate 350x250x20mm"),
            (400, 250, 25, "extended end plate 400x250x25mm"),
            (450, 280, 25, "extended end plate 450x280x25mm"),
            (500, 300, 32, "deep end plate 500x300x32mm"),
        ]

        for H, W, t, desc in endplate_cases:
            H_ft = H * MM_TO_FT
            W_ft = W * MM_TO_FT
            t_ft = t * MM_TO_FT
            samples.append(_s(
                f"Create a steel end plate moment connection family: {desc}. "
                "Include Height, Width, Thickness parameters and weld prep symbol note.",
                f"""\
using Autodesk.Revit.DB;

// End plate connection: {desc}
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pH = famMgr.AddParameter(
    "Height",    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pW = famMgr.AddParameter(
    "Width",     BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pT = famMgr.AddParameter(
    "Thickness", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pH, {H_ft:.6f}); // {H} mm
famMgr.Set(pW, {W_ft:.6f}); // {W} mm
famMgr.Set(pT, {t_ft:.6f}); // {t} mm

using (Transaction tx = new Transaction(familyDoc, "Create End Plate"))
{{
    tx.Start();

    double H = {H_ft:.6f}; // {H} mm
    double W = {W_ft:.6f}; // {W} mm
    double t = {t_ft:.6f}; // {t} mm

    // Flat plate profile (XY plane); plate face is in YZ plane
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(0, -W/2, -H/2), new XYZ(0,  W/2, -H/2)));
    loop.Append(Line.CreateBound(new XYZ(0,  W/2, -H/2), new XYZ(0,  W/2,  H/2)));
    loop.Append(Line.CreateBound(new XYZ(0,  W/2,  H/2), new XYZ(0, -W/2,  H/2)));
    loop.Append(Line.CreateBound(new XYZ(0, -W/2,  H/2), new XYZ(0, -W/2, -H/2)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero));

    // Plate thickness extruded in X direction (toward column)
    Extrusion endPlate = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, t);

    tx.Commit();
}}""",
            ))

        return samples

    # ------------------------------------------------------------------
    # 10. Reinforcement void patterns  (~25 samples)
    # ------------------------------------------------------------------

    def _reinforcement_voids(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        # Clear cover void cut in rectangular section
        cover_cases = [
            (250, 350, 35, "250x350mm beam, 35mm clear cover"),
            (250, 400, 40, "250x400mm beam, 40mm clear cover"),
            (300, 400, 40, "300x400mm beam, 40mm clear cover"),
            (300, 500, 40, "300x500mm beam, 40mm clear cover"),
            (350, 500, 40, "350x500mm beam, 40mm clear cover"),
            (350, 600, 45, "350x600mm beam, 45mm clear cover"),
            (400, 600, 50, "400x600mm beam, 50mm clear cover"),
            (400, 700, 50, "400x700mm beam, 50mm clear cover"),
            (500, 700, 50, "500x700mm beam, 50mm clear cover"),
            (500, 800, 50, "500x800mm beam, 50mm clear cover"),
            (300, 300, 35, "300x300mm column, 35mm clear cover"),
            (350, 350, 40, "350x350mm column, 40mm clear cover"),
            (400, 400, 40, "400x400mm column, 40mm clear cover"),
            (450, 450, 45, "450x450mm column, 45mm clear cover"),
            (500, 500, 50, "500x500mm column, 50mm clear cover"),
            (600, 600, 50, "600x600mm column, 50mm clear cover"),
        ]

        for b, h, cover, desc in cover_cases:
            b_ft = b * MM_TO_FT
            h_ft = h * MM_TO_FT
            c_ft = cover * MM_TO_FT
            bi = b - 2 * cover
            hi = h - 2 * cover
            bi_ft = bi * MM_TO_FT
            hi_ft = hi * MM_TO_FT
            samples.append(_s(
                f"Create a void extrusion representing the rebar cage clear cover zone: {desc}. "
                "The void defines the concrete cover region outside the rebar boundary.",
                f"""\
using Autodesk.Revit.DB;

// Rebar clear cover void: outer {b}x{h}mm, cover={cover}mm, inner {bi}x{hi}mm
// This void is subtracted from the column/beam solid to show rebar zone boundary
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pB  = famMgr.AddParameter(
    "b",          BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pH  = famMgr.AddParameter(
    "h",          BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pCV = famMgr.AddParameter(
    "ClearCover", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pL  = famMgr.AddParameter(
    "Length",     BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pB,  {b_ft:.6f}); // {b} mm
famMgr.Set(pH,  {h_ft:.6f}); // {h} mm
famMgr.Set(pCV, {c_ft:.6f}); // {cover} mm
famMgr.Set(pL,  {4000 * MM_TO_FT:.6f}); // 4000 mm

using (Transaction tx = new Transaction(familyDoc, "Create Cover Void"))
{{
    tx.Start();

    double b  = {b_ft:.6f};  // {b} mm
    double h  = {h_ft:.6f};  // {h} mm
    double cv = {c_ft:.6f};  // {cover} mm clear cover
    double L  = {4000 * MM_TO_FT:.6f};
    double bi = {bi_ft:.6f}; // inner width  {bi} mm
    double hi = {hi_ft:.6f}; // inner height {hi} mm

    // Outer section boundary
    CurveArray outerLoop = new CurveArray();
    outerLoop.Append(Line.CreateBound(new XYZ(0, -b/2, -h/2), new XYZ(0,  b/2, -h/2)));
    outerLoop.Append(Line.CreateBound(new XYZ(0,  b/2, -h/2), new XYZ(0,  b/2,  h/2)));
    outerLoop.Append(Line.CreateBound(new XYZ(0,  b/2,  h/2), new XYZ(0, -b/2,  h/2)));
    outerLoop.Append(Line.CreateBound(new XYZ(0, -b/2,  h/2), new XYZ(0, -b/2, -h/2)));

    // Rebar cage boundary (inner profile at clear cover offset)
    CurveArray innerLoop = new CurveArray();
    innerLoop.Append(Line.CreateBound(new XYZ(0, -bi/2, -hi/2), new XYZ(0, -bi/2,  hi/2)));
    innerLoop.Append(Line.CreateBound(new XYZ(0, -bi/2,  hi/2), new XYZ(0,  bi/2,  hi/2)));
    innerLoop.Append(Line.CreateBound(new XYZ(0,  bi/2,  hi/2), new XYZ(0,  bi/2, -hi/2)));
    innerLoop.Append(Line.CreateBound(new XYZ(0,  bi/2, -hi/2), new XYZ(0, -bi/2, -hi/2)));

    // Ring profile = outer - inner (cover zone)
    CurveArrArray profile = new CurveArrArray();
    profile.Append(outerLoop);
    profile.Append(innerLoop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero));

    // isSolid = false: this is a void that cuts into the main solid
    Extrusion coverVoid = familyDoc.FamilyCreate.NewExtrusion(false, profile, sp, L);

    tx.Commit();
}}""",
            ))

        # Circular column rebar pattern (void cylinders for each bar)
        rebar_cases = [
            (300,  6, 16, 35, "6-T16 bars in 300mm dia column"),
            (350,  8, 16, 35, "8-T16 bars in 350mm dia column"),
            (400,  8, 20, 40, "8-T20 bars in 400mm dia column"),
            (450,  8, 20, 40, "8-T20 bars in 450mm dia column"),
            (500, 10, 25, 40, "10-T25 bars in 500mm dia column"),
            (550, 10, 25, 45, "10-T25 bars in 550mm dia column"),
            (600, 12, 25, 50, "12-T25 bars in 600mm dia column"),
            (650, 12, 32, 50, "12-T32 bars in 650mm dia column"),
            (700, 14, 32, 50, "14-T32 bars in 700mm dia column"),
            (750, 14, 32, 55, "14-T32 bars in 750mm dia column"),
            (800, 16, 32, 60, "16-T32 bars in 800mm dia column"),
        ]

        for col_dia, n_bars, bar_dia, cover, desc in rebar_cases:
            col_r    = col_dia / 2
            bar_r    = bar_dia / 2
            cage_r   = col_r - cover - bar_r  # centre of rebar from column centreline
            col_r_ft = col_r    * MM_TO_FT
            bar_r_ft = bar_r    * MM_TO_FT
            cage_r_ft = cage_r  * MM_TO_FT
            h_ft     = 3000 * MM_TO_FT
            samples.append(_s(
                f"Create void cylinders representing rebar positions in a circular column: {desc}. "
                "The voids model rebar as 32-segment polygon cuts through the column solid.",
                f"""\
using Autodesk.Revit.DB;
using System;

// Rebar void pattern in circular column: {desc}
// Column dia={col_dia}mm, {n_bars} bars of T{bar_dia}, cover={cover}mm
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pND = famMgr.AddParameter(
    "NumBars",    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Integer, false);
FamilyParameter pBD = famMgr.AddParameter(
    "BarDiameter", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pCV = famMgr.AddParameter(
    "ClearCover",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pND, {n_bars});
famMgr.Set(pBD, {bar_dia * MM_TO_FT:.6f}); // {bar_dia} mm
famMgr.Set(pCV, {cover   * MM_TO_FT:.6f}); // {cover} mm

using (Transaction tx = new Transaction(familyDoc, "Create Rebar Voids"))
{{
    tx.Start();

    int    nb    = {n_bars};
    double barR  = {bar_r_ft:.6f};  // bar radius {bar_r} mm
    double cageR = {cage_r_ft:.6f}; // cage centroid radius {cage_r:.1f} mm
    double L     = {h_ft:.6f};      // column height 3000 mm
    int    seg   = 32; // polygon segments per bar void

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero));

    for (int i = 0; i < nb; i++)
    {{
        double theta = 2 * Math.PI * i / nb; // angular position of each bar
        double cy    = cageR * Math.Cos(theta); // Y centre
        double cz    = cageR * Math.Sin(theta); // Z centre

        CurveArray barLoop = new CurveArray();
        for (int j = 0; j < seg; j++)
        {{
            double a0 = 2 * Math.PI * j / seg;
            double a1 = 2 * Math.PI * (j + 1) / seg;
            XYZ p0 = new XYZ(0, cy + barR * Math.Cos(a0), cz + barR * Math.Sin(a0));
            XYZ p1 = new XYZ(0, cy + barR * Math.Cos(a1), cz + barR * Math.Sin(a1));
            barLoop.Append(Line.CreateBound(p0, p1));
        }}

        CurveArrArray barProfile = new CurveArrArray();
        barProfile.Append(barLoop);

        // void (isSolid=false) cuts bar hole through column length
        Extrusion barVoid = familyDoc.FamilyCreate.NewExtrusion(
            false, barProfile, sp, L);
    }}

    tx.Commit();
}}""",
            ))

        # Stirrup void pattern (rectangular loop voids for shear links)
        stirrup_cases = [
            (200, 350, 35, 10, 125, "stirrups in 200x350mm beam, T10@125"),
            (250, 400, 40, 10, 150, "stirrups in 250x400mm beam, T10@150"),
            (250, 500, 40, 10, 150, "stirrups in 250x500mm beam, T10@150"),
            (300, 500, 40, 10, 150, "stirrups in 300x500mm beam, T10@150"),
            (300, 600, 50, 12, 200, "stirrups in 300x600mm beam, T12@200"),
            (350, 600, 50, 12, 150, "stirrups in 350x600mm beam, T12@150"),
            (400, 700, 50, 12, 200, "stirrups in 400x700mm beam, T12@200"),
        ]

        for b, h, cover, bar_d, spacing, desc in stirrup_cases:
            b_ft  = b  * MM_TO_FT
            h_ft  = h  * MM_TO_FT
            c_ft  = cover  * MM_TO_FT
            bd_ft = bar_d  * MM_TO_FT
            sp_ft = spacing * MM_TO_FT
            bi = b - 2 * cover
            hi = h - 2 * cover
            bi_ft = bi * MM_TO_FT
            hi_ft = hi * MM_TO_FT
            L = 4000
            n_stirrups = int(L / spacing) + 1
            samples.append(_s(
                f"Create void rectangles representing stirrup (shear link) positions: {desc}. "
                "Each void is a thin rectangular frame representing one stirrup bar.",
                f"""\
using Autodesk.Revit.DB;

// Stirrup voids: {desc}
// Beam {b}x{h}mm, cover={cover}mm, bar T{bar_d}, spacing={spacing}mm
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pSp = famMgr.AddParameter(
    "StirrupSpacing", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pBD = famMgr.AddParameter(
    "BarDiameter",    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pSp, {sp_ft:.6f}); // {spacing} mm
famMgr.Set(pBD, {bd_ft:.6f}); // {bar_d} mm

using (Transaction tx = new Transaction(familyDoc, "Create Stirrup Voids"))
{{
    tx.Start();

    double b   = {b_ft:.6f};  // beam width {b} mm
    double h   = {h_ft:.6f};  // beam depth {h} mm
    double cv  = {c_ft:.6f};  // cover {cover} mm
    double barR = {bar_d / 2 * MM_TO_FT:.6f}; // bar radius {bar_d / 2} mm
    double sp  = {sp_ft:.6f}; // stirrup spacing {spacing} mm
    double bi  = {bi_ft:.6f}; // inner width {bi} mm
    double hi  = {hi_ft:.6f}; // inner height {hi} mm
    int    ns  = {n_stirrups}; // number of stirrups over 4000mm length
    double t   = 2 * barR;    // stirrup bar diameter = void thickness

    for (int i = 0; i < ns; i++)
    {{
        double x = i * sp; // position along beam

        // Stirrup: outer frame rectangle minus inner rectangle at location x
        SketchPlane sp_plane = SketchPlane.Create(familyDoc,
            Plane.CreateByNormalAndOrigin(
                XYZ.BasisX, new XYZ(x, 0, 0)));

        // Outer stirrup boundary
        CurveArray outer = new CurveArray();
        outer.Append(Line.CreateBound(
            new XYZ(x, -bi/2 - t, -hi/2 - t),
            new XYZ(x,  bi/2 + t, -hi/2 - t)));
        outer.Append(Line.CreateBound(
            new XYZ(x,  bi/2 + t, -hi/2 - t),
            new XYZ(x,  bi/2 + t,  hi/2 + t)));
        outer.Append(Line.CreateBound(
            new XYZ(x,  bi/2 + t,  hi/2 + t),
            new XYZ(x, -bi/2 - t,  hi/2 + t)));
        outer.Append(Line.CreateBound(
            new XYZ(x, -bi/2 - t,  hi/2 + t),
            new XYZ(x, -bi/2 - t, -hi/2 - t)));

        // Inner void (removes material from link bar ring)
        CurveArray inner = new CurveArray();
        inner.Append(Line.CreateBound(
            new XYZ(x, -bi/2, -hi/2),
            new XYZ(x, -bi/2,  hi/2)));
        inner.Append(Line.CreateBound(
            new XYZ(x, -bi/2,  hi/2),
            new XYZ(x,  bi/2,  hi/2)));
        inner.Append(Line.CreateBound(
            new XYZ(x,  bi/2,  hi/2),
            new XYZ(x,  bi/2, -hi/2)));
        inner.Append(Line.CreateBound(
            new XYZ(x,  bi/2, -hi/2),
            new XYZ(x, -bi/2, -hi/2)));

        CurveArrArray profile = new CurveArrArray();
        profile.Append(outer);
        profile.Append(inner);

        // Thin void slice at stirrup thickness
        Extrusion stirrupVoid = familyDoc.FamilyCreate.NewExtrusion(
            false, profile, sp_plane, t);
    }}

    tx.Commit();
}}""",
            ))

        return samples
