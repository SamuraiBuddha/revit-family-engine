"""One-shot helper: appends remaining methods to mep_family_generator.py, then deletes itself."""
import os

MM_TO_FT = 1.0 / 304.8

def ft(mm):
    return f"{mm * MM_TO_FT:.6f}"

PIPE_FITTINGS = f"""
    # ------------------------------------------------------------------
    # Pipe fittings
    # ------------------------------------------------------------------

    def _pipe_fittings(self) -> List[SAMPLE]:
        samples = []

        samples.append(_s(
            "Create a 90-degree pipe elbow fitting family with 50mm pipe connectors",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pNomDiam = famMgr.AddParameter(
    "Nominal Diameter",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length,
    false);
famMgr.Set(pNomDiam, {ft(50)}); // 50 mm

FamilyParameter pBendRadius = famMgr.AddParameter(
    "Bend Radius",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length,
    false);
famMgr.Set(pBendRadius, {ft(75)}); // 75 mm (1.5D)

using (Transaction tx = new Transaction(familyDoc, "Create Pipe Elbow"))
{{
    tx.Start();

    double diameter = {ft(50)};  // 50 mm
    double bendR    = {ft(75)};  // 75 mm bend radius

    ConnectorElement connA = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, diameter,
        new XYZ(0, 0, -bendR));
    connA.FlowDirection = FlowDirectionType.In;

    ConnectorElement connB = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, diameter,
        new XYZ(bendR, 0, 0));
    connB.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Create a pipe tee fitting family with three 80mm pipe connectors (run-in, run-out, branch)",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Pipe Tee"))
{{
    tx.Start();

    double diameter = {ft(80)}; // 80 mm
    double halfLen  = {ft(150)}; // 150 mm

    ConnectorElement runIn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, diameter,
        new XYZ(-halfLen, 0, 0));
    runIn.FlowDirection = FlowDirectionType.In;

    ConnectorElement runOut = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, diameter,
        new XYZ( halfLen, 0, 0));
    runOut.FlowDirection = FlowDirectionType.Out;

    ConnectorElement branch = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, diameter,
        new XYZ(0, 0, {ft(150)})); // 150 mm up
    branch.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Create a concentric pipe reducer fitting family, reducing from 100mm to 50mm",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

FamilyManager famMgr = familyDoc.FamilyManager;
famMgr.AddParameter("Large Diameter", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.AddParameter("Small Diameter", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

using (Transaction tx = new Transaction(familyDoc, "Create Pipe Reducer"))
{{
    tx.Start();

    double largeDiam = {ft(100)}; // 100 mm
    double smallDiam = {ft(50)};  // 50 mm
    double length    = {ft(200)}; // 200 mm

    ConnectorElement largeEnd = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, largeDiam,
        new XYZ(0, 0, -length / 2.0));
    largeEnd.FlowDirection = FlowDirectionType.In;

    ConnectorElement smallEnd = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, smallDiam,
        new XYZ(0, 0,  length / 2.0));
    smallEnd.FlowDirection = FlowDirectionType.Out;

    double lR = largeDiam / 2.0;
    double sR = smallDiam / 2.0;
    int n = 16;
    CurveArray bottomLoop = new CurveArray();
    CurveArray topLoop    = new CurveArray();
    for (int i = 0; i < n; i++)
    {{
        double a0 = 2 * System.Math.PI * i / n;
        double a1 = 2 * System.Math.PI * (i + 1) / n;
        bottomLoop.Append(Line.CreateBound(
            new XYZ(lR * System.Math.Cos(a0), lR * System.Math.Sin(a0), -length / 2.0),
            new XYZ(lR * System.Math.Cos(a1), lR * System.Math.Sin(a1), -length / 2.0)));
        topLoop.Append(Line.CreateBound(
            new XYZ(sR * System.Math.Cos(a0), sR * System.Math.Sin(a0), length / 2.0),
            new XYZ(sR * System.Math.Cos(a1), sR * System.Math.Sin(a1), length / 2.0)));
    }}
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, new XYZ(0, 0, -length / 2.0)));
    familyDoc.FamilyCreate.NewBlend(true, topLoop, bottomLoop, sp);

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Create a pipe cross fitting family with four 65mm connectors",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Pipe Cross"))
{{
    tx.Start();

    double diameter = {ft(65)}; // 65 mm
    double arm      = {ft(120)}; // 120 mm arm length

    ConnectorElement.CreatePipeConnector(familyDoc, PipeSystemType.SupplyHydronic, diameter,
        new XYZ(-arm, 0, 0)).FlowDirection = FlowDirectionType.In;
    ConnectorElement.CreatePipeConnector(familyDoc, PipeSystemType.SupplyHydronic, diameter,
        new XYZ( arm, 0, 0)).FlowDirection = FlowDirectionType.Out;
    ConnectorElement.CreatePipeConnector(familyDoc, PipeSystemType.SupplyHydronic, diameter,
        new XYZ(0, -arm, 0)).FlowDirection = FlowDirectionType.Out;
    ConnectorElement.CreatePipeConnector(familyDoc, PipeSystemType.SupplyHydronic, diameter,
        new XYZ(0,  arm, 0)).FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Create a 45-degree pipe elbow fitting family with 50mm connectors",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;
using System;

using (Transaction tx = new Transaction(familyDoc, "Create 45-Degree Pipe Elbow"))
{{
    tx.Start();

    double diameter = {ft(50)}; // 50 mm
    double bendR    = {ft(75)}; // 75 mm bend radius
    double angle    = Math.PI / 4.0; // 45 degrees

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
}}\"\"\"))

        samples.append(_s(
            "Create a pipe wye (Y-fitting) with a 45-degree branch, 100mm main, 65mm branch",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;
using System;

using (Transaction tx = new Transaction(familyDoc, "Create Pipe Wye"))
{{
    tx.Start();

    double mainDiam   = {ft(100)}; // 100 mm
    double branchDiam = {ft(65)};  // 65 mm
    double halfRun    = {ft(200)}; // 200 mm
    double branchLen  = {ft(150)}; // 150 mm
    double angle      = Math.PI / 4.0;

    ConnectorElement runIn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, mainDiam, new XYZ(-halfRun, 0, 0));
    runIn.FlowDirection = FlowDirectionType.In;

    ConnectorElement runOut = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, mainDiam, new XYZ( halfRun, 0, 0));
    runOut.FlowDirection = FlowDirectionType.Out;

    ConnectorElement branch = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, branchDiam,
        new XYZ(branchLen * Math.Cos(angle), 0, branchLen * Math.Sin(angle)));
    branch.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Create a pipe union fitting with two 50mm aligned connectors",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Pipe Union"))
{{
    tx.Start();

    double diameter = {ft(50)}; // 50 mm
    double halfLen  = {ft(60)}; // 60 mm

    ConnectorElement sideA = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, diameter, new XYZ(0, 0, -halfLen));
    sideA.FlowDirection = FlowDirectionType.In;

    ConnectorElement sideB = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, diameter, new XYZ(0, 0,  halfLen));
    sideB.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Create a pipe end cap fitting family with a single 50mm connector",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Pipe Cap"))
{{
    tx.Start();

    ConnectorElement openEnd = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic,
        {ft(50)}, // 50 mm
        XYZ.Zero);
    openEnd.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Create an eccentric pipe reducer fitting, 100mm inlet to 50mm outlet",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Eccentric Reducer"))
{{
    tx.Start();

    double largeDiam = {ft(100)}; // 100 mm
    double smallDiam = {ft(50)};  // 50 mm
    double length    = {ft(200)}; // 200 mm
    double offset    = (largeDiam - smallDiam) / 2.0; // bottom-flat eccentric

    ConnectorElement largeEnd = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, largeDiam, XYZ.Zero);
    largeEnd.FlowDirection = FlowDirectionType.In;

    ConnectorElement smallEnd = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, smallDiam,
        new XYZ(offset, 0, length));
    smallEnd.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        for large_mm, small_mm in [(150, 100), (200, 150), (250, 200)]:
            large_ft = round(large_mm / 304.8, 6)
            small_ft = round(small_mm / 304.8, 6)
            length_ft = round(max(large_mm, 200) / 304.8, 6)
            samples.append(_s(
                f"Create a concentric pipe reducer from {{large_mm}}mm to {{small_mm}}mm",
                f\"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Pipe Reducer {{large_mm}}x{{small_mm}}"))
{{{{
    tx.Start();

    double largeDiam = {{large_ft}}; // {{large_mm}} mm
    double smallDiam = {{small_ft}}; // {{small_mm}} mm
    double length    = {{length_ft}}; // {{max(large_mm, 200)}} mm

    ConnectorElement largeEnd = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, largeDiam,
        new XYZ(0, 0, -length / 2.0));
    largeEnd.FlowDirection = FlowDirectionType.In;

    ConnectorElement smallEnd = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, smallDiam,
        new XYZ(0, 0,  length / 2.0));
    smallEnd.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}}}\"\"\"))

        for run_mm, branch_mm in [(100, 65), (150, 100)]:
            run_ft    = round(run_mm / 304.8, 6)
            branch_ft = round(branch_mm / 304.8, 6)
            samples.append(_s(
                f"Create a pipe tee with {{run_mm}}mm run and {{branch_mm}}mm branch",
                f\"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Pipe Tee {{run_mm}}x{{branch_mm}}"))
{{{{
    tx.Start();

    double runDiam    = {{run_ft}}; // {{run_mm}} mm run
    double branchDiam = {{branch_ft}}; // {{branch_mm}} mm branch
    double halfLen    = {{run_ft}};

    ConnectorElement runIn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, runDiam, new XYZ(-halfLen, 0, 0));
    runIn.FlowDirection = FlowDirectionType.In;

    ConnectorElement runOut = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, runDiam, new XYZ( halfLen, 0, 0));
    runOut.FlowDirection = FlowDirectionType.Out;

    ConnectorElement branch = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, branchDiam,
        new XYZ(0, 0, {{branch_ft}}));
    branch.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}}}\"\"\"))

        return samples
"""

DUCT_FITTINGS = f"""
    # ------------------------------------------------------------------
    # Duct fittings
    # ------------------------------------------------------------------

    def _duct_fittings(self) -> List[SAMPLE]:
        samples = []

        samples.append(_s(
            "Create a 90-degree rectangular duct elbow fitting, 400x200mm",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Rect Duct Elbow 90"))
{{
    tx.Start();

    double width  = {ft(400)}; // 400 mm
    double height = {ft(200)}; // 200 mm
    double bendR  = {ft(400)}; // 400 mm bend radius (1W)

    ConnectorElement connA = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ(0, 0, -bendR));
    connA.Width = width; connA.Height = height;
    connA.FlowDirection = FlowDirectionType.In;

    ConnectorElement connB = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ(bendR, 0, 0));
    connB.Width = width; connB.Height = height;
    connB.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Create a 90-degree round duct elbow fitting, 315mm diameter",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Round Duct Elbow 90"))
{{
    tx.Start();

    double diameter = {ft(315)}; // 315 mm
    double bendR    = {ft(473)}; // 473 mm (1.5D)

    ConnectorElement connA = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Round,
        new XYZ(0, 0, -bendR));
    connA.Radius = diameter / 2.0;
    connA.FlowDirection = FlowDirectionType.In;

    ConnectorElement connB = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Round,
        new XYZ(bendR, 0, 0));
    connB.Radius = diameter / 2.0;
    connB.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Create a rectangular-to-round duct transition fitting (400x200mm rect to 315mm round)",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Duct Transition"))
{{
    tx.Start();

    double length = {ft(300)}; // 300 mm

    ConnectorElement rectConn = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular, XYZ.Zero);
    rectConn.Width  = {ft(400)}; // 400 mm
    rectConn.Height = {ft(200)}; // 200 mm
    rectConn.FlowDirection = FlowDirectionType.In;

    ConnectorElement roundConn = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Round,
        new XYZ(0, 0, length));
    roundConn.Radius = {315 * MM_TO_FT / 2.0:.6f}; // 157.5 mm radius
    roundConn.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Create a rectangular duct tee fitting, 600x300mm main, 400x200mm branch",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Duct Tee"))
{{
    tx.Start();

    double mainW = {ft(600)}; double mainH = {ft(300)};
    double brnW  = {ft(400)}; double brnH  = {ft(200)};
    double halfRun = {ft(400)};

    ConnectorElement mainIn = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ(-halfRun, 0, 0));
    mainIn.Width = mainW; mainIn.Height = mainH;
    mainIn.FlowDirection = FlowDirectionType.In;

    ConnectorElement mainOut = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ( halfRun, 0, 0));
    mainOut.Width = mainW; mainOut.Height = mainH;
    mainOut.FlowDirection = FlowDirectionType.Out;

    ConnectorElement branch = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ(0, 0, {ft(300)})); // 300 mm up
    branch.Width = brnW; branch.Height = brnH;
    branch.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Create a concentric rectangular duct reducer, 600x300mm to 400x200mm",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Duct Reducer"))
{{
    tx.Start();

    double length = {ft(300)}; // 300 mm

    ConnectorElement largeEnd = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular, XYZ.Zero);
    largeEnd.Width = {ft(600)}; largeEnd.Height = {ft(300)};
    largeEnd.FlowDirection = FlowDirectionType.In;

    ConnectorElement smallEnd = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ(0, 0, length));
    smallEnd.Width = {ft(400)}; smallEnd.Height = {ft(200)};
    smallEnd.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Create a 45-degree rectangular duct elbow, 300x200mm",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;
using System;

using (Transaction tx = new Transaction(familyDoc, "Create Duct Elbow 45"))
{{
    tx.Start();

    double width = {ft(300)}; double height = {ft(200)};
    double bendR = {ft(300)}; // 1W
    double angle = Math.PI / 4.0;

    ConnectorElement connA = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ(0, 0, -bendR));
    connA.Width = width; connA.Height = height;
    connA.FlowDirection = FlowDirectionType.In;

    ConnectorElement connB = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ(bendR * Math.Sin(angle), 0, bendR * (1.0 - Math.Cos(angle))));
    connB.Width = width; connB.Height = height;
    connB.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Create a duct wye fitting with 45-degree branch, 500x250mm main, 300x200mm branch",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;
using System;

using (Transaction tx = new Transaction(familyDoc, "Create Duct Wye"))
{{
    tx.Start();

    double mainW = {ft(500)}; double mainH = {ft(250)};
    double brnW  = {ft(300)}; double brnH  = {ft(200)};
    double halfRun = {ft(300)}; double brnLen = {ft(250)};
    double angle = Math.PI / 4.0;

    ConnectorElement mainIn = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ(-halfRun, 0, 0));
    mainIn.Width = mainW; mainIn.Height = mainH;
    mainIn.FlowDirection = FlowDirectionType.In;

    ConnectorElement mainOut = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ( halfRun, 0, 0));
    mainOut.Width = mainW; mainOut.Height = mainH;
    mainOut.FlowDirection = FlowDirectionType.Out;

    ConnectorElement branch = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ(brnLen * Math.Cos(angle), 0, brnLen * Math.Sin(angle)));
    branch.Width = brnW; branch.Height = brnH;
    branch.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Create a rectangular duct end cap fitting, 400x200mm",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Duct Cap"))
{{
    tx.Start();

    ConnectorElement conn = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular, XYZ.Zero);
    conn.Width = {ft(400)}; conn.Height = {ft(200)};
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Create a return air duct tee fitting, 800x400mm main, 400x300mm branch",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Return Air Tee"))
{{
    tx.Start();

    double halfRun = {ft(500)};

    ConnectorElement mainIn = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.ReturnAir, ConnectorProfileType.Rectangular,
        new XYZ(-halfRun, 0, 0));
    mainIn.Width = {ft(800)}; mainIn.Height = {ft(400)};
    mainIn.FlowDirection = FlowDirectionType.In;

    ConnectorElement mainOut = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.ReturnAir, ConnectorProfileType.Rectangular,
        new XYZ( halfRun, 0, 0));
    mainOut.Width = {ft(800)}; mainOut.Height = {ft(400)};
    mainOut.FlowDirection = FlowDirectionType.Out;

    ConnectorElement branch = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.ReturnAir, ConnectorProfileType.Rectangular,
        new XYZ(0, 0, {ft(300)}));
    branch.Width = {ft(400)}; branch.Height = {ft(300)};
    branch.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        samples.append(_s(
            "Create a duct offset (S-curve) fitting, 400x200mm, 300mm lateral offset",
            \"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Duct Offset"))
{{
    tx.Start();

    double width = {ft(400)}; double height = {ft(200)};
    double axial = {ft(600)}; double lateral = {ft(300)};

    ConnectorElement connA = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular, XYZ.Zero);
    connA.Width = width; connA.Height = height;
    connA.FlowDirection = FlowDirectionType.In;

    ConnectorElement connB = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ(lateral, 0, axial));
    connB.Width = width; connB.Height = height;
    connB.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}\"\"\"))

        for w_mm, h_mm in [(300, 150), (500, 300)]:
            w_ft = round(w_mm / 304.8, 6)
            h_ft = round(h_mm / 304.8, 6)
            samples.append(_s(
                f"Create a 90-degree rectangular duct elbow, {{w_mm}}x{{h_mm}}mm",
                f\"\"\"\\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Duct Elbow {{w_mm}}x{{h_mm}}"))
{{{{
    tx.Start();

    double width = {{w_ft}}; double height = {{h_ft}};
    double bendR = {{w_ft}}; // 1W

    ConnectorElement connA = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ(0, 0, -bendR));
    connA.Width = width; connA.Height = height;
    connA.FlowDirection = FlowDirectionType.In;

    ConnectorElement connB = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ(bendR, 0, 0));
    connB.Width = width; connB.Height = height;
    connB.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}}}\"\"\"))

        return samples
"""

path = r'C:/Users/JordanEhrig/Documents/GitHub/revit-family-engine/training_pipeline/generators/mep_family_generator.py'
with open(path, 'a', encoding='utf-8') as f:
    f.write(PIPE_FITTINGS)
    f.write(DUCT_FITTINGS)

print('done')
