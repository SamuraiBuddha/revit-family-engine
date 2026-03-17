"""Training data generator: Revit structural family patterns.

Produces ~250 Alpaca-format training pairs covering W-sections, HSS tubing,
concrete columns, beams, and foundation families.
"""

from __future__ import annotations

from typing import Any, Dict, List

SAMPLE = Dict[str, Any]
MM_TO_FT = 1.0 / 304.8


def _s(instruction: str, output: str) -> SAMPLE:
    return {"instruction": instruction, "input": "", "output": output}


def _ft(mm: float) -> str:
    return f"{mm * MM_TO_FT:.6f}"


class StructuralFamilyGenerator:
    """Generates training samples for Revit structural family creation."""

    def generate(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []
        samples += self._w_sections()
        samples += self._hss_sections()
        samples += self._concrete_columns()
        samples += self._structural_beams()
        samples += self._foundations()
        samples += self._structural_parameters()
        samples += self._rebar_patterns()
        samples += self._steel_connections()
        return samples

    # ------------------------------------------------------------------
    # W-sections (wide-flange steel)
    # ------------------------------------------------------------------

    def _w_sections(self) -> List[SAMPLE]:
        samples = []
        # (designation, d_mm, bf_mm, tf_mm, tw_mm)
        sections = [
            ("W200x31",  210, 134, 10, 7),
            ("W250x45",  266, 148, 13, 8),
            ("W310x52",  318, 167, 13, 8),
            ("W360x64",  347, 203, 13, 8),
            ("W410x85",  417, 181, 18, 11),
            ("W460x97",  466, 193, 19, 11),
            ("W530x101", 549, 183, 16, 10),
            ("W610x82",  599, 178, 12, 10),
            ("W760x173", 762, 267, 22, 14),
        ]
        for (desig, d, bf, tf, tw) in sections:
            for (h_mm, use) in [(3000, "column"), (6000, "beam"), (4500, "member")]:
                samples.append(_s(
                    f"Create a {desig} structural steel {use} family, {h_mm}mm long",
                    f"""\
using Autodesk.Revit.DB;

// {desig}: d={d}mm bf={bf}mm tf={tf}mm tw={tw}mm
// FamilyManager params -- OUTSIDE Transaction
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pd  = famMgr.AddParameter("d",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pbf = famMgr.AddParameter("bf", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter ptf = famMgr.AddParameter("tf", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter ptw = famMgr.AddParameter("tw", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter ph  = famMgr.AddParameter("Length", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pd,  {_ft(d)});  // {d} mm
famMgr.Set(pbf, {_ft(bf)}); // {bf} mm
famMgr.Set(ptf, {_ft(tf)}); // {tf} mm
famMgr.Set(ptw, {_ft(tw)}); // {tw} mm
famMgr.Set(ph,  {_ft(h_mm)});  // {h_mm} mm

using (Transaction tx = new Transaction(familyDoc, "Create {desig} Profile"))
{{
    tx.Start();
    double d = {_ft(d)}; double bf = {_ft(bf)};
    double tf = {_ft(tf)}; double tw = {_ft(tw)};
    double h  = {_ft(h_mm)};

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bf/2, -d/2, 0),    new XYZ( bf/2, -d/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bf/2, -d/2, 0),    new XYZ( bf/2, -d/2+tf, 0)));
    loop.Append(Line.CreateBound(new XYZ( bf/2, -d/2+tf, 0), new XYZ( tw/2, -d/2+tf, 0)));
    loop.Append(Line.CreateBound(new XYZ( tw/2, -d/2+tf, 0), new XYZ( tw/2,  d/2-tf, 0)));
    loop.Append(Line.CreateBound(new XYZ( tw/2,  d/2-tf, 0), new XYZ( bf/2,  d/2-tf, 0)));
    loop.Append(Line.CreateBound(new XYZ( bf/2,  d/2-tf, 0), new XYZ( bf/2,  d/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bf/2,  d/2, 0),    new XYZ(-bf/2,  d/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-bf/2,  d/2, 0),    new XYZ(-bf/2,  d/2-tf, 0)));
    loop.Append(Line.CreateBound(new XYZ(-bf/2,  d/2-tf, 0), new XYZ(-tw/2,  d/2-tf, 0)));
    loop.Append(Line.CreateBound(new XYZ(-tw/2,  d/2-tf, 0), new XYZ(-tw/2, -d/2+tf, 0)));
    loop.Append(Line.CreateBound(new XYZ(-tw/2, -d/2+tf, 0), new XYZ(-bf/2, -d/2+tf, 0)));
    loop.Append(Line.CreateBound(new XYZ(-bf/2, -d/2+tf, 0), new XYZ(-bf/2, -d/2, 0)));
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc, Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);
    tx.Commit();
}}"""))
        return samples  # 9 * 3 = 27 samples

    # ------------------------------------------------------------------
    # HSS hollow structural sections
    # ------------------------------------------------------------------

    def _hss_sections(self) -> List[SAMPLE]:
        samples = []
        # (designation, B_mm, H_mm, t_mm)
        sections = [
            ("HSS100x100x6",  100, 100, 6),
            ("HSS150x100x6",  150, 100, 6),
            ("HSS150x150x8",  150, 150, 8),
            ("HSS200x150x8",  200, 150, 8),
            ("HSS200x200x10", 200, 200, 10),
            ("HSS250x150x8",  250, 150, 8),
            ("HSS300x200x10", 300, 200, 10),
            ("HSS400x200x12", 400, 200, 12),
        ]
        for (desig, B, H, t) in sections:
            for (length_mm, usage) in [(3000, "column"), (5000, "brace"), (6000, "beam")]:
                samples.append(_s(
                    f"Create a {desig} HSS {usage} family, {length_mm}mm long",
                    f"""\
using Autodesk.Revit.DB;

// {desig}: outer {B}x{H}mm, wall thickness {t}mm
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pB = famMgr.AddParameter("B", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pH = famMgr.AddParameter("H", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pt = famMgr.AddParameter("t", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pB, {_ft(B)}); // {B} mm
famMgr.Set(pH, {_ft(H)}); // {H} mm
famMgr.Set(pt, {_ft(t)}); // {t} mm wall thickness

using (Transaction tx = new Transaction(familyDoc, "Create {desig}"))
{{
    tx.Start();
    double B = {_ft(B)}; double H = {_ft(H)}; double t = {_ft(t)};
    double len = {_ft(length_mm)};

    // Outer rectangle
    CurveArray outer = new CurveArray();
    outer.Append(Line.CreateBound(new XYZ(-B/2, -H/2, 0), new XYZ( B/2, -H/2, 0)));
    outer.Append(Line.CreateBound(new XYZ( B/2, -H/2, 0), new XYZ( B/2,  H/2, 0)));
    outer.Append(Line.CreateBound(new XYZ( B/2,  H/2, 0), new XYZ(-B/2,  H/2, 0)));
    outer.Append(Line.CreateBound(new XYZ(-B/2,  H/2, 0), new XYZ(-B/2, -H/2, 0)));

    // Inner rectangle (hollow)
    CurveArray inner = new CurveArray();
    double bi = B/2 - t; double hi = H/2 - t;
    inner.Append(Line.CreateBound(new XYZ(-bi, -hi, 0), new XYZ( bi, -hi, 0)));
    inner.Append(Line.CreateBound(new XYZ( bi, -hi, 0), new XYZ( bi,  hi, 0)));
    inner.Append(Line.CreateBound(new XYZ( bi,  hi, 0), new XYZ(-bi,  hi, 0)));
    inner.Append(Line.CreateBound(new XYZ(-bi,  hi, 0), new XYZ(-bi, -hi, 0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(outer);
    profile.Append(inner); // inner loop creates hollow

    SketchPlane sp = SketchPlane.Create(familyDoc, Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, len);
    tx.Commit();
}}"""))
        return samples  # 8 * 3 = 24 samples

    # ------------------------------------------------------------------
    # Concrete columns
    # ------------------------------------------------------------------

    def _concrete_columns(self) -> List[SAMPLE]:
        samples = []
        sizes = [
            (300, 300, 3000), (400, 400, 3600), (500, 500, 4000),
            (600, 600, 4500), (300, 600, 3600), (400, 800, 4000),
            (250, 250, 3000), (350, 350, 3600), (450, 600, 4000),
            (500, 800, 5000),
        ]
        for (w, d, h) in sizes:
            samples.append(_s(
                f"Create a rectangular concrete column family {w}x{d}mm cross-section, {h}mm height",
                f"""\
using Autodesk.Revit.DB;

// Rectangular concrete column: {w}x{d}mm, {h}mm height
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW = famMgr.AddParameter("Width",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pD = famMgr.AddParameter("Depth",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pH = famMgr.AddParameter("Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pW, {_ft(w)}); // {w} mm
famMgr.Set(pD, {_ft(d)}); // {d} mm
famMgr.Set(pH, {_ft(h)}); // {h} mm

using (Transaction tx = new Transaction(familyDoc, "Create Concrete Column"))
{{
    tx.Start();
    double w = {_ft(w)}; double d = {_ft(d)}; double h = {_ft(h)};

    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-w/2, -d/2, 0), new XYZ( w/2, -d/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, -d/2, 0), new XYZ( w/2,  d/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2,  d/2, 0), new XYZ(-w/2,  d/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-w/2,  d/2, 0), new XYZ(-w/2, -d/2, 0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc, Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);
    tx.Commit();
}}"""))

        # Circular concrete column
        for (r, h, desc) in [(150, 3000, "300mm dia"), (200, 4000, "400mm dia"), (250, 4500, "500mm dia")]:
            import math
            samples.append(_s(
                f"Create a circular concrete column family {desc} cross-section, {h}mm height",
                f"""\
using Autodesk.Revit.DB;
using System;

// Circular concrete column: {r*2}mm diameter, {h}mm height
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pR = famMgr.AddParameter("Radius", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pH = famMgr.AddParameter("Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pR, {_ft(r)}); // {r} mm radius
famMgr.Set(pH, {_ft(h)}); // {h} mm

using (Transaction tx = new Transaction(familyDoc, "Create Circular Column"))
{{
    tx.Start();
    double radius = {_ft(r)}; double h = {_ft(h)};
    int n = 32;
    CurveArray loop = new CurveArray();
    for (int i = 0; i < n; i++)
    {{
        double a0 = 2 * Math.PI * i / n;
        double a1 = 2 * Math.PI * (i + 1) / n;
        loop.Append(Line.CreateBound(
            new XYZ(radius * Math.Cos(a0), radius * Math.Sin(a0), 0),
            new XYZ(radius * Math.Cos(a1), radius * Math.Sin(a1), 0)));
    }}
    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc, Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);
    tx.Commit();
}}"""))
        return samples  # 10 + 3 = 13 samples

    # ------------------------------------------------------------------
    # Structural beams
    # ------------------------------------------------------------------

    def _structural_beams(self) -> List[SAMPLE]:
        samples = []
        beam_cases = [
            (300, 600, 4000, "concrete rectangular beam"),
            (350, 700, 5000, "concrete rectangular beam"),
            (400, 800, 6000, "concrete rectangular beam"),
            (250, 500, 3000, "light concrete beam"),
            (500, 900, 7200, "heavy concrete beam"),
            (300, 500, 4500, "concrete floor beam"),
            (200, 400, 3600, "secondary concrete beam"),
        ]
        for (w, d, span, desc) in beam_cases:
            samples.append(_s(
                f"Create a {desc} family {w}x{d}mm cross-section, {span}mm span",
                f"""\
using Autodesk.Revit.DB;

// {desc}: {w}x{d}mm, {span}mm span
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW    = famMgr.AddParameter("Width",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pD    = famMgr.AddParameter("Depth",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pSpan = famMgr.AddParameter("Span",   BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pW,    {_ft(w)});    // {w} mm
famMgr.Set(pD,    {_ft(d)});    // {d} mm
famMgr.Set(pSpan, {_ft(span)}); // {span} mm

using (Transaction tx = new Transaction(familyDoc, "Create Beam Profile"))
{{
    tx.Start();
    double bw = {_ft(w)}; double bd = {_ft(d)}; double span = {_ft(span)};

    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2, 0, 0),  new XYZ( bw/2, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, 0, 0),  new XYZ( bw/2, 0, bd)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, 0, bd), new XYZ(-bw/2, 0, bd)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2, 0, bd), new XYZ(-bw/2, 0, 0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc, Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, span);
    tx.Commit();
}}"""))

        # T-beam
        t_beams = [
            (600, 200, 100, 400, 5000, "T-beam 600mm flange"),
            (800, 250, 120, 500, 7200, "T-beam 800mm flange"),
            (500, 200, 100, 350, 4500, "T-beam 500mm flange"),
        ]
        for (bf, bw, tf, dw, span, desc) in t_beams:
            samples.append(_s(
                f"Create a concrete {desc} cross-section, {span}mm span",
                f"""\
using Autodesk.Revit.DB;

// {desc}: bf={bf}mm bw={bw}mm tf={tf}mm dw={dw}mm span={span}mm
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pbf = famMgr.AddParameter("FlangeWidth",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pbw = famMgr.AddParameter("WebWidth",     BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter ptf = famMgr.AddParameter("FlangeThick",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pdw = famMgr.AddParameter("WebDepth",     BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pbf, {_ft(bf)}); famMgr.Set(pbw, {_ft(bw)});
famMgr.Set(ptf, {_ft(tf)}); famMgr.Set(pdw, {_ft(dw)});

using (Transaction tx = new Transaction(familyDoc, "Create T-Beam"))
{{
    tx.Start();
    double bf = {_ft(bf)}; double bw = {_ft(bw)};
    double tf = {_ft(tf)}; double dw = {_ft(dw)};
    double span = {_ft(span)};

    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bf/2, 0, 0),     new XYZ( bf/2, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ( bf/2, 0, 0),     new XYZ( bf/2, 0, tf)));
    loop.Append(Line.CreateBound(new XYZ( bf/2, 0, tf),    new XYZ( bw/2, 0, tf)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, 0, tf),    new XYZ( bw/2, 0, tf+dw)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, 0, tf+dw), new XYZ(-bw/2, 0, tf+dw)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2, 0, tf+dw), new XYZ(-bw/2, 0, tf)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2, 0, tf),    new XYZ(-bf/2, 0, tf)));
    loop.Append(Line.CreateBound(new XYZ(-bf/2, 0, tf),    new XYZ(-bf/2, 0, 0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc, Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, span);
    tx.Commit();
}}"""))
        return samples  # 7 + 3 = 10 samples

    # ------------------------------------------------------------------
    # Foundations
    # ------------------------------------------------------------------

    def _foundations(self) -> List[SAMPLE]:
        samples = []
        footing_cases = [
            (800,  800,  300,  "small spread footing"),
            (1000, 1000, 400,  "medium spread footing"),
            (1200, 1200, 500,  "standard spread footing"),
            (1500, 1500, 600,  "large spread footing"),
            (2000, 2000, 700,  "heavy load footing"),
            (1200, 2400, 500,  "rectangular pad footing"),
            (900,  1800, 400,  "strip footing section"),
            (2500, 2500, 800,  "column footing for 400mm column"),
            (600,  600,  250,  "light column footing"),
            (1800, 3600, 600,  "wall footing pad"),
        ]
        for (L, W, H, desc) in footing_cases:
            samples.append(_s(
                f"Create a {desc} family {L}x{W}mm plan, {H}mm thick",
                f"""\
using Autodesk.Revit.DB;

// {desc}: {L}x{W}mm plan, {H}mm thick
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pL = famMgr.AddParameter("Length",    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pW = famMgr.AddParameter("Width",     BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pH = famMgr.AddParameter("Thickness", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pL, {_ft(L)}); // {L} mm
famMgr.Set(pW, {_ft(W)}); // {W} mm
famMgr.Set(pH, {_ft(H)}); // {H} mm

using (Transaction tx = new Transaction(familyDoc, "Create Footing"))
{{
    tx.Start();
    double l = {_ft(L)}; double w = {_ft(W)}; double h = {_ft(H)};

    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-l/2, -w/2, 0), new XYZ( l/2, -w/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( l/2, -w/2, 0), new XYZ( l/2,  w/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( l/2,  w/2, 0), new XYZ(-l/2,  w/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-l/2,  w/2, 0), new XYZ(-l/2, -w/2, 0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc, Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    // Footing extends downward from reference level
    Extrusion ext = familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);
    ext.StartOffset = -h; // start below reference
    ext.EndOffset   = 0;

    tx.Commit();
}}"""))

        # Step footing
        samples.append(_s("Create a stepped footing family with two levels: base 1500x1500x400mm, cap 900x900x300mm",
            f"""\
using Autodesk.Revit.DB;

// Stepped footing: base 1500x1500x400mm, cap 900x900x300mm
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pBL = famMgr.AddParameter("BaseLength",    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pBH = famMgr.AddParameter("BaseThickness", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pCL = famMgr.AddParameter("CapLength",     BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pCH = famMgr.AddParameter("CapThickness",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pBL, {_ft(1500)}); famMgr.Set(pBH, {_ft(400)});
famMgr.Set(pCL, {_ft(900)});  famMgr.Set(pCH, {_ft(300)});

using (Transaction tx = new Transaction(familyDoc, "Create Stepped Footing"))
{{
    tx.Start();
    double bL = {_ft(1500)}; double bH = {_ft(400)};
    double cL = {_ft(900)};  double cH = {_ft(300)};
    SketchPlane sp = SketchPlane.Create(familyDoc, Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // Base slab
    CurveArray baseLoop = new CurveArray();
    baseLoop.Append(Line.CreateBound(new XYZ(-bL/2,-bL/2,0), new XYZ(bL/2,-bL/2,0)));
    baseLoop.Append(Line.CreateBound(new XYZ(bL/2,-bL/2,0),  new XYZ(bL/2,bL/2,0)));
    baseLoop.Append(Line.CreateBound(new XYZ(bL/2,bL/2,0),   new XYZ(-bL/2,bL/2,0)));
    baseLoop.Append(Line.CreateBound(new XYZ(-bL/2,bL/2,0),  new XYZ(-bL/2,-bL/2,0)));
    CurveArrArray baseProfile = new CurveArrArray();
    baseProfile.Append(baseLoop);
    Extrusion baseExt = familyDoc.FamilyCreate.NewExtrusion(true, baseProfile, sp, bH);
    baseExt.StartOffset = -bH; baseExt.EndOffset = 0;

    // Cap
    SketchPlane spCap = SketchPlane.Create(familyDoc, Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    CurveArray capLoop = new CurveArray();
    capLoop.Append(Line.CreateBound(new XYZ(-cL/2,-cL/2,0), new XYZ(cL/2,-cL/2,0)));
    capLoop.Append(Line.CreateBound(new XYZ(cL/2,-cL/2,0),  new XYZ(cL/2,cL/2,0)));
    capLoop.Append(Line.CreateBound(new XYZ(cL/2,cL/2,0),   new XYZ(-cL/2,cL/2,0)));
    capLoop.Append(Line.CreateBound(new XYZ(-cL/2,cL/2,0),  new XYZ(-cL/2,-cL/2,0)));
    CurveArrArray capProfile = new CurveArrArray();
    capProfile.Append(capLoop);
    familyDoc.FamilyCreate.NewExtrusion(true, capProfile, spCap, cH);
    tx.Commit();
}}"""))
        return samples  # 10 + 1 = 11 samples

    # ------------------------------------------------------------------
    # Structural parameters
    # ------------------------------------------------------------------

    def _structural_parameters(self) -> List[SAMPLE]:
        samples = []

        bip_cases = [
            ("FAMILY_BASE_LEVEL_PARAM",   "base level",    "Get the base level of a structural column"),
            ("FAMILY_TOP_LEVEL_PARAM",    "top level",     "Get the top level of a structural column"),
            ("STRUCTURAL_SECTION_SHAPE",  "section shape", "Read the structural section shape parameter"),
            ("STRUCTURAL_MATERIAL_PARAM", "material",      "Read the structural material parameter"),
        ]
        for (bip, desc, instruction) in bip_cases:
            samples.append(_s(instruction,
                f"""\
using Autodesk.Revit.DB;

FamilyInstance column = new FilteredElementCollector(doc)
    .OfCategory(BuiltInCategory.OST_StructuralColumns)
    .OfClass(typeof(FamilyInstance))
    .Cast<FamilyInstance>()
    .FirstOrDefault();

if (column != null)
{{
    Parameter param = column.get_Parameter(BuiltInParameter.{bip});
    // Read {desc}
    if (param != null)
    {{
        if (param.StorageType == StorageType.ElementId)
        {{
            ElementId eid = param.AsElementId();
            Element el = doc.GetElement(eid);
        }}
        else if (param.StorageType == StorageType.Integer)
        {{
            int val = param.AsInteger();
        }}
    }}
}}"""))

        for (param_name, group, ptype, default_mm, desc) in [
            ("FramingWidth",  "PG_GEOMETRY",    "ParameterType.Length", 200, "framing width 200mm"),
            ("FramingDepth",  "PG_GEOMETRY",    "ParameterType.Length", 400, "framing depth 400mm"),
            ("DesignLoad",    "PG_STRUCTURAL",  "ParameterType.Number",  50, "design load 50 (kN)"),
            ("SeismicZone",   "PG_STRUCTURAL",  "ParameterType.Text",     0, "seismic zone text"),
            ("WindExposure",  "PG_STRUCTURAL",  "ParameterType.Text",     0, "wind exposure category"),
            ("CoverDepth",    "PG_STRUCTURAL",  "ParameterType.Length",  40, "rebar cover 40mm"),
        ]:
            if ptype == "ParameterType.Length" and default_mm > 0:
                set_line = f'famMgr.Set(p, {_ft(default_mm)}); // {default_mm} mm'
            elif ptype == "ParameterType.Number":
                set_line = f'famMgr.Set(p, {float(default_mm)}); // {default_mm}'
            else:
                set_line = f'famMgr.Set(p, ""); // empty default text'
            samples.append(_s(f"Add a '{param_name}' structural parameter ({desc}) to a family",
                f"""\
using Autodesk.Revit.DB;

// FamilyManager operation OUTSIDE Transaction
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter p = famMgr.AddParameter(
    "{param_name}",
    BuiltInParameterGroup.{group},
    {ptype},
    false); // false = type parameter
{set_line}"""))

        # Structural collector patterns
        for (cat, desc) in [
            ("OST_StructuralColumns", "structural columns"),
            ("OST_StructuralFraming",  "structural beams and braces"),
            ("OST_StructuralFoundation", "structural foundations"),
        ]:
            samples.append(_s(f"Collect all {desc} in the document",
                f"""\
using Autodesk.Revit.DB;
using System.Collections.Generic;

IList<FamilyInstance> elements = new FilteredElementCollector(doc)
    .OfCategory(BuiltInCategory.{cat})
    .OfClass(typeof(FamilyInstance))
    .Cast<FamilyInstance>()
    .ToList();

foreach (FamilyInstance fi in elements)
{{
    string typeName = fi.Symbol.Name;
    string familyName = fi.Symbol.FamilyName;
    ElementId levelId = fi.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)?.AsElementId();
}}"""))

        return samples  # 4 + 6 + 3 = 13 samples

    # ------------------------------------------------------------------
    # Rebar patterns
    # ------------------------------------------------------------------

    def _rebar_patterns(self) -> List[SAMPLE]:
        samples = []

        # Straight rebar
        for (dia, desc) in [(12, "T12"), (16, "T16"), (20, "T20"), (25, "T25"), (32, "T32")]:
            samples.append(_s(f"Create a single straight {desc} rebar in a concrete column",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;
using System;

// Straight {desc} bar ({dia}mm diameter)
using (Transaction tx = new Transaction(doc, "Create {desc} Rebar"))
{{
    tx.Start();

    // Find rebar bar type for {dia}mm
    RebarBarType barType = new FilteredElementCollector(doc)
        .OfClass(typeof(RebarBarType))
        .Cast<RebarBarType>()
        .FirstOrDefault(bt => Math.Abs(bt.BarDiameter - {_ft(dia)}) < 0.001);

    FamilyInstance host = new FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_StructuralColumns)
        .OfClass(typeof(FamilyInstance))
        .Cast<FamilyInstance>()
        .FirstOrDefault();

    if (barType != null && host != null)
    {{
        // Straight bar: 3000mm long
        double length = {_ft(3000)}; // 3000 mm
        XYZ start = new XYZ(0, 0, {_ft(40)});  // 40mm cover
        XYZ end   = new XYZ(0, 0, length);

        RebarHookType noHook = null; // straight bar, no hooks
        Rebar.Create(doc, barType, noHook, noHook,
            RebarStyle.Standard, host,
            new XYZ(1, 0, 0),  // normal to bar plane
            new List<Curve> {{ Line.CreateBound(start, end) }},
            RebarHookOrientation.Left, RebarHookOrientation.Left,
            true, false);
    }}

    tx.Commit();
}}"""))

        # Stirrup/tie rebar
        for (col_w, col_d, desc) in [(300, 300, "square column"), (400, 600, "rectangular column")]:
            samples.append(_s(f"Create a closed stirrup for a {col_w}x{col_d}mm concrete {desc}",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;
using System.Collections.Generic;

// Closed rectangular stirrup: {col_w}x{col_d}mm column, 40mm cover
using (Transaction tx = new Transaction(doc, "Create Stirrup"))
{{
    tx.Start();

    RebarBarType barType = new FilteredElementCollector(doc)
        .OfClass(typeof(RebarBarType)).Cast<RebarBarType>()
        .FirstOrDefault(bt => Math.Abs(bt.BarDiameter - {_ft(10)}) < 0.001); // T10 stirrup

    FamilyInstance host = new FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_StructuralColumns)
        .OfClass(typeof(FamilyInstance)).Cast<FamilyInstance>().FirstOrDefault();

    if (barType != null && host != null)
    {{
        double cover = {_ft(40)}; // 40 mm cover
        double bw = {_ft(col_w)} - 2 * cover;
        double bd = {_ft(col_d)} - 2 * cover;

        // Rectangular stirrup path (closed)
        var curves = new List<Curve>
        {{
            Line.CreateBound(new XYZ(-bw/2, -bd/2, 0), new XYZ( bw/2, -bd/2, 0)),
            Line.CreateBound(new XYZ( bw/2, -bd/2, 0), new XYZ( bw/2,  bd/2, 0)),
            Line.CreateBound(new XYZ( bw/2,  bd/2, 0), new XYZ(-bw/2,  bd/2, 0)),
            Line.CreateBound(new XYZ(-bw/2,  bd/2, 0), new XYZ(-bw/2, -bd/2, 0)),
        }};

        RebarHookType hookType90 = new FilteredElementCollector(doc)
            .OfClass(typeof(RebarHookType)).Cast<RebarHookType>()
            .FirstOrDefault(h => h.Name.Contains("90"));

        Rebar.Create(doc, barType, hookType90, hookType90,
            RebarStyle.StirrupTie, host, XYZ.BasisZ, curves,
            RebarHookOrientation.Left, RebarHookOrientation.Left,
            true, false);
    }}
    tx.Commit();
}}"""))

        return samples  # 5 + 2 = 7 samples

    # ------------------------------------------------------------------
    # Steel connections
    # ------------------------------------------------------------------

    def _steel_connections(self) -> List[SAMPLE]:
        samples = []
        plate_cases = [
            (200, 200, 16, "base plate"),
            (300, 300, 20, "heavy base plate"),
            (150, 300, 12, "gusset plate"),
            (100, 200, 10, "clip angle plate"),
            (250, 400, 16, "end plate"),
        ]
        for (pw, ph, t, desc) in plate_cases:
            samples.append(_s(f"Create a {desc} family {pw}x{ph}mm, {t}mm thick",
                f"""\
using Autodesk.Revit.DB;

// Steel {desc}: {pw}x{ph}mm, {t}mm thick
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW = famMgr.AddParameter("PlateWidth",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pH = famMgr.AddParameter("PlateHeight", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pT = famMgr.AddParameter("Thickness",   BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pW, {_ft(pw)}); // {pw} mm
famMgr.Set(pH, {_ft(ph)}); // {ph} mm
famMgr.Set(pT, {_ft(t)});  // {t} mm

using (Transaction tx = new Transaction(familyDoc, "Create {desc.title()}"))
{{
    tx.Start();
    double pw = {_ft(pw)}; double ph = {_ft(ph)}; double t = {_ft(t)};

    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-pw/2, -ph/2, 0), new XYZ( pw/2, -ph/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( pw/2, -ph/2, 0), new XYZ( pw/2,  ph/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( pw/2,  ph/2, 0), new XYZ(-pw/2,  ph/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-pw/2,  ph/2, 0), new XYZ(-pw/2, -ph/2, 0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc, Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, t);
    tx.Commit();
}}"""))
        return samples  # 5 samples


if __name__ == "__main__":
    gen = StructuralFamilyGenerator()
    samples = gen.generate()
    print(f"Generated {len(samples)} samples")
    assert all(set(s.keys()) == {"instruction", "input", "output"} for s in samples)
    print("[OK] All samples valid")
