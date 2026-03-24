"""Training data generator: MEP Revit family connectors and equipment.

Produces ~250 Alpaca-format training pairs covering pipe connectors, duct
connectors, conduit connectors, pipe/duct fittings, equipment families,
electrical fixtures, sprinkler heads, plumbing fixtures, and connector
parameter patterns.
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
    """Generates training samples for Revit MEP family connector creation."""

    def generate(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []
        samples += self._pipe_connectors()
        samples += self._duct_connectors()
        samples += self._conduit_connectors()
        samples += self._pipe_fittings()
        samples += self._duct_fittings()
        samples += self._equipment_families()
        samples += self._electrical_fixtures()
        samples += self._sprinkler_heads()
        samples += self._plumbing_fixtures()
        samples += self._connector_parameters()
        return samples

    # ------------------------------------------------------------------
    # Pipe connectors
    # ------------------------------------------------------------------

    def _pipe_connectors(self) -> List[SAMPLE]:
        samples = []

        # Basic single pipe connector cases
        cases = [
            (50,  "supply", "SupplyHydronic", "Add a 50mm supply pipe connector to a Revit family"),
            (100, "return", "ReturnHydronic",  "Add a 100mm return hydronic pipe connector"),
            (25,  "supply", "SupplyHydronic",  "Add a 25mm domestic cold water pipe connector"),
            (75,  "supply", "OtherPipe",        "Add a 75mm generic pipe connector with supply direction"),
            (150, "bidirectional", "SupplyHydronic", "Add a 150mm bidirectional pipe connector"),
        ]
        for dia_mm, flow_label, sys_type, instruction in cases:
            dia_ft = dia_mm * MM_TO_FT
            flow_enum = {
                "supply": "FlowDirectionType.In",
                "return": "FlowDirectionType.Out",
                "bidirectional": "FlowDirectionType.Bidirectional",
            }[flow_label]
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

// Add pipe connector: diameter {dia_mm} mm, flow {flow_label}, system {sys_type}
// ConnectorManager is obtained from the family's MEP model -- no Transaction needed for connector setup
using (Transaction tx = new Transaction(familyDoc, "Add Pipe Connector"))
{{
    tx.Start();

    double diameter = {dia_ft:.6f}; // {dia_mm} mm

    // Place connector origin at family origin (adjust XYZ for actual port location)
    ConnectorElement pipeConn = ConnectorElement.CreatePipeConnector(
        familyDoc,
        PipeSystemType.{sys_type},
        diameter,
        XYZ.Zero);

    pipeConn.FlowDirection = {flow_enum};

    tx.Commit();
}}"""))

        # Connector with explicit origin positions
        port_cases = [
            (50,  "XYZ.Zero",                             "inlet at origin"),
            (50,  f"new XYZ(0, 0, {_ft(500)})",          "outlet 500mm above origin"),
            (80,  f"new XYZ({_ft(200)}, 0, 0)",          "side connector 200mm offset"),
            (100, f"new XYZ(0, {_ft(-150)}, 0)",         "connector offset -150mm in Y"),
        ]
        for dia_mm, origin_expr, desc in port_cases:
            dia_ft = dia_mm * MM_TO_FT
            samples.append(_s(
                f"Add a {dia_mm}mm pipe connector at {desc}",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

// Pipe connector at {desc}
using (Transaction tx = new Transaction(familyDoc, "Add Pipe Connector"))
{{
    tx.Start();

    double diameter = {dia_ft:.6f}; // {dia_mm} mm

    ConnectorElement pipeConn = ConnectorElement.CreatePipeConnector(
        familyDoc,
        PipeSystemType.SupplyHydronic,
        diameter,
        {origin_expr});

    pipeConn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}"""))

        # Pair of inlet + outlet connectors
        samples.append(_s(
            "Add a pair of 65mm pipe connectors (inlet and outlet) to a pipe fitting family",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

// Inlet connector at bottom, outlet connector at top
using (Transaction tx = new Transaction(familyDoc, "Add Pipe Connector Pair"))
{{
    tx.Start();

    double diameter = {65 * MM_TO_FT:.6f}; // 65 mm

    // Inlet -- fluid enters the fitting
    ConnectorElement inlet = ConnectorElement.CreatePipeConnector(
        familyDoc,
        PipeSystemType.SupplyHydronic,
        diameter,
        new XYZ(0, 0, {-300 * MM_TO_FT:.6f})); // -300 mm
    inlet.FlowDirection = FlowDirectionType.In;

    // Outlet -- fluid exits the fitting
    ConnectorElement outlet = ConnectorElement.CreatePipeConnector(
        familyDoc,
        PipeSystemType.SupplyHydronic,
        diameter,
        new XYZ(0, 0, {300 * MM_TO_FT:.6f})); // +300 mm
    outlet.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}"""))

        # Connector with angle (not aligned to Z)
        samples.append(_s(
            "Add a 50mm pipe connector pointing in the +X direction (horizontal branch)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

// Horizontal pipe connector -- connector direction set via transform
using (Transaction tx = new Transaction(familyDoc, "Add Horizontal Pipe Connector"))
{{
    tx.Start();

    double diameter = {50 * MM_TO_FT:.6f}; // 50 mm

    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc,
        PipeSystemType.SupplyHydronic,
        diameter,
        new XYZ({200 * MM_TO_FT:.6f}, 0, 0)); // 200 mm along X

    // Rotate connector to point in +X direction
    conn.SetCoordinateSystem(new Transform(Transform.Identity)
    {{
        Origin = new XYZ({200 * MM_TO_FT:.6f}, 0, 0),
        BasisX = XYZ.BasisY,
        BasisY = XYZ.BasisZ,
        BasisZ = XYZ.BasisX  // connector faces +X
    }});

    conn.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}"""))

        # Pressure/flow parameter on connector
        samples.append(_s(
            "Create a pipe connector with flow rate and pressure drop parameters",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

// FamilyManager parameter setup (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pFlow = famMgr.AddParameter(
    "Connector Flow",
    BuiltInParameterGroup.PG_MECHANICAL_FLOW,
    ParameterType.PipeFlow,
    false); // type parameter
famMgr.Set(pFlow, 0.0); // default 0 L/s

using (Transaction tx = new Transaction(familyDoc, "Add Pipe Connector"))
{{
    tx.Start();

    double diameter = {50 * MM_TO_FT:.6f}; // 50 mm

    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc,
        PipeSystemType.SupplyHydronic,
        diameter,
        XYZ.Zero);

    conn.FlowDirection = FlowDirectionType.In;

    // Assign flow parameter to connector
    Parameter flowParam = conn.get_Parameter(BuiltInParameter.RBS_PIPE_FLOW_PARAM);
    if (flowParam != null && !flowParam.IsReadOnly)
        flowParam.Set(0.001); // 0.001 m3/s = 1 L/s

    tx.Commit();
}}"""))

        # Multiple system types
        sys_cases = [
            ("DomesticHotWater",  "hot water",   60),
            ("DomesticColdWater", "cold water",  20),
            ("FireProtectWet",    "fire sprinkler wet",  25),
            ("FireProtectDry",    "fire sprinkler dry",  25),
            ("OtherPipe",         "process pipe", 100),
            ("Vent",              "plumbing vent", 50),
            ("Sanitary",          "sanitary drain", 100),
        ]
        for sys_type, label, dia_mm in sys_cases:
            dia_ft = dia_mm * MM_TO_FT
            samples.append(_s(
                f"Add a {dia_mm}mm {label} pipe connector (PipeSystemType.{sys_type})",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

// {label} pipe connector
using (Transaction tx = new Transaction(familyDoc, "Add {label.title()} Connector"))
{{
    tx.Start();

    double diameter = {dia_ft:.6f}; // {dia_mm} mm

    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc,
        PipeSystemType.{sys_type},
        diameter,
        XYZ.Zero);

    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}"""))

        # Diameter-driven by family parameter
        samples.append(_s(
            "Create a pipe connector whose diameter is driven by a family parameter",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

// Step 1: Define diameter parameter (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pDiam = famMgr.AddParameter(
    "Connector Diameter",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length,
    false);
famMgr.Set(pDiam, {50 * MM_TO_FT:.6f}); // default 50 mm

// Step 2: Create connector using current default value
using (Transaction tx = new Transaction(familyDoc, "Add Parametric Pipe Connector"))
{{
    tx.Start();

    double diameter = {50 * MM_TO_FT:.6f}; // 50 mm default

    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc,
        PipeSystemType.SupplyHydronic,
        diameter,
        XYZ.Zero);

    conn.FlowDirection = FlowDirectionType.In;

    // Link connector radius parameter to family parameter
    Parameter connDiamParam = conn.get_Parameter(BuiltInParameter.CONNECTOR_RADIUS);
    if (connDiamParam != null)
        famMgr.AssociateElementParameterToFamilyParameter(connDiamParam, pDiam);

    tx.Commit();
}}"""))

        return samples

    # ------------------------------------------------------------------
    # Duct connectors
    # ------------------------------------------------------------------

    def _duct_connectors(self) -> List[SAMPLE]:
        samples = []

        # Rectangular duct connectors
        rect_cases = [
            (400, 200, "supply", "SupplyAir",  "Add a 400x200mm rectangular supply air duct connector"),
            (600, 300, "return", "ReturnAir",  "Add a 600x300mm rectangular return air duct connector"),
            (300, 300, "supply", "SupplyAir",  "Add a 300x300mm square supply duct connector"),
            (800, 400, "exhaust","ExhaustAir", "Add a 800x400mm exhaust duct connector"),
            (250, 150, "supply", "SupplyAir",  "Add a 250x150mm small supply duct connector"),
        ]
        for w_mm, h_mm, flow_label, sys_type, instruction in rect_cases:
            w_ft = w_mm * MM_TO_FT
            h_ft = h_mm * MM_TO_FT
            flow_enum = {
                "supply": "FlowDirectionType.In",
                "return": "FlowDirectionType.Out",
                "exhaust": "FlowDirectionType.Out",
            }[flow_label]
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

// Rectangular duct connector: {w_mm} x {h_mm} mm, {flow_label} air
using (Transaction tx = new Transaction(familyDoc, "Add Duct Connector"))
{{
    tx.Start();

    double width  = {w_ft:.6f}; // {w_mm} mm
    double height = {h_ft:.6f}; // {h_mm} mm

    ConnectorElement ductConn = ConnectorElement.CreateDuctConnector(
        familyDoc,
        DuctSystemType.{sys_type},
        ConnectorProfileType.Rectangular,
        XYZ.Zero);

    ductConn.Width  = width;
    ductConn.Height = height;
    ductConn.FlowDirection = {flow_enum};

    tx.Commit();
}}"""))

        # Round duct connectors
        round_cases = [
            (200, "supply", "SupplyAir",  "Add a 200mm round supply duct connector"),
            (315, "return", "ReturnAir",  "Add a 315mm round return air duct connector"),
            (160, "supply", "SupplyAir",  "Add a 160mm round supply duct branch connector"),
            (400, "exhaust","ExhaustAir", "Add a 400mm round exhaust duct connector"),
            (100, "supply", "SupplyAir",  "Add a 100mm small round supply duct connector"),
        ]
        for dia_mm, flow_label, sys_type, instruction in round_cases:
            dia_ft = dia_mm * MM_TO_FT
            flow_enum = {
                "supply": "FlowDirectionType.In",
                "return": "FlowDirectionType.Out",
                "exhaust": "FlowDirectionType.Out",
            }[flow_label]
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

// Round duct connector: diameter {dia_mm} mm, {flow_label} air
using (Transaction tx = new Transaction(familyDoc, "Add Round Duct Connector"))
{{
    tx.Start();

    double diameter = {dia_ft:.6f}; // {dia_mm} mm

    ConnectorElement ductConn = ConnectorElement.CreateDuctConnector(
        familyDoc,
        DuctSystemType.{sys_type},
        ConnectorProfileType.Round,
        XYZ.Zero);

    ductConn.Radius = diameter / 2.0;
    ductConn.FlowDirection = {flow_enum};

    tx.Commit();
}}"""))

        # Duct connector with airflow parameter
        samples.append(_s(
            "Create a rectangular duct connector with airflow rate and velocity parameters",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

// Airflow parameter (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pFlow = famMgr.AddParameter(
    "Airflow",
    BuiltInParameterGroup.PG_MECHANICAL_AIRFLOW,
    ParameterType.AirFlow,
    false);
famMgr.Set(pFlow, 0.5); // 0.5 m3/s default

using (Transaction tx = new Transaction(familyDoc, "Add Duct Connector with Flow"))
{{
    tx.Start();

    double width  = {400 * MM_TO_FT:.6f}; // 400 mm
    double height = {200 * MM_TO_FT:.6f}; // 200 mm

    ConnectorElement ductConn = ConnectorElement.CreateDuctConnector(
        familyDoc,
        DuctSystemType.SupplyAir,
        ConnectorProfileType.Rectangular,
        XYZ.Zero);

    ductConn.Width  = width;
    ductConn.Height = height;
    ductConn.FlowDirection = FlowDirectionType.In;

    // Associate airflow
    Parameter flowParam = ductConn.get_Parameter(BuiltInParameter.RBS_DUCT_FLOW_PARAM);
    if (flowParam != null)
        famMgr.AssociateElementParameterToFamilyParameter(flowParam, pFlow);

    tx.Commit();
}}"""))

        # Pair supply/return
        samples.append(_s(
            "Add both a supply and return duct connector to a VAV box family",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Add VAV Duct Connectors"))
{{
    tx.Start();

    double width  = {400 * MM_TO_FT:.6f}; // 400 mm
    double height = {200 * MM_TO_FT:.6f}; // 200 mm

    // Inlet (supply air enters from upstream duct)
    ConnectorElement inlet = ConnectorElement.CreateDuctConnector(
        familyDoc,
        DuctSystemType.SupplyAir,
        ConnectorProfileType.Round,
        new XYZ(0, 0, {-200 * MM_TO_FT:.6f})); // -200 mm
    inlet.Radius = {100 * MM_TO_FT:.6f}; // 200 mm dia
    inlet.FlowDirection = FlowDirectionType.In;

    // Outlet (conditioned air to room)
    ConnectorElement outlet = ConnectorElement.CreateDuctConnector(
        familyDoc,
        DuctSystemType.SupplyAir,
        ConnectorProfileType.Rectangular,
        new XYZ(0, 0, {200 * MM_TO_FT:.6f})); // +200 mm
    outlet.Width  = width;
    outlet.Height = height;
    outlet.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}"""))

        # Connector at offset positions
        for idx, (x_mm, y_mm, z_mm, side_label) in enumerate([
            (0, 0, 300, "top"),
            (0, 0, -300, "bottom"),
            (300, 0, 0, "front"),
            (0, 300, 0, "right side"),
        ]):
            samples.append(_s(
                f"Add a 250x250mm duct connector on the {side_label} of a box family",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

// Duct connector at {side_label} face
using (Transaction tx = new Transaction(familyDoc, "Add Duct Connector {side_label.title()}"))
{{
    tx.Start();

    double w = {250 * MM_TO_FT:.6f}; // 250 mm

    ConnectorElement conn = ConnectorElement.CreateDuctConnector(
        familyDoc,
        DuctSystemType.SupplyAir,
        ConnectorProfileType.Rectangular,
        new XYZ({x_mm * MM_TO_FT:.6f}, {y_mm * MM_TO_FT:.6f}, {z_mm * MM_TO_FT:.6f}));

    conn.Width  = w;
    conn.Height = w;
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}"""))

        # Oval duct connector
        samples.append(_s(
            "Add an oval duct connector (400x200mm) to a flat duct fitting family",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Add Oval Duct Connector"))
{{
    tx.Start();

    double width  = {400 * MM_TO_FT:.6f}; // 400 mm
    double height = {200 * MM_TO_FT:.6f}; // 200 mm

    ConnectorElement conn = ConnectorElement.CreateDuctConnector(
        familyDoc,
        DuctSystemType.SupplyAir,
        ConnectorProfileType.Oval,
        XYZ.Zero);

    conn.Width  = width;
    conn.Height = height;
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}"""))


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
                f"Add a {w_mm}x{h_mm}mm rectangular {label} duct connector",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Add Duct Connector"))
{{
    tx.Start();

    ConnectorElement conn = ConnectorElement.CreateDuctConnector(
        familyDoc,
        DuctSystemType.{sys_type},
        ConnectorProfileType.Rectangular,
        XYZ.Zero);
    conn.Width  = {w_ft}; // {w_mm} mm
    conn.Height = {h_ft}; // {h_mm} mm
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}"""))

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
                f"Add a {dia_mm}mm round {label} duct connector",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Add Round Duct Connector"))
{{
    tx.Start();

    ConnectorElement conn = ConnectorElement.CreateDuctConnector(
        familyDoc,
        DuctSystemType.{sys_type},
        ConnectorProfileType.Round,
        XYZ.Zero);
    conn.Radius = {dia_ft} / 2.0; // {dia_mm} mm dia
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}}"""))

        return samples

    # ------------------------------------------------------------------
    # Conduit connectors
    # ------------------------------------------------------------------

    def _conduit_connectors(self) -> List[SAMPLE]:
        samples = []

        conduit_cases = [
            (27,  "Add a 27mm electrical conduit connector (1 inch trade size)"),
            (35,  "Add a 35mm conduit connector (1-1/4 inch trade size)"),
            (53,  "Add a 53mm conduit connector (2 inch trade size)"),
            (78,  "Add a 78mm conduit connector (3 inch trade size)"),
            (103, "Add a 103mm conduit connector (4 inch trade size)"),
        ]
        for dia_mm, instruction in conduit_cases:
            dia_ft = dia_mm * MM_TO_FT
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

// Conduit connector: {dia_mm} mm diameter
using (Transaction tx = new Transaction(familyDoc, "Add Conduit Connector"))
{{
    tx.Start();

    double diameter = {dia_ft:.6f}; // {dia_mm} mm

    ConnectorElement conduitConn = ConnectorElement.CreateConduitConnector(
        familyDoc,
        diameter,
        XYZ.Zero);

    tx.Commit();
}}"""))

        # Conduit connector with explicit origin
        samples.append(_s(
            "Add two 27mm conduit connectors (entry and exit) to a conduit body family",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

using (Transaction tx = new Transaction(familyDoc, "Add Conduit Connector Pair"))
{{
    tx.Start();

    double diameter = {27 * MM_TO_FT:.6f}; // 27 mm

    ConnectorElement entry = ConnectorElement.CreateConduitConnector(
        familyDoc,
        diameter,
        new XYZ(0, 0, {-100 * MM_TO_FT:.6f})); // -100 mm

    ConnectorElement exit_ = ConnectorElement.CreateConduitConnector(
        familyDoc,
        diameter,
        new XYZ(0, 0, {100 * MM_TO_FT:.6f})); // +100 mm

    tx.Commit();
}}"""))

        # Conduit connector with angle
        samples.append(_s(
            "Add a 53mm conduit connector oriented horizontally (+X direction) on a junction box",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

using (Transaction tx = new Transaction(familyDoc, "Add Horizontal Conduit Connector"))
{{
    tx.Start();

    double diameter = {53 * MM_TO_FT:.6f}; // 53 mm

    ConnectorElement conn = ConnectorElement.CreateConduitConnector(
        familyDoc,
        diameter,
        new XYZ({150 * MM_TO_FT:.6f}, 0, 0)); // 150 mm along X

    // Orient to face +X
    conn.SetCoordinateSystem(new Transform(Transform.Identity)
    {{
        Origin = new XYZ({150 * MM_TO_FT:.6f}, 0, 0),
        BasisX = XYZ.BasisY,
        BasisY = XYZ.BasisZ,
        BasisZ = XYZ.BasisX
    }});

    tx.Commit();
}}"""))

        # 4-way junction box
        samples.append(_s(
            "Add four 27mm conduit connectors to a 4-way junction box family (top, bottom, left, right)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

using (Transaction tx = new Transaction(familyDoc, "Add Junction Box Connectors"))
{{
    tx.Start();

    double diameter = {27 * MM_TO_FT:.6f}; // 27 mm
    double offset   = {75 * MM_TO_FT:.6f}; // 75 mm to face

    // Top
    ConnectorElement top = ConnectorElement.CreateConduitConnector(
        familyDoc, diameter, new XYZ(0, 0,  offset));
    // Bottom
    ConnectorElement bot = ConnectorElement.CreateConduitConnector(
        familyDoc, diameter, new XYZ(0, 0, -offset));
    // Left (+Y)
    ConnectorElement left = ConnectorElement.CreateConduitConnector(
        familyDoc, diameter, new XYZ(0,  offset, 0));
    // Right (-Y)
    ConnectorElement right = ConnectorElement.CreateConduitConnector(
        familyDoc, diameter, new XYZ(0, -offset, 0));

    tx.Commit();
}}"""))

        # Parametric conduit diameter
        samples.append(_s(
            "Create a conduit connector whose diameter is controlled by a family parameter",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

// Parameter outside Transaction
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pDiam = famMgr.AddParameter(
    "Conduit Diameter",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length,
    false);
famMgr.Set(pDiam, {27 * MM_TO_FT:.6f}); // 27 mm default

using (Transaction tx = new Transaction(familyDoc, "Add Parametric Conduit Connector"))
{{
    tx.Start();

    double diameter = {27 * MM_TO_FT:.6f}; // 27 mm default

    ConnectorElement conn = ConnectorElement.CreateConduitConnector(
        familyDoc,
        diameter,
        XYZ.Zero);

    Parameter connDiam = conn.get_Parameter(BuiltInParameter.CONNECTOR_RADIUS);
    if (connDiam != null)
        famMgr.AssociateElementParameterToFamilyParameter(connDiam, pDiam);

    tx.Commit();
}}"""))

        # Cable tray connector
        samples.append(_s(
            "Add a 300x100mm cable tray connector to a cable tray fitting family",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

using (Transaction tx = new Transaction(familyDoc, "Add Cable Tray Connector"))
{{
    tx.Start();

    double width  = {300 * MM_TO_FT:.6f}; // 300 mm
    double height = {100 * MM_TO_FT:.6f}; // 100 mm

    ConnectorElement trayConn = ConnectorElement.CreateCableTrayConnector(
        familyDoc,
        width,
        height,
        XYZ.Zero);

    tx.Commit();
}}"""))

        # Conduit on angled face
        samples.append(_s(
            "Add a 35mm conduit connector on a 45-degree angled face of a conduit elbow family",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;
using System;

using (Transaction tx = new Transaction(familyDoc, "Add Angled Conduit Connector"))
{{
    tx.Start();

    double diameter = {35 * MM_TO_FT:.6f}; // 35 mm
    double offsetDist = {100 * MM_TO_FT:.6f}; // 100 mm

    // 45-degree point: move along X=Y diagonal
    double diag = offsetDist / Math.Sqrt(2.0);
    XYZ origin = new XYZ(diag, diag, 0);

    ConnectorElement conn = ConnectorElement.CreateConduitConnector(
        familyDoc,
        diameter,
        origin);

    // Orient to face along 45-degree direction in XY plane
    XYZ faceDir = new XYZ(1.0 / Math.Sqrt(2.0), 1.0 / Math.Sqrt(2.0), 0);
    XYZ perpDir = new XYZ(-1.0 / Math.Sqrt(2.0), 1.0 / Math.Sqrt(2.0), 0);

    conn.SetCoordinateSystem(new Transform(Transform.Identity)
    {{
        Origin = origin,
        BasisX = perpDir,
        BasisY = XYZ.BasisZ,
        BasisZ = faceDir
    }});

    tx.Commit();
}}"""))


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
                f"""\
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
}}}}"""))

        return samples

    # ------------------------------------------------------------------
    # Pipe fittings
    # ------------------------------------------------------------------

    def _pipe_fittings(self) -> List[SAMPLE]:
        samples = []

        samples.append(_s(
            "Create a 90-degree pipe elbow fitting family with 50mm pipe connectors",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pNomDiam = famMgr.AddParameter(
    "Nominal Diameter",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length,
    false);
famMgr.Set(pNomDiam, 0.164042); // 50 mm

FamilyParameter pBendRadius = famMgr.AddParameter(
    "Bend Radius",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length,
    false);
famMgr.Set(pBendRadius, 0.246063); // 75 mm (1.5D)

using (Transaction tx = new Transaction(familyDoc, "Create Pipe Elbow"))
{
    tx.Start();

    double diameter = 0.164042;  // 50 mm
    double bendR    = 0.246063;  // 75 mm bend radius

    ConnectorElement connA = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, diameter,
        new XYZ(0, 0, -bendR));
    connA.FlowDirection = FlowDirectionType.In;

    ConnectorElement connB = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, diameter,
        new XYZ(bendR, 0, 0));
    connB.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}"""))

        samples.append(_s(
            "Create a pipe tee fitting family with three 80mm pipe connectors (run-in, run-out, branch)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Pipe Tee"))
{
    tx.Start();

    double diameter = 0.262467; // 80 mm
    double halfLen  = 0.492126; // 150 mm

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
        new XYZ(0, 0, 0.492126)); // 150 mm up
    branch.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}"""))

        samples.append(_s(
            "Create a concentric pipe reducer fitting family, reducing from 100mm to 50mm",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

FamilyManager famMgr = familyDoc.FamilyManager;
famMgr.AddParameter("Large Diameter", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.AddParameter("Small Diameter", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

using (Transaction tx = new Transaction(familyDoc, "Create Pipe Reducer"))
{
    tx.Start();

    double largeDiam = 0.328084; // 100 mm
    double smallDiam = 0.164042;  // 50 mm
    double length    = 0.656168; // 200 mm

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
    {
        double a0 = 2 * System.Math.PI * i / n;
        double a1 = 2 * System.Math.PI * (i + 1) / n;
        bottomLoop.Append(Line.CreateBound(
            new XYZ(lR * System.Math.Cos(a0), lR * System.Math.Sin(a0), -length / 2.0),
            new XYZ(lR * System.Math.Cos(a1), lR * System.Math.Sin(a1), -length / 2.0)));
        topLoop.Append(Line.CreateBound(
            new XYZ(sR * System.Math.Cos(a0), sR * System.Math.Sin(a0), length / 2.0),
            new XYZ(sR * System.Math.Cos(a1), sR * System.Math.Sin(a1), length / 2.0)));
    }
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, new XYZ(0, 0, -length / 2.0)));
    familyDoc.FamilyCreate.NewBlend(true, topLoop, bottomLoop, sp);

    tx.Commit();
}"""))

        samples.append(_s(
            "Create a pipe cross fitting family with four 65mm connectors",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Pipe Cross"))
{
    tx.Start();

    double diameter = 0.213255; // 65 mm
    double arm      = 0.393701; // 120 mm arm length

    ConnectorElement.CreatePipeConnector(familyDoc, PipeSystemType.SupplyHydronic, diameter,
        new XYZ(-arm, 0, 0)).FlowDirection = FlowDirectionType.In;
    ConnectorElement.CreatePipeConnector(familyDoc, PipeSystemType.SupplyHydronic, diameter,
        new XYZ( arm, 0, 0)).FlowDirection = FlowDirectionType.Out;
    ConnectorElement.CreatePipeConnector(familyDoc, PipeSystemType.SupplyHydronic, diameter,
        new XYZ(0, -arm, 0)).FlowDirection = FlowDirectionType.Out;
    ConnectorElement.CreatePipeConnector(familyDoc, PipeSystemType.SupplyHydronic, diameter,
        new XYZ(0,  arm, 0)).FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}"""))

        samples.append(_s(
            "Create a 45-degree pipe elbow fitting family with 50mm connectors",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;
using System;

using (Transaction tx = new Transaction(familyDoc, "Create 45-Degree Pipe Elbow"))
{
    tx.Start();

    double diameter = 0.164042; // 50 mm
    double bendR    = 0.246063; // 75 mm bend radius
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
}"""))

        samples.append(_s(
            "Create a pipe wye (Y-fitting) with a 45-degree branch, 100mm main, 65mm branch",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;
using System;

using (Transaction tx = new Transaction(familyDoc, "Create Pipe Wye"))
{
    tx.Start();

    double mainDiam   = 0.328084; // 100 mm
    double branchDiam = 0.213255;  // 65 mm
    double halfRun    = 0.656168; // 200 mm
    double branchLen  = 0.492126; // 150 mm
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
}"""))

        samples.append(_s(
            "Create a pipe union fitting with two 50mm aligned connectors",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Pipe Union"))
{
    tx.Start();

    double diameter = 0.164042; // 50 mm
    double halfLen  = 0.196850; // 60 mm

    ConnectorElement sideA = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, diameter, new XYZ(0, 0, -halfLen));
    sideA.FlowDirection = FlowDirectionType.In;

    ConnectorElement sideB = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, diameter, new XYZ(0, 0,  halfLen));
    sideB.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}"""))

        samples.append(_s(
            "Create a pipe end cap fitting family with a single 50mm connector",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Pipe Cap"))
{
    tx.Start();

    ConnectorElement openEnd = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic,
        0.164042, // 50 mm
        XYZ.Zero);
    openEnd.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}"""))

        samples.append(_s(
            "Create an eccentric pipe reducer fitting, 100mm inlet to 50mm outlet",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Eccentric Reducer"))
{
    tx.Start();

    double largeDiam = 0.328084; // 100 mm
    double smallDiam = 0.164042;  // 50 mm
    double length    = 0.656168; // 200 mm
    double offset    = (largeDiam - smallDiam) / 2.0; // bottom-flat eccentric

    ConnectorElement largeEnd = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, largeDiam, XYZ.Zero);
    largeEnd.FlowDirection = FlowDirectionType.In;

    ConnectorElement smallEnd = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, smallDiam,
        new XYZ(offset, 0, length));
    smallEnd.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}"""))

        for large_mm, small_mm in [(150, 100), (200, 150), (250, 200)]:
            large_ft = round(large_mm / 304.8, 6)
            small_ft = round(small_mm / 304.8, 6)
            length_ft = round(max(large_mm, 200) / 304.8, 6)
            samples.append(_s(
                f"Create a concentric pipe reducer from {large_mm}mm to {small_mm}mm",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Pipe Reducer {large_mm}x{small_mm}"))
{{
    tx.Start();

    double largeDiam = {large_ft}; // {large_mm} mm
    double smallDiam = {small_ft}; // {small_mm} mm
    double length    = {length_ft}; // {max(large_mm, 200)} mm

    ConnectorElement largeEnd = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, largeDiam,
        new XYZ(0, 0, -length / 2.0));
    largeEnd.FlowDirection = FlowDirectionType.In;

    ConnectorElement smallEnd = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, smallDiam,
        new XYZ(0, 0,  length / 2.0));
    smallEnd.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}"""))

        for run_mm, branch_mm in [(100, 65), (150, 100)]:
            run_ft    = round(run_mm / 304.8, 6)
            branch_ft = round(branch_mm / 304.8, 6)
            samples.append(_s(
                f"Create a pipe tee with {run_mm}mm run and {branch_mm}mm branch",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Pipe Tee {run_mm}x{branch_mm}"))
{{
    tx.Start();

    double runDiam    = {run_ft}; // {run_mm} mm run
    double branchDiam = {branch_ft}; // {branch_mm} mm branch
    double halfLen    = {run_ft};

    ConnectorElement runIn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, runDiam, new XYZ(-halfLen, 0, 0));
    runIn.FlowDirection = FlowDirectionType.In;

    ConnectorElement runOut = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, runDiam, new XYZ( halfLen, 0, 0));
    runOut.FlowDirection = FlowDirectionType.Out;

    ConnectorElement branch = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, branchDiam,
        new XYZ(0, 0, {branch_ft}));
    branch.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}}"""))

        return samples

    # ------------------------------------------------------------------
    # Duct fittings
    # ------------------------------------------------------------------

    def _duct_fittings(self) -> List[SAMPLE]:
        samples = []

        samples.append(_s(
            "Create a 90-degree rectangular duct elbow fitting, 400x200mm",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Rect Duct Elbow 90"))
{
    tx.Start();

    double width  = 1.312336; // 400 mm
    double height = 0.656168; // 200 mm
    double bendR  = 1.312336; // 400 mm bend radius (1W)

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
}"""))

        samples.append(_s(
            "Create a 90-degree round duct elbow fitting, 315mm diameter",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Round Duct Elbow 90"))
{
    tx.Start();

    double diameter = 1.033465; // 315 mm
    double bendR    = 1.551837; // 473 mm (1.5D)

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
}"""))

        samples.append(_s(
            "Create a rectangular-to-round duct transition fitting (400x200mm rect to 315mm round)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Duct Transition"))
{
    tx.Start();

    double length = 0.984252; // 300 mm

    ConnectorElement rectConn = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular, XYZ.Zero);
    rectConn.Width  = 1.312336; // 400 mm
    rectConn.Height = 0.656168; // 200 mm
    rectConn.FlowDirection = FlowDirectionType.In;

    ConnectorElement roundConn = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Round,
        new XYZ(0, 0, length));
    roundConn.Radius = 0.516732; // 157.5 mm radius
    roundConn.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}"""))

        samples.append(_s(
            "Create a rectangular duct tee fitting, 600x300mm main, 400x200mm branch",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Duct Tee"))
{
    tx.Start();

    double mainW = 1.968504; double mainH = 0.984252;
    double brnW  = 1.312336; double brnH  = 0.656168;
    double halfRun = 1.312336;

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
        new XYZ(0, 0, 0.984252)); // 300 mm up
    branch.Width = brnW; branch.Height = brnH;
    branch.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}"""))

        samples.append(_s(
            "Create a concentric rectangular duct reducer, 600x300mm to 400x200mm",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Duct Reducer"))
{
    tx.Start();

    double length = 0.984252; // 300 mm

    ConnectorElement largeEnd = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular, XYZ.Zero);
    largeEnd.Width = 1.968504; largeEnd.Height = 0.984252;
    largeEnd.FlowDirection = FlowDirectionType.In;

    ConnectorElement smallEnd = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ(0, 0, length));
    smallEnd.Width = 1.312336; smallEnd.Height = 0.656168;
    smallEnd.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}"""))

        samples.append(_s(
            "Create a 45-degree rectangular duct elbow, 300x200mm",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;
using System;

using (Transaction tx = new Transaction(familyDoc, "Create Duct Elbow 45"))
{
    tx.Start();

    double width = 0.984252; double height = 0.656168;
    double bendR = 0.984252; // 1W
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
}"""))

        samples.append(_s(
            "Create a duct wye fitting with 45-degree branch, 500x250mm main, 300x200mm branch",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;
using System;

using (Transaction tx = new Transaction(familyDoc, "Create Duct Wye"))
{
    tx.Start();

    double mainW = 1.640420; double mainH = 0.820210;
    double brnW  = 0.984252; double brnH  = 0.656168;
    double halfRun = 0.984252; double brnLen = 0.820210;
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
}"""))

        samples.append(_s(
            "Create a rectangular duct end cap fitting, 400x200mm",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Duct Cap"))
{
    tx.Start();

    ConnectorElement conn = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular, XYZ.Zero);
    conn.Width = 1.312336; conn.Height = 0.656168;
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}"""))

        samples.append(_s(
            "Create a return air duct tee fitting, 800x400mm main, 400x300mm branch",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Return Air Tee"))
{
    tx.Start();

    double halfRun = 1.640420;

    ConnectorElement mainIn = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.ReturnAir, ConnectorProfileType.Rectangular,
        new XYZ(-halfRun, 0, 0));
    mainIn.Width = 2.624672; mainIn.Height = 1.312336;
    mainIn.FlowDirection = FlowDirectionType.In;

    ConnectorElement mainOut = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.ReturnAir, ConnectorProfileType.Rectangular,
        new XYZ( halfRun, 0, 0));
    mainOut.Width = 2.624672; mainOut.Height = 1.312336;
    mainOut.FlowDirection = FlowDirectionType.Out;

    ConnectorElement branch = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.ReturnAir, ConnectorProfileType.Rectangular,
        new XYZ(0, 0, 0.984252));
    branch.Width = 1.312336; branch.Height = 0.984252;
    branch.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}"""))

        samples.append(_s(
            "Create a duct offset (S-curve) fitting, 400x200mm, 300mm lateral offset",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Duct Offset"))
{
    tx.Start();

    double width = 1.312336; double height = 0.656168;
    double axial = 1.968504; double lateral = 0.984252;

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
}"""))

        for w_mm, h_mm in [(300, 150), (500, 300)]:
            w_ft = round(w_mm / 304.8, 6)
            h_ft = round(h_mm / 304.8, 6)
            samples.append(_s(
                f"Create a 90-degree rectangular duct elbow, {w_mm}x{h_mm}mm",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create Duct Elbow {w_mm}x{h_mm}"))
{{
    tx.Start();

    double width = {w_ft}; double height = {h_ft};
    double bendR = {w_ft}; // 1W

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
}}"""))

        return samples

    # ------------------------------------------------------------------
    # Equipment families
    # ------------------------------------------------------------------

    def _equipment_families(self) -> List[SAMPLE]:
        samples = []

        # VAV box
        samples.append(_s(
            "Create a VAV (Variable Air Volume) box family with supply duct inlet and outlet connectors",
            """\
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
{
    tx.Start();

    // Body geometry: 600x400x300mm box
    double bw = 1.968504; double bd = 1.312336; double bh = 0.984252;
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
    inlet.Radius = 0.328084; // 200 mm dia
    inlet.FlowDirection = FlowDirectionType.In;

    // Rectangular outlet connector (downstream to diffusers)
    ConnectorElement outlet = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ( bw / 2, 0, bh / 2));
    outlet.Width  = 1.312336;
    outlet.Height = 0.656168;
    outlet.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}"""))

        # AHU (Air Handling Unit)
        samples.append(_s(
            "Create an Air Handling Unit (AHU) family with supply, return, and outdoor air duct connectors",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;

using (Transaction tx = new Transaction(familyDoc, "Create AHU"))
{
    tx.Start();

    // AHU body: 2000x1200x1800mm
    double bw = 6.561680; double bd = 3.937008; double bh = 5.905512;
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
    supply.Width = 2.624672; supply.Height = 1.312336;
    supply.FlowDirection = FlowDirectionType.Out;

    // Return air inlet (front face)
    ConnectorElement ret = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.ReturnAir, ConnectorProfileType.Rectangular,
        new XYZ(bw / 2, 0, bh / 2));
    ret.Width = 2.624672; ret.Height = 1.640420;
    ret.FlowDirection = FlowDirectionType.In;

    // Outdoor air intake (side)
    ConnectorElement oa = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.OtherAir, ConnectorProfileType.Rectangular,
        new XYZ(0, bd / 2, bh / 2));
    oa.Width = 1.312336; oa.Height = 0.984252;
    oa.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}"""))

        # Chilled water pump
        samples.append(_s(
            "Create a chilled water pump family with suction and discharge pipe connectors",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Chilled Water Pump"))
{
    tx.Start();

    // Pump body: 600x400x500mm
    double bw = 1.968504; double bd = 1.312336; double bh = 1.640420;
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
        0.328084, // 100 mm suction
        new XYZ(-bw / 2, 0, bh / 2));
    suction.FlowDirection = FlowDirectionType.In;

    // Discharge outlet (right side, reduced to 80mm)
    ConnectorElement discharge = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic,
        0.262467, // 80 mm discharge
        new XYZ( bw / 2, 0, bh / 2));
    discharge.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}"""))

        # Fan coil unit
        samples.append(_s(
            "Create a fan coil unit (FCU) family with supply/return hydronic pipe connectors and supply duct connector",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Mechanical;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Fan Coil Unit"))
{
    tx.Start();

    double bw = 2.624672; double bd = 0.984252; double bh = 0.656168;

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
        familyDoc, PipeSystemType.SupplyHydronic, 0.082021, // 25 mm
        new XYZ(-bw / 2 + 0.164042, 0, 0));
    cwSupply.FlowDirection = FlowDirectionType.In;

    // Chilled water return
    ConnectorElement cwReturn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.ReturnHydronic, 0.082021, // 25 mm
        new XYZ(-bw / 2 + 0.328084, 0, 0));
    cwReturn.FlowDirection = FlowDirectionType.Out;

    // Supply air duct outlet (bottom)
    ConnectorElement airOut = ConnectorElement.CreateDuctConnector(
        familyDoc, DuctSystemType.SupplyAir, ConnectorProfileType.Rectangular,
        new XYZ(0, 0, bh));
    airOut.Width = 1.968504; airOut.Height = 0.328084;
    airOut.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}"""))

        # Boiler family
        samples.append(_s(
            "Create a hot water boiler family with supply and return hydronic pipe connectors and gas connector",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Boiler"))
{
    tx.Start();

    double bw = 3.280840; double bd = 1.968504; double bh = 3.937008;

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
        familyDoc, PipeSystemType.SupplyHydronic, 0.328084,
        new XYZ(0.492126, 0, bh));
    hwSupply.FlowDirection = FlowDirectionType.Out;

    // HW return (top)
    ConnectorElement hwReturn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.ReturnHydronic, 0.328084,
        new XYZ(-0.492126, 0, bh));
    hwReturn.FlowDirection = FlowDirectionType.In;

    // Gas supply (back, bottom)
    ConnectorElement gas = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.OtherPipe, 0.164042,
        new XYZ(0, -bd / 2, 0.328084));
    gas.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}"""))

        # Cooling tower
        samples.append(_s(
            "Create a cooling tower family with condenser water supply and return pipe connectors",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Cooling Tower"))
{
    tx.Start();

    double bw = 6.561680; double bd = 6.561680; double bh = 9.842520;

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
        familyDoc, PipeSystemType.SupplyHydronic, 0.656168,
        new XYZ(0, -bd / 2, 1.640420));
    cwsIn.FlowDirection = FlowDirectionType.In;

    // Condenser water return (cooled water back to chillers)
    ConnectorElement cwsOut = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.ReturnHydronic, 0.656168,
        new XYZ(0, -bd / 2, 0.984252));
    cwsOut.FlowDirection = FlowDirectionType.Out;

    // Makeup water
    ConnectorElement makeup = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticColdWater, 0.082021,
        new XYZ(bw / 2, 0, 2.624672));
    makeup.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}"""))

        # Heat exchanger
        samples.append(_s(
            "Create a plate heat exchanger family with primary and secondary hydronic pipe connectors",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Heat Exchanger"))
{
    tx.Start();

    double bw = 2.624672; double bd = 0.984252; double bh = 3.280840;

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
        familyDoc, PipeSystemType.SupplyHydronic, 0.328084,
        new XYZ(-bw / 2, 0, bh * 0.8));
    priIn.FlowDirection = FlowDirectionType.In;

    ConnectorElement priOut = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.ReturnHydronic, 0.328084,
        new XYZ(-bw / 2, 0, bh * 0.2));
    priOut.FlowDirection = FlowDirectionType.Out;

    // Secondary circuit (right side: supply out, return in)
    ConnectorElement secOut = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, 0.262467,
        new XYZ( bw / 2, 0, bh * 0.8));
    secOut.FlowDirection = FlowDirectionType.Out;

    ConnectorElement secIn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.ReturnHydronic, 0.262467,
        new XYZ( bw / 2, 0, bh * 0.2));
    secIn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}"""))

        # Expansion tank
        samples.append(_s(
            "Create a hydronic expansion tank family with a single pipe connector",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;
using System;

using (Transaction tx = new Transaction(familyDoc, "Create Expansion Tank"))
{
    tx.Start();

    // Cylindrical tank body: 400mm diameter, 600mm tall
    double r = 0.656168; // 200 mm radius
    double h = 1.968504; // 600 mm height
    int n = 32;
    CurveArray tankLoop = new CurveArray();
    for (int i = 0; i < n; i++)
    {
        double a0 = 2 * Math.PI * i / n;
        double a1 = 2 * Math.PI * (i + 1) / n;
        tankLoop.Append(Line.CreateBound(
            new XYZ(r * Math.Cos(a0), r * Math.Sin(a0), 0),
            new XYZ(r * Math.Cos(a1), r * Math.Sin(a1), 0)));
    }
    CurveArrArray profile = new CurveArrArray();
    profile.Append(tankLoop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    // Single bottom connection
    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, 0.131234, // 40 mm
        XYZ.Zero);
    conn.FlowDirection = FlowDirectionType.Bidirectional;

    tx.Commit();
}"""))

        # Chiller
        samples.append(_s(
            "Create a water-cooled chiller family with chilled water and condenser water pipe connectors",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Chiller"))
{
    tx.Start();

    double bw = 9.842520; double bd = 3.937008; double bh = 4.921260;

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
        familyDoc, PipeSystemType.SupplyHydronic, 0.656168,
        new XYZ(-1.968504, -bd / 2, 1.312336));
    chwSupply.FlowDirection = FlowDirectionType.Out;

    // Chilled water return (into evaporator)
    ConnectorElement chwReturn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.ReturnHydronic, 0.656168,
        new XYZ(-0.984252, -bd / 2, 1.312336));
    chwReturn.FlowDirection = FlowDirectionType.In;

    // Condenser water supply (warm CW into condenser)
    ConnectorElement cwsIn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.SupplyHydronic, 0.656168,
        new XYZ(0.984252, -bd / 2, 1.312336));
    cwsIn.FlowDirection = FlowDirectionType.In;

    // Condenser water return (cooled CW back to tower)
    ConnectorElement cwsOut = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.ReturnHydronic, 0.656168,
        new XYZ(1.968504, -bd / 2, 1.312336));
    cwsOut.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}"""))


        # Additional equipment variants
        # Plate-and-frame heat exchanger
        samples.append(_s(
            "Create a domestic hot water heater family with cold water inlet, hot water outlet, and flue connector",
            """\
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
}"""))

        # Variable refrigerant flow (VRF) indoor unit
        samples.append(_s(
            "Create a VRF indoor cassette unit family with refrigerant pipe connectors and supply/return air duct connectors",
            """\
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
}"""))

        # Pressure reducing valve (PRV) station
        samples.append(_s(
            "Create a pressure reducing valve (PRV) station family with high-pressure inlet and reduced-pressure outlet",
            """\
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
}"""))

        # Pump with VFD parameter
        samples.append(_s(
            "Create a variable speed pump family with inlet/outlet pipe connectors and speed parameter",
            """\
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
}"""))

        return samples

    # ------------------------------------------------------------------
    # Electrical fixtures
    # ------------------------------------------------------------------

    def _electrical_fixtures(self) -> List[SAMPLE]:
        samples = []

        # Recessed lighting
        samples.append(_s(
            "Create a recessed light fixture family with an electrical connector (120V, 26W LED)",
            """\
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
{
    tx.Start();

    // Housing: 200mm diameter, 150mm deep cylinder
    double r = 0.328084; // 100 mm radius
    double depth = 0.492126; // 150 mm
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
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, depth);

    // Electrical connector at top of housing
    ConnectorElement elecConn = ConnectorElement.CreateElectricalConnector(
        familyDoc,
        ElectricalSystemType.PowerBalanced,
        new XYZ(0, 0, depth));
    elecConn.Voltage   = 120.0; // 120V
    elecConn.WiringType = WiringType.SinglePhase;

    tx.Commit();
}"""))

        # Linear fluorescent fixture
        samples.append(_s(
            "Create a 1200mm linear LED fixture family with a single-phase 277V electrical connector",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pLength = famMgr.AddParameter(
    "Fixture Length",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length,
    false);
famMgr.Set(pLength, 3.937008); // 1200 mm

using (Transaction tx = new Transaction(familyDoc, "Create Linear LED Fixture"))
{
    tx.Start();

    double length = 3.937008; // 1200 mm
    double width  = 0.246063;   // 75 mm
    double height = 0.196850;   // 60 mm

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
}"""))

        # Pendant light
        samples.append(_s(
            "Create a pendant light fixture family with a 120V electrical connector at the canopy",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

using (Transaction tx = new Transaction(familyDoc, "Create Pendant Light"))
{
    tx.Start();

    // Canopy plate at top: 150mm disc
    double cR = 0.246063;  // 75 mm radius
    double cH = 0.065617;  // 20 mm thick
    int n = 24;
    CurveArray canopyLoop = new CurveArray();
    for (int i = 0; i < n; i++)
    {
        double a0 = 2 * System.Math.PI * i / n;
        double a1 = 2 * System.Math.PI * (i + 1) / n;
        canopyLoop.Append(Line.CreateBound(
            new XYZ(cR * System.Math.Cos(a0), cR * System.Math.Sin(a0), 0),
            new XYZ(cR * System.Math.Cos(a1), cR * System.Math.Sin(a1), 0)));
    }
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
}"""))

        # Emergency exit sign
        samples.append(_s(
            "Create an emergency exit sign family with a 120V electrical connector and battery backup parameter",
            """\
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
{
    tx.Start();

    double w = 0.984252; double h_sign = 0.426509; double depth = 0.131234;

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
}"""))

        # Duplex receptacle
        samples.append(_s(
            "Create a duplex wall receptacle family with a 120V 20A electrical connector",
            """\
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
{
    tx.Start();

    double w = 0.229659; double h = 0.393701; double d = 0.098425;

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
}"""))

        # Panel board
        samples.append(_s(
            "Create an electrical panel family with a 3-phase 208V electrical connector",
            """\
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
{
    tx.Start();

    double w = 1.640420; double d = 0.328084; double h = 2.952756;

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
}"""))

        # Occupancy sensor
        samples.append(_s(
            "Create a ceiling occupancy sensor family with a low-voltage electrical connector",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

using (Transaction tx = new Transaction(familyDoc, "Create Occupancy Sensor"))
{
    tx.Start();

    double r = 0.164042; // 50 mm radius
    double h = 0.098425; // 30 mm height
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

    ConnectorElement conn = ConnectorElement.CreateElectricalConnector(
        familyDoc,
        ElectricalSystemType.PowerUnBalanced,
        new XYZ(0, 0, h));
    conn.Voltage    = 24.0; // 24V low-voltage
    conn.WiringType = WiringType.SinglePhase;

    tx.Commit();
}"""))

        # Data outlet (network)
        samples.append(_s(
            "Create a data outlet family with a telephone/data electrical connector",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

using (Transaction tx = new Transaction(familyDoc, "Create Data Outlet"))
{
    tx.Start();

    double w = 0.229659; double d = 0.098425; double h = 0.295276;

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
}"""))

        # Transformer
        samples.append(_s(
            "Create a dry-type transformer family with primary (480V) and secondary (120/208V) electrical connectors",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

using (Transaction tx = new Transaction(familyDoc, "Create Transformer"))
{
    tx.Start();

    double bw = 2.624672; double bd = 1.640420; double bh = 2.952756;

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
        new XYZ(-0.656168, 0, bh));
    primary.Voltage    = 480.0;
    primary.WiringType = WiringType.ThreePhase;

    // Secondary output (208V 3-phase)
    ConnectorElement secondary = ConnectorElement.CreateElectricalConnector(
        familyDoc,
        ElectricalSystemType.PowerBalanced,
        new XYZ( 0.656168, 0, bh));
    secondary.Voltage    = 208.0;
    secondary.WiringType = WiringType.ThreePhase;

    tx.Commit();
}"""))

        # Smoke detector
        samples.append(_s(
            "Create a smoke detector family with a fire alarm electrical connector",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;

using (Transaction tx = new Transaction(familyDoc, "Create Smoke Detector"))
{
    tx.Start();

    double r = 0.180446; // 55 mm radius
    double h = 0.131234; // 40 mm height
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

    ConnectorElement conn = ConnectorElement.CreateElectricalConnector(
        familyDoc,
        ElectricalSystemType.FireAlarm,
        new XYZ(0, 0, h));

    tx.Commit();
}"""))


        # Additional electrical fixture variants
        samples.append(_s(
            "Create a wall-mounted sconce fixture family with 120V single-phase electrical connector",
            """\
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
}"""))

        samples.append(_s(
            "Create an outdoor area light pole family with 240V single-phase electrical connector",
            """\
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
}"""))

        samples.append(_s(
            "Create a track lighting track family with a 120V circuit electrical connector and multiple fixture slots",
            """\
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
}"""))

        samples.append(_s(
            "Create a motor control center (MCC) bucket family with 480V 3-phase electrical connector",
            """\
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
}"""))

        samples.append(_s(
            "Create a GFCI outlet family with 120V 20A electrical connector and a TEST/RESET annotation",
            """\
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
}"""))

        return samples

    # ------------------------------------------------------------------
    # Sprinkler heads
    # ------------------------------------------------------------------

    def _sprinkler_heads(self) -> List[SAMPLE]:
        samples = []

        # Standard pendent sprinkler
        samples.append(_s(
            "Create a standard pendent fire sprinkler head family with a 25mm pipe connector and K-factor parameter",
            """\
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
{
    tx.Start();

    // Body: small cylinder 25mm dia, 100mm long (the frame arms + deflector below)
    double r = 0.041010; // 12.5 mm radius
    double h = 0.328084;  // 100 mm
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

    // Pipe connector at top (connects to wet pipe system)
    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc,
        PipeSystemType.FireProtectWet,
        0.082021, // 25 mm (1 inch nominal)
        new XYZ(0, 0, h));
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}"""))

        # Upright sprinkler
        samples.append(_s(
            "Create an upright fire sprinkler head family with a 25mm wet pipe connector",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pKFactor = famMgr.AddParameter(
    "K-Factor", BuiltInParameterGroup.PG_MECHANICAL_FLOW, ParameterType.Number, false);
famMgr.Set(pKFactor, 5.6);

using (Transaction tx = new Transaction(familyDoc, "Create Upright Sprinkler"))
{
    tx.Start();

    double r = 0.041010;
    double h = 0.262467;
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

    // Upright connector points downward (pipe above, water sprays up then down)
    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.FireProtectWet, 0.082021, XYZ.Zero);
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}"""))

        # Concealed sprinkler
        samples.append(_s(
            "Create a concealed fire sprinkler head family with a 25mm pipe connector and cover plate",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Concealed Sprinkler"))
{
    tx.Start();

    // Cover plate (flush with ceiling): 100mm disc
    double cpR = 0.164042;
    int n = 24;
    CurveArray cpLoop = new CurveArray();
    for (int i = 0; i < n; i++)
    {
        double a0 = 2 * System.Math.PI * i / n;
        double a1 = 2 * System.Math.PI * (i + 1) / n;
        cpLoop.Append(Line.CreateBound(
            new XYZ(cpR * System.Math.Cos(a0), cpR * System.Math.Sin(a0), 0),
            new XYZ(cpR * System.Math.Cos(a1), cpR * System.Math.Sin(a1), 0)));
    }
    CurveArrArray profile = new CurveArrArray();
    profile.Append(cpLoop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, 0.016404); // 5 mm thin

    // Pipe connector above cover plate
    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.FireProtectWet, 0.082021,
        new XYZ(0, 0, 0.164042)); // 50 mm above
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}"""))

        # Dry pipe sprinkler
        samples.append(_s(
            "Create a dry pipe sprinkler head family with a 25mm dry fire protection connector",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

FamilyManager famMgr = familyDoc.FamilyManager;
famMgr.AddParameter("K-Factor", BuiltInParameterGroup.PG_MECHANICAL_FLOW, ParameterType.Number, false);

using (Transaction tx = new Transaction(familyDoc, "Create Dry Pipe Sprinkler"))
{
    tx.Start();

    double r = 0.041010;
    double h = 0.328084;
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

    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.FireProtectDry, 0.082021,
        new XYZ(0, 0, h));
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}"""))

        # ESFR sprinkler (larger K-factor)
        samples.append(_s(
            "Create an ESFR (Early Suppression Fast Response) sprinkler family with 50mm pipe connector, K14 factor",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pKFactor = famMgr.AddParameter(
    "K-Factor", BuiltInParameterGroup.PG_MECHANICAL_FLOW, ParameterType.Number, false);
famMgr.Set(pKFactor, 14.0); // K14 ESFR

using (Transaction tx = new Transaction(familyDoc, "Create ESFR Sprinkler"))
{
    tx.Start();

    double r = 0.082021; // larger head body
    double h = 0.393701;
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

    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.FireProtectWet,
        0.164042, // 50 mm (2 inch) large orifice
        new XYZ(0, 0, h));
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}"""))

        # Sidewall sprinkler
        samples.append(_s(
            "Create a horizontal sidewall sprinkler family with a 25mm pipe connector oriented horizontally",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Sidewall Sprinkler"))
{
    tx.Start();

    double r = 0.041010;
    double h = 0.262467;
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

    // Sidewall: connector at side face, pointing in -Y direction (into wall pipe)
    ConnectorElement conn = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.FireProtectWet, 0.082021,
        new XYZ(0, 0.131234, h / 2.0)); // offset to wall side
    conn.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}"""))


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
                f"""\
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
}}}}"""))

        return samples

    # ------------------------------------------------------------------
    # Plumbing fixtures
    # ------------------------------------------------------------------

    def _plumbing_fixtures(self) -> List[SAMPLE]:
        samples = []

        # Sink
        samples.append(_s(
            "Create a single-basin sink family with hot water, cold water, and drain pipe connectors",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Sink"))
{
    tx.Start();

    // Sink body: 600x500x200mm
    double bw = 1.968504; double bd = 1.640420; double bh = 0.656168;
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
        familyDoc, PipeSystemType.DomesticHotWater, 0.049213, // 15 mm (1/2" nom.)
        new XYZ(-0.328084, -bd / 2, -bh / 2));
    hot.FlowDirection = FlowDirectionType.In;

    // Cold water supply (right side under sink)
    ConnectorElement cold = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticColdWater, 0.049213,
        new XYZ( 0.328084, -bd / 2, -bh / 2));
    cold.FlowDirection = FlowDirectionType.In;

    // Drain (center bottom)
    ConnectorElement drain = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.Sanitary, 0.131234, // 40 mm (1-1/2" nom.)
        new XYZ(0, 0, -bh));
    drain.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}"""))

        # Water closet (toilet)
        samples.append(_s(
            "Create a wall-hung water closet (toilet) family with cold water supply and sanitary drain connectors",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Water Closet"))
{
    tx.Start();

    double bw = 1.246719; double bd = 2.230971; double bh = 1.312336;
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
        familyDoc, PipeSystemType.DomesticColdWater, 0.065617, // 20 mm
        new XYZ(0, bd, 0.820210)); // 250mm AFF back wall
    cwSupply.FlowDirection = FlowDirectionType.In;

    // Sanitary drain (rough-in at floor)
    ConnectorElement sanDrain = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.Sanitary, 0.328084, // 100 mm (4")
        new XYZ(0, 0.656168, 0)); // 200 mm from wall rough-in
    sanDrain.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}"""))

        # Bathtub
        samples.append(_s(
            "Create a bathtub family with hot, cold water supply and drain/overflow connectors",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Bathtub"))
{
    tx.Start();

    double bw = 2.493438; double bd = 4.986877; double bh = 1.410761;
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
        familyDoc, PipeSystemType.DomesticHotWater, 0.049213,
        new XYZ(-0.246063, bd, 0.656168));
    hot.FlowDirection = FlowDirectionType.In;

    // Cold supply
    ConnectorElement cold = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticColdWater, 0.049213,
        new XYZ( 0.246063, bd, 0.656168));
    cold.FlowDirection = FlowDirectionType.In;

    // Drain (foot end, near floor)
    ConnectorElement drain = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.Sanitary, 0.131234,
        new XYZ(0, 0.328084, 0));
    drain.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}"""))

        # Floor drain
        samples.append(_s(
            "Create a floor drain family with a 100mm sanitary drain connector and trap primer port",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Floor Drain"))
{
    tx.Start();

    // Drain body: 200mm square
    double w = 0.656168;
    CurveArrArray profile = new CurveArrArray();
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-w/2, -w/2, 0), new XYZ( w/2, -w/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2, -w/2, 0), new XYZ( w/2,  w/2, 0)));
    loop.Append(Line.CreateBound(new XYZ( w/2,  w/2, 0), new XYZ(-w/2,  w/2, 0)));
    loop.Append(Line.CreateBound(new XYZ(-w/2,  w/2, 0), new XYZ(-w/2, -w/2, 0)));
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, 0.328084); // 100 mm body

    // Main drain outlet (below floor)
    ConnectorElement drain = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.Sanitary, 0.328084, // 100 mm (4")
        new XYZ(0, 0, -0.328084)); // below body
    drain.FlowDirection = FlowDirectionType.Out;

    // Trap primer port (small cold water inlet)
    ConnectorElement trapPrime = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticColdWater, 0.049213,
        new XYZ(w / 2, 0, -0.164042));
    trapPrime.FlowDirection = FlowDirectionType.In;

    tx.Commit();
}"""))

        # Urinal
        samples.append(_s(
            "Create a wall-hung urinal family with cold water supply and sanitary drain connectors",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Urinal"))
{
    tx.Start();

    double bw = 1.148294; double bd = 1.049869; double bh = 1.837270;
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
        familyDoc, PipeSystemType.DomesticColdWater, 0.065617,
        new XYZ(0, bd, bh * 0.9));
    cold.FlowDirection = FlowDirectionType.In;

    // Sanitary drain (below fixture)
    ConnectorElement drain = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.Sanitary, 0.164042, // 50 mm (2")
        new XYZ(0, 0.328084, 0));
    drain.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}"""))

        # Shower base
        samples.append(_s(
            "Create a shower base family with hot/cold supply and drain connectors",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

using (Transaction tx = new Transaction(familyDoc, "Create Shower Base"))
{
    tx.Start();

    double bw = 2.952756; double bd = 2.952756; double bh = 0.196850;
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
        familyDoc, PipeSystemType.DomesticHotWater, 0.049213,
        new XYZ(-0.164042, -bd / 2, bh + 0.656168));
    hot.FlowDirection = FlowDirectionType.In;

    ConnectorElement cold = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.DomesticColdWater, 0.049213,
        new XYZ( 0.164042, -bd / 2, bh + 0.656168));
    cold.FlowDirection = FlowDirectionType.In;

    // Center drain
    ConnectorElement drain = ConnectorElement.CreatePipeConnector(
        familyDoc, PipeSystemType.Sanitary, 0.164042,
        new XYZ(0, 0, 0));
    drain.FlowDirection = FlowDirectionType.Out;

    tx.Commit();
}"""))


        # Additional plumbing fixture variants
        # Utility sink
        samples.append(_s(
            "Create a utility (mop) sink family with hot/cold supply and 75mm drain connector",
            """\
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
}"""))

        # Drinking fountain
        samples.append(_s(
            "Create a wall-mounted drinking fountain family with cold water supply and drain connectors",
            """\
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
}"""))

        # Laundry tub
        samples.append(_s(
            "Create a laundry tub family with hot/cold supply, 50mm drain, and standpipe for washer",
            """\
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
}"""))

        # Hose bib / sill cock
        samples.append(_s(
            "Create a hose bib (sill cock) family with a 15mm cold water pipe connector",
            """\
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
}"""))

        # Condensate drain pan
        samples.append(_s(
            "Create a condensate drain pan family for a split system, with a 20mm sanitary drain connector",
            """\
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
}"""))

        return samples

    # ------------------------------------------------------------------
    # Connector parameters
    # ------------------------------------------------------------------

    def _connector_parameters(self) -> List[SAMPLE]:
        samples = []

        samples.append(_s(
            "Set the domain of a connector to Piping using ConnectorDomain enumeration",
            """\
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
}}"""))

        samples.append(_s(
            "Set a duct connector system type to ExhaustAir versus SupplyAir",
            """\
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
}}"""))

        samples.append(_s(
            "Associate a connector flow parameter to a family parameter so it drives from the type table",
            """\
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
}}"""))

        samples.append(_s(
            "Set pressure drop parameters on a pipe connector for hydraulic calculations",
            """\
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
}}"""))

        samples.append(_s(
            "Create a bidirectional pipe connector for an expansion tank or pressure gauge port",
            """\
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
}}"""))

        samples.append(_s(
            "Enumerate all ConnectorElement objects in a family document to inspect their properties",
            """\
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
"""))

        samples.append(_s(
            "Set a duct connector velocity pressure parameter for system analysis",
            """\
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
}}"""))

        samples.append(_s(
            "Create a connector with a specific coordinate system (connector face orientation) using SetCoordinateSystem",
            """\
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
}}"""))

        samples.append(_s(
            "Create multiple connectors with different system types in one family to represent a multi-service terminal",
            """\
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
}}"""))

        samples.append(_s(
            "Read connector flow direction and system type from an existing connector element",
            """\
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
"""))

        return samples
