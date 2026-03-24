"""Training data generator: Advanced Revit family patterns.

Produces ~200 Alpaca-format training pairs covering complex, multi-step
family creation: multi-extrusion families, parametric arrays, conditional
visibility, formula chains, void cuts, swept blends, multi-material setups,
nested family workflows, custom profiles, and adaptive components.
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


class AdvancedFamilyGenerator:
    """Generates training samples for complex, multi-step Revit family patterns."""

    def generate(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []
        samples += self._multi_extrusion_families()
        samples += self._parametric_array_patterns()
        samples += self._conditional_visibility()
        samples += self._formula_chains()
        samples += self._void_cut_patterns()
        samples += self._swept_blend_forms()
        samples += self._multi_material_families()
        samples += self._nested_family_workflows()
        samples += self._complex_profiles()
        samples += self._adaptive_components()
        return samples

    # ------------------------------------------------------------------
    # 1. Multi-extrusion families
    # ------------------------------------------------------------------

    def _multi_extrusion_families(self) -> List[SAMPLE]:
        samples = []

        # Desk: top slab + four legs
        w_ft = _ft(1500)
        d_ft = _ft(750)
        top_h_ft = _ft(30)
        leg_w_ft = _ft(50)
        leg_h_ft = _ft(720)
        desk_h_ft = _ft(750)
        samples.append(_s(
            "Create a parametric desk family with a top slab and four legs using multiple extrusions",
            f"""\
using Autodesk.Revit.DB;

// Multi-extrusion desk: top slab 1500x750x30mm + four 50x50mm legs, 720mm tall
// Total height = 750mm (leg 720mm + slab 30mm)
using (Transaction tx = new Transaction(familyDoc, "Create Desk"))
{{
    tx.Start();

    SketchPlane spZ = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    double w    = {w_ft};  // 1500 mm
    double d    = {d_ft};  // 750 mm
    double topH = {top_h_ft};  // 30 mm slab thickness
    double legW = {leg_w_ft};  // 50 mm leg side
    double legH = {leg_h_ft};  // 720 mm leg height
    double deskH = {desk_h_ft}; // 750 mm total

    // -- Top slab (at z = legH) --
    SketchPlane spTop = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, new XYZ(0, 0, legH)));

    CurveArrArray topProfile = new CurveArrArray();
    CurveArray topLoop = new CurveArray();
    topLoop.Append(Line.CreateBound(new XYZ(-w/2, -d/2, legH), new XYZ( w/2, -d/2, legH)));
    topLoop.Append(Line.CreateBound(new XYZ( w/2, -d/2, legH), new XYZ( w/2,  d/2, legH)));
    topLoop.Append(Line.CreateBound(new XYZ( w/2,  d/2, legH), new XYZ(-w/2,  d/2, legH)));
    topLoop.Append(Line.CreateBound(new XYZ(-w/2,  d/2, legH), new XYZ(-w/2, -d/2, legH)));
    topProfile.Append(topLoop);
    Extrusion slab = familyDoc.FamilyCreate.NewExtrusion(true, topProfile, spTop, topH);
    slab.StartOffset = 0;

    // -- Four legs at corners (at z = 0) --
    double ox = w / 2 - legW / 2 - {_ft(25)}; // 25mm inset
    double oy = d / 2 - legW / 2 - {_ft(25)};

    double[,] corners = new double[,]
    {{
        {{ -ox, -oy }}, {{  ox, -oy }},
        {{  ox,  oy }}, {{ -ox,  oy }}
    }};

    for (int i = 0; i < 4; i++)
    {{
        double cx = corners[i, 0];
        double cy = corners[i, 1];

        CurveArrArray legProfile = new CurveArrArray();
        CurveArray legLoop = new CurveArray();
        legLoop.Append(Line.CreateBound(new XYZ(cx - legW/2, cy - legW/2, 0),
                                        new XYZ(cx + legW/2, cy - legW/2, 0)));
        legLoop.Append(Line.CreateBound(new XYZ(cx + legW/2, cy - legW/2, 0),
                                        new XYZ(cx + legW/2, cy + legW/2, 0)));
        legLoop.Append(Line.CreateBound(new XYZ(cx + legW/2, cy + legW/2, 0),
                                        new XYZ(cx - legW/2, cy + legW/2, 0)));
        legLoop.Append(Line.CreateBound(new XYZ(cx - legW/2, cy + legW/2, 0),
                                        new XYZ(cx - legW/2, cy - legW/2, 0)));
        legProfile.Append(legLoop);
        Extrusion leg = familyDoc.FamilyCreate.NewExtrusion(true, legProfile, spZ, legH);
    }}

    tx.Commit();
}}""",
        ))

        # Table: top + apron stretchers + four legs
        samples.append(_s(
            "Create a rectangular dining table family with top, four apron stretchers, and four legs",
            f"""\
using Autodesk.Revit.DB;

// Table: 1800x900mm top (40mm thick), 50x100mm aprons, 75x75mm legs 700mm tall
using (Transaction tx = new Transaction(familyDoc, "Create Table"))
{{
    tx.Start();

    double w      = {_ft(1800)};  // 1800 mm
    double d      = {_ft(900)};   // 900 mm
    double topThk = {_ft(40)};    // 40 mm
    double apW    = {_ft(50)};    // apron width (face)
    double apH    = {_ft(100)};   // apron height
    double legSz  = {_ft(75)};    // 75 mm leg side
    double legH   = {_ft(700)};   // 700 mm
    double inset  = {_ft(75)};    // leg inset from edge

    SketchPlane spZ = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // Top slab
    SketchPlane spTop = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, new XYZ(0, 0, legH)));
    CurveArrArray topProf = new CurveArrArray();
    CurveArray tl = new CurveArray();
    tl.Append(Line.CreateBound(new XYZ(-w/2, -d/2, legH), new XYZ( w/2, -d/2, legH)));
    tl.Append(Line.CreateBound(new XYZ( w/2, -d/2, legH), new XYZ( w/2,  d/2, legH)));
    tl.Append(Line.CreateBound(new XYZ( w/2,  d/2, legH), new XYZ(-w/2,  d/2, legH)));
    tl.Append(Line.CreateBound(new XYZ(-w/2,  d/2, legH), new XYZ(-w/2, -d/2, legH)));
    topProf.Append(tl);
    familyDoc.FamilyCreate.NewExtrusion(true, topProf, spTop, topThk);

    // Long aprons (front and back)
    double apronZ  = legH - apH;
    double apronLen = w - 2 * inset;
    foreach (double ySign in new[] {{ -1.0, 1.0 }})
    {{
        double apY = ySign * (d / 2 - apW / 2);
        SketchPlane spAp = SketchPlane.Create(familyDoc,
            Plane.CreateByNormalAndOrigin(XYZ.BasisZ, new XYZ(0, 0, apronZ)));
        CurveArrArray apProf = new CurveArrArray();
        CurveArray al = new CurveArray();
        al.Append(Line.CreateBound(new XYZ(-apronLen/2, apY - apW/2, apronZ),
                                   new XYZ( apronLen/2, apY - apW/2, apronZ)));
        al.Append(Line.CreateBound(new XYZ( apronLen/2, apY - apW/2, apronZ),
                                   new XYZ( apronLen/2, apY + apW/2, apronZ)));
        al.Append(Line.CreateBound(new XYZ( apronLen/2, apY + apW/2, apronZ),
                                   new XYZ(-apronLen/2, apY + apW/2, apronZ)));
        al.Append(Line.CreateBound(new XYZ(-apronLen/2, apY + apW/2, apronZ),
                                   new XYZ(-apronLen/2, apY - apW/2, apronZ)));
        apProf.Append(al);
        familyDoc.FamilyCreate.NewExtrusion(true, apProf, spAp, apH);
    }}

    // Four corner legs
    double lx = w / 2 - inset;
    double ly = d / 2 - inset;
    double[,] lc = {{ {{ -lx, -ly }}, {{ lx, -ly }}, {{ lx, ly }}, {{ -lx, ly }} }};
    for (int i = 0; i < 4; i++)
    {{
        double cx = lc[i, 0], cy = lc[i, 1];
        CurveArrArray lp = new CurveArrArray();
        CurveArray ll = new CurveArray();
        ll.Append(Line.CreateBound(new XYZ(cx-legSz/2,cy-legSz/2,0),new XYZ(cx+legSz/2,cy-legSz/2,0)));
        ll.Append(Line.CreateBound(new XYZ(cx+legSz/2,cy-legSz/2,0),new XYZ(cx+legSz/2,cy+legSz/2,0)));
        ll.Append(Line.CreateBound(new XYZ(cx+legSz/2,cy+legSz/2,0),new XYZ(cx-legSz/2,cy+legSz/2,0)));
        ll.Append(Line.CreateBound(new XYZ(cx-legSz/2,cy+legSz/2,0),new XYZ(cx-legSz/2,cy-legSz/2,0)));
        lp.Append(ll);
        familyDoc.FamilyCreate.NewExtrusion(true, lp, spZ, legH);
    }}

    tx.Commit();
}}""",
        ))

        # Bookshelf: carcass + shelves
        samples.append(_s(
            "Create a bookshelf family with two side panels, top, bottom, and three adjustable shelves",
            f"""\
using Autodesk.Revit.DB;

// Bookshelf: 900mm wide, 300mm deep, 2100mm tall; 18mm panel thickness; 3 shelves
using (Transaction tx = new Transaction(familyDoc, "Create Bookshelf"))
{{
    tx.Start();

    double W    = {_ft(900)};   // 900 mm
    double D    = {_ft(300)};   // 300 mm
    double H    = {_ft(2100)};  // 2100 mm
    double thk  = {_ft(18)};    // 18 mm panel thickness

    SketchPlane spZ = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // Left panel
    CurveArrArray lpProf = new CurveArrArray();
    CurveArray lpL = new CurveArray();
    lpL.Append(Line.CreateBound(new XYZ(-W/2,     -D/2, 0), new XYZ(-W/2+thk, -D/2, 0)));
    lpL.Append(Line.CreateBound(new XYZ(-W/2+thk, -D/2, 0), new XYZ(-W/2+thk,  D/2, 0)));
    lpL.Append(Line.CreateBound(new XYZ(-W/2+thk,  D/2, 0), new XYZ(-W/2,      D/2, 0)));
    lpL.Append(Line.CreateBound(new XYZ(-W/2,      D/2, 0), new XYZ(-W/2,     -D/2, 0)));
    lpProf.Append(lpL);
    familyDoc.FamilyCreate.NewExtrusion(true, lpProf, spZ, H);

    // Right panel
    CurveArrArray rpProf = new CurveArrArray();
    CurveArray rpL = new CurveArray();
    rpL.Append(Line.CreateBound(new XYZ(W/2-thk, -D/2, 0), new XYZ(W/2,     -D/2, 0)));
    rpL.Append(Line.CreateBound(new XYZ(W/2,     -D/2, 0), new XYZ(W/2,      D/2, 0)));
    rpL.Append(Line.CreateBound(new XYZ(W/2,      D/2, 0), new XYZ(W/2-thk,  D/2, 0)));
    rpL.Append(Line.CreateBound(new XYZ(W/2-thk,  D/2, 0), new XYZ(W/2-thk, -D/2, 0)));
    rpProf.Append(rpL);
    familyDoc.FamilyCreate.NewExtrusion(true, rpProf, spZ, H);

    // Top, bottom, and 3 shelves as horizontal panels
    double innerW = W - 2 * thk;
    double[] shelfZ = new[] {{ 0.0, H - thk,
        H * 0.25, H * 0.50, H * 0.75 }}; // bottom, top, 3 shelves

    foreach (double sz in shelfZ)
    {{
        SketchPlane spS = SketchPlane.Create(familyDoc,
            Plane.CreateByNormalAndOrigin(XYZ.BasisZ, new XYZ(0, 0, sz)));
        CurveArrArray sProf = new CurveArrArray();
        CurveArray sL = new CurveArray();
        double x0 = -W/2 + thk, x1 = W/2 - thk;
        sL.Append(Line.CreateBound(new XYZ(x0, -D/2, sz), new XYZ(x1, -D/2, sz)));
        sL.Append(Line.CreateBound(new XYZ(x1, -D/2, sz), new XYZ(x1,  D/2, sz)));
        sL.Append(Line.CreateBound(new XYZ(x1,  D/2, sz), new XYZ(x0,  D/2, sz)));
        sL.Append(Line.CreateBound(new XYZ(x0,  D/2, sz), new XYZ(x0, -D/2, sz)));
        sProf.Append(sL);
        familyDoc.FamilyCreate.NewExtrusion(true, sProf, spS, thk);
    }}

    tx.Commit();
}}""",
        ))

        # Cabinet body with door recess
        samples.append(_s(
            "Create a wall cabinet family with a recessed door opening using two extrusions",
            f"""\
using Autodesk.Revit.DB;

// Wall cabinet: 600x300x700mm body with 540x640mm door recess (20mm border)
using (Transaction tx = new Transaction(familyDoc, "Create Cabinet"))
{{
    tx.Start();

    double W   = {_ft(600)};  // 600 mm
    double D   = {_ft(300)};  // 300 mm
    double H   = {_ft(700)};  // 700 mm
    double thk = {_ft(20)};   // 20 mm shell thickness

    SketchPlane spZ = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // Outer shell as hollow box (outer minus inner profile)
    CurveArrArray shellProf = new CurveArrArray();

    // Outer loop
    CurveArray outerL = new CurveArray();
    outerL.Append(Line.CreateBound(new XYZ(-W/2, -D/2, 0), new XYZ( W/2, -D/2, 0)));
    outerL.Append(Line.CreateBound(new XYZ( W/2, -D/2, 0), new XYZ( W/2,  D/2, 0)));
    outerL.Append(Line.CreateBound(new XYZ( W/2,  D/2, 0), new XYZ(-W/2,  D/2, 0)));
    outerL.Append(Line.CreateBound(new XYZ(-W/2,  D/2, 0), new XYZ(-W/2, -D/2, 0)));
    shellProf.Append(outerL);

    // Inner loop (hollow)
    double ix0 = -W/2 + thk, ix1 = W/2 - thk;
    double iy0 = -D/2 + thk, iy1 =  D/2; // open front
    CurveArray innerL = new CurveArray();
    innerL.Append(Line.CreateBound(new XYZ(ix0, iy0, 0), new XYZ(ix1, iy0, 0)));
    innerL.Append(Line.CreateBound(new XYZ(ix1, iy0, 0), new XYZ(ix1, iy1, 0)));
    innerL.Append(Line.CreateBound(new XYZ(ix1, iy1, 0), new XYZ(ix0, iy1, 0)));
    innerL.Append(Line.CreateBound(new XYZ(ix0, iy1, 0), new XYZ(ix0, iy0, 0)));
    shellProf.Append(innerL);

    familyDoc.FamilyCreate.NewExtrusion(true, shellProf, spZ, H);

    tx.Commit();
}}""",
        ))

        # Window frame: outer casing + inner sill extrusion
        samples.append(_s(
            "Create a window family with two extrusions: outer frame casing and interior sill",
            f"""\
using Autodesk.Revit.DB;

// Window: 1200x1500mm rough opening; 75mm frame; 200mm deep sill at bottom
using (Transaction tx = new Transaction(familyDoc, "Create Window Frame"))
{{
    tx.Start();

    double RW   = {_ft(1200)}; // rough opening width
    double RH   = {_ft(1500)}; // rough opening height
    double FrW  = {_ft(75)};   // frame width
    double FrD  = {_ft(150)};  // frame depth
    double SillD = {_ft(200)}; // sill depth

    SketchPlane spZ = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // Frame as hollow rectangular profile
    CurveArrArray frameProf = new CurveArrArray();
    CurveArray outerF = new CurveArray();
    outerF.Append(Line.CreateBound(new XYZ(-RW/2, 0, 0),    new XYZ( RW/2, 0, 0)));
    outerF.Append(Line.CreateBound(new XYZ( RW/2, 0, 0),    new XYZ( RW/2, FrD, 0)));
    outerF.Append(Line.CreateBound(new XYZ( RW/2, FrD, 0),  new XYZ(-RW/2, FrD, 0)));
    outerF.Append(Line.CreateBound(new XYZ(-RW/2, FrD, 0),  new XYZ(-RW/2, 0, 0)));
    frameProf.Append(outerF);

    double iw = RW - 2*FrW, ih = RH - 2*FrW;
    CurveArray innerF = new CurveArray();
    innerF.Append(Line.CreateBound(new XYZ(-iw/2, 0, FrW),  new XYZ( iw/2, 0, FrW)));
    innerF.Append(Line.CreateBound(new XYZ( iw/2, 0, FrW),  new XYZ( iw/2, FrD, FrW)));
    innerF.Append(Line.CreateBound(new XYZ( iw/2, FrD, FrW),new XYZ(-iw/2, FrD, FrW)));
    innerF.Append(Line.CreateBound(new XYZ(-iw/2, FrD, FrW),new XYZ(-iw/2, 0, FrW)));
    frameProf.Append(innerF);

    SketchPlane spY = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, frameProf, spY, RH);

    // Interior sill at bottom
    SketchPlane spSill = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    CurveArrArray sillProf = new CurveArrArray();
    CurveArray sillL = new CurveArray();
    sillL.Append(Line.CreateBound(new XYZ(-RW/2,     0,     0), new XYZ(RW/2,     0,     0)));
    sillL.Append(Line.CreateBound(new XYZ( RW/2,     0,     0), new XYZ(RW/2,     SillD, 0)));
    sillL.Append(Line.CreateBound(new XYZ( RW/2,     SillD, 0), new XYZ(-RW/2,    SillD, 0)));
    sillL.Append(Line.CreateBound(new XYZ(-RW/2,     SillD, 0), new XYZ(-RW/2,    0,     0)));
    sillProf.Append(sillL);
    familyDoc.FamilyCreate.NewExtrusion(true, sillProf, spSill, FrW);

    tx.Commit();
}}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # 2. Parametric array patterns
    # ------------------------------------------------------------------

    def _parametric_array_patterns(self) -> List[SAMPLE]:
        samples = []

        # Linear array of balusters driven by count parameter
        samples.append(_s(
            "Create a parametric baluster array family where the number of balusters is controlled by a family parameter",
            f"""\
using Autodesk.Revit.DB;

// Parametric baluster array: count param drives loop; spacing = Length / (Count - 1)
// Step 1: Add parameters (outside Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pCount  = famMgr.AddParameter("BalusterCount",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Integer, false);
FamilyParameter pLength = famMgr.AddParameter("RailingLength",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pHeight = famMgr.AddParameter("BalusterHeight",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pCount,  5);
famMgr.Set(pLength, {_ft(2000)}); // 2000 mm
famMgr.Set(pHeight, {_ft(900)});  // 900 mm

// Step 2: Create geometry (inside Transaction) -- uses current param values
using (Transaction tx = new Transaction(familyDoc, "Create Baluster Array"))
{{
    tx.Start();

    int    count  = 5;
    double length = {_ft(2000)};
    double height = {_ft(900)};
    double bSz    = {_ft(50)};  // 50mm square baluster

    double spacing = (count > 1) ? length / (count - 1) : 0;

    SketchPlane spZ = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    for (int i = 0; i < count; i++)
    {{
        double cx = -length / 2 + i * spacing;

        CurveArrArray prof = new CurveArrArray();
        CurveArray loop = new CurveArray();
        loop.Append(Line.CreateBound(new XYZ(cx-bSz/2, -bSz/2, 0),
                                     new XYZ(cx+bSz/2, -bSz/2, 0)));
        loop.Append(Line.CreateBound(new XYZ(cx+bSz/2, -bSz/2, 0),
                                     new XYZ(cx+bSz/2,  bSz/2, 0)));
        loop.Append(Line.CreateBound(new XYZ(cx+bSz/2,  bSz/2, 0),
                                     new XYZ(cx-bSz/2,  bSz/2, 0)));
        loop.Append(Line.CreateBound(new XYZ(cx-bSz/2,  bSz/2, 0),
                                     new XYZ(cx-bSz/2, -bSz/2, 0)));
        prof.Append(loop);
        familyDoc.FamilyCreate.NewExtrusion(true, prof, spZ, height);
    }}

    tx.Commit();
}}""",
        ))

        # Radial array of bolt holes
        samples.append(_s(
            "Create a bolt-hole radial array family with a parameter controlling the number of holes on a bolt circle",
            f"""\
using Autodesk.Revit.DB;
using System;

// Radial bolt pattern: BoltCount holes on BoltCircleRadius
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pBoltCount  = famMgr.AddParameter("BoltCount",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Integer, false);
FamilyParameter pBoltRadius = famMgr.AddParameter("BoltCircleRadius",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pHoleDiam   = famMgr.AddParameter("HoleDiameter",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pBoltCount,  6);
famMgr.Set(pBoltRadius, {_ft(100)}); // 100 mm PCD
famMgr.Set(pHoleDiam,   {_ft(18)});  // 18 mm hole

using (Transaction tx = new Transaction(familyDoc, "Create Bolt Hole Array"))
{{
    tx.Start();

    int    n       = 6;
    double pcd     = {_ft(100)};  // pitch circle diameter radius
    double holeR   = {_ft(9)};    // 9 mm radius (18mm diam)
    int    segs    = 16;

    SketchPlane spZ = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    for (int i = 0; i < n; i++)
    {{
        double angle = 2 * Math.PI * i / n;
        double cx = pcd * Math.Cos(angle);
        double cy = pcd * Math.Sin(angle);

        // Circle approximation for void hole
        CurveArray holeLoop = new CurveArray();
        for (int s = 0; s < segs; s++)
        {{
            double a0 = 2 * Math.PI * s / segs;
            double a1 = 2 * Math.PI * (s + 1) / segs;
            holeLoop.Append(Line.CreateBound(
                new XYZ(cx + holeR * Math.Cos(a0), cy + holeR * Math.Sin(a0), 0),
                new XYZ(cx + holeR * Math.Cos(a1), cy + holeR * Math.Sin(a1), 0)));
        }}
        CurveArrArray holeProf = new CurveArrArray();
        holeProf.Append(holeLoop);

        // isSolid=false --> void through-hole
        familyDoc.FamilyCreate.NewExtrusion(false, holeProf, spZ, {_ft(30)}); // 30mm deep
    }}

    tx.Commit();
}}""",
        ))

        # Grid of studs
        samples.append(_s(
            "Create a stud grid family with rows and columns of cylindrical studs driven by RowCount and ColumnCount parameters",
            f"""\
using Autodesk.Revit.DB;
using System;

// Stud grid: RowCount x ColumnCount cylinders on a pitch grid
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pRows    = famMgr.AddParameter("RowCount",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Integer, false);
FamilyParameter pCols    = famMgr.AddParameter("ColumnCount",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Integer, false);
FamilyParameter pPitch   = famMgr.AddParameter("StudPitch",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pStudH   = famMgr.AddParameter("StudHeight",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pRows,  3);
famMgr.Set(pCols,  4);
famMgr.Set(pPitch, {_ft(50)});  // 50 mm pitch
famMgr.Set(pStudH, {_ft(8)});   // 8 mm stud height

using (Transaction tx = new Transaction(familyDoc, "Create Stud Grid"))
{{
    tx.Start();

    int    rows  = 3;
    int    cols  = 4;
    double pitch = {_ft(50)};
    double studH = {_ft(8)};
    double studR = {_ft(4)};  // 4mm radius
    int    segs  = 12;

    SketchPlane spZ = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    double totalW = (cols - 1) * pitch;
    double totalD = (rows - 1) * pitch;

    for (int r = 0; r < rows; r++)
    {{
        for (int c = 0; c < cols; c++)
        {{
            double cx = -totalW / 2 + c * pitch;
            double cy = -totalD / 2 + r * pitch;

            CurveArray studLoop = new CurveArray();
            for (int s = 0; s < segs; s++)
            {{
                double a0 = 2 * Math.PI * s / segs;
                double a1 = 2 * Math.PI * (s + 1) / segs;
                studLoop.Append(Line.CreateBound(
                    new XYZ(cx + studR * Math.Cos(a0), cy + studR * Math.Sin(a0), 0),
                    new XYZ(cx + studR * Math.Cos(a1), cy + studR * Math.Sin(a1), 0)));
            }}
            CurveArrArray studProf = new CurveArrArray();
            studProf.Append(studLoop);
            familyDoc.FamilyCreate.NewExtrusion(true, studProf, spZ, studH);
        }}
    }}

    tx.Commit();
}}""",
        ))

        # Fin array on a panel
        samples.append(_s(
            "Create a heat sink family with a base plate and an array of cooling fins controlled by a FinCount parameter",
            f"""\
using Autodesk.Revit.DB;

// Heat sink: 200x200mm base 10mm thick + FinCount thin fins 5mm wide 40mm tall
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pFinCount = famMgr.AddParameter("FinCount",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Integer, false);
famMgr.Set(pFinCount, 8);

using (Transaction tx = new Transaction(familyDoc, "Create Heat Sink"))
{{
    tx.Start();

    double baseW  = {_ft(200)}; // 200 mm
    double baseD  = {_ft(200)}; // 200 mm
    double baseH  = {_ft(10)};  // 10 mm base
    double finW   = {_ft(5)};   // 5 mm fin width
    double finH   = {_ft(40)};  // 40 mm fin height
    int    nFins  = 8;

    SketchPlane spZ = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // Base plate
    CurveArrArray baseProf = new CurveArrArray();
    CurveArray bl = new CurveArray();
    bl.Append(Line.CreateBound(new XYZ(-baseW/2,-baseD/2,0),new XYZ( baseW/2,-baseD/2,0)));
    bl.Append(Line.CreateBound(new XYZ( baseW/2,-baseD/2,0),new XYZ( baseW/2, baseD/2,0)));
    bl.Append(Line.CreateBound(new XYZ( baseW/2, baseD/2,0),new XYZ(-baseW/2, baseD/2,0)));
    bl.Append(Line.CreateBound(new XYZ(-baseW/2, baseD/2,0),new XYZ(-baseW/2,-baseD/2,0)));
    baseProf.Append(bl);
    familyDoc.FamilyCreate.NewExtrusion(true, baseProf, spZ, baseH);

    // Fins above base
    SketchPlane spFin = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, new XYZ(0, 0, baseH)));

    double spacing = (nFins > 1) ? (baseW - finW) / (nFins - 1) : 0;

    for (int i = 0; i < nFins; i++)
    {{
        double fx = -baseW/2 + finW/2 + i * spacing;
        CurveArrArray finProf = new CurveArrArray();
        CurveArray fl = new CurveArray();
        fl.Append(Line.CreateBound(new XYZ(fx-finW/2,-baseD/2,baseH),new XYZ(fx+finW/2,-baseD/2,baseH)));
        fl.Append(Line.CreateBound(new XYZ(fx+finW/2,-baseD/2,baseH),new XYZ(fx+finW/2, baseD/2,baseH)));
        fl.Append(Line.CreateBound(new XYZ(fx+finW/2, baseD/2,baseH),new XYZ(fx-finW/2, baseD/2,baseH)));
        fl.Append(Line.CreateBound(new XYZ(fx-finW/2, baseD/2,baseH),new XYZ(fx-finW/2,-baseD/2,baseH)));
        finProf.Append(fl);
        familyDoc.FamilyCreate.NewExtrusion(true, finProf, spFin, finH);
    }}

    tx.Commit();
}}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # 3. Conditional visibility by detail level
    # ------------------------------------------------------------------

    def _conditional_visibility(self) -> List[SAMPLE]:
        samples = []

        # Coarse/medium/fine three-level pattern
        samples.append(_s(
            "Create three extrusions for a column family, each visible at a different detail level (coarse, medium, fine)",
            f"""\
using Autodesk.Revit.DB;
using System;
using System.Linq;

// Three detail-level extrusions: simple box (coarse), octagonal (medium), 16-sided (fine)
using (Transaction tx = new Transaction(familyDoc, "Create Multi-LOD Column"))
{{
    tx.Start();

    double R = {_ft(150)};   // 150 mm radius
    double H = {_ft(3000)};  // 3000 mm height

    SketchPlane spZ = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // Coarse: simple square box
    CurveArrArray coarseProf = new CurveArrArray();
    CurveArray cl = new CurveArray();
    cl.Append(Line.CreateBound(new XYZ(-R,-R,0),new XYZ( R,-R,0)));
    cl.Append(Line.CreateBound(new XYZ( R,-R,0),new XYZ( R, R,0)));
    cl.Append(Line.CreateBound(new XYZ( R, R,0),new XYZ(-R, R,0)));
    cl.Append(Line.CreateBound(new XYZ(-R, R,0),new XYZ(-R,-R,0)));
    coarseProf.Append(cl);
    Extrusion coarseExt = familyDoc.FamilyCreate.NewExtrusion(true, coarseProf, spZ, H);
    FamilyElementVisibility coarseVis = new FamilyElementVisibility(FamilyElementVisibilityType.Model);
    coarseVis.IsShownInCoarse = true;  coarseVis.IsShownInMedium = false; coarseVis.IsShownInFine = false;
    coarseExt.SetVisibility(coarseVis);

    // Medium: octagonal
    double a45 = R * 0.7071;
    XYZ[] octPts = {{ new XYZ(R,0,0), new XYZ(a45,a45,0), new XYZ(0,R,0), new XYZ(-a45,a45,0),
                      new XYZ(-R,0,0), new XYZ(-a45,-a45,0), new XYZ(0,-R,0), new XYZ(a45,-a45,0) }};
    CurveArrArray medProf = new CurveArrArray();
    CurveArray ml = new CurveArray();
    for (int i = 0; i < 8; i++) ml.Append(Line.CreateBound(octPts[i], octPts[(i+1)%8]));
    medProf.Append(ml);
    Extrusion medExt = familyDoc.FamilyCreate.NewExtrusion(true, medProf, spZ, H);
    FamilyElementVisibility medVis = new FamilyElementVisibility(FamilyElementVisibilityType.Model);
    medVis.IsShownInCoarse = false; medVis.IsShownInMedium = true; medVis.IsShownInFine = false;
    medExt.SetVisibility(medVis);

    // Fine: 16-sided polygon
    CurveArrArray fineProf = new CurveArrArray();
    CurveArray fl = new CurveArray();
    int nSeg = 16;
    XYZ prevPt = new XYZ(R, 0, 0);
    for (int i = 1; i <= nSeg; i++)
    {{
        double ang = 2 * Math.PI * i / nSeg;
        XYZ curPt = new XYZ(R * Math.Cos(ang), R * Math.Sin(ang), 0);
        fl.Append(Line.CreateBound(prevPt, curPt));
        prevPt = curPt;
    }}
    fineProf.Append(fl);
    Extrusion fineExt = familyDoc.FamilyCreate.NewExtrusion(true, fineProf, spZ, H);
    FamilyElementVisibility fineVis = new FamilyElementVisibility(FamilyElementVisibilityType.Model);
    fineVis.IsShownInCoarse = false; fineVis.IsShownInMedium = false; fineVis.IsShownInFine = true;
    fineExt.SetVisibility(fineVis);

    tx.Commit();
}}""",
        ))

        # YesNo parameter visibility gate
        samples.append(_s(
            "Create a family where a YesNo parameter controls visibility of a decorative cap extrusion",
            f"""\
using Autodesk.Revit.DB;

// YesNo visibility: 'ShowDecoration' param shows/hides a decorative cap
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pShowDec = famMgr.AddParameter(
    "ShowDecoration",
    BuiltInParameterGroup.PG_VISIBILITY,
    ParameterType.YesNo,
    true);
famMgr.Set(pShowDec, 1); // default: visible

using (Transaction tx = new Transaction(familyDoc, "Create Conditional Cap"))
{{
    tx.Start();

    double W    = {_ft(200)};   // 200 mm
    double capH = {_ft(50)};    // 50 mm cap height
    double baseZ = {_ft(500)};  // 500 mm above ground

    SketchPlane spCap = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, new XYZ(0, 0, baseZ)));

    CurveArrArray capProf = new CurveArrArray();
    CurveArray capL = new CurveArray();
    capL.Append(Line.CreateBound(new XYZ(-W/2,-W/2,baseZ),new XYZ( W/2,-W/2,baseZ)));
    capL.Append(Line.CreateBound(new XYZ( W/2,-W/2,baseZ),new XYZ( W/2, W/2,baseZ)));
    capL.Append(Line.CreateBound(new XYZ( W/2, W/2,baseZ),new XYZ(-W/2, W/2,baseZ)));
    capL.Append(Line.CreateBound(new XYZ(-W/2, W/2,baseZ),new XYZ(-W/2,-W/2,baseZ)));
    capProf.Append(capL);
    Extrusion capExt = familyDoc.FamilyCreate.NewExtrusion(true, capProf, spCap, capH);

    // Associate built-in IS_VISIBLE_PARAM with the YesNo family parameter
    Parameter visParam = capExt.get_Parameter(BuiltInParameter.IS_VISIBLE_PARAM);
    if (visParam != null && !visParam.IsReadOnly)
        famMgr.AssociateElementParameterToFamilyParameter(visParam, pShowDec);

    tx.Commit();
}}""",
        ))

        # Plan-only symbolic lines
        samples.append(_s(
            "Add a plan-only symbolic line representation (2D overhead view) to a furniture family",
            f"""\
using Autodesk.Revit.DB;

// Plan-only 2D symbol: visible in floor plan views only, not elevation or 3D
using (Transaction tx = new Transaction(familyDoc, "Create Plan Symbol"))
{{
    tx.Start();

    double W = {_ft(600)}; // 600 mm
    double D = {_ft(300)}; // 300 mm

    SketchPlane spZ = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // Symbolic lines use NewSymbolicCurve -- visible only in cut/plan views
    Curve[] planLines = new Curve[]
    {{
        Line.CreateBound(new XYZ(-W/2,-D/2,0), new XYZ( W/2,-D/2,0)),
        Line.CreateBound(new XYZ( W/2,-D/2,0), new XYZ( W/2, D/2,0)),
        Line.CreateBound(new XYZ( W/2, D/2,0), new XYZ(-W/2, D/2,0)),
        Line.CreateBound(new XYZ(-W/2, D/2,0), new XYZ(-W/2,-D/2,0)),
        // Diagonal cross indicating plan symbol
        Line.CreateBound(new XYZ(-W/2,-D/2,0), new XYZ( W/2, D/2,0)),
        Line.CreateBound(new XYZ( W/2,-D/2,0), new XYZ(-W/2, D/2,0)),
    }};

    foreach (Curve c in planLines)
        familyDoc.FamilyCreate.NewSymbolicCurve(c, spZ);

    tx.Commit();
}}""",
        ))

        # Elevation-only extrusion
        samples.append(_s(
            "Create an extrusion that is visible in front and back elevations but hidden in plan and section views",
            f"""\
using Autodesk.Revit.DB;

// Elevation-only 3D geometry: hidden in plan/section
using (Transaction tx = new Transaction(familyDoc, "Create Elevation-Only Element"))
{{
    tx.Start();

    double W = {_ft(400)};
    double H = {_ft(600)};
    double D = {_ft(10)};   // thin slab

    SketchPlane spY = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    CurveArrArray prof = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-W/2, 0, 0), new XYZ( W/2, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ( W/2, 0, 0), new XYZ( W/2, 0, H)));
    loop.Append(Line.CreateBound(new XYZ( W/2, 0, H), new XYZ(-W/2, 0, H)));
    loop.Append(Line.CreateBound(new XYZ(-W/2, 0, H), new XYZ(-W/2, 0, 0)));
    prof.Append(loop);

    Extrusion elevExt = familyDoc.FamilyCreate.NewExtrusion(true, prof, spY, D);

    FamilyElementVisibility vis = new FamilyElementVisibility(FamilyElementVisibilityType.Model);
    vis.IsShownInCoarse        = true;
    vis.IsShownInMedium        = true;
    vis.IsShownInFine          = true;
    vis.IsShownInFrontBack      = true;
    vis.IsShownInLeftRight      = false;
    vis.IsShownInPlanRCPCut     = false;
    elevExt.SetVisibility(vis);

    tx.Commit();
}}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # 4. Formula chains
    # ------------------------------------------------------------------

    def _formula_chains(self) -> List[SAMPLE]:
        samples = []

        # Golden ratio chain
        samples.append(_s(
            "Create a family with a formula chain where Height = Width * 1.618 (golden ratio) and Depth = Width / 2",
            """\
using Autodesk.Revit.DB;

// Formula chain: Depth = Width / 2; Height = Width * 1.618
FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter pWidth  = famMgr.AddParameter("Width",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pDepth  = famMgr.AddParameter("Depth",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pHeight = famMgr.AddParameter("Height",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pWidth, 0.984252); // 300 mm seed value

// Chain: formulas reference earlier parameters
famMgr.SetFormula(pDepth,  "Width / 2");
famMgr.SetFormula(pHeight, "Width * 1.618");

// Geometry (inside Transaction) uses current seed values
using (Transaction tx = new Transaction(familyDoc, "Create Golden Ratio Box"))
{
    tx.Start();

    double w = 0.984252;      // 300 mm
    double d = w / 2;
    double h = w * 1.618;

    CurveArrArray prof = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-w/2,-d/2,0), new XYZ( w/2,-d/2,0)));
    loop.Append(Line.CreateBound(new XYZ( w/2,-d/2,0), new XYZ( w/2, d/2,0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, d/2,0), new XYZ(-w/2, d/2,0)));
    loop.Append(Line.CreateBound(new XYZ(-w/2, d/2,0), new XYZ(-w/2,-d/2,0)));
    prof.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, prof, sp, h);

    tx.Commit();
}""",
        ))

        # Conditional if() formula
        samples.append(_s(
            "Use the Revit family formula if() syntax to switch between two height values based on a YesNo parameter",
            """\
using Autodesk.Revit.DB;

// Conditional formula: Height = if(IsExtended, ExtendedHeight, StandardHeight)
FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter pStdH   = famMgr.AddParameter("StandardHeight",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pExtH   = famMgr.AddParameter("ExtendedHeight",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pIsExt  = famMgr.AddParameter("IsExtended",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.YesNo, false);
FamilyParameter pHeight = famMgr.AddParameter("Height",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pStdH,  0.984252); // 300 mm
famMgr.Set(pExtH,  1.968504); // 600 mm
famMgr.Set(pIsExt, 0);        // default: not extended

// Revit if() formula syntax: if(condition, trueValue, falseValue)
famMgr.SetFormula(pHeight, "if(IsExtended, ExtendedHeight, StandardHeight)");
// Height parameter is now formula-driven; never set it directly""",
        ))

        # Multi-level composite wall chain
        samples.append(_s(
            "Create a formula chain where WallThickness drives CoreThickness, FinishThickness, and TotalThickness",
            f"""\
using Autodesk.Revit.DB;

// Composite wall formula chain
// CoreThickness    = WallThickness * 0.6
// FinishThickness  = WallThickness * 0.2
// TotalThickness   = CoreThickness + FinishThickness * 2 = WallThickness
FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter pWall   = famMgr.AddParameter("WallThickness",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pCore   = famMgr.AddParameter("CoreThickness",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pFinish = famMgr.AddParameter("FinishThickness",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pTotal  = famMgr.AddParameter("TotalThickness",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pWall, {_ft(200)}); // 200 mm seed

famMgr.SetFormula(pCore,   "WallThickness * 0.6");
famMgr.SetFormula(pFinish, "WallThickness * 0.2");
famMgr.SetFormula(pTotal,  "CoreThickness + FinishThickness * 2");
// TotalThickness validates to WallThickness (0.6W + 0.4W = W)""",
        ))

        # Lookup via type catalog
        samples.append(_s(
            "Create a family type catalog acting as a size lookup table with Small, Medium, and Large types",
            f"""\
using Autodesk.Revit.DB;

// Type catalog lookup table: three types encoding discrete W/D/H combinations
FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter pWidth  = famMgr.AddParameter("Width",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pDepth  = famMgr.AddParameter("Depth",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pHeight = famMgr.AddParameter("Height",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

var sizeTable = new (string name, double w, double d, double h)[]
{{
    ("Small",  {_ft(300)}, {_ft(300)}, {_ft(600)}),
    ("Medium", {_ft(600)}, {_ft(400)}, {_ft(900)}),
    ("Large",  {_ft(900)}, {_ft(500)}, {_ft(1200)}),
}};

FamilyType savedType = famMgr.CurrentType;

foreach (var (name, w, d, h) in sizeTable)
{{
    FamilyType ft = famMgr.NewType(name);
    famMgr.CurrentType = ft;
    famMgr.Set(pWidth,  w);
    famMgr.Set(pDepth,  d);
    famMgr.Set(pHeight, h);
}}

famMgr.CurrentType = savedType; // restore default""",
        ))

        # Trigonometric / sqrt formula
        samples.append(_s(
            "Use sqrt() in a Revit family formula to compute the diagonal of a rectangular panel from Width and Depth",
            f"""\
using Autodesk.Revit.DB;

// Diagonal = sqrt(Width^2 + Depth^2); DiagonalAngle = asin(Depth / Diagonal)
FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter pW     = famMgr.AddParameter("Width",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pD     = famMgr.AddParameter("Depth",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pDiag  = famMgr.AddParameter("Diagonal",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pAngle = famMgr.AddParameter("DiagonalAngle",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Angle, false);

famMgr.Set(pW, {_ft(400)}); // 400 mm
famMgr.Set(pD, {_ft(300)}); // 300 mm

// sqrt() and asin() are valid Revit formula functions
// ^ is the power operator in Revit formulas
famMgr.SetFormula(pDiag,  "sqrt(Width ^ 2 + Depth ^ 2)");
famMgr.SetFormula(pAngle, "asin(Depth / Diagonal)");""",
        ))

        return samples

    # ------------------------------------------------------------------
    # 5. Void cut patterns
    # ------------------------------------------------------------------

    def _void_cut_patterns(self) -> List[SAMPLE]:
        samples = []

        # Perforated panel: grid of circular voids
        samples.append(_s(
            "Create a perforated metal panel family with a grid of circular void cuts",
            f"""\
using Autodesk.Revit.DB;
using System;

// Perforated panel: 600x600x10mm solid with 5x5 grid of 40mm diameter void holes
using (Transaction tx = new Transaction(familyDoc, "Create Perforated Panel"))
{{
    tx.Start();

    double panW   = {_ft(600)};  // 600 mm panel width
    double panD   = {_ft(600)};  // 600 mm panel depth
    double panThk = {_ft(10)};   // 10 mm thickness
    double holeR  = {_ft(20)};   // 20 mm hole radius (40mm dia)
    double pitch  = {_ft(100)};  // 100 mm hole pitch
    int    nHoles = 5;
    int    segs   = 16;

    SketchPlane spZ = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // Solid base panel
    CurveArrArray panProf = new CurveArrArray();
    CurveArray pl = new CurveArray();
    pl.Append(Line.CreateBound(new XYZ(-panW/2,-panD/2,0),new XYZ( panW/2,-panD/2,0)));
    pl.Append(Line.CreateBound(new XYZ( panW/2,-panD/2,0),new XYZ( panW/2, panD/2,0)));
    pl.Append(Line.CreateBound(new XYZ( panW/2, panD/2,0),new XYZ(-panW/2, panD/2,0)));
    pl.Append(Line.CreateBound(new XYZ(-panW/2, panD/2,0),new XYZ(-panW/2,-panD/2,0)));
    panProf.Append(pl);
    familyDoc.FamilyCreate.NewExtrusion(true, panProf, spZ, panThk);

    // Void holes
    double startX = -(nHoles - 1) * pitch / 2;
    double startY = -(nHoles - 1) * pitch / 2;

    for (int r = 0; r < nHoles; r++)
    {{
        for (int c = 0; c < nHoles; c++)
        {{
            double cx = startX + c * pitch;
            double cy = startY + r * pitch;

            CurveArray holeLoop = new CurveArray();
            for (int s = 0; s < segs; s++)
            {{
                double a0 = 2 * Math.PI * s / segs;
                double a1 = 2 * Math.PI * (s + 1) / segs;
                holeLoop.Append(Line.CreateBound(
                    new XYZ(cx + holeR*Math.Cos(a0), cy + holeR*Math.Sin(a0), 0),
                    new XYZ(cx + holeR*Math.Cos(a1), cy + holeR*Math.Sin(a1), 0)));
            }}
            CurveArrArray holeProf = new CurveArrArray();
            holeProf.Append(holeLoop);
            // isSolid=false creates void
            familyDoc.FamilyCreate.NewExtrusion(false, holeProf, spZ, panThk);
        }}
    }}

    tx.Commit();
}}""",
        ))

        # Slot cuts in a structural member
        samples.append(_s(
            "Create a structural beam family with horizontal rectangular slot cuts for web openings",
            f"""\
using Autodesk.Revit.DB;

// Beam with web slots: 200x400mm profile 3000mm long; 3 rectangular slot voids 100x200mm
using (Transaction tx = new Transaction(familyDoc, "Create Beam With Slots"))
{{
    tx.Start();

    double bW  = {_ft(200)};   // 200 mm flange width
    double bH  = {_ft(400)};   // 400 mm section height
    double bL  = {_ft(3000)};  // 3000 mm beam length
    double sW  = {_ft(100)};   // slot width
    double sH  = {_ft(200)};   // slot height
    int    nSlots = 3;

    SketchPlane spY = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    // Solid beam extrusion along Y axis
    CurveArrArray beamProf = new CurveArrArray();
    CurveArray bl = new CurveArray();
    bl.Append(Line.CreateBound(new XYZ(-bW/2,0,0),    new XYZ( bW/2,0,0)));
    bl.Append(Line.CreateBound(new XYZ( bW/2,0,0),    new XYZ( bW/2,0,bH)));
    bl.Append(Line.CreateBound(new XYZ( bW/2,0,bH),   new XYZ(-bW/2,0,bH)));
    bl.Append(Line.CreateBound(new XYZ(-bW/2,0,bH),   new XYZ(-bW/2,0,0)));
    beamProf.Append(bl);
    familyDoc.FamilyCreate.NewExtrusion(true, beamProf, spY, bL);

    // Void slots at evenly spaced Y positions
    double slotCenterZ = bH / 2;
    double yStep = bL / (nSlots + 1);

    for (int i = 1; i <= nSlots; i++)
    {{
        double yCtr = -bL/2 + i * yStep;

        // Void profile in XZ plane at Y = yCtr
        SketchPlane spSlot = SketchPlane.Create(familyDoc,
            Plane.CreateByNormalAndOrigin(XYZ.BasisY, new XYZ(0, yCtr, 0)));

        CurveArrArray slotProf = new CurveArrArray();
        CurveArray sl = new CurveArray();
        sl.Append(Line.CreateBound(new XYZ(-sW/2, yCtr, slotCenterZ-sH/2),
                                   new XYZ( sW/2, yCtr, slotCenterZ-sH/2)));
        sl.Append(Line.CreateBound(new XYZ( sW/2, yCtr, slotCenterZ-sH/2),
                                   new XYZ( sW/2, yCtr, slotCenterZ+sH/2)));
        sl.Append(Line.CreateBound(new XYZ( sW/2, yCtr, slotCenterZ+sH/2),
                                   new XYZ(-sW/2, yCtr, slotCenterZ+sH/2)));
        sl.Append(Line.CreateBound(new XYZ(-sW/2, yCtr, slotCenterZ+sH/2),
                                   new XYZ(-sW/2, yCtr, slotCenterZ-sH/2)));
        slotProf.Append(sl);
        familyDoc.FamilyCreate.NewExtrusion(false, slotProf, spSlot, bW);
    }}

    tx.Commit();
}}""",
        ))

        # Hollow cylindrical void in a solid block
        samples.append(_s(
            "Create a void cylinder cut through the center of a solid rectangular block to form a tube shape",
            f"""\
using Autodesk.Revit.DB;
using System;

// Hollow tube: solid 300x300mm square block 500mm tall with 200mm diameter void bore
using (Transaction tx = new Transaction(familyDoc, "Create Hollow Tube"))
{{
    tx.Start();

    double blockSz = {_ft(300)};  // 300 mm
    double blockH  = {_ft(500)};  // 500 mm
    double voidR   = {_ft(100)};  // 100 mm (200mm dia bore)
    int    segs    = 24;

    SketchPlane spZ = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // Outer solid block
    CurveArrArray blockProf = new CurveArrArray();
    CurveArray bl = new CurveArray();
    bl.Append(Line.CreateBound(new XYZ(-blockSz/2,-blockSz/2,0),new XYZ( blockSz/2,-blockSz/2,0)));
    bl.Append(Line.CreateBound(new XYZ( blockSz/2,-blockSz/2,0),new XYZ( blockSz/2, blockSz/2,0)));
    bl.Append(Line.CreateBound(new XYZ( blockSz/2, blockSz/2,0),new XYZ(-blockSz/2, blockSz/2,0)));
    bl.Append(Line.CreateBound(new XYZ(-blockSz/2, blockSz/2,0),new XYZ(-blockSz/2,-blockSz/2,0)));
    blockProf.Append(bl);
    familyDoc.FamilyCreate.NewExtrusion(true, blockProf, spZ, blockH);

    // Void cylinder along Z axis
    CurveArray voidLoop = new CurveArray();
    for (int s = 0; s < segs; s++)
    {{
        double a0 = 2 * Math.PI * s / segs;
        double a1 = 2 * Math.PI * (s + 1) / segs;
        voidLoop.Append(Line.CreateBound(
            new XYZ(voidR * Math.Cos(a0), voidR * Math.Sin(a0), 0),
            new XYZ(voidR * Math.Cos(a1), voidR * Math.Sin(a1), 0)));
    }}
    CurveArrArray voidProf = new CurveArrArray();
    voidProf.Append(voidLoop);
    familyDoc.FamilyCreate.NewExtrusion(false, voidProf, spZ, blockH);

    tx.Commit();
}}""",
        ))

        # Keyway slot
        samples.append(_s(
            "Create a shaft family with a rectangular keyway slot void cut along its length",
            f"""\
using Autodesk.Revit.DB;
using System;

// Shaft with keyway: 50mm radius cylinder 300mm long, 10x6mm keyway void
using (Transaction tx = new Transaction(familyDoc, "Create Keyed Shaft"))
{{
    tx.Start();

    double shaftR  = {_ft(50)};   // 50 mm shaft radius
    double shaftL  = {_ft(300)};  // 300 mm length
    double keyW    = {_ft(10)};   // 10 mm keyway width
    double keyH    = {_ft(6)};    // 6 mm keyway depth
    int    segs    = 24;

    SketchPlane spZ = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // Shaft body (cylinder)
    CurveArray shaftLoop = new CurveArray();
    for (int s = 0; s < segs; s++)
    {{
        double a0 = 2 * Math.PI * s / segs;
        double a1 = 2 * Math.PI * (s + 1) / segs;
        shaftLoop.Append(Line.CreateBound(
            new XYZ(shaftR*Math.Cos(a0), shaftR*Math.Sin(a0), 0),
            new XYZ(shaftR*Math.Cos(a1), shaftR*Math.Sin(a1), 0)));
    }}
    CurveArrArray shaftProf = new CurveArrArray();
    shaftProf.Append(shaftLoop);
    familyDoc.FamilyCreate.NewExtrusion(true, shaftProf, spZ, shaftL);

    // Keyway void: rectangular slot at top of shaft (Y = shaftR upward)
    // Void profile in XY plane; extruded along Z (shaft axis)
    double keyStartY = shaftR - keyH;
    CurveArray keyLoop = new CurveArray();
    keyLoop.Append(Line.CreateBound(new XYZ(-keyW/2, keyStartY,     0),
                                    new XYZ( keyW/2, keyStartY,     0)));
    keyLoop.Append(Line.CreateBound(new XYZ( keyW/2, keyStartY,     0),
                                    new XYZ( keyW/2, shaftR + keyH, 0)));
    keyLoop.Append(Line.CreateBound(new XYZ( keyW/2, shaftR + keyH, 0),
                                    new XYZ(-keyW/2, shaftR + keyH, 0)));
    keyLoop.Append(Line.CreateBound(new XYZ(-keyW/2, shaftR + keyH, 0),
                                    new XYZ(-keyW/2, keyStartY,     0)));
    CurveArrArray keyProf = new CurveArrArray();
    keyProf.Append(keyLoop);
    familyDoc.FamilyCreate.NewExtrusion(false, keyProf, spZ, shaftL);

    tx.Commit();
}}""",
        ))

        # Angled chamfer void
        samples.append(_s(
            "Cut a 45-degree chamfer void on all four top edges of a rectangular block",
            f"""\
using Autodesk.Revit.DB;

// 45-degree edge chamfer on a 300x300x200mm block using four triangular void extrusions
using (Transaction tx = new Transaction(familyDoc, "Create Chamfered Block"))
{{
    tx.Start();

    double W = {_ft(300)};  // 300 mm
    double D = {_ft(300)};  // 300 mm
    double H = {_ft(200)};  // 200 mm
    double C = {_ft(20)};   // 20 mm chamfer

    SketchPlane spZ = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // Main solid block
    CurveArrArray blockProf = new CurveArrArray();
    CurveArray bl = new CurveArray();
    bl.Append(Line.CreateBound(new XYZ(-W/2,-D/2,0),new XYZ( W/2,-D/2,0)));
    bl.Append(Line.CreateBound(new XYZ( W/2,-D/2,0),new XYZ( W/2, D/2,0)));
    bl.Append(Line.CreateBound(new XYZ( W/2, D/2,0),new XYZ(-W/2, D/2,0)));
    bl.Append(Line.CreateBound(new XYZ(-W/2, D/2,0),new XYZ(-W/2,-D/2,0)));
    blockProf.Append(bl);
    familyDoc.FamilyCreate.NewExtrusion(true, blockProf, spZ, H);

    // Front edge chamfer void (Y = -D/2): triangular profile in XZ plane
    SketchPlane spFront = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, new XYZ(0, -D/2 - C/2, 0)));

    // Triangle: at top of block, height C, width C (45deg)
    CurveArrArray chamProf = new CurveArrArray();
    CurveArray chamL = new CurveArray();
    double topZ = H;
    double yEdge = -D/2;
    chamL.Append(Line.CreateBound(new XYZ(-W/2,     yEdge, topZ),     new XYZ(W/2,      yEdge, topZ)));
    chamL.Append(Line.CreateBound(new XYZ( W/2,     yEdge, topZ),     new XYZ(W/2,      yEdge - C, topZ)));
    chamL.Append(Line.CreateBound(new XYZ( W/2,     yEdge - C, topZ), new XYZ(-W/2,     yEdge - C, topZ)));
    chamL.Append(Line.CreateBound(new XYZ(-W/2,     yEdge - C, topZ), new XYZ(-W/2,     yEdge, topZ)));
    chamProf.Append(chamL);

    // Extrude void in Z direction (downward -C)
    SketchPlane spTopCham = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, new XYZ(0, 0, H)));
    CurveArrArray topChamProf = new CurveArrArray();
    CurveArray tcl = new CurveArray();
    tcl.Append(Line.CreateBound(new XYZ(-W/2,   -D/2,    H), new XYZ( W/2,   -D/2,    H)));
    tcl.Append(Line.CreateBound(new XYZ( W/2,   -D/2,    H), new XYZ( W/2,   -D/2+C,  H)));
    tcl.Append(Line.CreateBound(new XYZ( W/2,   -D/2+C,  H), new XYZ(-W/2,   -D/2+C,  H)));
    tcl.Append(Line.CreateBound(new XYZ(-W/2,   -D/2+C,  H), new XYZ(-W/2,   -D/2,    H)));
    topChamProf.Append(tcl);
    Extrusion chamVoid = familyDoc.FamilyCreate.NewExtrusion(false, topChamProf, spTopCham, C);
    chamVoid.StartOffset = -C;

    tx.Commit();
}}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # 6. Swept blend forms
    # ------------------------------------------------------------------

    def _swept_blend_forms(self) -> List[SAMPLE]:
        samples = []

        # Tapered handrail
        samples.append(_s(
            "Create a swept blend form for a tapered handrail that transitions from a round to an oval cross-section",
            f"""\
using Autodesk.Revit.DB;
using System;

// SweptBlend: circular bottom profile transitions to oval top over 1200mm path
using (Transaction tx = new Transaction(familyDoc, "Create Tapered Handrail"))
{{
    tx.Start();

    double pathLen = {_ft(1200)}; // 1200 mm path length
    double r1      = {_ft(25)};   // 25 mm start radius (circle)
    double r2x     = {_ft(30)};   // 30 mm end X radius (oval)
    double r2y     = {_ft(15)};   // 15 mm end Y radius (oval)
    int    segs    = 16;

    // Sweep path: straight line along X
    CurveArray pathCurve = new CurveArray();
    pathCurve.Append(Line.CreateBound(XYZ.Zero, new XYZ(pathLen, 0, 0)));

    SketchPlane pathPlane = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    ModelCurveArray pathLines = familyDoc.FamilyCreate.NewModelCurveArray(pathCurve, pathPlane);
    ReferenceArray pathRefs = new ReferenceArray();
    foreach (ModelCurve mc in pathLines)
        pathRefs.Append(mc.GeometryCurve.Reference);

    // Start profile: circle (at X=0, in YZ plane)
    CurveArray startLoop = new CurveArray();
    XYZ prevS = new XYZ(0, r1, 0);
    for (int i = 1; i <= segs; i++)
    {{
        double a = 2 * Math.PI * i / segs;
        XYZ curS = new XYZ(0, r1 * Math.Cos(a), r1 * Math.Sin(a));
        startLoop.Append(Line.CreateBound(prevS, curS));
        prevS = curS;
    }}

    // End profile: oval (at X=pathLen, in YZ plane)
    CurveArray endLoop = new CurveArray();
    XYZ prevE = new XYZ(pathLen, r2x, 0);
    for (int i = 1; i <= segs; i++)
    {{
        double a = 2 * Math.PI * i / segs;
        XYZ curE = new XYZ(pathLen, r2x * Math.Cos(a), r2y * Math.Sin(a));
        endLoop.Append(Line.CreateBound(prevE, curE));
        prevE = curE;
    }}

    SweptBlend sb = familyDoc.FamilyCreate.NewSweptBlend(
        true,          // isSolid
        pathRefs,      // path
        null,          // profile plane (null = auto)
        new SweepProfile(startLoop),
        new SweepProfile(endLoop));

    tx.Commit();
}}""",
        ))

        # Column capital transition
        samples.append(_s(
            "Create a swept blend for a column capital that widens from a 150mm square base to a 400mm square top over 200mm",
            f"""\
using Autodesk.Revit.DB;

// Column capital: NewSweptBlend with short vertical path, small-to-large rectangle
using (Transaction tx = new Transaction(familyDoc, "Create Column Capital"))
{{
    tx.Start();

    double pathH = {_ft(200)};  // 200 mm height
    double bot   = {_ft(150)};  // 150 mm bottom square side
    double top   = {_ft(400)};  // 400 mm top square side

    // Vertical path (Z axis)
    CurveArray pathCurve = new CurveArray();
    pathCurve.Append(Line.CreateBound(XYZ.Zero, new XYZ(0, 0, pathH)));
    SketchPlane pathPlane = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero));
    ModelCurveArray pathLines = familyDoc.FamilyCreate.NewModelCurveArray(pathCurve, pathPlane);
    ReferenceArray pathRefs = new ReferenceArray();
    foreach (ModelCurve mc in pathLines) pathRefs.Append(mc.GeometryCurve.Reference);

    // Bottom profile (150x150 square at z=0, in XY plane)
    CurveArray botLoop = new CurveArray();
    botLoop.Append(Line.CreateBound(new XYZ(-bot/2,-bot/2,0),new XYZ( bot/2,-bot/2,0)));
    botLoop.Append(Line.CreateBound(new XYZ( bot/2,-bot/2,0),new XYZ( bot/2, bot/2,0)));
    botLoop.Append(Line.CreateBound(new XYZ( bot/2, bot/2,0),new XYZ(-bot/2, bot/2,0)));
    botLoop.Append(Line.CreateBound(new XYZ(-bot/2, bot/2,0),new XYZ(-bot/2,-bot/2,0)));

    // Top profile (400x400 square at z=pathH)
    CurveArray topLoop = new CurveArray();
    topLoop.Append(Line.CreateBound(new XYZ(-top/2,-top/2,pathH),new XYZ( top/2,-top/2,pathH)));
    topLoop.Append(Line.CreateBound(new XYZ( top/2,-top/2,pathH),new XYZ( top/2, top/2,pathH)));
    topLoop.Append(Line.CreateBound(new XYZ( top/2, top/2,pathH),new XYZ(-top/2, top/2,pathH)));
    topLoop.Append(Line.CreateBound(new XYZ(-top/2, top/2,pathH),new XYZ(-top/2,-top/2,pathH)));

    familyDoc.FamilyCreate.NewSweptBlend(
        true, pathRefs, null,
        new SweepProfile(botLoop),
        new SweepProfile(topLoop));

    tx.Commit();
}}""",
        ))

        # Duct transition
        samples.append(_s(
            "Create a duct transition swept blend that morphs from a 400x300mm rectangle to a 300mm diameter circle over 500mm",
            f"""\
using Autodesk.Revit.DB;
using System;

// Duct transition: rectangular to circular cross-section
using (Transaction tx = new Transaction(familyDoc, "Create Duct Transition"))
{{
    tx.Start();

    double pathLen = {_ft(500)};  // 500 mm transition length
    double rW      = {_ft(400)};  // rectangular width
    double rD      = {_ft(300)};  // rectangular depth
    double circR   = {_ft(150)}; // circular radius (300mm dia)
    int    segs    = 16;

    // Horizontal path along X
    CurveArray pathCurve = new CurveArray();
    pathCurve.Append(Line.CreateBound(XYZ.Zero, new XYZ(pathLen, 0, 0)));
    SketchPlane pathPlane = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    ModelCurveArray pathLines = familyDoc.FamilyCreate.NewModelCurveArray(pathCurve, pathPlane);
    ReferenceArray pathRefs = new ReferenceArray();
    foreach (ModelCurve mc in pathLines) pathRefs.Append(mc.GeometryCurve.Reference);

    // Start profile: 400x300 rectangle in YZ plane at X=0
    CurveArray startLoop = new CurveArray();
    startLoop.Append(Line.CreateBound(new XYZ(0,-rW/2,-rD/2),new XYZ(0, rW/2,-rD/2)));
    startLoop.Append(Line.CreateBound(new XYZ(0, rW/2,-rD/2),new XYZ(0, rW/2, rD/2)));
    startLoop.Append(Line.CreateBound(new XYZ(0, rW/2, rD/2),new XYZ(0,-rW/2, rD/2)));
    startLoop.Append(Line.CreateBound(new XYZ(0,-rW/2, rD/2),new XYZ(0,-rW/2,-rD/2)));

    // End profile: circle in YZ plane at X=pathLen
    CurveArray endLoop = new CurveArray();
    XYZ prevE = new XYZ(pathLen, circR, 0);
    for (int i = 1; i <= segs; i++)
    {{
        double a = 2 * Math.PI * i / segs;
        XYZ curE = new XYZ(pathLen, circR * Math.Cos(a), circR * Math.Sin(a));
        endLoop.Append(Line.CreateBound(prevE, curE));
        prevE = curE;
    }}

    familyDoc.FamilyCreate.NewSweptBlend(
        true, pathRefs, null,
        new SweepProfile(startLoop),
        new SweepProfile(endLoop));

    tx.Commit();
}}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # 7. Multi-material families
    # ------------------------------------------------------------------

    def _multi_material_families(self) -> List[SAMPLE]:
        samples = []

        # Composite panel: core + two face skins with different materials
        samples.append(_s(
            "Create a composite sandwich panel family with three extrusions assigned to different subcategories and materials",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

// Composite panel: steel face + insulation core + steel face, each as separate extrusion
// with distinct subcategories and material parameters
FamilyManager famMgr = familyDoc.FamilyManager;

// Material parameters per layer
FamilyParameter pFaceMat = famMgr.AddParameter("FaceMaterial",
    BuiltInParameterGroup.PG_MATERIALS, ParameterType.Material, true);
FamilyParameter pCoreMat = famMgr.AddParameter("CoreMaterial",
    BuiltInParameterGroup.PG_MATERIALS, ParameterType.Material, true);

using (Transaction tx = new Transaction(familyDoc, "Create Composite Panel"))
{{
    tx.Start();

    double W      = {_ft(1200)}; // 1200 mm
    double H      = {_ft(600)};  // 600 mm
    double faceT  = {_ft(2)};    // 2 mm steel face
    double coreT  = {_ft(50)};   // 50 mm insulation core

    SketchPlane spZ = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // Create subcategories for each layer
    Category famCat = familyDoc.OwnerFamily.FamilyCategory;
    CategoryNameMap subCats = famCat.SubCategories;

    Category faceSubCat = subCats.Contains("FaceLayer")
        ? subCats.get_Item("FaceLayer")
        : familyDoc.Settings.Categories.NewSubcategory(famCat, "FaceLayer");
    Category coreSubCat = subCats.Contains("CoreLayer")
        ? subCats.get_Item("CoreLayer")
        : familyDoc.Settings.Categories.NewSubcategory(famCat, "CoreLayer");

    // Bottom face skin
    double z0 = 0;
    CurveArrArray f1Prof = new CurveArrArray();
    CurveArray f1l = new CurveArray();
    f1l.Append(Line.CreateBound(new XYZ(-W/2,0,z0),new XYZ(W/2,0,z0)));
    f1l.Append(Line.CreateBound(new XYZ(W/2,0,z0),new XYZ(W/2,H,z0)));
    f1l.Append(Line.CreateBound(new XYZ(W/2,H,z0),new XYZ(-W/2,H,z0)));
    f1l.Append(Line.CreateBound(new XYZ(-W/2,H,z0),new XYZ(-W/2,0,z0)));
    f1Prof.Append(f1l);
    Extrusion face1 = familyDoc.FamilyCreate.NewExtrusion(true, f1Prof, spZ, faceT);
    face1.Subcategory = faceSubCat;

    // Core insulation
    double z1 = faceT;
    SketchPlane spCore = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, new XYZ(0,0,z1)));
    CurveArrArray cProf = new CurveArrArray();
    CurveArray cl = new CurveArray();
    cl.Append(Line.CreateBound(new XYZ(-W/2,0,z1),new XYZ(W/2,0,z1)));
    cl.Append(Line.CreateBound(new XYZ(W/2,0,z1),new XYZ(W/2,H,z1)));
    cl.Append(Line.CreateBound(new XYZ(W/2,H,z1),new XYZ(-W/2,H,z1)));
    cl.Append(Line.CreateBound(new XYZ(-W/2,H,z1),new XYZ(-W/2,0,z1)));
    cProf.Append(cl);
    Extrusion core = familyDoc.FamilyCreate.NewExtrusion(true, cProf, spCore, coreT);
    core.Subcategory = coreSubCat;

    // Top face skin
    double z2 = faceT + coreT;
    SketchPlane spFace2 = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, new XYZ(0,0,z2)));
    CurveArrArray f2Prof = new CurveArrArray();
    CurveArray f2l = new CurveArray();
    f2l.Append(Line.CreateBound(new XYZ(-W/2,0,z2),new XYZ(W/2,0,z2)));
    f2l.Append(Line.CreateBound(new XYZ(W/2,0,z2),new XYZ(W/2,H,z2)));
    f2l.Append(Line.CreateBound(new XYZ(W/2,H,z2),new XYZ(-W/2,H,z2)));
    f2l.Append(Line.CreateBound(new XYZ(-W/2,H,z2),new XYZ(-W/2,0,z2)));
    f2Prof.Append(f2l);
    Extrusion face2 = familyDoc.FamilyCreate.NewExtrusion(true, f2Prof, spFace2, faceT);
    face2.Subcategory = faceSubCat;

    // Assign materials via parameters
    Material steelMat = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Material)).Cast<Material>()
        .FirstOrDefault(m => m.Name.Contains("Steel"));
    Material insMat = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Material)).Cast<Material>()
        .FirstOrDefault(m => m.Name.Contains("Insulation"));

    if (steelMat != null) famMgr.Set(pFaceMat, steelMat.Id);
    if (insMat   != null) famMgr.Set(pCoreMat, insMat.Id);

    tx.Commit();
}}""",
        ))

        # Door family: frame + panel + glass with separate material params
        samples.append(_s(
            "Create a door family with frame, panel, and glazing extrusions each assigned separate material parameters",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

// Door: 900x2100mm; 75mm frame; lower solid panel; upper glazing
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pFrameMat  = famMgr.AddParameter("FrameMaterial",
    BuiltInParameterGroup.PG_MATERIALS, ParameterType.Material, true);
FamilyParameter pPanelMat  = famMgr.AddParameter("PanelMaterial",
    BuiltInParameterGroup.PG_MATERIALS, ParameterType.Material, true);
FamilyParameter pGlassMat  = famMgr.AddParameter("GlazingMaterial",
    BuiltInParameterGroup.PG_MATERIALS, ParameterType.Material, true);

using (Transaction tx = new Transaction(familyDoc, "Create Door"))
{{
    tx.Start();

    double RW   = {_ft(900)};   // rough opening width
    double RH   = {_ft(2100)};  // rough opening height
    double FrW  = {_ft(75)};    // frame width
    double FrD  = {_ft(100)};   // frame depth
    double panH = {_ft(1000)};  // lower solid panel height
    double thk  = {_ft(45)};    // door thickness

    SketchPlane spY = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    // Frame (hollow profile = outer - inner loop)
    CurveArrArray frameProf = new CurveArrArray();
    CurveArray outerF = new CurveArray();
    outerF.Append(Line.CreateBound(new XYZ(-RW/2,0,0),   new XYZ(RW/2,0,0)));
    outerF.Append(Line.CreateBound(new XYZ(RW/2,0,0),    new XYZ(RW/2,0,RH)));
    outerF.Append(Line.CreateBound(new XYZ(RW/2,0,RH),   new XYZ(-RW/2,0,RH)));
    outerF.Append(Line.CreateBound(new XYZ(-RW/2,0,RH),  new XYZ(-RW/2,0,0)));
    frameProf.Append(outerF);
    CurveArray innerF = new CurveArray();
    double iX = RW/2-FrW, iH = RH-FrW;
    innerF.Append(Line.CreateBound(new XYZ(-iX,0,FrW),new XYZ(iX,0,FrW)));
    innerF.Append(Line.CreateBound(new XYZ(iX,0,FrW),new XYZ(iX,0,iH)));
    innerF.Append(Line.CreateBound(new XYZ(iX,0,iH),new XYZ(-iX,0,iH)));
    innerF.Append(Line.CreateBound(new XYZ(-iX,0,iH),new XYZ(-iX,0,FrW)));
    frameProf.Append(innerF);
    Extrusion frame = familyDoc.FamilyCreate.NewExtrusion(true, frameProf, spY, FrD);

    // Lower solid panel (from FrW to panH)
    double panW = RW - 2*FrW;
    SketchPlane spPanel = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, new XYZ(0, FrD*0.1, 0)));
    CurveArrArray panProf = new CurveArrArray();
    CurveArray pl = new CurveArray();
    double pz0 = FrW, pz1 = FrW + panH;
    pl.Append(Line.CreateBound(new XYZ(-panW/2,FrD*0.1,pz0),new XYZ(panW/2,FrD*0.1,pz0)));
    pl.Append(Line.CreateBound(new XYZ(panW/2,FrD*0.1,pz0),new XYZ(panW/2,FrD*0.1,pz1)));
    pl.Append(Line.CreateBound(new XYZ(panW/2,FrD*0.1,pz1),new XYZ(-panW/2,FrD*0.1,pz1)));
    pl.Append(Line.CreateBound(new XYZ(-panW/2,FrD*0.1,pz1),new XYZ(-panW/2,FrD*0.1,pz0)));
    panProf.Append(pl);
    Extrusion panel = familyDoc.FamilyCreate.NewExtrusion(true, panProf, spPanel, thk);

    // Upper glazing
    double gz0 = FrW + panH + {_ft(20)};
    double gz1 = RH - FrW;
    SketchPlane spGlass = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, new XYZ(0, FrD*0.4, 0)));
    CurveArrArray gProf = new CurveArrArray();
    CurveArray gl = new CurveArray();
    gl.Append(Line.CreateBound(new XYZ(-panW/2,FrD*0.4,gz0),new XYZ(panW/2,FrD*0.4,gz0)));
    gl.Append(Line.CreateBound(new XYZ(panW/2,FrD*0.4,gz0),new XYZ(panW/2,FrD*0.4,gz1)));
    gl.Append(Line.CreateBound(new XYZ(panW/2,FrD*0.4,gz1),new XYZ(-panW/2,FrD*0.4,gz1)));
    gl.Append(Line.CreateBound(new XYZ(-panW/2,FrD*0.4,gz1),new XYZ(-panW/2,FrD*0.4,gz0)));
    gProf.Append(gl);
    Extrusion glazing = familyDoc.FamilyCreate.NewExtrusion(true, gProf, spGlass, {_ft(6)});

    // Assign materials to each extrusion parameter
    void AssignMat(Extrusion ext, FamilyParameter matParam)
    {{
        Parameter mp = ext.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM);
        if (mp != null && !mp.IsReadOnly)
            famMgr.AssociateElementParameterToFamilyParameter(mp, matParam);
    }}
    AssignMat(frame,   pFrameMat);
    AssignMat(panel,   pPanelMat);
    AssignMat(glazing, pGlassMat);

    tx.Commit();
}}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # 8. Nested family workflows
    # ------------------------------------------------------------------

    def _nested_family_workflows(self) -> List[SAMPLE]:
        samples = []

        # Load and place nested family at multiple positions
        samples.append(_s(
            "Load a nested bolt family and place four instances at corner positions in a base plate family",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

// Load nested bolt family and place 4 instances at base plate corners
using (Transaction tx = new Transaction(familyDoc, "Place Nested Bolts"))
{{
    tx.Start();

    double plateW = {_ft(300)};  // 300 mm base plate
    double offset = {_ft(30)};   // 30 mm bolt inset from edge
    double boltX  = plateW/2 - offset;
    double boltY  = plateW/2 - offset;

    // Load nested family
    string boltPath = @"C:\\ProgramData\\Autodesk\\RVT 2026\\Libraries\\US Imperial\\Structural\\Connections\\Bolts\\Hex Bolt.rfa";
    Family boltFamily;
    bool loaded = familyDoc.LoadFamily(boltPath, out boltFamily);

    if (!loaded)
    {{
        boltFamily = new FilteredElementCollector(familyDoc)
            .OfClass(typeof(Family)).Cast<Family>()
            .FirstOrDefault(f => f.Name.Contains("Hex Bolt"));
    }}

    if (boltFamily != null)
    {{
        FamilySymbol boltSymbol = familyDoc.GetElement(
            boltFamily.GetFamilySymbolIds().First()) as FamilySymbol;
        if (!boltSymbol.IsActive) boltSymbol.Activate();

        // Four corner positions
        XYZ[] boltPts = new XYZ[]
        {{
            new XYZ(-boltX, -boltY, 0),
            new XYZ( boltX, -boltY, 0),
            new XYZ( boltX,  boltY, 0),
            new XYZ(-boltX,  boltY, 0),
        }};

        foreach (XYZ pt in boltPts)
        {{
            familyDoc.FamilyCreate.NewFamilyInstance(
                pt, boltSymbol, familyDoc.ActiveView);
        }}
    }}

    tx.Commit();
}}""",
        ))

        # Shared parameter mapping between host and nested
        samples.append(_s(
            "Map a shared parameter from a nested family to the host family so the parameter is exposed in the project",
            """\
using Autodesk.Revit.DB;
using System.Linq;

// Shared parameter mapping: host family exposes nested family's 'BoltDiameter' as shared param
// Step 1: Load shared parameter file
Application app = familyDoc.Application;
DefinitionFile sharedParamFile = app.OpenSharedParameterFile();
// (Assumes shared parameter file is already set in app.SharedParametersFilename)

DefinitionGroup grp = sharedParamFile.Groups.get_Item("Structural")
    ?? sharedParamFile.Groups.Create("Structural");

ExternalDefinitionCreationOptions opts = new ExternalDefinitionCreationOptions(
    "BoltDiameter", SpecTypeId.Length);
ExternalDefinition extDef = grp.Definitions.Contains("BoltDiameter")
    ? (ExternalDefinition)grp.Definitions.get_Item("BoltDiameter")
    : (ExternalDefinition)grp.Definitions.Create(opts);

// Step 2: Add as shared parameter in host family
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter hostParam = famMgr.AddParameter(
    extDef,
    BuiltInParameterGroup.PG_GEOMETRY,
    false); // type parameter

// Step 3: Get nested family instance and map its parameter
FamilyInstance nestedInst = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(FamilyInstance)).Cast<FamilyInstance>()
    .FirstOrDefault(fi => fi.Symbol.Family.Name.Contains("Bolt"));

if (nestedInst != null)
{
    Parameter nestedParam = nestedInst.LookupParameter("BoltDiameter");
    if (nestedParam != null)
        famMgr.AssociateElementParameterToFamilyParameter(nestedParam, hostParam);
}""",
        ))

        # Iterating nested instances and adjusting positions
        samples.append(_s(
            "Iterate all nested family instances in the host family and move them to new positions using ElementTransformUtils",
            f"""\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

// Reposition all nested family instances within the host family document
using (Transaction tx = new Transaction(familyDoc, "Reposition Nested Instances"))
{{
    tx.Start();

    List<FamilyInstance> nestedInstances = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(FamilyInstance))
        .Cast<FamilyInstance>()
        .ToList();

    double offsetZ = {_ft(50)};  // Shift all nested instances up 50 mm

    foreach (FamilyInstance fi in nestedInstances)
    {{
        // Move each instance by the Z offset vector
        XYZ moveVec = new XYZ(0, 0, offsetZ);
        ElementTransformUtils.MoveElement(familyDoc, fi.Id, moveVec);
    }}

    tx.Commit();
}}""",
        ))

        # Nested family with type-driven parameter
        samples.append(_s(
            "Load a nested family and activate a specific type by name to control the nested component's size",
            """\
using Autodesk.Revit.DB;
using System.Linq;

// Load nested family, pick specific type by name (e.g., 'M20' bolt type)
using (Transaction tx = new Transaction(familyDoc, "Set Nested Family Type"))
{
    tx.Start();

    // Assume nested family already loaded
    Family nestedFamily = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Family)).Cast<Family>()
        .FirstOrDefault(f => f.Name.Contains("Hex Bolt"));

    if (nestedFamily != null)
    {
        // Find the M20 type
        FamilySymbol m20Type = nestedFamily.GetFamilySymbolIds()
            .Select(id => familyDoc.GetElement(id) as FamilySymbol)
            .FirstOrDefault(sym => sym?.Name == "M20");

        if (m20Type != null)
        {
            if (!m20Type.IsActive) m20Type.Activate();

            // Change type of existing nested instance
            FamilyInstance nestedInst = new FilteredElementCollector(familyDoc)
                .OfClass(typeof(FamilyInstance)).Cast<FamilyInstance>()
                .FirstOrDefault(fi => fi.Symbol.Family.Id == nestedFamily.Id);

            if (nestedInst != null)
                nestedInst.Symbol = m20Type;
        }
    }

    tx.Commit();
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # 9. Complex profiles
    # ------------------------------------------------------------------

    def _complex_profiles(self) -> List[SAMPLE]:
        samples = []

        # T-section beam
        samples.append(_s(
            "Create a T-section structural beam extrusion with a 200x20mm flange and 150x15mm web",
            f"""\
using Autodesk.Revit.DB;

// T-section: 200mm wide flange 20mm thick on top of 150mm web 15mm thick, total height 170mm
// Lengths in feet. 2000mm extrusion depth.
using (Transaction tx = new Transaction(familyDoc, "Create T-Section Beam"))
{{
    tx.Start();

    double fW  = {_ft(200)};  // flange width 200 mm
    double fT  = {_ft(20)};   // flange thickness 20 mm
    double wH  = {_ft(150)};  // web height 150 mm
    double wT  = {_ft(15)};   // web thickness 15 mm
    double len = {_ft(2000)}; // extrusion length

    // T profile built from an L-shaped polygon (counterclockwise)
    // Origin at bottom-center of web
    CurveArray tLoop = new CurveArray();
    // Web left, up
    tLoop.Append(Line.CreateBound(new XYZ(-wT/2, 0, 0),   new XYZ(-wT/2, 0, wH)));
    // Flange bottom left
    tLoop.Append(Line.CreateBound(new XYZ(-wT/2, 0, wH),  new XYZ(-fW/2, 0, wH)));
    // Flange top left to right
    tLoop.Append(Line.CreateBound(new XYZ(-fW/2, 0, wH),  new XYZ(-fW/2, 0, wH+fT)));
    tLoop.Append(Line.CreateBound(new XYZ(-fW/2, 0, wH+fT), new XYZ(fW/2, 0, wH+fT)));
    tLoop.Append(Line.CreateBound(new XYZ(fW/2, 0, wH+fT), new XYZ(fW/2, 0, wH)));
    // Flange bottom right
    tLoop.Append(Line.CreateBound(new XYZ(fW/2, 0, wH),   new XYZ(wT/2, 0, wH)));
    // Web right down
    tLoop.Append(Line.CreateBound(new XYZ(wT/2, 0, wH),   new XYZ(wT/2, 0, 0)));
    // Bottom close
    tLoop.Append(Line.CreateBound(new XYZ(wT/2, 0, 0),    new XYZ(-wT/2, 0, 0)));

    CurveArrArray tProf = new CurveArrArray();
    tProf.Append(tLoop);

    SketchPlane spY = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, tProf, spY, len);

    tx.Commit();
}}""",
        ))

        # C-channel (U-section)
        samples.append(_s(
            "Create a C-channel (U-section) structural extrusion with 150mm flange width, 200mm web height, and 12mm thickness",
            f"""\
using Autodesk.Revit.DB;

// C-channel: 150mm flanges, 200mm web height, 12mm thickness, 3000mm long
using (Transaction tx = new Transaction(familyDoc, "Create C-Channel"))
{{
    tx.Start();

    double fW  = {_ft(150)};   // flange width 150 mm
    double wH  = {_ft(200)};   // web height (total section height)
    double t   = {_ft(12)};    // thickness 12 mm
    double len = {_ft(3000)};  // length 3000 mm

    // C profile (open to the right, origin at bottom-left of web)
    CurveArray cLoop = new CurveArray();
    // Outer boundary counterclockwise
    cLoop.Append(Line.CreateBound(new XYZ(0,  0, 0),   new XYZ(fW, 0, 0)));       // bottom flange outer
    cLoop.Append(Line.CreateBound(new XYZ(fW, 0, 0),   new XYZ(fW, 0, t)));       // bottom flange tip
    cLoop.Append(Line.CreateBound(new XYZ(fW, 0, t),   new XYZ(t,  0, t)));       // bottom flange inner
    cLoop.Append(Line.CreateBound(new XYZ(t,  0, t),   new XYZ(t,  0, wH-t)));    // web inner left
    cLoop.Append(Line.CreateBound(new XYZ(t,  0, wH-t),new XYZ(fW, 0, wH-t)));    // top flange inner
    cLoop.Append(Line.CreateBound(new XYZ(fW, 0, wH-t),new XYZ(fW, 0, wH)));      // top flange tip
    cLoop.Append(Line.CreateBound(new XYZ(fW, 0, wH),  new XYZ(0,  0, wH)));      // top flange outer
    cLoop.Append(Line.CreateBound(new XYZ(0,  0, wH),  new XYZ(0,  0, 0)));       // web outer

    CurveArrArray cProf = new CurveArrArray();
    cProf.Append(cLoop);

    SketchPlane spY = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, cProf, spY, len);

    tx.Commit();
}}""",
        ))

        # Hollow rectangular section (RHS/SHS)
        samples.append(_s(
            "Create a hollow rectangular section (RHS) extrusion with 150x100mm outer dimensions and 6mm wall thickness",
            f"""\
using Autodesk.Revit.DB;

// RHS: 150x100mm outer, 6mm wall, 4000mm long; profiled as outer loop + inner void loop
using (Transaction tx = new Transaction(familyDoc, "Create RHS Extrusion"))
{{
    tx.Start();

    double oW  = {_ft(150)};  // outer width
    double oH  = {_ft(100)};  // outer height
    double t   = {_ft(6)};    // wall thickness
    double len = {_ft(4000)}; // length

    CurveArrArray rhsProf = new CurveArrArray();

    // Outer loop
    CurveArray outer = new CurveArray();
    outer.Append(Line.CreateBound(new XYZ(-oW/2,-oH/2,0),new XYZ( oW/2,-oH/2,0)));
    outer.Append(Line.CreateBound(new XYZ( oW/2,-oH/2,0),new XYZ( oW/2, oH/2,0)));
    outer.Append(Line.CreateBound(new XYZ( oW/2, oH/2,0),new XYZ(-oW/2, oH/2,0)));
    outer.Append(Line.CreateBound(new XYZ(-oW/2, oH/2,0),new XYZ(-oW/2,-oH/2,0)));
    rhsProf.Append(outer);

    // Inner (void) loop
    double iW = oW - 2*t, iH = oH - 2*t;
    CurveArray inner = new CurveArray();
    inner.Append(Line.CreateBound(new XYZ(-iW/2,-iH/2,0),new XYZ( iW/2,-iH/2,0)));
    inner.Append(Line.CreateBound(new XYZ( iW/2,-iH/2,0),new XYZ( iW/2, iH/2,0)));
    inner.Append(Line.CreateBound(new XYZ( iW/2, iH/2,0),new XYZ(-iW/2, iH/2,0)));
    inner.Append(Line.CreateBound(new XYZ(-iW/2, iH/2,0),new XYZ(-iW/2,-iH/2,0)));
    rhsProf.Append(inner);

    SketchPlane spY = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, rhsProf, spY, len);

    tx.Commit();
}}""",
        ))

        # Z-purlin profile
        samples.append(_s(
            "Create a Z-purlin cold-formed steel extrusion with 200mm web, 75mm flanges, and 20mm lips",
            f"""\
using Autodesk.Revit.DB;

// Z-purlin: 200mm web, 75mm top+bottom flanges with 20mm lips, 2mm thickness, 6000mm long
using (Transaction tx = new Transaction(familyDoc, "Create Z-Purlin"))
{{
    tx.Start();

    double wH  = {_ft(200)};  // web height
    double fW  = {_ft(75)};   // flange width
    double lip = {_ft(20)};   // lip length
    double t   = {_ft(2)};    // thickness 2 mm
    double len = {_ft(6000)}; // 6000 mm

    // Z-profile centerline (offset flanges opposite directions)
    // Bottom flange projects right; top flange projects left
    CurveArray zLoop = new CurveArray();

    // Start at bottom-right lip tip
    XYZ p0  = new XYZ(fW,      0, 0);       // bottom flange outer tip
    XYZ p1  = new XYZ(fW,      0, t);       // bottom flange outer top
    XYZ p2  = new XYZ(t,       0, t);       // bottom flange inner corner
    XYZ p3  = new XYZ(t,       0, wH-t);    // web inner top
    XYZ p4  = new XYZ(-fW+t,   0, wH-t);    // top flange inner
    XYZ p5  = new XYZ(-fW+t,   0, wH);      // top flange outer bottom
    XYZ p6  = new XYZ(-fW+t+lip,0,wH);      // top lip outer
    XYZ p7  = new XYZ(-fW+t+lip,0,wH-t);   // top lip inner
    XYZ p8  = new XYZ(-fW+2*t, 0, wH-t);   // step back
    XYZ p9  = new XYZ(-fW+2*t, 0, 0+t);
    XYZ p10 = new XYZ(fW-lip,  0, t);
    XYZ p11 = new XYZ(fW-lip,  0, 0);

    XYZ[] pts = {{ p0,p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11 }};
    for (int i = 0; i < pts.Length; i++)
        zLoop.Append(Line.CreateBound(pts[i], pts[(i+1)%pts.Length]));

    CurveArrArray zProf = new CurveArrArray();
    zProf.Append(zLoop);

    SketchPlane spY = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, zProf, spY, len);

    tx.Commit();
}}""",
        ))

        # I-beam (wide flange) profile
        samples.append(_s(
            "Create an I-beam (wide flange W200x46) extrusion with accurate flange and web dimensions",
            f"""\
using Autodesk.Revit.DB;

// W200x46: d=203mm, bf=203mm, tf=11mm, tw=7.2mm (approximate), length=6000mm
using (Transaction tx = new Transaction(familyDoc, "Create W200x46 I-Beam"))
{{
    tx.Start();

    double d   = {_ft(203)};  // section depth
    double bf  = {_ft(203)};  // flange width
    double tf  = {_ft(11)};   // flange thickness
    double tw  = {_ft(7)};    // web thickness (approx 7.2mm)
    double len = {_ft(6000)}; // 6000 mm

    // I profile (symmetric about centroid)
    // Start at bottom-left flange tip, counterclockwise
    double hw2 = d/2 - tf;  // half web height

    CurveArray iLoop = new CurveArray();
    iLoop.Append(Line.CreateBound(new XYZ(-bf/2,-d/2,0),     new XYZ(bf/2,-d/2,0)));   // bottom flange outer
    iLoop.Append(Line.CreateBound(new XYZ(bf/2,-d/2,0),      new XYZ(bf/2,-d/2+tf,0))); // bottom flange right
    iLoop.Append(Line.CreateBound(new XYZ(bf/2,-d/2+tf,0),   new XYZ(tw/2,-d/2+tf,0))); // fillet into web
    iLoop.Append(Line.CreateBound(new XYZ(tw/2,-d/2+tf,0),   new XYZ(tw/2,d/2-tf,0)));  // right web
    iLoop.Append(Line.CreateBound(new XYZ(tw/2,d/2-tf,0),    new XYZ(bf/2,d/2-tf,0)));  // top fillet
    iLoop.Append(Line.CreateBound(new XYZ(bf/2,d/2-tf,0),    new XYZ(bf/2,d/2,0)));      // top flange right
    iLoop.Append(Line.CreateBound(new XYZ(bf/2,d/2,0),       new XYZ(-bf/2,d/2,0)));     // top flange outer
    iLoop.Append(Line.CreateBound(new XYZ(-bf/2,d/2,0),      new XYZ(-bf/2,d/2-tf,0)));  // top flange left
    iLoop.Append(Line.CreateBound(new XYZ(-bf/2,d/2-tf,0),   new XYZ(-tw/2,d/2-tf,0)));  // top left fillet
    iLoop.Append(Line.CreateBound(new XYZ(-tw/2,d/2-tf,0),   new XYZ(-tw/2,-d/2+tf,0))); // left web
    iLoop.Append(Line.CreateBound(new XYZ(-tw/2,-d/2+tf,0),  new XYZ(-bf/2,-d/2+tf,0))); // bottom left fillet
    iLoop.Append(Line.CreateBound(new XYZ(-bf/2,-d/2+tf,0),  new XYZ(-bf/2,-d/2,0)));    // bottom flange left

    CurveArrArray iProf = new CurveArrArray();
    iProf.Append(iLoop);

    SketchPlane spY = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, iProf, spY, len);

    tx.Commit();
}}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # 10. Adaptive components
    # ------------------------------------------------------------------

    def _adaptive_components(self) -> List[SAMPLE]:
        samples = []

        # Two-point adaptive panel
        samples.append(_s(
            "Create a two-point adaptive component family that generates a flat panel between two adaptive points",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.PointClouds;

// Two-point adaptive component: panel spans between adaptive point 1 and point 2
// Must be created in an Adaptive Component family template
// Adaptive points are set up in the family template; accessed via AdaptiveComponentInstanceUtils

// In the adaptive family document, points are reference points
// We extrude a panel between the two placement points

using (Transaction tx = new Transaction(familyDoc, "Create Adaptive Panel"))
{{
    tx.Start();

    // Collect adaptive placement points (reference points tagged as adaptive)
    FilteredElementCollector collector = new FilteredElementCollector(familyDoc);
    IList<Element> refPoints = collector
        .OfClass(typeof(ReferencePoint))
        .ToElements();

    // Adaptive family: first two reference points are AP1 and AP2
    if (refPoints.Count >= 2)
    {{
        ReferencePoint ap1 = refPoints[0] as ReferencePoint;
        ReferencePoint ap2 = refPoints[1] as ReferencePoint;

        // Create a reference line between the two adaptive points
        ReferencePointArray rpa = new ReferencePointArray();
        rpa.Append(ap1);
        rpa.Append(ap2);

        CurveByPoints pathCurve = familyDoc.FamilyCreate.NewCurveByPoints(rpa);

        // Panel width perpendicular to path
        double panelW = {_ft(1000)};  // 1000 mm panel width
        double panelT = {_ft(20)};    // 20 mm thickness

        // Use the curve as sweep path for a rectangular profile
        ReferenceArray pathRefs = new ReferenceArray();
        pathRefs.Append(pathCurve.GeometryCurve.Reference);

        CurveArray panelProfile = new CurveArray();
        panelProfile.Append(Line.CreateBound(new XYZ(0,-panelW/2,0),  new XYZ(0, panelW/2,0)));
        panelProfile.Append(Line.CreateBound(new XYZ(0, panelW/2,0),  new XYZ(0, panelW/2,panelT)));
        panelProfile.Append(Line.CreateBound(new XYZ(0, panelW/2,panelT),new XYZ(0,-panelW/2,panelT)));
        panelProfile.Append(Line.CreateBound(new XYZ(0,-panelW/2,panelT),new XYZ(0,-panelW/2,0)));

        ReferenceArrayArray pathArray = new ReferenceArrayArray();
        pathArray.Append(pathRefs);

        familyDoc.FamilyCreate.NewSweep(
            true, pathArray,
            new SweepProfile(panelProfile),
            0,
            ProfilePlaneLocation.Start);
    }}

    tx.Commit();
}}""",
        ))

        # Four-point adaptive shell
        samples.append(_s(
            "Create a four-point adaptive component family that generates a warped surface panel across four corner points",
            f"""\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

// Four-point adaptive component: warped quad surface using lofted form between point pairs
// Adaptive family template required; four adaptive reference points pre-exist
using (Transaction tx = new Transaction(familyDoc, "Create 4-Point Adaptive Shell"))
{{
    tx.Start();

    // Get the four adaptive reference points
    List<ReferencePoint> adaptivePts = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePoint))
        .Cast<ReferencePoint>()
        .Take(4)
        .ToList();

    if (adaptivePts.Count == 4)
    {{
        // Create a form by lofting through profile curves at each pair of points
        // Profile 1: line from AP1 to AP2
        ReferencePointArray edge1 = new ReferencePointArray();
        edge1.Append(adaptivePts[0]);
        edge1.Append(adaptivePts[1]);
        CurveByPoints curve1 = familyDoc.FamilyCreate.NewCurveByPoints(edge1);

        // Profile 2: line from AP4 to AP3
        ReferencePointArray edge2 = new ReferencePointArray();
        edge2.Append(adaptivePts[3]);
        edge2.Append(adaptivePts[2]);
        CurveByPoints curve2 = familyDoc.FamilyCreate.NewCurveByPoints(edge2);

        // Loft a form (Blend) between the two edge curves
        ReferenceArrayArray profileSet = new ReferenceArrayArray();

        ReferenceArray profile1 = new ReferenceArray();
        profile1.Append(curve1.GeometryCurve.Reference);
        profileSet.Append(profile1);

        ReferenceArray profile2 = new ReferenceArray();
        profile2.Append(curve2.GeometryCurve.Reference);
        profileSet.Append(profile2);

        // NewLoftForm creates a surface between profiles
        Form loftForm = familyDoc.FamilyCreate.NewLoftForm(true, profileSet);
    }}

    tx.Commit();
}}""",
        ))

        # Reporting parameters on adaptive points
        samples.append(_s(
            "Add reporting parameters to an adaptive component family to read back the distance between two adaptive points",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

// Reporting parameter: reads the length of a reference line between two adaptive points
// Reporting parameters are read-only; driven by geometry, not user input
FamilyManager famMgr = familyDoc.FamilyManager;

// Add a reporting length parameter
FamilyParameter pSpan = famMgr.AddParameter(
    "SpanLength",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length,
    false);  // type parameter

// In adaptive families, reporting parameters are labeled on dimensions
// that reference adaptive point geometry
using (Transaction tx = new Transaction(familyDoc, "Add Reporting Span"))
{{
    tx.Start();

    // Get the reference line (curve between AP1 and AP2)
    CurveElement spanCurve = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(CurveElement))
        .Cast<CurveElement>()
        .FirstOrDefault();

    if (spanCurve != null)
    {{
        View activeView = familyDoc.ActiveView;

        // Create a linear dimension along the span curve
        ReferenceArray dimRefs = new ReferenceArray();
        dimRefs.Append(spanCurve.GeometryCurve.GetEndPointReference(0));
        dimRefs.Append(spanCurve.GeometryCurve.GetEndPointReference(1));

        Line dimLine = spanCurve.GeometryCurve as Line;
        if (dimLine != null)
        {{
            Dimension spanDim = familyDoc.FamilyCreate.NewLinearDimension(
                activeView, dimLine, dimRefs);

            // Label dimension with reporting parameter
            if (spanDim != null && spanDim.IsReferencesValidForLabel())
            {{
                spanDim.FamilyLabel = pSpan;
                // Mark as reporting (read-only from geometry)
                spanDim.IsReporting = true;
            }}
        }}
    }}

    tx.Commit();
}}""",
        ))

        return samples
