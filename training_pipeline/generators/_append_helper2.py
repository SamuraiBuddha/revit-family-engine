"""Appends equipment_families, electrical_fixtures, sprinkler_heads,
plumbing_fixtures, and connector_parameters methods."""

MM_TO_FT = 1.0 / 304.8

def ft(mm):
    return f"{mm * MM_TO_FT:.6f}"

EQUIPMENT = f"""
    # ------------------------------------------------------------------
    # Equipment families
    # ------------------------------------------------------------------

    def _equipment_families(self) -> List[SAMPLE]:
        samples = []

        # VAV box
        samples.append(_s(
            "Create a VAV (Variable Air Volume) box family with supply duct inlet and outlet connectors",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

// VAV box: round inlet (upstream duct), rectangular outlet (to room diffusers)
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pAirflow = famMgr.AddParameter(
    "Maximum Airflow",
    BuiltInParameterGroup.PG_MECHANICAL_AIRFLOW,
    ParameterType.AirFlow,
    false);
famMgr.Set(pAirflow, 0.472); // 1000 CFM = 0.472 m3/s

using (Transaction tx = new Transaction(familyDoc, "Create VAV Box"))
{{
    tx.Start();

    // Body geometry: 600x400x300mm box
    double bw = {ft(600)}; double bd = {ft(400)}; double bh = {ft(300)};
    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2, -bd/2, 0), new XYZ( bw/2, -bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, -bd/2, 0), new XYZ( bw/2,  bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,  bd/2, 0), new XYZ(-bw/2,  bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2,  bd/2, 0), new XYZ(-bw/2, -bd/2, 0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    // Round inlet connector (upstream)
    ConnectorElement inlet = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Round,
        new XYZ(-bw / 2, 0, bh / 2));
    inlet.Radius = {200 * MM_TO_FT / 2:.6f}; // 200 mm dia
    inlet.FlowDirection = FlowDirectionType.In;

    // Rectangular outlet connector (downstream to diffusers)
    ConnectorElement outlet = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ( bw / 2, 0, bh / 2));
    outlet.Width  = {ft(400)};
    outlet.Height = {ft(200)};
    outlet.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        # AHU (Air Handling Unit)
        samples.append(_s(
            "Create an Air Handling Unit (AHU) family with supply, return, and outdoor air duct connectors",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create AHU"))
{{
    tx.Start();

    // AHU body: 2000x1200x1800mm
    double bw = {ft(2000)}; double bd = {ft(1200)}; double bh = {ft(1800)};
    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(0, 0, 0),   new XYZ(bw, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ(bw, 0, 0),  new XYZ(bw, bd, 0)));
    loop.Append(Line.CreateBound(new XYZ(bw, bd, 0), new XYZ(0, bd, 0)));
    loop.Append(Line.CreateBound(new XYZ(0, bd, 0),  new XYZ(0, 0, 0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    // Supply air outlet (top)
    ConnectorElement supply = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ(bw / 2, bd / 2, bh));
    supply.Width = {ft(800)}; supply.Height = {ft(400)};
    supply.FlowDirection = FlowDirectionType.Out;

    // Return air inlet (front face)
    ConnectorElement ret = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.ReturnAir, ConnectorProfileType.Rectangular,
        new XYZ(bw / 2, 0, bh / 2));
    ret.Width = {ft(800)}; ret.Height = {ft(500)};
    ret.FlowDirection = FlowDirectionType.In;

    // Outdoor air intake (side)
    ConnectorElement oa = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.OtherAir, ConnectorProfileType.Rectangular,
        new XYZ(0, bd / 2, bh / 2));
    oa.Width = {ft(400)}; oa.Height = {ft(300)};
    oa.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}\"\"\"))

        # Chilled water pump
        samples.append(_s(
            "Create a chilled water pump family with suction and discharge pipe connectors",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Chilled Water Pump"))
{{
    tx.Start();

    // Pump body: 600x400x500mm
    double bw = {ft(600)}; double bd = {ft(400)}; double bh = {ft(500)};
    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2, -bd/2, 0), new XYZ( bw/2, -bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, -bd/2, 0), new XYZ( bw/2,  bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,  bd/2, 0), new XYZ(-bw/2,  bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2,  bd/2, 0), new XYZ(-bw/2, -bd/2, 0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    // Suction inlet (left side)
    ConnectorElement suction = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic,
        {ft(100)}, // 100 mm suction
        new XYZ(-bw / 2, 0, bh / 2));
    suction.FlowDirection = FlowDirectionType.In;

    // Discharge outlet (right side, reduced to 80mm)
    ConnectorElement discharge = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic,
        {ft(80)}, // 80 mm discharge
        new XYZ( bw / 2, 0, bh / 2));
    discharge.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        # Fan coil unit
        samples.append(_s(
            "Create a fan coil unit (FCU) family with supply/return hydronic pipe connectors and supply duct connector",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Fan Coil Unit"))
{{
    tx.Start();

    double bw = {ft(800)}; double bd = {ft(300)}; double bh = {ft(200)};

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2, -bd/2, 0), new XYZ( bw/2, -bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, -bd/2, 0), new XYZ( bw/2,  bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,  bd/2, 0), new XYZ(-bw/2,  bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2,  bd/2, 0), new XYZ(-bw/2, -bd/2, 0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    // Chilled water supply (small bore)
    ConnectorElement cwSupply = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, {ft(25)}, // 25 mm
        new XYZ(-bw / 2 + {ft(50)}, 0, 0));
    cwSupply.FlowDirection = FlowDirectionType.In;

    // Chilled water return
    ConnectorElement cwReturn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.ReturnHydronic, {ft(25)}, // 25 mm
        new XYZ(-bw / 2 + {ft(100)}, 0, 0));
    cwReturn.FlowDirection = FlowDirectionType.Out;

    // Supply air duct outlet (bottom)
    ConnectorElement airOut = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ(0, 0, bh));
    airOut.Width = {ft(600)}; airOut.Height = {ft(100)};
    airOut.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        # Boiler family
        samples.append(_s(
            "Create a hot water boiler family with supply and return hydronic pipe connectors and gas connector",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Boiler"))
{{
    tx.Start();

    double bw = {ft(1000)}; double bd = {ft(600)}; double bh = {ft(1200)};

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2, -bd/2, 0), new XYZ( bw/2, -bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, -bd/2, 0), new XYZ( bw/2,  bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,  bd/2, 0), new XYZ(-bw/2,  bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2,  bd/2, 0), new XYZ(-bw/2, -bd/2, 0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    // HW supply (top)
    ConnectorElement hwSupply = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, {ft(100)},
        new XYZ({ft(150)}, 0, bh));
    hwSupply.FlowDirection = FlowDirectionType.Out;

    // HW return (top)
    ConnectorElement hwReturn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.ReturnHydronic, {ft(100)},
        new XYZ(-{ft(150)}, 0, bh));
    hwReturn.FlowDirection = FlowDirectionType.In;

    // Gas supply (back, bottom)
    ConnectorElement gas = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.OtherPipe, {ft(50)},
        new XYZ(0, -bd / 2, {ft(100)}));
    gas.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}\"\"\"))

        # Cooling tower
        samples.append(_s(
            "Create a cooling tower family with condenser water supply and return pipe connectors",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Cooling Tower"))
{{
    tx.Start();

    double bw = {ft(2000)}; double bd = {ft(2000)}; double bh = {ft(3000)};

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2, -bd/2, 0), new XYZ( bw/2, -bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, -bd/2, 0), new XYZ( bw/2,  bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,  bd/2, 0), new XYZ(-bw/2,  bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2,  bd/2, 0), new XYZ(-bw/2, -bd/2, 0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    // Condenser water supply (warm water from chillers -- enters tower)
    ConnectorElement cwsIn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, {ft(200)},
        new XYZ(0, -bd / 2, {ft(500)}));
    cwsIn.FlowDirection = FlowDirectionType.In;

    // Condenser water return (cooled water back to chillers)
    ConnectorElement cwsOut = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.ReturnHydronic, {ft(200)},
        new XYZ(0, -bd / 2, {ft(300)}));
    cwsOut.FlowDirection = FlowDirectionType.Out;

    // Makeup water
    ConnectorElement makeup = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticColdWater, {ft(25)},
        new XYZ(bw / 2, 0, {ft(800)}));
    makeup.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}\"\"\"))

        # Heat exchanger
        samples.append(_s(
            "Create a plate heat exchanger family with primary and secondary hydronic pipe connectors",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Heat Exchanger"))
{{
    tx.Start();

    double bw = {ft(800)}; double bd = {ft(300)}; double bh = {ft(1000)};

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2, -bd/2, 0), new XYZ( bw/2, -bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, -bd/2, 0), new XYZ( bw/2,  bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,  bd/2, 0), new XYZ(-bw/2,  bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2,  bd/2, 0), new XYZ(-bw/2, -bd/2, 0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    // Primary circuit (left side: supply in, return out)
    ConnectorElement priIn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, {ft(100)},
        new XYZ(-bw / 2, 0, bh * 0.8));
    priIn.FlowDirection = FlowDirectionType.In;

    ConnectorElement priOut = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.ReturnHydronic, {ft(100)},
        new XYZ(-bw / 2, 0, bh * 0.2));
    priOut.FlowDirection = FlowDirectionType.Out;

    // Secondary circuit (right side: supply out, return in)
    ConnectorElement secOut = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, {ft(80)},
        new XYZ( bw / 2, 0, bh * 0.8));
    secOut.FlowDirection = FlowDirectionType.Out;

    ConnectorElement secIn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.ReturnHydronic, {ft(80)},
        new XYZ( bw / 2, 0, bh * 0.2));
    secIn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}\"\"\"))

        # Expansion tank
        samples.append(_s(
            "Create a hydronic expansion tank family with a single pipe connector",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;
using System;

using (Transaction tx = new Transaction(familyDoc, "Create Expansion Tank"))
{{
    tx.Start();

    // Cylindrical tank body: 400mm diameter, 600mm tall
    double r = {ft(200)}; // 200 mm radius
    double h = {ft(600)}; // 600 mm height
    int n = 32;
    CurveArray tankLoop = new CurveArray();
    for (int i = 0; i < n; i++)
    {{
        double a0 = 2 * Math.PI * i / n;
        double a1 = 2 * Math.PI * (i + 1) / n;
        tankLoop.Append(Line.CreateBound(
            new XYZ(r * Math.Cos(a0), r * Math.Sin(a0), 0),
            new XYZ(r * Math.Cos(a1), r * Math.Sin(a1), 0)));
    }}
    CurveArrArray profile = new CurveArrArray();
    profile.Append(tankLoop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    // Single bottom connection
    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, {ft(40)}, // 40 mm
        XYZ.Zero);
    conn.FlowDirection = FlowDirectionType.Bidirectional;

    tx.Commit();
}}\"\"\"))

        # Chiller
        samples.append(_s(
            "Create a water-cooled chiller family with chilled water and condenser water pipe connectors",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Chiller"))
{{
    tx.Start();

    double bw = {ft(3000)}; double bd = {ft(1200)}; double bh = {ft(1500)};

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2, -bd/2, 0), new XYZ( bw/2, -bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, -bd/2, 0), new XYZ( bw/2,  bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,  bd/2, 0), new XYZ(-bw/2,  bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2,  bd/2, 0), new XYZ(-bw/2, -bd/2, 0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    // Chilled water supply (out of evaporator)
    ConnectorElement chwSupply = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, {ft(200)},
        new XYZ(-{ft(600)}, -bd / 2, {ft(400)}));
    chwSupply.FlowDirection = FlowDirectionType.Out;

    // Chilled water return (into evaporator)
    ConnectorElement chwReturn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.ReturnHydronic, {ft(200)},
        new XYZ(-{ft(300)}, -bd / 2, {ft(400)}));
    chwReturn.FlowDirection = FlowDirectionType.In;

    // Condenser water supply (warm CW into condenser)
    ConnectorElement cwsIn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, {ft(200)},
        new XYZ({ft(300)}, -bd / 2, {ft(400)}));
    cwsIn.FlowDirection = FlowDirectionType.In;

    // Condenser water return (cooled CW back to tower)
    ConnectorElement cwsOut = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.ReturnHydronic, {ft(200)},
        new XYZ({ft(600)}, -bd / 2, {ft(400)}));
    cwsOut.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        return samples
"""

ELECTRICAL = f"""
    # ------------------------------------------------------------------
    # Electrical fixtures
    # ------------------------------------------------------------------

    def _electrical_fixtures(self) -> List[SAMPLE]:
        samples = []

        # Recessed lighting
        samples.append(_s(
            "Create a recessed light fixture family with an electrical connector (120V, 26W LED)",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

// Electrical parameters (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pVoltage = famMgr.AddParameter(
    "Voltage",
    BuiltInParameterGroup.PG_ELECTRICAL,
    ParameterType.ElectricalVoltage,
    false);
famMgr.Set(pVoltage, 120.0); // 120V

FamilyParameter pWattage = famMgr.AddParameter(
    "Wattage",
    BuiltInParameterGroup.PG_ELECTRICAL,
    ParameterType.ElectricalPower,
    false);
famMgr.Set(pWattage, 26.0); // 26W

using (Transaction tx = new Transaction(familyDoc, "Create Recessed Light"))
{{
    tx.Start();

    // Housing: 200mm diameter, 150mm deep cylinder
    double r = {ft(100)}; // 100 mm radius
    double depth = {ft(150)}; // 150 mm
    int n = 24;
    CurveArray loop = new CurveArray();
    for (int i = 0; i < n; i++)
    {{
        double a0 = 2 * System.Math.PI * i / n;
        double a1 = 2 * System.Math.PI * (i + 1) / n;
        loop.Append(Line.CreateBound(
            new XYZ(r * System.Math.Cos(a0), r * System.Math.Sin(a0), 0),
            new XYZ(r * System.Math.Cos(a1), r * System.Math.Sin(a1), 0)));
    }}
    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, depth);

    // Electrical connector at top of housing
    ConnectorElement elecConn = ConnectorElement.CreateElectricalConnector(
        familyDoc,
        ElectricalSystemType.PowerBalanced,
        new XYZ(0, 0, depth));
    elecConn.Voltage   = 120.0; // 120V
    elecConn.WiringType = WiringType.SinglePhase;

    tx.Commit();
}}\"\"\"))

        # Linear fluorescent fixture
        samples.append(_s(
            "Create a 1200mm linear LED fixture family with a single-phase 277V electrical connector",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pLength = famMgr.AddParameter(
    "Fixture Length",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length,
    false);
famMgr.Set(pLength, {ft(1200)}); // 1200 mm

using (Transaction tx = new Transaction(familyDoc, "Create Linear LED Fixture"))
{{
    tx.Start();

    double length = {ft(1200)}; // 1200 mm
    double width  = {ft(75)};   // 75 mm
    double height = {ft(60)};   // 60 mm

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-length/2, -width/2, 0), new XYZ( length/2, -width/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( length/2, -width/2, 0), new XYZ( length/2,  width/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( length/2,  width/2, 0), new XYZ(-length/2,  width/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-length/2,  width/2, 0), new XYZ(-length/2, -width/2, 0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, height);

    // Electrical connector at center top
    ConnectorElement conn = ConnectorElement.CreateElectricalConnector(
        familyDoc,
        ElectricalSystemType.PowerBalanced,
        new XYZ(0, 0, height));
    conn.Voltage    = 277.0;
    conn.WiringType = WiringType.SinglePhase;

    tx.Commit();
}}\"\"\"))

        # Pendant light
        samples.append(_s(
            "Create a pendant light fixture family with a 120V electrical connector at the canopy",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

using (Transaction tx = new Transaction(familyDoc, "Create Pendant Light"))
{{
    tx.Start();

    // Canopy plate at top: 150mm disc
    double cR = {ft(75)};  // 75 mm radius
    double cH = {ft(20)};  // 20 mm thick
    int n = 24;
    CurveArray canopyLoop = new CurveArray();
    for (int i = 0; i < n; i++)
    {{
        double a0 = 2 * System.Math.PI * i / n;
        double a1 = 2 * System.Math.PI * (i + 1) / n;
        canopyLoop.Append(Line.CreateBound(
            new XYZ(cR * System.Math.Cos(a0), cR * System.Math.Sin(a0), 0),
            new XYZ(cR * System.Math.Cos(a1), cR * System.Math.Sin(a1), 0)));
    }}
    CurveArrArray profile = new CurveArrArray();
    profile.Append(canopyLoop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, cH);

    // Electrical connector at canopy center
    ConnectorElement conn = ConnectorElement.CreateElectricalConnector(
        familyDoc,
        ElectricalSystemType.PowerBalanced,
        new XYZ(0, 0, cH));
    conn.Voltage    = 120.0;
    conn.WiringType = WiringType.SinglePhase;

    tx.Commit();
}}\"\"\"))

        # Emergency exit sign
        samples.append(_s(
            "Create an emergency exit sign family with a 120V electrical connector and battery backup parameter",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pBattery = famMgr.AddParameter(
    "Battery Backup Hours",
    BuiltInParameterGroup.PG_ELECTRICAL,
    ParameterType.Number,
    false);
famMgr.Set(pBattery, 90.0); // 90 minutes = 1.5 hrs (code minimum)

using (Transaction tx = new Transaction(familyDoc, "Create Exit Sign"))
{{
    tx.Start();

    double w = {ft(300)}; double h_sign = {ft(130)}; double depth = {ft(40)};

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-w/2, 0, 0),      new XYZ( w/2, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, 0, 0),      new XYZ( w/2, depth, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, depth, 0),  new XYZ(-w/2, depth, 0)));
    loop.Append(Line.CreateBound(new XYZ(-w/2, depth, 0),  new XYZ(-w/2, 0, 0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h_sign);

    // Electrical connector
    ConnectorElement conn = ConnectorElement.CreateElectricalConnector(
        familyDoc,
        ElectricalSystemType.PowerBalanced,
        new XYZ(0, depth, h_sign / 2));
    conn.Voltage    = 120.0;
    conn.WiringType = WiringType.SinglePhase;

    tx.Commit();
}}\"\"\"))

        # Duplex receptacle
        samples.append(_s(
            "Create a duplex wall receptacle family with a 120V 20A electrical connector",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pAmperage = famMgr.AddParameter(
    "Amperage",
    BuiltInParameterGroup.PG_ELECTRICAL,
    ParameterType.ElectricalCurrent,
    false);
famMgr.Set(pAmperage, 20.0); // 20A

using (Transaction tx = new Transaction(familyDoc, "Create Duplex Receptacle"))
{{
    tx.Start();

    double w = {ft(70)}; double h = {ft(120)}; double d = {ft(30)};

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-w/2, 0, 0),  new XYZ( w/2, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, 0, 0),  new XYZ( w/2, d, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, d, 0),  new XYZ(-w/2, d, 0)));
    loop.Append(Line.CreateBound(new XYZ(-w/2, d, 0),  new XYZ(-w/2, 0, 0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    ConnectorElement conn = ConnectorElement.CreateElectricalConnector(
        familyDoc,
        ElectricalSystemType.PowerBalanced,
        new XYZ(0, d, h / 2));
    conn.Voltage    = 120.0;
    conn.WiringType = WiringType.SinglePhase;

    tx.Commit();
}}\"\"\"))

        # Panel board
        samples.append(_s(
            "Create an electrical panel family with a 3-phase 208V electrical connector",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pAmpacity = famMgr.AddParameter(
    "Main Breaker Rating",
    BuiltInParameterGroup.PG_ELECTRICAL,
    ParameterType.ElectricalCurrent,
    false);
famMgr.Set(pAmpacity, 200.0); // 200A main

using (Transaction tx = new Transaction(familyDoc, "Create Electrical Panel"))
{{
    tx.Start();

    double w = {ft(500)}; double d = {ft(100)}; double h = {ft(900)};

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-w/2, 0, 0), new XYZ( w/2, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, 0, 0), new XYZ( w/2, d, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, d, 0), new XYZ(-w/2, d, 0)));
    loop.Append(Line.CreateBound(new XYZ(-w/2, d, 0), new XYZ(-w/2, 0, 0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    // 3-phase power connector (top of panel)
    ConnectorElement conn = ConnectorElement.CreateElectricalConnector(
        familyDoc,
        ElectricalSystemType.PowerBalanced,
        new XYZ(0, d / 2, h));
    conn.Voltage    = 208.0;
    conn.WiringType = WiringType.ThreePhase;

    tx.Commit();
}}\"\"\"))

        # Occupancy sensor
        samples.append(_s(
            "Create a ceiling occupancy sensor family with a low-voltage electrical connector",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

using (Transaction tx = new Transaction(familyDoc, "Create Occupancy Sensor"))
{{
    tx.Start();

    double r = {ft(50)}; // 50 mm radius
    double h = {ft(30)}; // 30 mm height
    int n = 24;
    CurveArray loop = new CurveArray();
    for (int i = 0; i < n; i++)
    {{
        double a0 = 2 * System.Math.PI * i / n;
        double a1 = 2 * System.Math.PI * (i + 1) / n;
        loop.Append(Line.CreateBound(
            new XYZ(r * System.Math.Cos(a0), r * System.Math.Sin(a0), 0),
            new XYZ(r * System.Math.Cos(a1), r * System.Math.Sin(a1), 0)));
    }}
    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    ConnectorElement conn = ConnectorElement.CreateElectricalConnector(
        familyDoc,
        ElectricalSystemType.PowerUnBalanced,
        new XYZ(0, 0, h));
    conn.Voltage    = 24.0; // 24V low-voltage
    conn.WiringType = WiringType.SinglePhase;

    tx.Commit();
}}\"\"\"))

        # Data outlet (network)
        samples.append(_s(
            "Create a data outlet family with a telephone/data electrical connector",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

using (Transaction tx = new Transaction(familyDoc, "Create Data Outlet"))
{{
    tx.Start();

    double w = {ft(70)}; double d = {ft(30)}; double h = {ft(90)};

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-w/2, 0, 0), new XYZ( w/2, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, 0, 0), new XYZ( w/2, d, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, d, 0), new XYZ(-w/2, d, 0)));
    loop.Append(Line.CreateBound(new XYZ(-w/2, d, 0), new XYZ(-w/2, 0, 0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    ConnectorElement conn = ConnectorElement.CreateElectricalConnector(
        familyDoc,
        ElectricalSystemType.TelephoneData,
        new XYZ(0, d, h / 2));

    tx.Commit();
}}\"\"\"))

        # Transformer
        samples.append(_s(
            "Create a dry-type transformer family with primary (480V) and secondary (120/208V) electrical connectors",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

using (Transaction tx = new Transaction(familyDoc, "Create Transformer"))
{{
    tx.Start();

    double bw = {ft(800)}; double bd = {ft(500)}; double bh = {ft(900)};

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2, -bd/2, 0), new XYZ( bw/2, -bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, -bd/2, 0), new XYZ( bw/2,  bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,  bd/2, 0), new XYZ(-bw/2,  bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2,  bd/2, 0), new XYZ(-bw/2, -bd/2, 0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    // Primary input (480V 3-phase)
    ConnectorElement primary = ConnectorElement.CreateElectricalConnector(
        familyDoc,
        ElectricalSystemType.PowerBalanced,
        new XYZ(-{ft(200)}, 0, bh));
    primary.Voltage    = 480.0;
    primary.WiringType = WiringType.ThreePhase;

    // Secondary output (208V 3-phase)
    ConnectorElement secondary = ConnectorElement.CreateElectricalConnector(
        familyDoc,
        ElectricalSystemType.PowerBalanced,
        new XYZ( {ft(200)}, 0, bh));
    secondary.Voltage    = 208.0;
    secondary.WiringType = WiringType.ThreePhase;

    tx.Commit();
}}\"\"\"))

        # Smoke detector
        samples.append(_s(
            "Create a smoke detector family with a fire alarm electrical connector",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

using (Transaction tx = new Transaction(familyDoc, "Create Smoke Detector"))
{{
    tx.Start();

    double r = {ft(55)}; // 55 mm radius
    double h = {ft(40)}; // 40 mm height
    int n = 24;
    CurveArray loop = new CurveArray();
    for (int i = 0; i < n; i++)
    {{
        double a0 = 2 * System.Math.PI * i / n;
        double a1 = 2 * System.Math.PI * (i + 1) / n;
        loop.Append(Line.CreateBound(
            new XYZ(r * System.Math.Cos(a0), r * System.Math.Sin(a0), 0),
            new XYZ(r * System.Math.Cos(a1), r * System.Math.Sin(a1), 0)));
    }}
    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    ConnectorElement conn = ConnectorElement.CreateElectricalConnector(
        familyDoc,
        ElectricalSystemType.FireAlarm,
        new XYZ(0, 0, h));

    tx.Commit();
}}\"\"\"))

        return samples
"""

SPRINKLER = f"""
    # ------------------------------------------------------------------
    # Sprinkler heads
    # ------------------------------------------------------------------

    def _sprinkler_heads(self) -> List[SAMPLE]:
        samples = []

        # Standard pendent sprinkler
        samples.append(_s(
            "Create a standard pendent fire sprinkler head family with a 25mm pipe connector and K-factor parameter",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

// Sprinkler parameters (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pKFactor = famMgr.AddParameter(
    "K-Factor",
    BuiltInParameterGroup.PG_MECHANICAL_FLOW,
    ParameterType.Number,
    false);
famMgr.Set(pKFactor, 5.6); // Standard K5.6 (US GPM/psi^0.5)

FamilyParameter pTempRating = famMgr.AddParameter(
    "Temperature Rating",
    BuiltInParameterGroup.PG_DATA,
    ParameterType.Number,
    false);
famMgr.Set(pTempRating, 68.0); // 68 degrees C (ordinary hazard)

using (Transaction tx = new Transaction(familyDoc, "Create Pendent Sprinkler"))
{{
    tx.Start();

    // Body: small cylinder 25mm dia, 100mm long (the frame arms + deflector below)
    double r = {ft(12.5)}; // 12.5 mm radius
    double h = {ft(100)};  // 100 mm
    int n = 16;
    CurveArray loop = new CurveArray();
    for (int i = 0; i < n; i++)
    {{
        double a0 = 2 * System.Math.PI * i / n;
        double a1 = 2 * System.Math.PI * (i + 1) / n;
        loop.Append(Line.CreateBound(
            new XYZ(r * System.Math.Cos(a0), r * System.Math.Sin(a0), 0),
            new XYZ(r * System.Math.Cos(a1), r * System.Math.Sin(a1), 0)));
    }}
    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    // Pipe connector at top (connects to wet pipe system)
    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc,
        PipeSystemType.FireProtectWet,
        {ft(25)}, // 25 mm (1 inch nominal)
        new XYZ(0, 0, h));
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}\"\"\"))

        # Upright sprinkler
        samples.append(_s(
            "Create an upright fire sprinkler head family with a 25mm wet pipe connector",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pKFactor = famMgr.AddParameter(
    "K-Factor", BuiltInParameterGroup.PG_MECHANICAL_FLOW, ParameterType.Number, false);
famMgr.Set(pKFactor, 5.6);

using (Transaction tx = new Transaction(familyDoc, "Create Upright Sprinkler"))
{{
    tx.Start();

    double r = {ft(12.5)};
    double h = {ft(80)};
    int n = 16;
    CurveArray loop = new CurveArray();
    for (int i = 0; i < n; i++)
    {{
        double a0 = 2 * System.Math.PI * i / n;
        double a1 = 2 * System.Math.PI * (i + 1) / n;
        loop.Append(Line.CreateBound(
            new XYZ(r * System.Math.Cos(a0), r * System.Math.Sin(a0), 0),
            new XYZ(r * System.Math.Cos(a1), r * System.Math.Sin(a1), 0)));
    }}
    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    // Upright connector points downward (pipe above, water sprays up then down)
    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.FireProtectWet, {ft(25)}, XYZ.Zero);
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}\"\"\"))

        # Concealed sprinkler
        samples.append(_s(
            "Create a concealed fire sprinkler head family with a 25mm pipe connector and cover plate",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Concealed Sprinkler"))
{{
    tx.Start();

    // Cover plate (flush with ceiling): 100mm disc
    double cpR = {ft(50)};
    int n = 24;
    CurveArray cpLoop = new CurveArray();
    for (int i = 0; i < n; i++)
    {{
        double a0 = 2 * System.Math.PI * i / n;
        double a1 = 2 * System.Math.PI * (i + 1) / n;
        cpLoop.Append(Line.CreateBound(
            new XYZ(cpR * System.Math.Cos(a0), cpR * System.Math.Sin(a0), 0),
            new XYZ(cpR * System.Math.Cos(a1), cpR * System.Math.Sin(a1), 0)));
    }}
    CurveArrArray profile = new CurveArrArray();
    profile.Append(cpLoop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, {ft(5)}); // 5 mm thin

    // Pipe connector above cover plate
    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.FireProtectWet, {ft(25)},
        new XYZ(0, 0, {ft(50)})); // 50 mm above
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}\"\"\"))

        # Dry pipe sprinkler
        samples.append(_s(
            "Create a dry pipe sprinkler head family with a 25mm dry fire protection connector",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

FamilyManager famMgr = familyDoc.FamilyManager;
famMgr.AddParameter("K-Factor", BuiltInParameterGroup.PG_MECHANICAL_FLOW, ParameterType.Number, false);

using (Transaction tx = new Transaction(familyDoc, "Create Dry Pipe Sprinkler"))
{{
    tx.Start();

    double r = {ft(12.5)};
    double h = {ft(100)};
    int n = 16;
    CurveArray loop = new CurveArray();
    for (int i = 0; i < n; i++)
    {{
        double a0 = 2 * System.Math.PI * i / n;
        double a1 = 2 * System.Math.PI * (i + 1) / n;
        loop.Append(Line.CreateBound(
            new XYZ(r * System.Math.Cos(a0), r * System.Math.Sin(a0), 0),
            new XYZ(r * System.Math.Cos(a1), r * System.Math.Sin(a1), 0)));
    }}
    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.FireProtectDry, {ft(25)},
        new XYZ(0, 0, h));
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}\"\"\"))

        # ESFR sprinkler (larger K-factor)
        samples.append(_s(
            "Create an ESFR (Early Suppression Fast Response) sprinkler family with 50mm pipe connector, K14 factor",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pKFactor = famMgr.AddParameter(
    "K-Factor", BuiltInParameterGroup.PG_MECHANICAL_FLOW, ParameterType.Number, false);
famMgr.Set(pKFactor, 14.0); // K14 ESFR

using (Transaction tx = new Transaction(familyDoc, "Create ESFR Sprinkler"))
{{
    tx.Start();

    double r = {ft(25)}; // larger head body
    double h = {ft(120)};
    int n = 16;
    CurveArray loop = new CurveArray();
    for (int i = 0; i < n; i++)
    {{
        double a0 = 2 * System.Math.PI * i / n;
        double a1 = 2 * System.Math.PI * (i + 1) / n;
        loop.Append(Line.CreateBound(
            new XYZ(r * System.Math.Cos(a0), r * System.Math.Sin(a0), 0),
            new XYZ(r * System.Math.Cos(a1), r * System.Math.Sin(a1), 0)));
    }}
    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.FireProtectWet,
        {ft(50)}, // 50 mm (2 inch) large orifice
        new XYZ(0, 0, h));
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}\"\"\"))

        # Sidewall sprinkler
        samples.append(_s(
            "Create a horizontal sidewall sprinkler family with a 25mm pipe connector oriented horizontally",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Sidewall Sprinkler"))
{{
    tx.Start();

    double r = {ft(12.5)};
    double h = {ft(80)};
    int n = 16;
    CurveArray loop = new CurveArray();
    for (int i = 0; i < n; i++)
    {{
        double a0 = 2 * System.Math.PI * i / n;
        double a1 = 2 * System.Math.PI * (i + 1) / n;
        loop.Append(Line.CreateBound(
            new XYZ(r * System.Math.Cos(a0), r * System.Math.Sin(a0), 0),
            new XYZ(r * System.Math.Cos(a1), r * System.Math.Sin(a1), 0)));
    }}
    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    // Sidewall: connector at side face, pointing in -Y direction (into wall pipe)
    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.FireProtectWet, {ft(25)},
        new XYZ(0, {ft(40)}, h / 2.0)); // offset to wall side
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}\"\"\"))

        return samples
"""

PLUMBING = f"""
    # ------------------------------------------------------------------
    # Plumbing fixtures
    # ------------------------------------------------------------------

    def _plumbing_fixtures(self) -> List[SAMPLE]:
        samples = []

        # Sink
        samples.append(_s(
            "Create a single-basin sink family with hot water, cold water, and drain pipe connectors",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Sink"))
{{
    tx.Start();

    // Sink body: 600x500x200mm
    double bw = {ft(600)}; double bd = {ft(500)}; double bh = {ft(200)};
    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2, -bd/2, 0), new XYZ( bw/2, -bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, -bd/2, 0), new XYZ( bw/2,  bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,  bd/2, 0), new XYZ(-bw/2,  bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2,  bd/2, 0), new XYZ(-bw/2, -bd/2, 0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    // Hot water supply (left side under sink)
    ConnectorElement hot = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticHotWater, {ft(15)}, // 15 mm (1/2" nom.)
        new XYZ(-{ft(100)}, -bd / 2, -bh / 2));
    hot.FlowDirection = FlowDirectionType.In;

    // Cold water supply (right side under sink)
    ConnectorElement cold = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticColdWater, {ft(15)},
        new XYZ( {ft(100)}, -bd / 2, -bh / 2));
    cold.FlowDirection = FlowDirectionType.In;

    // Drain (center bottom)
    ConnectorElement drain = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.Sanitary, {ft(40)}, // 40 mm (1-1/2" nom.)
        new XYZ(0, 0, -bh));
    drain.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        # Water closet (toilet)
        samples.append(_s(
            "Create a wall-hung water closet (toilet) family with cold water supply and sanitary drain connectors",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Water Closet"))
{{
    tx.Start();

    double bw = {ft(380)}; double bd = {ft(680)}; double bh = {ft(400)};
    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2, 0, 0),  new XYZ( bw/2, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, 0, 0),  new XYZ( bw/2, bd, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, bd, 0), new XYZ(-bw/2, bd, 0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2, bd, 0), new XYZ(-bw/2, 0, 0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    // Cold water flush valve supply (back wall)
    ConnectorElement cwSupply = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticColdWater, {ft(20)}, // 20 mm
        new XYZ(0, bd, {ft(250)})); // 250mm AFF back wall
    cwSupply.FlowDirection = FlowDirectionType.In;

    // Sanitary drain (rough-in at floor)
    ConnectorElement sanDrain = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.Sanitary, {ft(100)}, // 100 mm (4")
        new XYZ(0, {ft(200)}, 0)); // 200 mm from wall rough-in
    sanDrain.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        # Bathtub
        samples.append(_s(
            "Create a bathtub family with hot, cold water supply and drain/overflow connectors",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Bathtub"))
{{
    tx.Start();

    double bw = {ft(760)}; double bd = {ft(1520)}; double bh = {ft(430)};
    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2, 0, 0),  new XYZ( bw/2, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, 0, 0),  new XYZ( bw/2, bd, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, bd, 0), new XYZ(-bw/2, bd, 0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2, bd, 0), new XYZ(-bw/2, 0, 0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    // Hot supply (faucet end)
    ConnectorElement hot = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticHotWater, {ft(15)},
        new XYZ(-{ft(75)}, bd, {ft(200)}));
    hot.FlowDirection = FlowDirectionType.In;

    // Cold supply
    ConnectorElement cold = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticColdWater, {ft(15)},
        new XYZ( {ft(75)}, bd, {ft(200)}));
    cold.FlowDirection = FlowDirectionType.In;

    // Drain (foot end, near floor)
    ConnectorElement drain = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.Sanitary, {ft(40)},
        new XYZ(0, {ft(100)}, 0));
    drain.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        # Floor drain
        samples.append(_s(
            "Create a floor drain family with a 100mm sanitary drain connector and trap primer port",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Floor Drain"))
{{
    tx.Start();

    // Drain body: 200mm square
    double w = {ft(200)};
    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-w/2, -w/2, 0), new XYZ( w/2, -w/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, -w/2, 0), new XYZ( w/2,  w/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2,  w/2, 0), new XYZ(-w/2,  w/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-w/2,  w/2, 0), new XYZ(-w/2, -w/2, 0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, {ft(100)}); // 100 mm body

    // Main drain outlet (below floor)
    ConnectorElement drain = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.Sanitary, {ft(100)}, // 100 mm (4")
        new XYZ(0, 0, -{ft(100)})); // below body
    drain.FlowDirection = FlowDirectionType.Out;

    // Trap primer port (small cold water inlet)
    ConnectorElement trapPrime = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticColdWater, {ft(15)},
        new XYZ(w / 2, 0, -{ft(50)}));
    trapPrime.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}\"\"\"))

        # Urinal
        samples.append(_s(
            "Create a wall-hung urinal family with cold water supply and sanitary drain connectors",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Urinal"))
{{
    tx.Start();

    double bw = {ft(350)}; double bd = {ft(320)}; double bh = {ft(560)};
    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2, 0, 0),  new XYZ( bw/2, 0, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, 0, 0),  new XYZ( bw/2, bd, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, bd, 0), new XYZ(-bw/2, bd, 0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2, bd, 0), new XYZ(-bw/2, 0, 0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    // Flush valve supply (back wall, high)
    ConnectorElement cold = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticColdWater, {ft(20)},
        new XYZ(0, bd, bh * 0.9));
    cold.FlowDirection = FlowDirectionType.In;

    // Sanitary drain (below fixture)
    ConnectorElement drain = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.Sanitary, {ft(50)}, // 50 mm (2")
        new XYZ(0, {ft(100)}, 0));
    drain.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        # Shower base
        samples.append(_s(
            "Create a shower base family with hot/cold supply and drain connectors",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Shower Base"))
{{
    tx.Start();

    double bw = {ft(900)}; double bd = {ft(900)}; double bh = {ft(60)};
    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2, -bd/2, 0), new XYZ( bw/2, -bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, -bd/2, 0), new XYZ( bw/2,  bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,  bd/2, 0), new XYZ(-bw/2,  bd/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2,  bd/2, 0), new XYZ(-bw/2, -bd/2, 0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    ConnectorElement hot = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticHotWater, {ft(15)},
        new XYZ(-{ft(50)}, -bd / 2, bh + {ft(200)}));
    hot.FlowDirection = FlowDirectionType.In;

    ConnectorElement cold = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticColdWater, {ft(15)},
        new XYZ( {ft(50)}, -bd / 2, bh + {ft(200)}));
    cold.FlowDirection = FlowDirectionType.In;

    // Center drain
    ConnectorElement drain = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.Sanitary, {ft(50)},
        new XYZ(0, 0, 0));
    drain.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        return samples
"""

CONNECTOR_PARAMS = """
    # ------------------------------------------------------------------
    # Connector parameters
    # ------------------------------------------------------------------

    def _connector_parameters(self) -> List[SAMPLE]:
        samples = []

        samples.append(_s(
            "Set the domain of a connector to Piping using ConnectorDomain enumeration",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

// ConnectorDomain is read-only; it is determined by which Create method you use.
// CreatePipeConnector --> Domain = Piping
// CreateDuctConnector --> Domain = Hvac
// CreateElectricalConnector --> Domain = Electrical
// CreateConduitConnector --> Domain = Electrical

// To verify after creation:
using (Transaction tx = new Transaction(familyDoc, "Add Pipe Connector"))
{{
    tx.Start();

    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic,
        0.164042, // 50 mm
        XYZ.Zero);

    // Domain is automatically Piping
    // conn.Domain == Domain.DomainPiping
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Set a duct connector system type to ExhaustAir versus SupplyAir",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

// System type is set at creation time; use the correct DuctSystemType overload.
using (Transaction tx = new Transaction(familyDoc, "Add Exhaust Duct Connector"))
{{
    tx.Start();

    // ExhaustAir system type
    ConnectorElement exhaustConn = ConnectorElement.CreateDuctConnector(
        familyDoc,
        DuctSystemType.ExhaustAir,          // system type set here
        ConnectorProfileType.Rectangular,
        XYZ.Zero);
    exhaustConn.Width  = 1.312336; // 400 mm
    exhaustConn.Height = 0.656168; // 200 mm
    exhaustConn.FlowDirection = FlowDirectionType.Out; // exhaust flows out

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Associate a connector flow parameter to a family parameter so it drives from the type table",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

// Airflow family parameter (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pAirflow = famMgr.AddParameter(
    "Design Airflow",
    BuiltInParameterGroup.PG_MECHANICAL_AIRFLOW,
    ParameterType.AirFlow,
    false); // type parameter -- drives from type table
famMgr.Set(pAirflow, 0.5); // 0.5 m3/s default

using (Transaction tx = new Transaction(familyDoc, "Add Parametric Duct Connector"))
{{
    tx.Start();

    ConnectorElement conn = ConnectorElement.CreateDuctConnector(
        familyDoc,
        DuctSystemType.SupplyAir,
        ConnectorProfileType.Rectangular,
        XYZ.Zero);
    conn.Width  = 1.312336; // 400 mm
    conn.Height = 0.656168; // 200 mm
    conn.FlowDirection = FlowDirectionType.In;

    // Associate the connector flow parameter to the family parameter
    Parameter flowParam = conn.get_Parameter(BuiltInParameter.RBS_DUCT_FLOW_PARAM);
    if (flowParam != null && !flowParam.IsReadOnly)
        famMgr.AssociateElementParameterToFamilyParameter(flowParam, pAirflow);

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Set pressure drop parameters on a pipe connector for hydraulic calculations",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pPressureDrop = famMgr.AddParameter(
    "Pressure Drop",
    BuiltInParameterGroup.PG_MECHANICAL,
    ParameterType.PipingPressure,
    false);
famMgr.Set(pPressureDrop, 0.0); // Pa

using (Transaction tx = new Transaction(familyDoc, "Add Pipe Connector with Pressure Drop"))
{{
    tx.Start();

    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic,
        0.213255, // 65 mm
        XYZ.Zero);
    conn.FlowDirection = FlowDirectionType.In;

    Parameter pdParam = conn.get_Parameter(BuiltInParameter.RBS_PIPE_PRESSURE_DROP_PARAM);
    if (pdParam != null && !pdParam.IsReadOnly)
        famMgr.AssociateElementParameterToFamilyParameter(pdParam, pPressureDrop);

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Create a bidirectional pipe connector for an expansion tank or pressure gauge port",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Add Bidirectional Pipe Connector"))
{{
    tx.Start();

    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc,
        PipeSystemType.SupplyHydronic,
        0.082021, // 25 mm
        XYZ.Zero);

    // Bidirectional: flow can enter or leave (pressure/sensor ports)
    conn.FlowDirection = FlowDirectionType.Bidirectional;

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Enumerate all ConnectorElement objects in a family document to inspect their properties",
            \"\"\"\\
using Autodesk.Revit.DB;
using System.Linq;

// Collect all connector elements in the family
IList<Element> connectors = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(ConnectorElement))
    .ToElements();

foreach (ConnectorElement conn in connectors.Cast<ConnectorElement>())
{
    string info = "Connector Id=" + conn.Id.ToString() +
                  ", CoordinateSystemType=" + conn.CoordinateSystemType.ToString() +
                  ", FlowDirection=" + conn.FlowDirection.ToString();

    // Log or display connector info
    System.Diagnostics.Trace.WriteLine(info);
}
\"\"\"))

        samples.append(_s(
            "Set a duct connector velocity pressure parameter for system analysis",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pVelocity = famMgr.AddParameter(
    "Connector Velocity",
    BuiltInParameterGroup.PG_MECHANICAL,
    ParameterType.HVACVelocity,
    false);
famMgr.Set(pVelocity, 5.0); // 5 m/s default design velocity

using (Transaction tx = new Transaction(familyDoc, "Add Duct Connector with Velocity"))
{{
    tx.Start();

    ConnectorElement conn = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Round,
        XYZ.Zero);
    conn.Radius = 0.328084; // 200 mm dia
    conn.FlowDirection = FlowDirectionType.In;

    Parameter velParam = conn.get_Parameter(BuiltInParameter.RBS_DUCT_VELOCITY_PARAM);
    if (velParam != null && !velParam.IsReadOnly)
        famMgr.AssociateElementParameterToFamilyParameter(velParam, pVelocity);

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Create a connector with a specific coordinate system (connector face orientation) using SetCoordinateSystem",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

// Connector oriented to face +Y direction (used for side-exiting connectors)
using (Transaction tx = new Transaction(familyDoc, "Add Oriented Pipe Connector"))
{{
    tx.Start();

    double diameter = 0.164042; // 50 mm
    XYZ origin = new XYZ(0, 0.984252, 0); // 300 mm in Y

    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, diameter, origin);
    conn.FlowDirection = FlowDirectionType.Out;

    // Connector faces +Y: BasisZ of connector coordinate system = flow direction
    Transform t = Transform.Identity;
    t.Origin = origin;
    t.BasisX = XYZ.BasisX;          // connector local X
    t.BasisY = XYZ.BasisZ;          // connector local Y (up)
    t.BasisZ = XYZ.BasisY;          // connector faces +Y (flow out)
    conn.SetCoordinateSystem(t);

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Create multiple connectors with different system types in one family to represent a multi-service terminal",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;
using Autodesk.Revit.DB.Plumbing;

// Multi-service terminal: supply air + chilled water supply + chilled water return
using (Transaction tx = new Transaction(familyDoc, "Add Multi-Service Connectors"))
{{
    tx.Start();

    // Supply air outlet
    ConnectorElement air = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Round,
        new XYZ(0, 0, 1.312336)); // 400 mm
    air.Radius = 0.164042; // 100 mm dia
    air.FlowDirection = FlowDirectionType.Out;

    // Chilled water supply
    ConnectorElement cwsIn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, 0.082021, // 25 mm
        new XYZ(0.328084, 0, 0)); // 100 mm
    cwsIn.FlowDirection = FlowDirectionType.In;

    // Chilled water return
    ConnectorElement cwsOut = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.ReturnHydronic, 0.082021, // 25 mm
        new XYZ(0.492126, 0, 0)); // 150 mm
    cwsOut.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Read connector flow direction and system type from an existing connector element",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;
using System.Linq;

// Find existing pipe connectors in the family
var pipeConns = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(ConnectorElement))
    .Cast<ConnectorElement>()
    .Where(c => c.CoordinateSystemType == ConnectorCoordinateSystemType.Cylindrical)
    .ToList();

foreach (ConnectorElement conn in pipeConns)
{
    FlowDirectionType dir  = conn.FlowDirection;
    double radius = conn.Radius; // internal feet
    double radiusMm = radius * 304.8; // convert to mm

    System.Diagnostics.Trace.WriteLine(
        "Pipe connector: r=" + radiusMm.ToString("F1") + "mm, flow=" + dir.ToString());
}
\"\"\"))

        return samples
"""

path = r'C:/Users/JordanEhrig/Documents/GitHub/revit-family-engine/training_pipeline/generators/mep_family_generator.py'
with open(path, 'a', encoding='utf-8') as f:
    f.write(EQUIPMENT)
    f.write(ELECTRICAL)
    f.write(SPRINKLER)
    f.write(PLUMBING)
    f.write(CONNECTOR_PARAMS)

print('done')
