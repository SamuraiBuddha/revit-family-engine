"""Training data generator: Broad Revit API reference coverage.

Produces ~200 Alpaca-format training pairs covering FilteredElementCollector,
parameter access, view operations, annotation elements, element transforms,
document operations, selection/picking, geometry access, event handling,
error handling, and unit conversion.
"""

from __future__ import annotations

from typing import Any, Dict, List

SAMPLE = Dict[str, Any]
MM_TO_FT = 1.0 / 304.8


def _s(instruction: str, output: str) -> SAMPLE:
    return {"instruction": instruction, "input": "", "output": output}


def _ft(mm: float) -> str:
    return f"{mm * MM_TO_FT:.6f}"


class RevitAPIReferenceGenerator:
    """Generates training samples covering the broad Revit API surface area."""

    def generate(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []
        samples += self._filtered_element_collector()
        samples += self._element_parameter_access()
        samples += self._view_operations()
        samples += self._annotation_elements()
        samples += self._element_transforms()
        samples += self._document_operations()
        samples += self._selection_and_picking()
        samples += self._geometry_access()
        samples += self._event_handling()
        samples += self._error_handling()
        samples += self._units_and_conversion()
        return samples

    # ------------------------------------------------------------------
    # 1. FilteredElementCollector (~25 samples)
    # ------------------------------------------------------------------

    def _filtered_element_collector(self) -> List[SAMPLE]:
        samples = []

        # OfClass basics
        samples.append(_s(
            "Collect all walls in the active document using FilteredElementCollector",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

// Collect all Wall elements in the document
IList<Element> walls = new FilteredElementCollector(doc)
    .OfClass(typeof(Wall))
    .ToElements();

foreach (Wall wall in walls.Cast<Wall>())
{
    // Process each wall
    string wallTypeName = wall.WallType.Name;
}""",
        ))

        samples.append(_s(
            "Collect all FamilyInstance elements in a Revit document",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

IList<Element> instances = new FilteredElementCollector(doc)
    .OfClass(typeof(FamilyInstance))
    .ToElements();

// Cast for typed access
IEnumerable<FamilyInstance> famInstances = instances.Cast<FamilyInstance>();""",
        ))

        samples.append(_s(
            "Collect all Level elements using OfClass and cast to Level",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

List<Level> levels = new FilteredElementCollector(doc)
    .OfClass(typeof(Level))
    .Cast<Level>()
    .OrderBy(l => l.Elevation)
    .ToList();

foreach (Level level in levels)
{
    double elevationFt = level.Elevation;
    double elevationMm = elevationFt * 304.8;
}""",
        ))

        # OfCategory basics
        samples.append(_s(
            "Collect all door elements by category using OfCategory",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

IList<Element> doors = new FilteredElementCollector(doc)
    .OfCategory(BuiltInCategory.OST_Doors)
    .WhereElementIsNotElementType()
    .ToElements();

// Use .WhereElementIsElementType() to get door types instead""",
        ))

        samples.append(_s(
            "Collect all furniture elements by category in a specific view",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

// Passing a viewId limits collection to elements visible in that view
ElementId viewId = doc.ActiveView.Id;

IList<Element> furniture = new FilteredElementCollector(doc, viewId)
    .OfCategory(BuiltInCategory.OST_Furniture)
    .WhereElementIsNotElementType()
    .ToElements();""",
        ))

        # WherePasses with ElementClassFilter
        samples.append(_s(
            "Use WherePasses with ElementClassFilter to collect Floor elements",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

ElementClassFilter floorFilter = new ElementClassFilter(typeof(Floor));

IList<Element> floors = new FilteredElementCollector(doc)
    .WherePasses(floorFilter)
    .ToElements();""",
        ))

        # WherePasses with ElementCategoryFilter
        samples.append(_s(
            "Use WherePasses with ElementCategoryFilter to collect structural columns",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

ElementCategoryFilter colFilter = new ElementCategoryFilter(
    BuiltInCategory.OST_StructuralColumns);

IList<Element> columns = new FilteredElementCollector(doc)
    .WherePasses(colFilter)
    .WhereElementIsNotElementType()
    .ToElements();""",
        ))

        # LogicalAndFilter
        samples.append(_s(
            "Combine two filters with LogicalAndFilter to find structural wall instances",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

ElementClassFilter    wallClass  = new ElementClassFilter(typeof(Wall));
ElementCategoryFilter wallCat    = new ElementCategoryFilter(
    BuiltInCategory.OST_StructuralFraming, true); // inverted = exclude framing

LogicalAndFilter combined = new LogicalAndFilter(wallClass, wallCat);

IList<Element> structWalls = new FilteredElementCollector(doc)
    .WherePasses(combined)
    .WhereElementIsNotElementType()
    .ToElements();""",
        ))

        # BoundingBoxIntersectsFilter
        samples.append(_s(
            "Find all elements whose bounding box intersects a given room outline using BoundingBoxIntersectsFilter",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

// Define outline (feet)
double minX = 0.0, minY = 0.0, minZ = 0.0;
double maxX = 10.0, maxY = 8.0, maxZ = 9.84252; // ~3m

Outline outline = new Outline(
    new XYZ(minX, minY, minZ),
    new XYZ(maxX, maxY, maxZ));

BoundingBoxIntersectsFilter bbFilter = new BoundingBoxIntersectsFilter(outline);

IList<Element> elements = new FilteredElementCollector(doc)
    .WherePasses(bbFilter)
    .WhereElementIsNotElementType()
    .ToElements();""",
        ))

        # ElementIntersectsSolidFilter
        samples.append(_s(
            "Find elements that physically intersect a given solid using ElementIntersectsSolidFilter",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

// Build a solid box to use as intersection test geometry
XYZ min = new XYZ(0, 0, 0);
XYZ max = new XYZ(3.28084, 3.28084, 9.84252); // 1m x 1m x 3m in feet

Solid testSolid = GeometryCreationUtilities.CreateExtrusionGeometry(
    new CurveLoop[] {
        CurveLoop.CreateViaThicken(
            Line.CreateBound(new XYZ(min.X, min.Y, 0), new XYZ(max.X, min.Y, 0)),
            max.Y - min.Y, XYZ.BasisZ) },
    XYZ.BasisZ, max.Z);

ElementIntersectsSolidFilter solidFilter = new ElementIntersectsSolidFilter(testSolid);

IList<Element> intersecting = new FilteredElementCollector(doc)
    .WherePasses(solidFilter)
    .WhereElementIsNotElementType()
    .ToElements();""",
        ))

        # OfClass + OfCategory chained
        samples.append(_s(
            "Collect all FamilySymbol types for the Doors category",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

List<FamilySymbol> doorTypes = new FilteredElementCollector(doc)
    .OfClass(typeof(FamilySymbol))
    .OfCategory(BuiltInCategory.OST_Doors)
    .Cast<FamilySymbol>()
    .ToList();

foreach (FamilySymbol dt in doorTypes)
{
    string familyName = dt.FamilyName;
    string typeName   = dt.Name;
}""",
        ))

        # LINQ where clause
        samples.append(_s(
            "Use LINQ to filter collected walls by a parameter value (wall type name contains 'Exterior')",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

List<Wall> exteriorWalls = new FilteredElementCollector(doc)
    .OfClass(typeof(Wall))
    .Cast<Wall>()
    .Where(w => w.WallType.Name.Contains("Exterior"))
    .ToList();""",
        ))

        # ParameterValueFilter
        samples.append(_s(
            "Filter elements by a built-in parameter value using ParameterValueFilter",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

// Find all rooms with area > 20 m2 (20 m2 = 215.278 ft2)
ParameterValueProvider provider = new ParameterValueProvider(
    new ElementId(BuiltInParameter.ROOM_AREA));

FilterNumericRuleEvaluator evaluator = new FilterNumericGreater();
double threshold = 215.278; // ft2
double epsilon   = 0.01;

FilterRule rule = new FilterDoubleRule(provider, evaluator, threshold, epsilon);

ElementParameterFilter paramFilter = new ElementParameterFilter(rule);

IList<Element> largeRooms = new FilteredElementCollector(doc)
    .OfCategory(BuiltInCategory.OST_Rooms)
    .WherePasses(paramFilter)
    .ToElements();""",
        ))

        # First() shortcut
        samples.append(_s(
            "Get the first ViewPlan named 'Level 1' using FirstOrDefault and LINQ",
            """\
using Autodesk.Revit.DB;
using System.Linq;

ViewPlan level1Plan = new FilteredElementCollector(doc)
    .OfClass(typeof(ViewPlan))
    .Cast<ViewPlan>()
    .FirstOrDefault(v => v.Name == "Level 1" && !v.IsTemplate);""",
        ))

        # Collect element ids only
        samples.append(_s(
            "Collect only ElementIds of all rooms (faster than collecting full elements)",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

ICollection<ElementId> roomIds = new FilteredElementCollector(doc)
    .OfCategory(BuiltInCategory.OST_Rooms)
    .WhereElementIsNotElementType()
    .ToElementIds();""",
        ))

        # Collect in linked document
        samples.append(_s(
            "Collect elements from a linked Revit document using FilteredElementCollector on the link instance",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

// Get the first RevitLinkInstance in the host document
RevitLinkInstance linkInst = new FilteredElementCollector(doc)
    .OfClass(typeof(RevitLinkInstance))
    .Cast<RevitLinkInstance>()
    .FirstOrDefault();

if (linkInst != null)
{
    Document linkedDoc = linkInst.GetLinkDocument();
    if (linkedDoc != null)
    {
        IList<Element> linkedWalls = new FilteredElementCollector(linkedDoc)
            .OfClass(typeof(Wall))
            .ToElements();
    }
}""",
        ))

        # WhereElementIsElementType
        samples.append(_s(
            "Collect all WallType element types in the document",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

List<WallType> wallTypes = new FilteredElementCollector(doc)
    .OfClass(typeof(WallType))
    .Cast<WallType>()
    .ToList();

foreach (WallType wt in wallTypes)
{
    double widthFt = wt.Width;
    double widthMm = widthFt * 304.8;
}""",
        ))

        # ExclusionFilter
        samples.append(_s(
            "Collect all walls except a specific set of wall ElementIds using ExclusionFilter",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

// Suppose we have wall ids to exclude
ICollection<ElementId> excludedIds = new List<ElementId>
{
    new ElementId(123456),
    new ElementId(789012),
};

ExclusionFilter exclusion = new ExclusionFilter(excludedIds);

IList<Element> remainingWalls = new FilteredElementCollector(doc)
    .OfClass(typeof(Wall))
    .WherePasses(exclusion)
    .ToElements();""",
        ))

        # Count samples
        samples.append(_s(
            "Get a count of all door instances in the model without loading full elements",
            """\
using Autodesk.Revit.DB;

int doorCount = new FilteredElementCollector(doc)
    .OfCategory(BuiltInCategory.OST_Doors)
    .WhereElementIsNotElementType()
    .GetElementCount();""",
        ))

        # Collect rooms
        samples.append(_s(
            "Collect all placed Room elements (not unplaced) using FilteredElementCollector",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using System.Collections.Generic;
using System.Linq;

List<Room> placedRooms = new FilteredElementCollector(doc)
    .OfCategory(BuiltInCategory.OST_Rooms)
    .Cast<Room>()
    .Where(r => r.Area > 0) // Area > 0 means the room is placed and bounded
    .ToList();""",
        ))

        # Collect sheets
        samples.append(_s(
            "Collect all ViewSheet elements sorted by sheet number",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

List<ViewSheet> sheets = new FilteredElementCollector(doc)
    .OfClass(typeof(ViewSheet))
    .Cast<ViewSheet>()
    .OrderBy(s => s.SheetNumber)
    .ToList();

foreach (ViewSheet sheet in sheets)
{
    string num  = sheet.SheetNumber;
    string name = sheet.Name;
}""",
        ))

        # Collect grid lines
        samples.append(_s(
            "Collect all Grid elements in the document",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

List<Grid> grids = new FilteredElementCollector(doc)
    .OfClass(typeof(Grid))
    .Cast<Grid>()
    .ToList();

foreach (Grid g in grids)
{
    string gridName   = g.Name;
    Curve  gridCurve  = g.Curve;
}""",
        ))

        # Collect by multiple categories with LogicalOrFilter
        samples.append(_s(
            "Collect both doors and windows using LogicalOrFilter",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

ElementCategoryFilter doorFilter   = new ElementCategoryFilter(BuiltInCategory.OST_Doors);
ElementCategoryFilter windowFilter = new ElementCategoryFilter(BuiltInCategory.OST_Windows);

LogicalOrFilter openingFilter = new LogicalOrFilter(doorFilter, windowFilter);

IList<Element> openings = new FilteredElementCollector(doc)
    .WherePasses(openingFilter)
    .WhereElementIsNotElementType()
    .ToElements();""",
        ))

        # Collect workset elements
        samples.append(_s(
            "Collect all elements on a specific workset by workset id",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

// Get workset named "Architecture"
WorksetId targetWorksetId = doc.GetWorksetTable()
    .GetWorksets(WorksetKind.UserWorkset)
    .Cast<Workset>()
    .Where(ws => ws.Name == "Architecture")
    .Select(ws => ws.Id)
    .FirstOrDefault();

if (targetWorksetId != null)
{
    ElementWorksetFilter worksetFilter = new ElementWorksetFilter(targetWorksetId);
    IList<Element> archElements = new FilteredElementCollector(doc)
        .WherePasses(worksetFilter)
        .ToElements();
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # 2. Element Parameter Access (~20 samples)
    # ------------------------------------------------------------------


    def _element_parameter_access(self) -> List[SAMPLE]:
        samples = []

        # get_Parameter BuiltInParameter read
        samples.append(_s(
            "Read the base offset of a wall using get_Parameter with BuiltInParameter",
            """\
using Autodesk.Revit.DB;

Wall wall = doc.GetElement(wallId) as Wall;
if (wall != null)
{
    Parameter baseOffset = wall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET);
    if (baseOffset != null)
    {
        double offsetFt = baseOffset.AsDouble();
        double offsetMm = offsetFt * 304.8;
    }
}""",
        ))

        # LookupParameter by name
        samples.append(_s(
            "Read a custom parameter named 'Fire Rating' from a wall using LookupParameter",
            """\
using Autodesk.Revit.DB;

Wall wall = doc.GetElement(wallId) as Wall;
Parameter fireRating = wall?.LookupParameter("Fire Rating");

if (fireRating != null && fireRating.HasValue)
{
    string rating = fireRating.AsString();
    // or fireRating.AsValueString() for display string with units
}""",
        ))

        # Write double parameter
        samples.append(_s(
            "Set the height of a wall by writing to its Unconnected Height parameter",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Set Wall Height"))
{
    tx.Start();

    Wall wall = doc.GetElement(wallId) as Wall;
    Parameter heightParam = wall?.get_Parameter(
        BuiltInParameter.WALL_USER_HEIGHT_PARAM);

    if (heightParam != null && !heightParam.IsReadOnly)
    {
        double heightFt = 3000.0 / 304.8; // 3000 mm -> feet
        heightParam.Set(heightFt);
    }

    tx.Commit();
}""",
        ))

        # Write string parameter
        samples.append(_s(
            "Write a string value to a text parameter named 'Description' on an element",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Set Description"))
{
    tx.Start();

    Element elem = doc.GetElement(elementId);
    Parameter descParam = elem?.LookupParameter("Description");

    if (descParam != null && descParam.StorageType == StorageType.String
        && !descParam.IsReadOnly)
    {
        descParam.Set("Prefabricated steel column - Grade S355");
    }

    tx.Commit();
}""",
        ))

        # Write integer / YesNo parameter
        samples.append(_s(
            "Toggle a Yes/No parameter named 'Is Structural' to true on a floor element",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Set Structural Flag"))
{
    tx.Start();

    Floor floor = doc.GetElement(floorId) as Floor;
    Parameter structParam = floor?.LookupParameter("Is Structural");

    if (structParam != null && structParam.StorageType == StorageType.Integer)
    {
        structParam.Set(1); // 1 = true, 0 = false for YesNo parameters
    }

    tx.Commit();
}""",
        ))

        # Write ElementId parameter (material)
        samples.append(_s(
            "Assign a material by ElementId to a material parameter on a floor",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(doc, "Assign Material"))
{
    tx.Start();

    Floor floor = doc.GetElement(floorId) as Floor;

    // Find material by name
    Material concrete = new FilteredElementCollector(doc)
        .OfClass(typeof(Material))
        .Cast<Material>()
        .FirstOrDefault(m => m.Name.Contains("Concrete"));

    if (concrete != null)
    {
        Parameter matParam = floor?.get_Parameter(
            BuiltInParameter.MATERIAL_ID_PARAM);
        matParam?.Set(concrete.Id);
    }

    tx.Commit();
}""",
        ))

        # Iterate all parameters
        samples.append(_s(
            "Iterate and print all parameters of a given element",
            """\
using Autodesk.Revit.DB;
using System.Text;

Element elem = doc.GetElement(elementId);
StringBuilder sb = new StringBuilder();

foreach (Parameter param in elem.Parameters)
{
    string name    = param.Definition.Name;
    string valStr  = param.AsValueString() ?? param.AsString() ?? param.AsDouble().ToString("F4");
    sb.AppendLine($"{name}: {valStr}");
}

string paramReport = sb.ToString();""",
        ))

        # Check StorageType before read
        samples.append(_s(
            "Safely read a parameter value by checking its StorageType first",
            """\
using Autodesk.Revit.DB;

Element elem = doc.GetElement(elementId);
Parameter p  = elem?.LookupParameter("MyParam");

if (p != null && p.HasValue)
{
    switch (p.StorageType)
    {
        case StorageType.Double:
            double d = p.AsDouble();
            break;
        case StorageType.Integer:
            int i = p.AsInteger();
            break;
        case StorageType.String:
            string s = p.AsString();
            break;
        case StorageType.ElementId:
            ElementId id = p.AsElementId();
            break;
    }
}""",
        ))

        # GetTypeId and type parameters
        samples.append(_s(
            "Access a type parameter by getting the element's type first",
            """\
using Autodesk.Revit.DB;

// Instance parameters live on the element; type parameters on the type
Element instance = doc.GetElement(elementId);
ElementId typeId = instance.GetTypeId();
ElementType elemType = doc.GetElement(typeId) as ElementType;

if (elemType != null)
{
    Parameter typeWidthParam = elemType.LookupParameter("Frame Width");
    double typeWidthFt = typeWidthParam?.AsDouble() ?? 0.0;
}""",
        ))

        # ParameterSet iteration
        samples.append(_s(
            "Find all parameters whose value exceeds a threshold by iterating ParameterSet",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

Element elem = doc.GetElement(elementId);
List<string> largeParams = new List<string>();

foreach (Parameter p in elem.Parameters)
{
    if (p.StorageType == StorageType.Double && p.HasValue)
    {
        double val = p.AsDouble();
        if (val > 100.0) // arbitrary threshold in internal units
            largeParams.Add(p.Definition.Name);
    }
}""",
        ))

        # Shared parameter GUID lookup
        samples.append(_s(
            "Look up a shared parameter by its GUID using GetParameters",
            """\
using Autodesk.Revit.DB;
using System;
using System.Linq;

Guid sharedParamGuid = new Guid("a1b2c3d4-e5f6-7890-abcd-ef1234567890");

Element elem = doc.GetElement(elementId);
Parameter sharedParam = elem.GetParameters(
    sharedParamGuid.ToString())  // overload accepting name -- use InternalDefinition
    .FirstOrDefault();

// Preferred: iterate and match ExternalDefinition Guid
Parameter found = elem.Parameters
    .Cast<Parameter>()
    .FirstOrDefault(p =>
    {
        ExternalDefinition ext = p.Definition as ExternalDefinition;
        return ext != null && ext.GUID == sharedParamGuid;
    });""",
        ))

        # Read room area / perimeter
        samples.append(_s(
            "Read the area and perimeter of a Room element",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;

Room room = doc.GetElement(roomId) as Room;
if (room != null)
{
    double areaFt2 = room.Area;         // ft^2
    double areaMm2 = areaFt2 * 92903.04;// ft^2 -> mm^2

    Parameter perimParam = room.get_Parameter(BuiltInParameter.ROOM_PERIMETER);
    double perimFt = perimParam?.AsDouble() ?? 0.0;
    double perimMm = perimFt * 304.8;
}""",
        ))

        # Write comment parameter
        samples.append(_s(
            "Set the Comments instance parameter on a family instance",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Set Comment"))
{
    tx.Start();

    FamilyInstance fi = doc.GetElement(instanceId) as FamilyInstance;
    Parameter comments = fi?.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS);

    if (comments != null && !comments.IsReadOnly)
    {
        comments.Set("Reviewed by structural engineer 2026-03-23");
    }

    tx.Commit();
}""",
        ))

        # AsValueString vs AsDouble
        samples.append(_s(
            "Get a formatted display string (with units) for a length parameter using AsValueString",
            """\
using Autodesk.Revit.DB;

Element elem = doc.GetElement(elementId);
Parameter lengthParam = elem?.get_Parameter(BuiltInParameter.CURVE_ELEM_LENGTH);

if (lengthParam != null)
{
    // AsValueString() respects the document's display unit settings
    string displayValue = lengthParam.AsValueString(); // e.g. "3000 mm" or "9' 10.11\""
    double rawFeet      = lengthParam.AsDouble();
}""",
        ))

        # Batch update parameters across collection
        samples.append(_s(
            "Batch-update the 'Mark' parameter on all door instances",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

using (Transaction tx = new Transaction(doc, "Number Doors"))
{
    tx.Start();

    List<FamilyInstance> doors = new FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Doors)
        .WhereElementIsNotElementType()
        .Cast<FamilyInstance>()
        .ToList();

    int counter = 1;
    foreach (FamilyInstance door in doors)
    {
        Parameter markParam = door.get_Parameter(BuiltInParameter.ALL_MODEL_MARK);
        if (markParam != null && !markParam.IsReadOnly)
            markParam.Set($"D{counter:D3}");
        counter++;
    }

    tx.Commit();
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # 3. View Operations (~20 samples)
    # ------------------------------------------------------------------


    def _view_operations(self) -> List[SAMPLE]:
        samples = []

        # Create floor plan view
        samples.append(_s(
            "Create a new floor plan ViewPlan for an existing Level",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(doc, "Create Floor Plan"))
{
    tx.Start();

    Level level = new FilteredElementCollector(doc)
        .OfClass(typeof(Level))
        .Cast<Level>()
        .FirstOrDefault(l => l.Name == "Level 2");

    // Find the 'Floor Plan' ViewFamilyType
    ViewFamilyType vft = new FilteredElementCollector(doc)
        .OfClass(typeof(ViewFamilyType))
        .Cast<ViewFamilyType>()
        .FirstOrDefault(v => v.ViewFamily == ViewFamily.FloorPlan);

    if (level != null && vft != null)
    {
        ViewPlan floorPlan = ViewPlan.Create(doc, vft.Id, level.Id);
        floorPlan.Name = "Level 2 - Floor Plan";
    }

    tx.Commit();
}""",
        ))

        # Create reflected ceiling plan
        samples.append(_s(
            "Create a reflected ceiling plan (RCP) for Level 1",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(doc, "Create RCP"))
{
    tx.Start();

    Level level = new FilteredElementCollector(doc)
        .OfClass(typeof(Level))
        .Cast<Level>()
        .FirstOrDefault(l => l.Name == "Level 1");

    ViewFamilyType rcpType = new FilteredElementCollector(doc)
        .OfClass(typeof(ViewFamilyType))
        .Cast<ViewFamilyType>()
        .FirstOrDefault(v => v.ViewFamily == ViewFamily.CeilingPlan);

    if (level != null && rcpType != null)
    {
        ViewPlan rcp = ViewPlan.Create(doc, rcpType.Id, level.Id);
        rcp.Name = "Level 1 - Reflected Ceiling Plan";
    }

    tx.Commit();
}""",
        ))

        # Create 3D view
        samples.append(_s(
            "Create a new default 3D view",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(doc, "Create 3D View"))
{
    tx.Start();

    ViewFamilyType view3dType = new FilteredElementCollector(doc)
        .OfClass(typeof(ViewFamilyType))
        .Cast<ViewFamilyType>()
        .FirstOrDefault(v => v.ViewFamily == ViewFamily.ThreeDimensional);

    if (view3dType != null)
    {
        View3D view3d = View3D.CreateIsometric(doc, view3dType.Id);
        view3d.Name = "Coordination 3D View";
    }

    tx.Commit();
}""",
        ))

        # Create section view
        samples.append(_s(
            "Create a building section view using a BoundingBoxXYZ transform",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(doc, "Create Section"))
{
    tx.Start();

    ViewFamilyType sectionType = new FilteredElementCollector(doc)
        .OfClass(typeof(ViewFamilyType))
        .Cast<ViewFamilyType>()
        .FirstOrDefault(v => v.ViewFamily == ViewFamily.Section);

    if (sectionType != null)
    {
        // Section box: origin, orientation, half-extents
        BoundingBoxXYZ sectionBox = new BoundingBoxXYZ();
        Transform t = Transform.Identity;
        // Section looking in +Y direction; X is section width, Z is height
        t.BasisX = XYZ.BasisX;
        t.BasisY = XYZ.BasisZ;
        t.BasisZ = XYZ.BasisY.Negate();
        t.Origin = new XYZ(0, 16.4042, 0); // 5m in Y (feet)
        sectionBox.Transform = t;
        sectionBox.Min = new XYZ(-16.4042, 0, -3.28084); // half-extents
        sectionBox.Max = new XYZ( 16.4042, 32.8084, 0);

        ViewSection section = ViewSection.CreateSection(doc, sectionType.Id, sectionBox);
        section.Name = "Section A-A";
    }

    tx.Commit();
}""",
        ))

        # Create callout view
        samples.append(_s(
            "Create a callout view from an existing floor plan view",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(doc, "Create Callout"))
{
    tx.Start();

    ViewPlan parentView = new FilteredElementCollector(doc)
        .OfClass(typeof(ViewPlan))
        .Cast<ViewPlan>()
        .FirstOrDefault(v => v.Name == "Level 1" && !v.IsTemplate);

    ViewFamilyType calloutType = new FilteredElementCollector(doc)
        .OfClass(typeof(ViewFamilyType))
        .Cast<ViewFamilyType>()
        .FirstOrDefault(v => v.ViewFamily == ViewFamily.FloorPlan);

    if (parentView != null && calloutType != null)
    {
        // Callout region in view coordinates (feet)
        XYZ min = new XYZ(0, 0, 0);
        XYZ max = new XYZ(9.84252, 9.84252, 0); // 3m x 3m

        ViewPlan callout = ViewPlan.CreateCallout(
            doc, parentView.Id, calloutType.Id, min, max);
        callout.Name = "Stair Core Detail";
    }

    tx.Commit();
}""",
        ))

        # Duplicate view
        samples.append(_s(
            "Duplicate an existing view with detailing using ViewDuplicateOption",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(doc, "Duplicate View"))
{
    tx.Start();

    ViewPlan sourceView = new FilteredElementCollector(doc)
        .OfClass(typeof(ViewPlan))
        .Cast<ViewPlan>()
        .FirstOrDefault(v => v.Name == "Level 1" && !v.IsTemplate);

    if (sourceView != null && sourceView.CanViewBeDuplicated(ViewDuplicateOption.WithDetailing))
    {
        ElementId newViewId = sourceView.Duplicate(ViewDuplicateOption.WithDetailing);
        View newView = doc.GetElement(newViewId) as View;
        if (newView != null)
            newView.Name = "Level 1 - Copy";
    }

    tx.Commit();
}""",
        ))

        # Set view scale
        samples.append(_s(
            "Set the scale of a view to 1:50",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Set View Scale"))
{
    tx.Start();

    View view = doc.GetElement(viewId) as View;
    if (view != null && view.CanModifyViewScale())
    {
        view.Scale = 50; // 1:50
    }

    tx.Commit();
}""",
        ))

        # Set view detail level
        samples.append(_s(
            "Set a view's detail level to Fine",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Set Detail Level"))
{
    tx.Start();

    View view = doc.GetElement(viewId) as View;
    if (view != null)
    {
        view.DetailLevel = ViewDetailLevel.Fine;
    }

    tx.Commit();
}""",
        ))

        # Override element graphics in view
        samples.append(_s(
            "Override the surface foreground pattern of a wall to solid red in a specific view",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Override Graphics"))
{
    tx.Start();

    View view = doc.GetElement(viewId) as View;
    OverrideGraphicSettings ogs = new OverrideGraphicSettings();

    // Set surface foreground color to red
    ogs.SetSurfaceForegroundPatternColor(new Color(255, 0, 0));
    ogs.SetSurfaceForegroundPatternVisible(true);

    // Apply to a specific element
    view.SetElementOverrides(wallId, ogs);

    tx.Commit();
}""",
        ))

        # Add view to sheet
        samples.append(_s(
            "Place a view onto a sheet at a specified location",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(doc, "Place View on Sheet"))
{
    tx.Start();

    ViewSheet sheet = new FilteredElementCollector(doc)
        .OfClass(typeof(ViewSheet))
        .Cast<ViewSheet>()
        .FirstOrDefault(s => s.SheetNumber == "A101");

    View plan = new FilteredElementCollector(doc)
        .OfClass(typeof(ViewPlan))
        .Cast<ViewPlan>()
        .FirstOrDefault(v => v.Name == "Level 1" && !v.IsTemplate);

    if (sheet != null && plan != null && Viewport.CanAddViewToSheet(doc, sheet.Id, plan.Id))
    {
        // Center point on sheet in feet (sheet coordinates)
        XYZ location = new XYZ(1.0, 0.75, 0); // ~305mm, 229mm from sheet origin
        Viewport viewport = Viewport.Create(doc, sheet.Id, plan.Id, location);
    }

    tx.Commit();
}""",
        ))

        # Crop region
        samples.append(_s(
            "Set a crop region box on a floor plan view to a specific rectangle",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Set Crop Region"))
{
    tx.Start();

    ViewPlan plan = doc.GetElement(viewId) as ViewPlan;
    if (plan != null && plan.CropBoxActive)
    {
        BoundingBoxXYZ cropBox = plan.CropBox;
        cropBox.Min = new XYZ(-16.4042, -9.84252, -98.4252); // -5m, -3m, -30m in ft
        cropBox.Max = new XYZ( 16.4042,  9.84252,  98.4252);
        plan.CropBox        = cropBox;
        plan.CropBoxActive  = true;
        plan.CropBoxVisible = true;
    }

    tx.Commit();
}""",
        ))

        # Visibility/Graphics category override
        samples.append(_s(
            "Turn off the visibility of the Furniture category in a specific view",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Hide Furniture Category"))
{
    tx.Start();

    View view = doc.GetElement(viewId) as View;
    if (view != null)
    {
        ElementId furnitureCatId = new ElementId(BuiltInCategory.OST_Furniture);
        if (view.GetCategoryHidden(furnitureCatId) == false)
            view.SetCategoryHidden(furnitureCatId, true);
    }

    tx.Commit();
}""",
        ))

        # Get active view
        samples.append(_s(
            "Get the current active view and print its name and type",
            """\
using Autodesk.Revit.DB;

View activeView = doc.ActiveView;
string viewName = activeView.Name;
ViewType viewType = activeView.ViewType;
// ViewType enum: FloorPlan, CeilingPlan, Elevation, Section, Detail, ThreeD, etc.""",
        ))

        # Rename view
        samples.append(_s(
            "Rename a view by finding it and setting its Name property inside a transaction",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(doc, "Rename View"))
{
    tx.Start();

    View targetView = new FilteredElementCollector(doc)
        .OfClass(typeof(View))
        .Cast<View>()
        .FirstOrDefault(v => v.Name == "Old View Name");

    if (targetView != null)
        targetView.Name = "New View Name";

    tx.Commit();
}""",
        ))

        # Create elevation marker
        samples.append(_s(
            "Create an interior elevation marker with four elevation views",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(doc, "Create Elevations"))
{
    tx.Start();

    ViewFamilyType elevType = new FilteredElementCollector(doc)
        .OfClass(typeof(ViewFamilyType))
        .Cast<ViewFamilyType>()
        .FirstOrDefault(v => v.ViewFamily == ViewFamily.Elevation);

    ViewPlan hostPlan = new FilteredElementCollector(doc)
        .OfClass(typeof(ViewPlan))
        .Cast<ViewPlan>()
        .FirstOrDefault(v => v.Name == "Level 1" && !v.IsTemplate);

    if (elevType != null && hostPlan != null)
    {
        XYZ markerLocation = new XYZ(4.92126, 4.92126, 0); // ~1.5m, 1.5m
        ElevationMarker marker = ElevationMarker.CreateElevationMarker(
            doc, elevType.Id, markerLocation, 50); // scale 1:50

        // Create all 4 elevation views (indices 0-3)
        for (int i = 0; i < marker.MaximumViewCount; i++)
        {
            if (marker.IsAvailableIndex(i))
                marker.CreateElevation(doc, hostPlan.Id, i);
        }
    }

    tx.Commit();
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # 4. Annotation Elements (~11 samples)
    # ------------------------------------------------------------------

    def _annotation_elements(self) -> List[SAMPLE]:
        samples = []

        # TextNote
        samples.append(_s(
            "Create a TextNote annotation in a floor plan view",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(doc, "Create Text Note"))
{
    tx.Start();

    View view = doc.GetElement(viewId) as View;

    TextNoteType tnt = new FilteredElementCollector(doc)
        .OfClass(typeof(TextNoteType))
        .Cast<TextNoteType>()
        .FirstOrDefault();

    if (view != null && tnt != null)
    {
        XYZ location = new XYZ(3.28084, 3.28084, 0); // ~1m, 1m in feet
        TextNote textNote = TextNote.Create(
            doc, view.Id, location, "Structural wall - see S-001", tnt.Id);
    }

    tx.Commit();
}""",
        ))

        samples.append(_s(
            "Create a TextNote with centered horizontal alignment",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(doc, "Create Centered Text Note"))
{
    tx.Start();

    View view = doc.GetElement(viewId) as View;
    TextNoteType tnt = new FilteredElementCollector(doc)
        .OfClass(typeof(TextNoteType))
        .Cast<TextNoteType>()
        .FirstOrDefault();

    if (view != null && tnt != null)
    {
        TextNoteOptions opts = new TextNoteOptions(tnt.Id)
        {
            HorizontalAlignment = HorizontalTextAlignment.Center,
            Rotation = 0.0
        };
        TextNote.Create(doc, view.Id, new XYZ(5.0, 5.0, 0), "CENTER ALIGNED NOTE", opts);
    }

    tx.Commit();
}""",
        ))

        # DetailLine
        samples.append(_s(
            "Create a detail line annotation between two points in a view",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Create Detail Line"))
{
    tx.Start();

    View view = doc.GetElement(viewId) as View;
    if (view != null)
    {
        Line line = Line.CreateBound(XYZ.Zero, new XYZ(9.84252, 0, 0)); // 3000mm
        doc.Create.NewDetailCurve(view, line);
    }

    tx.Commit();
}""",
        ))

        # FilledRegion
        samples.append(_s(
            "Create a FilledRegion with a rectangular boundary in a view",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

using (Transaction tx = new Transaction(doc, "Create Filled Region"))
{
    tx.Start();

    View view = doc.GetElement(viewId) as View;
    FilledRegionType frt = new FilteredElementCollector(doc)
        .OfClass(typeof(FilledRegionType))
        .Cast<FilledRegionType>()
        .FirstOrDefault();

    if (view != null && frt != null)
    {
        double w = 6.56168; // 2000mm in ft
        double h = 3.28084; // 1000mm in ft

        CurveLoop boundary = new CurveLoop();
        boundary.Append(Line.CreateBound(new XYZ(0, 0, 0), new XYZ(w, 0, 0)));
        boundary.Append(Line.CreateBound(new XYZ(w, 0, 0), new XYZ(w, h, 0)));
        boundary.Append(Line.CreateBound(new XYZ(w, h, 0), new XYZ(0, h, 0)));
        boundary.Append(Line.CreateBound(new XYZ(0, h, 0), new XYZ(0, 0, 0)));

        FilledRegion.Create(doc, frt.Id, view.Id, new List<CurveLoop> { boundary });
    }

    tx.Commit();
}""",
        ))

        # Linear dimension
        samples.append(_s(
            "Create a linear dimension between two reference planes in a view",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

using (Transaction tx = new Transaction(doc, "Create Linear Dimension"))
{
    tx.Start();

    View view = doc.GetElement(viewId) as View;
    List<ReferencePlane> rps = new FilteredElementCollector(doc)
        .OfClass(typeof(ReferencePlane))
        .Cast<ReferencePlane>()
        .Take(2).ToList();

    if (view != null && rps.Count == 2)
    {
        ReferenceArray refs = new ReferenceArray();
        refs.Append(rps[0].GetReference());
        refs.Append(rps[1].GetReference());

        Line dimLine = Line.CreateBound(new XYZ(-3.0, 3.28084, 0), new XYZ(3.0, 3.28084, 0));
        doc.Create.NewDimension(view, dimLine, refs);
    }

    tx.Commit();
}""",
        ))

        # Tag instance
        samples.append(_s(
            "Tag a door FamilyInstance with its default tag in a floor plan view",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Tag Door"))
{
    tx.Start();

    View view = doc.GetElement(viewId) as View;
    FamilyInstance door = doc.GetElement(doorId) as FamilyInstance;

    if (view != null && door != null)
    {
        Reference doorRef = new Reference(door);
        LocationPoint lp  = door.Location as LocationPoint;
        XYZ tagLoc = lp != null
            ? new XYZ(lp.Point.X + 0.5, lp.Point.Y + 0.5, 0)
            : XYZ.Zero;

        IndependentTag.Create(
            doc, view.Id, doorRef, false,
            TagMode.TM_ADDBY_CATEGORY,
            TagOrientation.Horizontal,
            tagLoc);
    }

    tx.Commit();
}""",
        ))

        # Spot elevation
        samples.append(_s(
            "Create a spot elevation annotation on the top face of a floor element",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Create Spot Elevation"))
{
    tx.Start();

    View view = doc.GetElement(viewId) as View;
    Floor floor = doc.GetElement(floorId) as Floor;

    if (view != null && floor != null)
    {
        Options opts = new Options { ComputeReferences = true, View = view };
        Reference topFaceRef = null;

        foreach (GeometryObject obj in floor.get_Geometry(opts))
        {
            if (obj is Solid solid)
            {
                foreach (Face face in solid.Faces)
                {
                    if (face.ComputeNormal(new UV(0.5, 0.5)).IsAlmostEqualTo(XYZ.BasisZ))
                    {
                        topFaceRef = face.Reference;
                        break;
                    }
                }
            }
            if (topFaceRef != null) break;
        }

        if (topFaceRef != null)
        {
            XYZ origin = new XYZ(3.28084, 3.28084, 0);
            XYZ bend   = origin + new XYZ(0.5, 0.5, 0);
            XYZ end    = origin + new XYZ(1.0, 0.5, 0);
            doc.Create.NewSpotElevation(view, topFaceRef, origin, bend, end, origin, false);
        }
    }

    tx.Commit();
}""",
        ))

        # Revision cloud
        samples.append(_s(
            "Create a revision cloud on a view to mark a changed area",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

using (Transaction tx = new Transaction(doc, "Create Revision Cloud"))
{
    tx.Start();

    IList<ElementId> revIds = Revision.GetAllRevisionIds(doc);
    ElementId revId = revIds.LastOrDefault();
    View view = doc.GetElement(viewId) as View;

    if (revId != null && view != null)
    {
        CurveLoop loop = new CurveLoop();
        loop.Append(Line.CreateBound(new XYZ(0.5, 0.5, 0), new XYZ(2.0, 0.5, 0)));
        loop.Append(Line.CreateBound(new XYZ(2.0, 0.5, 0), new XYZ(2.0, 1.5, 0)));
        loop.Append(Line.CreateBound(new XYZ(2.0, 1.5, 0), new XYZ(0.5, 1.5, 0)));
        loop.Append(Line.CreateBound(new XYZ(0.5, 1.5, 0), new XYZ(0.5, 0.5, 0)));

        RevisionCloud.Create(doc, view, revId, new List<CurveLoop> { loop });
    }

    tx.Commit();
}""",
        ))

        # Room tag all rooms
        samples.append(_s(
            "Tag all rooms in the active floor plan view with room tags",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using System.Collections.Generic;
using System.Linq;

using (Transaction tx = new Transaction(doc, "Tag All Rooms"))
{
    tx.Start();

    ViewPlan plan = doc.ActiveView as ViewPlan;
    if (plan == null) { tx.RollBack(); return; }

    List<Room> rooms = new FilteredElementCollector(doc, plan.Id)
        .OfCategory(BuiltInCategory.OST_Rooms)
        .Cast<Room>()
        .Where(r => r.Area > 0)
        .ToList();

    foreach (Room room in rooms)
    {
        LocationPoint lp = room.Location as LocationPoint;
        if (lp != null)
        {
            UV tagPoint = new UV(lp.Point.X, lp.Point.Y);
            doc.Create.NewRoomTag(new LinkElementId(room.Id), tagPoint, plan.Id);
        }
    }

    tx.Commit();
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # 5. Element Transforms (~20 samples)
    # ------------------------------------------------------------------

    def _element_transforms(self) -> List[SAMPLE]:
        samples = []

        # MoveElement
        samples.append(_s(
            "Move a wall element by a translation vector of (1000mm, 0, 0)",
            f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Move Wall"))
{{
    tx.Start();

    XYZ translation = new XYZ({_ft(1000)}, 0, 0); // 1000 mm in feet
    ElementTransformUtils.MoveElement(doc, wallId, translation);

    tx.Commit();
}}""",
        ))

        samples.append(_s(
            "Move multiple elements simultaneously using MoveElements",
            f"""\
using Autodesk.Revit.DB;
using System.Collections.Generic;

using (Transaction tx = new Transaction(doc, "Move Elements"))
{{
    tx.Start();

    ICollection<ElementId> ids = new List<ElementId> {{ elemId1, elemId2, elemId3 }};
    XYZ delta = new XYZ(0, {_ft(500)}, 0); // 500 mm in Y

    ElementTransformUtils.MoveElements(doc, ids, delta);

    tx.Commit();
}}""",
        ))

        # RotateElement
        samples.append(_s(
            "Rotate a family instance 45 degrees about the Z-axis through its location point",
            """\
using Autodesk.Revit.DB;
using System;

using (Transaction tx = new Transaction(doc, "Rotate Element"))
{
    tx.Start();

    FamilyInstance fi = doc.GetElement(instanceId) as FamilyInstance;
    LocationPoint lp  = fi?.Location as LocationPoint;

    if (lp != null)
    {
        Line axis = Line.CreateBound(lp.Point, lp.Point + XYZ.BasisZ);
        double angleRad = Math.PI / 4.0; // 45 degrees
        ElementTransformUtils.RotateElement(doc, instanceId, axis, angleRad);
    }

    tx.Commit();
}""",
        ))

        samples.append(_s(
            "Rotate a wall 90 degrees about a vertical axis at the world origin",
            """\
using Autodesk.Revit.DB;
using System;

using (Transaction tx = new Transaction(doc, "Rotate Wall 90"))
{
    tx.Start();

    Line axis     = Line.CreateBound(XYZ.Zero, XYZ.BasisZ);
    double angle  = Math.PI / 2.0; // 90 degrees
    ElementTransformUtils.RotateElement(doc, wallId, axis, angle);

    tx.Commit();
}""",
        ))

        # CopyElement
        samples.append(_s(
            "Copy a family instance and offset it by 2000mm in X",
            f"""\
using Autodesk.Revit.DB;
using System.Collections.Generic;

using (Transaction tx = new Transaction(doc, "Copy Element"))
{{
    tx.Start();

    XYZ offset = new XYZ({_ft(2000)}, 0, 0); // 2000 mm in feet
    ICollection<ElementId> newIds = ElementTransformUtils.CopyElement(
        doc, instanceId, offset);

    tx.Commit();
}}""",
        ))

        samples.append(_s(
            "Copy a set of elements to a different level by specifying a Z offset",
            f"""\
using Autodesk.Revit.DB;
using System.Collections.Generic;

using (Transaction tx = new Transaction(doc, "Copy to Upper Level"))
{{
    tx.Start();

    ICollection<ElementId> sourceIds = new List<ElementId> {{ id1, id2, id3 }};
    double floorHeightFt = {_ft(3000)}; // 3000 mm storey height

    XYZ offset = new XYZ(0, 0, floorHeightFt);
    ICollection<ElementId> copies = ElementTransformUtils.CopyElements(
        doc, sourceIds, offset);

    tx.Commit();
}}""",
        ))

        # MirrorElement
        samples.append(_s(
            "Mirror a family instance about a vertical plane at X=0",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Mirror Element"))
{
    tx.Start();

    // Mirror plane: YZ plane (normal = X axis, passing through origin)
    Plane mirrorPlane = Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero);

    // MirrorElement returns the new mirrored element id
    ElementId mirroredId = ElementTransformUtils.MirrorElement(
        doc, instanceId, mirrorPlane);

    tx.Commit();
}""",
        ))

        samples.append(_s(
            "Mirror multiple walls about a reference plane",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

using (Transaction tx = new Transaction(doc, "Mirror Walls"))
{
    tx.Start();

    ReferencePlane rp = new FilteredElementCollector(doc)
        .OfClass(typeof(ReferencePlane))
        .Cast<ReferencePlane>()
        .FirstOrDefault(p => p.Name == "Mirror Axis");

    if (rp != null)
    {
        Plane mirrorPlane = rp.GetPlane();
        ICollection<ElementId> wallIds = new List<ElementId> { wallId1, wallId2 };

        ICollection<ElementId> mirrored = ElementTransformUtils.MirrorElements(
            doc, wallIds, mirrorPlane, true); // true = copy (not move)
    }

    tx.Commit();
}""",
        ))

        # LocationPoint set
        samples.append(_s(
            "Move a family instance by directly setting its LocationPoint",
            f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Set Location Point"))
{{
    tx.Start();

    FamilyInstance fi = doc.GetElement(instanceId) as FamilyInstance;
    LocationPoint lp  = fi?.Location as LocationPoint;

    if (lp != null)
    {{
        lp.Point = new XYZ({_ft(3000)}, {_ft(1500)}, 0); // 3000mm, 1500mm
    }}

    tx.Commit();
}}""",
        ))

        # LocationCurve move for walls
        samples.append(_s(
            "Reposition a wall by setting new start and end points on its LocationCurve",
            f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Move Wall by Curve"))
{{
    tx.Start();

    Wall wall = doc.GetElement(wallId) as Wall;
    LocationCurve lc = wall?.Location as LocationCurve;

    if (lc != null)
    {{
        Line newLine = Line.CreateBound(
            new XYZ(0, {_ft(1000)}, 0),
            new XYZ({_ft(6000)}, {_ft(1000)}, 0));
        lc.Curve = newLine;
    }}

    tx.Commit();
}}""",
        ))

        # CopyElements between docs
        samples.append(_s(
            "Copy elements from one document to another using ElementTransformUtils.CopyElements",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

using (Transaction tx = new Transaction(destDoc, "Copy from Source"))
{
    tx.Start();

    ICollection<ElementId> sourceIds = new List<ElementId> { id1, id2 };

    // CopyPasteOptions controls element type handling
    CopyPasteOptions opts = new CopyPasteOptions();
    opts.SetDuplicateTypeNamesHandler(new CopyHandler());

    ElementTransformUtils.CopyElements(
        sourceDoc,
        sourceIds,
        destDoc,
        Transform.Identity,
        opts);

    tx.Commit();
}

// Minimal handler that uses destination types
public class CopyHandler : IDuplicateTypeNamesHandler
{
    public DuplicateTypeAction OnDuplicateTypeNamesFound(
        DuplicateTypeNamesHandlerArgs args)
        => DuplicateTypeAction.UseDestinationTypes;
}""",
        ))

        # Array linear
        samples.append(_s(
            "Create a linear array of a column family instance with 5 copies at 3000mm spacing",
            f"""\
using Autodesk.Revit.DB;
using System.Collections.Generic;

using (Transaction tx = new Transaction(doc, "Linear Array"))
{{
    tx.Start();

    XYZ spacing = new XYZ({_ft(3000)}, 0, 0); // 3000mm spacing in X

    // Manual copy loop (Revit API does not expose NewArray for FamilyInstances directly)
    for (int i = 1; i <= 4; i++) // 4 additional copies = 5 total
    {{
        XYZ offset = new XYZ(spacing.X * i, 0, 0);
        ElementTransformUtils.CopyElement(doc, columnId, offset);
    }}

    tx.Commit();
}}""",
        ))

        # Rotate about host axis
        samples.append(_s(
            "Rotate a FamilyInstance to a specific absolute angle by reading and adjusting its current rotation",
            """\
using Autodesk.Revit.DB;
using System;

using (Transaction tx = new Transaction(doc, "Set Absolute Rotation"))
{
    tx.Start();

    FamilyInstance fi = doc.GetElement(instanceId) as FamilyInstance;
    LocationPoint lp  = fi?.Location as LocationPoint;

    if (lp != null)
    {
        double currentAngle = lp.Rotation;          // radians
        double targetAngle  = Math.PI / 2.0;        // 90 degrees
        double delta        = targetAngle - currentAngle;

        Line axis = Line.CreateBound(lp.Point, lp.Point + XYZ.BasisZ);
        ElementTransformUtils.RotateElement(doc, instanceId, axis, delta);
    }

    tx.Commit();
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # 6. Document Operations (~20 samples)
    # ------------------------------------------------------------------

    def _document_operations(self) -> List[SAMPLE]:
        samples = []

        # Open family doc
        samples.append(_s(
            "Open a Revit family (.rfa) file as a Document for editing",
            """\
using Autodesk.Revit.DB;

// uiApp is UIApplication from IExternalCommand.Execute
Application app = uiApp.Application;

string familyPath = @"C:\Families\CustomColumn.rfa";
Document familyDoc = app.OpenDocumentFile(familyPath);

// familyDoc.IsFamilyDocument == true""",
        ))

        # EditFamily
        samples.append(_s(
            "Open a loaded family for in-place editing using Document.EditFamily",
            """\
using Autodesk.Revit.DB;

Family family = doc.GetElement(familyId) as Family;
if (family != null && family.IsEditable)
{
    Document familyDoc = doc.EditFamily(family);
    // Make changes to familyDoc here, then reload
}""",
        ))

        # LoadFamily
        samples.append(_s(
            "Load a family from disk into the project document",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Load Family"))
{
    tx.Start();

    Family loadedFamily;
    bool success = doc.LoadFamily(
        @"C:\Families\Steel_Column_W.rfa",
        out loadedFamily);

    if (success)
    {
        // Activate all symbols
        foreach (ElementId symId in loadedFamily.GetFamilySymbolIds())
        {
            FamilySymbol sym = doc.GetElement(symId) as FamilySymbol;
            if (sym != null && !sym.IsActive)
                sym.Activate();
        }
    }

    tx.Commit();
}""",
        ))

        # LoadFamilySymbol
        samples.append(_s(
            "Load a specific family type from a family file using LoadFamilySymbol",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Load Family Symbol"))
{
    tx.Start();

    FamilySymbol symbol;
    bool loaded = doc.LoadFamilySymbol(
        @"C:\Families\Doors\Single_Flush.rfa",
        "36\" x 84\"",
        out symbol);

    if (loaded && !symbol.IsActive)
        symbol.Activate();

    tx.Commit();
}""",
        ))

        # Save family back to project
        samples.append(_s(
            "Save family changes and reload into the project with LoadOptions to override types",
            """\
using Autodesk.Revit.DB;

// familyDoc is the opened family document
familyDoc.Save();

// Reload back into host doc
using (Transaction tx = new Transaction(hostDoc, "Reload Family"))
{
    tx.Start();

    IFamilyLoadOptions opts = new FamilyLoadOptions();
    Family reloaded;
    familyDoc.LoadFamily(hostDoc, opts, out reloaded);

    tx.Commit();
}

// FamilyLoadOptions: overwrite existing types
public class FamilyLoadOptions : IFamilyLoadOptions
{
    public bool OnFamilyFound(bool familyInUse, out bool overwriteParameterValues)
    {
        overwriteParameterValues = true;
        return true; // overwrite
    }
    public bool OnSharedFamilyFound(Family sharedFamily, bool familyInUse,
        out FamilySource source, out bool overwriteParameterValues)
    {
        source = FamilySource.Family;
        overwriteParameterValues = true;
        return true;
    }
}""",
        ))

        # SaveAs
        samples.append(_s(
            "Save the active document to a new file path using Document.SaveAs",
            """\
using Autodesk.Revit.DB;

SaveAsOptions opts = new SaveAsOptions
{
    OverwriteExistingFile = true,
    MaximumBackups        = 3,
    Compact               = true,
};

doc.SaveAs(@"C:\Projects\MyProject_Backup.rvt", opts);""",
        ))

        # Transaction group
        samples.append(_s(
            "Use a TransactionGroup to wrap multiple transactions that can be rolled back together",
            """\
using Autodesk.Revit.DB;

using (TransactionGroup tg = new TransactionGroup(doc, "Batch Modifications"))
{
    tg.Start();

    using (Transaction tx1 = new Transaction(doc, "Step 1"))
    {
        tx1.Start();
        // ... first changes ...
        tx1.Commit();
    }

    using (Transaction tx2 = new Transaction(doc, "Step 2"))
    {
        tx2.Start();
        // ... second changes ...
        tx2.Commit();
    }

    // Assimilate merges all sub-transactions into one undo step
    tg.Assimilate();
    // Or tg.RollBack() to undo all
}""",
        ))

        # SubTransaction
        samples.append(_s(
            "Use a SubTransaction to make incremental changes that can be rolled back independently",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Outer Transaction"))
{
    tx.Start();

    using (SubTransaction sub = new SubTransaction(doc))
    {
        sub.Start();
        // Experimental change
        bool success = TryModification(doc);
        if (success)
            sub.Commit();
        else
            sub.RollBack(); // revert only the sub-transaction
    }

    tx.Commit();
}""",
        ))

        # Open/close linked files
        samples.append(_s(
            "Load all unloaded Revit links in the current document",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

using (Transaction tx = new Transaction(doc, "Load All Links"))
{
    tx.Start();

    IList<Element> links = new FilteredElementCollector(doc)
        .OfClass(typeof(RevitLinkType))
        .ToElements();

    foreach (RevitLinkType linkType in links)
    {
        if (linkType.GetLinkedFileStatus() != LinkedFileStatus.Loaded)
        {
            linkType.Load();
        }
    }

    tx.Commit();
}""",
        ))

        # Purge unused
        samples.append(_s(
            "Get the set of purgeable element ids and purge unused elements from the document",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

using (Transaction tx = new Transaction(doc, "Purge Unused"))
{
    tx.Start();

    HashSet<ElementId> purgeableIds;
    PerformanceAdviser adviser = PerformanceAdviser.GetPerformanceAdviser();
    // Revit 2023+: use doc.GetUnusedElements
    ICollection<ElementId> unused = doc.GetUnusedElements(new HashSet<ElementId>());

    doc.Delete(unused);

    tx.Commit();
}""",
        ))

        # Delete elements
        samples.append(_s(
            "Delete a list of elements from the document by their ElementIds",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

using (Transaction tx = new Transaction(doc, "Delete Elements"))
{
    tx.Start();

    ICollection<ElementId> idsToDelete = new List<ElementId>
    {
        new ElementId(100001),
        new ElementId(100002),
    };

    // Delete returns ids of additionally deleted dependents
    ICollection<ElementId> deleted = doc.Delete(idsToDelete);

    tx.Commit();
}""",
        ))

        # Workset creation
        samples.append(_s(
            "Create a new user workset named 'MEP Systems' in a workshared document",
            """\
using Autodesk.Revit.DB;

if (doc.IsWorkshared)
{
    using (Transaction tx = new Transaction(doc, "Create Workset"))
    {
        tx.Start();
        Workset.Create(doc, "MEP Systems");
        tx.Commit();
    }
}""",
        ))

        # Get/set project information
        samples.append(_s(
            "Read and update project information parameters (project name, number, address)",
            """\
using Autodesk.Revit.DB;

ProjectInfo pi = doc.ProjectInformation;

using (Transaction tx = new Transaction(doc, "Update Project Info"))
{
    tx.Start();

    pi.Name          = "Office Tower - Phase 2";
    pi.Number        = "2026-OT-002";
    pi.Address       = "123 Main Street, Anytown";
    pi.ClientName    = "ACME Developments";
    pi.BuildingName  = "Tower B";
    pi.Status        = "Design Development";
    pi.IssueDate     = "2026-03-23";

    tx.Commit();
}""",
        ))

        # FamilyManager add type
        samples.append(_s(
            "Add a new FamilyType to a family document and set its parameters",
            """\
using Autodesk.Revit.DB;

// FamilyManager operations must occur OUTSIDE Transaction blocks
FamilyManager fm = familyDoc.FamilyManager;

FamilyType newType = fm.NewType("600x900");

// Set parameter values for this type
FamilyParameter widthParam  = fm.get_Parameter("Width");
FamilyParameter heightParam = fm.get_Parameter("Height");

fm.CurrentType = newType;
fm.Set(widthParam,  600.0 / 304.8); // 600mm -> ft
fm.Set(heightParam, 900.0 / 304.8); // 900mm -> ft""",
        ))

        # Family document - close without saving
        samples.append(_s(
            "Close a family document without saving after inspecting it",
            """\
using Autodesk.Revit.DB;

Application app = uiApp.Application;

// Open read-only (no changes planned)
OpenOptions openOpts = new OpenOptions();
ModelPath modelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(
    @"C:\Families\MyFamily.rfa");

Document familyDoc = app.OpenDocumentFile(modelPath, openOpts);

try
{
    // Inspect the family...
    bool isFamilyDoc = familyDoc.IsFamilyDocument;
}
finally
{
    familyDoc.Close(false); // false = do not save
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # 7. Selection and Picking (~15 samples)
    # ------------------------------------------------------------------

    def _selection_and_picking(self) -> List[SAMPLE]:
        samples = []

        # Get current selection
        samples.append(_s(
            "Get the currently selected elements in the Revit UI",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Autodesk.Revit.UI.Selection;
using System.Collections.Generic;

UIDocument uidoc = uiApp.ActiveUIDocument;
Selection selection = uidoc.Selection;

ICollection<ElementId> selectedIds = selection.GetElementIds();
foreach (ElementId id in selectedIds)
{
    Element elem = doc.GetElement(id);
}""",
        ))

        # Set selection
        samples.append(_s(
            "Programmatically select a list of elements in the Revit UI",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Autodesk.Revit.UI.Selection;
using System.Collections.Generic;

UIDocument uidoc = uiApp.ActiveUIDocument;

ICollection<ElementId> idsToSelect = new List<ElementId>
{
    wall1Id, wall2Id, column1Id
};

uidoc.Selection.SetElementIds(idsToSelect);""",
        ))

        # PickObject single
        samples.append(_s(
            "Prompt the user to pick a single element from the model",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Autodesk.Revit.UI.Selection;

UIDocument uidoc = uiApp.ActiveUIDocument;

try
{
    Reference pickedRef = uidoc.Selection.PickObject(
        ObjectType.Element,
        "Select an element");

    Element picked = doc.GetElement(pickedRef);
}
catch (Autodesk.Revit.Exceptions.OperationCanceledException)
{
    // User pressed Escape
}""",
        ))

        # PickObject with filter
        samples.append(_s(
            "Prompt the user to pick only a Wall element using a selection filter",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Autodesk.Revit.UI.Selection;

public class WallSelectionFilter : ISelectionFilter
{
    public bool AllowElement(Element elem) => elem is Wall;
    public bool AllowReference(Reference reference, XYZ position) => false;
}

// In command Execute():
UIDocument uidoc = uiApp.ActiveUIDocument;
try
{
    Reference r = uidoc.Selection.PickObject(
        ObjectType.Element,
        new WallSelectionFilter(),
        "Select a wall");

    Wall wall = doc.GetElement(r) as Wall;
}
catch (Autodesk.Revit.Exceptions.OperationCanceledException) { }""",
        ))

        # PickObjects multiple
        samples.append(_s(
            "Prompt the user to pick multiple elements at once using PickObjects",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Autodesk.Revit.UI.Selection;
using System.Collections.Generic;

UIDocument uidoc = uiApp.ActiveUIDocument;

IList<Reference> refs = uidoc.Selection.PickObjects(
    ObjectType.Element,
    "Select multiple elements (Finish with Finish button)");

List<Element> elements = new List<Element>();
foreach (Reference r in refs)
    elements.Add(doc.GetElement(r));""",
        ))

        # PickPoint
        samples.append(_s(
            "Prompt the user to pick a point in the model using PickPoint",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Autodesk.Revit.UI.Selection;

UIDocument uidoc = uiApp.ActiveUIDocument;

try
{
    XYZ pickedPoint = uidoc.Selection.PickPoint(
        ObjectSnapTypes.Endpoints | ObjectSnapTypes.Midpoints,
        "Pick a point on the model");

    double xMm = pickedPoint.X * 304.8;
    double yMm = pickedPoint.Y * 304.8;
    double zMm = pickedPoint.Z * 304.8;
}
catch (Autodesk.Revit.Exceptions.OperationCanceledException) { }""",
        ))

        # PickElementsByRectangle
        samples.append(_s(
            "Allow the user to drag a selection box to pick multiple elements",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Autodesk.Revit.UI.Selection;
using System.Collections.Generic;

UIDocument uidoc = uiApp.ActiveUIDocument;

IList<Element> picked = uidoc.Selection.PickElementsByRectangle(
    "Drag a rectangle to select elements");

foreach (Element e in picked)
{
    // Process selected elements
}""",
        ))

        # PickFace
        samples.append(_s(
            "Prompt the user to pick a face on an element",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Autodesk.Revit.UI.Selection;

UIDocument uidoc = uiApp.ActiveUIDocument;

try
{
    Reference faceRef = uidoc.Selection.PickObject(
        ObjectType.Face,
        "Pick a face");

    // Resolve the face geometry
    GeometryObject geomObj = doc.GetElement(faceRef)
        .GetGeometryObjectFromReference(faceRef);
    Face face = geomObj as Face;
}
catch (Autodesk.Revit.Exceptions.OperationCanceledException) { }""",
        ))

        # PickEdge
        samples.append(_s(
            "Prompt the user to pick an edge on an element",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Autodesk.Revit.UI.Selection;

UIDocument uidoc = uiApp.ActiveUIDocument;

try
{
    Reference edgeRef = uidoc.Selection.PickObject(
        ObjectType.Edge,
        "Pick an edge");

    Element elem  = doc.GetElement(edgeRef);
    Edge edge     = elem.GetGeometryObjectFromReference(edgeRef) as Edge;
    Curve edgeCrv = edge?.AsCurve();
}
catch (Autodesk.Revit.Exceptions.OperationCanceledException) { }""",
        ))

        # Selection filter by category
        samples.append(_s(
            "Create an ISelectionFilter that only allows structural columns",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI.Selection;

public class StructuralColumnFilter : ISelectionFilter
{
    public bool AllowElement(Element elem)
    {
        return elem.Category?.Id.IntegerValue ==
               (int)BuiltInCategory.OST_StructuralColumns;
    }

    public bool AllowReference(Reference reference, XYZ position) => false;
}

// Usage:
// Reference r = uidoc.Selection.PickObject(
//     ObjectType.Element, new StructuralColumnFilter(), "Pick column");""",
        ))

        # GetSelectionElementIds typed
        samples.append(_s(
            "Filter the current UI selection to only walls and process them",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using System.Collections.Generic;
using System.Linq;

UIDocument uidoc = uiApp.ActiveUIDocument;

List<Wall> selectedWalls = uidoc.Selection
    .GetElementIds()
    .Select(id => doc.GetElement(id))
    .OfType<Wall>()
    .ToList();

foreach (Wall wall in selectedWalls)
{
    double lengthFt = wall.get_Parameter(
        BuiltInParameter.CURVE_ELEM_LENGTH)?.AsDouble() ?? 0;
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # 8. Geometry Access (~20 samples)
    # ------------------------------------------------------------------

    def _geometry_access(self) -> List[SAMPLE]:
        samples = []

        # get_Geometry basics
        samples.append(_s(
            "Access the geometry of an element and iterate its solids",
            """\
using Autodesk.Revit.DB;

Element elem = doc.GetElement(elementId);
Options opts = new Options
{
    ComputeReferences = true,
    IncludeNonVisibleObjects = false,
    DetailLevel = ViewDetailLevel.Fine
};

GeometryElement geomElem = elem.get_Geometry(opts);

foreach (GeometryObject obj in geomElem)
{
    if (obj is Solid solid && solid.Volume > 0)
    {
        double volFt3 = solid.Volume;
        double volM3  = volFt3 * 0.0283168;
    }
    else if (obj is GeometryInstance gi)
    {
        // Nested family geometry
        foreach (GeometryObject instObj in gi.GetInstanceGeometry())
        {
            if (instObj is Solid instSolid && instSolid.Volume > 0)
            {
                // Process instSolid
            }
        }
    }
}""",
        ))

        # BoundingBox
        samples.append(_s(
            "Get the bounding box of an element in world coordinates",
            """\
using Autodesk.Revit.DB;

Element elem = doc.GetElement(elementId);
BoundingBoxXYZ bb = elem.get_BoundingBox(null); // null = world coordinates

if (bb != null)
{
    XYZ min = bb.Min;
    XYZ max = bb.Max;
    double widthFt  = max.X - min.X;
    double depthFt  = max.Y - min.Y;
    double heightFt = max.Z - min.Z;
    double widthMm  = widthFt * 304.8;
}""",
        ))

        # BoundingBox in view
        samples.append(_s(
            "Get the bounding box of an element in the coordinate system of a specific view",
            """\
using Autodesk.Revit.DB;

Element elem = doc.GetElement(elementId);
View view = doc.GetElement(viewId) as View;

BoundingBoxXYZ bb = elem.get_BoundingBox(view);
if (bb != null)
{
    // Min/Max are in the view's coordinate system
    double heightInView = bb.Max.Z - bb.Min.Z;
}""",
        ))

        # Traverse faces of a solid
        samples.append(_s(
            "Iterate all faces of a solid and compute their areas",
            """\
using Autodesk.Revit.DB;

Solid solid = GetFirstSolid(doc, elementId); // helper

double totalAreaFt2 = 0.0;
foreach (Face face in solid.Faces)
{
    totalAreaFt2 += face.Area;
}
double totalAreaMm2 = totalAreaFt2 * 92903.04; // ft^2 -> mm^2

static Solid GetFirstSolid(Document d, ElementId id)
{
    Options o = new Options();
    foreach (GeometryObject obj in d.GetElement(id).get_Geometry(o))
        if (obj is Solid s && s.Volume > 0) return s;
    return null;
}""",
        ))

        # Traverse edges of a face
        samples.append(_s(
            "Get all edge loops of a face and measure total edge length",
            """\
using Autodesk.Revit.DB;

Face face = GetFaceFromElement(doc, elementId); // helper

double totalLengthFt = 0.0;
foreach (EdgeArray loop in face.EdgeLoops)
{
    foreach (Edge edge in loop)
    {
        Curve edgeCurve = edge.AsCurve();
        totalLengthFt += edgeCurve.Length;
    }
}
double totalLengthMm = totalLengthFt * 304.8;""",
        ))

        # Face normal at UV
        samples.append(_s(
            "Compute the face normal at its center (UV midpoint)",
            """\
using Autodesk.Revit.DB;

Face face = GetFaceFromElement(doc, elementId);

BoundingBoxUV uvBounds = face.GetBoundingBox();
UV center = new UV(
    (uvBounds.Min.U + uvBounds.Max.U) / 2.0,
    (uvBounds.Min.V + uvBounds.Max.V) / 2.0);

XYZ normal = face.ComputeNormal(center);
bool isFacingUp = normal.IsAlmostEqualTo(XYZ.BasisZ);""",
        ))

        # Solid Boolean
        samples.append(_s(
            "Perform a Boolean intersection between two solids using BooleanOperationsUtils",
            """\
using Autodesk.Revit.DB;

Solid solid1 = GetFirstSolid(doc, elem1Id);
Solid solid2 = GetFirstSolid(doc, elem2Id);

try
{
    Solid intersection = BooleanOperationsUtils.ExecuteBooleanOperation(
        solid1, solid2, BooleanOperationsType.Intersect);

    bool theyIntersect = intersection != null && intersection.Volume > 1e-9;
}
catch (Autodesk.Revit.Exceptions.InvalidOperationException)
{
    // Solids may not be valid for Boolean operations
}""",
        ))

        # CurveLoop from edges
        samples.append(_s(
            "Build a CurveLoop from the outer boundary of a planar face",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

PlanarFace pFace = GetPlanarFaceFromElement(doc, elementId);

// EdgeLoops[0] is the outer boundary for a planar face
List<Curve> boundaryCurves = new List<Curve>();
foreach (Edge edge in pFace.EdgeLoops.get_Item(0))
{
    boundaryCurves.Add(edge.AsCurve());
}

CurveLoop outerLoop = CurveLoop.Create(boundaryCurves);
double perimeterFt  = outerLoop.GetExactLength();""",
        ))

        # Solid volume / centroid
        samples.append(_s(
            "Get the volume and centroid of the first solid of a family instance",
            """\
using Autodesk.Revit.DB;

FamilyInstance fi = doc.GetElement(instanceId) as FamilyInstance;
Options opts = new Options { DetailLevel = ViewDetailLevel.Fine };

foreach (GeometryObject obj in fi.get_Geometry(opts))
{
    GeometryInstance gi = obj as GeometryInstance;
    if (gi == null) continue;

    foreach (GeometryObject instObj in gi.GetInstanceGeometry())
    {
        if (instObj is Solid solid && solid.Volume > 0)
        {
            double volumeFt3  = solid.Volume;
            double volumeMm3  = volumeFt3 * 28316846.6; // ft3 -> mm3
            XYZ    centroid   = solid.ComputeCentroid();
            break;
        }
    }
}""",
        ))

        # Line / Curve intersection
        samples.append(_s(
            "Find the intersection point between two lines using SetComparisonResult",
            """\
using Autodesk.Revit.DB;

Line line1 = Line.CreateBound(new XYZ(0, 0, 0), new XYZ(10, 0, 0));
Line line2 = Line.CreateBound(new XYZ(5, -5, 0), new XYZ(5, 5, 0));

IntersectionResultArray results;
SetComparisonResult result = line1.Intersect(line2, out results);

if (result == SetComparisonResult.Overlap && results.Size > 0)
{
    XYZ intersectionPt = results.get_Item(0).XYZPoint;
}""",
        ))

        # Tessellate curve
        samples.append(_s(
            "Tessellate an arc curve into polyline points for export",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

Arc arc = Arc.Create(XYZ.Zero, 3.28084, 0, Math.PI, XYZ.BasisX, XYZ.BasisY); // radius 1m

IList<XYZ> tessellatedPoints = arc.Tessellate();
foreach (XYZ pt in tessellatedPoints)
{
    double xMm = pt.X * 304.8;
    double yMm = pt.Y * 304.8;
}""",
        ))

        # Project point onto face
        samples.append(_s(
            "Project a 3D point onto a face and get the UV parameter",
            """\
using Autodesk.Revit.DB;

Face face = GetFaceFromElement(doc, elementId);
XYZ testPoint = new XYZ(3.28084, 3.28084, 0);

IntersectionResult projection = face.Project(testPoint);
if (projection != null)
{
    UV uv       = projection.UVPoint;
    XYZ closest = projection.XYZPoint;
    double dist = projection.Distance; // feet
}""",
        ))

        # RayIntersection
        samples.append(_s(
            "Cast a ray downward from a point and find the first intersecting element using ReferenceIntersector",
            """\
using Autodesk.Revit.DB;

View3D view3d = new FilteredElementCollector(doc)
    .OfClass(typeof(View3D))
    .Cast<View3D>()
    .FirstOrDefault(v => !v.IsTemplate);

if (view3d != null)
{
    ReferenceIntersector ri = new ReferenceIntersector(
        view3d,
        FindReferenceTarget.Face);
    ri.FindReferencesInRevitLinks = false;

    XYZ origin    = new XYZ(5.0, 5.0, 30.0);
    XYZ direction = XYZ.BasisZ.Negate(); // downward

    ReferenceWithContext rwc = ri.FindNearest(origin, direction);
    if (rwc != null)
    {
        Element hit = doc.GetElement(rwc.GetReference());
        double distanceFt = rwc.Proximity;
    }
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # 9. Event Handling (~15 samples)
    # ------------------------------------------------------------------

    def _event_handling(self) -> List[SAMPLE]:
        samples = []

        # IExternalCommand skeleton
        samples.append(_s(
            "Write a minimal IExternalCommand implementation",
            """\
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

[Transaction(TransactionMode.Manual)]
[Regeneration(RegenerationOption.Manual)]
public class MyCommand : IExternalCommand
{
    public Result Execute(
        ExternalCommandData commandData,
        ref string message,
        ElementSet elements)
    {
        UIApplication uiApp = commandData.Application;
        UIDocument    uidoc = uiApp.ActiveUIDocument;
        Document      doc   = uidoc.Document;

        try
        {
            using (Transaction tx = new Transaction(doc, "My Command"))
            {
                tx.Start();
                // ... do work ...
                tx.Commit();
            }
            return Result.Succeeded;
        }
        catch (Exception ex)
        {
            message = ex.Message;
            return Result.Failed;
        }
    }
}""",
        ))

        # IExternalApplication with ribbon
        samples.append(_s(
            "Implement IExternalApplication to add a ribbon panel with a push button on startup",
            """\
using Autodesk.Revit.Attributes;
using Autodesk.Revit.UI;
using System.Reflection;

public class MyApplication : IExternalApplication
{
    public Result OnStartup(UIControlledApplication application)
    {
        RibbonPanel panel = application.CreateRibbonPanel("My Tools");

        string dllPath = Assembly.GetExecutingAssembly().Location;

        PushButtonData buttonData = new PushButtonData(
            "MyCommandButton",
            "Run\nTool",
            dllPath,
            "MyNamespace.MyCommand")
        {
            ToolTip = "Runs the custom tool",
            LargeImage = LoadImage("icon32.png"),
        };

        panel.AddItem(buttonData);
        return Result.Succeeded;
    }

    public Result OnShutdown(UIControlledApplication application)
        => Result.Succeeded;

    private System.Windows.Media.ImageSource LoadImage(string name)
    {
        // Load embedded resource image
        var assembly = Assembly.GetExecutingAssembly();
        using var stream = assembly.GetManifestResourceStream($"MyNamespace.Resources.{name}");
        var decoder = new System.Windows.Media.Imaging.PngBitmapDecoder(
            stream, System.Windows.Media.Imaging.BitmapCreateOptions.PreservePixelFormat,
            System.Windows.Media.Imaging.BitmapCacheOption.Default);
        return decoder.Frames[0];
    }
}""",
        ))

        # DocumentChanged event
        samples.append(_s(
            "Subscribe to the DocumentChanged event to detect element additions",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Events;
using System.Collections.Generic;

// In IExternalApplication.OnStartup:
application.ControlledApplication.DocumentChanged += OnDocumentChanged;

private void OnDocumentChanged(object sender, DocumentChangedEventArgs e)
{
    ICollection<ElementId> added   = e.GetAddedElementIds();
    ICollection<ElementId> deleted = e.GetDeletedElementIds();
    ICollection<ElementId> modified = e.GetModifiedElementIds();

    Document doc = e.GetDocument();
    foreach (ElementId id in added)
    {
        Element elem = doc.GetElement(id);
        // Log or react to new elements
    }
}""",
        ))

        # DocumentSaving event
        samples.append(_s(
            "Subscribe to DocumentSaving to run validation before a document is saved",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Events;

// In OnStartup:
app.ControlledApplication.DocumentSaving += OnDocumentSaving;

private void OnDocumentSaving(object sender, DocumentSavingEventArgs e)
{
    Document doc = e.Document;
    bool isValid = RunValidation(doc);

    if (!isValid)
    {
        // Cancel the save by throwing -- not supported in Revit
        // Instead: show a task dialog warning
        Autodesk.Revit.UI.TaskDialog.Show(
            "Validation Warning",
            "Model has validation issues. Please review before saving.");
    }
}""",
        ))

        # ViewActivated event
        samples.append(_s(
            "Subscribe to ViewActivated to update UI when the user switches views",
            """\
using Autodesk.Revit.UI;
using Autodesk.Revit.UI.Events;

// In OnStartup:
uiApp.ViewActivated += OnViewActivated;

private void OnViewActivated(object sender, ViewActivatedEventArgs e)
{
    View currentView  = e.CurrentActiveView;
    View previousView = e.PreviousActiveView;

    string msg = $"Switched to: {currentView?.Name ?? "None"}";
    // Update status bar or custom panel
}""",
        ))

        # Idling event
        samples.append(_s(
            "Subscribe to the Idling event to perform background processing in Revit's thread",
            """\
using Autodesk.Revit.UI;
using Autodesk.Revit.UI.Events;
using System.Collections.Concurrent;

private static ConcurrentQueue<Action<Document>> _workQueue =
    new ConcurrentQueue<Action<Document>>();

// In OnStartup:
uiApp.Idling += OnIdling;

private void OnIdling(object sender, IdlingEventArgs e)
{
    UIApplication app = sender as UIApplication;
    if (app == null) return;

    if (_workQueue.TryDequeue(out Action<Document> work))
    {
        Document doc = app.ActiveUIDocument?.Document;
        if (doc != null)
        {
            using (Transaction tx = new Transaction(doc, "Background Work"))
            {
                tx.Start();
                work(doc);
                tx.Commit();
            }
        }
    }
    else
    {
        // No more work; raise frequency to minimum to reduce overhead
        e.SetRaiseWithoutDelay(false);
    }
}""",
        ))

        # ExternalEvent + IExternalEventHandler
        samples.append(_s(
            "Create an ExternalEvent to marshal work from a non-Revit thread into Revit's context",
            """\
using Autodesk.Revit.UI;

// Handler class
public class UpdateParameterHandler : IExternalEventHandler
{
    public ElementId TargetId { get; set; }
    public string    NewValue  { get; set; }

    public void Execute(UIApplication app)
    {
        Document doc = app.ActiveUIDocument.Document;
        using (Transaction tx = new Transaction(doc, "Update Parameter"))
        {
            tx.Start();
            Element elem = doc.GetElement(TargetId);
            elem?.LookupParameter("MyParam")?.Set(NewValue);
            tx.Commit();
        }
    }

    public string GetName() => "UpdateParameterHandler";
}

// Register once in OnStartup:
var handler = new UpdateParameterHandler();
ExternalEvent externalEvent = ExternalEvent.Create(handler);

// From WPF button click or background thread:
handler.TargetId = selectedId;
handler.NewValue = "New Value";
externalEvent.Raise(); // queues execution in Revit thread""",
        ))

        # Add-in manifest snippet
        samples.append(_s(
            "Write a .addin manifest file to register an IExternalCommand with Revit 2026",
            """\
<?xml version="1.0" encoding="utf-8"?>
<!-- File: MyAddin.addin -->
<!-- Place in: %AppData%\\Autodesk\\Revit\\Addins\\2026\\ -->
<RevitAddIns>
  <AddIn Type="Application">
    <Name>My Revit Add-in</Name>
    <Assembly>C:\\Addins\\MyAddin\\MyAddin.dll</Assembly>
    <AddInId>a1b2c3d4-e5f6-7890-abcd-ef1234567890</AddInId>
    <FullClassName>MyNamespace.MyApplication</FullClassName>
    <VendorId>MYCO</VendorId>
    <VendorDescription>My Company</VendorDescription>
  </AddIn>
  <AddIn Type="Command">
    <Name>My Command</Name>
    <Assembly>C:\\Addins\\MyAddin\\MyAddin.dll</Assembly>
    <AddInId>b2c3d4e5-f6a7-8901-bcde-f12345678901</AddInId>
    <FullClassName>MyNamespace.MyCommand</FullClassName>
    <Text>Run Tool</Text>
    <VendorId>MYCO</VendorId>
  </AddIn>
</RevitAddIns>""",
        ))

        # DocumentOpened event
        samples.append(_s(
            "Subscribe to the DocumentOpened event to auto-run setup when a document is opened",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Events;

// In OnStartup:
app.ControlledApplication.DocumentOpened += OnDocumentOpened;

private void OnDocumentOpened(object sender, DocumentOpenedEventArgs e)
{
    Document doc = e.Document;
    if (doc.IsWorkshared && !doc.IsReadOnly)
    {
        // Example: sync worksets on open
        SynchronizeWithCentralOptions syncOpts =
            new SynchronizeWithCentralOptions();
        syncOpts.SetRelinquishOptions(new RelinquishOptions(true));
        // doc.SynchronizeWithCentral(new TransactWithCentralOptions(), syncOpts);
    }
}""",
        ))

        # TaskDialog
        samples.append(_s(
            "Show a TaskDialog with Yes/No buttons and respond to the user's choice",
            """\
using Autodesk.Revit.UI;

TaskDialog dialog = new TaskDialog("Confirmation Required")
{
    MainInstruction  = "Delete selected elements?",
    MainContent      = "This will permanently remove the selected elements from the model.",
    CommonButtons    = TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No,
    DefaultButton    = TaskDialogResult.No,
    FooterText       = "Action cannot be undone.",
};

TaskDialogResult result = dialog.Show();

if (result == TaskDialogResult.Yes)
{
    // Proceed with deletion
    using (Transaction tx = new Transaction(doc, "Delete Elements"))
    {
        tx.Start();
        doc.Delete(selectedIds);
        tx.Commit();
    }
}""",
        ))

        # ProgressBar / CancellationToken
        samples.append(_s(
            "Use a ProgressIndicator to report progress during a long-running loop",
            """\
using Autodesk.Revit.UI;
using System.Collections.Generic;

UIApplication uiApp = commandData.Application;
int total = elements.Count;

using (Autodesk.Revit.DB.ProgressIndicator pi =
    uiApp.Application.Create.NewProgressIndicator())
{
    pi.ProgressBarEnabled = true;
    pi.Caption = "Processing elements...";
    pi.Start(0, total);

    for (int i = 0; i < total; i++)
    {
        if (pi.IsCanceled())
            break;

        ProcessElement(elements[i]);
        pi.Increment();
    }
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # 10. Error Handling (~15 samples)
    # ------------------------------------------------------------------

    def _error_handling(self) -> List[SAMPLE]:
        samples = []

        # IFailuresPreprocessor
        samples.append(_s(
            "Implement IFailuresPreprocessor to suppress and auto-resolve non-critical warnings",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

public class SuppressWarningsPreprocessor : IFailuresPreprocessor
{
    public FailureProcessingResult PreprocessFailures(FailuresAccessor a)
    {
        IList<FailureMessageAccessor> failures = a.GetFailureMessages();
        bool hasErrors = false;

        foreach (FailureMessageAccessor fma in failures)
        {
            FailureSeverity severity = fma.GetSeverity();

            if (severity == FailureSeverity.Warning)
            {
                // Delete the warning (suppress it)
                a.DeleteWarning(fma);
            }
            else if (severity == FailureSeverity.Error)
            {
                // Try to resolve with the first available resolution
                IList<FailureResolutionType> resolutions =
                    fma.GetApplicableResolutionTypes();
                if (resolutions.Count > 0)
                {
                    fma.SetCurrentResolutionType(resolutions[0]);
                    a.ResolveFailure(fma);
                }
                else
                {
                    hasErrors = true;
                }
            }
        }

        return hasErrors
            ? FailureProcessingResult.ProceedWithRollBack
            : FailureProcessingResult.Continue;
    }
}

// Attach to transaction:
using (Transaction tx = new Transaction(doc, "Safe Operation"))
{
    tx.Start();
    FailureHandlingOptions opts = tx.GetFailureHandlingOptions();
    opts.SetFailuresPreprocessor(new SuppressWarningsPreprocessor());
    tx.SetFailureHandlingOptions(opts);

    // ... do work ...
    tx.Commit();
}""",
        ))

        # RollBack on exception
        samples.append(_s(
            "Roll back a transaction when an exception is caught to leave the model unmodified",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Risky Operation"))
{
    tx.Start();
    try
    {
        PerformRiskyWork(doc);
        tx.Commit();
    }
    catch (Exception ex)
    {
        if (tx.HasStarted())
            tx.RollBack();

        Autodesk.Revit.UI.TaskDialog.Show("Error",
            $"Operation failed:\\n{ex.Message}");
    }
}""",
        ))

        # FailuresAccessor in IFailuresPostprocessor
        samples.append(_s(
            "Implement IFailuresPostprocessor to log all failures after a transaction commits",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.IO;

public class FailureLogger : IFailuresPostprocessor
{
    private readonly string _logPath;
    public FailureLogger(string logPath) => _logPath = logPath;

    public FailureProcessingResult ProcessFailures(FailuresAccessor a)
    {
        IList<FailureMessageAccessor> msgs = a.GetFailureMessages();
        using StreamWriter sw = File.AppendText(_logPath);

        foreach (FailureMessageAccessor fma in msgs)
        {
            sw.WriteLine($"[{fma.GetSeverity()}] {fma.GetDescriptionText()}");
        }

        return FailureProcessingResult.Continue;
    }
}

// Attach:
FailureHandlingOptions opts = tx.GetFailureHandlingOptions();
opts.SetFailuresPostprocessor(new FailureLogger(@"C:\\Logs\\revit_failures.log"));
tx.SetFailureHandlingOptions(opts);""",
        ))

        # Catch Revit-specific exceptions
        samples.append(_s(
            "Catch Revit-specific exceptions (InvalidOperationException, ArgumentException) in a command",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.Exceptions;

try
{
    using (Transaction tx = new Transaction(doc, "Operation"))
    {
        tx.Start();
        DoWork(doc);
        tx.Commit();
    }
}
catch (Autodesk.Revit.Exceptions.InvalidOperationException ex)
{
    // Revit API state was invalid (e.g., wrong document context)
    Logger.Error($"Invalid operation: {ex.Message}");
}
catch (Autodesk.Revit.Exceptions.ArgumentException ex)
{
    // Bad argument passed to Revit API
    Logger.Error($"Argument error: {ex.Message}");
}
catch (Autodesk.Revit.Exceptions.OperationCanceledException)
{
    // User cancelled - not an error
}
catch (Exception ex)
{
    // Unexpected exception
    Logger.Error($"Unexpected: {ex}");
    throw;
}""",
        ))

        # PostFailure
        samples.append(_s(
            "Post a custom failure message during a transaction using FailureDefinition",
            """\
using Autodesk.Revit.DB;

// Define the failure once (e.g., in a static initializer):
public static class MyFailures
{
    public static readonly FailureDefinitionId InvalidGeometry =
        new FailureDefinitionId(new Guid("a1b2c3d4-e5f6-7890-abcd-ef1234567890"));

    static MyFailures()
    {
        FailureDefinition def = FailureDefinition.CreateFailureDefinition(
            InvalidGeometry,
            FailureSeverity.Warning,
            "The geometry created is invalid and may cause issues.");
    }
}

// Post during transaction:
using (Transaction tx = new Transaction(doc, "Geometry Check"))
{
    tx.Start();
    // ... create geometry ...
    if (GeometryIsInvalid())
    {
        FailureMessage msg = new FailureMessage(MyFailures.InvalidGeometry);
        doc.PostFailure(msg);
    }
    tx.Commit();
}""",
        ))

        # Null-check pattern
        samples.append(_s(
            "Apply defensive null-checking when accessing Revit API objects",
            """\
using Autodesk.Revit.DB;

// Defensive pattern: always null-check Revit API objects
Element elem = doc?.GetElement(elementId);
if (elem == null) return Result.Failed;

Parameter param = elem.LookupParameter("MyParam");
if (param == null || !param.HasValue) return Result.Failed;

double value = param.AsDouble();
if (value <= 0)
{
    message = "Parameter value must be positive.";
    return Result.Failed;
}

// Proceed safely
return Result.Succeeded;""",
        ))

        # Transaction status check
        samples.append(_s(
            "Check TransactionStatus before committing to ensure the transaction is still active",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Checked Commit"))
{
    tx.Start();

    try
    {
        DoWork(doc);

        if (tx.GetStatus() == TransactionStatus.Started)
            tx.Commit();
        else
            tx.RollBack();
    }
    catch
    {
        if (tx.GetStatus() == TransactionStatus.Started)
            tx.RollBack();
        throw;
    }
}""",
        ))

        # FailureHandlingOptions ClearAfterRollback
        samples.append(_s(
            "Configure FailureHandlingOptions to clear failure messages after a rollback",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "With Failure Options"))
{
    tx.Start();

    FailureHandlingOptions opts = tx.GetFailureHandlingOptions();
    opts.SetClearAfterRollback(true);
    opts.SetDelayedMiniWarnings(false);
    tx.SetFailureHandlingOptions(opts);

    // ... do work ...
    tx.Commit();
}""",
        ))

        # Validate element before access
        samples.append(_s(
            "Validate that an ElementId is valid and the element exists before accessing it",
            """\
using Autodesk.Revit.DB;

bool IsValidElement(Document doc, ElementId id)
{
    if (id == null || id == ElementId.InvalidElementId)
        return false;

    Element elem = doc.GetElement(id);
    return elem != null && !elem.IsValidObject;
}

// Usage:
if (!IsValidElement(doc, suspectId))
{
    message = $"Element {suspectId.IntegerValue} no longer exists.";
    return Result.Failed;
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # 11. Units and Conversion (~15 samples)
    # ------------------------------------------------------------------

    def _units_and_conversion(self) -> List[SAMPLE]:
        samples = []

        # mm to feet
        samples.append(_s(
            "Convert a length in millimeters to Revit internal feet for use in the API",
            """\
// Revit internal length unit: feet (1 foot = 304.8 mm)
double mm = 2400.0;
double feet = mm / 304.8;   // = 7.874016 ft

// Alternatively using UnitUtils (Revit 2022+):
// double feet = UnitUtils.ConvertToInternalUnits(mm, UnitTypeId.Millimeters);""",
        ))

        # feet to mm
        samples.append(_s(
            "Convert a Revit internal feet value to millimeters for display",
            """\
double internalFeet = 7.874016;
double mm = internalFeet * 304.8; // = 2400.0 mm

// Using UnitUtils:
// double mm = UnitUtils.ConvertFromInternalUnits(internalFeet, UnitTypeId.Millimeters);""",
        ))

        # UnitUtils ConvertToInternalUnits
        samples.append(_s(
            "Use UnitUtils.ConvertToInternalUnits to convert 500mm to Revit internal feet",
            """\
using Autodesk.Revit.DB;

// Revit 2022+ API
double mm = 500.0;
double internalFt = UnitUtils.ConvertToInternalUnits(mm, UnitTypeId.Millimeters);
// internalFt == 500 / 304.8 == 1.640420 ft""",
        ))

        # UnitUtils ConvertFromInternalUnits
        samples.append(_s(
            "Use UnitUtils.ConvertFromInternalUnits to display a Revit length in meters",
            """\
using Autodesk.Revit.DB;

double internalFt = 9.84252; // 3000mm
double meters = UnitUtils.ConvertFromInternalUnits(internalFt, UnitTypeId.Meters);
// meters == 3.0""",
        ))

        # Degrees to radians
        samples.append(_s(
            "Convert degrees to radians for Revit rotation API calls",
            """\
using System;

// Revit rotation parameters are always in radians
double degrees = 45.0;
double radians = degrees * Math.PI / 180.0; // = 0.785398 rad

// To convert back:
double backToDegrees = radians * 180.0 / Math.PI;""",
        ))

        # Area conversion
        samples.append(_s(
            "Convert a Revit area value (internal sq ft) to square meters",
            """\
using Autodesk.Revit.DB;

double areaFt2 = 107.6391; // internal sq ft

// Manual: 1 ft^2 = 0.092903 m^2
double areaM2 = areaFt2 * 0.092903;

// Using UnitUtils:
double areaM2_api = UnitUtils.ConvertFromInternalUnits(areaFt2, UnitTypeId.SquareMeters);""",
        ))

        # Volume conversion
        samples.append(_s(
            "Convert a Revit volume value (internal cubic feet) to cubic meters",
            """\
using Autodesk.Revit.DB;

double volFt3 = 35.3147; // internal cubic ft

// Manual: 1 ft^3 = 0.028317 m^3
double volM3 = volFt3 * 0.028317;

// Using UnitUtils:
double volM3_api = UnitUtils.ConvertFromInternalUnits(volFt3, UnitTypeId.CubicMeters);""",
        ))

        # Document display units
        samples.append(_s(
            "Read the document's current length display unit setting",
            """\
using Autodesk.Revit.DB;

Units docUnits   = doc.GetUnits();
FormatOptions fo = docUnits.GetFormatOptions(SpecTypeId.Length);
ForgeTypeId displayUnit = fo.GetUnitTypeId();

// Check if the document is using millimeters
bool isMm = displayUnit == UnitTypeId.Millimeters;
bool isFt = displayUnit == UnitTypeId.Feet;""",
        ))

        # Set document display units
        samples.append(_s(
            "Set the document's length display unit to millimeters",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Set Display Units"))
{
    tx.Start();

    Units units = doc.GetUnits();
    FormatOptions fo = new FormatOptions(UnitTypeId.Millimeters);
    fo.Accuracy = 1.0; // round to 1 mm
    units.SetFormatOptions(SpecTypeId.Length, fo);
    doc.SetUnits(units);

    tx.Commit();
}""",
        ))

        # AsValueString with units
        samples.append(_s(
            "Format a length in feet as a display string respecting document units using FormatValueString",
            """\
using Autodesk.Revit.DB;

double internalFt = 9.84252; // 3000mm

// Use the document's unit formatting
string displayStr = UnitFormatUtils.Format(
    doc.GetUnits(),
    SpecTypeId.Length,
    internalFt,
    false); // false = use document accuracy

// Result depends on document units: "3000 mm" or "9' 10 1/8\"""",
        ))

        # Parameter set with unit conversion
        samples.append(_s(
            "Set a length parameter to 1500mm by first converting to internal feet",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Set Length Param"))
{
    tx.Start();

    Element elem  = doc.GetElement(elementId);
    Parameter p   = elem?.LookupParameter("Shelf Height");

    if (p != null && p.StorageType == StorageType.Double && !p.IsReadOnly)
    {
        double mm = 1500.0;
        double ft = UnitUtils.ConvertToInternalUnits(mm, UnitTypeId.Millimeters);
        p.Set(ft);
    }

    tx.Commit();
}""",
        ))

        # Angular parameter
        samples.append(_s(
            "Set an angular parameter (slope) to 30 degrees by converting to radians",
            """\
using Autodesk.Revit.DB;
using System;

using (Transaction tx = new Transaction(doc, "Set Slope Angle"))
{
    tx.Start();

    Element elem   = doc.GetElement(elementId);
    Parameter angle = elem?.LookupParameter("Slope Angle");

    if (angle != null && angle.StorageType == StorageType.Double && !angle.IsReadOnly)
    {
        double degrees = 30.0;
        double radians = UnitUtils.ConvertToInternalUnits(degrees, UnitTypeId.Degrees);
        angle.Set(radians);
    }

    tx.Commit();
}""",
        ))

        # Pipe/Duct diameter with unit check
        samples.append(_s(
            "Read a pipe diameter in mm from its parameter accounting for internal feet conversion",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;

Pipe pipe = doc.GetElement(pipeId) as Pipe;
if (pipe != null)
{
    Parameter diaParam = pipe.get_Parameter(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM);
    if (diaParam != null)
    {
        double diaFt = diaParam.AsDouble();
        double diaMm = UnitUtils.ConvertFromInternalUnits(diaFt, UnitTypeId.Millimeters);
        // e.g. 0.328084 ft -> 100 mm pipe
    }
}""",
        ))

        # UnitUtils.IsValidUnit
        samples.append(_s(
            "Check if a ForgeTypeId represents a valid unit type before applying it",
            """\
using Autodesk.Revit.DB;

ForgeTypeId candidateUnit = UnitTypeId.Millimeters;

bool isValid = UnitUtils.IsValidUnit(SpecTypeId.Length, candidateUnit);
if (isValid)
{
    FormatOptions fo = new FormatOptions(candidateUnit);
    // Apply fo to document units...
}""",
        ))

        # Convert slope percent to radians
        samples.append(_s(
            "Convert a roof slope expressed as a percentage to radians for a Revit parameter",
            """\
using System;

// Slope: rise over run * 100 = percent
// e.g. 12% slope = atan(0.12) radians
double slopePercent = 12.0;
double slopeRatio   = slopePercent / 100.0;     // 0.12
double slopeRadians = Math.Atan(slopeRatio);     // ~0.1194 rad
double slopeDegrees = slopeRadians * 180.0 / Math.PI; // ~6.84 degrees

// Set on Revit roof slope parameter:
// slopeParam.Set(slopeRadians);""",
        ))

        return samples
