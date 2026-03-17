"""Training data generator: Revit wall-hosted family patterns.

Produces ~250 Alpaca-format training pairs covering basic walls, curtain walls,
wall openings, compound wall layers, and wall-hosted elements.
"""

from __future__ import annotations

from typing import Any, Dict, List

SAMPLE = Dict[str, Any]
MM_TO_FT = 1.0 / 304.8
INCH_TO_FT = 1.0 / 12.0


def _s(instruction: str, output: str) -> SAMPLE:
    return {"instruction": instruction, "input": "", "output": output}


def _ft(mm: float) -> str:
    return f"{mm * MM_TO_FT:.6f}"


class WallFamilyGenerator:
    """Generates training samples for Revit wall family creation and wall-hosted patterns."""

    def generate(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []
        samples += self._basic_walls()
        samples += self._wall_hosted_families()
        samples += self._curtain_walls()
        samples += self._wall_openings()
        samples += self._compound_wall_layers()
        samples += self._wall_parameters()
        samples += self._wall_sweeps_reveals()
        return samples

    # ------------------------------------------------------------------
    # Basic wall creation
    # ------------------------------------------------------------------

    def _basic_walls(self) -> List[SAMPLE]:
        samples = []
        cases = [
            (3600, 3000, "Create a basic wall 3600mm long, 3000mm high"),
            (5000, 2700, "Create a standard partition wall 5000mm long, 2700mm high"),
            (7200, 4200, "Create a tall exterior wall 7200mm long, 4200mm high"),
            (1200, 2100, "Create a short corridor wall 1200mm long, 2100mm high"),
            (9000, 3600, "Create a long structural wall 9000mm long, 3600mm high"),
            (2400, 2400, "Create a square room wall 2400mm long, 2400mm high"),
            (4500, 3300, "Create a commercial office wall 4500mm long, 3300mm high"),
        ]
        for length_mm, height_mm, instruction in cases:
            l_ft = _ft(length_mm)
            h_ft = _ft(height_mm)
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;

// {instruction}
using (Transaction tx = new Transaction(doc, "Create Wall"))
{{
    tx.Start();

    double length = {l_ft}; // {length_mm} mm
    double height = {h_ft}; // {height_mm} mm

    Line wallLine = Line.CreateBound(XYZ.Zero, new XYZ(length, 0, 0));

    Level level = new FilteredElementCollector(doc)
        .OfClass(typeof(Level))
        .Cast<Level>()
        .FirstOrDefault();

    WallType wallType = new FilteredElementCollector(doc)
        .OfClass(typeof(WallType))
        .Cast<WallType>()
        .First(wt => wt.Kind == WallKind.Basic);

    Wall wall = Wall.Create(doc, wallLine, wallType.Id, level.Id,
        height, 0, false, false);

    tx.Commit();
}}"""))

        # Angled wall
        samples.append(_s("Create a diagonal wall at 45 degrees, 5000mm long, 3000mm high",
            f"""\
using Autodesk.Revit.DB;
using System;

// Diagonal wall at 45 degrees
using (Transaction tx = new Transaction(doc, "Create Diagonal Wall"))
{{
    tx.Start();

    double length = {_ft(5000)}; // 5000 mm
    double height = {_ft(3000)}; // 3000 mm
    double angle  = Math.PI / 4;  // 45 degrees

    XYZ start = XYZ.Zero;
    XYZ end   = new XYZ(length * Math.Cos(angle), length * Math.Sin(angle), 0);

    Line wallLine = Line.CreateBound(start, end);

    Level level = new FilteredElementCollector(doc)
        .OfClass(typeof(Level)).Cast<Level>().FirstOrDefault();

    WallType wallType = new FilteredElementCollector(doc)
        .OfClass(typeof(WallType)).Cast<WallType>()
        .First(wt => wt.Kind == WallKind.Basic);

    Wall wall = Wall.Create(doc, wallLine, wallType.Id, level.Id,
        height, 0, false, false);

    tx.Commit();
}}"""))

        # Curved wall
        samples.append(_s("Create an arc (curved) wall with radius 3000mm and 90-degree sweep",
            f"""\
using Autodesk.Revit.DB;
using System;

// Curved wall: radius 3000mm, 90-degree arc
using (Transaction tx = new Transaction(doc, "Create Curved Wall"))
{{
    tx.Start();

    double radius = {_ft(3000)}; // 3000 mm
    double height = {_ft(3000)}; // 3000 mm

    XYZ center = XYZ.Zero;
    XYZ start  = new XYZ(radius, 0, 0);
    XYZ end    = new XYZ(0, radius, 0);

    Arc arc = Arc.Create(start, end,
        new XYZ(radius * Math.Cos(Math.PI / 4), radius * Math.Sin(Math.PI / 4), 0));

    Level level = new FilteredElementCollector(doc)
        .OfClass(typeof(Level)).Cast<Level>().FirstOrDefault();

    WallType wallType = new FilteredElementCollector(doc)
        .OfClass(typeof(WallType)).Cast<WallType>()
        .First(wt => wt.Kind == WallKind.Basic);

    Wall wall = Wall.Create(doc, arc, wallType.Id, level.Id,
        height, 0, false, false);

    tx.Commit();
}}"""))

        # Wall with offset from level
        samples.append(_s("Create a wall starting 1200mm above base level (base offset), 3600mm high",
            f"""\
using Autodesk.Revit.DB;

// Wall with 1200mm base offset above level
using (Transaction tx = new Transaction(doc, "Create Offset Wall"))
{{
    tx.Start();

    double length     = {_ft(4000)}; // 4000 mm
    double height     = {_ft(3600)}; // 3600 mm
    double baseOffset = {_ft(1200)}; // 1200 mm base offset

    Line wallLine = Line.CreateBound(XYZ.Zero, new XYZ(length, 0, 0));

    Level level = new FilteredElementCollector(doc)
        .OfClass(typeof(Level)).Cast<Level>().FirstOrDefault();

    WallType wallType = new FilteredElementCollector(doc)
        .OfClass(typeof(WallType)).Cast<WallType>()
        .First(wt => wt.Kind == WallKind.Basic);

    Wall wall = Wall.Create(doc, wallLine, wallType.Id, level.Id,
        height, baseOffset, false, false);

    tx.Commit();
}}"""))

        # Flipped wall (exterior face orientation)
        samples.append(_s("Create a wall and flip its orientation so the exterior face points inward",
            f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Create and Flip Wall"))
{{
    tx.Start();

    Line wallLine = Line.CreateBound(XYZ.Zero, new XYZ({_ft(4800)}, 0, 0));

    Level level = new FilteredElementCollector(doc)
        .OfClass(typeof(Level)).Cast<Level>().FirstOrDefault();

    WallType wallType = new FilteredElementCollector(doc)
        .OfClass(typeof(WallType)).Cast<WallType>()
        .First(wt => wt.Kind == WallKind.Basic);

    Wall wall = Wall.Create(doc, wallLine, wallType.Id, level.Id,
        {_ft(3000)}, 0, false, false);

    // Flip the wall orientation
    wall.Flip();

    tx.Commit();
}}"""))

        # Room bounding wall
        samples.append(_s("Create a room-bounding wall and verify it is set as a room bounding element",
            f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Create Room Bounding Wall"))
{{
    tx.Start();

    Line wallLine = Line.CreateBound(XYZ.Zero, new XYZ({_ft(6000)}, 0, 0));

    Level level = new FilteredElementCollector(doc)
        .OfClass(typeof(Level)).Cast<Level>().FirstOrDefault();

    WallType wallType = new FilteredElementCollector(doc)
        .OfClass(typeof(WallType)).Cast<WallType>()
        .First(wt => wt.Kind == WallKind.Basic);

    Wall wall = Wall.Create(doc, wallLine, wallType.Id, level.Id,
        {_ft(2700)}, 0, false, true); // last bool = isStructural; room bounding is default true

    // Confirm room bounding is set
    Parameter rbParam = wall.get_Parameter(BuiltInParameter.WALL_ATTR_ROOM_BOUNDING);
    if (rbParam != null && !rbParam.IsReadOnly)
        rbParam.Set(1); // 1 = true

    tx.Commit();
}}"""))

        return samples  # 12 samples

    # ------------------------------------------------------------------
    # Wall-hosted families
    # ------------------------------------------------------------------

    def _wall_hosted_families(self) -> List[SAMPLE]:
        samples = []

        samples.append(_s("Load a door family and place it in a wall",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;

// Load door family and insert in a wall
using (Transaction tx = new Transaction(doc, "Place Door"))
{{
    tx.Start();

    // Load family from default Revit library
    string familyPath = @"C:\\ProgramData\\Autodesk\\RVT 2024\\Libraries\\US Metric\\Doors\\M_Single-Flush.rfa";
    Family doorFamily = null;
    doc.LoadFamily(familyPath, out doorFamily);

    FamilySymbol symbol = null;
    if (doorFamily != null)
    {{
        symbol = doc.GetElement(doorFamily.GetFamilySymbolIds().First()) as FamilySymbol;
        symbol.Activate();
    }}

    // Find a wall to host the door
    Wall hostWall = new FilteredElementCollector(doc)
        .OfClass(typeof(Wall)).Cast<Wall>().FirstOrDefault();

    if (symbol != null && hostWall != null)
    {{
        // Place at midpoint of wall, at floor level
        LocationCurve lc = hostWall.Location as LocationCurve;
        XYZ midPt = lc.Curve.Evaluate(0.5, true);

        doc.NewFamilyInstance(midPt, symbol, hostWall, StructuralType.NonStructural);
    }}

    tx.Commit();
}}"""))

        samples.append(_s("Load a window family and place multiple instances in a wall at equal spacing",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;

using (Transaction tx = new Transaction(doc, "Place Windows"))
{{
    tx.Start();

    string familyPath = @"C:\\ProgramData\\Autodesk\\RVT 2024\\Libraries\\US Metric\\Windows\\M_Fixed.rfa";
    Family winFamily = null;
    doc.LoadFamily(familyPath, out winFamily);

    FamilySymbol symbol = null;
    if (winFamily != null)
    {{
        symbol = doc.GetElement(winFamily.GetFamilySymbolIds().First()) as FamilySymbol;
        symbol.Activate();
    }}

    Wall hostWall = new FilteredElementCollector(doc)
        .OfClass(typeof(Wall)).Cast<Wall>().FirstOrDefault();

    if (symbol != null && hostWall != null)
    {{
        LocationCurve lc   = hostWall.Location as LocationCurve;
        double wallLength  = lc.Curve.Length;
        int count          = 3;
        double spacing     = wallLength / (count + 1);

        for (int i = 1; i <= count; i++)
        {{
            double t   = (spacing * i) / wallLength;
            XYZ    pt  = lc.Curve.Evaluate(t, true);
            XYZ    ptZ = new XYZ(pt.X, pt.Y, {_ft(1000)}); // 1000mm AFF
            doc.NewFamilyInstance(ptZ, symbol, hostWall, StructuralType.NonStructural);
        }}
    }}

    tx.Commit();
}}"""))

        samples.append(_s("Find all doors in a wall and read their Width and Height parameters",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

// Collect doors hosted in walls and read dimensions
IList<FamilyInstance> doors = new FilteredElementCollector(doc)
    .OfCategory(BuiltInCategory.OST_Doors)
    .OfClass(typeof(FamilyInstance))
    .Cast<FamilyInstance>()
    .ToList();

foreach (FamilyInstance door in doors)
{
    Parameter widthParam  = door.Symbol.get_Parameter(BuiltInParameter.DOOR_WIDTH);
    Parameter heightParam = door.Symbol.get_Parameter(BuiltInParameter.DOOR_HEIGHT);

    if (widthParam  != null) { double wMm = widthParam.AsDouble()  / MM_TO_FT; }
    if (heightParam != null) { double hMm = heightParam.AsDouble() / MM_TO_FT; }
    // MM_TO_FT = 1.0 / 304.8
}"""))

        samples.append(_s("Set a door's rough width and height using BuiltInParameter",
            f"""\
using Autodesk.Revit.DB;

// Set door rough opening dimensions
FamilyInstance door = new FilteredElementCollector(doc)
    .OfCategory(BuiltInCategory.OST_Doors)
    .OfClass(typeof(FamilyInstance))
    .Cast<FamilyInstance>()
    .FirstOrDefault();

if (door != null)
{{
    using (Transaction tx = new Transaction(doc, "Set Door Size"))
    {{
        tx.Start();

        // Rough width: 900mm
        Parameter rwParam = door.Symbol.get_Parameter(BuiltInParameter.DOOR_WIDTH);
        if (rwParam != null && !rwParam.IsReadOnly)
            rwParam.Set({_ft(900)}); // 900 mm

        // Rough height: 2100mm
        Parameter rhParam = door.Symbol.get_Parameter(BuiltInParameter.DOOR_HEIGHT);
        if (rhParam != null && !rhParam.IsReadOnly)
            rhParam.Set({_ft(2100)}); // 2100 mm

        tx.Commit();
    }}
}}"""))

        for (cat, bip, w, h, desc) in [
            ("OST_Windows", "WINDOW_WIDTH",  900, 1200, "window"),
            ("OST_Doors",   "DOOR_WIDTH",    800, 2100, "door"),
        ]:
            samples.append(_s(f"Get the host wall of a {desc} family instance",
                f"""\
using Autodesk.Revit.DB;

// Get the host wall for a {desc}
FamilyInstance fi = new FilteredElementCollector(doc)
    .OfCategory(BuiltInCategory.{cat})
    .OfClass(typeof(FamilyInstance))
    .Cast<FamilyInstance>()
    .FirstOrDefault();

if (fi != null)
{{
    Wall hostWall = fi.Host as Wall;
    if (hostWall != null)
    {{
        double wallThicknessMm = hostWall.Width / MM_TO_FT;
        string wallTypeName    = hostWall.WallType.Name;
    }}
    // MM_TO_FT = 1.0 / 304.8
}}"""))

        samples.append(_s("Place a wall-hosted electrical outlet family at 300mm AFF",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;

using (Transaction tx = new Transaction(doc, "Place Outlet"))
{{
    tx.Start();

    string familyPath = @"C:\\ProgramData\\Autodesk\\RVT 2024\\Libraries\\US Metric\\Electrical\\M_Duplex Receptacle.rfa";
    Family family = null;
    doc.LoadFamily(familyPath, out family);

    Wall hostWall = new FilteredElementCollector(doc)
        .OfClass(typeof(Wall)).Cast<Wall>().FirstOrDefault();

    if (family != null && hostWall != null)
    {{
        FamilySymbol sym = doc.GetElement(family.GetFamilySymbolIds().First()) as FamilySymbol;
        sym.Activate();

        LocationCurve lc = hostWall.Location as LocationCurve;
        XYZ pt = lc.Curve.Evaluate(0.5, true);
        XYZ ptAff = new XYZ(pt.X, pt.Y, {_ft(300)}); // 300 mm AFF

        doc.NewFamilyInstance(ptAff, sym, hostWall, StructuralType.NonStructural);
    }}

    tx.Commit();
}}"""))

        samples.append(_s("Mirror a door family instance about a reference plane",
            f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Mirror Door"))
{{
    tx.Start();

    FamilyInstance door = new FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Doors)
        .OfClass(typeof(FamilyInstance))
        .Cast<FamilyInstance>()
        .FirstOrDefault();

    if (door != null)
    {{
        // Mirror about a vertical plane at x = 0
        Plane mirrorPlane = Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero);
        ElementTransformUtils.MirrorElements(doc,
            new List<ElementId> {{ door.Id }}, mirrorPlane, true);
    }}

    tx.Commit();
}}"""))

        # wall-hosted panel
        samples.append(_s("Create a wall and then place a wall-hosted panel (generic annotation) on it",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;

using (Transaction tx = new Transaction(doc, "Place Wall Panel"))
{{
    tx.Start();

    Line wallLine = Line.CreateBound(XYZ.Zero, new XYZ({_ft(6000)}, 0, 0));

    Level level = new FilteredElementCollector(doc)
        .OfClass(typeof(Level)).Cast<Level>().FirstOrDefault();

    WallType wallType = new FilteredElementCollector(doc)
        .OfClass(typeof(WallType)).Cast<WallType>()
        .First(wt => wt.Kind == WallKind.Basic);

    Wall wall = Wall.Create(doc, wallLine, wallType.Id, level.Id,
        {_ft(3000)}, 0, false, false);

    // Load and place panel family
    string panelPath = @"C:\\ProgramData\\Autodesk\\RVT 2024\\Libraries\\US Metric\\Speciality Equipment\\M_Panel Board-Surface Mounted.rfa";
    Family panelFamily = null;
    doc.LoadFamily(panelPath, out panelFamily);

    if (panelFamily != null)
    {{
        FamilySymbol sym = doc.GetElement(panelFamily.GetFamilySymbolIds().First()) as FamilySymbol;
        sym.Activate();

        // Place at 1500mm AFF, mid-wall
        XYZ pt = new XYZ({_ft(3000)}, 0, {_ft(1500)});
        doc.NewFamilyInstance(pt, sym, wall, StructuralType.NonStructural);
    }}

    tx.Commit();
}}"""))

        return samples  # ~10 samples

    # ------------------------------------------------------------------
    # Curtain walls
    # ------------------------------------------------------------------

    def _curtain_walls(self) -> List[SAMPLE]:
        samples = []

        samples.append(_s("Create a curtain wall 12000mm long, 4500mm high",
            f"""\
using Autodesk.Revit.DB;

// Curtain wall: 12000mm long, 4500mm high
using (Transaction tx = new Transaction(doc, "Create Curtain Wall"))
{{
    tx.Start();

    double length = {_ft(12000)}; // 12000 mm
    double height = {_ft(4500)};  // 4500 mm

    Line wallLine = Line.CreateBound(XYZ.Zero, new XYZ(length, 0, 0));

    Level level = new FilteredElementCollector(doc)
        .OfClass(typeof(Level)).Cast<Level>().FirstOrDefault();

    WallType curtainType = new FilteredElementCollector(doc)
        .OfClass(typeof(WallType))
        .Cast<WallType>()
        .First(wt => wt.Kind == WallKind.Curtain);

    Wall curtainWall = Wall.Create(doc, wallLine, curtainType.Id,
        level.Id, height, 0, false, false);

    tx.Commit();
}}"""))

        samples.append(_s("Set the horizontal grid spacing on a curtain wall to 1500mm",
            f"""\
using Autodesk.Revit.DB;

Wall curtainWall = new FilteredElementCollector(doc)
    .OfClass(typeof(Wall)).Cast<Wall>()
    .First(w => w.WallType.Kind == WallKind.Curtain);

using (Transaction tx = new Transaction(doc, "Set Curtain Grid Spacing"))
{{
    tx.Start();

    CurtainGrid grid = curtainWall.CurtainGrid;

    // Set horizontal (U) grid spacing to 1500mm
    double spacing = {_ft(1500)}; // 1500 mm

    // Use CurtainGridLine spacing parameter
    Parameter hSpacing = curtainWall.WallType.get_Parameter(
        BuiltInParameter.SPACING_LAYOUT_U);
    if (hSpacing != null && !hSpacing.IsReadOnly)
        hSpacing.Set(spacing);

    tx.Commit();
}}"""))

        samples.append(_s("Get all curtain panels from a curtain wall and list their areas",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

Wall curtainWall = new FilteredElementCollector(doc)
    .OfClass(typeof(Wall)).Cast<Wall>()
    .First(w => w.WallType.Kind == WallKind.Curtain);

CurtainGrid grid = curtainWall.CurtainGrid;

ICollection<ElementId> panelIds = grid.GetPanelIds();
foreach (ElementId panelId in panelIds)
{
    Panel panel = doc.GetElement(panelId) as Panel;
    if (panel != null)
    {
        // Panel area in sq-ft internally; convert to sq-m
        double areaSqFt = panel.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)?.AsDouble() ?? 0;
        double areaSqM  = areaSqFt * 0.092903;
    }
}"""))

        samples.append(_s("Replace all curtain panels on a curtain wall with a specific panel type",
            """\
using Autodesk.Revit.DB;

// Replace curtain panels with a specific FamilySymbol
PanelType targetType = new FilteredElementCollector(doc)
    .OfClass(typeof(PanelType))
    .Cast<PanelType>()
    .FirstOrDefault(pt => pt.Name.Contains("Glazed"));

Wall curtainWall = new FilteredElementCollector(doc)
    .OfClass(typeof(Wall)).Cast<Wall>()
    .First(w => w.WallType.Kind == WallKind.Curtain);

if (targetType != null)
{
    using (Transaction tx = new Transaction(doc, "Replace Curtain Panels"))
    {
        tx.Start();

        CurtainGrid grid = curtainWall.CurtainGrid;
        foreach (ElementId panelId in grid.GetPanelIds())
        {
            Panel panel = doc.GetElement(panelId) as Panel;
            if (panel != null)
                panel.PanelType = targetType;
        }

        tx.Commit();
    }
}"""))

        samples.append(_s("Add a vertical curtain grid line at a specific position on a curtain wall",
            f"""\
using Autodesk.Revit.DB;

Wall curtainWall = new FilteredElementCollector(doc)
    .OfClass(typeof(Wall)).Cast<Wall>()
    .First(w => w.WallType.Kind == WallKind.Curtain);

using (Transaction tx = new Transaction(doc, "Add Curtain Grid Line"))
{{
    tx.Start();

    CurtainGrid grid = curtainWall.CurtainGrid;

    // Add V (vertical) grid line at u=3000mm from wall start
    double pos = {_ft(3000)}; // 3000 mm from start
    grid.AddGridLine(true, pos, false); // true = U-direction (vertical)

    tx.Commit();
}}"""))

        samples.append(_s("Get all curtain wall mullions and set their type",
            """\
using Autodesk.Revit.DB;

Wall curtainWall = new FilteredElementCollector(doc)
    .OfClass(typeof(Wall)).Cast<Wall>()
    .First(w => w.WallType.Kind == WallKind.Curtain);

MullionType targetMullionType = new FilteredElementCollector(doc)
    .OfClass(typeof(MullionType))
    .Cast<MullionType>()
    .FirstOrDefault();

if (targetMullionType != null)
{
    using (Transaction tx = new Transaction(doc, "Set Mullion Types"))
    {
        tx.Start();

        CurtainGrid grid = curtainWall.CurtainGrid;
        foreach (ElementId mullionId in grid.GetMullionIds())
        {
            Mullion mullion = doc.GetElement(mullionId) as Mullion;
            if (mullion != null)
                mullion.MullionType = targetMullionType;
        }

        tx.Commit();
    }
}"""))

        samples.append(_s("Create a curtain wall system (not wall-based) on a flat face",
            f"""\
using Autodesk.Revit.DB;

// CurtainSystem on a topographic or flat surface
using (Transaction tx = new Transaction(doc, "Create Curtain System"))
{{
    tx.Start();

    // Get a face from an existing floor or surface
    Floor floor = new FilteredElementCollector(doc)
        .OfClass(typeof(Floor)).Cast<Floor>().FirstOrDefault();

    if (floor != null)
    {{
        Options geomOpts = new Options {{ ComputeReferences = true }};
        GeometryElement geom = floor.get_Geometry(geomOpts);

        foreach (GeometryObject obj in geom)
        {{
            Solid solid = obj as Solid;
            if (solid != null)
            {{
                foreach (Face face in solid.Faces)
                {{
                    PlanarFace pf = face as PlanarFace;
                    if (pf != null && pf.FaceNormal.IsAlmostEqualTo(XYZ.BasisZ))
                    {{
                        CurtainSystemType csType = new FilteredElementCollector(doc)
                            .OfClass(typeof(CurtainSystemType))
                            .Cast<CurtainSystemType>().FirstOrDefault();
                        if (csType != null)
                        {{
                            IList<Reference> faces = new List<Reference> {{ pf.Reference }};
                            doc.Create.NewCurtainSystem2(faces, csType);
                        }}
                        break;
                    }}
                }}
                break;
            }}
        }}
    }}

    tx.Commit();
}}"""))

        return samples  # 7 samples

    # ------------------------------------------------------------------
    # Wall openings
    # ------------------------------------------------------------------

    def _wall_openings(self) -> List[SAMPLE]:
        samples = []
        opening_cases = [
            (900, 2100, "standard door opening 900x2100mm"),
            (1200, 2100, "wide door opening 1200x2100mm"),
            (600, 600,  "small service hatch 600x600mm"),
            (3000, 2400, "large equipment opening 3000x2400mm"),
            (1800, 2400, "double door rough opening 1800x2400mm"),
        ]
        for w_mm, h_mm, desc in opening_cases:
            samples.append(_s(f"Create a rectangular wall opening for {desc}",
                f"""\
using Autodesk.Revit.DB;

// Rectangular opening in a wall: {w_mm}mm wide x {h_mm}mm high
using (Transaction tx = new Transaction(doc, "Create Wall Opening"))
{{
    tx.Start();

    Wall wall = new FilteredElementCollector(doc)
        .OfClass(typeof(Wall)).Cast<Wall>().FirstOrDefault();

    if (wall != null)
    {{
        // Opening centered on wall at base level
        LocationCurve lc  = wall.Location as LocationCurve;
        XYZ midPt         = lc.Curve.Evaluate(0.5, true);

        double halfW = {_ft(w_mm / 2)}; // half of {w_mm} mm
        double height = {_ft(h_mm)}; // {h_mm} mm

        XYZ btmLeft  = new XYZ(midPt.X - halfW, midPt.Y, 0);
        XYZ topRight = new XYZ(midPt.X + halfW, midPt.Y, height);

        doc.Create.NewOpening(wall, btmLeft, topRight);
    }}

    tx.Commit();
}}"""))

        # Void extrusion opening
        samples.append(_s("Create a void extrusion cut through a wall to form a circular opening of 400mm diameter",
            f"""\
using Autodesk.Revit.DB;
using System;

// Void extrusion: circular opening 400mm diameter through wall
// (typically done in family editor)
using (Transaction tx = new Transaction(familyDoc, "Create Circular Void Opening"))
{{
    tx.Start();

    double radius   = {_ft(200)}; // 200 mm radius
    double wallThk  = {_ft(300)}; // 300 mm wall thickness (void depth)
    int    segments = 32;

    CurveArray loop = new CurveArray();
    for (int i = 0; i < segments; i++)
    {{
        double a0 = 2 * Math.PI * i / segments;
        double a1 = 2 * Math.PI * (i + 1) / segments;
        loop.Append(Line.CreateBound(
            new XYZ(radius * Math.Cos(a0), radius * Math.Sin(a0), 0),
            new XYZ(radius * Math.Cos(a1), radius * Math.Sin(a1), 0)));
    }}

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // isSolid = false --> void cuts existing solid
    familyDoc.FamilyCreate.NewExtrusion(false, profile, sp, wallThk);

    tx.Commit();
}}"""))

        samples.append(_s("Create an arched (semicircular top) wall opening 1200mm wide x 2400mm to top of arch",
            f"""\
using Autodesk.Revit.DB;
using System;

using (Transaction tx = new Transaction(doc, "Create Arched Opening"))
{{
    tx.Start();

    Wall wall = new FilteredElementCollector(doc)
        .OfClass(typeof(Wall)).Cast<Wall>().FirstOrDefault();

    if (wall != null)
    {{
        double halfW     = {_ft(600)};  // 600 mm (half of 1200mm)
        double rectH     = {_ft(1800)}; // 1800 mm rectangular portion
        double archR     = {_ft(600)};  // 600 mm arch radius (= halfW)

        // Opening profile: rectangle + semicircle on top
        CurveArray profile = new CurveArray();
        // Left vertical
        profile.Append(Line.CreateBound(new XYZ(-halfW, 0, 0), new XYZ(-halfW, 0, rectH)));
        // Arc
        profile.Append(Arc.Create(
            new XYZ(-halfW, 0, rectH),
            new XYZ( halfW, 0, rectH),
            new XYZ(0, 0, rectH + archR)));
        // Right vertical
        profile.Append(Line.CreateBound(new XYZ(halfW, 0, rectH), new XYZ(halfW, 0, 0)));
        // Bottom
        profile.Append(Line.CreateBound(new XYZ(halfW, 0, 0), new XYZ(-halfW, 0, 0)));

        LocationCurve lc = wall.Location as LocationCurve;
        XYZ origin = lc.Curve.Evaluate(0.5, true);

        doc.Create.NewOpening(wall, profile, true);
    }}

    tx.Commit();
}}"""))

        return samples  # 8 samples

    # ------------------------------------------------------------------
    # Compound wall layers
    # ------------------------------------------------------------------

    def _compound_wall_layers(self) -> List[SAMPLE]:
        samples = []

        samples.append(_s("Create a compound wall type with 3 layers: exterior cladding 25mm, insulation 100mm, structural concrete 200mm",
            f"""\
using Autodesk.Revit.DB;
using System.Collections.Generic;

using (Transaction tx = new Transaction(doc, "Create Compound Wall Type"))
{{
    tx.Start();

    WallType baseType = new FilteredElementCollector(doc)
        .OfClass(typeof(WallType)).Cast<WallType>()
        .First(wt => wt.Kind == WallKind.Basic);

    WallType newType = baseType.Duplicate("Compound 325mm") as WallType;

    CompoundStructure cs = newType.GetCompoundStructure();
    IList<CompoundStructureLayer> layers = new List<CompoundStructureLayer>();

    // Exterior cladding: 25mm
    layers.Add(new CompoundStructureLayer({_ft(25)},
        MaterialFunctionAssignment.Finish1,
        ElementId.InvalidElementId));

    // Thermal insulation: 100mm
    layers.Add(new CompoundStructureLayer({_ft(100)},
        MaterialFunctionAssignment.Insulation,
        ElementId.InvalidElementId));

    // Structural concrete: 200mm
    layers.Add(new CompoundStructureLayer({_ft(200)},
        MaterialFunctionAssignment.Structure,
        ElementId.InvalidElementId));

    cs.SetLayers(layers);
    newType.SetCompoundStructure(cs);

    tx.Commit();
}}"""))

        samples.append(_s("Read the layer thicknesses and functions of an existing compound wall type",
            """\
using Autodesk.Revit.DB;

WallType wallType = new FilteredElementCollector(doc)
    .OfClass(typeof(WallType)).Cast<WallType>()
    .First(wt => wt.Kind == WallKind.Basic);

CompoundStructure cs = wallType.GetCompoundStructure();
if (cs != null)
{
    for (int i = 0; i < cs.LayerCount; i++)
    {
        CompoundStructureLayer layer = cs.GetLayer(i);
        double thicknessMm = layer.Width / MM_TO_FT; // convert feet -> mm
        MaterialFunctionAssignment func = layer.Function;
        ElementId matId = layer.MaterialId;
        // MM_TO_FT = 1.0 / 304.8
    }
}"""))

        samples.append(_s("Assign a material to the structural layer of a compound wall type",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Assign Layer Material"))
{
    tx.Start();

    WallType wallType = new FilteredElementCollector(doc)
        .OfClass(typeof(WallType)).Cast<WallType>()
        .First(wt => wt.Kind == WallKind.Basic);

    // Find concrete material
    Material concrete = new FilteredElementCollector(doc)
        .OfClass(typeof(Material))
        .Cast<Material>()
        .FirstOrDefault(m => m.Name.Contains("Concrete"));

    CompoundStructure cs = wallType.GetCompoundStructure();
    IList<CompoundStructureLayer> layers = cs.GetLayers();

    for (int i = 0; i < layers.Count; i++)
    {
        if (layers[i].Function == MaterialFunctionAssignment.Structure && concrete != null)
        {
            // Replace structural layer material
            CompoundStructureLayer newLayer = new CompoundStructureLayer(
                layers[i].Width, layers[i].Function, concrete.Id);
            layers[i] = newLayer;
        }
    }

    cs.SetLayers(layers);
    wallType.SetCompoundStructure(cs);

    tx.Commit();
}"""))

        samples.append(_s("Create a 5-layer exterior wall type: finish 12mm, air gap 25mm, insulation 75mm, CMU 190mm, interior gypsum 12mm",
            f"""\
using Autodesk.Revit.DB;
using System.Collections.Generic;

using (Transaction tx = new Transaction(doc, "Create 5-Layer Wall"))
{{
    tx.Start();

    WallType baseType = new FilteredElementCollector(doc)
        .OfClass(typeof(WallType)).Cast<WallType>()
        .First(wt => wt.Kind == WallKind.Basic);

    WallType newType = baseType.Duplicate("Exterior 5-Layer 314mm") as WallType;
    CompoundStructure cs = newType.GetCompoundStructure();

    IList<CompoundStructureLayer> layers = new List<CompoundStructureLayer>
    {{
        // Exterior to interior (layer 0 = exterior face)
        new CompoundStructureLayer({_ft(12)},  MaterialFunctionAssignment.Finish1,    ElementId.InvalidElementId), // 12mm exterior finish
        new CompoundStructureLayer({_ft(25)},  MaterialFunctionAssignment.Membrane,   ElementId.InvalidElementId), // 25mm air gap
        new CompoundStructureLayer({_ft(75)},  MaterialFunctionAssignment.Insulation, ElementId.InvalidElementId), // 75mm insulation
        new CompoundStructureLayer({_ft(190)}, MaterialFunctionAssignment.Structure,  ElementId.InvalidElementId), // 190mm CMU
        new CompoundStructureLayer({_ft(12)},  MaterialFunctionAssignment.Finish2,    ElementId.InvalidElementId), // 12mm interior gypsum
    }};

    cs.SetLayers(layers);
    newType.SetCompoundStructure(cs);

    tx.Commit();
}}"""))

        samples.append(_s("Get the total thickness of a compound wall type",
            """\
using Autodesk.Revit.DB;

WallType wallType = new FilteredElementCollector(doc)
    .OfClass(typeof(WallType)).Cast<WallType>()
    .First(wt => wt.Kind == WallKind.Basic);

double totalThicknessMm = 0;
CompoundStructure cs = wallType.GetCompoundStructure();
if (cs != null)
{
    for (int i = 0; i < cs.LayerCount; i++)
        totalThicknessMm += cs.GetLayer(i).Width / MM_TO_FT;
}
// MM_TO_FT = 1.0 / 304.8
// totalThicknessMm now holds total wall thickness in mm"""))

        return samples  # 5 samples

    # ------------------------------------------------------------------
    # Wall parameters
    # ------------------------------------------------------------------

    def _wall_parameters(self) -> List[SAMPLE]:
        samples = []

        bip_cases = [
            ("WALL_USER_HEIGHT_PARAM",  "unconnected height",  3000, "Set a wall's unconnected height to 3000mm"),
            ("WALL_BASE_OFFSET",        "base offset",          300, "Set a wall's base offset to 300mm"),
            ("WALL_TOP_OFFSET",         "top offset",          -100, "Set a wall's top offset to -100mm"),
        ]
        for bip, desc, value_mm, instruction in bip_cases:
            samples.append(_s(instruction, f"""\
using Autodesk.Revit.DB;

Wall wall = new FilteredElementCollector(doc)
    .OfClass(typeof(Wall)).Cast<Wall>().FirstOrDefault();

if (wall != null)
{{
    using (Transaction tx = new Transaction(doc, "Set Wall {desc.title()}"))
    {{
        tx.Start();

        Parameter param = wall.get_Parameter(BuiltInParameter.{bip});
        if (param != null && !param.IsReadOnly)
            param.Set({_ft(abs(value_mm)) if value_mm >= 0 else f"-{_ft(abs(value_mm))}"}); // {value_mm} mm

        tx.Commit();
    }}
}}
// MM_TO_FT = 1.0 / 304.8"""))

        samples.append(_s("Read a wall's width (thickness) using BuiltInParameter.WALL_ATTR_WIDTH_PARAM",
            """\
using Autodesk.Revit.DB;

Wall wall = new FilteredElementCollector(doc)
    .OfClass(typeof(Wall)).Cast<Wall>().FirstOrDefault();

if (wall != null)
{
    // Wall width is a type parameter
    Parameter widthParam = wall.WallType.get_Parameter(BuiltInParameter.WALL_ATTR_WIDTH_PARAM);
    double widthMm = widthParam?.AsDouble() / MM_TO_FT ?? 0;
    // MM_TO_FT = 1.0 / 304.8
}"""))

        samples.append(_s("Set a wall's base constraint level to Level 2",
            """\
using Autodesk.Revit.DB;

Wall wall = new FilteredElementCollector(doc)
    .OfClass(typeof(Wall)).Cast<Wall>().FirstOrDefault();

Level level2 = new FilteredElementCollector(doc)
    .OfClass(typeof(Level)).Cast<Level>()
    .FirstOrDefault(l => l.Name == "Level 2");

if (wall != null && level2 != null)
{
    using (Transaction tx = new Transaction(doc, "Set Wall Base Level"))
    {
        tx.Start();

        Parameter baseLevel = wall.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT);
        if (baseLevel != null && !baseLevel.IsReadOnly)
            baseLevel.Set(level2.Id);

        tx.Commit();
    }
}"""))

        samples.append(_s("Set a wall's top constraint to 'Up to Level: Level 3'",
            """\
using Autodesk.Revit.DB;

Wall wall = new FilteredElementCollector(doc)
    .OfClass(typeof(Wall)).Cast<Wall>().FirstOrDefault();

Level level3 = new FilteredElementCollector(doc)
    .OfClass(typeof(Level)).Cast<Level>()
    .FirstOrDefault(l => l.Name == "Level 3");

if (wall != null && level3 != null)
{
    using (Transaction tx = new Transaction(doc, "Set Wall Top Constraint"))
    {
        tx.Start();

        Parameter topConstraint = wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE);
        if (topConstraint != null && !topConstraint.IsReadOnly)
            topConstraint.Set(level3.Id);

        tx.Commit();
    }
}"""))

        samples.append(_s("Check if a wall is structural using its structural usage parameter",
            """\
using Autodesk.Revit.DB;

Wall wall = new FilteredElementCollector(doc)
    .OfClass(typeof(Wall)).Cast<Wall>().FirstOrDefault();

if (wall != null)
{
    Parameter structUsage = wall.get_Parameter(BuiltInParameter.WALL_STRUCTURAL_USAGE_PARAM);
    if (structUsage != null)
    {
        int usage = structUsage.AsInteger();
        bool isStructural = usage != 0; // 0 = Non-bearing
    }
}"""))

        return samples  # 7 samples

    # ------------------------------------------------------------------
    # Wall sweeps and reveals
    # ------------------------------------------------------------------

    def _wall_sweeps_reveals(self) -> List[SAMPLE]:
        samples = []

        samples.append(_s("Add a base wall sweep (skirting board) at 150mm height to a wall type",
            f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Add Wall Sweep"))
{{
    tx.Start();

    WallType wallType = new FilteredElementCollector(doc)
        .OfClass(typeof(WallType)).Cast<WallType>()
        .First(wt => wt.Kind == WallKind.Basic);

    WallSweepInfo info = new WallSweepInfo(WallSweepType.Sweep, true);
    info.Distance   = {_ft(150)};  // 150 mm from base
    info.WallSide   = WallSide.Interior;
    info.SweepAtTop = false;       // at base
    info.OffsetFromWall = 0;

    // Find a sweep profile
    WallSweepType sweepTypeRef = WallSweepType.Sweep;
    WallType sweptType = wallType.Duplicate("Wall with Base Sweep") as WallType;
    CompoundStructure cs = sweptType.GetCompoundStructure();
    cs.AddWallSweep(info);
    sweptType.SetCompoundStructure(cs);

    tx.Commit();
}}"""))

        samples.append(_s("Get all wall sweeps on a wall type and print their heights",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

WallType wallType = new FilteredElementCollector(doc)
    .OfClass(typeof(WallType)).Cast<WallType>()
    .First(wt => wt.Kind == WallKind.Basic);

CompoundStructure cs = wallType.GetCompoundStructure();
if (cs != null)
{
    IList<WallSweepInfo> sweeps = cs.GetWallSweepsInfo();
    foreach (WallSweepInfo sweep in sweeps)
    {
        double heightMm = sweep.Distance / MM_TO_FT;
        WallSide side   = sweep.WallSide;
        bool isTop      = sweep.SweepAtTop;
    }
    // MM_TO_FT = 1.0 / 304.8
}"""))

        samples.append(_s("Add a horizontal reveal at mid-height to an exterior wall type",
            f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Add Wall Reveal"))
{{
    tx.Start();

    WallType wallType = new FilteredElementCollector(doc)
        .OfClass(typeof(WallType)).Cast<WallType>()
        .First(wt => wt.Kind == WallKind.Basic);

    WallType revealType = wallType.Duplicate("Wall with Mid Reveal") as WallType;

    WallSweepInfo revealInfo = new WallSweepInfo(WallSweepType.Reveal, true);
    revealInfo.Distance     = {_ft(1500)}; // 1500 mm from base (mid-height of 3m wall)
    revealInfo.WallSide     = WallSide.Exterior;
    revealInfo.SweepAtTop   = false;
    revealInfo.OffsetFromWall = 0;

    CompoundStructure cs = revealType.GetCompoundStructure();
    cs.AddWallSweep(revealInfo);
    revealType.SetCompoundStructure(cs);

    tx.Commit();
}}"""))

        samples.append(_s("Remove all wall sweeps from a wall type",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

using (Transaction tx = new Transaction(doc, "Remove Wall Sweeps"))
{
    tx.Start();

    WallType wallType = new FilteredElementCollector(doc)
        .OfClass(typeof(WallType)).Cast<WallType>()
        .First(wt => wt.Kind == WallKind.Basic);

    CompoundStructure cs = wallType.GetCompoundStructure();
    if (cs != null)
    {
        IList<WallSweepInfo> sweeps = cs.GetWallSweepsInfo();
        for (int i = sweeps.Count - 1; i >= 0; i--)
            cs.RemoveWallSweep(i);
        wallType.SetCompoundStructure(cs);
    }

    tx.Commit();
}"""))

        return samples  # 4 samples


if __name__ == "__main__":
    import json
    gen = WallFamilyGenerator()
    samples = gen.generate()
    print(f"Generated {len(samples)} samples")
    assert all(set(s.keys()) == {"instruction", "input", "output"} for s in samples), "Bad sample structure"
    print("[OK] All samples valid")
