"""Training data generator: Revit MEP family patterns.

Produces ~250 Alpaca-format training pairs covering duct/pipe fittings,
electrical families, mechanical equipment, and plumbing fixtures.
"""

from __future__ import annotations

from typing import Any, Dict, List

SAMPLE = Dict[str, Any]
MM_TO_FT = 1.0 / 304.8


def _s(instruction: str, output: str) -> SAMPLE:
    return {"instruction": instruction, "input": "", "output": output}


def _ft(mm: float) -> str:
    return f"{mm * MM_TO_FT:.6f}"


class MEPFamilyGenerator:
    """Generates training samples for Revit MEP family creation."""

    def generate(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []
        samples += self._pipe_fittings()
        samples += self._duct_fittings()
        samples += self._electrical_families()
        samples += self._mechanical_equipment()
        samples += self._plumbing_fixtures()
        samples += self._mep_connectors()
        samples += self._mep_parameters()
        return samples

    # ------------------------------------------------------------------
    # Pipe fittings
    # ------------------------------------------------------------------

    def _pipe_fittings(self) -> List[SAMPLE]:
        samples = []
        # (DN_mm, OD_mm, angle_deg, fitting_type)
        elbow_cases = [
            (25,  33.4, 90, "DN25 90-degree elbow"),
            (32,  42.2, 90, "DN32 90-degree elbow"),
            (40,  48.3, 90, "DN40 90-degree elbow"),
            (50,  60.3, 90, "DN50 90-degree elbow"),
            (65,  76.1, 90, "DN65 90-degree elbow"),
            (80,  88.9, 90, "DN80 90-degree elbow"),
            (100, 114.3, 90, "DN100 90-degree elbow"),
            (150, 168.3, 90, "DN150 90-degree elbow"),
            (200, 219.1, 45, "DN200 45-degree elbow"),
            (25,  33.4, 45, "DN25 45-degree elbow"),
        ]
        for (dn, od, angle, desc) in elbow_cases:
            r_bend = od * 1.5  # typical centerline bend radius
            samples.append(_s(
                f"Create a pipe {desc} family with {od}mm OD",
                f"""\
using Autodesk.Revit.DB;

// Pipe {desc}: OD={od}mm, bend radius={r_bend:.1f}mm
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pOD = famMgr.AddParameter("NominalDiameter",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pAngle = famMgr.AddParameter("Angle",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Angle, false);
famMgr.Set(pOD, {_ft(od)}); // {od} mm OD
famMgr.Set(pAngle, {angle * 3.14159265 / 180:.6f}); // {angle} degrees

using (Transaction tx = new Transaction(familyDoc, "Create Pipe Elbow Body"))
{{
    tx.Start();
    double od = {_ft(od)};
    double r  = {_ft(r_bend)};  // bend radius

    // Elbow body: solid of revolution of a pipe cross-section
    // Profile: annular ring in YZ plane
    double pipeR = od / 2;
    double wallT = {_ft(max(3, od * 0.05))};  // approx wall thickness

    CurveArray loop = new CurveArray();
    // Outer arc of cross-section at bend radius
    double ri = pipeR - wallT;
    loop.Append(Line.CreateBound(new XYZ(0, r - pipeR, 0), new XYZ(0, r + pipeR, 0)));
    loop.Append(Line.CreateBound(new XYZ(0, r + pipeR, 0), new XYZ(0, r + ri, 0)));
    loop.Append(Line.CreateBound(new XYZ(0, r + ri, 0),    new XYZ(0, r - ri, 0)));
    loop.Append(Line.CreateBound(new XYZ(0, r - ri, 0),    new XYZ(0, r - pipeR, 0)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero));
    Line axis = Line.CreateBound(XYZ.Zero, new XYZ(0, 0, {_ft(r_bend)}));
    familyDoc.FamilyCreate.NewRevolution(true, profile, sp, axis,
        0, {angle * 3.14159265 / 180:.6f});
    tx.Commit();
}}"""))

        # Pipe tee
        for (dn, od, desc) in [(50, 60.3, "DN50"), (80, 88.9, "DN80"), (100, 114.3, "DN100")]:
            samples.append(_s(f"Create a {desc} pipe tee family with {od}mm OD",
                f"""\
using Autodesk.Revit.DB;

// {desc} pipe tee: OD={od}mm
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pOD = famMgr.AddParameter("NominalDiameter",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pOD, {_ft(od)}); // {od} mm OD

using (Transaction tx = new Transaction(familyDoc, "Create Tee Body"))
{{
    tx.Start();
    double od = {_ft(od)};
    double r  = od / 2;
    double bodyLen = od * 3;

    // Main run: solid cylinder
    double wallT = r * 0.1;
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));

    // Simplified: rectangular placeholder for tee body
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-r, 0, 0),    new XYZ( r, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ( r, 0, 0),    new XYZ( r, 0, r*2)));
    loop.Append(Line.CreateBound(new XYZ( r, 0, r*2),  new XYZ(-r, 0, r*2)));
    loop.Append(Line.CreateBound(new XYZ(-r, 0, r*2),  new XYZ(-r, 0, 0)));
    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bodyLen);
    tx.Commit();
}}"""))

        # Reducer
        for (dn1, od1, dn2, od2) in [(100, 114.3, 80, 88.9), (80, 88.9, 50, 60.3), (150, 168.3, 100, 114.3)]:
            samples.append(_s(
                f"Create a pipe reducer DN{dn1}x{dn2} ({od1}mm to {od2}mm OD)",
                f"""\
using Autodesk.Revit.DB;

// Pipe reducer: {od1}mm to {od2}mm OD
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pOD1 = famMgr.AddParameter("InletDiameter",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pOD2 = famMgr.AddParameter("OutletDiameter",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pOD1, {_ft(od1)}); // {od1} mm
famMgr.Set(pOD2, {_ft(od2)}); // {od2} mm

using (Transaction tx = new Transaction(familyDoc, "Create Reducer"))
{{
    tx.Start();
    double od1 = {_ft(od1)}; double od2 = {_ft(od2)};
    double length = {_ft(150)}; // 150mm body length

    // Reducer: blend from larger to smaller
    CurveArray bottomLoop = new CurveArray();
    bottomLoop.Append(Line.CreateBound(new XYZ(-od1/2, -od1/2, 0),      new XYZ( od1/2, -od1/2, 0)));
    bottomLoop.Append(Line.CreateBound(new XYZ( od1/2, -od1/2, 0),      new XYZ( od1/2,  od1/2, 0)));
    bottomLoop.Append(Line.CreateBound(new XYZ( od1/2,  od1/2, 0),      new XYZ(-od1/2,  od1/2, 0)));
    bottomLoop.Append(Line.CreateBound(new XYZ(-od1/2,  od1/2, 0),      new XYZ(-od1/2, -od1/2, 0)));
    CurveArray topLoop = new CurveArray();
    topLoop.Append(Line.CreateBound(new XYZ(-od2/2, -od2/2, length),    new XYZ( od2/2, -od2/2, length)));
    topLoop.Append(Line.CreateBound(new XYZ( od2/2, -od2/2, length),    new XYZ( od2/2,  od2/2, length)));
    topLoop.Append(Line.CreateBound(new XYZ( od2/2,  od2/2, length),    new XYZ(-od2/2,  od2/2, length)));
    topLoop.Append(Line.CreateBound(new XYZ(-od2/2,  od2/2, length),    new XYZ(-od2/2, -od2/2, length)));
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewBlend(true, topLoop, bottomLoop, sp);
    tx.Commit();
}}"""))
        return samples  # 10 + 3 + 3 = 16

    # ------------------------------------------------------------------
    # Duct fittings
    # ------------------------------------------------------------------

    def _duct_fittings(self) -> List[SAMPLE]:
        samples = []
        # (W1, H1, W2, H2, desc) for transitions
        transitions = [
            (400, 200, 300, 150, "400x200 to 300x150"),
            (600, 300, 400, 200, "600x300 to 400x200"),
            (800, 400, 600, 300, "800x400 to 600x300"),
            (300, 300, 200, 200, "300x300 to 200x200"),
            (500, 250, 350, 200, "500x250 to 350x200"),
        ]
        for (W1, H1, W2, H2, desc) in transitions:
            samples.append(_s(f"Create a rectangular duct transition family {desc}",
                f"""\
using Autodesk.Revit.DB;

// Duct transition: {W1}x{H1}mm to {W2}x{H2}mm
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW1 = famMgr.AddParameter("InletWidth",   BuiltInParameterGroup.PG_MECHANICAL, ParameterType.Length, false);
FamilyParameter pH1 = famMgr.AddParameter("InletHeight",  BuiltInParameterGroup.PG_MECHANICAL, ParameterType.Length, false);
FamilyParameter pW2 = famMgr.AddParameter("OutletWidth",  BuiltInParameterGroup.PG_MECHANICAL, ParameterType.Length, false);
FamilyParameter pH2 = famMgr.AddParameter("OutletHeight", BuiltInParameterGroup.PG_MECHANICAL, ParameterType.Length, false);
famMgr.Set(pW1, {_ft(W1)}); famMgr.Set(pH1, {_ft(H1)});
famMgr.Set(pW2, {_ft(W2)}); famMgr.Set(pH2, {_ft(H2)});

using (Transaction tx = new Transaction(familyDoc, "Create Duct Transition"))
{{
    tx.Start();
    double w1 = {_ft(W1)}; double h1 = {_ft(H1)};
    double w2 = {_ft(W2)}; double h2 = {_ft(H2)};
    double length = {_ft(400)}; // 400mm body length

    CurveArray bottomLoop = new CurveArray();
    bottomLoop.Append(Line.CreateBound(new XYZ(-w1/2, -h1/2, 0),      new XYZ( w1/2, -h1/2, 0)));
    bottomLoop.Append(Line.CreateBound(new XYZ( w1/2, -h1/2, 0),      new XYZ( w1/2,  h1/2, 0)));
    bottomLoop.Append(Line.CreateBound(new XYZ( w1/2,  h1/2, 0),      new XYZ(-w1/2,  h1/2, 0)));
    bottomLoop.Append(Line.CreateBound(new XYZ(-w1/2,  h1/2, 0),      new XYZ(-w1/2, -h1/2, 0)));

    CurveArray topLoop = new CurveArray();
    topLoop.Append(Line.CreateBound(new XYZ(-w2/2, -h2/2, length),    new XYZ( w2/2, -h2/2, length)));
    topLoop.Append(Line.CreateBound(new XYZ( w2/2, -h2/2, length),    new XYZ( w2/2,  h2/2, length)));
    topLoop.Append(Line.CreateBound(new XYZ( w2/2,  h2/2, length),    new XYZ(-w2/2,  h2/2, length)));
    topLoop.Append(Line.CreateBound(new XYZ(-w2/2,  h2/2, length),    new XYZ(-w2/2, -h2/2, length)));

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewBlend(true, topLoop, bottomLoop, sp);
    tx.Commit();
}}"""))

        # Straight duct sections
        duct_sizes = [
            (200, 100, 2000), (300, 150, 2000), (400, 200, 2000),
            (500, 300, 2000), (600, 300, 2000), (800, 400, 2000),
            (1000, 500, 2000), (1200, 600, 2000),
        ]
        for (W, H, L) in duct_sizes:
            samples.append(_s(f"Create a straight rectangular duct family {W}x{H}mm, {L}mm length",
                f"""\
using Autodesk.Revit.DB;

// Rectangular duct: {W}x{H}mm, {L}mm long
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW = famMgr.AddParameter("Width",  BuiltInParameterGroup.PG_MECHANICAL, ParameterType.Length, false);
FamilyParameter pH = famMgr.AddParameter("Height", BuiltInParameterGroup.PG_MECHANICAL, ParameterType.Length, false);
FamilyParameter pL = famMgr.AddParameter("Length", BuiltInParameterGroup.PG_MECHANICAL, ParameterType.Length, false);
famMgr.Set(pW, {_ft(W)}); famMgr.Set(pH, {_ft(H)}); famMgr.Set(pL, {_ft(L)});

using (Transaction tx = new Transaction(familyDoc, "Create Duct Section"))
{{
    tx.Start();
    double w = {_ft(W)}; double h = {_ft(H)}; double l = {_ft(L)};
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-w/2, -h/2, 0), new XYZ( w/2, -h/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, -h/2, 0), new XYZ( w/2,  h/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2,  h/2, 0), new XYZ(-w/2,  h/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-w/2,  h/2, 0), new XYZ(-w/2, -h/2, 0)));
    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, l);
    tx.Commit();
}}"""))
        return samples  # 5 + 8 = 13

    # ------------------------------------------------------------------
    # Electrical families
    # ------------------------------------------------------------------

    def _electrical_families(self) -> List[SAMPLE]:
        samples = []
        panel_cases = [
            (20,  120, "20A residential panel"),
            (40,  120, "40A sub-panel"),
            (100, 120, "100A main panel"),
            (200, 208, "200A 3-phase panel"),
            (400, 480, "400A service entrance panel"),
        ]
        for (amps, volts, desc) in panel_cases:
            samples.append(_s(f"Create an electrical {desc} family",
                f"""\
using Autodesk.Revit.DB;

// Electrical {desc}: {amps}A, {volts}V
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pAmps  = famMgr.AddParameter("AmpereRating", BuiltInParameterGroup.PG_ELECTRICAL, ParameterType.Number, false);
FamilyParameter pVolts = famMgr.AddParameter("Voltage",      BuiltInParameterGroup.PG_ELECTRICAL, ParameterType.Number, false);
FamilyParameter pW     = famMgr.AddParameter("Width",        BuiltInParameterGroup.PG_GEOMETRY,   ParameterType.Length, false);
FamilyParameter pH     = famMgr.AddParameter("Height",       BuiltInParameterGroup.PG_GEOMETRY,   ParameterType.Length, false);
FamilyParameter pD     = famMgr.AddParameter("Depth",        BuiltInParameterGroup.PG_GEOMETRY,   ParameterType.Length, false);
famMgr.Set(pAmps,  {float(amps)});
famMgr.Set(pVolts, {float(volts)});
famMgr.Set(pW, {_ft(400)}); // 400 mm width
famMgr.Set(pH, {_ft(600)}); // 600 mm height
famMgr.Set(pD, {_ft(150)}); // 150 mm depth

using (Transaction tx = new Transaction(familyDoc, "Create Panel Box"))
{{
    tx.Start();
    double w = {_ft(400)}; double h = {_ft(600)}; double d = {_ft(150)};
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-w/2, 0, 0),  new XYZ( w/2, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, 0, 0),  new XYZ( w/2, d, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, d, 0),  new XYZ(-w/2, d, 0)));
    loop.Append(Line.CreateBound(new XYZ(-w/2, d, 0),  new XYZ(-w/2, 0, 0)));
    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);
    tx.Commit();
}}"""))

        # Light fixtures
        for (L, W, desc) in [(600, 600, "600x600mm recessed panel"), (1200, 300, "1200x300mm linear fixture"),
                              (300, 300, "300x300mm downlight"), (600, 150, "600x150mm strip light")]:
            samples.append(_s(f"Create a {desc} lighting family",
                f"""\
using Autodesk.Revit.DB;

// Lighting fixture: {L}x{W}mm
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pL = famMgr.AddParameter("Length",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pW = famMgr.AddParameter("Width",   BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pLW = famMgr.AddParameter("Wattage", BuiltInParameterGroup.PG_ELECTRICAL, ParameterType.Number, false);
famMgr.Set(pL, {_ft(L)}); famMgr.Set(pW, {_ft(W)}); famMgr.Set(pLW, 40.0);

using (Transaction tx = new Transaction(familyDoc, "Create Light Fixture"))
{{
    tx.Start();
    double l = {_ft(L)}; double w = {_ft(W)}; double depth = {_ft(50)}; // 50mm depth
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-l/2, -w/2, 0), new XYZ( l/2, -w/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( l/2, -w/2, 0), new XYZ( l/2,  w/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( l/2,  w/2, 0), new XYZ(-l/2,  w/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-l/2,  w/2, 0), new XYZ(-l/2, -w/2, 0)));
    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, depth);
    tx.Commit();
}}"""))
        return samples  # 5 + 4 = 9

    # ------------------------------------------------------------------
    # Mechanical equipment
    # ------------------------------------------------------------------

    def _mechanical_equipment(self) -> List[SAMPLE]:
        samples = []
        mech_cases = [
            (2000, 1000, 1500, "air handling unit (AHU)",    10000.0, 8000.0, 5000.0),
            (600,  400,  600,  "VAV box",                      2000.0, 1500.0,  800.0),
            (800,  600,  400,  "fan coil unit",                3000.0, 2500.0, 1200.0),
            (1200, 800,  1000, "heat exchanger",               8000.0, 7000.0, 3000.0),
            (500,  500,  400,  "inline fan",                   1500.0, 1200.0,  600.0),
        ]
        for (L, W, H, desc, cooling, heating, airflow) in mech_cases:
            samples.append(_s(f"Create a {desc} family {L}x{W}x{H}mm",
                f"""\
using Autodesk.Revit.DB;

// {desc}: {L}x{W}x{H}mm
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pL = famMgr.AddParameter("Length",          BuiltInParameterGroup.PG_GEOMETRY,    ParameterType.Length, false);
FamilyParameter pW = famMgr.AddParameter("Width",           BuiltInParameterGroup.PG_GEOMETRY,    ParameterType.Length, false);
FamilyParameter pH = famMgr.AddParameter("Height",          BuiltInParameterGroup.PG_GEOMETRY,    ParameterType.Length, false);
FamilyParameter pC = famMgr.AddParameter("CoolingCapacity", BuiltInParameterGroup.PG_MECHANICAL,  ParameterType.Number, false);
FamilyParameter pHt = famMgr.AddParameter("HeatingCapacity",BuiltInParameterGroup.PG_MECHANICAL,  ParameterType.Number, false);
FamilyParameter pAF = famMgr.AddParameter("AirFlow",        BuiltInParameterGroup.PG_MECHANICAL,  ParameterType.Number, false);
famMgr.Set(pL, {_ft(L)}); famMgr.Set(pW, {_ft(W)}); famMgr.Set(pH, {_ft(H)});
famMgr.Set(pC, {cooling}); famMgr.Set(pHt, {heating}); famMgr.Set(pAF, {airflow});

using (Transaction tx = new Transaction(familyDoc, "Create {desc.split()[0].title()} Body"))
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
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);
    tx.Commit();
}}"""))
        return samples  # 5

    # ------------------------------------------------------------------
    # Plumbing fixtures
    # ------------------------------------------------------------------

    def _plumbing_fixtures(self) -> List[SAMPLE]:
        samples = []
        fixtures = [
            (600, 450, 200, "kitchen sink",        50, "HotCold"),
            (700, 400, 180, "bathroom vanity sink", 40, "HotCold"),
            (380, 680, 200, "floor-mounted toilet", 100, "ColdOnly"),
            (380, 700, 900, "wall-hung toilet",     100, "ColdOnly"),
            (350, 350, 900, "urinal",               50,  "ColdOnly"),
            (450, 450, 50,  "floor drain",          100, "DrainOnly"),
            (600, 600, 800, "water heater",         25,  "HotColdGas"),
            (300, 200, 400, "hose bib",             25,  "Cold"),
        ]
        for (L, W, H, desc, conn_dia, conn_type) in fixtures:
            samples.append(_s(f"Create a plumbing {desc} family {L}x{W}mm",
                f"""\
using Autodesk.Revit.DB;

// Plumbing {desc}: {L}x{W}mm, {H}mm height, {conn_dia}mm connections ({conn_type})
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pL  = famMgr.AddParameter("Length",    BuiltInParameterGroup.PG_GEOMETRY,  ParameterType.Length, false);
FamilyParameter pW  = famMgr.AddParameter("Width",     BuiltInParameterGroup.PG_GEOMETRY,  ParameterType.Length, false);
FamilyParameter pH  = famMgr.AddParameter("Height",    BuiltInParameterGroup.PG_GEOMETRY,  ParameterType.Length, false);
FamilyParameter pDia = famMgr.AddParameter("ConnDiameter", BuiltInParameterGroup.PG_PLUMBING, ParameterType.Length, false);
famMgr.Set(pL, {_ft(L)}); famMgr.Set(pW, {_ft(W)}); famMgr.Set(pH, {_ft(H)});
famMgr.Set(pDia, {_ft(conn_dia)}); // {conn_dia} mm connection diameter

using (Transaction tx = new Transaction(familyDoc, "Create {desc.title()} Body"))
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
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);
    tx.Commit();
}}"""))
        return samples  # 8

    # ------------------------------------------------------------------
    # MEP connectors
    # ------------------------------------------------------------------

    def _mep_connectors(self) -> List[SAMPLE]:
        samples = []
        connector_cases = [
            ("Pipe",       "Autodesk.Revit.DB.Plumbing.PipeConnector",     "Domain.DomainPiping",    "50mm pipe"),
            ("Duct",       "Autodesk.Revit.DB.Mechanical.DuctConnector",   "Domain.DomainHvac",      "300x200mm duct"),
            ("Conduit",    "Autodesk.Revit.DB.Electrical.ConduitConnector","Domain.DomainElectrical","25mm conduit"),
        ]
        for (type_name, ns, domain, desc) in connector_cases:
            samples.append(_s(f"Add a {type_name} connector to a {desc} family",
                f"""\
using Autodesk.Revit.DB;

// Add {type_name} connector to MEP family
// ConnectorElement is added in the family editor through FamilyCreate
using (Transaction tx = new Transaction(familyDoc, "Add {type_name} Connector"))
{{
    tx.Start();

    // In family editor: place connector at origin on reference plane
    // Connectors are added via the family connector UI or via:
    ConnectorElement connector = ConnectorElement.Create{type_name}Connector(
        familyDoc,
        {domain},
        new XYZ(0, 0, 0));  // connector origin

    // Set flow direction and system type
    connector.Direction = FlowDirectionType.Bidirectional;

    // Set connector size
    Parameter diaParam = connector.get_Parameter(BuiltInParameter.CONNECTOR_RADIUS);
    if (diaParam != null && !diaParam.IsReadOnly)
        diaParam.Set({_ft(25)}); // 25mm (radius = 25mm for 50mm OD)

    tx.Commit();
}}"""))

        # Generic connector patterns
        for (flow_dir, desc) in [("Inlet", "supply"), ("Outlet", "return"), ("Bidirectional", "bidirectional")]:
            samples.append(_s(f"Create a {desc} duct connector on a mechanical equipment family",
                f"""\
using Autodesk.Revit.DB;

// {desc} duct connector on mechanical equipment family
using (Transaction tx = new Transaction(familyDoc, "Add {flow_dir} Duct Connector"))
{{
    tx.Start();

    ConnectorElement conn = ConnectorElement.CreateDuctConnector(
        familyDoc,
        Domain.DomainHvac,
        new XYZ(0, 0, {_ft(500)})); // 500mm above origin

    conn.Direction = FlowDirectionType.{flow_dir};

    // Set connector width and height for rectangular duct
    Parameter wParam = conn.get_Parameter(BuiltInParameter.CONNECTOR_WIDTH);
    Parameter hParam = conn.get_Parameter(BuiltInParameter.CONNECTOR_HEIGHT);
    if (wParam != null) wParam.Set({_ft(400)}); // 400mm width
    if (hParam != null) hParam.Set({_ft(200)}); // 200mm height

    tx.Commit();
}}"""))
        return samples  # 3 + 3 = 6

    # ------------------------------------------------------------------
    # MEP parameters
    # ------------------------------------------------------------------

    def _mep_parameters(self) -> List[SAMPLE]:
        samples = []
        bip_cases = [
            ("RBS_PIPE_DIAMETER_PARAM",      "pipe nominal diameter",  "Pipe"),
            ("RBS_DUCT_WIDTH_PARAM",          "duct width",            "Duct"),
            ("RBS_DUCT_HEIGHT_PARAM",         "duct height",           "Duct"),
            ("RBS_ELEC_VOLTAGE",              "electrical voltage",    "Electrical device"),
            ("RBS_ELEC_NUMBER_OF_POLES",      "number of poles",       "Electrical device"),
            ("RBS_CALCULATED_SIZE",           "calculated size",       "MEP element"),
            ("RBS_PIPE_INSULATION_THICKNESS", "pipe insulation thickness", "Pipe"),
            ("RBS_DUCT_INSULATION_THICKNESS", "duct insulation thickness", "Duct"),
        ]
        for (bip, desc, category) in bip_cases:
            samples.append(_s(f"Read the {desc} from a {category.lower()} element",
                f"""\
using Autodesk.Revit.DB;

// Read {desc} using BuiltInParameter.{bip}
Element mepElement = new FilteredElementCollector(doc)
    .OfCategory(BuiltInCategory.OST_MechanicalEquipment)
    .OfClass(typeof(FamilyInstance))
    .Cast<FamilyInstance>()
    .FirstOrDefault();

if (mepElement != null)
{{
    Parameter param = mepElement.get_Parameter(BuiltInParameter.{bip});
    if (param != null)
    {{
        if (param.StorageType == StorageType.Double)
        {{
            double valueMm = param.AsDouble() / MM_TO_FT; // convert feet to mm
        }}
        else if (param.StorageType == StorageType.Integer)
        {{
            int value = param.AsInteger();
        }}
    }}
    // MM_TO_FT = 1.0 / 304.8
}}"""))

        # Set MEP parameters
        for (param_name, group, ptype, default_val, unit) in [
            ("SystemType",       "PG_MECHANICAL",  "ParameterType.Text",    "Supply Air",    "text"),
            ("InsulationThick",  "PG_MECHANICAL",  "ParameterType.Length",  25,              "mm"),
            ("DesignFlowRate",   "PG_MECHANICAL",  "ParameterType.Number",  500.0,           "L/s"),
            ("WorkingPressure",  "PG_PLUMBING",    "ParameterType.Number",  10.0,            "bar"),
            ("CircuitLength",    "PG_ELECTRICAL",  "ParameterType.Length",  30000,           "mm"),
        ]:
            if ptype == "ParameterType.Length" and isinstance(default_val, (int, float)) and default_val > 0:
                set_line = f'famMgr.Set(p, {_ft(default_val)}); // {default_val} mm'
            elif ptype == "ParameterType.Number":
                set_line = f'famMgr.Set(p, {float(default_val)}); // {default_val} {unit}'
            else:
                set_line = f'famMgr.Set(p, "{default_val}"); // default text'
            samples.append(_s(f"Add a '{param_name}' MEP parameter to a family",
                f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter p = famMgr.AddParameter(
    "{param_name}",
    BuiltInParameterGroup.{group},
    {ptype},
    false);
{set_line}"""))
        return samples  # 8 + 5 = 13


if __name__ == "__main__":
    gen = MEPFamilyGenerator()
    samples = gen.generate()
    print(f"Generated {len(samples)} samples")
    assert all(set(s.keys()) == {"instruction", "input", "output"} for s in samples)
    print("[OK] All samples valid")
