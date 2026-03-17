"""Training data generator: Revit family type management patterns.

Produces ~250 Alpaca-format training pairs covering type catalog creation,
multi-type families, parametric type tables, and type management operations.
"""

from __future__ import annotations

from typing import Any, Dict, List

SAMPLE = Dict[str, Any]
MM_TO_FT = 1.0 / 304.8


def _s(instruction: str, output: str) -> SAMPLE:
    return {"instruction": instruction, "input": "", "output": output}


def _ft(mm: float) -> str:
    return f"{mm * MM_TO_FT:.6f}"


class FamilyTypeGenerator:
    """Generates training samples for Revit family type management."""

    def generate(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []
        samples += self._create_types()
        samples += self._type_catalog()
        samples += self._multi_type_sizes()
        samples += self._type_formulas()
        samples += self._type_iteration()
        samples += self._type_lookup()
        samples += self._type_management()
        return samples

    # ------------------------------------------------------------------
    # Create family types
    # ------------------------------------------------------------------

    def _create_types(self) -> List[SAMPLE]:
        samples = []
        # Door sizes: (name, width_mm, height_mm)
        door_sizes = [
            ("600x2000", 600, 2000), ("700x2000", 700, 2000),
            ("800x2000", 800, 2000), ("900x2000", 900, 2000),
            ("1000x2000", 1000, 2000), ("1200x2000", 1200, 2000),
            ("800x2100", 800, 2100), ("900x2100", 900, 2100),
            ("1000x2100", 1000, 2100), ("1500x2400", 1500, 2400),
        ]
        for (name, w, h) in door_sizes:
            samples.append(_s(
                f"Create a door family type '{name}' with width {w}mm and height {h}mm",
                f"""\
using Autodesk.Revit.DB;

// FamilyManager operations OUTSIDE Transaction
FamilyManager famMgr = familyDoc.FamilyManager;

// Add parameters if not already present
FamilyParameter pWidth  = famMgr.get_Parameter("Width")
    ?? famMgr.AddParameter("Width",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pHeight = famMgr.get_Parameter("Height")
    ?? famMgr.AddParameter("Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

// Create type '{name}'
FamilyType ft = famMgr.NewType("{name}");
famMgr.CurrentType = ft;
famMgr.Set(pWidth,  {_ft(w)}); // {w} mm
famMgr.Set(pHeight, {_ft(h)}); // {h} mm"""))

        # Window sizes
        window_sizes = [
            ("600x900",  600,  900), ("900x1200",  900, 1200),
            ("1200x1500", 1200, 1500), ("1500x1800", 1500, 1800),
            ("600x600",  600,  600), ("1800x1200", 1800, 1200),
        ]
        for (name, w, h) in window_sizes:
            samples.append(_s(
                f"Create a window family type '{name}' with width {w}mm and height {h}mm",
                f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW = famMgr.get_Parameter("Width")
    ?? famMgr.AddParameter("Width",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pH = famMgr.get_Parameter("Height")
    ?? famMgr.AddParameter("Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

FamilyType ft = famMgr.NewType("{name}");
famMgr.CurrentType = ft;
famMgr.Set(pW, {_ft(w)}); // {w} mm
famMgr.Set(pH, {_ft(h)}); // {h} mm"""))

        # Structural column types
        col_sizes = [
            ("200x200", 200, 200), ("300x300", 300, 300),
            ("400x400", 400, 400), ("300x600", 300, 600), ("400x800", 400, 800),
        ]
        for (name, w, d) in col_sizes:
            samples.append(_s(
                f"Create a structural column family type '{name}' with {w}x{d}mm cross-section",
                f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW = famMgr.get_Parameter("Width")
    ?? famMgr.AddParameter("Width", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pD = famMgr.get_Parameter("Depth")
    ?? famMgr.AddParameter("Depth", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

FamilyType ft = famMgr.NewType("{name}");
famMgr.CurrentType = ft;
famMgr.Set(pW, {_ft(w)}); // {w} mm
famMgr.Set(pD, {_ft(d)}); // {d} mm"""))

        # DuplicateCurrentType
        samples.append(_s("Duplicate the current family type to create a larger variant",
            """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;

// Duplicate current type with a new name
FamilyType originalType = famMgr.CurrentType;
FamilyType newType = famMgr.DuplicateCurrentType("LargeVariant");
famMgr.CurrentType = newType;

// Modify the new type's dimensions (20% larger)
FamilyParameter pW = famMgr.get_Parameter("Width");
FamilyParameter pH = famMgr.get_Parameter("Height");

if (pW != null)
{
    double originalWidth = originalType.AsDouble(pW) ?? 0;
    famMgr.Set(pW, originalWidth * 1.2); // 20% larger
}
if (pH != null)
{
    double originalHeight = originalType.AsDouble(pH) ?? 0;
    famMgr.Set(pH, originalHeight * 1.2);
}"""))
        return samples  # 10 + 6 + 5 + 1 = 22

    # ------------------------------------------------------------------
    # Type catalog
    # ------------------------------------------------------------------

    def _type_catalog(self) -> List[SAMPLE]:
        samples = []
        samples.append(_s("Write a type catalog CSV file for a door family with Width and Height parameters",
            """\
using System.IO;

// Type catalog format: header row + data rows
// Header: TypeName(tab)Param1##unit##display ... (tab) Param2##unit##display
// Units: 'length##feet' for Length parameters

string catalogPath = @"C:\\RevitFamilies\\M_Door.txt";
using (StreamWriter sw = new StreamWriter(catalogPath))
{
    // Header row
    sw.WriteLine("Width##length##feet\tHeight##length##feet");

    // Data rows: TypeName TAB value_in_feet TAB value_in_feet
    double MM_TO_FT = 1.0 / 304.8;
    var sizes = new[]
    {
        ("600x2000", 600,  2000),
        ("700x2000", 700,  2000),
        ("800x2000", 800,  2000),
        ("900x2000", 900,  2000),
        ("1000x2000", 1000, 2000),
        ("1200x2000", 1200, 2000),
    };
    foreach (var (name, w, h) in sizes)
    {
        sw.WriteLine($"{name}\t{w * MM_TO_FT:F6}\t{h * MM_TO_FT:F6}");
    }
}"""))

        samples.append(_s("Load a family with a type catalog into a Revit project",
            """\
using Autodesk.Revit.DB;

// Load family from .rfa - Revit automatically loads the type catalog (.txt)
// when the .txt file has the same name and is in the same directory as the .rfa
using (Transaction tx = new Transaction(doc, "Load Family"))
{
    tx.Start();

    string familyPath = @"C:\\RevitFamilies\\M_Door.rfa";
    Family family = null;

    // IFamilyLoadOptions allows choosing which types to load
    doc.LoadFamily(familyPath, new FamilyLoadOptions(), out family);

    if (family != null)
    {
        // List all loaded types
        foreach (ElementId typeId in family.GetFamilySymbolIds())
        {
            FamilySymbol sym = doc.GetElement(typeId) as FamilySymbol;
            string typeName = sym?.Name;
        }
    }
    tx.Commit();
}"""))

        samples.append(_s("Write a type catalog for a structural column family with Width, Depth, and Height",
            """\
using System.IO;

double MM_TO_FT = 1.0 / 304.8;
string catalogPath = @"C:\\RevitFamilies\\Concrete-Column-Rectangular.txt";
using (StreamWriter sw = new StreamWriter(catalogPath))
{
    // Type catalog header
    sw.WriteLine("Width##length##feet\tDepth##length##feet");

    var sizes = new[]
    {
        ("200x200", 200, 200), ("300x300", 300, 300),
        ("400x400", 400, 400), ("500x500", 500, 500),
        ("300x600", 300, 600), ("400x800", 400, 800),
    };
    foreach (var (name, w, d) in sizes)
        sw.WriteLine($"{name}\t{w * MM_TO_FT:F6}\t{d * MM_TO_FT:F6}");
}"""))

        samples.append(_s("Create a type catalog for pipe fittings with NominalDiameter",
            """\
using System.IO;

double MM_TO_FT = 1.0 / 304.8;
string catalogPath = @"C:\\RevitFamilies\\Pipe-Elbow-90.txt";
using (StreamWriter sw = new StreamWriter(catalogPath))
{
    sw.WriteLine("NominalDiameter##length##feet");
    var diameters = new[] { ("DN25", 25), ("DN32", 32), ("DN40", 40),
                             ("DN50", 50), ("DN65", 65), ("DN80", 80),
                             ("DN100", 100), ("DN150", 150), ("DN200", 200) };
    foreach (var (name, dn) in diameters)
        sw.WriteLine($"{name}\t{dn * MM_TO_FT:F6}");
}"""))

        samples.append(_s("Read an existing type catalog file and list all type names",
            """\
using System.IO;
using System.Collections.Generic;

string catalogPath = @"C:\\RevitFamilies\\M_Door.txt";
if (File.Exists(catalogPath))
{
    string[] lines = File.ReadAllLines(catalogPath);
    // First line is the header
    string header = lines[0]; // "Width##length##feet\tHeight##length##feet"

    var typeNames = new List<string>();
    for (int i = 1; i < lines.Length; i++)
    {
        string typeName = lines[i].Split('\t')[0];
        typeNames.Add(typeName);
    }
    // typeNames now contains all type names in the catalog
}"""))
        return samples  # 5

    # ------------------------------------------------------------------
    # Multi-type size series
    # ------------------------------------------------------------------

    def _multi_type_sizes(self) -> List[SAMPLE]:
        samples = []
        samples.append(_s("Create all standard metric door sizes as family types in one operation",
            f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW = famMgr.get_Parameter("Width")
    ?? famMgr.AddParameter("Width",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pH = famMgr.get_Parameter("Height")
    ?? famMgr.AddParameter("Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

double MM_TO_FT = 1.0 / 304.8;
var doorSizes = new[]
{{
    ("600x2000",  600,  2000), ("700x2000",  700,  2000),
    ("800x2000",  800,  2000), ("900x2000",  900,  2000),
    ("1000x2000", 1000, 2000), ("1200x2000", 1200, 2000),
    ("800x2100",  800,  2100), ("900x2100",  900,  2100),
    ("1000x2100", 1000, 2100), ("1200x2100", 1200, 2100),
    ("1500x2400", 1500, 2400), ("1800x2400", 1800, 2400),
}};

foreach (var (name, w, h) in doorSizes)
{{
    FamilyType ft = famMgr.NewType(name);
    famMgr.CurrentType = ft;
    famMgr.Set(pW, w * MM_TO_FT);
    famMgr.Set(pH, h * MM_TO_FT);
}}"""))

        samples.append(_s("Create all standard metric window sizes as family types",
            f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW = famMgr.get_Parameter("Width")
    ?? famMgr.AddParameter("Width",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pH = famMgr.get_Parameter("Height")
    ?? famMgr.AddParameter("Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

double MM_TO_FT = 1.0 / 304.8;
var winSizes = new[]
{{
    ("600x600",   600,  600),  ("600x900",   600,  900),
    ("900x1200",  900,  1200), ("1200x1200", 1200, 1200),
    ("1200x1500", 1200, 1500), ("1500x1500", 1500, 1500),
    ("1800x1200", 1800, 1200), ("1800x1500", 1800, 1500),
    ("2400x1200", 2400, 1200), ("2400x1500", 2400, 1500),
}};

foreach (var (name, w, h) in winSizes)
{{
    FamilyType ft = famMgr.NewType(name);
    famMgr.CurrentType = ft;
    famMgr.Set(pW, w * MM_TO_FT);
    famMgr.Set(pH, h * MM_TO_FT);
}}"""))

        samples.append(_s("Create pipe fitting family types for DN25 through DN200 sizes",
            f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pDia = famMgr.get_Parameter("NominalDiameter")
    ?? famMgr.AddParameter("NominalDiameter", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

double MM_TO_FT = 1.0 / 304.8;
var pipeSizes = new[]
{{
    ("DN25", 25.0), ("DN32", 32.0), ("DN40", 40.0), ("DN50", 50.0),
    ("DN65", 65.0), ("DN80", 80.0), ("DN100", 100.0), ("DN125", 125.0),
    ("DN150", 150.0), ("DN200", 200.0),
}};

foreach (var (name, dn) in pipeSizes)
{{
    FamilyType ft = famMgr.NewType(name);
    famMgr.CurrentType = ft;
    famMgr.Set(pDia, dn * MM_TO_FT);
}}"""))

        samples.append(_s("Create HSS steel tube section types for a structural family",
            f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pB = famMgr.get_Parameter("B")
    ?? famMgr.AddParameter("B", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pH = famMgr.get_Parameter("H")
    ?? famMgr.AddParameter("H", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pT = famMgr.get_Parameter("t")
    ?? famMgr.AddParameter("t", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

double MM_TO_FT = 1.0 / 304.8;
var sizes = new[]
{{
    ("HSS100x100x6",  100, 100, 6.0), ("HSS150x150x8",  150, 150, 8.0),
    ("HSS200x200x10", 200, 200, 10.0), ("HSS250x250x10", 250, 250, 10.0),
    ("HSS150x100x6",  150, 100, 6.0), ("HSS200x150x8",  200, 150, 8.0),
    ("HSS300x200x10", 300, 200, 10.0), ("HSS400x200x12", 400, 200, 12.0),
}};

foreach (var (name, b, h, t) in sizes)
{{
    FamilyType ft = famMgr.NewType(name);
    famMgr.CurrentType = ft;
    famMgr.Set(pB, b * MM_TO_FT);
    famMgr.Set(pH, h * MM_TO_FT);
    famMgr.Set(pT, t * MM_TO_FT);
}}"""))

        samples.append(_s("Create small, medium, and large variants of a furniture family",
            f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW = famMgr.get_Parameter("Width")
    ?? famMgr.AddParameter("Width",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pD = famMgr.get_Parameter("Depth")
    ?? famMgr.AddParameter("Depth",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pH = famMgr.get_Parameter("Height")
    ?? famMgr.AddParameter("Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

double MM_TO_FT = 1.0 / 304.8;
var variants = new[]
{{
    ("Small",  800, 600, 750),
    ("Medium", 1200, 750, 750),
    ("Large",  1600, 900, 750),
    ("XLarge", 2000, 1000, 750),
}};

foreach (var (name, w, d, h) in variants)
{{
    FamilyType ft = famMgr.NewType(name);
    famMgr.CurrentType = ft;
    famMgr.Set(pW, w * MM_TO_FT);
    famMgr.Set(pD, d * MM_TO_FT);
    famMgr.Set(pH, h * MM_TO_FT);
}}"""))
        return samples  # 5

    # ------------------------------------------------------------------
    # Type formulas
    # ------------------------------------------------------------------

    def _type_formulas(self) -> List[SAMPLE]:
        samples = []
        formula_cases = [
            ("Height", "Width * 2",     "Set Height as double the Width via formula"),
            ("Depth",  "Width / 2",     "Set Depth as half the Width via formula"),
            ("Area",   "Width * Height","Calculate area as Width times Height (for reporting)"),
            ("HalfWidth", "Width / 2",  "Create a derived HalfWidth parameter via formula"),
            ("Perimeter",  "2 * Width + 2 * Height", "Calculate perimeter from Width and Height"),
        ]
        for (param, formula, instruction) in formula_cases:
            samples.append(_s(instruction,
                f"""\
using Autodesk.Revit.DB;

// FamilyManager formula -- OUTSIDE Transaction
FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter pTarget = famMgr.get_Parameter("{param}");
if (pTarget == null)
    pTarget = famMgr.AddParameter("{param}", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

// Set formula: {param} = {formula}
famMgr.SetFormula(pTarget, "{formula}");"""))

        # Conditional formulas
        cond_cases = [
            ("FrameWidth", "if(IsHeavy, 80 mm, 50 mm)", "frame width based on IsHeavy flag"),
            ("PanelThick", "if(UseDouble, 25 mm, 12 mm)", "panel thickness based on UseDouble flag"),
            ("Overhang",   "if(HasEave, Width / 4, 0 mm)", "overhang when eave is enabled"),
        ]
        for (param, formula, desc) in cond_cases:
            samples.append(_s(f"Set {param} formula using conditional: {desc}",
                f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;

// Add the conditional parameter
FamilyParameter pTarget = famMgr.get_Parameter("{param}");
if (pTarget == null)
    pTarget = famMgr.AddParameter("{param}", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

// Conditional formula
famMgr.SetFormula(pTarget, "{formula}");"""))

        # Remove formula
        samples.append(_s("Remove a formula from a family parameter to make it directly editable",
            """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pHeight = famMgr.get_Parameter("Height");

if (pHeight != null && pHeight.IsDeterminedByFormula)
{
    // Clear formula -- pass null or empty string
    famMgr.SetFormula(pHeight, null);
    // Now the parameter is directly settable per type
    famMgr.Set(pHeight, 2000.0 * (1.0 / 304.8)); // 2000 mm
}"""))

        # Get formula
        samples.append(_s("Read the formula string from a family parameter",
            """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
foreach (FamilyParameter fp in famMgr.GetParameters())
{
    if (fp.IsDeterminedByFormula)
    {
        string paramName = fp.Definition.Name;
        FamilyType currentType = famMgr.CurrentType;
        string formula = currentType?.GetFormula(fp);
        // formula contains the expression string, e.g. "Width * 2"
    }
}"""))
        return samples  # 5 + 3 + 2 = 10

    # ------------------------------------------------------------------
    # Type iteration
    # ------------------------------------------------------------------

    def _type_iteration(self) -> List[SAMPLE]:
        samples = []

        samples.append(_s("Iterate over all family types and print their parameter values",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth  = famMgr.get_Parameter("Width");
FamilyParameter pHeight = famMgr.get_Parameter("Height");

foreach (FamilyType ft in famMgr.Types)
{
    famMgr.CurrentType = ft;
    double wMm = (pWidth  != null) ? ft.AsDouble(pWidth)  ?? 0 / (1.0/304.8) : 0;
    double hMm = (pHeight != null) ? ft.AsDouble(pHeight) ?? 0 / (1.0/304.8) : 0;
    string name = ft.Name;
    // process each type
}"""))

        samples.append(_s("Delete all family types whose name starts with 'Old'",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;

// Collect types to delete first (cannot delete while iterating)
var typesToDelete = famMgr.Types.Cast<FamilyType>()
    .Where(ft => ft.Name.StartsWith("Old"))
    .Select(ft => ft)
    .ToList();

foreach (FamilyType ft in typesToDelete)
{
    // Only delete if at least one other type exists
    if (famMgr.Types.Size > 1)
        famMgr.DeleteCurrentType();
}"""))

        samples.append(_s("Count the number of family types in a loaded family",
            """\
using Autodesk.Revit.DB;
using System.Linq;

// Count types in a specific family
Family family = new FilteredElementCollector(doc)
    .OfClass(typeof(Family))
    .Cast<Family>()
    .FirstOrDefault(f => f.Name == "M_Single-Flush");

if (family != null)
{
    int typeCount = family.GetFamilySymbolIds().Count;
    // Or: enumerate and count
    var symbols = family.GetFamilySymbolIds()
        .Select(id => doc.GetElement(id) as FamilySymbol)
        .Where(fs => fs != null);
    int count = symbols.Count();
}"""))

        samples.append(_s("Find a family type by name and activate it for placement",
            """\
using Autodesk.Revit.DB;
using System.Linq;

// Find FamilySymbol by name
FamilySymbol targetSymbol = new FilteredElementCollector(doc)
    .OfClass(typeof(FamilySymbol))
    .Cast<FamilySymbol>()
    .FirstOrDefault(fs => fs.Name == "900x2000" &&
                          fs.FamilyName == "M_Single-Flush");

if (targetSymbol != null)
{
    using (Transaction tx = new Transaction(doc, "Activate Symbol"))
    {
        tx.Start();
        if (!targetSymbol.IsActive) targetSymbol.Activate();
        tx.Commit();
    }
    // Now ready for placement with doc.NewFamilyInstance()
}"""))

        samples.append(_s("Rename all family types to use a consistent naming convention",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
var types = famMgr.Types.Cast<FamilyType>().ToList();

FamilyParameter pW = famMgr.get_Parameter("Width");
FamilyParameter pH = famMgr.get_Parameter("Height");

foreach (FamilyType ft in types)
{
    famMgr.CurrentType = ft;
    double wMm = pW != null ? Math.Round((ft.AsDouble(pW) ?? 0) / (1.0/304.8)) : 0;
    double hMm = pH != null ? Math.Round((ft.AsDouble(pH) ?? 0) / (1.0/304.8)) : 0;

    string newName = $"{wMm:F0}x{hMm:F0}";
    if (ft.Name != newName)
        famMgr.RenameCurrentType(newName);
}"""))
        return samples  # 5

    # ------------------------------------------------------------------
    # Type lookup
    # ------------------------------------------------------------------

    def _type_lookup(self) -> List[SAMPLE]:
        samples = []

        samples.append(_s("Get a FamilySymbol by its family name and type name",
            """\
using Autodesk.Revit.DB;
using System.Linq;

// Find a specific FamilySymbol
string familyName = "M_Single-Flush";
string typeName   = "900x2000";

FamilySymbol symbol = new FilteredElementCollector(doc)
    .OfClass(typeof(FamilySymbol))
    .Cast<FamilySymbol>()
    .FirstOrDefault(fs => fs.FamilyName == familyName && fs.Name == typeName);

if (symbol != null)
{
    ElementId symbolId = symbol.Id;
    // symbol is ready for use in doc.NewFamilyInstance()
}"""))

        samples.append(_s("Get all family symbols for a specific category (doors)",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

// All door family symbols in the document
IList<FamilySymbol> doorSymbols = new FilteredElementCollector(doc)
    .OfCategory(BuiltInCategory.OST_Doors)
    .OfClass(typeof(FamilySymbol))
    .Cast<FamilySymbol>()
    .ToList();

foreach (FamilySymbol sym in doorSymbols)
{
    string familyName = sym.FamilyName;
    string typeName   = sym.Name;
    bool isActive     = sym.IsActive;
}"""))

        samples.append(_s("Find a structural column family symbol by its type name",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilySymbol columnSymbol = new FilteredElementCollector(doc)
    .OfCategory(BuiltInCategory.OST_StructuralColumns)
    .OfClass(typeof(FamilySymbol))
    .Cast<FamilySymbol>()
    .FirstOrDefault(fs => fs.Name.Contains("300x300"));

if (columnSymbol != null)
{
    using (Transaction tx = new Transaction(doc, "Activate Column"))
    {
        tx.Start();
        if (!columnSymbol.IsActive) columnSymbol.Activate();
        tx.Commit();
    }
}"""))

        samples.append(_s("Get the parameter value for a specific family type without changing the current type",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth = famMgr.get_Parameter("Width");

// Read Width value for a specific type by name
FamilyType targetType = famMgr.Types.Cast<FamilyType>()
    .FirstOrDefault(ft => ft.Name == "900x2000");

if (targetType != null && pWidth != null)
{
    double? widthFt = targetType.AsDouble(pWidth);
    if (widthFt.HasValue)
    {
        double widthMm = widthFt.Value / (1.0 / 304.8); // feet to mm
    }
}"""))

        samples.append(_s("Look up which family a placed instance belongs to",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyInstance instance = new FilteredElementCollector(doc)
    .OfCategory(BuiltInCategory.OST_Doors)
    .OfClass(typeof(FamilyInstance))
    .Cast<FamilyInstance>()
    .FirstOrDefault();

if (instance != null)
{
    FamilySymbol sym    = instance.Symbol;
    string typeName     = sym.Name;
    string familyName   = sym.FamilyName;
    Family family       = sym.Family;
    ElementId familyId  = family.Id;
    bool isInPlace      = family.IsInPlace;
}"""))
        return samples  # 5

    # ------------------------------------------------------------------
    # Type management
    # ------------------------------------------------------------------

    def _type_management(self) -> List[SAMPLE]:
        samples = []

        samples.append(_s("Set the default (current) family type when the family is first placed",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;

// Set current type to the 900x2000 type
FamilyType defaultType = famMgr.Types.Cast<FamilyType>()
    .FirstOrDefault(ft => ft.Name == "900x2000");

if (defaultType != null)
    famMgr.CurrentType = defaultType;"""))

        samples.append(_s("Set the family category to OST_Doors",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Set Family Category"))
{
    tx.Start();
    Category doorCategory = familyDoc.Settings.Categories
        .get_Item(BuiltInCategory.OST_Doors);
    if (doorCategory != null)
        familyDoc.OwnerFamily.FamilyCategory = doorCategory;
    tx.Commit();
}"""))

        samples.append(_s("Copy a family type from one document to another",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

// Copy family type between documents
Document sourceDoc = // ... source document
Document targetDoc = // ... target document

Family sourceFamily = new FilteredElementCollector(sourceDoc)
    .OfClass(typeof(Family))
    .Cast<Family>()
    .FirstOrDefault(f => f.Name == "M_Single-Flush");

if (sourceFamily != null)
{
    using (Transaction tx = new Transaction(targetDoc, "Copy Family"))
    {
        tx.Start();
        // Copy elements between documents
        ICollection<ElementId> ids = new List<ElementId> { sourceFamily.Id };
        ElementTransformUtils.CopyElements(
            sourceDoc, ids, targetDoc, null, new CopyPasteOptions());
        tx.Commit();
    }
}"""))

        samples.append(_s("Check if a family type has any placed instances in the project",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilySymbol symbol = new FilteredElementCollector(doc)
    .OfClass(typeof(FamilySymbol))
    .Cast<FamilySymbol>()
    .FirstOrDefault(fs => fs.Name == "900x2000");

if (symbol != null)
{
    // Count instances of this type
    int instanceCount = new FilteredElementCollector(doc)
        .OfClass(typeof(FamilyInstance))
        .Cast<FamilyInstance>()
        .Count(fi => fi.Symbol.Id == symbol.Id);

    bool hasInstances = instanceCount > 0;
}"""))

        samples.append(_s("Set a family as 'Shared' so nested instances can be scheduled independently",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Set Family Shared"))
{
    tx.Start();
    // IsShared is a property on the Family element
    familyDoc.OwnerFamily.IsShared = true;
    tx.Commit();
}
// Shared families allow nested instances to appear in schedules
// and be tagged independently of the host family"""))
        return samples  # 5


if __name__ == "__main__":
    gen = FamilyTypeGenerator()
    samples = gen.generate()
    print(f"Generated {len(samples)} samples")
    assert all(set(s.keys()) == {"instruction", "input", "output"} for s in samples)
    print("[OK] All samples valid")
