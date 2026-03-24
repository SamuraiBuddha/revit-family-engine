"""Inserts additional samples into each method of mep_family_generator.py
by replacing each method's 'return samples' with additional appends + return."""

MM_TO_FT = 1.0 / 304.8

def ft(mm):
    return round(mm * MM_TO_FT, 6)

path = r'C:/Users/JordanEhrig/Documents/GitHub/revit-family-engine/training_pipeline/generators/mep_family_generator.py'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# -----------------------------------------------------------------------
# Additional pipe connector samples (inject before last return in _pipe_connectors)
# -----------------------------------------------------------------------
PIPE_EXTRA = f"""
        # Additional pipe connector variants
        for sys_type, label, dia_mm in [
            ("ReturnHydronic",    "return hydronic",    65),
            ("SupplyHydronic",    "supply hydronic",   150),
            ("DomesticHotWater",  "domestic hot water", 20),
            ("DomesticColdWater", "domestic cold water",20),
            ("Sanitary",          "sanitary vent",      80),
            ("Vent",              "plumbing vent",      50),
            ("OtherPipe",         "chilled water",     100),
            ("FireProtectWet",    "fire protection wet",32),
            ("SupplyHydronic",    "condensate",         15),
            ("OtherPipe",         "compressed air",     25),
            ("OtherPipe",         "natural gas",        50),
            ("DomesticColdWater", "irrigation supply",  25),
            ("SupplyHydronic",    "heating hot water",  80),
            ("ReturnHydronic",    "heating return",     80),
            ("OtherPipe",         "fuel oil",           25),
        ]:
            dia_ft = round(dia_mm / 304.8, 6)
            samples.append(_s(
                f"Add a {{dia_mm}}mm {{label}} pipe connector to a Revit family",
                f\"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Add {{label.title()}} Connector"))
{{{{
    tx.Start();

    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc,
        PipeSystemType.{{sys_type}},
        {{dia_ft}}, // {{dia_mm}} mm
        XYZ.Zero);
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}}}\"\"\"))

"""

# -----------------------------------------------------------------------
# Additional duct connector samples
# -----------------------------------------------------------------------
DUCT_EXTRA = f"""
        # Additional duct connector variants
        for w_mm, h_mm, sys_type, label in [
            (500, 250, "SupplyAir",  "medium supply duct"),
            (300, 200, "ReturnAir",  "return duct branch"),
            (200, 200, "ExhaustAir", "toilet exhaust"),
            (400, 250, "SupplyAir",  "fan coil supply"),
            (600, 400, "ReturnAir",  "large return plenum"),
            (150, 150, "SupplyAir",  "small VAV branch"),
            (1000, 500, "SupplyAir", "large supply trunk"),
            (800, 300, "ReturnAir",  "return trunk"),
            (250, 200, "ExhaustAir", "kitchen exhaust"),
            (300, 150, "SupplyAir",  "ceiling diffuser neck"),
            (450, 225, "SupplyAir",  "medium supply"),
            (700, 350, "ReturnAir",  "medium return"),
            (200, 100, "ExhaustAir", "small exhaust branch"),
            (600, 200, "SupplyAir",  "flat wide supply"),
            (400, 400, "SupplyAir",  "square supply"),
            (350, 175, "ReturnAir",  "standard return"),
            (160, 160, "SupplyAir",  "square branch supply"),
            (500, 500, "ReturnAir",  "large square return"),
        ]:
            w_ft = round(w_mm / 304.8, 6)
            h_ft = round(h_mm / 304.8, 6)
            samples.append(_s(
                f"Add a {{w_mm}}x{{h_mm}}mm rectangular {{label}} duct connector",
                f\"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Add Duct Connector"))
{{{{
    tx.Start();

    ConnectorElement conn = ConnectorElement.CreateDuctConnector(
        familyDoc,
        DuctSystemType.{{sys_type}},
        ConnectorProfileType.Rectangular,
        XYZ.Zero);
    conn.Width  = {{w_ft}}; // {{w_mm}} mm
    conn.Height = {{h_ft}}; // {{h_mm}} mm
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}}}\"\"\"))

        # Additional round duct connector variants
        for dia_mm, sys_type, label in [
            (125, "SupplyAir",  "125mm round supply"),
            (250, "SupplyAir",  "250mm round supply"),
            (355, "ReturnAir",  "355mm round return"),
            (500, "ExhaustAir", "500mm round exhaust"),
            (450, "SupplyAir",  "450mm round supply"),
            (180, "SupplyAir",  "180mm round branch"),
            (560, "ReturnAir",  "560mm round return"),
            (710, "SupplyAir",  "710mm large round supply"),
        ]:
            dia_ft = round(dia_mm / 304.8, 6)
            samples.append(_s(
                f"Add a {{dia_mm}}mm round {{label}} duct connector",
                f\"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Add Round Duct Connector"))
{{{{
    tx.Start();

    ConnectorElement conn = ConnectorElement.CreateDuctConnector(
        familyDoc,
        DuctSystemType.{{sys_type}},
        ConnectorProfileType.Round,
        XYZ.Zero);
    conn.Radius = {{dia_ft}} / 2.0; // {{dia_mm}} mm dia
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}}}\"\"\"))

"""

# -----------------------------------------------------------------------
# Additional conduit connector samples
# -----------------------------------------------------------------------
CONDUIT_EXTRA = """
        # Additional conduit connector variants
        for dia_mm, desc in [
            (16,  "16mm conduit connector (1/2 inch trade size)"),
            (21,  "21mm conduit connector (3/4 inch trade size)"),
            (41,  "41mm conduit connector (1-1/2 inch trade size)"),
            (63,  "63mm conduit connector (2-1/2 inch trade size)"),
            (91,  "91mm conduit connector (3-1/2 inch trade size)"),
            (129, "129mm conduit connector (5 inch trade size)"),
            (155, "155mm conduit connector (6 inch trade size)"),
            (27,  "27mm surface raceway conduit connector"),
            (35,  "35mm wireway conduit connector"),
        ]:
            dia_ft = round(dia_mm / 304.8, 6)
            samples.append(_s(
                f"Add a {desc}",
                f\"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

using (Transaction tx = new Transaction(familyDoc, "Add Conduit Connector"))
{{{{
    tx.Start();

    ConnectorElement conn = ConnectorElement.CreateConduitConnector(
        familyDoc,
        {dia_ft}, // {dia_mm} mm
        XYZ.Zero);

    tx.Commit();
}}}}\"\"\"))

"""

# -----------------------------------------------------------------------
# Additional pipe fitting samples
# -----------------------------------------------------------------------
PIPE_FIT_EXTRA = """
        # Additional pipe fitting variants
        for angle_label, angle_expr, desc in [
            ("22.5", "Math.PI / 8.0",  "22.5-degree"),
            ("11.25","Math.PI / 16.0", "11.25-degree"),
        ]:
            samples.append(_s(
                f"Create a {angle_label}-degree pipe elbow fitting with 50mm connectors",
                f\"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;
using System;

using (Transaction tx = new Transaction(familyDoc, "Create {angle_label}-Degree Pipe Elbow"))
{{{{
    tx.Start();

    double diameter = 0.164042; // 50 mm
    double bendR    = 0.246063; // 75 mm bend radius
    double angle    = {angle_expr};

    ConnectorElement connA = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, diameter,
        new XYZ(0, 0, -bendR));
    connA.FlowDirection = FlowDirectionType.In;

    double bx = bendR * Math.Sin(angle);
    double bz = bendR * (1.0 - Math.Cos(angle));
    ConnectorElement connB = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, diameter,
        new XYZ(bx, 0, bz));
    connB.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}}}\"\"\"))

        # Fire protection tee
        samples.append(_s(
            "Create a fire protection pipe tee fitting, 50mm run and 32mm branch",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Fire Pipe Tee"))
{
    tx.Start();

    double runDiam    = 0.164042; // 50 mm
    double branchDiam = 0.104987; // 32 mm
    double halfLen    = 0.492126; // 150 mm

    ConnectorElement.CreatePipeConnector(familyDoc, PipeSystemType.FireProtectWet,
        runDiam, new XYZ(-halfLen, 0, 0)).FlowDirection = FlowDirectionType.In;
    ConnectorElement.CreatePipeConnector(familyDoc, PipeSystemType.FireProtectWet,
        runDiam, new XYZ( halfLen, 0, 0)).FlowDirection = FlowDirectionType.Out;
    ConnectorElement.CreatePipeConnector(familyDoc, PipeSystemType.FireProtectWet,
        branchDiam, new XYZ(0, 0, 0.344488)).FlowDirection = FlowDirectionType.Out; // 105 mm

    tx.Commit();
}\"\"\"))

        # Sanitary tee (P-trap outlet)
        samples.append(_s(
            "Create a sanitary tee fitting with 100mm sanitary connectors",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Sanitary Tee"))
{
    tx.Start();

    double d = 0.328084; // 100 mm
    double h = 0.492126; // 150 mm

    ConnectorElement.CreatePipeConnector(familyDoc, PipeSystemType.Sanitary,
        d, new XYZ(-h, 0, 0)).FlowDirection = FlowDirectionType.In;
    ConnectorElement.CreatePipeConnector(familyDoc, PipeSystemType.Sanitary,
        d, new XYZ( h, 0, 0)).FlowDirection = FlowDirectionType.Out;
    ConnectorElement.CreatePipeConnector(familyDoc, PipeSystemType.Sanitary,
        d, new XYZ(0, 0, h)).FlowDirection = FlowDirectionType.In;

    tx.Commit();
}\"\"\"))

        # Sweep elbow (long radius, 1.5D)
        samples.append(_s(
            "Create a long-radius (1.5D) 90-degree pipe elbow fitting, 100mm",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Long Radius Elbow 100mm"))
{
    tx.Start();

    double d = 0.328084; // 100 mm
    double r = 0.492126; // 150 mm (1.5D)

    ConnectorElement connA = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, d, new XYZ(0, 0, -r));
    connA.FlowDirection = FlowDirectionType.In;

    ConnectorElement connB = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, d, new XYZ(r, 0, 0));
    connB.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}\"\"\"))

        # Short radius elbow (1D)
        samples.append(_s(
            "Create a short-radius (1D) 90-degree pipe elbow fitting, 100mm",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Short Radius Elbow 100mm"))
{
    tx.Start();

    double d = 0.328084; // 100 mm
    double r = 0.328084; // 100 mm (1D)

    ConnectorElement connA = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, d, new XYZ(0, 0, -r));
    connA.FlowDirection = FlowDirectionType.In;

    ConnectorElement connB = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, d, new XYZ(r, 0, 0));
    connB.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}\"\"\"))

        # Manifold (4-port)
        samples.append(_s(
            "Create a 4-port hydronic manifold fitting with one 100mm inlet and three 25mm branch outlets",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Hydronic Manifold"))
{
    tx.Start();

    double mainDiam   = 0.328084; // 100 mm
    double branchDiam = 0.082021; // 25 mm
    double halfRun    = 0.656168; // 200 mm
    double spacing    = 0.196850; // 60 mm branch spacing

    // Main inlet
    ConnectorElement mainIn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, mainDiam,
        new XYZ(-halfRun, 0, 0));
    mainIn.FlowDirection = FlowDirectionType.In;

    // Three branch outlets (spaced 60mm apart along X)
    for (int i = 0; i < 3; i++)
    {
        ConnectorElement branch = ConnectorElement.CreatePipeConnector(
            familyDoc, PipeSystemType.SupplyHydronic, branchDiam,
            new XYZ(-spacing + i * spacing, 0, 0.164042)); // 50mm above
        branch.FlowDirection = FlowDirectionType.Out;
    }

    tx.Commit();
}\"\"\"))

        # Ball valve body stub
        samples.append(_s(
            "Create a ball valve family with two 65mm pipe connectors (full bore, inline)",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Ball Valve"))
{
    tx.Start();

    double d       = 0.213255; // 65 mm
    double halfLen = 0.262467; // 80 mm body half-length

    ConnectorElement inlet = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, d,
        new XYZ(0, 0, -halfLen));
    inlet.FlowDirection = FlowDirectionType.In;

    ConnectorElement outlet = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, d,
        new XYZ(0, 0,  halfLen));
    outlet.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}\"\"\"))

        # Strainer Y-body
        samples.append(_s(
            "Create a Y-strainer pipe fitting with 80mm inline connectors and a blowdown port",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Y-Strainer"))
{
    tx.Start();

    double d       = 0.262467; // 80 mm inline
    double halfLen = 0.393701; // 120 mm

    ConnectorElement inlet = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, d, new XYZ(0, 0, -halfLen));
    inlet.FlowDirection = FlowDirectionType.In;

    ConnectorElement outlet = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, d, new XYZ(0, 0,  halfLen));
    outlet.FlowDirection = FlowDirectionType.Out;

    // Blowdown port at 45 degrees down
    ConnectorElement blowdown = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.OtherPipe, 0.082021, // 25 mm
        new XYZ(0, -0.196850, -0.196850)); // 60mm offset
    blowdown.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}\"\"\"))

"""

# -----------------------------------------------------------------------
# Additional duct fitting samples
# -----------------------------------------------------------------------
DUCT_FIT_EXTRA = """
        # Additional duct fitting variants
        # Duct cross (4-way)
        samples.append(_s(
            "Create a rectangular duct cross (4-way) fitting, 500x250mm",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Duct Cross"))
{
    tx.Start();

    double w = 1.640420; // 500 mm
    double h = 0.820210; // 250 mm
    double arm = 1.312336; // 400 mm arm

    ConnectorElement.CreateDuctConnector(familyDoc, DuctSystemType.SupplyAir,
        ConnectorProfileType.Rectangular, new XYZ(-arm, 0, 0))
        .Width = w;
    ConnectorElement.CreateDuctConnector(familyDoc, DuctSystemType.SupplyAir,
        ConnectorProfileType.Rectangular, new XYZ( arm, 0, 0))
        .Width = w;
    ConnectorElement.CreateDuctConnector(familyDoc, DuctSystemType.SupplyAir,
        ConnectorProfileType.Rectangular, new XYZ(0, -arm, 0))
        .Width = w;
    ConnectorElement.CreateDuctConnector(familyDoc, DuctSystemType.SupplyAir,
        ConnectorProfileType.Rectangular, new XYZ(0,  arm, 0))
        .Width = w;

    tx.Commit();
}\"\"\"))

        # Round-to-round reducer
        samples.append(_s(
            "Create a concentric round duct reducer, 400mm to 315mm diameter",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Round Duct Reducer"))
{
    tx.Start();

    double length = 0.984252; // 300 mm

    ConnectorElement largeEnd = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Round, XYZ.Zero);
    largeEnd.Radius = 0.656168; // 400 mm dia
    largeEnd.FlowDirection = FlowDirectionType.In;

    ConnectorElement smallEnd = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Round,
        new XYZ(0, 0, length));
    smallEnd.Radius = 0.516732; // 315 mm dia
    smallEnd.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}\"\"\"))

        # Exhaust fan discharge fitting
        samples.append(_s(
            "Create an exhaust fan discharge fitting with round inlet and rectangular outlet, 315mm to 400x200mm",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Fan Discharge Fitting"))
{
    tx.Start();

    // Round inlet (from fan)
    ConnectorElement roundIn = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.ExhaustAir, ConnectorProfileType.Round, XYZ.Zero);
    roundIn.Radius = 0.516732; // 315 mm dia
    roundIn.FlowDirection = FlowDirectionType.In;

    // Rectangular outlet (to ductwork)
    ConnectorElement rectOut = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.ExhaustAir, ConnectorProfileType.Rectangular,
        new XYZ(0, 0, 0.656168)); // 200 mm transition length
    rectOut.Width  = 1.312336; // 400 mm
    rectOut.Height = 0.656168; // 200 mm
    rectOut.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}\"\"\"))

        # Duct boot (floor/wall diffuser connection)
        samples.append(_s(
            "Create a duct boot fitting transitioning from a round duct to a floor register opening",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

// Duct boot: round duct inlet, rectangular floor register outlet
using (Transaction tx = new Transaction(familyDoc, "Create Duct Boot"))
{
    tx.Start();

    ConnectorElement roundIn = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Round,
        new XYZ(0, 0, 0.656168)); // 200 mm above floor
    roundIn.Radius = 0.262467; // 160 mm dia
    roundIn.FlowDirection = FlowDirectionType.In;

    ConnectorElement rectOut = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        XYZ.Zero); // at floor level
    rectOut.Width  = 0.820210; // 250 mm
    rectOut.Height = 0.328084; // 100 mm
    rectOut.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}\"\"\"))

        # Multi-way volume damper stub
        samples.append(_s(
            "Create a duct balancing damper body with inlet and outlet duct connectors, 400x200mm",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pPosition = famMgr.AddParameter(
    "Damper Position",
    BuiltInParameterGroup.PG_MECHANICAL,
    ParameterType.Number,
    true); // instance -- position varies
famMgr.Set(pPosition, 100.0); // 100% open

using (Transaction tx = new Transaction(familyDoc, "Create Volume Damper"))
{
    tx.Start();

    double w = 1.312336; // 400 mm
    double h = 0.656168; // 200 mm
    double bodyLen = 0.656168; // 200 mm body

    ConnectorElement inlet = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        XYZ.Zero);
    inlet.Width = w; inlet.Height = h;
    inlet.FlowDirection = FlowDirectionType.In;

    ConnectorElement outlet = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ(0, 0, bodyLen));
    outlet.Width = w; outlet.Height = h;
    outlet.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}\"\"\"))

        # Duct flex connection stub
        samples.append(_s(
            "Create a flexible duct connection fitting with two round connectors, 200mm diameter",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pFlexLen = famMgr.AddParameter(
    "Flex Length",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length,
    true); // instance
famMgr.Set(pFlexLen, 0.984252); // 300 mm default

using (Transaction tx = new Transaction(familyDoc, "Create Flex Duct Stub"))
{
    tx.Start();

    double r = 0.328084; // 200 mm dia
    double len = 0.984252; // 300 mm

    ConnectorElement connA = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Round, XYZ.Zero);
    connA.Radius = r / 2.0;
    connA.FlowDirection = FlowDirectionType.In;

    ConnectorElement connB = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Round,
        new XYZ(0, 0, len));
    connB.Radius = r / 2.0;
    connB.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}\"\"\"))

        # Duct silencer stub
        samples.append(_s(
            "Create a duct silencer (sound attenuator) body with 600x300mm rectangular connectors",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pSilencerLen = famMgr.AddParameter(
    "Silencer Length",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length,
    false);
famMgr.Set(pSilencerLen, 3.280840); // 1000 mm

using (Transaction tx = new Transaction(familyDoc, "Create Duct Silencer"))
{
    tx.Start();

    double w = 1.968504; // 600 mm
    double h = 0.984252; // 300 mm
    double bodyLen = 3.280840; // 1000 mm

    ConnectorElement inlet = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular, XYZ.Zero);
    inlet.Width = w; inlet.Height = h;
    inlet.FlowDirection = FlowDirectionType.In;

    ConnectorElement outlet = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ(0, 0, bodyLen));
    outlet.Width = w; outlet.Height = h;
    outlet.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}\"\"\"))

"""

# -----------------------------------------------------------------------
# Additional equipment samples
# -----------------------------------------------------------------------
EQUIP_EXTRA = """
        # Additional equipment variants
        # Plate-and-frame heat exchanger
        samples.append(_s(
            "Create a domestic hot water heater family with cold water inlet, hot water outlet, and flue connector",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Water Heater"))
{
    tx.Start();

    // Tank body: 500mm dia cylinder, 1200mm tall
    double r = 0.820210; // 500 mm dia
    double h = 3.937008; // 1200 mm
    int n = 24;
    CurveArray loop = new CurveArray();
    for (int i = 0; i < n; i++)
    {
        double a0 = 2 * System.Math.PI * i / n;
        double a1 = 2 * System.Math.PI * (i + 1) / n;
        loop.Append(Line.CreateBound(
            new XYZ(r * System.Math.Cos(a0), r * System.Math.Sin(a0), 0),
            new XYZ(r * System.Math.Cos(a1), r * System.Math.Sin(a1), 0)));
    }
    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    // Cold water inlet (bottom)
    ConnectorElement cwIn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticColdWater, 0.082021, // 25 mm
        new XYZ(0.25, 0, 0.328084)); // 100 mm up
    cwIn.FlowDirection = FlowDirectionType.In;

    // Hot water outlet (top)
    ConnectorElement hwOut = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticHotWater, 0.082021, // 25 mm
        new XYZ(-0.25, 0, h - 0.328084));
    hwOut.FlowDirection = FlowDirectionType.Out;

    // Flue gas outlet (top center)
    ConnectorElement flue = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.ExhaustAir, ConnectorProfileType.Round,
        new XYZ(0, 0, h));
    flue.Radius = 0.246063; // 150 mm dia
    flue.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}\"\"\"))

        # Variable refrigerant flow (VRF) indoor unit
        samples.append(_s(
            "Create a VRF indoor cassette unit family with refrigerant pipe connectors and supply/return air duct connectors",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create VRF Indoor Unit"))
{
    tx.Start();

    double bw = 0.984252; double bd = 0.984252; double bh = 0.098425; // 840x840x30mm

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2,-bd/2,0), new XYZ( bw/2,-bd/2,0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,-bd/2,0), new XYZ( bw/2, bd/2,0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, bd/2,0), new XYZ(-bw/2, bd/2,0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2, bd/2,0), new XYZ(-bw/2,-bd/2,0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    // Refrigerant liquid line (small bore)
    ConnectorElement liqLine = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.OtherPipe, 0.032808, // 10 mm liquid line
        new XYZ(-0.25, -bd/2, bh));
    liqLine.FlowDirection = FlowDirectionType.In;

    // Refrigerant gas/suction line (larger bore)
    ConnectorElement gasLine = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.OtherPipe, 0.065617, // 20 mm gas line
        new XYZ( 0.25, -bd/2, bh));
    gasLine.FlowDirection = FlowDirectionType.Out;

    // Condensate drain
    ConnectorElement drain = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.Sanitary, 0.049213, // 15 mm condensate
        new XYZ(0, bd/2, bh));
    drain.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}\"\"\"))

        # Pressure reducing valve (PRV) station
        samples.append(_s(
            "Create a pressure reducing valve (PRV) station family with high-pressure inlet and reduced-pressure outlet",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pSetPoint = famMgr.AddParameter(
    "Set Point Pressure",
    BuiltInParameterGroup.PG_MECHANICAL,
    ParameterType.PipingPressure,
    false);
famMgr.Set(pSetPoint, 300000.0); // 300 kPa set point

using (Transaction tx = new Transaction(familyDoc, "Create PRV Station"))
{
    tx.Start();

    // Body: 400x200x300mm box
    double bw = 1.312336; double bd = 0.656168; double bh = 0.984252;
    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2,-bd/2,0), new XYZ( bw/2,-bd/2,0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,-bd/2,0), new XYZ( bw/2, bd/2,0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, bd/2,0), new XYZ(-bw/2, bd/2,0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2, bd/2,0), new XYZ(-bw/2,-bd/2,0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    // High-pressure inlet
    ConnectorElement hiIn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, 0.262467, // 80 mm
        new XYZ(-bw/2, 0, bh/2));
    hiIn.FlowDirection = FlowDirectionType.In;

    // Reduced-pressure outlet
    ConnectorElement loOut = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, 0.213255, // 65 mm
        new XYZ( bw/2, 0, bh/2));
    loOut.FlowDirection = FlowDirectionType.Out;

    // Relief valve port (small)
    ConnectorElement relief = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.OtherPipe, 0.082021, // 25 mm
        new XYZ(0, 0, bh));
    relief.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}\"\"\"))

        # Pump with VFD parameter
        samples.append(_s(
            "Create a variable speed pump family with inlet/outlet pipe connectors and speed parameter",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pSpeed = famMgr.AddParameter(
    "Design Speed",
    BuiltInParameterGroup.PG_MECHANICAL,
    ParameterType.Number,
    false);
famMgr.Set(pSpeed, 100.0); // 100% speed

FamilyParameter pFlow = famMgr.AddParameter(
    "Design Flow",
    BuiltInParameterGroup.PG_MECHANICAL_FLOW,
    ParameterType.PipeFlow,
    false);
famMgr.Set(pFlow, 0.01); // 10 L/s

using (Transaction tx = new Transaction(familyDoc, "Create Variable Speed Pump"))
{
    tx.Start();

    double bw = 0.984252; double bd = 0.656168; double bh = 0.820210;

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2,-bd/2,0), new XYZ( bw/2,-bd/2,0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,-bd/2,0), new XYZ( bw/2, bd/2,0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, bd/2,0), new XYZ(-bw/2, bd/2,0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2, bd/2,0), new XYZ(-bw/2,-bd/2,0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    ConnectorElement suction = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, 0.262467, // 80 mm
        new XYZ(-bw/2, 0, bh/2));
    suction.FlowDirection = FlowDirectionType.In;

    ConnectorElement discharge = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, 0.213255, // 65 mm
        new XYZ( bw/2, 0, bh/2));
    discharge.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}\"\"\"))

"""

# -----------------------------------------------------------------------
# Additional electrical samples
# -----------------------------------------------------------------------
ELEC_EXTRA = """
        # Additional electrical fixture variants
        samples.append(_s(
            "Create a wall-mounted sconce fixture family with 120V single-phase electrical connector",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

using (Transaction tx = new Transaction(familyDoc, "Create Wall Sconce"))
{
    tx.Start();

    double bw = 0.492126; // 150 mm
    double bd = 0.196850; // 60 mm
    double bh = 0.328084; // 100 mm

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2,0,0),  new XYZ( bw/2,0,0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,0,0),  new XYZ( bw/2,bd,0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,bd,0), new XYZ(-bw/2,bd,0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2,bd,0), new XYZ(-bw/2,0,0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    ConnectorElement conn = ConnectorElement.CreateElectricalConnector(
        familyDoc, ElectricalSystemType.PowerBalanced,
        new XYZ(0, 0, bh));
    conn.Voltage = 120.0;
    conn.WiringType = WiringType.SinglePhase;

    tx.Commit();
}\"\"\"))

        samples.append(_s(
            "Create an outdoor area light pole family with 240V single-phase electrical connector",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

using (Transaction tx = new Transaction(familyDoc, "Create Area Light Pole"))
{
    tx.Start();

    // Pole: 150mm dia, 8000mm tall
    double r = 0.246063; // 75 mm radius
    double h = 26.246719; // 8000 mm
    int n = 16;
    CurveArray loop = new CurveArray();
    for (int i = 0; i < n; i++)
    {
        double a0 = 2 * System.Math.PI * i / n;
        double a1 = 2 * System.Math.PI * (i + 1) / n;
        loop.Append(Line.CreateBound(
            new XYZ(r * System.Math.Cos(a0), r * System.Math.Sin(a0), 0),
            new XYZ(r * System.Math.Cos(a1), r * System.Math.Sin(a1), 0)));
    }
    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    // Base electrical connector
    ConnectorElement conn = ConnectorElement.CreateElectricalConnector(
        familyDoc, ElectricalSystemType.PowerBalanced, XYZ.Zero);
    conn.Voltage = 240.0;
    conn.WiringType = WiringType.SinglePhase;

    tx.Commit();
}\"\"\"))

        samples.append(_s(
            "Create a track lighting track family with a 120V circuit electrical connector and multiple fixture slots",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pTrackLen = famMgr.AddParameter(
    "Track Length",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length,
    false);
famMgr.Set(pTrackLen, 2.952756); // 900 mm

using (Transaction tx = new Transaction(familyDoc, "Create Lighting Track"))
{
    tx.Start();

    double trackLen = 2.952756; // 900 mm
    double trackW   = 0.114829; // 35 mm
    double trackH   = 0.098425; // 30 mm

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-trackLen/2,-trackW/2,0), new XYZ( trackLen/2,-trackW/2,0)));
    loop.Append(Line.CreateBound(new XYZ( trackLen/2,-trackW/2,0), new XYZ( trackLen/2, trackW/2,0)));
    loop.Append(Line.CreateBound(new XYZ( trackLen/2, trackW/2,0), new XYZ(-trackLen/2, trackW/2,0)));
    loop.Append(Line.CreateBound(new XYZ(-trackLen/2, trackW/2,0), new XYZ(-trackLen/2,-trackW/2,0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, trackH);

    // Feed connector at one end
    ConnectorElement feed = ConnectorElement.CreateElectricalConnector(
        familyDoc, ElectricalSystemType.PowerBalanced,
        new XYZ(-trackLen/2, 0, trackH));
    feed.Voltage = 120.0;
    feed.WiringType = WiringType.SinglePhase;

    tx.Commit();
}\"\"\"))

        samples.append(_s(
            "Create a motor control center (MCC) bucket family with 480V 3-phase electrical connector",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pHP = famMgr.AddParameter(
    "Motor HP",
    BuiltInParameterGroup.PG_ELECTRICAL,
    ParameterType.Number,
    false);
famMgr.Set(pHP, 25.0); // 25 HP

using (Transaction tx = new Transaction(familyDoc, "Create MCC Bucket"))
{
    tx.Start();

    double bw = 0.656168; // 200 mm
    double bd = 0.328084; // 100 mm
    double bh = 1.312336; // 400 mm

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2,0,0), new XYZ( bw/2,0,0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,0,0), new XYZ( bw/2,bd,0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,bd,0),new XYZ(-bw/2,bd,0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2,bd,0),new XYZ(-bw/2,0,0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    ConnectorElement conn = ConnectorElement.CreateElectricalConnector(
        familyDoc, ElectricalSystemType.PowerBalanced,
        new XYZ(0, bd/2, bh));
    conn.Voltage = 480.0;
    conn.WiringType = WiringType.ThreePhase;

    tx.Commit();
}\"\"\"))

        samples.append(_s(
            "Create a GFCI outlet family with 120V 20A electrical connector and a TEST/RESET annotation",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pAmpere = famMgr.AddParameter(
    "Circuit Breaker Rating",
    BuiltInParameterGroup.PG_ELECTRICAL,
    ParameterType.ElectricalCurrent,
    false);
famMgr.Set(pAmpere, 20.0); // 20A

using (Transaction tx = new Transaction(familyDoc, "Create GFCI Outlet"))
{
    tx.Start();

    double bw = 0.229659; // 70 mm
    double bd = 0.098425; // 30 mm
    double bh = 0.393701; // 120 mm

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2,0,0), new XYZ( bw/2,0,0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,0,0), new XYZ( bw/2,bd,0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,bd,0),new XYZ(-bw/2,bd,0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2,bd,0),new XYZ(-bw/2,0,0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    ConnectorElement conn = ConnectorElement.CreateElectricalConnector(
        familyDoc, ElectricalSystemType.PowerBalanced,
        new XYZ(0, bd, bh/2));
    conn.Voltage = 120.0;
    conn.WiringType = WiringType.SinglePhase;

    tx.Commit();
}\"\"\"))

"""

# -----------------------------------------------------------------------
# Additional sprinkler samples
# -----------------------------------------------------------------------
SPRINKLER_EXTRA = """
        # Additional sprinkler variants
        for k_factor, dia_mm, label in [
            (8.0,  25, "K8.0 standard response sprinkler"),
            (11.2, 32, "K11.2 large orifice sprinkler"),
            (16.8, 40, "K16.8 extra large orifice sprinkler"),
            (5.6,  25, "K5.6 quick response sprinkler"),
            (5.6,  25, "K5.6 pendent extended coverage sprinkler"),
            (8.0,  25, "K8.0 horizontal sidewall sprinkler"),
            (11.2, 32, "K11.2 upright sprinkler"),
            (14.0, 40, "K14.0 ESFR upright sprinkler"),
        ]:
            dia_ft = round(dia_mm / 304.8, 6)
            samples.append(_s(
                f"Create a {label} family with {dia_mm}mm pipe connector and K={k_factor} parameter",
                f\"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pK = famMgr.AddParameter(
    "K-Factor", BuiltInParameterGroup.PG_MECHANICAL_FLOW, ParameterType.Number, false);
famMgr.Set(pK, {k_factor});

using (Transaction tx = new Transaction(familyDoc, "Create Sprinkler"))
{{{{
    tx.Start();

    double r = {round(dia_mm/2.0/304.8,6)}; // {dia_mm/2} mm radius
    double h = 0.328084; // 100 mm body height
    int n = 16;
    CurveArray loop = new CurveArray();
    for (int i = 0; i < n; i++)
    {{{{
        double a0 = 2 * System.Math.PI * i / n;
        double a1 = 2 * System.Math.PI * (i + 1) / n;
        loop.Append(Line.CreateBound(
            new XYZ(r * System.Math.Cos(a0), r * System.Math.Sin(a0), 0),
            new XYZ(r * System.Math.Cos(a1), r * System.Math.Sin(a1), 0)));
    }}}}
    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.FireProtectWet,
        {dia_ft}, // {dia_mm} mm
        new XYZ(0, 0, h));
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}}}\"\"\"))

"""

# -----------------------------------------------------------------------
# Additional plumbing samples
# -----------------------------------------------------------------------
PLUMBING_EXTRA = """
        # Additional plumbing fixture variants
        # Utility sink
        samples.append(_s(
            "Create a utility (mop) sink family with hot/cold supply and 75mm drain connector",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Utility Sink"))
{
    tx.Start();

    double bw = 1.640420; // 500 mm
    double bd = 1.640420; // 500 mm
    double bh = 0.820210; // 250 mm

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2,-bd/2,0),new XYZ( bw/2,-bd/2,0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,-bd/2,0),new XYZ( bw/2, bd/2,0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, bd/2,0),new XYZ(-bw/2, bd/2,0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2, bd/2,0),new XYZ(-bw/2,-bd/2,0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    ConnectorElement hot = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticHotWater, 0.049213, // 15 mm
        new XYZ(-0.25, -bd/2, bh/2));
    hot.FlowDirection = FlowDirectionType.In;

    ConnectorElement cold = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticColdWater, 0.049213, // 15 mm
        new XYZ( 0.25, -bd/2, bh/2));
    cold.FlowDirection = FlowDirectionType.In;

    ConnectorElement drain = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.Sanitary, 0.246063, // 75 mm
        new XYZ(0, 0, 0));
    drain.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}\"\"\"))

        # Drinking fountain
        samples.append(_s(
            "Create a wall-mounted drinking fountain family with cold water supply and drain connectors",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Drinking Fountain"))
{
    tx.Start();

    double bw = 0.984252; double bd = 0.656168; double bh = 0.492126;

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2,0,0),  new XYZ( bw/2,0,0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,0,0),  new XYZ( bw/2,bd,0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,bd,0), new XYZ(-bw/2,bd,0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2,bd,0), new XYZ(-bw/2,0,0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    ConnectorElement cold = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticColdWater, 0.049213, // 15 mm
        new XYZ(0, bd, bh/2));
    cold.FlowDirection = FlowDirectionType.In;

    ConnectorElement drain = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.Sanitary, 0.082021, // 25 mm
        new XYZ(0, bd/2, 0));
    drain.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}\"\"\"))

        # Laundry tub
        samples.append(_s(
            "Create a laundry tub family with hot/cold supply, 50mm drain, and standpipe for washer",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Laundry Tub"))
{
    tx.Start();

    double bw = 1.968504; double bd = 1.640420; double bh = 0.820210;

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2,-bd/2,0),new XYZ( bw/2,-bd/2,0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,-bd/2,0),new XYZ( bw/2, bd/2,0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, bd/2,0),new XYZ(-bw/2, bd/2,0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2, bd/2,0),new XYZ(-bw/2,-bd/2,0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    ConnectorElement hot = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticHotWater, 0.049213, // 15 mm
        new XYZ(-0.25, -bd/2, bh * 0.6));
    hot.FlowDirection = FlowDirectionType.In;

    ConnectorElement cold = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticColdWater, 0.049213, // 15 mm
        new XYZ( 0.25, -bd/2, bh * 0.6));
    cold.FlowDirection = FlowDirectionType.In;

    ConnectorElement drain = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.Sanitary, 0.164042, // 50 mm
        new XYZ(0, 0, 0));
    drain.FlowDirection = FlowDirectionType.Out;

    // Washer standpipe (accepts machine drain hose)
    ConnectorElement standpipe = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.Sanitary, 0.082021, // 25 mm
        new XYZ(0.5, -bd/2, bh));
    standpipe.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}\"\"\"))

        # Hose bib / sill cock
        samples.append(_s(
            "Create a hose bib (sill cock) family with a 15mm cold water pipe connector",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Hose Bib"))
{
    tx.Start();

    // Body: small 80mm dia disc, 80mm deep
    double r = 0.131234; // 40 mm radius
    double h = 0.262467; // 80 mm
    int n = 16;
    CurveArray loop = new CurveArray();
    for (int i = 0; i < n; i++)
    {
        double a0 = 2 * System.Math.PI * i / n;
        double a1 = 2 * System.Math.PI * (i + 1) / n;
        loop.Append(Line.CreateBound(
            new XYZ(r * System.Math.Cos(a0), r * System.Math.Sin(a0), 0),
            new XYZ(r * System.Math.Cos(a1), r * System.Math.Sin(a1), 0)));
    }
    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    // Cold water inlet at back
    ConnectorElement cold = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticColdWater, 0.049213, // 15 mm
        new XYZ(0, 0, h));
    cold.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}\"\"\"))

        # Condensate drain pan
        samples.append(_s(
            "Create a condensate drain pan family for a split system, with a 20mm sanitary drain connector",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Condensate Drain Pan"))
{
    tx.Start();

    double bw = 2.952756; double bd = 1.640420; double bh = 0.164042; // 900x500x50mm

    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-bw/2,-bd/2,0),new XYZ( bw/2,-bd/2,0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2,-bd/2,0),new XYZ( bw/2, bd/2,0)));
    loop.Append(Line.CreateBound(new XYZ( bw/2, bd/2,0),new XYZ(-bw/2, bd/2,0)));
    loop.Append(Line.CreateBound(new XYZ(-bw/2, bd/2,0),new XYZ(-bw/2,-bd/2,0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, bh);

    // Condensate outlet at corner
    ConnectorElement drain = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.Sanitary, 0.065617, // 20 mm
        new XYZ(-bw/2 + 0.164042, -bd/2 + 0.164042, 0));
    drain.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}\"\"\"))

"""

# -----------------------------------------------------------------------
# Now perform the injections
# The strategy: replace "        return samples\n" in each method with
# the extra content + "        return samples\n"
# We must do it from bottom to top so line numbers don't shift.
# -----------------------------------------------------------------------

# Find method boundaries using unique surrounding text
injections = [
    # (unique text just before "return samples" in that method, extra content)
    (
        # _pipe_connectors last unique line before return
        '        samples.append(_s(\n            f"Add a parametric pipe connector whose diameter is controlled',
        PIPE_EXTRA,
    ),
    (
        '        samples.append(_s(\n            "Add an oval duct connector',
        DUCT_EXTRA,
    ),
    (
        '        samples.append(_s(\n            "Create a conduit connector whose diameter is controlled',
        CONDUIT_EXTRA,
    ),
    (
        'samples.append(_s(\n            "Add a flexible pipe connector stub',
        PIPE_FIT_EXTRA,
    ),
    (
        '        samples.append(_s(\n            "Create a 90-degree rectangular duct elbow, 500x300mm',
        DUCT_FIT_EXTRA,
    ),
    (
        '        samples.append(_s(\n            "Create a cooling tower family',
        EQUIP_EXTRA,
    ),
    (
        '        samples.append(_s(\n            "Create a smoke detector family',
        ELEC_EXTRA,
    ),
    (
        '        samples.append(_s(\n            "Create a horizontal sidewall sprinkler family',
        SPRINKLER_EXTRA,
    ),
    (
        '        samples.append(_s(\n            "Create a shower base family',
        PLUMBING_EXTRA,
    ),
]

for anchor, extra in injections:
    if anchor in content:
        # Find the next "        return samples" after this anchor
        anchor_pos = content.find(anchor)
        return_pos = content.find('\n        return samples\n', anchor_pos)
        if return_pos != -1:
            insert_at = return_pos + 1  # after the newline before 'return'
            content = content[:insert_at] + extra + content[insert_at:]
            print(f'Injected after anchor: {anchor[:60]!r}')
        else:
            print(f'WARNING: return samples not found after anchor: {anchor[:60]!r}')
    else:
        print(f'WARNING: anchor not found: {anchor[:60]!r}')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('done writing file')
