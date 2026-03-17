"""
RevitAPIReferenceGenerator: Q&A pairs, method examples, namespace reference, error handling.
Produces ~200 Alpaca training pairs.
"""
from typing import Dict, List

SAMPLE = Dict[str, str]


def _s(instruction: str, output: str) -> SAMPLE:
    return {"instruction": instruction, "input": "", "output": output}


class RevitAPIReferenceGenerator:
    """Generates Q&A and code-example training samples covering the Revit API."""

    def generate(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []
        samples.extend(self._api_qa_pairs())
        samples.extend(self._method_examples())
        samples.extend(self._namespace_reference())
        samples.extend(self._error_handling())
        samples.extend(self._common_patterns())
        samples.extend(self._unit_conversion())
        return samples

    # ------------------------------------------------------------------
    # Q&A pairs
    # ------------------------------------------------------------------
    def _api_qa_pairs(self) -> List[SAMPLE]:
        pairs = [
            (
                "What is the difference between a Document and a FamilyDocument in Revit API?",
                "A `Document` represents any open Revit project or family file. "
                "A `FamilyDocument` is a `Document` whose `IsFamilyDocument` property returns `true`. "
                "Only a `FamilyDocument` exposes the `FamilyManager` property, which lets you create and "
                "edit family types and parameters.\n\n"
                "// Check if a document is a family document:\n"
                "bool isFam = doc.IsFamilyDocument;\n"
                "FamilyManager famMgr = doc.FamilyManager; // only valid when IsFamilyDocument == true",
            ),
            (
                "How do you open a family file for editing in the Revit API?",
                "Use `Application.OpenDocumentFile` with the path to the `.rfa` file:\n\n"
                "```csharp\n"
                "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\to\\\\MyFamily.rfa\");\n"
                "FamilyManager famMgr = famDoc.FamilyManager;\n"
                "```\n\n"
                "After editing, save with `famDoc.Save()` or `famDoc.SaveAs()` and close with `famDoc.Close(false)`.",
            ),
            (
                "What is a Transaction in the Revit API and when is it required?",
                "A `Transaction` is required whenever you modify the Revit document model (geometry, parameters, elements). "
                "Read-only operations do NOT need a transaction.\n\n"
                "```csharp\n"
                "using (Transaction tx = new Transaction(doc, \"My Operation\")) {\n"
                "    tx.Start();\n"
                "    // ... document modifications ...\n"
                "    tx.Commit();\n"
                "}\n"
                "```\n\n"
                "Transactions cannot be nested. Use `SubTransaction` or `TransactionGroup` for grouping.",
            ),
            (
                "How do you access FamilyManager parameters without a Transaction?",
                "`FamilyManager` operations such as `AddParameter`, `Set`, `SetFormula`, and `NewType` "
                "are handled internally by the API and do NOT require you to open a `Transaction`. "
                "Wrapping them in a `Transaction` will throw an exception.\n\n"
                "```csharp\n"
                "// Correct - no Transaction needed:\n"
                "FamilyParameter fp = famMgr.AddParameter(\n"
                "    \"Width\", BuiltInParameterGroup.PG_GEOMETRY,\n"
                "    ParameterType.Length, true);\n"
                "famMgr.Set(fp, 1.0); // 1 foot\n"
                "```",
            ),
            (
                "What is the unit system used internally by the Revit API?",
                "The Revit API uses **decimal feet** for all length values, regardless of the project's "
                "display unit setting. Always convert before passing values:\n\n"
                "```csharp\n"
                "double MM_TO_FT = 1.0 / 304.8;\n"
                "double widthFt = 900 * MM_TO_FT; // 900 mm -> feet\n"
                "double inchToFt = 1.0 / 12.0;\n"
                "double doorWidthFt = 36 * inchToFt; // 36 inches -> feet\n"
                "```",
            ),
            (
                "How do you retrieve all elements of a specific category in a Revit document?",
                "Use `FilteredElementCollector` with `OfCategory` or `OfClass`:\n\n"
                "```csharp\n"
                "// All walls:\n"
                "var walls = new FilteredElementCollector(doc)\n"
                "    .OfCategory(BuiltInCategory.OST_Walls)\n"
                "    .OfClass(typeof(Wall))\n"
                "    .Cast<Wall>()\n"
                "    .ToList();\n\n"
                "// All family instances:\n"
                "var instances = new FilteredElementCollector(doc)\n"
                "    .OfClass(typeof(FamilyInstance))\n"
                "    .Cast<FamilyInstance>()\n"
                "    .ToList();\n"
                "```",
            ),
            (
                "What is the difference between BuiltInParameter and FamilyParameter?",
                "`BuiltInParameter` values (e.g., `BuiltInParameter.DOOR_HEIGHT`) are system-defined "
                "parameters that Revit attaches to specific element types. They cannot be deleted.\n\n"
                "`FamilyParameter` objects are created by the family author via `FamilyManager.AddParameter`. "
                "They are specific to that family and can be instance or type parameters.\n\n"
                "```csharp\n"
                "// Reading a built-in parameter:\n"
                "double h = elem.get_Parameter(BuiltInParameter.DOOR_HEIGHT).AsDouble();\n\n"
                "// Reading a family parameter:\n"
                "Parameter p = elem.LookupParameter(\"MyCustomParam\");\n"
                "double v = p.AsDouble();\n"
                "```",
            ),
            (
                "How do you load a family into a Revit project?",
                "Use `Document.LoadFamily` to load from a file path:\n\n"
                "```csharp\n"
                "using (Transaction tx = new Transaction(doc, \"Load Family\")) {\n"
                "    tx.Start();\n"
                "    Family loadedFamily;\n"
                "    bool success = doc.LoadFamily(\n"
                "        @\"C:\\\\path\\\\to\\\\MyFamily.rfa\", out loadedFamily);\n"
                "    tx.Commit();\n"
                "}\n"
                "```\n\n"
                "If the family is already loaded, `LoadFamily` returns `false` but does not throw. "
                "Use `IFamilyLoadOptions` to control overwrite behavior.",
            ),
            (
                "How do you place a family instance in a Revit project?",
                "Use `Document.NewFamilyInstance` (or the `FamilyInstanceCreationData` approach for batch):\n\n"
                "```csharp\n"
                "using (Transaction tx = new Transaction(doc, \"Place Family\")) {\n"
                "    tx.Start();\n"
                "    XYZ location = new XYZ(0, 0, 0);\n"
                "    FamilySymbol symbol = // obtain from loaded family\n"
                "    if (!symbol.IsActive) symbol.Activate();\n"
                "    FamilyInstance inst = doc.NewFamilyInstance(\n"
                "        location, symbol, StructuralType.NonStructural);\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
            (
                "What is the purpose of FamilySymbol.Activate() in the Revit API?",
                "In Revit 2015+, a `FamilySymbol` (type) must be activated before it can be placed. "
                "An inactive symbol has no geometry cached and cannot be instantiated. "
                "Calling `Activate()` forces the geometry to be generated.\n\n"
                "```csharp\n"
                "if (!symbol.IsActive) {\n"
                "    symbol.Activate();\n"
                "    doc.Regenerate(); // optional but recommended\n"
                "}\n"
                "FamilyInstance inst = doc.NewFamilyInstance(pt, symbol, StructuralType.NonStructural);\n"
                "```",
            ),
            (
                "How do you create a new family type programmatically?",
                "Use `FamilyManager.NewType` on an open family document. No Transaction needed.\n\n"
                "```csharp\n"
                "Document famDoc = app.OpenDocumentFile(path);\n"
                "FamilyManager famMgr = famDoc.FamilyManager;\n"
                "FamilyType newType = famMgr.NewType(\"900x2100\");\n"
                "famMgr.CurrentType = newType;\n"
                "FamilyParameter width = famMgr.get_Parameter(\"Width\");\n"
                "famMgr.Set(width, 900 * (1.0 / 304.8));\n"
                "FamilyParameter height = famMgr.get_Parameter(\"Height\");\n"
                "famMgr.Set(height, 2100 * (1.0 / 304.8));\n"
                "famDoc.Save();\n"
                "```",
            ),
            (
                "How do you iterate over all family types in a family document?",
                "Use `FamilyManager.Types` property:\n\n"
                "```csharp\n"
                "Document famDoc = app.OpenDocumentFile(path);\n"
                "FamilyManager famMgr = famDoc.FamilyManager;\n"
                "FamilyTypeSet types = famMgr.Types;\n"
                "foreach (FamilyType ft in types) {\n"
                "    Console.WriteLine(ft.Name);\n"
                "    famMgr.CurrentType = ft;\n"
                "    FamilyParameter wp = famMgr.get_Parameter(\"Width\");\n"
                "    if (wp != null) {\n"
                "        double w = famMgr.CurrentType.AsDouble(wp) ?? 0;\n"
                "        Console.WriteLine($\"  Width: {w * 304.8:F0} mm\");\n"
                "    }\n"
                "}\n"
                "```",
            ),
            (
                "What is the XYZ class in the Revit API?",
                "`XYZ` is an immutable 3D point/vector class. All coordinates are in **decimal feet**.\n\n"
                "```csharp\n"
                "XYZ origin = XYZ.Zero;        // (0, 0, 0)\n"
                "XYZ pt = new XYZ(1.0, 2.0, 0); // 1ft, 2ft, 0ft\n"
                "XYZ unitX = XYZ.BasisX;        // (1, 0, 0)\n"
                "double dist = pt.DistanceTo(origin); // Euclidean distance in feet\n"
                "XYZ norm = pt.Normalize();     // unit vector\n"
                "XYZ sum = pt.Add(new XYZ(0.5, 0, 0));\n"
                "```",
            ),
            (
                "How do you create a reference plane in a family document?",
                "Use `FamilyDocument` (as a `Document`) with `NewReferencePlane2`:\n\n"
                "```csharp\n"
                "using (Transaction tx = new Transaction(famDoc, \"Add Ref Plane\")) {\n"
                "    tx.Start();\n"
                "    XYZ bubbleEnd = new XYZ(0, 2, 0);\n"
                "    XYZ freeEnd  = new XYZ(0, -2, 0);\n"
                "    XYZ cutVec   = new XYZ(1, 0, 0);\n"
                "    View view    = // active plan view\n"
                "    ReferencePlane rp = famDoc.NewReferencePlane2(\n"
                "        bubbleEnd, freeEnd, cutVec, view);\n"
                "    rp.Name = \"WidthRef\";\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
            (
                "How do you add a formula to a family parameter?",
                "Use `FamilyManager.SetFormula`. No Transaction needed:\n\n"
                "```csharp\n"
                "FamilyParameter depth = famMgr.get_Parameter(\"Depth\");\n"
                "FamilyParameter width = famMgr.get_Parameter(\"Width\");\n"
                "// Set Depth = Width / 2:\n"
                "famMgr.SetFormula(depth, \"Width / 2\");\n\n"
                "// Clear a formula:\n"
                "famMgr.SetFormula(depth, null);\n"
                "```",
            ),
            (
                "What is an ElementId and how do you use it?",
                "`ElementId` is a wrapper around an integer that uniquely identifies an element in a document. "
                "It is used to retrieve elements and to reference them.\n\n"
                "```csharp\n"
                "// Get element by ID:\n"
                "ElementId id = new ElementId(12345);\n"
                "Element elem = doc.GetElement(id);\n\n"
                "// Elements expose their own ID:\n"
                "ElementId wallId = wall.Id;\n\n"
                "// Built-in categories also use ElementId:\n"
                "ElementId catId = new ElementId(BuiltInCategory.OST_Doors);\n"
                "```",
            ),
            (
                "How do you delete an element in Revit API?",
                "Use `Document.Delete(ElementId)` inside a `Transaction`:\n\n"
                "```csharp\n"
                "using (Transaction tx = new Transaction(doc, \"Delete Element\")) {\n"
                "    tx.Start();\n"
                "    ICollection<ElementId> deleted = doc.Delete(elem.Id);\n"
                "    // deleted contains IDs of all elements removed (cascading)\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
            (
                "What is the difference between Instance and Type parameters in Revit families?",
                "**Type parameters** are shared by all instances of a family type. Changing one updates all placements.\n"
                "**Instance parameters** are per-placement; each instance can have a different value.\n\n"
                "In the API:\n"
                "```csharp\n"
                "// isInstance = true  -> instance parameter\n"
                "// isInstance = false -> type parameter\n"
                "FamilyParameter fp = famMgr.AddParameter(\n"
                "    \"Depth\",\n"
                "    BuiltInParameterGroup.PG_GEOMETRY,\n"
                "    ParameterType.Length,\n"
                "    isInstance: true);  // instance\n"
                "```",
            ),
            (
                "How do you read a parameter value from a FamilyInstance at runtime?",
                "Use `Element.get_Parameter(BuiltInParameter)` or `LookupParameter(name)`:\n\n"
                "```csharp\n"
                "FamilyInstance door = // obtained from collector\n\n"
                "// Built-in parameter:\n"
                "double height = door.get_Parameter(BuiltInParameter.DOOR_HEIGHT).AsDouble();\n\n"
                "// Custom parameter by name:\n"
                "Parameter fireRating = door.LookupParameter(\"FireRating\");\n"
                "string rating = fireRating?.AsString() ?? \"None\";\n"
                "```",
            ),
            (
                "How do you use FilteredElementCollector with multiple filters?",
                "Chain filters to narrow results. `WhereElementIsNotElementType()` is commonly needed:\n\n"
                "```csharp\n"
                "// Doors that are instances (not types) on Level 1:\n"
                "Level level1 = // get level\n"
                "var doors = new FilteredElementCollector(doc)\n"
                "    .OfCategory(BuiltInCategory.OST_Doors)\n"
                "    .WhereElementIsNotElementType()\n"
                "    .Cast<FamilyInstance>()\n"
                "    .Where(d => d.LevelId == level1.Id)\n"
                "    .ToList();\n"
                "```",
            ),
        ]
        return [_s(q, a) for q, a in pairs]

    # ------------------------------------------------------------------
    # Method examples
    # ------------------------------------------------------------------
    def _method_examples(self) -> List[SAMPLE]:
        examples = [
            (
                "Show a complete example of NewExtrusion in a Revit family document.",
                "```csharp\n"
                "double MM_TO_FT = 1.0 / 304.8;\n"
                "using (Transaction tx = new Transaction(famDoc, \"Extrusion\")) {\n"
                "    tx.Start();\n"
                "    SketchPlane sketchPlane = SketchPlane.Create(famDoc,\n"
                "        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));\n"
                "    CurveArrArray profile = new CurveArrArray();\n"
                "    CurveArray loop = new CurveArray();\n"
                "    double w = 300 * MM_TO_FT;\n"
                "    double h = 200 * MM_TO_FT;\n"
                "    loop.Append(Line.CreateBound(new XYZ(-w/2, -h/2, 0), new XYZ( w/2, -h/2, 0)));\n"
                "    loop.Append(Line.CreateBound(new XYZ( w/2, -h/2, 0), new XYZ( w/2,  h/2, 0)));\n"
                "    loop.Append(Line.CreateBound(new XYZ( w/2,  h/2, 0), new XYZ(-w/2,  h/2, 0)));\n"
                "    loop.Append(Line.CreateBound(new XYZ(-w/2,  h/2, 0), new XYZ(-w/2, -h/2, 0)));\n"
                "    profile.Append(loop);\n"
                "    double depth = 150 * MM_TO_FT;\n"
                "    Extrusion ext = famDoc.FamilyCreate.NewExtrusion(true, profile, sketchPlane, depth);\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
            (
                "Show a complete example of NewRevolution in a Revit family document.",
                "```csharp\n"
                "double MM_TO_FT = 1.0 / 304.8;\n"
                "using (Transaction tx = new Transaction(famDoc, \"Revolution\")) {\n"
                "    tx.Start();\n"
                "    Plane axisPlane = Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero);\n"
                "    SketchPlane sp = SketchPlane.Create(famDoc, axisPlane);\n"
                "    CurveArrArray profile = new CurveArrArray();\n"
                "    CurveArray loop = new CurveArray();\n"
                "    double r = 50 * MM_TO_FT;\n"
                "    double h = 100 * MM_TO_FT;\n"
                "    loop.Append(Line.CreateBound(new XYZ(r,     0, 0), new XYZ(r,     0, h)));\n"
                "    loop.Append(Line.CreateBound(new XYZ(r,     0, h), new XYZ(r+10*MM_TO_FT, 0, h)));\n"
                "    loop.Append(Line.CreateBound(new XYZ(r+10*MM_TO_FT, 0, h), new XYZ(r+10*MM_TO_FT, 0, 0)));\n"
                "    loop.Append(Line.CreateBound(new XYZ(r+10*MM_TO_FT, 0, 0), new XYZ(r, 0, 0)));\n"
                "    profile.Append(loop);\n"
                "    Line axis = Line.CreateBound(XYZ.Zero, XYZ.BasisZ);\n"
                "    Revolution rev = famDoc.FamilyCreate.NewRevolution(true, profile, sp, axis, 0, 2*Math.PI);\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
            (
                "Show a complete example of NewSweep in a Revit family document.",
                "```csharp\n"
                "double MM_TO_FT = 1.0 / 304.8;\n"
                "using (Transaction tx = new Transaction(famDoc, \"Sweep\")) {\n"
                "    tx.Start();\n"
                "    // Path curve\n"
                "    CurveArray path = new CurveArray();\n"
                "    double pathLen = 1000 * MM_TO_FT;\n"
                "    path.Append(Line.CreateBound(XYZ.Zero, new XYZ(pathLen, 0, 0)));\n"
                "    SweepProfile profile = famDoc.Application.Create.NewCurveLoopsProfile(\n"
                "        GetRectProfile(60 * MM_TO_FT, 40 * MM_TO_FT));\n"
                "    Sweep sweep = famDoc.FamilyCreate.NewSweep(\n"
                "        true, path, profile, 0, ProfilePlaneLocation.Start);\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
            (
                "Show a complete example of NewBlend in a Revit family document.",
                "```csharp\n"
                "double MM_TO_FT = 1.0 / 304.8;\n"
                "using (Transaction tx = new Transaction(famDoc, \"Blend\")) {\n"
                "    tx.Start();\n"
                "    SketchPlane bottomPlane = SketchPlane.Create(famDoc,\n"
                "        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));\n"
                "    // Bottom profile: 400x300 rectangle\n"
                "    CurveArray bottom = new CurveArray();\n"
                "    double bw = 400 * MM_TO_FT, bd = 300 * MM_TO_FT;\n"
                "    bottom.Append(Line.CreateBound(new XYZ(-bw/2,-bd/2,0), new XYZ(bw/2,-bd/2,0)));\n"
                "    bottom.Append(Line.CreateBound(new XYZ(bw/2,-bd/2,0), new XYZ(bw/2,bd/2,0)));\n"
                "    bottom.Append(Line.CreateBound(new XYZ(bw/2,bd/2,0), new XYZ(-bw/2,bd/2,0)));\n"
                "    bottom.Append(Line.CreateBound(new XYZ(-bw/2,bd/2,0), new XYZ(-bw/2,-bd/2,0)));\n"
                "    // Top profile: 200x200 square at height 300mm\n"
                "    CurveArray top = new CurveArray();\n"
                "    double tw = 200 * MM_TO_FT;\n"
                "    double th = 300 * MM_TO_FT;\n"
                "    top.Append(Line.CreateBound(new XYZ(-tw/2,-tw/2,th), new XYZ(tw/2,-tw/2,th)));\n"
                "    top.Append(Line.CreateBound(new XYZ(tw/2,-tw/2,th), new XYZ(tw/2,tw/2,th)));\n"
                "    top.Append(Line.CreateBound(new XYZ(tw/2,tw/2,th), new XYZ(-tw/2,tw/2,th)));\n"
                "    top.Append(Line.CreateBound(new XYZ(-tw/2,tw/2,th), new XYZ(-tw/2,-tw/2,th)));\n"
                "    Blend blend = famDoc.FamilyCreate.NewBlend(true, top, bottom, bottomPlane);\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
            (
                "Show how to add a shared parameter from a shared parameter file in Revit API.",
                "```csharp\n"
                "// Open or create shared parameter file:\n"
                "app.SharedParametersFilename = @\"C:\\\\SharedParams.txt\";\n"
                "DefinitionFile defFile = app.OpenSharedParameterFile();\n"
                "DefinitionGroup group = defFile.Groups.get_Item(\"MyGroup\")\n"
                "    ?? defFile.Groups.Create(\"MyGroup\");\n"
                "ExternalDefinition extDef = group.Definitions.get_Item(\"FireRating\")\n"
                "    as ExternalDefinition;\n"
                "if (extDef == null) {\n"
                "    ExternalDefinitionCreationOptions opts =\n"
                "        new ExternalDefinitionCreationOptions(\"FireRating\", SpecTypeId.String.Text);\n"
                "    extDef = group.Definitions.Create(opts) as ExternalDefinition;\n"
                "}\n"
                "// Bind to category:\n"
                "using (Transaction tx = new Transaction(doc, \"Add Shared Param\")) {\n"
                "    tx.Start();\n"
                "    CategorySet cats = app.Create.NewCategorySet();\n"
                "    cats.Insert(doc.Settings.Categories.get_Item(BuiltInCategory.OST_Walls));\n"
                "    Binding binding = app.Create.NewInstanceBinding(cats);\n"
                "    doc.ParameterBindings.Insert(extDef, binding, BuiltInParameterGroup.PG_DATA);\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
            (
                "How do you move an element using the Revit API?",
                "Use `ElementTransformUtils.MoveElement` inside a `Transaction`:\n\n"
                "```csharp\n"
                "double MM_TO_FT = 1.0 / 304.8;\n"
                "using (Transaction tx = new Transaction(doc, \"Move Element\")) {\n"
                "    tx.Start();\n"
                "    XYZ delta = new XYZ(500 * MM_TO_FT, 0, 0); // move 500mm in X\n"
                "    ElementTransformUtils.MoveElement(doc, elem.Id, delta);\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
            (
                "How do you rotate an element in Revit API?",
                "Use `ElementTransformUtils.RotateElement` with an axis line and angle in radians:\n\n"
                "```csharp\n"
                "using (Transaction tx = new Transaction(doc, \"Rotate Element\")) {\n"
                "    tx.Start();\n"
                "    Line axis = Line.CreateBound(\n"
                "        new XYZ(0, 0, 0), new XYZ(0, 0, 1)); // Z axis at origin\n"
                "    double angle = Math.PI / 4; // 45 degrees\n"
                "    ElementTransformUtils.RotateElement(doc, elem.Id, axis, angle);\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
            (
                "How do you copy an element in Revit API?",
                "Use `ElementTransformUtils.CopyElement` inside a `Transaction`:\n\n"
                "```csharp\n"
                "double MM_TO_FT = 1.0 / 304.8;\n"
                "using (Transaction tx = new Transaction(doc, \"Copy Element\")) {\n"
                "    tx.Start();\n"
                "    XYZ delta = new XYZ(1000 * MM_TO_FT, 0, 0);\n"
                "    ICollection<ElementId> copies = ElementTransformUtils.CopyElement(\n"
                "        doc, elem.Id, delta);\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
            (
                "Show how to create a linear dimension in a family document.",
                "```csharp\n"
                "double MM_TO_FT = 1.0 / 304.8;\n"
                "using (Transaction tx = new Transaction(famDoc, \"Add Dimension\")) {\n"
                "    tx.Start();\n"
                "    // Get references to two reference planes:\n"
                "    ReferencePlane rp1 = // left reference plane\n"
                "    ReferencePlane rp2 = // right reference plane\n"
                "    ReferenceArray refs = new ReferenceArray();\n"
                "    refs.Append(rp1.GetReference());\n"
                "    refs.Append(rp2.GetReference());\n"
                "    Line dimLine = Line.CreateBound(\n"
                "        new XYZ(0, -200 * MM_TO_FT, 0),\n"
                "        new XYZ(0,  200 * MM_TO_FT, 0));\n"
                "    View view = // plan view\n"
                "    Dimension dim = famDoc.FamilyCreate.NewLinearDimension(\n"
                "        view, dimLine, refs);\n"
                "    // Label the dimension to drive a parameter:\n"
                "    FamilyParameter fp = famDoc.FamilyManager.get_Parameter(\"Width\");\n"
                "    dim.FamilyLabel = fp;\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
            (
                "How do you create a mirror of elements in Revit API?",
                "Use `ElementTransformUtils.MirrorElements` with a mirror plane:\n\n"
                "```csharp\n"
                "using (Transaction tx = new Transaction(famDoc, \"Mirror\")) {\n"
                "    tx.Start();\n"
                "    Plane mirrorPlane = Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero);\n"
                "    ICollection<ElementId> newIds = ElementTransformUtils.MirrorElements(\n"
                "        famDoc, new List<ElementId> { ext.Id }, mirrorPlane, true);\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
        ]
        return [_s(q, a) for q, a in examples]

    # ------------------------------------------------------------------
    # Namespace reference
    # ------------------------------------------------------------------
    def _namespace_reference(self) -> List[SAMPLE]:
        refs = [
            (
                "What are the main namespaces in the Revit API and what do they contain?",
                "Key Revit API namespaces:\n\n"
                "- `Autodesk.Revit.DB` -- Core: Document, Element, Transaction, FilteredElementCollector, "
                "XYZ, Line, Plane, BuiltInCategory, BuiltInParameter\n"
                "- `Autodesk.Revit.DB.Architecture` -- Stairs, Railing, Room\n"
                "- `Autodesk.Revit.DB.Structure` -- AnalyticalModel, Rebar, StructuralType\n"
                "- `Autodesk.Revit.DB.Mechanical` -- Duct, Space, Zone\n"
                "- `Autodesk.Revit.DB.Electrical` -- ElectricalSystem, CableTray\n"
                "- `Autodesk.Revit.DB.Plumbing` -- Pipe, FlexPipe\n"
                "- `Autodesk.Revit.UI` -- UIApplication, UIDocument, ExternalCommand, IExternalApplication\n"
                "- `Autodesk.Revit.UI.Events` -- DocumentOpenedEventArgs, ViewActivatedEventArgs\n"
                "- `Autodesk.Revit.ApplicationServices` -- Application, ControlledApplication\n"
                "- `Autodesk.Revit.Attributes` -- TransactionAttribute, RegenerationAttribute\n"
                "- `Autodesk.Revit.Exceptions` -- InvalidOperationException, ArgumentException\n\n"
                "Most add-in code uses: `using Autodesk.Revit.DB;` and `using Autodesk.Revit.UI;`",
            ),
            (
                "What classes are in Autodesk.Revit.DB for geometry creation?",
                "Geometry creation classes in `Autodesk.Revit.DB`:\n\n"
                "- `XYZ` -- 3D point/vector (immutable)\n"
                "- `Line` -- bounded or unbound line; `Line.CreateBound(p1, p2)`, `Line.CreateUnbound(origin, dir)`\n"
                "- `Arc` -- circular arc; `Arc.Create(center, radius, start, end, xAxis, yAxis)`\n"
                "- `Ellipse` -- elliptical curve\n"
                "- `NurbSpline` -- NURBS curve\n"
                "- `HermiteSpline` -- Hermite spline\n"
                "- `Plane` -- infinite plane; `Plane.CreateByNormalAndOrigin(normal, origin)`\n"
                "- `CurveArray` -- ordered list of curves (for profile loops)\n"
                "- `CurveArrArray` -- array of CurveArray (for multi-loop profiles)\n"
                "- `SketchPlane` -- a plane within the document; `SketchPlane.Create(doc, plane)`\n"
                "- `Transform` -- 4x4 transformation matrix\n"
                "- `BoundingBoxXYZ` -- axis-aligned bounding box",
            ),
            (
                "What ExternalCommand attributes are required in Revit API add-ins?",
                "Every `IExternalCommand` class requires these attributes:\n\n"
                "```csharp\n"
                "[Transaction(TransactionMode.Manual)]  // or Automatic/ReadOnly\n"
                "[Regeneration(RegenerationOption.Manual)]\n"
                "public class MyCommand : IExternalCommand {\n"
                "    public Result Execute(\n"
                "        ExternalCommandData commandData,\n"
                "        ref string message,\n"
                "        ElementSet elements) {\n"
                "        UIApplication uiApp = commandData.Application;\n"
                "        Document doc = uiApp.ActiveUIDocument.Document;\n"
                "        // ... implementation ...\n"
                "        return Result.Succeeded;\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "`TransactionMode.Manual` is almost always used (you control transactions yourself). "
                "`TransactionMode.Automatic` wraps the entire command in one transaction (rarely used).",
            ),
            (
                "What is FilteredElementCollector and what quick filters are available?",
                "`FilteredElementCollector` is the primary mechanism for querying elements. "
                "Quick filters (applied before slow filters for performance):\n\n"
                "- `OfClass(Type)` -- filter by .NET class\n"
                "- `OfCategory(BuiltInCategory)` -- filter by Revit category\n"
                "- `WhereElementIsElementType()` -- only types (symbols)\n"
                "- `WhereElementIsNotElementType()` -- only instances\n"
                "- `WherePasses(ElementFilter)` -- custom filter\n\n"
                "Slow filters (LINQ, applied after):\n"
                "- `.Where(e => e.Name.Contains(\"Door\"))`\n"
                "- `.Cast<Wall>().Where(w => w.Width > 0.5)`\n\n"
                "Always use quick filters first for best performance.",
            ),
            (
                "What are the ParameterType values used most often in Revit family parameters?",
                "Common `ParameterType` values for `FamilyManager.AddParameter`:\n\n"
                "- `ParameterType.Length` -- distance in feet internally\n"
                "- `ParameterType.Angle` -- angle in radians internally\n"
                "- `ParameterType.Area` -- area in square feet internally\n"
                "- `ParameterType.Volume` -- volume in cubic feet internally\n"
                "- `ParameterType.Integer` -- whole number\n"
                "- `ParameterType.Number` -- real number (dimensionless)\n"
                "- `ParameterType.Text` -- string value\n"
                "- `ParameterType.YesNo` -- boolean (1=Yes, 0=No)\n"
                "- `ParameterType.Material` -- material element ID\n"
                "- `ParameterType.FamilyType` -- links to another family type\n\n"
                "Note: In Revit 2022+, `ParameterType` was replaced by `ForgeTypeId`/`SpecTypeId`. "
                "Use `SpecTypeId.Length`, `SpecTypeId.Angle`, etc.",
            ),
            (
                "How do you use TransactionGroup in the Revit API?",
                "`TransactionGroup` lets you group multiple transactions so they can be undone as one:\n\n"
                "```csharp\n"
                "using (TransactionGroup tg = new TransactionGroup(doc, \"Group Name\")) {\n"
                "    tg.Start();\n"
                "    using (Transaction t1 = new Transaction(doc, \"Step 1\")) {\n"
                "        t1.Start();\n"
                "        // ... modifications ...\n"
                "        t1.Commit();\n"
                "    }\n"
                "    using (Transaction t2 = new Transaction(doc, \"Step 2\")) {\n"
                "        t2.Start();\n"
                "        // ... modifications ...\n"
                "        t2.Commit();\n"
                "    }\n"
                "    tg.Assimilate(); // merges into one undo step\n"
                "    // or tg.Commit() to keep as separate steps in undo\n"
                "    // or tg.RollBack() to undo all\n"
                "}\n"
                "```",
            ),
            (
                "What is SubTransaction and when should you use it?",
                "`SubTransaction` is a lightweight checkpoint inside an open `Transaction`. "
                "It lets you roll back a portion of work without rolling back the whole transaction:\n\n"
                "```csharp\n"
                "using (Transaction tx = new Transaction(doc, \"Outer\")) {\n"
                "    tx.Start();\n"
                "    // ... some work ...\n"
                "    using (SubTransaction sub = new SubTransaction(doc)) {\n"
                "        sub.Start();\n"
                "        // ... experimental work ...\n"
                "        if (errorCondition)\n"
                "            sub.RollBack(); // undo only the sub-transaction\n"
                "        else\n"
                "            sub.Commit();\n"
                "    }\n"
                "    tx.Commit();\n"
                "}\n"
                "```\n\n"
                "Sub-transactions cannot span multiple outer transactions.",
            ),
            (
                "How do you get the active view in Revit API?",
                "```csharp\n"
                "UIDocument uidoc = commandData.Application.ActiveUIDocument;\n"
                "View activeView = uidoc.ActiveView;\n\n"
                "// Or from document:\n"
                "View docActiveView = doc.ActiveView;\n\n"
                "// Check view type:\n"
                "if (activeView.ViewType == ViewType.FloorPlan) { /* ... */ }\n"
                "if (activeView is View3D v3d) { /* 3D view specific */ }\n"
                "if (activeView is ViewPlan plan) { /* plan view specific */ }\n"
                "```",
            ),
            (
                "What is the Revit API event model and how do you subscribe to events?",
                "Revit raises events through `UIApplication` and `ControlledApplication`. "
                "Subscribe in `IExternalApplication.OnStartup`:\n\n"
                "```csharp\n"
                "public class MyApp : IExternalApplication {\n"
                "    public Result OnStartup(UIControlledApplication app) {\n"
                "        app.ControlledApplication.DocumentOpened += OnDocOpened;\n"
                "        app.ControlledApplication.DocumentSaving += OnDocSaving;\n"
                "        return Result.Succeeded;\n"
                "    }\n"
                "    public Result OnShutdown(UIControlledApplication app) {\n"
                "        app.ControlledApplication.DocumentOpened -= OnDocOpened;\n"
                "        return Result.Succeeded;\n"
                "    }\n"
                "    private void OnDocOpened(object sender, DocumentOpenedEventArgs e) {\n"
                "        Document doc = e.Document;\n"
                "        // handle event (no Transaction here unless using EventModificationContext)\n"
                "    }\n"
                "}\n"
                "```",
            ),
            (
                "How do you use UpdaterFramework (IUpdater) in the Revit API?",
                "`IUpdater` lets you respond to element changes as they happen:\n\n"
                "```csharp\n"
                "public class WallUpdater : IUpdater {\n"
                "    static AddInId appId = new AddInId(new Guid(\"...\"));\n"
                "    static UpdaterId updaterId = new UpdaterId(appId, new Guid(\"...\"));\n"
                "    public void Execute(UpdaterData data) {\n"
                "        Document doc = data.GetDocument();\n"
                "        foreach (ElementId id in data.GetModifiedElementIds()) {\n"
                "            Wall w = doc.GetElement(id) as Wall;\n"
                "            // react to change\n"
                "        }\n"
                "    }\n"
                "    public string GetAdditionalInformation() => \"Wall monitor\";\n"
                "    public ChangePriority GetChangePriority() => ChangePriority.Annotations;\n"
                "    public UpdaterId GetUpdaterId() => updaterId;\n"
                "    public string GetUpdaterName() => \"WallUpdater\";\n"
                "}\n"
                "// Registration:\n"
                "UpdaterRegistry.RegisterUpdater(new WallUpdater());\n"
                "ElementClassFilter filter = new ElementClassFilter(typeof(Wall));\n"
                "UpdaterRegistry.AddTrigger(updaterId, filter, Element.GetChangeTypeGeometry());\n"
                "```",
            ),
        ]
        return [_s(q, a) for q, a in refs]

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------
    def _error_handling(self) -> List[SAMPLE]:
        errors = [
            (
                "What causes 'The document is not a family document' in Revit API?",
                "This error occurs when you try to access `doc.FamilyManager` on a project document "
                "(`.rvt` file) rather than a family document (`.rfa` file).\n\n"
                "**Fix:**\n"
                "```csharp\n"
                "if (!doc.IsFamilyDocument) {\n"
                "    TaskDialog.Show(\"Error\", \"This command requires an open family (.rfa) document.\");\n"
                "    return Result.Failed;\n"
                "}\n"
                "FamilyManager famMgr = doc.FamilyManager; // safe now\n"
                "```",
            ),
            (
                "What causes 'Starting a transaction from a non-API context' in Revit API?",
                "This error occurs when you try to start a `Transaction` outside the Revit API call stack "
                "(e.g., from a background thread, a WinForms event not properly dispatched, or after the "
                "command has returned).\n\n"
                "**Fix:** Ensure all document modifications happen synchronously within `IExternalCommand.Execute` "
                "or within an `IExternalEventHandler.Execute` callback:\n\n"
                "```csharp\n"
                "// Wrong: background thread\n"
                "Task.Run(() => {\n"
                "    using (Transaction tx = new Transaction(doc, \"X\")) { // THROWS\n"
                "        tx.Start();\n"
                "    }\n"
                "});\n\n"
                "// Correct: use ExternalEvent for modeless dialogs\n"
                "ExternalEvent exEvent = ExternalEvent.Create(new MyHandler());\n"
                "exEvent.Raise();\n"
                "```",
            ),
            (
                "What causes 'Cannot modify document outside of a transaction' in Revit API?",
                "This error means you attempted to modify the model without first opening a `Transaction`. "
                "Every write operation (creating elements, changing parameters, deleting) requires an active transaction.\n\n"
                "**Fix:**\n"
                "```csharp\n"
                "// Wrong:\n"
                "doc.Delete(elem.Id); // THROWS\n\n"
                "// Correct:\n"
                "using (Transaction tx = new Transaction(doc, \"Delete\")) {\n"
                "    tx.Start();\n"
                "    doc.Delete(elem.Id);\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
            (
                "What causes 'The family symbol is not activated' in Revit API?",
                "In Revit 2015+, `FamilySymbol` must be activated before placement. "
                "Trying to place an inactive symbol throws this exception.\n\n"
                "**Fix:** Always check and activate before calling `NewFamilyInstance`:\n\n"
                "```csharp\n"
                "using (Transaction tx = new Transaction(doc, \"Place\")) {\n"
                "    tx.Start();\n"
                "    if (!symbol.IsActive) {\n"
                "        symbol.Activate();\n"
                "        doc.Regenerate();\n"
                "    }\n"
                "    doc.NewFamilyInstance(pt, symbol, StructuralType.NonStructural);\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
            (
                "What causes 'An item with the same key has already been added' when creating family parameters?",
                "This error happens when you call `FamilyManager.AddParameter` with a name that already "
                "exists in the family.\n\n"
                "**Fix:** Check before adding:\n\n"
                "```csharp\n"
                "FamilyManager famMgr = famDoc.FamilyManager;\n"
                "FamilyParameter existing = famMgr.get_Parameter(\"Width\");\n"
                "if (existing == null) {\n"
                "    FamilyParameter fp = famMgr.AddParameter(\n"
                "        \"Width\",\n"
                "        BuiltInParameterGroup.PG_GEOMETRY,\n"
                "        ParameterType.Length,\n"
                "        false);\n"
                "}\n"
                "```",
            ),
            (
                "How do you handle the case where LoadFamily returns false in Revit API?",
                "`LoadFamily` returns `false` if the family is already loaded. "
                "Use `IFamilyLoadOptions` to control the overwrite behavior, "
                "and check for the existing family by name:\n\n"
                "```csharp\n"
                "Family loadedFamily = null;\n"
                "using (Transaction tx = new Transaction(doc, \"Load Family\")) {\n"
                "    tx.Start();\n"
                "    bool loaded = doc.LoadFamily(path, new FamilyLoadOptions(), out loadedFamily);\n"
                "    if (!loaded) {\n"
                "        // Family already exists; find it:\n"
                "        loadedFamily = new FilteredElementCollector(doc)\n"
                "            .OfClass(typeof(Family))\n"
                "            .Cast<Family>()\n"
                "            .FirstOrDefault(f => f.Name == \"M_Single-Flush\");\n"
                "    }\n"
                "    tx.Commit();\n"
                "}\n\n"
                "public class FamilyLoadOptions : IFamilyLoadOptions {\n"
                "    public bool OnFamilyFound(bool familyInUse, out bool overwriteParameterValues) {\n"
                "        overwriteParameterValues = true;\n"
                "        return true; // overwrite\n"
                "    }\n"
                "    public bool OnSharedFamilyFound(Family sf, bool familyInUse,\n"
                "        out FamilySource src, out bool overwriteParamVals) {\n"
                "        src = FamilySource.Family;\n"
                "        overwriteParamVals = true;\n"
                "        return true;\n"
                "    }\n"
                "}\n"
                "```",
            ),
            (
                "What exception is thrown when accessing a deleted element in Revit API?",
                "`Autodesk.Revit.Exceptions.InvalidOperationException` with the message "
                "'The element has been deleted' is thrown when you access a property or method "
                "on an `Element` that was deleted in the current or a previous transaction.\n\n"
                "**Fix:** Always re-fetch elements by ID after any document modification:\n\n"
                "```csharp\n"
                "ElementId id = elem.Id;\n"
                "// ... transaction that may have regenerated or modified elements ...\n"
                "Element freshElem = doc.GetElement(id);\n"
                "if (freshElem == null) {\n"
                "    // element was deleted\n"
                "    return;\n"
                "}\n"
                "// safe to use freshElem\n"
                "```",
            ),
            (
                "How do you suppress Revit warning dialogs during API operations?",
                "Implement `IFailuresPreprocessor` and set it on the transaction:\n\n"
                "```csharp\n"
                "public class SuppressWarnings : IFailuresPreprocessor {\n"
                "    public FailureProcessingResult PreprocessFailures(FailuresAccessor fa) {\n"
                "        IList<FailureMessageAccessor> failures = fa.GetFailureMessages();\n"
                "        foreach (FailureMessageAccessor f in failures) {\n"
                "            if (f.GetSeverity() == FailureSeverity.Warning)\n"
                "                fa.DeleteWarning(f);\n"
                "        }\n"
                "        return FailureProcessingResult.Continue;\n"
                "    }\n"
                "}\n\n"
                "using (Transaction tx = new Transaction(doc, \"Silent Op\")) {\n"
                "    tx.Start();\n"
                "    FailureHandlingOptions opts = tx.GetFailureHandlingOptions();\n"
                "    opts.SetFailuresPreprocessor(new SuppressWarnings());\n"
                "    tx.SetFailureHandlingOptions(opts);\n"
                "    // ... modifications ...\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
        ]
        return [_s(q, a) for q, a in errors]

    # ------------------------------------------------------------------
    # Common patterns
    # ------------------------------------------------------------------
    def _common_patterns(self) -> List[SAMPLE]:
        patterns = [
            (
                "Show the standard pattern for a Revit external command that modifies elements.",
                "```csharp\n"
                "using Autodesk.Revit.Attributes;\n"
                "using Autodesk.Revit.DB;\n"
                "using Autodesk.Revit.UI;\n\n"
                "[Transaction(TransactionMode.Manual)]\n"
                "[Regeneration(RegenerationOption.Manual)]\n"
                "public class MyModifyCommand : IExternalCommand {\n"
                "    public Result Execute(\n"
                "        ExternalCommandData commandData,\n"
                "        ref string message,\n"
                "        ElementSet elements) {\n"
                "        UIApplication uiApp = commandData.Application;\n"
                "        UIDocument uidoc = uiApp.ActiveUIDocument;\n"
                "        Document doc = uidoc.Document;\n"
                "        try {\n"
                "            using (Transaction tx = new Transaction(doc, \"My Modification\")) {\n"
                "                tx.Start();\n"
                "                // ... perform modifications ...\n"
                "                tx.Commit();\n"
                "            }\n"
                "            return Result.Succeeded;\n"
                "        } catch (Exception ex) {\n"
                "            message = ex.Message;\n"
                "            return Result.Failed;\n"
                "        }\n"
                "    }\n"
                "}\n"
                "```",
            ),
            (
                "Show the pattern for batch-creating multiple elements inside one transaction.",
                "```csharp\n"
                "double MM_TO_FT = 1.0 / 304.8;\n"
                "var positions = new List<XYZ> {\n"
                "    new XYZ(0, 0, 0),\n"
                "    new XYZ(2000 * MM_TO_FT, 0, 0),\n"
                "    new XYZ(4000 * MM_TO_FT, 0, 0),\n"
                "};\n"
                "using (Transaction tx = new Transaction(doc, \"Batch Place\")) {\n"
                "    tx.Start();\n"
                "    if (!symbol.IsActive) symbol.Activate();\n"
                "    foreach (XYZ pt in positions) {\n"
                "        doc.NewFamilyInstance(pt, symbol, StructuralType.NonStructural);\n"
                "    }\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
            (
                "How do you report progress during long-running Revit API operations?",
                "Use `using` blocks with a local progress dialog, and call `doc.Regenerate()` "
                "periodically to keep the UI responsive. For very long tasks, use an `IExternalEventHandler`:\n\n"
                "```csharp\n"
                "int total = elementIds.Count;\n"
                "int processed = 0;\n"
                "using (Transaction tx = new Transaction(doc, \"Batch Update\")) {\n"
                "    tx.Start();\n"
                "    foreach (ElementId id in elementIds) {\n"
                "        Element e = doc.GetElement(id);\n"
                "        // ... modify e ...\n"
                "        processed++;\n"
                "        // Optionally update UI progress here\n"
                "    }\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
            (
                "Show the pattern for reading and writing a family parameter formula cycle.",
                "```csharp\n"
                "Document famDoc = app.OpenDocumentFile(path);\n"
                "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
                "// Add parameters (no Transaction needed):\n"
                "FamilyParameter width = famMgr.get_Parameter(\"Width\") ??\n"
                "    famMgr.AddParameter(\"Width\", BuiltInParameterGroup.PG_GEOMETRY,\n"
                "        ParameterType.Length, false);\n"
                "FamilyParameter depth = famMgr.get_Parameter(\"Depth\") ??\n"
                "    famMgr.AddParameter(\"Depth\", BuiltInParameterGroup.PG_GEOMETRY,\n"
                "        ParameterType.Length, false);\n"
                "FamilyParameter area = famMgr.get_Parameter(\"Area\") ??\n"
                "    famMgr.AddParameter(\"Area\", BuiltInParameterGroup.PG_GEOMETRY,\n"
                "        ParameterType.Area, false);\n\n"
                "// Set values and formulas:\n"
                "famMgr.Set(width, 900 * (1.0 / 304.8));\n"
                "famMgr.Set(depth, 600 * (1.0 / 304.8));\n"
                "famMgr.SetFormula(area, \"Width * Depth\");\n\n"
                "famDoc.Save();\n"
                "famDoc.Close(false);\n"
                "```",
            ),
            (
                "Show the pattern for selecting elements interactively in a Revit command.",
                "```csharp\n"
                "UIDocument uidoc = commandData.Application.ActiveUIDocument;\n"
                "// Prompt user to select one element:\n"
                "Reference pickedRef = uidoc.Selection.PickObject(\n"
                "    ObjectType.Element, \"Select an element\");\n"
                "Element elem = uidoc.Document.GetElement(pickedRef);\n\n"
                "// Prompt user to select multiple elements:\n"
                "IList<Reference> refs = uidoc.Selection.PickObjects(\n"
                "    ObjectType.Element, \"Select elements (Finish with done)\");\n"
                "List<Element> elems = refs\n"
                "    .Select(r => uidoc.Document.GetElement(r))\n"
                "    .ToList();\n"
                "```",
            ),
            (
                "How do you get all levels in a Revit project?",
                "```csharp\n"
                "var levels = new FilteredElementCollector(doc)\n"
                "    .OfClass(typeof(Level))\n"
                "    .Cast<Level>()\n"
                "    .OrderBy(l => l.Elevation)\n"
                "    .ToList();\n\n"
                "// Get a specific level by name:\n"
                "Level level1 = levels.FirstOrDefault(l => l.Name == \"Level 1\");\n\n"
                "// Get level elevation in mm:\n"
                "double elevMM = level1.Elevation * 304.8;\n"
                "```",
            ),
            (
                "Show how to create a wall in a Revit project using the API.",
                "```csharp\n"
                "double MM_TO_FT = 1.0 / 304.8;\n"
                "Level level = // obtain level\n"
                "WallType wallType = new FilteredElementCollector(doc)\n"
                "    .OfClass(typeof(WallType))\n"
                "    .Cast<WallType>()\n"
                "    .FirstOrDefault(wt => wt.Name.Contains(\"Generic - 200mm\"));\n\n"
                "using (Transaction tx = new Transaction(doc, \"Create Wall\")) {\n"
                "    tx.Start();\n"
                "    XYZ start = new XYZ(0, 0, 0);\n"
                "    XYZ end   = new XYZ(5000 * MM_TO_FT, 0, 0);\n"
                "    Line wallLine = Line.CreateBound(start, end);\n"
                "    double height = 3000 * MM_TO_FT;\n"
                "    Wall wall = Wall.Create(doc, wallLine, wallType.Id, level.Id,\n"
                "        height, 0, false, false);\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
            (
                "Show how to create a floor in a Revit project using the API.",
                "```csharp\n"
                "double MM_TO_FT = 1.0 / 304.8;\n"
                "Level level = // obtain level\n"
                "FloorType floorType = new FilteredElementCollector(doc)\n"
                "    .OfClass(typeof(FloorType))\n"
                "    .Cast<FloorType>()\n"
                "    .FirstOrDefault();\n\n"
                "using (Transaction tx = new Transaction(doc, \"Create Floor\")) {\n"
                "    tx.Start();\n"
                "    CurveArray boundary = new CurveArray();\n"
                "    double w = 6000 * MM_TO_FT, d = 4000 * MM_TO_FT;\n"
                "    boundary.Append(Line.CreateBound(new XYZ(0, 0, 0), new XYZ(w, 0, 0)));\n"
                "    boundary.Append(Line.CreateBound(new XYZ(w, 0, 0), new XYZ(w, d, 0)));\n"
                "    boundary.Append(Line.CreateBound(new XYZ(w, d, 0), new XYZ(0, d, 0)));\n"
                "    boundary.Append(Line.CreateBound(new XYZ(0, d, 0), new XYZ(0, 0, 0)));\n"
                "    Floor floor = doc.Create.NewFloor(boundary, floorType, level, false);\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
            (
                "How do you print or export a view to PDF using Revit API?",
                "Use `PrintManager` to print views to PDF (requires a PDF printer driver installed):\n\n"
                "```csharp\n"
                "PrintManager pm = doc.PrintManager;\n"
                "pm.PrintSetup.CurrentPrintSetting.PrintParameters.PaperPlacement =\n"
                "    PaperPlacementType.Center;\n"
                "pm.PrintSetup.CurrentPrintSetting.PrintParameters.HiddenLineViews =\n"
                "    HiddenLineViewsType.RasterProcessing;\n"
                "pm.PrintToFile = true;\n"
                "pm.PrintToFileName = @\"C:\\\\output\\\\drawing.pdf\";\n"
                "pm.SelectNewPrintDriver(\"Microsoft Print to PDF\");\n"
                "pm.Apply();\n"
                "using (Transaction tx = new Transaction(doc, \"Print View\")) {\n"
                "    tx.Start();\n"
                "    pm.SubmitPrint(doc.ActiveView);\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
            (
                "Show how to use WorksharingUtils to check out an element in Revit API.",
                "```csharp\n"
                "// Check if model is workshared:\n"
                "if (!doc.IsWorkshared) {\n"
                "    TaskDialog.Show(\"Info\", \"Model is not workshared.\");\n"
                "    return;\n"
                "}\n"
                "// Check ownership:\n"
                "WorksharingTooltipInfo info = WorksharingUtils.GetWorksharingTooltipInfo(doc, elem.Id);\n"
                "string owner = info.Owner;\n\n"
                "// Request ownership of elements:\n"
                "ICollection<ElementId> toCheckout = new List<ElementId> { elem.Id };\n"
                "using (Transaction tx = new Transaction(doc, \"Checkout\")) {\n"
                "    tx.Start();\n"
                "    CheckoutStatus status = WorksharingUtils.CheckoutElements(doc, toCheckout).First();\n"
                "    // status == CheckoutStatus.OwnedByCurrentUser -> success\n"
                "    tx.Commit();\n"
                "}\n"
                "```",
            ),
        ]
        return [_s(q, a) for q, a in patterns]

    # ------------------------------------------------------------------
    # Unit conversion
    # ------------------------------------------------------------------
    def _unit_conversion(self) -> List[SAMPLE]:
        conversions = [
            (
                "How do you convert millimeters to feet for Revit API length parameters?",
                "The Revit API stores all lengths in **decimal feet**. Convert with:\n\n"
                "```csharp\n"
                "double MM_TO_FT = 1.0 / 304.8;\n"
                "double widthFt = 900  * MM_TO_FT;  // 900 mm = 2.9528 ft\n"
                "double heightFt = 2100 * MM_TO_FT; // 2100 mm = 6.8898 ft\n"
                "double thickFt  = 200  * MM_TO_FT; // 200 mm  = 0.6562 ft\n"
                "```\n\n"
                "To convert back (display in mm):\n"
                "```csharp\n"
                "double FT_TO_MM = 304.8;\n"
                "double displayMM = someFeetValue * FT_TO_MM;\n"
                "```",
            ),
            (
                "How do you convert inches to feet for Revit API parameters?",
                "Use the inch-to-foot factor:\n\n"
                "```csharp\n"
                "double INCH_TO_FT = 1.0 / 12.0;\n"
                "double doorWidthFt   = 36  * INCH_TO_FT; // 36\"  = 3.0 ft\n"
                "double doorHeightFt  = 84  * INCH_TO_FT; // 84\"  = 7.0 ft\n"
                "double clearanceFt   = 60  * INCH_TO_FT; // 60\"  = 5.0 ft (ADA)\n"
                "double rampSlopeFt   = 1.0 / 12.0;       // 1:12 slope = 1 inch rise per foot\n"
                "```",
            ),
            (
                "How do you convert angles for Revit API parameters?",
                "Revit stores angles in **radians** internally:\n\n"
                "```csharp\n"
                "double DEG_TO_RAD = Math.PI / 180.0;\n"
                "double angle90  = 90  * DEG_TO_RAD; // pi/2\n"
                "double angle45  = 45  * DEG_TO_RAD; // pi/4\n"
                "double angle180 = 180 * DEG_TO_RAD; // pi\n"
                "double angle360 = 360 * DEG_TO_RAD; // 2*pi (full rotation)\n\n"
                "// Back to degrees:\n"
                "double displayDeg = radianValue * (180.0 / Math.PI);\n"
                "```",
            ),
            (
                "How do you display a Revit API value in a user-readable format?",
                "In Revit 2022+, use `UnitUtils.ConvertFromInternalUnits`:\n\n"
                "```csharp\n"
                "// Convert internal feet to mm for display:\n"
                "double mm = UnitUtils.ConvertFromInternalUnits(\n"
                "    param.AsDouble(), UnitTypeId.Millimeters);\n"
                "string label = $\"{mm:F0} mm\";\n\n"
                "// Convert mm to internal feet for setting:\n"
                "double ft = UnitUtils.ConvertToInternalUnits(900, UnitTypeId.Millimeters);\n"
                "param.Set(ft);\n"
                "```\n\n"
                "In Revit 2021 and earlier, use `DisplayUnitType`:\n"
                "```csharp\n"
                "double mm = UnitUtils.ConvertFromInternalUnits(\n"
                "    param.AsDouble(), DisplayUnitType.DUT_MILLIMETERS);\n"
                "```",
            ),
            (
                "What are the area and volume unit conversion factors in Revit API?",
                "Revit stores areas in **square feet** and volumes in **cubic feet**:\n\n"
                "```csharp\n"
                "// Area:\n"
                "double MM2_TO_FT2 = 1.0 / (304.8 * 304.8);\n"
                "double areaFt2 = 10000 * MM2_TO_FT2; // 10,000 mm^2 in ft^2\n\n"
                "// More commonly in m^2:\n"
                "double M2_TO_FT2 = 10.7639;  // 1 m^2 = 10.7639 ft^2\n"
                "double floorAreaFt2 = 25.0 * M2_TO_FT2; // 25 m^2\n\n"
                "// Volume:\n"
                "double M3_TO_FT3 = 35.3147;  // 1 m^3 = 35.3147 ft^3\n"
                "double volFt3 = 1.5 * M3_TO_FT3; // 1.5 m^3\n\n"
                "// Or use UnitUtils (Revit 2022+):\n"
                "double areaFt2_v2 = UnitUtils.ConvertToInternalUnits(25, UnitTypeId.SquareMeters);\n"
                "```",
            ),
            (
                "How do you set a length parameter value in a FamilyType to a millimeter value?",
                "```csharp\n"
                "double MM_TO_FT = 1.0 / 304.8;\n"
                "Document famDoc = app.OpenDocumentFile(path);\n"
                "FamilyManager famMgr = famDoc.FamilyManager;\n"
                "FamilyType type900 = famMgr.NewType(\"900x2100\");\n"
                "famMgr.CurrentType = type900;\n\n"
                "FamilyParameter width  = famMgr.get_Parameter(\"Width\");\n"
                "FamilyParameter height = famMgr.get_Parameter(\"Height\");\n\n"
                "// Set 900mm and 2100mm:\n"
                "famMgr.Set(width,  900  * MM_TO_FT);\n"
                "famMgr.Set(height, 2100 * MM_TO_FT);\n\n"
                "famDoc.Save();\n"
                "famDoc.Close(false);\n"
                "```",
            ),
            (
                "How do you read a parameter value and display it in millimeters from a FamilyInstance?",
                "```csharp\n"
                "double FT_TO_MM = 304.8;\n"
                "FamilyInstance door = // obtained from collector\n"
                "Parameter heightParam = door.get_Parameter(BuiltInParameter.DOOR_HEIGHT);\n"
                "if (heightParam != null && heightParam.HasValue) {\n"
                "    double heightFt = heightParam.AsDouble();\n"
                "    double heightMM = heightFt * FT_TO_MM;\n"
                "    TaskDialog.Show(\"Door Height\", $\"{heightMM:F0} mm\");\n"
                "}\n"
                "```",
            ),
            (
                "What is the pipe diameter conversion in Revit MEP API?",
                "Pipe and duct sizes in Revit API are stored in **decimal feet** like all lengths:\n\n"
                "```csharp\n"
                "double MM_TO_FT = 1.0 / 304.8;\n"
                "double INCH_TO_FT = 1.0 / 12.0;\n\n"
                "// Set pipe diameter to 100mm (DN100):\n"
                "Parameter diamParam = pipe.get_Parameter(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM);\n"
                "diamParam.Set(100 * MM_TO_FT);\n\n"
                "// Set pipe diameter to 4 inches:\n"
                "diamParam.Set(4 * INCH_TO_FT);\n\n"
                "// Read back:\n"
                "double diamFt = diamParam.AsDouble();\n"
                "double diamMM = diamFt * 304.8;\n"
                "double diamIn = diamFt * 12.0;\n"
                "```",
            ),
        ]
        return [_s(q, a) for q, a in conversions]
