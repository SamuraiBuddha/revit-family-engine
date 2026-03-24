"""Training data generator: Revit family types, type catalogs, nested families, shared parameters.

Produces ~250-280 Alpaca-format training pairs covering type catalog CSV authoring,
nested family loading and placement, shared parameter binding, type iteration and
duplication, and family category assignment.
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
        samples += self._type_creation()
        samples += self._type_catalog_csv()
        samples += self._nested_family_loading()
        samples += self._nested_family_placement()
        samples += self._shared_parameters()
        samples += self._type_iteration_queries()
        samples += self._family_category_assignment()
        samples += self._type_duplication()
        return samples

    # ------------------------------------------------------------------
    # Type creation and management (~40 samples)
    # ------------------------------------------------------------------

    def _type_creation(self) -> List[SAMPLE]:
        samples = []

        # Basic NewType cases
        basic_types = [
            ("Small",  600,  300, 2100, "a small door type 600x2100mm"),
            ("Medium", 900,  300, 2100, "a standard door type 900x2100mm"),
            ("Large",  1200, 300, 2200, "a large door type 1200x2200mm"),
            ("Double", 1800, 300, 2400, "a double-leaf door type 1800x2400mm"),
        ]
        for type_name, w, d, h, desc in basic_types:
            w_ft, d_ft, h_ft = w * MM_TO_FT, d * MM_TO_FT, h * MM_TO_FT
            samples.append(_s(
                f"Create a new family type called '{type_name}' for {desc}",
                f"""\
using Autodesk.Revit.DB;

// FamilyManager operations must occur OUTSIDE Transaction blocks
FamilyManager famMgr = familyDoc.FamilyManager;

// Create new type -- OUTSIDE transaction
FamilyType newType = famMgr.NewType("{type_name}");

// Set parameter values -- also OUTSIDE transaction
FamilyParameter pWidth  = famMgr.get_Parameter("Width");
FamilyParameter pDepth  = famMgr.get_Parameter("Thickness");
FamilyParameter pHeight = famMgr.get_Parameter("Height");

if (pWidth  != null) famMgr.Set(pWidth,  {w_ft:.6f}); // {w} mm
if (pDepth  != null) famMgr.Set(pDepth,  {d_ft:.6f}); // {d} mm
if (pHeight != null) famMgr.Set(pHeight, {h_ft:.6f}); // {h} mm""",
            ))

        # CurrentType usage
        samples.append(_s(
            "Get the currently active family type and read its Width parameter value",
            """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;

// CurrentType is the active type -- no transaction needed to read
FamilyType currentType = famMgr.CurrentType;

if (currentType != null)
{
    FamilyParameter pWidth = famMgr.get_Parameter("Width");
    if (pWidth != null)
    {
        double widthFt = currentType.AsDouble(pWidth);
        double widthMm = widthFt * 304.8;
        // widthMm is the width in millimetres
    }
}""",
        ))

        # Switch CurrentType
        type_names = ["Type A", "Type B", "Type C"]
        for tname in type_names:
            samples.append(_s(
                f"Switch the active family type to '{tname}'",
                f"""\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;

// Find and activate a specific type -- OUTSIDE transaction
FamilyType target = famMgr.Types
    .Cast<FamilyType>()
    .FirstOrDefault(t => t.Name == "{tname}");

if (target != null)
    famMgr.CurrentType = target;""",
            ))

        # Rename type
        samples.append(_s(
            "Rename an existing family type from 'Old Name' to 'New Name'",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;

FamilyType typeToRename = famMgr.Types
    .Cast<FamilyType>()
    .FirstOrDefault(t => t.Name == "Old Name");

if (typeToRename != null)
{
    famMgr.CurrentType = typeToRename;
    famMgr.RenameCurrentType("New Name");
}""",
        ))

        # Delete type
        samples.append(_s(
            "Delete a family type named 'Obsolete Type' if it exists",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;

FamilyType typeToDelete = famMgr.Types
    .Cast<FamilyType>()
    .FirstOrDefault(t => t.Name == "Obsolete Type");

if (typeToDelete != null)
{
    famMgr.CurrentType = typeToDelete;
    famMgr.DeleteCurrentType();
}""",
        ))

        # Iterate all types and list names
        samples.append(_s(
            "Iterate over all family types and collect their names into a list",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

FamilyManager famMgr = familyDoc.FamilyManager;

var typeNames = new List<string>();
foreach (FamilyType ft in famMgr.Types)
{
    typeNames.Add(ft.Name);
}
// typeNames now contains the name of every type defined in the family""",
        ))

        # Add multiple types in a loop
        window_types = [
            ("W600x900",   600,  900),
            ("W900x1200",  900,  1200),
            ("W1200x1500", 1200, 1500),
            ("W1500x1800", 1500, 1800),
        ]
        samples.append(_s(
            "Create four window family types (W600x900, W900x1200, W1200x1500, W1500x1800) with matching Width and Height values",
            f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth  = famMgr.get_Parameter("Width");
FamilyParameter pHeight = famMgr.get_Parameter("Height");

// Define types as (name, widthFt, heightFt)
var typeDefs = new (string Name, double W, double H)[]
{{
    ("{window_types[0][0]}", {window_types[0][1] * MM_TO_FT:.6f}, {window_types[0][2] * MM_TO_FT:.6f}), // {window_types[0][1]}x{window_types[0][2]} mm
    ("{window_types[1][0]}", {window_types[1][1] * MM_TO_FT:.6f}, {window_types[1][2] * MM_TO_FT:.6f}), // {window_types[1][1]}x{window_types[1][2]} mm
    ("{window_types[2][0]}", {window_types[2][1] * MM_TO_FT:.6f}, {window_types[2][2] * MM_TO_FT:.6f}), // {window_types[2][1]}x{window_types[2][2]} mm
    ("{window_types[3][0]}", {window_types[3][1] * MM_TO_FT:.6f}, {window_types[3][2] * MM_TO_FT:.6f}), // {window_types[3][1]}x{window_types[3][2]} mm
}};

foreach (var def in typeDefs)
{{
    FamilyType ft = famMgr.NewType(def.Name);
    if (pWidth  != null) famMgr.Set(pWidth,  def.W);
    if (pHeight != null) famMgr.Set(pHeight, def.H);
}}""",
        ))

        # Check whether a type exists before creating
        samples.append(_s(
            "Check whether a family type named 'Standard' already exists before creating it",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;

bool exists = famMgr.Types
    .Cast<FamilyType>()
    .Any(t => t.Name == "Standard");

if (!exists)
{
    FamilyType standard = famMgr.NewType("Standard");
    // set parameters as needed
}""",
        ))

        # Set a Yes/No parameter on a type
        samples.append(_s(
            "Set a Yes/No parameter 'Has Frame' to true on the current family type",
            """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pHasFrame = famMgr.get_Parameter("Has Frame");

if (pHasFrame != null && pHasFrame.StorageType == StorageType.Integer)
{
    famMgr.Set(pHasFrame, 1); // 1 = true for Yes/No parameters
}""",
        ))

        # Set a string parameter on a type
        samples.append(_s(
            "Set the 'Manufacturer' text parameter to 'Acme Corp' on the current family type",
            """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pManufacturer = famMgr.get_Parameter("Manufacturer");

if (pManufacturer != null && pManufacturer.StorageType == StorageType.String)
{
    famMgr.Set(pManufacturer, "Acme Corp");
}""",
        ))

        # Count types
        samples.append(_s(
            "Get the total number of family types defined in a family document",
            """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
int typeCount = famMgr.Types.Size;
// typeCount is the number of types in the family""",
        ))

        # Add parameter and set per-type values
        samples.append(_s(
            "Add a 'Frame Width' length parameter and set different values on each of three types",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;

// Add parameter OUTSIDE transaction
FamilyParameter pFrame = famMgr.AddParameter(
    "Frame Width",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length,
    false); // type parameter

// Set values per type
var perType = new (string TypeName, double FrameMm)[]
{{
    ("Small",  45.0),
    ("Medium", 60.0),
    ("Large",  75.0),
}};

foreach (var entry in perType)
{{
    FamilyType ft = famMgr.Types
        .Cast<FamilyType>()
        .FirstOrDefault(t => t.Name == entry.TypeName);
    if (ft != null)
    {{
        famMgr.CurrentType = ft;
        famMgr.Set(pFrame, entry.FrameMm * {MM_TO_FT:.6f}); // convert mm to ft
    }}
}}""",
        ))

        # Add instance Number parameter
        samples.append(_s(
            "Add an instance 'Weight' number parameter to a structural family and set a default value",
            """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;

// Add a dimensionless Number parameter as an instance parameter
FamilyParameter pWeight = famMgr.AddParameter(
    "Weight",
    BuiltInParameterGroup.PG_STRUCTURAL,
    ParameterType.Number,
    true); // instance = true

famMgr.Set(pWeight, 22.0); // kg/m, stored as plain number""",
        ))

        # RemoveParameter
        samples.append(_s(
            "Remove a family parameter named 'Obsolete Param' from the family manager",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter toRemove = famMgr.Parameters
    .Cast<FamilyParameter>()
    .FirstOrDefault(p => p.Definition.Name == "Obsolete Param");

if (toRemove != null)
    famMgr.RemoveParameter(toRemove);""",
        ))

        # Set formula on a type parameter
        samples.append(_s(
            "Set a formula on the 'Depth' parameter so it always equals half the 'Width' parameter",
            """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pDepth = famMgr.get_Parameter("Depth");

if (pDepth != null)
    famMgr.SetFormula(pDepth, "Width / 2");
// Revit will now drive Depth from Width across all types""",
        ))

        # Clear formula
        samples.append(_s(
            "Clear an existing formula from the 'Height' parameter so its value can be set independently",
            """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pHeight = famMgr.get_Parameter("Height");

if (pHeight != null)
    famMgr.SetFormula(pHeight, null); // null removes the formula""",
        ))

        # IsReadOnly check
        samples.append(_s(
            "Check whether the 'Width' parameter is read-only (driven by a formula) before attempting to set it",
            """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth = famMgr.get_Parameter("Width");

if (pWidth != null && !pWidth.IsDetermined)
{
    // IsDetermined == true means formula-driven -- cannot set directly
    famMgr.Set(pWidth, 0.984252); // 300 mm
}
else
{
    // Parameter is formula-driven; change the formula instead
    // famMgr.SetFormula(pWidth, "Height / 2");
}""",
        ))

        # Reporting parameter types
        samples.append(_s(
            "List all family parameters and their storage type (Double, Integer, String, ElementId)",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

FamilyManager famMgr = familyDoc.FamilyManager;
var paramInfo = new List<(string Name, StorageType Type, bool IsInstance)>();

foreach (FamilyParameter fp in famMgr.Parameters)
{
    paramInfo.Add((
        fp.Definition.Name,
        fp.StorageType,
        fp.IsInstance));
}
// paramInfo contains (Name, StorageType, IsInstance) for each parameter""",
        ))

        # Create type with formula-driven height
        samples.append(_s(
            "Create a 'Proportional' door type where Height is always 2.33 times the Width via formula",
            f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;

// Ensure Width and Height parameters exist
FamilyParameter pWidth  = famMgr.get_Parameter("Width")
    ?? famMgr.AddParameter("Width",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pHeight = famMgr.get_Parameter("Height")
    ?? famMgr.AddParameter("Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

// Create the type
FamilyType proportional = famMgr.NewType("Proportional");

// Set Width first (Height is formula-driven)
famMgr.Set(pWidth, {900 * MM_TO_FT:.6f}); // 900 mm

// Drive Height from Width
famMgr.SetFormula(pHeight, "Width * 2.33");
// Height will be 2097 mm when Width = 900 mm""",
        ))

        # Set angle parameter
        samples.append(_s(
            "Add an 'Opening Angle' parameter to a door family and set it to 90 degrees on the current type",
            """\
using Autodesk.Revit.DB;
using System;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pAngle = famMgr.AddParameter(
    "Opening Angle",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Angle,
    true); // instance parameter

// Revit stores angles in radians internally
double angleDeg = 90.0;
double angleRad = angleDeg * Math.PI / 180.0; // = 1.5707963...
famMgr.Set(pAngle, angleRad);""",
        ))

        # Enumerate types with AsValueString
        samples.append(_s(
            "For each family type, use AsValueString to get a human-readable formatted Width value",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth = famMgr.get_Parameter("Width");

var widthStrings = new Dictionary<string, string>();
foreach (FamilyType ft in famMgr.Types)
{
    famMgr.CurrentType = ft;
    if (pWidth != null)
    {
        // AsValueString returns the value formatted in the document's display units
        string displayVal = ft.AsValueString(pWidth);
        widthStrings[ft.Name] = displayVal ?? "N/A";
    }
}""",
        ))

        # MakeType vs MakeInstance
        samples.append(_s(
            "Convert an instance parameter 'Clearance' to a type parameter using MakeType",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pClearance = famMgr.Parameters
    .Cast<FamilyParameter>()
    .FirstOrDefault(p => p.Definition.Name == "Clearance");

if (pClearance != null && pClearance.IsInstance)
    famMgr.MakeType(pClearance);
// Parameter is now type-level -- one value shared across all instances of a type""",
        ))

        # MakeInstance
        samples.append(_s(
            "Convert a type parameter 'Offset' to an instance parameter using MakeInstance",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pOffset = famMgr.Parameters
    .Cast<FamilyParameter>()
    .FirstOrDefault(p => p.Definition.Name == "Offset");

if (pOffset != null && !pOffset.IsInstance)
    famMgr.MakeInstance(pOffset);
// Each placed instance can now have a different Offset value""",
        ))

        # Add reporting parameter
        samples.append(_s(
            "Add a reporting parameter 'Computed Area' that reports the product of Width and Depth",
            """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;

// Reporting parameters are read-only and driven by a formula
FamilyParameter pArea = famMgr.AddParameter(
    "Computed Area",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Area,
    false); // type parameter

famMgr.SetFormula(pArea, "Width * Depth");
// Value is recomputed by Revit whenever Width or Depth changes""",
        ))

        # Set value in all types at once (bulk update)
        samples.append(_s(
            "Set the 'Fire Rating' text parameter to '60 min' on all family types at once",
            """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pFireRating = famMgr.get_Parameter("Fire Rating");

if (pFireRating != null && pFireRating.StorageType == StorageType.String)
{
    foreach (FamilyType ft in famMgr.Types)
    {
        famMgr.CurrentType = ft;
        famMgr.Set(pFireRating, "60 min");
    }
}""",
        ))

        # Get BuiltInParameter equivalent
        samples.append(_s(
            "Look up the Revit built-in parameter that corresponds to a family parameter by its definition name",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;

foreach (FamilyParameter fp in famMgr.Parameters)
{
    // BuiltInParameter is available for built-in params; custom ones return INVALID
    InternalDefinition intDef = fp.Definition as InternalDefinition;
    if (intDef != null)
    {
        BuiltInParameter bip = intDef.BuiltInParameter;
        bool isBuiltIn = bip != BuiltInParameter.INVALID;
    }
}""",
        ))

        # Verify type names are unique
        samples.append(_s(
            "Verify that all family type names are unique and report any duplicates",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
var names = famMgr.Types.Cast<FamilyType>().Select(t => t.Name).ToList();
var duplicates = names
    .GroupBy(n => n)
    .Where(g => g.Count() > 1)
    .Select(g => g.Key)
    .ToList();
// duplicates is empty for a valid family -- Revit enforces uniqueness anyway""",
        ))

        # Bulk-create structured column types
        col_types = [
            ("250x250", 250, 250),
            ("300x300", 300, 300),
            ("350x350", 350, 350),
            ("400x400", 400, 400),
            ("450x450", 450, 450),
            ("500x500", 500, 500),
        ]
        col_entries = "\n    ".join(
            f'("{n}", {w * MM_TO_FT:.6f}, {d * MM_TO_FT:.6f}),' for n, w, d in col_types
        )
        samples.append(_s(
            "Create six concrete column types ranging from 250x250mm to 500x500mm",
            f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth = famMgr.get_Parameter("b");
FamilyParameter pDepth = famMgr.get_Parameter("d");

var colDefs = new (string Name, double WidthFt, double DepthFt)[]
{{
    {col_entries}
}};

foreach (var col in colDefs)
{{
    FamilyType ft = famMgr.NewType(col.Name);
    if (pWidth != null) famMgr.Set(pWidth, col.WidthFt);
    if (pDepth != null) famMgr.Set(pDepth, col.DepthFt);
}}""",
        ))

        # Print type summary table
        samples.append(_s(
            "Build a summary report (list of strings) showing each type name, width, height, and area",
            f"""\
using Autodesk.Revit.DB;
using System.Collections.Generic;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW = famMgr.get_Parameter("Width");
FamilyParameter pH = famMgr.get_Parameter("Height");

var report = new List<string> {{ "Type,Width(mm),Height(mm),Area(m2)" }};
foreach (FamilyType ft in famMgr.Types)
{{
    famMgr.CurrentType = ft;
    double wMm = pW != null ? ft.AsDouble(pW) * 304.8 : 0;
    double hMm = pH != null ? ft.AsDouble(pH) * 304.8 : 0;
    double areM2 = wMm * hMm / 1e6;
    report.Add($"{{ft.Name}},{{wMm:F0}},{{hMm:F0}},{{areM2:F4}}");
}}""",
        ))

        # Copy type values between documents
        samples.append(_s(
            "Copy type parameter values from a source family type to a matching type in a second family document",
            """\
using Autodesk.Revit.DB;
using System.Linq;

// Source: copy Width and Height from 'Standard' in sourceFamilyDoc
// Target: paste into 'Standard' in targetFamilyDoc

FamilyManager srcMgr = sourceFamilyDoc.FamilyManager;
FamilyManager tgtMgr = targetFamilyDoc.FamilyManager;

FamilyType srcType = srcMgr.Types.Cast<FamilyType>().FirstOrDefault(t => t.Name == "Standard");
FamilyType tgtType = tgtMgr.Types.Cast<FamilyType>().FirstOrDefault(t => t.Name == "Standard");

if (srcType != null && tgtType != null)
{
    srcMgr.CurrentType = srcType;
    tgtMgr.CurrentType = tgtType;

    FamilyParameter srcW = srcMgr.get_Parameter("Width");
    FamilyParameter tgtW = tgtMgr.get_Parameter("Width");
    if (srcW != null && tgtW != null)
        tgtMgr.Set(tgtW, srcType.AsDouble(srcW));

    FamilyParameter srcH = srcMgr.get_Parameter("Height");
    FamilyParameter tgtH = tgtMgr.get_Parameter("Height");
    if (srcH != null && tgtH != null)
        tgtMgr.Set(tgtH, srcType.AsDouble(srcH));
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # Type catalog CSV authoring (~50 samples)
    # ------------------------------------------------------------------

    def _type_catalog_csv(self) -> List[SAMPLE]:
        samples = []

        # --- Doors ---
        door_types = [
            ("Single-Flush-610x2032",  610,  38, 2032),
            ("Single-Flush-762x2032",  762,  38, 2032),
            ("Single-Flush-914x2032",  914,  38, 2032),
            ("Single-Flush-914x2134",  914,  38, 2134),
            ("Single-Flush-1067x2134", 1067, 44, 2134),
        ]
        door_csv_rows = "\n".join(
            f"{n},{w * MM_TO_FT:.6f},{d * MM_TO_FT:.6f},{h * MM_TO_FT:.6f}"
            for n, w, d, h in door_types
        )
        samples.append(_s(
            "Write a type catalog CSV file for a single-flush door family with five sizes",
            f"""\
##Type Name,Width##LENGTH##MILLIMETERS,Thickness##LENGTH##MILLIMETERS,Height##LENGTH##MILLIMETERS
{door_csv_rows}

// Type catalog rules:
// 1. First row is the header: ##Type Name followed by param##TYPE##UNIT columns
// 2. LENGTH parameters are stored in feet internally -- values in the CSV are in the
//    unit specified in the header (MILLIMETERS here), Revit converts on import
// 3. Save file as <FamilyName>.txt alongside the .rfa file
// 4. On load, Revit shows the type catalog dialog for the user to select types""",
        ))

        # --- Windows ---
        window_types = [
            ("Fixed-600x900",   600,  900,  50),
            ("Fixed-900x1200",  900,  1200, 50),
            ("Fixed-1200x1500", 1200, 1500, 65),
            ("Fixed-1500x1800", 1500, 1800, 65),
            ("Fixed-1800x2100", 1800, 2100, 75),
        ]
        window_csv_rows = "\n".join(
            f"{n},{w * MM_TO_FT:.6f},{h * MM_TO_FT:.6f},{fr * MM_TO_FT:.6f}"
            for n, w, h, fr in window_types
        )
        samples.append(_s(
            "Write a type catalog CSV for a fixed window family with five width/height combinations",
            f"""\
##Type Name,Width##LENGTH##MILLIMETERS,Height##LENGTH##MILLIMETERS,Frame Width##LENGTH##MILLIMETERS
{window_csv_rows}""",
        ))

        # --- Structural columns (W-sections) ---
        column_types = [
            ("W150x13",  152, 152, 8.9,  7.6),
            ("W200x22",  206, 166, 9.1,  6.4),
            ("W250x33",  259, 254, 9.7,  6.1),
            ("W310x45",  313, 166, 11.2, 6.9),
            ("W360x57",  358, 172, 13.1, 7.9),
            ("W410x75",  409, 179, 16.0, 9.4),
        ]
        col_csv_rows = "\n".join(
            f"{n},{d * MM_TO_FT:.6f},{bf * MM_TO_FT:.6f},{tf * MM_TO_FT:.6f},{tw * MM_TO_FT:.6f}"
            for n, d, bf, tf, tw in column_types
        )
        samples.append(_s(
            "Write a type catalog CSV for W-section structural columns covering W150 through W410",
            f"""\
##Type Name,d##LENGTH##MILLIMETERS,bf##LENGTH##MILLIMETERS,tf##LENGTH##MILLIMETERS,tw##LENGTH##MILLIMETERS
{col_csv_rows}

// d  = overall depth
// bf = flange width
// tf = flange thickness
// tw = web thickness""",
        ))

        # --- Steel beams (W-sections) ---
        beam_types = [
            ("W200x46",  203, 203, 11.0, 7.2),
            ("W250x58",  252, 203, 13.5, 8.0),
            ("W310x74",  310, 205, 16.3, 9.4),
            ("W360x91",  353, 254, 16.4, 9.8),
            ("W410x100", 415, 260, 17.2, 10.0),
        ]
        beam_csv_rows = "\n".join(
            f"{n},{d * MM_TO_FT:.6f},{bf * MM_TO_FT:.6f},{tf * MM_TO_FT:.6f},{tw * MM_TO_FT:.6f}"
            for n, d, bf, tf, tw in beam_types
        )
        samples.append(_s(
            "Write a type catalog CSV for W-section steel beams with depth, flange width, and thickness columns",
            f"""\
##Type Name,Depth##LENGTH##MILLIMETERS,Flange Width##LENGTH##MILLIMETERS,Flange Thickness##LENGTH##MILLIMETERS,Web Thickness##LENGTH##MILLIMETERS
{beam_csv_rows}""",
        ))

        # --- Pipes ---
        pipe_types = [
            ("DN15",  15,  21.3, 2.77),
            ("DN20",  20,  26.9, 2.87),
            ("DN25",  25,  33.7, 3.25),
            ("DN32",  32,  42.4, 3.25),
            ("DN40",  40,  48.3, 3.25),
            ("DN50",  50,  60.3, 3.65),
            ("DN65",  65,  76.1, 3.65),
            ("DN80",  80,  88.9, 4.05),
            ("DN100", 100, 114.3, 4.50),
        ]
        pipe_csv_rows = "\n".join(
            f"{n},{od * MM_TO_FT:.6f},{wt * MM_TO_FT:.6f}"
            for n, _, od, wt in pipe_types
        )
        samples.append(_s(
            "Write a type catalog CSV for a circular pipe family covering DN15 through DN100",
            f"""\
##Type Name,Outer Diameter##LENGTH##MILLIMETERS,Wall Thickness##LENGTH##MILLIMETERS
{pipe_csv_rows}

// Nominal bore is not a geometric parameter -- encode it in the type name (DNxx)
// Outer Diameter and Wall Thickness drive the extrusion and void profiles""",
        ))

        # --- Rectangular HSS columns ---
        hss_types = [
            ("HSS100x100x5",  100, 100, 5),
            ("HSS150x150x6",  150, 150, 6),
            ("HSS150x100x5",  150, 100, 5),
            ("HSS200x200x8",  200, 200, 8),
            ("HSS200x150x6",  200, 150, 6),
            ("HSS250x250x10", 250, 250, 10),
        ]
        hss_csv_rows = "\n".join(
            f"{n},{h * MM_TO_FT:.6f},{w * MM_TO_FT:.6f},{t * MM_TO_FT:.6f}"
            for n, h, w, t in hss_types
        )
        samples.append(_s(
            "Write a type catalog CSV for a rectangular hollow structural section (HSS) column family",
            f"""\
##Type Name,Depth##LENGTH##MILLIMETERS,Width##LENGTH##MILLIMETERS,Wall Thickness##LENGTH##MILLIMETERS
{hss_csv_rows}""",
        ))

        # --- Angle sections ---
        angle_types = [
            ("L75x75x6",   75,  75,  6),
            ("L100x100x8", 100, 100, 8),
            ("L100x75x8",  100, 75,  8),
            ("L150x100x10",150, 100, 10),
            ("L150x150x12",150, 150, 12),
        ]
        angle_csv_rows = "\n".join(
            f"{n},{a * MM_TO_FT:.6f},{b * MM_TO_FT:.6f},{t * MM_TO_FT:.6f}"
            for n, a, b, t in angle_types
        )
        samples.append(_s(
            "Write a type catalog CSV for a structural angle (L-section) family",
            f"""\
##Type Name,Leg A##LENGTH##MILLIMETERS,Leg B##LENGTH##MILLIMETERS,Thickness##LENGTH##MILLIMETERS
{angle_csv_rows}""",
        ))

        # --- Channel sections ---
        channel_types = [
            ("C100x11", 100, 50,  6.5, 4.5),
            ("C150x19", 152, 64,  9.2, 5.1),
            ("C200x28", 203, 76, 11.2, 5.7),
            ("C230x30", 229, 76, 11.0, 5.5),
            ("C250x37", 254, 76, 12.4, 7.4),
        ]
        channel_csv_rows = "\n".join(
            f"{n},{d * MM_TO_FT:.6f},{bf * MM_TO_FT:.6f},{tf * MM_TO_FT:.6f},{tw * MM_TO_FT:.6f}"
            for n, d, bf, tf, tw in channel_types
        )
        samples.append(_s(
            "Write a type catalog CSV for a C-channel (MC-section) structural family",
            f"""\
##Type Name,Depth##LENGTH##MILLIMETERS,Flange Width##LENGTH##MILLIMETERS,Flange Thickness##LENGTH##MILLIMETERS,Web Thickness##LENGTH##MILLIMETERS
{channel_csv_rows}""",
        ))

        # Header-only explanation sample
        samples.append(_s(
            "Explain the type catalog CSV header format and the three supported unit keywords",
            """\
// Type catalog CSV header format:
//   ##Type Name,<ParamName>##<DataType>##<Units>[,...]
//
// Supported DataTypes:
//   LENGTH   -- linear dimension (feet internally; display unit in Units column)
//   ANGLE    -- angular value (radians internally)
//   NUMBER   -- dimensionless real number
//   INTEGER  -- whole number
//   YES/NO   -- boolean (0 or 1)
//   TEXT     -- string value
//
// Common Units for LENGTH:
//   MILLIMETERS, CENTIMETERS, METERS, INCHES, FEET, FRACTIONAL_INCHES
//
// Example header:
//   ##Type Name,Width##LENGTH##MILLIMETERS,Height##LENGTH##MILLIMETERS
//
// Revit converts the CSV values from the stated unit to internal feet on import.
// The file must be saved as <FamilyName>.txt in the same folder as the .rfa file.""",
        ))

        # Type catalog with Yes/No column
        samples.append(_s(
            "Write a type catalog CSV for a door family that includes a 'Has Sidelight' Yes/No column",
            f"""\
##Type Name,Width##LENGTH##MILLIMETERS,Height##LENGTH##MILLIMETERS,Has Sidelight##YES/NO
Single-762-NoSide,{762 * MM_TO_FT:.6f},{2032 * MM_TO_FT:.6f},0
Single-762-Side,{762 * MM_TO_FT:.6f},{2032 * MM_TO_FT:.6f},1
Single-914-NoSide,{914 * MM_TO_FT:.6f},{2134 * MM_TO_FT:.6f},0
Single-914-Side,{914 * MM_TO_FT:.6f},{2134 * MM_TO_FT:.6f},1

// YES/NO columns use 0 (false) or 1 (true)""",
        ))

        # Type catalog with NUMBER column (weight lookup)
        samples.append(_s(
            "Write a type catalog CSV for a steel column family that includes a mass-per-length NUMBER column",
            f"""\
##Type Name,Depth##LENGTH##MILLIMETERS,Flange Width##LENGTH##MILLIMETERS,Mass Per Length##NUMBER
W150x13,{152 * MM_TO_FT:.6f},{152 * MM_TO_FT:.6f},13.0
W200x22,{206 * MM_TO_FT:.6f},{166 * MM_TO_FT:.6f},22.0
W250x33,{259 * MM_TO_FT:.6f},{254 * MM_TO_FT:.6f},33.0
W310x45,{313 * MM_TO_FT:.6f},{166 * MM_TO_FT:.6f},45.0

// NUMBER columns are dimensionless -- store kg/m directly as a real number""",
        ))

        # Loading a type catalog family programmatically
        samples.append(_s(
            "Load a family that has a type catalog and select specific types to load into the project",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

// IFamilyLoadOptions lets you control overwrite behaviour
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
}

// Load with type filter (type catalog dialog suppressed -- all types loaded)
using (Transaction tx = new Transaction(doc, "Load Door Family"))
{
    tx.Start();

    string path = @"C:\Families\Doors\Single-Flush.rfa";
    Family loadedFamily;
    doc.LoadFamily(path, new FamilyLoadOptions(), out loadedFamily);

    tx.Commit();
}""",
        ))

        # Generating catalog programmatically from C#
        samples.append(_s(
            "Generate a type catalog CSV file programmatically in C# for a parametric pipe fitting family",
            """\
using System;
using System.IO;
using System.Text;

// Generate type catalog CSV for a pipe fitting
string familyPath = @"C:\\Families\\Pipe\\Elbow-90.rfa";
string catalogPath = Path.ChangeExtension(familyPath, ".txt");

var sb = new StringBuilder();
sb.AppendLine("##Type Name,Outer Diameter##LENGTH##MILLIMETERS,Wall Thickness##LENGTH##MILLIMETERS");

// DN15 through DN100
var sizes = new (string Name, double OD, double WT)[]
{
    ("DN15",  21.3, 2.77),
    ("DN20",  26.9, 2.87),
    ("DN25",  33.7, 3.25),
    ("DN32",  42.4, 3.25),
    ("DN40",  48.3, 3.25),
    ("DN50",  60.3, 3.65),
    ("DN80",  88.9, 4.05),
    ("DN100", 114.3, 4.50),
};

foreach (var s in sizes)
{
    // Values in mm -- Revit converts on import per the MILLIMETERS header unit
    double odFt = s.OD / 304.8;
    double wtFt = s.WT / 304.8;
    sb.AppendLine($"{s.Name},{odFt:F6},{wtFt:F6}");
}

File.WriteAllText(catalogPath, sb.ToString(), Encoding.UTF8);""",
        ))

        # Catalog with ANGLE column
        samples.append(_s(
            "Write a type catalog CSV for a pipe elbow family with a bend angle column",
            f"""\
##Type Name,Outer Diameter##LENGTH##MILLIMETERS,Bend Angle##ANGLE
Elbow-90-DN25,{33.7 * MM_TO_FT:.6f},1.570796
Elbow-90-DN50,{60.3 * MM_TO_FT:.6f},1.570796
Elbow-45-DN25,{33.7 * MM_TO_FT:.6f},0.785398
Elbow-45-DN50,{60.3 * MM_TO_FT:.6f},0.785398

// ANGLE values are in radians (90 deg = pi/2 = 1.570796, 45 deg = pi/4 = 0.785398)""",
        ))

        # Catalog with mixed types
        samples.append(_s(
            "Write a type catalog CSV for an adjustable shelf family with width, depth, and thickness columns",
            f"""\
##Type Name,Width##LENGTH##MILLIMETERS,Depth##LENGTH##MILLIMETERS,Thickness##LENGTH##MILLIMETERS
Shelf-600x300x18,{600 * MM_TO_FT:.6f},{300 * MM_TO_FT:.6f},{18 * MM_TO_FT:.6f}
Shelf-800x300x18,{800 * MM_TO_FT:.6f},{300 * MM_TO_FT:.6f},{18 * MM_TO_FT:.6f}
Shelf-900x350x22,{900 * MM_TO_FT:.6f},{350 * MM_TO_FT:.6f},{22 * MM_TO_FT:.6f}
Shelf-1200x350x22,{1200 * MM_TO_FT:.6f},{350 * MM_TO_FT:.6f},{22 * MM_TO_FT:.6f}
Shelf-1500x400x25,{1500 * MM_TO_FT:.6f},{400 * MM_TO_FT:.6f},{25 * MM_TO_FT:.6f}""",
        ))

        # Stair riser catalog
        samples.append(_s(
            "Write a type catalog CSV for a stair component family with riser height and tread depth",
            f"""\
##Type Name,Riser Height##LENGTH##MILLIMETERS,Tread Depth##LENGTH##MILLIMETERS
Stair-150x280,{150 * MM_TO_FT:.6f},{280 * MM_TO_FT:.6f}
Stair-163x280,{163 * MM_TO_FT:.6f},{280 * MM_TO_FT:.6f}
Stair-175x250,{175 * MM_TO_FT:.6f},{250 * MM_TO_FT:.6f}
Stair-190x230,{190 * MM_TO_FT:.6f},{230 * MM_TO_FT:.6f}

// IBC: riser 100-190mm, tread >= 280mm (residential: 165-200mm riser)""",
        ))

        # Explain file placement rules
        samples.append(_s(
            "Explain where to place a type catalog file relative to the .rfa file and how Revit discovers it",
            """\
// Type catalog file placement rules:
//
// 1. The catalog file MUST have the same base name as the family:
//      MyDoor.rfa  -->  MyDoor.txt  (same folder)
//
// 2. Revit automatically detects the .txt file when loading the .rfa via:
//      - The UI (Insert > Load Family)
//      - LoadFamily() API call
//    If found, the type catalog dialog appears (UI) or all types are loaded (API).
//
// 3. When distributing families, always bundle the .txt alongside the .rfa.
//
// 4. To suppress the dialog and load all types programmatically:
//      Family fam;
//      doc.LoadFamily(rfaPath, new SilentFamilyLoadOptions(), out fam);
//
// 5. After loading, enumerate FamilySymbol objects to access individual types:
//      foreach (ElementId id in fam.GetFamilySymbolIds()) { ... }""",
        ))

        # Column schedule with TEXT column
        samples.append(_s(
            "Write a type catalog CSV for a column family that includes a 'Grade' text column for material grade",
            f"""\
##Type Name,Depth##LENGTH##MILLIMETERS,Width##LENGTH##MILLIMETERS,Grade##TEXT
COL-200x200-A36,{200 * MM_TO_FT:.6f},{200 * MM_TO_FT:.6f},A36
COL-200x200-A572,{200 * MM_TO_FT:.6f},{200 * MM_TO_FT:.6f},A572 Gr50
COL-300x300-A36,{300 * MM_TO_FT:.6f},{300 * MM_TO_FT:.6f},A36
COL-300x300-A572,{300 * MM_TO_FT:.6f},{300 * MM_TO_FT:.6f},A572 Gr50

// TEXT columns map to String FamilyParameters; use them for non-numeric attributes""",
        ))

        # T-section catalog
        t_types = [
            ("T100x50x5",  100, 50,  5),
            ("T150x75x6",  150, 75,  6),
            ("T200x100x8", 200, 100, 8),
            ("T250x125x10",250, 125, 10),
        ]
        t_csv = "\n".join(
            f"{n},{h * MM_TO_FT:.6f},{bf * MM_TO_FT:.6f},{tw * MM_TO_FT:.6f}"
            for n, h, bf, tw in t_types
        )
        samples.append(_s(
            "Write a type catalog CSV for a T-section structural family",
            f"""\
##Type Name,Depth##LENGTH##MILLIMETERS,Flange Width##LENGTH##MILLIMETERS,Web Thickness##LENGTH##MILLIMETERS
{t_csv}""",
        ))

        # Round tube catalog
        tube_types = [
            ("CHS48x3",  48.3, 3.0),
            ("CHS60x4",  60.3, 4.0),
            ("CHS76x4",  76.1, 4.0),
            ("CHS89x5",  88.9, 5.0),
            ("CHS114x5", 114.3, 5.0),
        ]
        tube_csv = "\n".join(
            f"{n},{od * MM_TO_FT:.6f},{wt * MM_TO_FT:.6f}"
            for n, od, wt in tube_types
        )
        samples.append(_s(
            "Write a type catalog CSV for a circular hollow section (CHS) structural family",
            f"""\
##Type Name,Outer Diameter##LENGTH##MILLIMETERS,Wall Thickness##LENGTH##MILLIMETERS
{tube_csv}""",
        ))

        # Floor / slab thickness catalog
        slab_types = [
            ("Slab-100mm", 100),
            ("Slab-150mm", 150),
            ("Slab-200mm", 200),
            ("Slab-250mm", 250),
            ("Slab-300mm", 300),
        ]
        slab_csv = "\n".join(
            f"{n},{t * MM_TO_FT:.6f}" for n, t in slab_types
        )
        samples.append(_s(
            "Write a type catalog CSV for a structural slab family with a single Thickness parameter",
            f"""\
##Type Name,Thickness##LENGTH##MILLIMETERS
{slab_csv}""",
        ))

        # Cabinet with width/height/depth
        cab_types = [
            ("Base-300",  300, 720, 580),
            ("Base-400",  400, 720, 580),
            ("Base-500",  500, 720, 580),
            ("Base-600",  600, 720, 580),
            ("Base-800",  800, 720, 580),
            ("Base-1000", 1000, 720, 580),
        ]
        cab_csv = "\n".join(
            f"{n},{w * MM_TO_FT:.6f},{h * MM_TO_FT:.6f},{d * MM_TO_FT:.6f}"
            for n, w, h, d in cab_types
        )
        samples.append(_s(
            "Write a type catalog CSV for a base cabinet family with Width, Height, and Depth",
            f"""\
##Type Name,Width##LENGTH##MILLIMETERS,Height##LENGTH##MILLIMETERS,Depth##LENGTH##MILLIMETERS
{cab_csv}""",
        ))

        # Wall cabinet
        wcab_types = [
            ("Wall-300x600",  300, 600, 320),
            ("Wall-400x600",  400, 600, 320),
            ("Wall-600x600",  600, 600, 320),
            ("Wall-600x900",  600, 900, 320),
            ("Wall-900x900",  900, 900, 320),
        ]
        wcab_csv = "\n".join(
            f"{n},{w * MM_TO_FT:.6f},{h * MM_TO_FT:.6f},{d * MM_TO_FT:.6f}"
            for n, w, h, d in wcab_types
        )
        samples.append(_s(
            "Write a type catalog CSV for a wall-hung cabinet family",
            f"""\
##Type Name,Width##LENGTH##MILLIMETERS,Height##LENGTH##MILLIMETERS,Depth##LENGTH##MILLIMETERS
{wcab_csv}""",
        ))

        # Duct rectangular
        duct_types = [
            ("200x100", 200, 100),
            ("300x150", 300, 150),
            ("400x200", 400, 200),
            ("500x250", 500, 250),
            ("600x300", 600, 300),
            ("800x400", 800, 400),
        ]
        duct_csv = "\n".join(
            f"{n},{w * MM_TO_FT:.6f},{h * MM_TO_FT:.6f}"
            for n, w, h in duct_types
        )
        samples.append(_s(
            "Write a type catalog CSV for a rectangular duct fitting family",
            f"""\
##Type Name,Width##LENGTH##MILLIMETERS,Height##LENGTH##MILLIMETERS
{duct_csv}""",
        ))

        # Conduit
        conduit_types = [
            ("Conduit-20mm",  20,  1.2),
            ("Conduit-25mm",  25,  1.4),
            ("Conduit-32mm",  32,  1.6),
            ("Conduit-40mm",  40,  1.8),
            ("Conduit-50mm",  50,  2.0),
        ]
        conduit_csv = "\n".join(
            f"{n},{od * MM_TO_FT:.6f},{wt * MM_TO_FT:.6f}"
            for n, od, wt in conduit_types
        )
        samples.append(_s(
            "Write a type catalog CSV for an electrical conduit family",
            f"""\
##Type Name,Outer Diameter##LENGTH##MILLIMETERS,Wall Thickness##LENGTH##MILLIMETERS
{conduit_csv}""",
        ))

        # Rebar sizes
        rebar_types = [
            ("N10", 11.3, 100),
            ("N12", 13.0, 113),
            ("N16", 17.9, 200),
            ("N20", 22.2, 314),
            ("N24", 26.4, 452),
            ("N28", 30.9, 616),
            ("N32", 35.7, 804),
        ]
        rebar_csv = "\n".join(
            f"{n},{od * MM_TO_FT:.6f},{area}" for n, od, area in rebar_types
        )
        samples.append(_s(
            "Write a type catalog CSV for a rebar family with nominal diameter and cross-sectional area",
            f"""\
##Type Name,Bar Diameter##LENGTH##MILLIMETERS,Cross Section Area##NUMBER
{rebar_csv}

// Cross Section Area stored as NUMBER (mm2) -- dimensionless in Revit""",
        ))

        # Explain INTEGER column
        samples.append(_s(
            "Write a type catalog CSV for a modular shelving unit that includes an 'Shelf Count' INTEGER column",
            f"""\
##Type Name,Width##LENGTH##MILLIMETERS,Height##LENGTH##MILLIMETERS,Shelf Count##INTEGER
Unit-600-3,{600 * MM_TO_FT:.6f},{900 * MM_TO_FT:.6f},3
Unit-600-4,{600 * MM_TO_FT:.6f},{1200 * MM_TO_FT:.6f},4
Unit-900-4,{900 * MM_TO_FT:.6f},{1200 * MM_TO_FT:.6f},4
Unit-900-5,{900 * MM_TO_FT:.6f},{1500 * MM_TO_FT:.6f},5

// INTEGER columns map to integer FamilyParameters (whole numbers only)""",
        ))

        # Precast panel
        panel_types = [
            ("Panel-600x2400",  600,  2400, 200),
            ("Panel-900x2400",  900,  2400, 200),
            ("Panel-1200x2400", 1200, 2400, 250),
            ("Panel-1200x3000", 1200, 3000, 250),
            ("Panel-1500x3000", 1500, 3000, 300),
        ]
        panel_csv = "\n".join(
            f"{n},{w * MM_TO_FT:.6f},{h * MM_TO_FT:.6f},{t * MM_TO_FT:.6f}"
            for n, w, h, t in panel_types
        )
        samples.append(_s(
            "Write a type catalog CSV for a precast concrete wall panel family",
            f"""\
##Type Name,Width##LENGTH##MILLIMETERS,Height##LENGTH##MILLIMETERS,Thickness##LENGTH##MILLIMETERS
{panel_csv}""",
        ))

        # Gutter section
        gutter_types = [
            ("Gutter-100x75",  100, 75,  3),
            ("Gutter-125x100", 125, 100, 3),
            ("Gutter-150x100", 150, 100, 4),
            ("Gutter-200x150", 200, 150, 4),
        ]
        gutter_csv = "\n".join(
            f"{n},{w * MM_TO_FT:.6f},{h * MM_TO_FT:.6f},{t * MM_TO_FT:.6f}"
            for n, w, h, t in gutter_types
        )
        samples.append(_s(
            "Write a type catalog CSV for a rectangular gutter/trunking family",
            f"""\
##Type Name,Width##LENGTH##MILLIMETERS,Height##LENGTH##MILLIMETERS,Thickness##LENGTH##MILLIMETERS
{gutter_csv}""",
        ))

        # Explain loading in C# with type name filter
        samples.append(_s(
            "Load only the types named 'DN50' and 'DN100' from a pipe family type catalog using LoadFamilySymbol",
            """\
using Autodesk.Revit.DB;

string rfaPath = @"C:\\Families\\Pipes\\Circular-Pipe.rfa";
var loadOptions = new OverwriteFamilyLoadOptions();

using (Transaction tx = new Transaction(doc, "Load Pipe Symbols"))
{
    tx.Start();

    // LoadFamilySymbol loads one type by name from the catalog
    FamilySymbol dn50, dn100;
    doc.LoadFamilySymbol(rfaPath, "DN50",  loadOptions, out dn50);
    doc.LoadFamilySymbol(rfaPath, "DN100", loadOptions, out dn100);

    if (dn50  != null && !dn50.IsActive)  dn50.Activate();
    if (dn100 != null && !dn100.IsActive) dn100.Activate();

    tx.Commit();
}""",
        ))

        # Catalog validation: explain what happens with mismatched values
        samples.append(_s(
            "Explain what Revit does when a type catalog value cannot be converted to the declared unit",
            """\
// When Revit parses a type catalog file it expects each data column value to be
// a valid floating-point number (or integer/string for those types).
//
// If a value is blank or non-numeric for a LENGTH/ANGLE/NUMBER column:
//   - Revit silently skips that type during import (it does not appear in the dialog)
//   - No error is thrown to the API caller
//
// Best practice: validate before writing
//   1. All LENGTH values must be positive reals.
//   2. TEXT values must not contain commas (they would break CSV parsing) -- use
//      semicolons or quotes if needed.
//   3. YES/NO values must be exactly 0 or 1.
//   4. INTEGER values must parse as Int32.
//
// Use a helper to pre-validate:
foreach (var row in catalogRows)
{
    if (row.Width <= 0 || row.Height <= 0)
        throw new InvalidOperationException($"Invalid dimensions for type {row.Name}");
}""",
        ))

        # Catalog with feet values (US imperial)
        samples.append(_s(
            "Write a type catalog CSV for a door family using FEET as the unit (US Imperial project)",
            """\
##Type Name,Width##LENGTH##FEET,Height##LENGTH##FEET
2-6x6-8,0.666667,6.666667
2-8x6-8,0.750000,6.666667
3-0x6-8,0.833333,6.666667
3-0x7-0,0.833333,7.000000
3-6x7-0,0.875000,7.000000

// FEET unit: values are already in internal Revit units (no conversion needed on import)""",
        ))

        # Catalog with METERS
        samples.append(_s(
            "Write a type catalog CSV for a curtain wall panel using METERS as the length unit",
            f"""\
##Type Name,Width##LENGTH##METERS,Height##LENGTH##METERS
CW-600x1000,0.600,1.000
CW-900x1200,0.900,1.200
CW-1200x1500,1.200,1.500
CW-1500x2000,1.500,2.000

// METERS: Revit multiplies by 3.28084 to convert to feet on import""",
        ))

        # Catalog for structural connections
        bolt_types = [
            ("M12-50",  12, 50),
            ("M16-60",  16, 60),
            ("M20-80",  20, 80),
            ("M24-100", 24, 100),
        ]
        bolt_csv = "\n".join(
            f"{n},{d * MM_TO_FT:.6f},{l * MM_TO_FT:.6f}"
            for n, d, l in bolt_types
        )
        samples.append(_s(
            "Write a type catalog CSV for a bolt / fastener family with nominal diameter and length",
            f"""\
##Type Name,Nominal Diameter##LENGTH##MILLIMETERS,Length##LENGTH##MILLIMETERS
{bolt_csv}""",
        ))

        # Curtain panel with infill depth
        curt_types = [
            ("CP-400x600-6mm",   400, 600, 6),
            ("CP-600x900-6mm",   600, 900, 6),
            ("CP-600x900-10mm",  600, 900, 10),
            ("CP-900x1200-10mm", 900, 1200, 10),
        ]
        curt_csv = "\n".join(
            f"{n},{w * MM_TO_FT:.6f},{h * MM_TO_FT:.6f},{g * MM_TO_FT:.6f}"
            for n, w, h, g in curt_types
        )
        samples.append(_s(
            "Write a type catalog CSV for a curtain panel family with Width, Height, and Glazing Thickness",
            f"""\
##Type Name,Width##LENGTH##MILLIMETERS,Height##LENGTH##MILLIMETERS,Glazing Thickness##LENGTH##MILLIMETERS
{curt_csv}""",
        ))

        # I-beam (imperial, inches)
        samples.append(_s(
            "Write a type catalog CSV for an I-beam family with values in INCHES (US Imperial)",
            """\
##Type Name,Depth##LENGTH##INCHES,Flange Width##LENGTH##INCHES,Web Thickness##LENGTH##INCHES
W6x9,6.000,3.940,0.170
W8x18,8.140,5.250,0.230
W10x22,10.170,5.750,0.240
W12x26,12.220,6.490,0.230
W14x30,13.840,6.730,0.270

// INCHES unit is valid for US Imperial families -- Revit converts to feet (divide by 12)""",
        ))

        # Explain use in Revit family template selection
        samples.append(_s(
            "Explain which Revit family templates support type catalog files and which do not",
            """\
// Type catalogs work with any loadable family (.rfa) template.
//
// Supported: Door, Window, Structural Column, Structural Framing, Pipe Fitting,
//            Generic Model, Casework, Furniture, etc.
//
// NOT supported:
//   - System families (walls, floors, roofs) -- they use Duplicate Type, not catalogs
//   - In-place families -- no external .rfa file, so no .txt catalog possible
//   - Annotation symbols -- size is controlled by view scale, not catalog
//
// Tip: If a family template has a type catalog, the .txt file must exist BEFORE
//      the .rfa is loaded. Revit detects the .txt at load time only.""",
        ))

        # Multi-size grille family
        grille_sizes = [
            (150, 150), (200, 100), (300, 150), (300, 300),
            (400, 200), (500, 250), (600, 300),
        ]
        grille_csv = "\n".join(
            f"Grille-{w}x{h},{w * MM_TO_FT:.6f},{h * MM_TO_FT:.6f}"
            for w, h in grille_sizes
        )
        samples.append(_s(
            "Write a type catalog CSV for an air grille family covering seven common face sizes",
            f"""\
##Type Name,Face Width##LENGTH##MILLIMETERS,Face Height##LENGTH##MILLIMETERS
{grille_csv}""",
        ))

        # Explain that catalog file can be auto-generated
        samples.append(_s(
            "Describe a Python script workflow to auto-generate a Revit type catalog .txt file from a pandas DataFrame",
            """\
# Workflow: generate type catalog .txt from a pandas DataFrame
#
# 1. Prepare a DataFrame with column names matching Revit parameter names:
#      df = pd.DataFrame({
#          "Type Name":  ["DN50", "DN80", "DN100"],
#          "Outer Diameter": [60.3, 88.9, 114.3],   # mm
#          "Wall Thickness": [3.65, 4.05, 4.50],     # mm
#      })
#
# 2. Build the header row using the catalog syntax:
#      param_units = {
#          "Outer Diameter": "LENGTH##MILLIMETERS",
#          "Wall Thickness":  "LENGTH##MILLIMETERS",
#      }
#      header = "##Type Name," + ",".join(
#          f"{col}##{spec}" for col, spec in param_units.items())
#
# 3. Write the CSV:
#      lines = [header]
#      for _, row in df.iterrows():
#          vals = [row["Type Name"]] + [
#              f"{row[col] / 304.8:.6f}" for col in param_units]
#          lines.append(",".join(vals))
#      Path("Circular-Pipe.txt").write_text("\\n".join(lines))
#
# 4. Place the .txt alongside the .rfa and reload into Revit.""",
        ))

        # Nested catalog file structure explanation
        samples.append(_s(
            "Explain how Revit resolves the type catalog .txt file when LoadFamily is called from C#",
            """\
// Revit type catalog resolution order when LoadFamily(rfaPath, ...) is called:
//
// 1. Strip the .rfa extension and add .txt:
//      "C:\\Families\\Doors\\SingleFlush.rfa"
//      --> looks for "C:\\Families\\Doors\\SingleFlush.txt"
//
// 2. If the .txt file is found:
//      a. UI mode: shows the type catalog dialog for user selection
//      b. API mode (LoadFamily overload): loads ALL types without a dialog
//         Use LoadFamilySymbol(path, typeName, ...) to load a single type.
//
// 3. If the .txt file is NOT found:
//      - LoadFamily loads the family with whatever types are embedded in the .rfa
//      - No type selection UI appears
//
// Note: FamilyManager.NewType() inside the .rfa defines embedded types;
//       the .txt catalog overrides them completely when loading into a project.""",
        ))

        # Beam pocket / embed plate catalog
        plate_types = [
            ("EP-100x100x10", 100, 100, 10),
            ("EP-150x150x12", 150, 150, 12),
            ("EP-200x200x16", 200, 200, 16),
            ("EP-250x250x20", 250, 250, 20),
        ]
        plate_csv = "\n".join(
            f"{n},{w * MM_TO_FT:.6f},{h * MM_TO_FT:.6f},{t * MM_TO_FT:.6f}"
            for n, w, h, t in plate_types
        )
        samples.append(_s(
            "Write a type catalog CSV for a steel embed plate family with Width, Height, and Thickness",
            f"""\
##Type Name,Width##LENGTH##MILLIMETERS,Height##LENGTH##MILLIMETERS,Thickness##LENGTH##MILLIMETERS
{plate_csv}""",
        ))

        # Insulation thickness catalog
        insul_types = [
            ("Insul-25mm",  25),
            ("Insul-50mm",  50),
            ("Insul-75mm",  75),
            ("Insul-100mm", 100),
            ("Insul-150mm", 150),
        ]
        insul_csv = "\n".join(
            f"{n},{t * MM_TO_FT:.6f}" for n, t in insul_types
        )
        samples.append(_s(
            "Write a type catalog CSV for a pipe insulation family with a single Thickness parameter",
            f"""\
##Type Name,Thickness##LENGTH##MILLIMETERS
{insul_csv}""",
        ))

        # Explain unit conversion in catalog
        samples.append(_s(
            "Explain how Revit converts the LENGTH values in a type catalog file from MILLIMETERS to internal feet",
            """\
// Revit type catalog unit conversion for LENGTH##MILLIMETERS:
//
//   Internal value (feet) = catalog value (mm) / 304.8
//
// Example:
//   Catalog row: "W600x900, 600, 900"  (mm columns)
//   Revit stores: Width = 600 / 304.8 = 1.968504 ft
//                 Height = 900 / 304.8 = 2.952756 ft
//
// The catalog file stores values in the DECLARED unit (MILLIMETERS, FEET, INCHES, etc.).
// Revit performs the conversion at load time -- you never store raw feet in a mm catalog.
//
// To write the catalog from C# or Python, always use the human-readable mm values
// in the text rows; do NOT pre-convert to feet unless you declare ##LENGTH##FEET.""",
        ))

        # Luminaire catalog
        lum_types = [
            ("LUM-600x600-36W",  600,  600, 36),
            ("LUM-1200x300-36W", 1200, 300, 36),
            ("LUM-1200x600-54W", 1200, 600, 54),
            ("LUM-600x600-54W",  600,  600, 54),
        ]
        lum_csv = "\n".join(
            f"{n},{w * MM_TO_FT:.6f},{h * MM_TO_FT:.6f},{p}"
            for n, w, h, p in lum_types
        )
        samples.append(_s(
            "Write a type catalog CSV for a recessed luminaire family with Width, Height, and Wattage",
            f"""\
##Type Name,Width##LENGTH##MILLIMETERS,Height##LENGTH##MILLIMETERS,Wattage##NUMBER
{lum_csv}

// Wattage is a dimensionless NUMBER -- stored as-is (watts)""",
        ))

        # Read type catalog file back to verify
        samples.append(_s(
            "Read and validate a type catalog CSV file in Python to ensure all length values are positive",
            """\
# Python validation script for a Revit type catalog .txt file
import csv
from pathlib import Path

def validate_type_catalog(txt_path: str) -> list[str]:
    errors = []
    path = Path(txt_path)
    if not path.exists():
        return [f"File not found: {txt_path}"]

    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)  # e.g. ["##Type Name", "Width##LENGTH##MILLIMETERS", ...]

        # Parse column specs
        col_specs = []
        for col in header[1:]:
            parts = col.split("##")
            col_specs.append((parts[0], parts[1] if len(parts) > 1 else "TEXT"))

        for row_num, row in enumerate(reader, start=2):
            if len(row) != len(header):
                errors.append(f"Row {row_num}: column count mismatch")
                continue
            type_name = row[0]
            for i, (param, dtype) in enumerate(col_specs, start=1):
                val = row[i]
                if dtype == "LENGTH":
                    try:
                        if float(val) <= 0:
                            errors.append(f"Row {row_num} '{type_name}': {param} = {val} (must be > 0)")
                    except ValueError:
                        errors.append(f"Row {row_num} '{type_name}': {param} = '{val}' not numeric")
    return errors""",
        ))

        return samples

    # ------------------------------------------------------------------
    # Nested family loading (~40 samples)
    # ------------------------------------------------------------------

    def _nested_family_loading(self) -> List[SAMPLE]:
        samples = []

        # Basic LoadFamily call
        lib_families = [
            ("W-Wide Flange",   r"C:\ProgramData\Autodesk\RVT 2026\Libraries\US Imperial\Structural\Framing\Steel\W-Wide Flange.rfa",   "structural steel beam"),
            ("Single Flush",    r"C:\ProgramData\Autodesk\RVT 2026\Libraries\US Imperial\Doors\Single Flush.rfa",                       "single-flush door"),
            ("Fixed",           r"C:\ProgramData\Autodesk\RVT 2026\Libraries\US Imperial\Windows\Fixed.rfa",                            "fixed window"),
            ("Round Duct",      r"C:\ProgramData\Autodesk\RVT 2026\Libraries\US Imperial\MEP\Air\Round Duct.rfa",                       "round duct fitting"),
        ]
        for fname, fpath, desc in lib_families:
            samples.append(_s(
                f"Load the '{fname}' family ({desc}) into a family document",
                f"""\
using Autodesk.Revit.DB;
using System.Linq;

// LoadFamily must be called inside a transaction when targeting a project document
// In a family document it can be called outside a transaction
using (Transaction tx = new Transaction(familyDoc, "Load {fname}"))
{{
    tx.Start();

    Family loaded;
    bool success = familyDoc.LoadFamily(@"{fpath}", out loaded);

    if (!success)
    {{
        // Already loaded -- find by name
        loaded = new FilteredElementCollector(familyDoc)
            .OfClass(typeof(Family))
            .Cast<Family>()
            .FirstOrDefault(f => f.Name == "{fname}");
    }}

    tx.Commit();
}}""",
            ))

        # IFamilyLoadOptions implementation
        samples.append(_s(
            "Implement IFamilyLoadOptions to silently overwrite an existing family on reload",
            """\
using Autodesk.Revit.DB;

public class OverwriteFamilyLoadOptions : IFamilyLoadOptions
{
    public bool OnFamilyFound(bool familyInUse, out bool overwriteParameterValues)
    {
        // Always overwrite, including parameter values
        overwriteParameterValues = true;
        return true;
    }

    public bool OnSharedFamilyFound(
        Family sharedFamily,
        bool familyInUse,
        out FamilySource source,
        out bool overwriteParameterValues)
    {
        source = FamilySource.Family;
        overwriteParameterValues = true;
        return true;
    }
}

// Usage:
// Family fam;
// doc.LoadFamily(path, new OverwriteFamilyLoadOptions(), out fam);""",
        ))

        # IFamilyLoadOptions -- keep existing
        samples.append(_s(
            "Implement IFamilyLoadOptions that keeps the existing family if it is already in use",
            """\
using Autodesk.Revit.DB;

public class KeepExistingFamilyLoadOptions : IFamilyLoadOptions
{
    public bool OnFamilyFound(bool familyInUse, out bool overwriteParameterValues)
    {
        if (familyInUse)
        {
            overwriteParameterValues = false;
            return false; // do not overwrite
        }
        overwriteParameterValues = true;
        return true;
    }

    public bool OnSharedFamilyFound(
        Family sharedFamily,
        bool familyInUse,
        out FamilySource source,
        out bool overwriteParameterValues)
    {
        source = FamilySource.Project;
        overwriteParameterValues = false;
        return !familyInUse;
    }
}""",
        ))

        # Check if already loaded by name
        samples.append(_s(
            "Check whether a family named 'Casework-Base Cabinet' is already loaded before attempting to load it",
            """\
using Autodesk.Revit.DB;
using System.Linq;

bool IsAlreadyLoaded(Document doc, string familyName)
{
    return new FilteredElementCollector(doc)
        .OfClass(typeof(Family))
        .Cast<Family>()
        .Any(f => f.Name == familyName);
}

// Usage
if (!IsAlreadyLoaded(familyDoc, "Casework-Base Cabinet"))
{
    using (Transaction tx = new Transaction(familyDoc, "Load Casework"))
    {
        tx.Start();
        Family fam;
        familyDoc.LoadFamily(@"C:\Families\Casework\Casework-Base Cabinet.rfa", out fam);
        tx.Commit();
    }
}""",
        ))

        # Load from relative path
        samples.append(_s(
            "Load a nested family from a path relative to the current family document's location",
            """\
using Autodesk.Revit.DB;
using System.IO;

// Resolve path relative to the host family
string hostPath = familyDoc.PathName; // e.g. C:\\Families\\Doors\\MyDoor.rfa
string dir = Path.GetDirectoryName(hostPath) ?? "";
string nestedPath = Path.Combine(dir, "Components", "DoorHandle.rfa");

if (File.Exists(nestedPath))
{
    using (Transaction tx = new Transaction(familyDoc, "Load Door Handle"))
    {
        tx.Start();
        Family handleFamily;
        familyDoc.LoadFamily(nestedPath, out handleFamily);
        tx.Commit();
    }
}""",
        ))

        # Enumerate loaded nested families
        samples.append(_s(
            "List all nested families already loaded inside a family document",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

IList<string> GetLoadedNestedFamilyNames(Document familyDoc)
{
    return new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Family))
        .Cast<Family>()
        .Select(f => f.Name)
        .OrderBy(n => n)
        .ToList();
}""",
        ))

        # Get symbol IDs after loading
        samples.append(_s(
            "After loading a family, retrieve all of its FamilySymbol element IDs",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

IList<FamilySymbol> GetSymbols(Document doc, Family family)
{
    var symbols = new List<FamilySymbol>();
    foreach (ElementId id in family.GetFamilySymbolIds())
    {
        if (doc.GetElement(id) is FamilySymbol sym)
            symbols.Add(sym);
    }
    return symbols;
}""",
        ))

        # Open nested family for editing
        samples.append(_s(
            "Open a loaded nested family document for editing from inside the host family editor",
            """\
using Autodesk.Revit.DB;
using System.Linq;

// Find the nested family
Family nestedFamily = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(Family))
    .Cast<Family>()
    .FirstOrDefault(f => f.Name == "DoorHardware");

if (nestedFamily != null)
{
    // EditFamily opens the nested .rfa in a new document
    Document nestedDoc = familyDoc.EditFamily(nestedFamily);
    // Make changes to nestedDoc, then LoadFamily back into familyDoc
}""",
        ))

        # Load family using LoadFamilySymbol
        samples.append(_s(
            "Load only a specific FamilySymbol from a type-catalog family without loading all types",
            """\
using Autodesk.Revit.DB;

// LoadFamilySymbol loads a single named type from the catalog
using (Transaction tx = new Transaction(doc, "Load Specific Symbol"))
{
    tx.Start();

    // Third argument is the type name from the catalog
    bool loaded = doc.LoadFamilySymbol(
        @"C:\Families\Doors\Single-Flush.rfa",
        "Single-Flush-914x2032",
        new OverwriteFamilyLoadOptions(),
        out FamilySymbol symbol);

    if (loaded && symbol != null && !symbol.IsActive)
        symbol.Activate();

    tx.Commit();
}""",
        ))

        # Remove nested family (unload)
        samples.append(_s(
            "Remove (delete) a nested family from a family document when it is no longer needed",
            """\
using Autodesk.Revit.DB;
using System.Linq;

// Deleting all instances and then the Family element removes it from the document
using (Transaction tx = new Transaction(familyDoc, "Remove Nested Family"))
{
    tx.Start();

    Family nestedFamily = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Family))
        .Cast<Family>()
        .FirstOrDefault(f => f.Name == "OldComponent");

    if (nestedFamily != null)
    {
        // Delete all instances first
        var instances = new FilteredElementCollector(familyDoc)
            .OfClass(typeof(FamilyInstance))
            .Cast<FamilyInstance>()
            .Where(fi => fi.Symbol.Family.Id == nestedFamily.Id)
            .Select(fi => fi.Id)
            .ToList();

        foreach (var id in instances)
            familyDoc.Delete(id);

        familyDoc.Delete(nestedFamily.Id);
    }

    tx.Commit();
}""",
        ))

        # Bulk-load multiple nested families
        nested_families_bulk = [
            ("Hinge",     r"C:\Families\Hardware\Hinge.rfa"),
            ("Knob",      r"C:\Families\Hardware\Knob.rfa"),
            ("Closer",    r"C:\Families\Hardware\Door Closer.rfa"),
        ]
        fam_list = "\n    ".join(
            f'@"{p}",' for _, p in nested_families_bulk
        )
        samples.append(_s(
            "Load multiple hardware component families (Hinge, Knob, Closer) into a door family document",
            f"""\
using Autodesk.Revit.DB;
using System.Collections.Generic;

var paths = new List<string>
{{
    {fam_list}
}};

var loadOptions = new OverwriteFamilyLoadOptions();

using (Transaction tx = new Transaction(familyDoc, "Load Hardware"))
{{
    tx.Start();
    foreach (string path in paths)
    {{
        Family fam;
        familyDoc.LoadFamily(path, loadOptions, out fam);
    }}
    tx.Commit();
}}""",
        ))

        # Handle load failure gracefully
        samples.append(_s(
            "Load a nested family and handle the case where the file does not exist at the specified path",
            """\
using Autodesk.Revit.DB;
using System.IO;

bool TryLoadNestedFamily(Document familyDoc, string rfaPath, out Family family)
{
    family = null;
    if (!File.Exists(rfaPath))
        return false;

    using (Transaction tx = new Transaction(familyDoc, "Load Nested Family"))
    {
        tx.Start();
        bool loaded = familyDoc.LoadFamily(rfaPath, out family);
        tx.Commit();
        return loaded || family != null;
    }
}""",
        ))

        # Verify category compatibility
        samples.append(_s(
            "Verify that a family's category is compatible with the host family before loading it as a nested family",
            """\
using Autodesk.Revit.DB;

// Open the candidate family document (read-only) to inspect its category
Document candidateDoc = app.OpenDocumentFile(rfaPath);
Category nestedCat = candidateDoc.OwnerFamily?.FamilyCategory;

// For example, only allow Specialty Equipment inside a Generic Model host
bool isCompatible = nestedCat?.Id.IntegerValue ==
    (int)BuiltInCategory.OST_SpecialityEquipment;

candidateDoc.Close(false); // close without saving

if (isCompatible)
{
    using (Transaction tx = new Transaction(familyDoc, "Load Nested"))
    {
        tx.Start();
        Family fam;
        familyDoc.LoadFamily(rfaPath, out fam);
        tx.Commit();
    }
}""",
        ))

        # Get family name from path before loading
        samples.append(_s(
            "Extract the family name from an .rfa file path without loading the file",
            """\
using System.IO;

string rfaPath = @"C:\\Families\\Doors\\SingleFlush.rfa";
string familyName = Path.GetFileNameWithoutExtension(rfaPath);
// familyName = "SingleFlush"
// Use this to check IsAlreadyLoaded(doc, familyName) before calling LoadFamily""",
        ))

        # Load from project template library
        samples.append(_s(
            "Load a family from the Revit default content library path determined at runtime",
            """\
using Autodesk.Revit.DB;
using System.IO;

// Determine the Revit content library path from the application
string libraryPath = app.GetLibraryPaths().Values.FirstOrDefault()
    ?? @"C:\\ProgramData\\Autodesk\\RVT 2026\\Libraries\\";

string doorPath = Path.Combine(libraryPath, "US Imperial", "Doors", "Single Flush.rfa");

if (File.Exists(doorPath))
{
    using (Transaction tx = new Transaction(doc, "Load Door"))
    {
        tx.Start();
        Family fam;
        doc.LoadFamily(doorPath, new OverwriteFamilyLoadOptions(), out fam);
        tx.Commit();
    }
}""",
        ))

        # IFamilyLoadOptions -- prompt user
        samples.append(_s(
            "Implement IFamilyLoadOptions that prompts the user (via a boolean flag) whether to overwrite",
            """\
using Autodesk.Revit.DB;

public class PromptFamilyLoadOptions : IFamilyLoadOptions
{
    private readonly bool _userSaidOverwrite;

    public PromptFamilyLoadOptions(bool userSaidOverwrite)
    {
        _userSaidOverwrite = userSaidOverwrite;
    }

    public bool OnFamilyFound(bool familyInUse, out bool overwriteParameterValues)
    {
        overwriteParameterValues = _userSaidOverwrite;
        return _userSaidOverwrite;
    }

    public bool OnSharedFamilyFound(Family sharedFamily, bool familyInUse,
        out FamilySource source, out bool overwriteParameterValues)
    {
        source = FamilySource.Family;
        overwriteParameterValues = _userSaidOverwrite;
        return _userSaidOverwrite;
    }
}""",
        ))

        # Get the family document path for an already-loaded family
        samples.append(_s(
            "For a Family element already in the document, retrieve its source .rfa file path if available",
            """\
using Autodesk.Revit.DB;
using System.Linq;

Family family = new FilteredElementCollector(doc)
    .OfClass(typeof(Family))
    .Cast<Family>()
    .FirstOrDefault(f => f.Name == "SingleFlush");

if (family != null)
{
    // FamilyDocument is only accessible if the family is open for editing
    // For a closed/loaded family, the path is stored in the family element:
    string path = family.get_Parameter(BuiltInParameter.ELEM_FAMILY_PARAM)
        ?.AsValueString() ?? "(embedded)";
}""",
        ))

        # Count symbols in a loaded family
        samples.append(_s(
            "Count how many FamilySymbol types are available in a loaded family named 'W-Wide Flange'",
            """\
using Autodesk.Revit.DB;
using System.Linq;

Family steelFamily = new FilteredElementCollector(doc)
    .OfClass(typeof(Family))
    .Cast<Family>()
    .FirstOrDefault(f => f.Name == "W-Wide Flange");

int symbolCount = steelFamily?.GetFamilySymbolIds().Count ?? 0;""",
        ))

        # Reload updated family
        samples.append(_s(
            "Reload a family from disk to pick up changes made outside of Revit (update in place)",
            """\
using Autodesk.Revit.DB;
using System.Linq;

string updatedPath = @"C:\\Families\\Doors\\SingleFlush.rfa";

// Use the overwrite options so the reload replaces the existing family
var opts = new OverwriteFamilyLoadOptions();

using (Transaction tx = new Transaction(doc, "Reload Family"))
{
    tx.Start();
    Family reloaded;
    // LoadFamily with the same name as an existing family triggers a reload
    doc.LoadFamily(updatedPath, opts, out reloaded);
    tx.Commit();
}""",
        ))

        # Load family into family (nested) vs project document
        samples.append(_s(
            "Explain the difference between loading a family into a project document vs into a family document",
            """\
// Loading into a PROJECT document:
//   - Call: doc.LoadFamily(path, out family) -- doc is the project (.rvt)
//   - Result: the family becomes available as a loadable type in schedules and tag
//   - Must be inside a Transaction
//   - Loaded Family element is visible in the Project Browser under Families
//
// Loading into a FAMILY document (nested family):
//   - Call: familyDoc.LoadFamily(path, out family) -- familyDoc is the .rfa
//   - Result: the family becomes a nested sub-component inside the host family
//   - Can be called outside a Transaction in some Revit versions, but safest inside one
//   - Loaded Family element appears when editing the host family
//   - To place instances of the nested family: use familyDoc.FamilyCreate.NewFamilyInstance
//
// In both cases the same LoadFamily API is used -- only the Document context differs.""",
        ))

        # Recursive nested family check
        samples.append(_s(
            "Recursively check how many levels of nested families exist in a loaded family document",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

int GetNestingDepth(Document doc, int currentDepth = 0)
{
    var nestedFamilies = new FilteredElementCollector(doc)
        .OfClass(typeof(Family))
        .Cast<Family>()
        .ToList();

    if (!nestedFamilies.Any()) return currentDepth;

    int maxDepth = currentDepth;
    foreach (Family nested in nestedFamilies)
    {
        Document nestedDoc = doc.EditFamily(nested);
        if (nestedDoc != null)
        {
            int depth = GetNestingDepth(nestedDoc, currentDepth + 1);
            maxDepth = Math.Max(maxDepth, depth);
            nestedDoc.Close(false);
        }
    }
    return maxDepth;
}
// Note: Revit limits nesting to 5 levels deep""",
        ))

        # Get FamilySymbol parameter values after loading
        samples.append(_s(
            "After loading a structural column family, read the 'b' and 'd' parameter values from each FamilySymbol",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

Family colFamily = new FilteredElementCollector(doc)
    .OfClass(typeof(Family))
    .Cast<Family>()
    .FirstOrDefault(f => f.Name == "Concrete-Rectangular-Column");

var columnData = new List<(string TypeName, double bMm, double dMm)>();

if (colFamily != null)
{
    foreach (ElementId id in colFamily.GetFamilySymbolIds())
    {
        if (doc.GetElement(id) is FamilySymbol sym)
        {
            double bFt = sym.LookupParameter("b")?.AsDouble() ?? 0;
            double dFt = sym.LookupParameter("d")?.AsDouble() ?? 0;
            columnData.Add((sym.Name, bFt * 304.8, dFt * 304.8));
        }
    }
}""",
        ))

        # Load and activate in single transaction
        samples.append(_s(
            "Load a family and immediately activate all of its symbols in a single transaction",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(doc, "Load and Activate"))
{
    tx.Start();

    Family fam;
    doc.LoadFamily(@"C:\\Families\\Windows\\Fixed.rfa",
        new OverwriteFamilyLoadOptions(), out fam);

    if (fam != null)
    {
        foreach (ElementId symId in fam.GetFamilySymbolIds())
        {
            if (doc.GetElement(symId) is FamilySymbol sym && !sym.IsActive)
                sym.Activate();
        }
    }

    tx.Commit();
}""",
        ))

        # Filter families by category
        samples.append(_s(
            "Collect all loaded families that belong to the 'Doors' category in a project document",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

IList<Family> GetDoorFamilies(Document doc)
{
    return new FilteredElementCollector(doc)
        .OfClass(typeof(Family))
        .Cast<Family>()
        .Where(f => f.FamilyCategory?.Id.IntegerValue ==
                    (int)BuiltInCategory.OST_Doors)
        .ToList();
}""",
        ))

        # Load family with progress feedback
        samples.append(_s(
            "Load multiple families from a folder and report which ones were newly loaded vs already present",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.IO;
using System.Linq;

var newlyLoaded  = new List<string>();
var alreadyExist = new List<string>();

string folder = @"C:\\ProjectFamilies\\";
var rfaPaths = Directory.GetFiles(folder, "*.rfa", SearchOption.TopDirectoryOnly);

using (Transaction tx = new Transaction(doc, "Load Project Families"))
{
    tx.Start();
    foreach (string path in rfaPaths)
    {
        string name = Path.GetFileNameWithoutExtension(path);
        bool exists = new FilteredElementCollector(doc)
            .OfClass(typeof(Family))
            .Cast<Family>()
            .Any(f => f.Name == name);

        if (exists)
        {
            alreadyExist.Add(name);
        }
        else
        {
            Family fam;
            doc.LoadFamily(path, new OverwriteFamilyLoadOptions(), out fam);
            if (fam != null) newlyLoaded.Add(name);
        }
    }
    tx.Commit();
}""",
        ))

        # Check if family is editable (not from library)
        samples.append(_s(
            "Check whether a loaded family can be edited (is not a system or read-only family)",
            """\
using Autodesk.Revit.DB;
using System.Linq;

Family family = new FilteredElementCollector(doc)
    .OfClass(typeof(Family))
    .Cast<Family>()
    .FirstOrDefault(f => f.Name == "MyComponent");

if (family != null)
{
    // IsEditable returns false for system families and some built-in content
    bool canEdit = family.IsEditable;

    if (canEdit)
    {
        Document famDoc = doc.EditFamily(family);
        // Make changes, then LoadFamily back
        famDoc.Close(false);
    }
}""",
        ))

        # Load with transaction group
        samples.append(_s(
            "Load a family inside a TransactionGroup so all sub-transactions can be rolled back atomically",
            """\
using Autodesk.Revit.DB;

using (TransactionGroup tg = new TransactionGroup(doc, "Load Family Batch"))
{
    tg.Start();
    try
    {
        using (Transaction tx = new Transaction(doc, "Load"))
        {
            tx.Start();
            Family fam;
            bool ok = doc.LoadFamily(@"C:\\Families\\Comp.rfa",
                new OverwriteFamilyLoadOptions(), out fam);
            if (!ok) throw new InvalidOperationException("Load failed");
            tx.Commit();
        }
        tg.Assimilate(); // commit the group
    }
    catch
    {
        tg.RollBack(); // undo all sub-transactions on failure
        throw;
    }
}""",
        ))

        # Find orphaned nested families (loaded but no instances)
        samples.append(_s(
            "Find nested families that are loaded but have no placed instances in the family document",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

IList<Family> GetUnusedNestedFamilies(Document familyDoc)
{
    var usedSymbolIds = new HashSet<ElementId>(
        new FilteredElementCollector(familyDoc)
            .OfClass(typeof(FamilyInstance))
            .Cast<FamilyInstance>()
            .Select(fi => fi.GetTypeId()));

    return new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Family))
        .Cast<Family>()
        .Where(f => !f.GetFamilySymbolIds().Any(id => usedSymbolIds.Contains(id)))
        .ToList();
}""",
        ))

        # Explain FamilySource enum
        samples.append(_s(
            "Explain the FamilySource enum used in IFamilyLoadOptions.OnSharedFamilyFound",
            """\
// FamilySource controls which version of a shared nested family is kept:
//
// FamilySource.Family:
//   Use the version embedded inside the family being loaded (.rfa file).
//   Choose this when distributing a family that must carry its own sub-components.
//
// FamilySource.Project:
//   Keep the version already loaded in the project document.
//   Choose this when the project has a newer or project-specific shared family.
//
// Example:
// public bool OnSharedFamilyFound(Family sharedFamily, bool familyInUse,
//     out FamilySource source, out bool overwriteParameterValues)
// {
//     source = familyInUse ? FamilySource.Project : FamilySource.Family;
//     overwriteParameterValues = !familyInUse;
//     return true;
// }""",
        ))

        # Load family and get default symbol
        samples.append(_s(
            "Load a family and retrieve its default (first) FamilySymbol, activating it if needed",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilySymbol GetDefaultSymbol(Document doc, string rfaPath)
{
    Family fam;
    using (Transaction tx = new Transaction(doc, "Load"))
    {
        tx.Start();
        doc.LoadFamily(rfaPath, new OverwriteFamilyLoadOptions(), out fam);
        tx.Commit();
    }

    if (fam == null)
    {
        // Already loaded -- find by name
        string name = System.IO.Path.GetFileNameWithoutExtension(rfaPath);
        fam = new FilteredElementCollector(doc)
            .OfClass(typeof(Family))
            .Cast<Family>()
            .FirstOrDefault(f => f.Name == name);
    }

    FamilySymbol sym = fam?.GetFamilySymbolIds()
        .Select(id => doc.GetElement(id) as FamilySymbol)
        .FirstOrDefault();

    if (sym != null && !sym.IsActive)
    {
        using (Transaction tx = new Transaction(doc, "Activate"))
        {
            tx.Start();
            sym.Activate();
            tx.Commit();
        }
    }

    return sym;
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # Nested family placement (~35 samples)
    # ------------------------------------------------------------------

    def _nested_family_placement(self) -> List[SAMPLE]:
        samples = []

        # Basic placement at origin
        placement_cases = [
            ("DoorHandle",     "door hardware component",   (0, 0, 0)),
            ("HingeComponent", "hinge at standard position",(0, 0, 900)),
            ("GlazingPanel",   "glazing panel insert",      (0, 50, 0)),
        ]
        for fname, desc, (x, y, z) in placement_cases:
            x_ft = x * MM_TO_FT
            y_ft = y * MM_TO_FT
            z_ft = z * MM_TO_FT
            samples.append(_s(
                f"Place a '{fname}' nested family instance ({desc}) in the family document",
                f"""\
using Autodesk.Revit.DB;
using System.Linq;

// Activate symbol and place instance -- must be inside a transaction
using (Transaction tx = new Transaction(familyDoc, "Place {fname}"))
{{
    tx.Start();

    Family nestedFamily = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Family))
        .Cast<Family>()
        .FirstOrDefault(f => f.Name == "{fname}");

    if (nestedFamily != null)
    {{
        FamilySymbol symbol = familyDoc.GetElement(
            nestedFamily.GetFamilySymbolIds().First()) as FamilySymbol;

        if (symbol != null)
        {{
            if (!symbol.IsActive)
                symbol.Activate(); // must activate before placement

            XYZ location = new XYZ({x_ft:.6f}, {y_ft:.6f}, {z_ft:.6f}); // {x},{y},{z} mm
            FamilyInstance inst = familyDoc.FamilyCreate.NewFamilyInstance(
                location, symbol, familyDoc.ActiveView);
        }}
    }}

    tx.Commit();
}}""",
            ))

        # Place with specific type from multi-type family
        samples.append(_s(
            "Place a specific type ('W200x22') from a loaded W-section nested family at the origin",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "Place W200x22"))
{{
    tx.Start();

    Family steelFamily = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Family))
        .Cast<Family>()
        .FirstOrDefault(f => f.Name == "W-Wide Flange");

    if (steelFamily != null)
    {{
        // Find the specific type by name
        FamilySymbol w200 = steelFamily.GetFamilySymbolIds()
            .Select(id => familyDoc.GetElement(id) as FamilySymbol)
            .Where(s => s != null)
            .FirstOrDefault(s => s.Name == "W200x22");

        if (w200 != null)
        {{
            if (!w200.IsActive) w200.Activate();

            FamilyInstance inst = familyDoc.FamilyCreate.NewFamilyInstance(
                XYZ.Zero, w200, familyDoc.ActiveView);
        }}
    }}

    tx.Commit();
}}""",
        ))

        # Place with transform (rotation)
        angles = [(90, "rotated 90 degrees"), (180, "flipped 180 degrees"), (45, "angled 45 degrees")]
        for deg, desc in angles:
            import math as _math
            rad = _math.radians(deg)
            samples.append(_s(
                f"Place a nested hinge family instance {desc} about the Z axis",
                f"""\
using Autodesk.Revit.DB;
using System.Linq;
using System;

using (Transaction tx = new Transaction(familyDoc, "Place Rotated Hinge"))
{{
    tx.Start();

    Family hingeFamily = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Family))
        .Cast<Family>()
        .FirstOrDefault(f => f.Name == "HingeComponent");

    if (hingeFamily != null)
    {{
        FamilySymbol symbol = familyDoc.GetElement(
            hingeFamily.GetFamilySymbolIds().First()) as FamilySymbol;

        if (symbol != null)
        {{
            if (!symbol.IsActive) symbol.Activate();

            FamilyInstance inst = familyDoc.FamilyCreate.NewFamilyInstance(
                XYZ.Zero, symbol, familyDoc.ActiveView);

            // Rotate about Z axis at origin
            Line axis = Line.CreateBound(XYZ.Zero, XYZ.BasisZ);
            ElementTransformUtils.RotateElement(familyDoc, inst.Id, axis, {rad:.6f}); // {deg} deg
        }}
    }}

    tx.Commit();
}}""",
            ))

        # Place multiple instances in a loop
        samples.append(_s(
            "Place three hinge instances at Z heights of 200mm, 1000mm, and 1800mm on a door leaf",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

double[] hingHeights = {{ {200*MM_TO_FT:.6f}, {1000*MM_TO_FT:.6f}, {1800*MM_TO_FT:.6f} }}; // mm: 200, 1000, 1800

using (Transaction tx = new Transaction(familyDoc, "Place Hinges"))
{{
    tx.Start();

    Family hingeFamily = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Family))
        .Cast<Family>()
        .FirstOrDefault(f => f.Name == "HingeComponent");

    if (hingeFamily != null)
    {{
        FamilySymbol sym = familyDoc.GetElement(
            hingeFamily.GetFamilySymbolIds().First()) as FamilySymbol;
        if (sym != null && !sym.IsActive) sym.Activate();

        foreach (double z in hingHeights)
        {{
            XYZ pt = new XYZ(0, 0, z);
            familyDoc.FamilyCreate.NewFamilyInstance(pt, sym, familyDoc.ActiveView);
        }}
    }}

    tx.Commit();
}}""",
        ))

        # Get placed instance and modify parameter
        samples.append(_s(
            "After placing a nested family instance, set its 'Size' instance parameter to 50mm",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "Place and Configure"))
{{
    tx.Start();

    Family nestedFam = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Family))
        .Cast<Family>()
        .FirstOrDefault(f => f.Name == "Connector");

    if (nestedFam != null)
    {{
        FamilySymbol sym = familyDoc.GetElement(
            nestedFam.GetFamilySymbolIds().First()) as FamilySymbol;

        if (sym != null)
        {{
            if (!sym.IsActive) sym.Activate();
            FamilyInstance inst = familyDoc.FamilyCreate.NewFamilyInstance(
                XYZ.Zero, sym, familyDoc.ActiveView);

            // Set instance parameter after placement
            Parameter sizeParam = inst.LookupParameter("Size");
            if (sizeParam != null && !sizeParam.IsReadOnly)
                sizeParam.Set({50 * MM_TO_FT:.6f}); // 50 mm
        }}
    }}

    tx.Commit();
}}""",
        ))

        # List all instances of a nested family
        samples.append(_s(
            "Collect all placed instances of a nested family named 'GlazingPanel' inside the family document",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

IList<FamilyInstance> GetNestedInstances(Document familyDoc, string nestedFamilyName)
{
    Family nestedFam = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Family))
        .Cast<Family>()
        .FirstOrDefault(f => f.Name == nestedFamilyName);

    if (nestedFam == null)
        return new List<FamilyInstance>();

    var symbolIds = new HashSet<ElementId>(nestedFam.GetFamilySymbolIds());

    return new FilteredElementCollector(familyDoc)
        .OfClass(typeof(FamilyInstance))
        .Cast<FamilyInstance>()
        .Where(fi => symbolIds.Contains(fi.GetTypeId()))
        .ToList();
}""",
        ))

        # Move an existing nested instance
        samples.append(_s(
            "Move a previously placed nested family instance to a new location at (100mm, 0, 900mm)",
            f"""\
using Autodesk.Revit.DB;

// Assumes 'inst' is a FamilyInstance already placed in the family document
using (Transaction tx = new Transaction(familyDoc, "Move Instance"))
{{
    tx.Start();

    XYZ newLocation = new XYZ({100*MM_TO_FT:.6f}, 0, {900*MM_TO_FT:.6f}); // 100mm, 0, 900mm
    ElementTransformUtils.MoveElement(familyDoc, inst.Id, newLocation - (inst.Location as LocationPoint).Point);

    tx.Commit();
}}""",
        ))

        # Activate multiple symbols at once
        samples.append(_s(
            "Activate all FamilySymbols from a loaded nested family before placing any instances",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "Activate Symbols"))
{
    tx.Start();

    Family nestedFam = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Family))
        .Cast<Family>()
        .FirstOrDefault(f => f.Name == "FrameComponent");

    if (nestedFam != null)
    {
        foreach (ElementId id in nestedFam.GetFamilySymbolIds())
        {
            if (familyDoc.GetElement(id) is FamilySymbol sym && !sym.IsActive)
                sym.Activate();
        }
    }

    tx.Commit();
}""",
        ))

        # Place with mirroring
        samples.append(_s(
            "Place two hinge instances mirrored about the vertical centre line of a door leaf",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "Place Mirrored Hinges"))
{{
    tx.Start();

    Family hingeFam = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Family)).Cast<Family>()
        .FirstOrDefault(f => f.Name == "HingeComponent");

    if (hingeFam != null)
    {{
        FamilySymbol sym = familyDoc.GetElement(hingeFam.GetFamilySymbolIds().First()) as FamilySymbol;
        if (sym != null && !sym.IsActive) sym.Activate();

        // Left hinge
        FamilyInstance left = familyDoc.FamilyCreate.NewFamilyInstance(
            new XYZ(-{38 * MM_TO_FT:.6f}, 0, {200 * MM_TO_FT:.6f}), sym, familyDoc.ActiveView);

        // Right hinge: mirror about YZ plane
        FamilyInstance right = familyDoc.FamilyCreate.NewFamilyInstance(
            new XYZ( {38 * MM_TO_FT:.6f}, 0, {200 * MM_TO_FT:.6f}), sym, familyDoc.ActiveView);
        ElementTransformUtils.MirrorElement(familyDoc, right.Id,
            Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero));
    }}

    tx.Commit();
}}""",
        ))

        # Replace instance type
        samples.append(_s(
            "Change the FamilySymbol (type) of an existing nested family instance to a different symbol",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "Change Instance Type"))
{
    tx.Start();

    // inst is the existing FamilyInstance
    Family parentFam = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Family)).Cast<Family>()
        .FirstOrDefault(f => f.Name == "DoorKnob");

    FamilySymbol newSymbol = parentFam?.GetFamilySymbolIds()
        .Select(id => familyDoc.GetElement(id) as FamilySymbol)
        .FirstOrDefault(s => s?.Name == "LeverHandle");

    if (newSymbol != null)
    {
        if (!newSymbol.IsActive) newSymbol.Activate();
        inst.Symbol = newSymbol; // reassign the type
    }

    tx.Commit();
}""",
        ))

        # Read instance location point
        samples.append(_s(
            "Read the XYZ location of a placed nested family instance and convert it to millimetres",
            """\
using Autodesk.Revit.DB;

// inst is a FamilyInstance placed in the family document
LocationPoint loc = inst.Location as LocationPoint;
if (loc != null)
{
    XYZ ptFt = loc.Point; // in feet
    double xMm = ptFt.X * 304.8;
    double yMm = ptFt.Y * 304.8;
    double zMm = ptFt.Z * 304.8;
}""",
        ))

        # Place along a line at intervals
        samples.append(_s(
            "Place nested fastener instances at 400mm intervals along a 2400mm horizontal line",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

double spacing = {400 * MM_TO_FT:.6f}; // 400 mm
double totalLen = {2400 * MM_TO_FT:.6f}; // 2400 mm
int count = (int)(totalLen / spacing) + 1; // 7 fasteners

using (Transaction tx = new Transaction(familyDoc, "Place Fasteners"))
{{
    tx.Start();

    Family fastenerFam = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Family)).Cast<Family>()
        .FirstOrDefault(f => f.Name == "Bolt");

    if (fastenerFam != null)
    {{
        FamilySymbol sym = familyDoc.GetElement(
            fastenerFam.GetFamilySymbolIds().First()) as FamilySymbol;
        if (sym != null && !sym.IsActive) sym.Activate();

        for (int i = 0; i < count; i++)
        {{
            XYZ pt = new XYZ(i * spacing, 0, 0);
            familyDoc.FamilyCreate.NewFamilyInstance(pt, sym, familyDoc.ActiveView);
        }}
    }}

    tx.Commit();
}}""",
        ))

        # Place with reference level
        samples.append(_s(
            "Place a nested family instance relative to a named reference level inside the family",
            """\
using Autodesk.Revit.DB;
using System.Linq;

// In a family document, levels are reference levels (not project levels)
Level refLevel = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(Level))
    .Cast<Level>()
    .FirstOrDefault(l => l.Name == "Ref. Level");

using (Transaction tx = new Transaction(familyDoc, "Place on Level"))
{
    tx.Start();

    Family compFam = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Family)).Cast<Family>()
        .FirstOrDefault(f => f.Name == "SillComponent");

    if (compFam != null && refLevel != null)
    {
        FamilySymbol sym = familyDoc.GetElement(
            compFam.GetFamilySymbolIds().First()) as FamilySymbol;
        if (sym != null && !sym.IsActive) sym.Activate();

        // NewFamilyInstance overload with Level places element at that elevation
        FamilyInstance inst = familyDoc.FamilyCreate.NewFamilyInstance(
            XYZ.Zero, sym, refLevel, StructuralType.NonStructural);
    }

    tx.Commit();
}""",
        ))

        # Get all instances and their locations as a dict
        samples.append(_s(
            "Build a dictionary mapping each nested family instance Id to its XYZ location in millimetres",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

var instanceLocations = new Dictionary<ElementId, XYZ>();

foreach (FamilyInstance fi in new FilteredElementCollector(familyDoc)
    .OfClass(typeof(FamilyInstance)).Cast<FamilyInstance>())
{
    if (fi.Location is LocationPoint lp)
    {
        // Convert feet to mm
        instanceLocations[fi.Id] = new XYZ(
            lp.Point.X * 304.8,
            lp.Point.Y * 304.8,
            lp.Point.Z * 304.8);
    }
}""",
        ))

        # Check bounding box after placement
        samples.append(_s(
            "After placing a nested family instance, get its bounding box to verify it fits within a given volume",
            f"""\
using Autodesk.Revit.DB;

// 'inst' is a newly placed FamilyInstance
BoundingBoxXYZ bb = inst.get_BoundingBox(null); // null = model bounding box

if (bb != null)
{{
    double widthMm  = (bb.Max.X - bb.Min.X) * 304.8;
    double depthMm  = (bb.Max.Y - bb.Min.Y) * 304.8;
    double heightMm = (bb.Max.Z - bb.Min.Z) * 304.8;

    bool fitsWidth  = widthMm  <= {900 * 1.0:.0f};  // 900 mm max
    bool fitsHeight = heightMm <= {2100 * 1.0:.0f}; // 2100 mm max
}}""",
        ))

        # Delete all instances of a specific nested family
        samples.append(_s(
            "Delete all placed instances of a nested family named 'TempComponent' from the family document",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "Remove TempComponent Instances"))
{
    tx.Start();

    Family tempFam = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Family)).Cast<Family>()
        .FirstOrDefault(f => f.Name == "TempComponent");

    if (tempFam != null)
    {
        var symIds = new HashSet<ElementId>(tempFam.GetFamilySymbolIds());
        var instIds = new FilteredElementCollector(familyDoc)
            .OfClass(typeof(FamilyInstance))
            .Cast<FamilyInstance>()
            .Where(fi => symIds.Contains(fi.GetTypeId()))
            .Select(fi => fi.Id)
            .ToList();

        foreach (var id in instIds)
            familyDoc.Delete(id);
    }

    tx.Commit();
}""",
        ))

        # Place on a face
        samples.append(_s(
            "Place a nested family instance on the face of an extrusion using NewFamilyInstance face overload",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "Place on Face"))
{
    tx.Start();

    // Get the top face of an existing extrusion
    Options geomOpts = new Options { ComputeReferences = true };
    Face topFace = null;
    foreach (GeometryObject obj in extrusion.get_Geometry(geomOpts))
    {
        if (obj is Solid solid)
        {
            foreach (Face face in solid.Faces)
            {
                if (face.ComputeNormal(UV.Zero).IsAlmostEqualTo(XYZ.BasisZ))
                {
                    topFace = face;
                    break;
                }
            }
        }
    }

    if (topFace != null)
    {
        Family compFam = new FilteredElementCollector(familyDoc)
            .OfClass(typeof(Family)).Cast<Family>()
            .FirstOrDefault(f => f.Name == "SurfaceComponent");

        FamilySymbol sym = familyDoc?.GetElement(
            compFam?.GetFamilySymbolIds().First() ?? ElementId.InvalidElementId) as FamilySymbol;

        if (sym != null)
        {
            if (!sym.IsActive) sym.Activate();
            // Place on face at UV (0.5, 0.5) -- centre of the face
            familyDoc.FamilyCreate.NewFamilyInstance(
                topFace.Evaluate(new UV(0.5, 0.5)),
                sym,
                topFace,
                familyDoc.ActiveView);
        }
    }

    tx.Commit();
}""",
        ))

        # Associate nested instance parameter with host parameter
        samples.append(_s(
            "Associate a nested family instance parameter 'Size' with a host family parameter 'Connector Size' so they flex together",
            """\
using Autodesk.Revit.DB;

// After placing the nested instance:
FamilyManager famMgr = familyDoc.FamilyManager;

// Get the host parameter that should drive the nested one
FamilyParameter hostParam = famMgr.get_Parameter("Connector Size");

// Get the instance parameter on the nested family instance
Parameter nestedParam = nestedInst.LookupParameter("Size");

if (hostParam != null && nestedParam != null && !nestedParam.IsReadOnly)
{
    // AssociateElementParameterToFamilyParameter links them
    famMgr.AssociateElementParameterToFamilyParameter(nestedParam, hostParam);
}
// Now when Connector Size changes type value, the nested Size flexes automatically""",
        ))

        # Disassociate parameter
        samples.append(_s(
            "Remove the association between a nested instance parameter 'Size' and its host family parameter",
            """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
Parameter nestedParam = nestedInst.LookupParameter("Size");

if (nestedParam != null)
{
    // DissociateElementParameterFromFamilyParameter breaks the link
    famMgr.DissociateElementParameterFromFamilyParameter(nestedInst, nestedParam.Definition);
}""",
        ))

        # Place with custom orientation transform
        samples.append(_s(
            "Place a nested hinge instance with a custom Transform that both translates and rotates it",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;
using System;

double angle90 = Math.PI / 2.0; // 90 degrees in radians

using (Transaction tx = new Transaction(familyDoc, "Place Transformed Hinge"))
{{
    tx.Start();

    Family hingeFam = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Family)).Cast<Family>()
        .FirstOrDefault(f => f.Name == "HingeComponent");

    if (hingeFam != null)
    {{
        FamilySymbol sym = familyDoc.GetElement(
            hingeFam.GetFamilySymbolIds().First()) as FamilySymbol;
        if (sym != null && !sym.IsActive) sym.Activate();

        // Place at origin first
        FamilyInstance inst = familyDoc.FamilyCreate.NewFamilyInstance(
            XYZ.Zero, sym, familyDoc.ActiveView);

        // Apply transform: move to (50mm, 0, 900mm) and rotate 90 deg about Z
        Transform rot = Transform.CreateRotation(XYZ.BasisZ, angle90);
        Transform trans = Transform.CreateTranslation(
            new XYZ({50 * MM_TO_FT:.6f}, 0, {900 * MM_TO_FT:.6f}));
        ElementTransformUtils.MoveElement(familyDoc, inst.Id,
            trans.Origin - (inst.Location as LocationPoint).Point);
        ElementTransformUtils.RotateElement(familyDoc, inst.Id,
            Line.CreateBound((inst.Location as LocationPoint).Point,
                (inst.Location as LocationPoint).Point + XYZ.BasisZ), angle90);
    }}

    tx.Commit();
}}""",
        ))

        # Check IsActive before placement
        samples.append(_s(
            "Explain why FamilySymbol.Activate() must be called before placing an instance and what happens if you skip it",
            """\
// FamilySymbol.IsActive controls whether Revit has resolved the symbol's geometry
// and made it ready for placement.
//
// Symptoms if you skip Activate():
//   - Revit throws an Autodesk.Revit.Exceptions.InvalidOperationException
//     with message "The FamilySymbol must be activated before placing."
//
// Correct pattern:
//   if (!symbol.IsActive)
//       symbol.Activate(); // must be inside an active transaction
//   familyDoc.FamilyCreate.NewFamilyInstance(point, symbol, view);
//
// Activate() is cheap -- it is safe to call it unconditionally:
//   symbol.Activate(); // no-op if already active
//
// Note: In Revit 2015 and earlier, Activate() did not exist; symbols were
// activated automatically. The explicit call is required from Revit 2016 onward.""",
        ))

        # Summarise all nested instances
        samples.append(_s(
            "Generate a CSV-style report listing every nested family instance name, type name, and XYZ location",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Text;

var sb = new StringBuilder();
sb.AppendLine("FamilyName,TypeName,X_mm,Y_mm,Z_mm");

foreach (FamilyInstance fi in new FilteredElementCollector(familyDoc)
    .OfClass(typeof(FamilyInstance)).Cast<FamilyInstance>())
{
    string famName  = fi.Symbol.Family.Name;
    string typeName = fi.Symbol.Name;
    double xMm = 0, yMm = 0, zMm = 0;

    if (fi.Location is LocationPoint lp)
    {
        xMm = lp.Point.X * 304.8;
        yMm = lp.Point.Y * 304.8;
        zMm = lp.Point.Z * 304.8;
    }
    sb.AppendLine($"{famName},{typeName},{xMm:F1},{yMm:F1},{zMm:F1}");
}
string report = sb.ToString();""",
        ))

        return samples

    # ------------------------------------------------------------------
    # Shared parameters (~30 samples)
    # ------------------------------------------------------------------

    def _shared_parameters(self) -> List[SAMPLE]:
        samples = []

        # Open shared parameter file
        samples.append(_s(
            "Open an existing shared parameter file and access its parameter groups",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.ApplicationServices;

// app is an Autodesk.Revit.ApplicationServices.Application
app.SharedParametersFilename = @"C:\SharedParams\RevitSharedParams.txt";
DefinitionFile defFile = app.OpenSharedParameterFile();

if (defFile != null)
{
    foreach (DefinitionGroup grp in defFile.Groups)
    {
        string groupName = grp.Name;
        foreach (ExternalDefinition def in grp.Definitions)
        {
            string paramName = def.Name;
            System.Guid paramGuid = def.GUID;
        }
    }
}""",
        ))

        # Create shared parameter file
        samples.append(_s(
            "Create a new shared parameter file and add a parameter group called 'Structural Data'",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.ApplicationServices;
using System.IO;

string spPath = @"C:\\SharedParams\\NewSharedParams.txt";
if (!File.Exists(spPath))
    File.Create(spPath).Close(); // create empty file

app.SharedParametersFilename = spPath;
DefinitionFile defFile = app.OpenSharedParameterFile();

// Create a group
DefinitionGroup group = defFile.Groups.get_Item("Structural Data")
    ?? defFile.Groups.Create("Structural Data");

// Create a definition
ExternalDefinitionCreationOptions opts =
    new ExternalDefinitionCreationOptions("Steel Grade", ParameterType.Text);
opts.Description = "Material grade designation, e.g. A36 or A572 Gr50";
ExternalDefinition extDef2 = group.Definitions.Create(opts) as ExternalDefinition;""",
        ))

        # Bind shared param to category -- type binding
        shared_params_type = [
            ("Fire Rating",   "BuiltInParameterGroup.PG_FIRE_PROTECTION",    "ParameterType.Text",   "OST_Doors",   "door"),
            ("Acoustic Class","BuiltInParameterGroup.PG_ENERGY_ANALYSIS",    "ParameterType.Text",   "OST_Windows", "window"),
            ("Load Capacity", "BuiltInParameterGroup.PG_STRUCTURAL_ANALYSIS","ParameterType.Number", "OST_StructuralColumns", "column"),
        ]
        for param_name, pg, pt, bic, desc in shared_params_type:
            samples.append(_s(
                f"Add the shared parameter '{param_name}' as a type parameter to the {desc} category",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.ApplicationServices;

// Step 1: Open shared parameter file
app.SharedParametersFilename = @"C:\\SharedParams\\RevitSharedParams.txt";
DefinitionFile defFile = app.OpenSharedParameterFile();
DefinitionGroup group = defFile.Groups.get_Item("Project Parameters");
ExternalDefinition extDef = group.Definitions.get_Item("{param_name}") as ExternalDefinition;

if (extDef == null)
{{
    var opts = new ExternalDefinitionCreationOptions("{param_name}", {pt});
    extDef = group.Definitions.Create(opts) as ExternalDefinition;
}}

// Step 2: Create category set and binding
CategorySet categories = app.Create.NewCategorySet();
Category cat = doc.Settings.Categories.get_Item(BuiltInCategory.{bic});
categories.Insert(cat);

// TypeBinding binds to type parameters; InstanceBinding for instance parameters
TypeBinding typeBinding = app.Create.NewTypeBinding(categories);

// Step 3: Insert into the document -- OUTSIDE transaction for family documents
using (Transaction tx = new Transaction(doc, "Add Shared Parameter"))
{{
    tx.Start();
    doc.ParameterBindings.Insert(extDef, typeBinding, {pg});
    tx.Commit();
}}""",
            ))

        # Bind shared param -- instance binding
        shared_params_inst = [
            ("Installation Date", "BuiltInParameterGroup.PG_DATA",        "ParameterType.Text",   "OST_Furniture",      "furniture"),
            ("Serial Number",     "BuiltInParameterGroup.PG_IDENTITY_DATA","ParameterType.Text",   "OST_MechanicalEquipment", "mechanical equipment"),
            ("Flow Rate",         "BuiltInParameterGroup.PG_MECHANICAL",   "ParameterType.Number", "OST_PipeAccessory",  "pipe accessory"),
        ]
        for param_name, pg, pt, bic, desc in shared_params_inst:
            samples.append(_s(
                f"Bind the shared parameter '{param_name}' as an instance parameter to the {desc} category",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.ApplicationServices;

app.SharedParametersFilename = @"C:\\SharedParams\\RevitSharedParams.txt";
DefinitionFile defFile = app.OpenSharedParameterFile();
DefinitionGroup group = defFile.Groups.get_Item("Project Parameters");
ExternalDefinition extDef = group.Definitions.get_Item("{param_name}") as ExternalDefinition;

CategorySet cats = app.Create.NewCategorySet();
Category cat = doc.Settings.Categories.get_Item(BuiltInCategory.{bic});
cats.Insert(cat);

InstanceBinding instBinding = app.Create.NewInstanceBinding(cats);

using (Transaction tx = new Transaction(doc, "Add Instance Shared Param"))
{{
    tx.Start();
    doc.ParameterBindings.Insert(extDef, instBinding, {pg});
    tx.Commit();
}}""",
            ))

        # Check if shared param already bound
        samples.append(_s(
            "Check whether a shared parameter named 'Fire Rating' is already bound in the document",
            """\
using Autodesk.Revit.DB;

bool IsSharedParamBound(Document doc, string paramName)
{
    BindingMap bindings = doc.ParameterBindings;
    DefinitionBindingMapIterator it = bindings.ForwardIterator();
    while (it.MoveNext())
    {
        if (it.Key is ExternalDefinition extDef && extDef.Name == paramName)
            return true;
    }
    return false;
}""",
        ))

        # Read shared param GUID
        samples.append(_s(
            "Retrieve the GUID of a shared parameter named 'Steel Grade' from the shared parameter file",
            """\
using Autodesk.Revit.DB;
using System;

Guid GetSharedParamGuid(Application app, string groupName, string paramName)
{
    app.SharedParametersFilename = @"C:\SharedParams\RevitSharedParams.txt";
    DefinitionFile defFile = app.OpenSharedParameterFile();
    DefinitionGroup group = defFile?.Groups.get_Item(groupName);
    ExternalDefinition def = group?.Definitions.get_Item(paramName) as ExternalDefinition;
    return def?.GUID ?? Guid.Empty;
}""",
        ))

        # Add shared param to family via FamilyManager
        samples.append(_s(
            "Add a shared parameter 'Mark' to a family document using FamilyManager.AddParameter with an ExternalDefinition",
            """\
using Autodesk.Revit.DB;

// Open shared param file
app.SharedParametersFilename = @"C:\SharedParams\RevitSharedParams.txt";
DefinitionFile defFile = app.OpenSharedParameterFile();
DefinitionGroup group = defFile.Groups.get_Item("Identity");
ExternalDefinition markDef = group.Definitions.get_Item("Mark") as ExternalDefinition;

if (markDef != null)
{
    FamilyManager famMgr = familyDoc.FamilyManager;
    // AddParameter with ExternalDefinition creates a shared parameter on the family
    FamilyParameter markParam = famMgr.AddParameter(
        markDef,
        BuiltInParameterGroup.PG_IDENTITY_DATA,
        true); // true = instance parameter
}""",
        ))

        # Re-bind (update) a shared parameter definition
        samples.append(_s(
            "Re-bind an existing shared parameter 'Fire Rating' to also include the Windows category",
            """\
using Autodesk.Revit.DB;

app.SharedParametersFilename = @"C:\SharedParams\RevitSharedParams.txt";
DefinitionFile defFile = app.OpenSharedParameterFile();
ExternalDefinition extDef = defFile.Groups
    .get_Item("Project Parameters")
    .Definitions.get_Item("Fire Rating") as ExternalDefinition;

using (Transaction tx = new Transaction(doc, "Update Binding"))
{
    tx.Start();

    BindingMap bindings = doc.ParameterBindings;

    // Remove old binding
    bindings.Remove(extDef);

    // Re-add with extended category set
    CategorySet cats = app.Create.NewCategorySet();
    cats.Insert(doc.Settings.Categories.get_Item(BuiltInCategory.OST_Doors));
    cats.Insert(doc.Settings.Categories.get_Item(BuiltInCategory.OST_Windows));
    cats.Insert(doc.Settings.Categories.get_Item(BuiltInCategory.OST_Walls));

    TypeBinding tb = app.Create.NewTypeBinding(cats);
    bindings.Insert(extDef, tb, BuiltInParameterGroup.PG_FIRE_PROTECTION);

    tx.Commit();
}""",
        ))

        # Enumerate all shared param bindings
        samples.append(_s(
            "Iterate over all shared parameter bindings in a document and print each parameter name and its bound categories",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

var report = new List<string>();
DefinitionBindingMapIterator it = doc.ParameterBindings.ForwardIterator();
while (it.MoveNext())
{
    if (it.Key is ExternalDefinition extDef)
    {
        var catNames = new List<string>();
        if (it.Current is ElementBinding binding)
        {
            foreach (Category cat in binding.Categories)
                catNames.Add(cat.Name);
        }
        report.Add($"{extDef.Name} (GUID: {extDef.GUID}) -> {string.Join(", ", catNames)}");
    }
}""",
        ))

        # Create shared param file from scratch with multiple groups
        samples.append(_s(
            "Create a shared parameter file with two groups: 'Structural Data' and 'Identity Data'",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.ApplicationServices;
using System.IO;

string spPath = @"C:\\SharedParams\\ProjectShared.txt";
if (!File.Exists(spPath)) File.Create(spPath).Close();

app.SharedParametersFilename = spPath;
DefinitionFile defFile = app.OpenSharedParameterFile();

DefinitionGroup structural = defFile.Groups.get_Item("Structural Data")
    ?? defFile.Groups.Create("Structural Data");
DefinitionGroup identity = defFile.Groups.get_Item("Identity Data")
    ?? defFile.Groups.Create("Identity Data");

// Add a parameter to each group
var structOpts = new ExternalDefinitionCreationOptions("Load Capacity", ParameterType.Number);
structural.Definitions.Create(structOpts);

var identOpts = new ExternalDefinitionCreationOptions("Asset Tag", ParameterType.Text);
identity.Definitions.Create(identOpts);""",
        ))

        # Read a shared parameter value from a placed element
        samples.append(_s(
            "Read the value of the shared parameter 'Fire Rating' from a door element using its GUID",
            """\
using Autodesk.Revit.DB;
using System;

// Known GUID for the shared parameter
Guid fireRatingGuid = new Guid("00000000-0000-0000-0000-000000000001"); // replace with real GUID

// Find the parameter on a door element by GUID
Parameter fireRatingParam = doorElement.get_Parameter(fireRatingGuid);
if (fireRatingParam != null)
{
    string rating = fireRatingParam.AsString();
}""",
        ))

        # Export shared parameter info to CSV
        samples.append(_s(
            "Export all shared parameter definitions (name, GUID, group, type) from a shared parameter file to a list",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

var defs = new List<(string Group, string Name, System.Guid Guid, string Type)>();

app.SharedParametersFilename = @"C:\\SharedParams\\ProjectShared.txt";
DefinitionFile defFile = app.OpenSharedParameterFile();

if (defFile != null)
{
    foreach (DefinitionGroup grp in defFile.Groups)
    {
        foreach (ExternalDefinition def in grp.Definitions)
        {
            defs.Add((grp.Name, def.Name, def.GUID, def.ParameterType.ToString()));
        }
    }
}""",
        ))

        # Shared param on multiple categories at once
        samples.append(_s(
            "Bind the shared parameter 'Asset ID' to four categories: Doors, Windows, Furniture, and Mechanical Equipment",
            """\
using Autodesk.Revit.DB;

app.SharedParametersFilename = @"C:\\SharedParams\\ProjectShared.txt";
DefinitionFile defFile = app.OpenSharedParameterFile();
ExternalDefinition assetDef = defFile.Groups
    .get_Item("Identity Data")
    .Definitions.get_Item("Asset ID") as ExternalDefinition;

CategorySet cats = app.Create.NewCategorySet();
BuiltInCategory[] bics = {
    BuiltInCategory.OST_Doors,
    BuiltInCategory.OST_Windows,
    BuiltInCategory.OST_Furniture,
    BuiltInCategory.OST_MechanicalEquipment,
};
foreach (var bic in bics)
    cats.Insert(doc.Settings.Categories.get_Item(bic));

InstanceBinding instBinding = app.Create.NewInstanceBinding(cats);

using (Transaction tx = new Transaction(doc, "Bind Asset ID"))
{
    tx.Start();
    doc.ParameterBindings.Insert(assetDef, instBinding,
        BuiltInParameterGroup.PG_IDENTITY_DATA);
    tx.Commit();
}""",
        ))

        # Shared param in schedule
        samples.append(_s(
            "Explain how to make a shared parameter appear in a Revit schedule after binding it",
            """\
// After binding a shared parameter to a category:
//
// 1. The parameter automatically appears in the "Add Parameter" dialog when
//    creating or modifying a schedule for that category.
//
// 2. To add it programmatically to an existing ScheduleDefinition:
//
//    ScheduleDefinition def = schedule.Definition;
//    SchedulableField field = def.GetSchedulableFields()
//        .FirstOrDefault(f => f.GetSchedulableFieldType() == SchedulableFieldType.Instance
//                          && f.ColumnHeading == "Asset ID");
//    if (field != null)
//        def.AddField(field);
//
// 3. For the shared parameter to appear as schedulable, it must be:
//    a. Bound to the schedule's category (or parent category for sub-elements)
//    b. Not hidden via ParameterElement.CanBeHiddenInSchedule
//
// 4. Shared parameters bound as InstanceBinding show per-instance values;
//    TypeBinding shows the same value for all instances of a type.""",
        ))

        # Get or create shared param definition safely
        samples.append(_s(
            "Write a helper method that gets an existing shared parameter definition or creates it if missing",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.ApplicationServices;

ExternalDefinition GetOrCreateSharedParam(
    Application app,
    string spFilePath,
    string groupName,
    string paramName,
    ParameterType paramType)
{
    app.SharedParametersFilename = spFilePath;
    DefinitionFile defFile = app.OpenSharedParameterFile();

    DefinitionGroup group = defFile.Groups.get_Item(groupName)
        ?? defFile.Groups.Create(groupName);

    ExternalDefinition existing = group.Definitions.get_Item(paramName) as ExternalDefinition;
    if (existing != null) return existing;

    var opts = new ExternalDefinitionCreationOptions(paramName, paramType)
    {
        Visible = true
    };
    return group.Definitions.Create(opts) as ExternalDefinition;
}""",
        ))

        # Shared param GUID stability
        samples.append(_s(
            "Explain why using the GUID to look up a shared parameter is more reliable than using its name",
            """\
// Shared parameter GUIDs vs names:
//
// Name-based lookup:
//   Parameter p = element.LookupParameter("Fire Rating");
//   PROBLEM: If two different shared parameter definitions happen to share the same
//   name (different GUIDs), LookupParameter returns the first match only.
//   Also, renaming the parameter in the shared param file breaks name-based lookups.
//
// GUID-based lookup (recommended):
//   Guid guid = new Guid("a1b2c3d4-...");
//   Parameter p = element.get_Parameter(guid);
//   BENEFIT: GUIDs are globally unique and immutable -- they survive renames.
//   Store GUIDs as constants in your add-in for all shared parameters.
//
// Convention: define a static class for all shared param GUIDs:
//   public static class SharedParamGuids
//   {
//       public static readonly Guid FireRating =
//           new Guid("a1b2c3d4-e5f6-7890-abcd-ef1234567890");
//   }""",
        ))

        # Remove a shared param binding
        samples.append(_s(
            "Remove the binding for a shared parameter named 'Legacy Param' from all categories",
            """\
using Autodesk.Revit.DB;

app.SharedParametersFilename = @"C:\\SharedParams\\ProjectShared.txt";
DefinitionFile defFile = app.OpenSharedParameterFile();
ExternalDefinition legacyDef = defFile.Groups
    .get_Item("Legacy")
    ?.Definitions.get_Item("Legacy Param") as ExternalDefinition;

if (legacyDef != null)
{
    using (Transaction tx = new Transaction(doc, "Remove Legacy Param"))
    {
        tx.Start();
        doc.ParameterBindings.Remove(legacyDef);
        tx.Commit();
    }
}""",
        ))

        # Check if shared param exists in shared param file
        samples.append(_s(
            "Check whether a shared parameter named 'Thermal Resistance' already exists in the shared parameter file",
            """\
using Autodesk.Revit.DB;

bool SharedParamExists(Application app, string spPath, string groupName, string paramName)
{
    app.SharedParametersFilename = spPath;
    DefinitionFile defFile = app.OpenSharedParameterFile();
    DefinitionGroup group = defFile?.Groups.get_Item(groupName);
    return group?.Definitions.get_Item(paramName) != null;
}""",
        ))

        # Bulk-add shared params to family
        shared_bulk = [
            ("Product Code",    "ParameterType.Text",   "PG_IDENTITY_DATA"),
            ("Warranty Period", "ParameterType.Integer", "PG_DATA"),
            ("Weight",          "ParameterType.Number",  "PG_STRUCTURAL"),
        ]
        bulk_code = "\n    ".join(
            f'("{n}", {pt}, BuiltInParameterGroup.{pg}),'
            for n, pt, pg in shared_bulk
        )
        samples.append(_s(
            "Add three shared parameters (Product Code, Warranty Period, Weight) to a family document in bulk",
            f"""\
using Autodesk.Revit.DB;

app.SharedParametersFilename = @"C:\\SharedParams\\ProjectShared.txt";
DefinitionFile defFile = app.OpenSharedParameterFile();
DefinitionGroup group = defFile.Groups.get_Item("Product Data")
    ?? defFile.Groups.Create("Product Data");

FamilyManager famMgr = familyDoc.FamilyManager;

var paramDefs = new (string Name, ParameterType Type, BuiltInParameterGroup Group)[]
{{
    {bulk_code}
}};

foreach (var pd in paramDefs)
{{
    ExternalDefinition extDef = group.Definitions.get_Item(pd.Name) as ExternalDefinition;
    if (extDef == null)
    {{
        var opts = new ExternalDefinitionCreationOptions(pd.Name, pd.Type);
        extDef = group.Definitions.Create(opts) as ExternalDefinition;
    }}
    if (extDef != null)
        famMgr.AddParameter(extDef, pd.Group, true); // instance param
}}""",
        ))

        # Shared param visibility
        samples.append(_s(
            "Create a shared parameter definition that is hidden from the Properties palette but still schedulable",
            """\
using Autodesk.Revit.DB;

var opts = new ExternalDefinitionCreationOptions("Internal Code", ParameterType.Text)
{
    Visible = false, // hides from Properties palette UI
    Description = "Internal tracking code -- not for user editing"
};

DefinitionGroup group = defFile.Groups.get_Item("Internal")
    ?? defFile.Groups.Create("Internal");

ExternalDefinition internalDef = group.Definitions.Create(opts) as ExternalDefinition;
// The parameter is still schedulable via SchedulableFields""",
        ))

        # Shared param with user-visible description
        samples.append(_s(
            "Create a shared parameter with a description and a tooltip that appears in the Revit UI",
            """\
using Autodesk.Revit.DB;

var opts = new ExternalDefinitionCreationOptions(
    "Fire Resistance Rating",
    ParameterType.Text)
{
    Description = "Fire resistance period in minutes, e.g. 30, 60, 90, 120.",
    Visible = true
};

DefinitionGroup group = defFile.Groups.get_Item("Fire Protection")
    ?? defFile.Groups.Create("Fire Protection");

ExternalDefinition fireDef = group.Definitions.Create(opts) as ExternalDefinition;
// Description appears as a tooltip in the Element Properties dialog""",
        ))

        # Move shared param to different group
        samples.append(_s(
            "Move an existing shared parameter definition from one group to another in the shared parameter file",
            """\
using Autodesk.Revit.DB;

// Shared parameter files do not support direct move -- you must recreate:
app.SharedParametersFilename = @"C:\\SharedParams\\ProjectShared.txt";
DefinitionFile defFile = app.OpenSharedParameterFile();

DefinitionGroup oldGroup = defFile.Groups.get_Item("Misc");
ExternalDefinition existing = oldGroup?.Definitions.get_Item("Room Volume") as ExternalDefinition;

if (existing != null)
{
    DefinitionGroup newGroup = defFile.Groups.get_Item("Space Data")
        ?? defFile.Groups.Create("Space Data");

    // Recreate with same GUID so existing project bindings remain valid
    var opts = new ExternalDefinitionCreationOptions("Room Volume", ParameterType.Volume)
    {
        GUID = existing.GUID // preserve the GUID
    };
    newGroup.Definitions.Create(opts);
    oldGroup.Definitions.Erase(existing); // remove from old group
}""",
        ))

        # Shared param on all model categories
        samples.append(_s(
            "Bind a shared parameter 'Specification Note' to all model categories in the document",
            """\
using Autodesk.Revit.DB;
using System.Linq;

app.SharedParametersFilename = @"C:\\SharedParams\\ProjectShared.txt";
DefinitionFile defFile = app.OpenSharedParameterFile();
ExternalDefinition specDef = defFile.Groups
    .get_Item("Notes")
    .Definitions.get_Item("Specification Note") as ExternalDefinition;

// Build a CategorySet from all model categories
CategorySet allModelCats = app.Create.NewCategorySet();
foreach (Category cat in doc.Settings.Categories)
{
    if (cat.CategoryType == CategoryType.Model && cat.AllowsBoundParameters)
        allModelCats.Insert(cat);
}

InstanceBinding binding = app.Create.NewInstanceBinding(allModelCats);

using (Transaction tx = new Transaction(doc, "Bind Spec Note"))
{
    tx.Start();
    doc.ParameterBindings.Insert(specDef, binding, BuiltInParameterGroup.PG_TEXT);
    tx.Commit();
}""",
        ))

        # Shared param value set via FilteredElementCollector
        samples.append(_s(
            "Set the 'Asset ID' shared parameter to a unique value on every door in the project",
            """\
using Autodesk.Revit.DB;
using System;

Guid assetIdGuid = new Guid("a1b2c3d4-e5f6-7890-abcd-ef1234567890");

using (Transaction tx = new Transaction(doc, "Set Asset IDs"))
{
    tx.Start();
    int counter = 1;
    foreach (FamilyInstance door in new FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Doors)
        .OfClass(typeof(FamilyInstance))
        .Cast<FamilyInstance>())
    {
        Parameter p = door.get_Parameter(assetIdGuid);
        if (p != null && !p.IsReadOnly)
            p.Set($"DOOR-{counter++:D4}");
    }
    tx.Commit();
}""",
        ))

        # Shared param on annotation
        samples.append(_s(
            "Bind a shared parameter 'Revision Code' to the General Annotations category for use in annotation families",
            """\
using Autodesk.Revit.DB;

app.SharedParametersFilename = @"C:\\SharedParams\\ProjectShared.txt";
DefinitionFile defFile = app.OpenSharedParameterFile();
ExternalDefinition revDef = defFile.Groups
    .get_Item("Revision Data")
    .Definitions.get_Item("Revision Code") as ExternalDefinition;

CategorySet cats = app.Create.NewCategorySet();
cats.Insert(doc.Settings.Categories.get_Item(BuiltInCategory.OST_GenericAnnotation));

TypeBinding tb = app.Create.NewTypeBinding(cats);

using (Transaction tx = new Transaction(doc, "Bind Revision Code"))
{
    tx.Start();
    doc.ParameterBindings.Insert(revDef, tb, BuiltInParameterGroup.PG_IDENTITY_DATA);
    tx.Commit();
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # Type iteration and queries (~35 samples)
    # ------------------------------------------------------------------

    def _type_iteration_queries(self) -> List[SAMPLE]:
        samples = []

        # Iterate types and read one parameter
        param_queries = [
            ("Width",  "length", "widthFt * 304.8",  "door family",    "door width"),
            ("Height", "length", "heightFt * 304.8", "window family",  "window height"),
            ("Depth",  "length", "depthFt * 304.8",  "column family",  "section depth"),
        ]
        for pname, ptype, convert_expr, family_type, desc in param_queries:
            samples.append(_s(
                f"Iterate all family types and print the {desc} value for each",
                f"""\
using Autodesk.Revit.DB;
using System.Collections.Generic;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter p{pname} = famMgr.get_Parameter("{pname}");

var results = new Dictionary<string, double>();

foreach (FamilyType ft in famMgr.Types)
{{
    famMgr.CurrentType = ft;
    if (p{pname} != null)
    {{
        double {pname.lower()}Ft = ft.AsDouble(p{pname});
        results[ft.Name] = {convert_expr}; // convert ft -> mm
    }}
}}
// results maps type name to {desc} in mm""",
            ))

        # Filter types by parameter value
        samples.append(_s(
            "Find all family types where Width is greater than or equal to 900mm",
            f"""\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth = famMgr.get_Parameter("Width");
double minWidthFt = {900 * MM_TO_FT:.6f}; // 900 mm in feet

var wideTypes = famMgr.Types
    .Cast<FamilyType>()
    .Where(ft => pWidth != null && ft.AsDouble(pWidth) >= minWidthFt)
    .Select(ft => ft.Name)
    .ToList();""",
        ))

        # Sort types by parameter
        samples.append(_s(
            "Sort all family types by their Height parameter value (ascending) and return the sorted names",
            f"""\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pHeight = famMgr.get_Parameter("Height");

var sorted = famMgr.Types
    .Cast<FamilyType>()
    .OrderBy(ft => pHeight != null ? ft.AsDouble(pHeight) : 0)
    .Select(ft => ft.Name)
    .ToList();""",
        ))

        # Check parameter has formula
        samples.append(_s(
            "Identify which family parameters have formulas set and print the formula strings",
            """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
foreach (FamilyParameter fp in famMgr.Parameters)
{
    if (fp.IsDetermined) // driven by formula
    {
        string formula = famMgr.CurrentType?.AsString(fp) ?? "(no value)";
        // Access formula string through the FamilyParameter.Formula property (Revit 2023+)
        // For older versions: reflection or UI inspection is needed
    }
}""",
        ))

        # Read integer parameter
        samples.append(_s(
            "Iterate all family types and read the integer value of the 'Panel Count' parameter",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pPanels = famMgr.get_Parameter("Panel Count");

var panelCounts = new Dictionary<string, int>();
foreach (FamilyType ft in famMgr.Types)
{
    famMgr.CurrentType = ft;
    if (pPanels != null && pPanels.StorageType == StorageType.Integer)
        panelCounts[ft.Name] = ft.AsInteger(pPanels);
}""",
        ))

        # Read string parameter
        samples.append(_s(
            "Collect the 'Manufacturer' text parameter value for every family type",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pMfr = famMgr.get_Parameter("Manufacturer");

var manufacturers = new Dictionary<string, string>();
foreach (FamilyType ft in famMgr.Types)
{
    famMgr.CurrentType = ft;
    if (pMfr != null && pMfr.StorageType == StorageType.String)
        manufacturers[ft.Name] = ft.AsString(pMfr) ?? string.Empty;
}""",
        ))

        # Read ElementId parameter (material)
        samples.append(_s(
            "For each family type, retrieve the ElementId of the 'Body Material' parameter",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pMat = famMgr.get_Parameter("Body Material");

var materialIds = new Dictionary<string, ElementId>();
foreach (FamilyType ft in famMgr.Types)
{
    famMgr.CurrentType = ft;
    if (pMat != null && pMat.StorageType == StorageType.ElementId)
        materialIds[ft.Name] = ft.AsElementId(pMat);
}""",
        ))

        # Compare two types
        samples.append(_s(
            "Compare the Width and Height of two family types ('Small' and 'Large') and determine which is taller",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pHeight = famMgr.get_Parameter("Height");

FamilyType small = famMgr.Types.Cast<FamilyType>().FirstOrDefault(t => t.Name == "Small");
FamilyType large = famMgr.Types.Cast<FamilyType>().FirstOrDefault(t => t.Name == "Large");

if (small != null && large != null && pHeight != null)
{
    double smallH = small.AsDouble(pHeight) * 304.8; // mm
    double largeH = large.AsDouble(pHeight) * 304.8; // mm
    bool largeIsTaller = largeH > smallH;
}""",
        ))

        # Find the largest type
        samples.append(_s(
            "Find the family type with the largest Width parameter value",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth = famMgr.get_Parameter("Width");

FamilyType widest = famMgr.Types
    .Cast<FamilyType>()
    .OrderByDescending(ft => pWidth != null ? ft.AsDouble(pWidth) : 0)
    .FirstOrDefault();""",
        ))

        # Dump all parameters and values for a type
        samples.append(_s(
            "Dump all FamilyParameter names and their values for the currently active family type",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyType currentType = famMgr.CurrentType;
var dump = new Dictionary<string, object>();

foreach (FamilyParameter fp in famMgr.Parameters)
{
    object val = fp.StorageType switch
    {
        StorageType.Double    => currentType.AsDouble(fp),
        StorageType.Integer   => currentType.AsInteger(fp),
        StorageType.String    => currentType.AsString(fp),
        StorageType.ElementId => currentType.AsElementId(fp),
        _                     => null
    };
    dump[fp.Definition.Name] = val;
}""",
        ))

        # Verify parameter consistency across types
        samples.append(_s(
            "Check that all family types have a non-zero Width parameter (data validation)",
            f"""\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth = famMgr.get_Parameter("Width");

var invalidTypes = famMgr.Types
    .Cast<FamilyType>()
    .Where(ft => pWidth == null || ft.AsDouble(pWidth) <= 0)
    .Select(ft => ft.Name)
    .ToList();

// invalidTypes lists every type missing a valid Width value""",
        ))

        # Group types by Height
        samples.append(_s(
            "Group family types into 'standard' (height <= 2100mm) and 'tall' (height > 2100mm) categories",
            f"""\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pHeight = famMgr.get_Parameter("Height");
double thresholdFt = {2100 * MM_TO_FT:.6f}; // 2100 mm

var standard = new List<string>();
var tall     = new List<string>();

foreach (FamilyType ft in famMgr.Types)
{{
    double h = pHeight != null ? ft.AsDouble(pHeight) : 0;
    if (h <= thresholdFt) standard.Add(ft.Name);
    else                  tall.Add(ft.Name);
}}""",
        ))

        # Collect all unique material ids across types
        samples.append(_s(
            "Collect all unique material ElementIds used across all family types for the 'Body Material' parameter",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pMat = famMgr.get_Parameter("Body Material");

var uniqueMatIds = new HashSet<ElementId>();
foreach (FamilyType ft in famMgr.Types)
{
    if (pMat != null && pMat.StorageType == StorageType.ElementId)
    {
        ElementId matId = ft.AsElementId(pMat);
        if (matId != null && matId != ElementId.InvalidElementId)
            uniqueMatIds.Add(matId);
    }
}""",
        ))

        # Check if parameter has same value across all types
        samples.append(_s(
            "Check whether the 'Thickness' parameter has the same value in all family types",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pThick = famMgr.get_Parameter("Thickness");

var values = famMgr.Types
    .Cast<FamilyType>()
    .Select(ft => pThick != null ? ft.AsDouble(pThick) : double.NaN)
    .ToList();

bool allSame = values.Distinct().Count() == 1;""",
        ))

        # Get type with minimum area
        samples.append(_s(
            "Find the family type with the smallest cross-sectional area (Width * Depth)",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW = famMgr.get_Parameter("Width");
FamilyParameter pD = famMgr.get_Parameter("Depth");

FamilyType smallest = famMgr.Types
    .Cast<FamilyType>()
    .OrderBy(ft =>
    {{
        double w = pW != null ? ft.AsDouble(pW) : 0;
        double d = pD != null ? ft.AsDouble(pD) : 0;
        return w * d; // area in ft^2
    }})
    .FirstOrDefault();""",
        ))

        # Query types whose name matches a pattern
        samples.append(_s(
            "Find all family types whose name starts with 'W' (W-section steel)",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;

var wSections = famMgr.Types
    .Cast<FamilyType>()
    .Where(ft => ft.Name.StartsWith("W", System.StringComparison.OrdinalIgnoreCase))
    .Select(ft => ft.Name)
    .ToList();""",
        ))

        # Types with Yes/No param set to true
        samples.append(_s(
            "Collect all family types where the 'Has Frame' Yes/No parameter is set to true (1)",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pHasFrame = famMgr.get_Parameter("Has Frame");

var framedTypes = famMgr.Types
    .Cast<FamilyType>()
    .Where(ft => pHasFrame != null && ft.AsInteger(pHasFrame) == 1)
    .Select(ft => ft.Name)
    .ToList();""",
        ))

        # Calculate average Height across all types
        samples.append(_s(
            "Calculate the average Height parameter value (in mm) across all family types",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pHeight = famMgr.get_Parameter("Height");

double avgMm = famMgr.Types
    .Cast<FamilyType>()
    .Where(ft => pHeight != null)
    .Average(ft => ft.AsDouble(pHeight) * 304.8);""",
        ))

        # Find types with parameter value in a range
        samples.append(_s(
            "Find all family types where Height is between 2000mm and 2200mm (inclusive)",
            f"""\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pH = famMgr.get_Parameter("Height");
double minFt = {2000 * MM_TO_FT:.6f}; // 2000 mm
double maxFt = {2200 * MM_TO_FT:.6f}; // 2200 mm

var inRange = famMgr.Types
    .Cast<FamilyType>()
    .Where(ft => pH != null && ft.AsDouble(pH) >= minFt && ft.AsDouble(pH) <= maxFt)
    .Select(ft => ft.Name)
    .ToList();""",
        ))

        # Detect formula-driven parameters
        samples.append(_s(
            "List all family parameters that are formula-driven (IsDetermined == true) on the current type",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
var formulaDriven = famMgr.Parameters
    .Cast<FamilyParameter>()
    .Where(fp => fp.IsDetermined)
    .Select(fp => fp.Definition.Name)
    .ToList();
// formulaDriven lists parameters whose value is computed from a formula""",
        ))

        # Type lookup by parameter value
        samples.append(_s(
            "Find the family type whose Width parameter value is closest to a given target (850mm)",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth = famMgr.get_Parameter("Width");
double targetFt = {850 * MM_TO_FT:.6f}; // 850 mm

FamilyType closest = famMgr.Types
    .Cast<FamilyType>()
    .OrderBy(ft => Math.Abs((pWidth != null ? ft.AsDouble(pWidth) : 0) - targetFt))
    .FirstOrDefault();""",
        ))

        # Export type data to JSON-like structure
        samples.append(_s(
            "Build a list of anonymous objects (one per type) containing name, width, and height for JSON serialization",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW = famMgr.get_Parameter("Width");
FamilyParameter pH = famMgr.get_Parameter("Height");

var data = famMgr.Types
    .Cast<FamilyType>()
    .Select(ft => new
    {
        name      = ft.Name,
        widthMm   = pW != null ? ft.AsDouble(pW) * 304.8 : 0.0,
        heightMm  = pH != null ? ft.AsDouble(pH) * 304.8 : 0.0,
    })
    .ToList();
// Serialize with Newtonsoft.Json: JsonConvert.SerializeObject(data, Formatting.Indented)""",
        ))

        # Detect missing parameters
        samples.append(_s(
            "Detect which family types are missing a value for the 'Description' text parameter",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pDesc = famMgr.get_Parameter("Description");

var missing = famMgr.Types
    .Cast<FamilyType>()
    .Where(ft => pDesc == null || string.IsNullOrWhiteSpace(ft.AsString(pDesc)))
    .Select(ft => ft.Name)
    .ToList();""",
        ))

        # Compare types: ratio of dimensions
        samples.append(_s(
            "Calculate the aspect ratio (Width / Height) for every family type and flag those outside 0.3-0.7",
            f"""\
using Autodesk.Revit.DB;
using System.Collections.Generic;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW = famMgr.get_Parameter("Width");
FamilyParameter pH = famMgr.get_Parameter("Height");

var flagged = new List<string>();
foreach (FamilyType ft in famMgr.Types)
{{
    double w = pW != null ? ft.AsDouble(pW) : 0;
    double h = pH != null ? ft.AsDouble(pH) : 0;
    if (h > 0)
    {{
        double ratio = w / h;
        if (ratio < 0.3 || ratio > 0.7)
            flagged.Add($"{{ft.Name}} (ratio={{ratio:F2}})");
    }}
}}""",
        ))

        # Iterate and update a parameter in bulk
        samples.append(_s(
            "Increase the 'Frame Width' parameter by 10mm on every family type that currently has a value below 50mm",
            f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pFrame = famMgr.get_Parameter("Frame Width");
double thresholdFt = {50 * MM_TO_FT:.6f}; // 50 mm
double incrementFt = {10 * MM_TO_FT:.6f}; // 10 mm

foreach (FamilyType ft in famMgr.Types)
{{
    famMgr.CurrentType = ft;
    if (pFrame != null && ft.AsDouble(pFrame) < thresholdFt)
        famMgr.Set(pFrame, ft.AsDouble(pFrame) + incrementFt);
}}""",
        ))

        # Explain AsDouble vs AsValueString
        samples.append(_s(
            "Explain the difference between FamilyType.AsDouble and FamilyType.AsValueString for a length parameter",
            """\
// FamilyType.AsDouble(param):
//   Returns the raw internal value in Revit's internal units (FEET for length).
//   Always returns a double regardless of the display unit setting.
//   Example: Width = 900mm --> AsDouble returns 0.984252 (ft)
//   Use for calculations; convert with: valueMm = valueDouble * 304.8
//
// FamilyType.AsValueString(param):
//   Returns a formatted string in the DOCUMENT's current display units.
//   If the project uses mm, "900mm" is returned; if feet, "2' 11 37/64\"" is returned.
//   Use for display and reports, NOT for calculations (the format varies).
//
// Best practice:
//   - Always use AsDouble for programmatic comparisons and math
//   - Use AsValueString only for UI labels or schedule export text""",
        ))

        # Query type parameter StorageType
        samples.append(_s(
            "Before reading a parameter value, check its StorageType to call the correct As* method",
            """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyType currentType = famMgr.CurrentType;

foreach (FamilyParameter fp in famMgr.Parameters)
{
    object value = null;
    switch (fp.StorageType)
    {
        case StorageType.Double:
            value = currentType.AsDouble(fp);
            break;
        case StorageType.Integer:
            value = currentType.AsInteger(fp);
            break;
        case StorageType.String:
            value = currentType.AsString(fp);
            break;
        case StorageType.ElementId:
            value = currentType.AsElementId(fp);
            break;
    }
    // 'value' is now the typed value for this parameter on the current type
}""",
        ))

        # Detect parameter group
        samples.append(_s(
            "List all parameters that belong to the PG_GEOMETRY parameter group",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;

var geomParams = famMgr.Parameters
    .Cast<FamilyParameter>()
    .Where(fp =>
    {
        var intDef = fp.Definition as InternalDefinition;
        return intDef?.ParameterGroup == BuiltInParameterGroup.PG_GEOMETRY;
    })
    .Select(fp => fp.Definition.Name)
    .ToList();""",
        ))

        # Types in ascending order of area
        samples.append(_s(
            "Return family types sorted by cross-sectional area (Width x Depth) in ascending order",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW = famMgr.get_Parameter("Width");
FamilyParameter pD = famMgr.get_Parameter("Depth");

var sorted = famMgr.Types
    .Cast<FamilyType>()
    .OrderBy(ft =>
    {
        double w = pW != null ? ft.AsDouble(pW) : 0;
        double d = pD != null ? ft.AsDouble(pD) : 0;
        return w * d;
    })
    .Select(ft => ft.Name)
    .ToList();""",
        ))

        # Check if any type has a material parameter set to InvalidElementId
        samples.append(_s(
            "Find family types where the 'Body Material' parameter is unset (InvalidElementId)",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pMat = famMgr.get_Parameter("Body Material");

var unsetMaterial = famMgr.Types
    .Cast<FamilyType>()
    .Where(ft =>
    {
        if (pMat == null) return true;
        ElementId matId = ft.AsElementId(pMat);
        return matId == null || matId == ElementId.InvalidElementId;
    })
    .Select(ft => ft.Name)
    .ToList();""",
        ))

        # Get all parameter names
        samples.append(_s(
            "Get a flat list of all parameter names (both instance and type) defined in the family",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;

var allParamNames = famMgr.Parameters
    .Cast<FamilyParameter>()
    .Select(fp => fp.Definition.Name)
    .OrderBy(n => n)
    .ToList();""",
        ))

        return samples

    # ------------------------------------------------------------------
    # Family category assignment (~25 samples)
    # ------------------------------------------------------------------

    def _family_category_assignment(self) -> List[SAMPLE]:
        samples = []

        # Set family category
        categories = [
            ("OST_Doors",                "Doors",                "door family"),
            ("OST_Windows",              "Windows",              "window family"),
            ("OST_Furniture",            "Furniture",            "furniture family"),
            ("OST_MechanicalEquipment",  "Mechanical Equipment", "mechanical equipment family"),
            ("OST_StructuralColumns",    "Structural Columns",   "structural column family"),
            ("OST_StructuralFraming",    "Structural Framing",   "structural beam/brace family"),
            ("OST_PipeFittings",         "Pipe Fittings",        "pipe fitting family"),
            ("OST_LightingFixtures",     "Lighting Fixtures",    "lighting fixture family"),
            ("OST_GenericModel",         "Generic Models",       "generic model family"),
            ("OST_Casework",             "Casework",             "casework family"),
        ]
        for bic, cat_name, desc in categories:
            samples.append(_s(
                f"Set the family category to '{cat_name}' for a {desc}",
                f"""\
using Autodesk.Revit.DB;

// Set family category -- must be done inside a transaction
using (Transaction tx = new Transaction(familyDoc, "Set Family Category"))
{{
    tx.Start();

    Category targetCat = familyDoc.Settings.Categories
        .get_Item(BuiltInCategory.{bic});

    if (targetCat != null)
        familyDoc.OwnerFamily.FamilyCategory = targetCat;

    tx.Commit();
}}""",
            ))

        # Read current category
        samples.append(_s(
            "Read the current category of a family document and print its name",
            """\
using Autodesk.Revit.DB;

Category familyCategory = familyDoc.OwnerFamily?.FamilyCategory;
if (familyCategory != null)
{
    string categoryName = familyCategory.Name;
    BuiltInCategory bic = (BuiltInCategory)familyCategory.Id.IntegerValue;
}""",
        ))

        # Create subcategory
        subcategory_cases = [
            ("Frame",         "Glass",          "door frame subcategory"),
            ("Hardware",      "Doors",          "door hardware subcategory"),
            ("Mullion",       "Windows",        "window mullion subcategory"),
            ("Web",           "Structural Framing", "beam web subcategory"),
            ("Flange",        "Structural Framing", "beam flange subcategory"),
        ]
        for subcat_name, parent_name, desc in subcategory_cases:
            samples.append(_s(
                f"Create a subcategory '{subcat_name}' under the '{parent_name}' category for {desc}",
                f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Subcategory"))
{{
    tx.Start();

    Categories cats = familyDoc.Settings.Categories;
    Category parentCat = cats.get_Item("{parent_name}");

    if (parentCat != null)
    {{
        Category subCat = cats.NewSubcategory(parentCat, "{subcat_name}");
        // Optionally set a display colour
        subCat.LineColor = new Color(128, 128, 128);
    }}

    tx.Commit();
}}""",
            ))

        # Assign element to subcategory
        samples.append(_s(
            "Assign a family extrusion to the 'Frame' subcategory of the Doors category",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Assign Subcategory"))
{
    tx.Start();

    Category subCat = familyDoc.Settings.Categories
        .get_Item("Doors")
        ?.SubCategories
        .get_Item("Frame");

    if (subCat != null && frameExtrusion != null)
    {
        // Set the subcategory on the element's graphical parameter
        Parameter subcatParam = frameExtrusion
            .get_Parameter(BuiltInParameter.FAMILY_ELEM_SUBCATEGORY);
        if (subcatParam != null && !subcatParam.IsReadOnly)
            subcatParam.Set(subCat.Id);
    }

    tx.Commit();
}""",
        ))

        # List available subcategories
        samples.append(_s(
            "List all existing subcategories of the 'Doors' category in a family document",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

var subCatNames = new List<string>();
Category doorsCat = familyDoc.Settings.Categories.get_Item("Doors");
if (doorsCat != null)
{
    foreach (Category sub in doorsCat.SubCategories)
        subCatNames.Add(sub.Name);
}""",
        ))

        # Set subcategory line weight
        samples.append(_s(
            "Set the projection line weight of the 'Frame' subcategory to 3 (medium) in a door family",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Set Line Weight"))
{
    tx.Start();

    Category subCat = familyDoc.Settings.Categories
        .get_Item("Doors")
        ?.SubCategories.get_Item("Frame");

    if (subCat != null)
    {
        // SetLineWeight: first arg is weight (1-16), second is projection (0) or cut (1)
        subCat.SetLineWeight(3, GraphicsStyleType.Projection);
        subCat.SetLineWeight(5, GraphicsStyleType.Cut);
    }

    tx.Commit();
}""",
        ))

        # Set subcategory line pattern
        samples.append(_s(
            "Set a dashed line pattern on the 'Hidden Lines' subcategory of a structural framing family",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "Set Hidden Line Pattern"))
{
    tx.Start();

    Category hiddenSub = familyDoc.Settings.Categories
        .get_Item("Structural Framing")
        ?.SubCategories.get_Item("Hidden Lines");

    if (hiddenSub != null)
    {
        // Find the Dash line pattern
        LinePatternElement dashPattern = new FilteredElementCollector(familyDoc)
            .OfClass(typeof(LinePatternElement))
            .Cast<LinePatternElement>()
            .FirstOrDefault(lp => lp.Name.Contains("Dash"));

        if (dashPattern != null)
            hiddenSub.SetLinePatternId(dashPattern.Id, GraphicsStyleType.Projection);
    }

    tx.Commit();
}""",
        ))

        # Delete subcategory
        samples.append(_s(
            "Delete the 'Temporary' subcategory from a family document if it exists",
            """\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Delete Subcategory"))
{
    tx.Start();

    Category parentCat = familyDoc.Settings.Categories
        .get_Item(familyDoc.OwnerFamily.FamilyCategory.Name);

    Category tempSub = parentCat?.SubCategories.get_Item("Temporary");
    if (tempSub != null)
        familyDoc.Delete(tempSub.Id);

    tx.Commit();
}""",
        ))

        # Assign material to subcategory
        samples.append(_s(
            "Assign a material to the 'Glass' subcategory in a door family so glazed elements render with the glass material",
            """\
using Autodesk.Revit.DB;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "Set Subcategory Material"))
{
    tx.Start();

    Category glassSub = familyDoc.Settings.Categories
        .get_Item("Doors")?.SubCategories.get_Item("Glass");

    if (glassSub != null)
    {
        Material glassMat = new FilteredElementCollector(familyDoc)
            .OfClass(typeof(Material))
            .Cast<Material>()
            .FirstOrDefault(m => m.Name.Contains("Glass"));

        if (glassMat != null)
            glassSub.Material = glassMat;
    }

    tx.Commit();
}""",
        ))

        # Check category supports parameters
        samples.append(_s(
            "Check whether the current family category supports parameter binding before attempting to bind",
            """\
using Autodesk.Revit.DB;

Category familyCat = familyDoc.OwnerFamily?.FamilyCategory;

if (familyCat != null && familyCat.AllowsBoundParameters)
{
    // Safe to add parameters
    FamilyManager famMgr = familyDoc.FamilyManager;
    FamilyParameter p = famMgr.AddParameter(
        "Custom Param",
        BuiltInParameterGroup.PG_DATA,
        ParameterType.Text,
        true);
}
else
{
    // e.g. Detail Component families do not support all parameter types
}""",
        ))

        # Conditional category assignment with switch
        samples.append(_s(
            "Write a helper method that returns the correct BuiltInCategory for a given family use-case string",
            """\
using Autodesk.Revit.DB;

BuiltInCategory GetCategoryForUseCase(string useCase)
{
    return useCase.ToLowerInvariant() switch
    {
        "door"           => BuiltInCategory.OST_Doors,
        "window"         => BuiltInCategory.OST_Windows,
        "column"         => BuiltInCategory.OST_StructuralColumns,
        "beam"           => BuiltInCategory.OST_StructuralFraming,
        "pipe fitting"   => BuiltInCategory.OST_PipeFittings,
        "duct fitting"   => BuiltInCategory.OST_DuctFittings,
        "lighting"       => BuiltInCategory.OST_LightingFixtures,
        "furniture"      => BuiltInCategory.OST_Furniture,
        "casework"       => BuiltInCategory.OST_Casework,
        "equipment"      => BuiltInCategory.OST_MechanicalEquipment,
        _                => BuiltInCategory.OST_GenericModel
    };
}""",
        ))

        # Explain category vs sub-category for element visibility
        samples.append(_s(
            "Explain the relationship between family category, subcategory, and element visibility in Revit views",
            """\
// Category hierarchy in Revit families:
//
// Family Category (e.g. Doors):
//   - Set on the entire family (familyDoc.OwnerFamily.FamilyCategory)
//   - Determines where the family appears in schedules, filters, and the
//     View / Visibility-Graphics (V/G) dialog
//
// Sub-Category (e.g. Doors > Frame):
//   - Created inside the family with Categories.NewSubcategory(parentCat, name)
//   - Assigned to individual geometry elements (extrusions, sweeps, etc.)
//   - Allows per-element visibility override in V/G: users can turn off
//     'Frame' while keeping 'Panel' visible
//   - Each sub-category can have its own line weight, line colour, and material
//
// Best practice:
//   - Create named sub-categories for all logically separate geometry groups
//   - Assign every element to a sub-category (default = parent category)
//   - Use sub-categories to support BIM workflows that need selective visibility""",
        ))

        return samples

    # ------------------------------------------------------------------
    # Type duplication (~25 samples)
    # ------------------------------------------------------------------

    def _type_duplication(self) -> List[SAMPLE]:
        samples = []

        # Basic duplication pattern
        dup_cases = [
            ("Standard",  "Standard-Wide",  "Width",  900,  1200, "widen a standard door type"),
            ("Base",      "Base-Tall",       "Height", 2100, 2400, "create a tall variant of the base type"),
            ("Default",   "Default-Narrow",  "Width",  900,  750,  "narrow variant for accessible clearance"),
        ]
        for source, dest, param, old_mm, new_mm, desc in dup_cases:
            old_ft = old_mm * MM_TO_FT
            new_ft = new_mm * MM_TO_FT
            samples.append(_s(
                f"Duplicate the '{source}' family type to '{dest}' and change its {param} ({desc})",
                f"""\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;

// Select source type
FamilyType sourceType = famMgr.Types
    .Cast<FamilyType>()
    .FirstOrDefault(t => t.Name == "{source}");

if (sourceType != null)
{{
    famMgr.CurrentType = sourceType;

    // DuplicateCurrentType copies all parameter values from the current type
    FamilyType newType = famMgr.DuplicateCurrentType("{dest}");

    // Modify the duplicated type
    FamilyParameter p{param} = famMgr.get_Parameter("{param}");
    if (p{param} != null)
        famMgr.Set(p{param}, {new_ft:.6f}); // {new_mm} mm
}}""",
            ))

        # Duplicate and set multiple params
        samples.append(_s(
            "Duplicate the 'Single-762x2032' door type to 'Single-914x2134' and update Width and Height",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth  = famMgr.get_Parameter("Width");
FamilyParameter pHeight = famMgr.get_Parameter("Height");

FamilyType source = famMgr.Types
    .Cast<FamilyType>()
    .FirstOrDefault(t => t.Name == "Single-762x2032");

if (source != null)
{{
    famMgr.CurrentType = source;
    FamilyType newType = famMgr.DuplicateCurrentType("Single-914x2134");

    if (pWidth  != null) famMgr.Set(pWidth,  {914  * MM_TO_FT:.6f}); // 914 mm
    if (pHeight != null) famMgr.Set(pHeight, {2134 * MM_TO_FT:.6f}); // 2134 mm
}}""",
        ))

        # Duplicate a column type for each W-section
        w_sections = [
            ("W200x22",  206, 166),
            ("W250x33",  259, 254),
            ("W310x45",  313, 166),
        ]
        samples.append(_s(
            "Starting from a 'W150x13' base type, duplicate and create W200x22, W250x33, and W310x45 types",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pDepth = famMgr.get_Parameter("d");
FamilyParameter pFlange = famMgr.get_Parameter("bf");

FamilyType baseType = famMgr.Types
    .Cast<FamilyType>()
    .FirstOrDefault(t => t.Name == "W150x13");

if (baseType != null)
{{
    var newSections = new (string Name, double DepthMm, double FlangeWidthMm)[]
    {{
        ("{w_sections[0][0]}", {w_sections[0][1]}, {w_sections[0][2]}),
        ("{w_sections[1][0]}", {w_sections[1][1]}, {w_sections[1][2]}),
        ("{w_sections[2][0]}", {w_sections[2][1]}, {w_sections[2][2]}),
    }};

    foreach (var sec in newSections)
    {{
        famMgr.CurrentType = baseType;
        FamilyType nt = famMgr.DuplicateCurrentType(sec.Name);
        if (pDepth  != null) famMgr.Set(pDepth,  sec.DepthMm * {MM_TO_FT:.6f});
        if (pFlange != null) famMgr.Set(pFlange, sec.FlangeWidthMm * {MM_TO_FT:.6f});
    }}
}}""",
        ))

        # Batch duplicate with name suffix
        samples.append(_s(
            "Duplicate every existing family type and append '_Mirror' to each copy (bulk duplication)",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;

// Snapshot the original list before modifying
var originalTypes = famMgr.Types.Cast<FamilyType>().ToList();

foreach (FamilyType ft in originalTypes)
{
    famMgr.CurrentType = ft;
    string mirrorName = ft.Name + "_Mirror";

    bool alreadyExists = famMgr.Types
        .Cast<FamilyType>()
        .Any(t => t.Name == mirrorName);

    if (!alreadyExists)
        famMgr.DuplicateCurrentType(mirrorName);
}""",
        ))

        # Duplicate and override formula
        samples.append(_s(
            "Duplicate the 'Standard' type to 'Slimline' and remove the Height formula so it can be set manually",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pHeight = famMgr.get_Parameter("Height");

FamilyType standard = famMgr.Types
    .Cast<FamilyType>()
    .FirstOrDefault(t => t.Name == "Standard");

if (standard != null)
{
    famMgr.CurrentType = standard;
    FamilyType slimline = famMgr.DuplicateCurrentType("Slimline");

    // Remove formula -- set to empty string
    if (pHeight != null)
    {
        famMgr.SetFormula(pHeight, null); // null clears the formula
        famMgr.Set(pHeight, 1800 * (1.0 / 304.8)); // 1800 mm
    }
}""",
        ))

        # Duplicate with material change
        samples.append(_s(
            "Duplicate the 'Oak-Veneer' door type to 'Painted-White' and change its material parameter",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pMat = famMgr.get_Parameter("Door Material");

FamilyType oakType = famMgr.Types
    .Cast<FamilyType>()
    .FirstOrDefault(t => t.Name == "Oak-Veneer");

if (oakType != null)
{
    famMgr.CurrentType = oakType;
    FamilyType whiteType = famMgr.DuplicateCurrentType("Painted-White");

    if (pMat != null)
    {
        Material paintedMat = new FilteredElementCollector(familyDoc)
            .OfClass(typeof(Material))
            .Cast<Material>()
            .FirstOrDefault(m => m.Name.Contains("White Paint"));

        if (paintedMat != null)
            famMgr.Set(pMat, paintedMat.Id);
    }
}""",
        ))

        # Duplicate and rename batch (size matrix)
        widths  = [600, 700, 800, 900, 1000]
        heights = [2000, 2100, 2200]
        first_w, first_h = widths[0], heights[0]
        type_matrix_code_lines = []
        for w in widths:
            for h in heights:
                type_matrix_code_lines.append(
                    f'    ("{w}x{h}", {w * MM_TO_FT:.6f}, {h * MM_TO_FT:.6f}),'
                )
        type_matrix_block = "\n".join(type_matrix_code_lines)
        samples.append(_s(
            f"Generate a full size matrix of door types from {first_w}x{first_h} to {widths[-1]}x{heights[-1]}mm by duplicating a base type",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth  = famMgr.get_Parameter("Width");
FamilyParameter pHeight = famMgr.get_Parameter("Height");

FamilyType baseType = famMgr.Types.Cast<FamilyType>().First();

var matrix = new (string Name, double WidthFt, double HeightFt)[]
{{
{type_matrix_block}
}};

foreach (var entry in matrix)
{{
    bool exists = famMgr.Types.Cast<FamilyType>().Any(t => t.Name == entry.Name);
    if (exists) continue;

    famMgr.CurrentType = baseType;
    FamilyType newType = famMgr.DuplicateCurrentType(entry.Name);
    if (pWidth  != null) famMgr.Set(pWidth,  entry.WidthFt);
    if (pHeight != null) famMgr.Set(pHeight, entry.HeightFt);
}}""",
        ))

        # Verify duplication result
        samples.append(_s(
            "After duplicating a type, verify the new type exists and its parameter value is correct",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth = famMgr.get_Parameter("Width");

// Duplicate and verify
FamilyType baseType = famMgr.Types.Cast<FamilyType>().First();
famMgr.CurrentType = baseType;
FamilyType duped = famMgr.DuplicateCurrentType("Verified Copy");
famMgr.Set(pWidth, {1200 * MM_TO_FT:.6f}); // 1200 mm

// Verification
FamilyType verified = famMgr.Types
    .Cast<FamilyType>()
    .FirstOrDefault(t => t.Name == "Verified Copy");

bool nameExists  = verified != null;
double actualMm  = verified != null && pWidth != null
    ? verified.AsDouble(pWidth) * 304.8
    : 0.0;
bool valueCorrect = Math.Abs(actualMm - 1200.0) < 0.01;""",
        ))

        # Duplicate with incremented numeric name
        samples.append(_s(
            "Duplicate the 'Type-1' family type and auto-increment the name to 'Type-2', 'Type-3', etc.",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;

// Find the highest existing Type-N number
int maxN = famMgr.Types
    .Cast<FamilyType>()
    .Where(t => t.Name.StartsWith("Type-"))
    .Select(t => int.TryParse(t.Name.Substring(5), out int n) ? n : 0)
    .DefaultIfEmpty(0)
    .Max();

FamilyType source = famMgr.Types
    .Cast<FamilyType>()
    .FirstOrDefault(t => t.Name == "Type-1");

if (source != null)
{
    famMgr.CurrentType = source;
    string newName = $"Type-{maxN + 1}";
    FamilyType newType = famMgr.DuplicateCurrentType(newName);
}""",
        ))

        # Duplicate preserving formula
        samples.append(_s(
            "Duplicate a type and confirm that formula-driven parameters retain their formulas in the copy",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pHeight = famMgr.get_Parameter("Height");

FamilyType source = famMgr.Types.Cast<FamilyType>().FirstOrDefault(t => t.Name == "Base");
if (source != null)
{
    famMgr.CurrentType = source;
    FamilyType copy = famMgr.DuplicateCurrentType("Base-Copy");

    // DuplicateCurrentType copies formulas -- pHeight.IsDetermined should still be true
    // if the source had a formula set on Height.
    bool formulaPreserved = pHeight != null && pHeight.IsDetermined;
}""",
        ))

        # Duplicate and apply a scale factor
        samples.append(_s(
            "Duplicate a 'Standard' type to 'Compact' and scale both Width and Depth by 0.75",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW = famMgr.get_Parameter("Width");
FamilyParameter pD = famMgr.get_Parameter("Depth");

FamilyType standard = famMgr.Types
    .Cast<FamilyType>()
    .FirstOrDefault(t => t.Name == "Standard");

if (standard != null)
{{
    famMgr.CurrentType = standard;
    double origW = standard.AsDouble(pW);
    double origD = standard.AsDouble(pD);

    FamilyType compact = famMgr.DuplicateCurrentType("Compact");

    const double scale = 0.75;
    if (pW != null) famMgr.Set(pW, origW * scale);
    if (pD != null) famMgr.Set(pD, origD * scale);
}}""",
        ))

        # Duplicate with suffix from a list
        suffixes = ["_A", "_B", "_C", "_D"]
        suffix_list = ", ".join(f'"{s}"' for s in suffixes)
        samples.append(_s(
            "Create four variants of the 'Base' type by duplicating it with suffixes _A, _B, _C, _D",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyType baseType = famMgr.Types
    .Cast<FamilyType>()
    .FirstOrDefault(t => t.Name == "Base");

if (baseType != null)
{{
    string[] suffixes = {{ {suffix_list} }};
    foreach (string suffix in suffixes)
    {{
        famMgr.CurrentType = baseType;
        famMgr.DuplicateCurrentType("Base" + suffix);
        // Modify type-specific parameters here if needed
    }}
}}""",
        ))

        # Duplicate types from external list (data-driven)
        samples.append(_s(
            "Load type definitions from a list of tuples and create each by duplicating a seed type",
            f"""\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW = famMgr.get_Parameter("Width");
FamilyParameter pH = famMgr.get_Parameter("Height");

// External definition source (could come from CSV or database)
var typeDefs = new List<(string Name, double WidthMm, double HeightMm)>
{{
    ("Type-600x900",  600,  900),
    ("Type-800x1100", 800,  1100),
    ("Type-1000x1200",1000, 1200),
    ("Type-1200x1500",1200, 1500),
}};

FamilyType seed = famMgr.Types.Cast<FamilyType>().First();

foreach (var def in typeDefs)
{{
    bool exists = famMgr.Types.Cast<FamilyType>().Any(t => t.Name == def.Name);
    if (exists) continue;

    famMgr.CurrentType = seed;
    FamilyType newType = famMgr.DuplicateCurrentType(def.Name);
    if (pW != null) famMgr.Set(pW, def.WidthMm * {MM_TO_FT:.6f});
    if (pH != null) famMgr.Set(pH, def.HeightMm * {MM_TO_FT:.6f});
}}""",
        ))

        # Duplicate and change material and formula
        samples.append(_s(
            "Duplicate the 'Pine-Wood' cabinet type to 'Oak-Wood' and change only the material parameter",
            """\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pMat = famMgr.get_Parameter("Cabinet Material");

FamilyType pine = famMgr.Types
    .Cast<FamilyType>()
    .FirstOrDefault(t => t.Name == "Pine-Wood");

if (pine != null)
{
    famMgr.CurrentType = pine;
    FamilyType oak = famMgr.DuplicateCurrentType("Oak-Wood");

    Material oakMaterial = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Material))
        .Cast<Material>()
        .FirstOrDefault(m => m.Name.Contains("Oak"));

    if (pMat != null && oakMaterial != null)
        famMgr.Set(pMat, oakMaterial.Id);
}""",
        ))

        # Error handling during duplication
        samples.append(_s(
            "Handle the exception thrown when trying to create a duplicate type with a name that already exists",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.Exceptions;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
string newTypeName = "Standard";

bool alreadyExists = famMgr.Types
    .Cast<FamilyType>()
    .Any(t => t.Name == newTypeName);

if (alreadyExists)
{
    // Use a unique name to avoid ArgumentException
    newTypeName = $"Standard-{System.DateTime.Now.Ticks}";
}

FamilyType baseType = famMgr.Types.Cast<FamilyType>().First();
famMgr.CurrentType = baseType;

try
{
    FamilyType newType = famMgr.DuplicateCurrentType(newTypeName);
}
catch (ArgumentException ex)
{
    // Thrown if the name is still a duplicate
    // Handle: log the error, prompt user, or skip
}""",
        ))

        # Explain DuplicateCurrentType vs NewType
        samples.append(_s(
            "Explain the difference between FamilyManager.DuplicateCurrentType and FamilyManager.NewType",
            """\
// FamilyManager.NewType(name):
//   Creates a brand-new type with NO parameter values inherited.
//   All parameters start at zero/empty/default.
//   Use when building a type from scratch.
//
// FamilyManager.DuplicateCurrentType(name):
//   Creates a copy of the CURRENTLY ACTIVE type, including:
//   - All parameter values
//   - Formula assignments (IsDetermined parameters remain formula-driven)
//   - Material assignments
//   Use when creating a variant of an existing type; fewer values to re-set.
//
// Pattern for DuplicateCurrentType:
//   famMgr.CurrentType = sourceType;           // activate source FIRST
//   FamilyType copy = famMgr.DuplicateCurrentType("NewName"); // copy is now active
//   famMgr.Set(param, newValue);               // modify only the differing values
//
// After DuplicateCurrentType, the newly created type becomes CurrentType.""",
        ))

        # Duplicate and set per-type cost parameter
        costs = [(900, 150.0), (1200, 185.0), (1500, 220.0), (1800, 270.0)]
        cost_entries = "\n    ".join(
            f'("{w}mm", {w * MM_TO_FT:.6f}, {c}),' for w, c in costs
        )
        samples.append(_s(
            "Create four door types of different widths and set a 'Unit Cost' number parameter on each",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth = famMgr.get_Parameter("Width");
FamilyParameter pCost  = famMgr.get_Parameter("Unit Cost")
    ?? famMgr.AddParameter("Unit Cost", BuiltInParameterGroup.PG_DATA, ParameterType.Number, false);

FamilyType seed = famMgr.Types.Cast<FamilyType>().First();

var typeDefs = new (string Name, double WidthFt, double Cost)[]
{{
    {cost_entries}
}};

foreach (var def in typeDefs)
{{
    famMgr.CurrentType = seed;
    FamilyType newType = famMgr.DuplicateCurrentType(def.Name);
    if (pWidth != null) famMgr.Set(pWidth, def.WidthFt);
    if (pCost  != null) famMgr.Set(pCost,  def.Cost);
}}""",
        ))

        # Duplicate for metric/imperial pairs
        samples.append(_s(
            "Create metric and imperial variants of a 'Standard' type (900mm Width vs 36 inch Width)",
            f"""\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth = famMgr.get_Parameter("Width");

FamilyType standard = famMgr.Types
    .Cast<FamilyType>()
    .FirstOrDefault(t => t.Name == "Standard");

if (standard != null)
{{
    // Metric variant: 900mm
    famMgr.CurrentType = standard;
    FamilyType metric = famMgr.DuplicateCurrentType("Standard-900mm");
    if (pWidth != null) famMgr.Set(pWidth, {900 * MM_TO_FT:.6f}); // 900 mm

    // Imperial variant: 36 inches = 914.4mm
    famMgr.CurrentType = standard;
    FamilyType imperial = famMgr.DuplicateCurrentType("Standard-36in");
    if (pWidth != null) famMgr.Set(pWidth, {914.4 * MM_TO_FT:.6f}); // 36 in = 914.4 mm
}}""",
        ))

        # Rename types in batch
        samples.append(_s(
            "Rename all family types by replacing spaces with hyphens in their names",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;

// Snapshot names before modifying
var typeList = famMgr.Types.Cast<FamilyType>().ToList();

foreach (FamilyType ft in typeList)
{
    string newName = ft.Name.Replace(' ', '-');
    if (newName != ft.Name)
    {
        famMgr.CurrentType = ft;
        famMgr.RenameCurrentType(newName);
    }
}""",
        ))

        # Duplicate types from another family document
        samples.append(_s(
            "Copy types from a source family document into a target family document by iterating and duplicating",
            """\
using Autodesk.Revit.DB;
using System.Linq;

// Open source family for reading
Document srcDoc = app.OpenDocumentFile(srcFamilyPath);
FamilyManager srcMgr = srcDoc.FamilyManager;
FamilyManager tgtMgr = targetFamilyDoc.FamilyManager;

// Parameters assumed to exist in both families
FamilyParameter tgtW = tgtMgr.get_Parameter("Width");
FamilyParameter tgtH = tgtMgr.get_Parameter("Height");
FamilyParameter srcW = srcMgr.get_Parameter("Width");
FamilyParameter srcH = srcMgr.get_Parameter("Height");

FamilyType tgtSeed = tgtMgr.Types.Cast<FamilyType>().First();

foreach (FamilyType srcType in srcMgr.Types.Cast<FamilyType>())
{
    srcMgr.CurrentType = srcType;
    double w = srcW != null ? srcType.AsDouble(srcW) : 0;
    double h = srcH != null ? srcType.AsDouble(srcH) : 0;

    tgtMgr.CurrentType = tgtSeed;
    FamilyType newType = tgtMgr.DuplicateCurrentType(srcType.Name);
    if (tgtW != null) tgtMgr.Set(tgtW, w);
    if (tgtH != null) tgtMgr.Set(tgtH, h);
}

srcDoc.Close(false);""",
        ))

        # Explain that DuplicateCurrentType needs CurrentType set first
        samples.append(_s(
            "Explain why DuplicateCurrentType must be preceded by setting CurrentType and what happens if it is not",
            """\
// DuplicateCurrentType always copies the CURRENTLY ACTIVE type (famMgr.CurrentType).
// If CurrentType is null (e.g. newly created family with no types), the call throws
// an InvalidOperationException.
//
// ALWAYS set famMgr.CurrentType before calling DuplicateCurrentType:
//
//   // WRONG -- may duplicate the wrong type if another operation changed CurrentType:
//   FamilyType copy = famMgr.DuplicateCurrentType("MyCopy");
//
//   // CORRECT -- explicit source selection:
//   FamilyType source = famMgr.Types.Cast<FamilyType>()
//       .FirstOrDefault(t => t.Name == "Source");
//   famMgr.CurrentType = source;
//   FamilyType copy = famMgr.DuplicateCurrentType("MyCopy");
//
// After duplication, famMgr.CurrentType == the newly created copy.
// Set any parameters immediately after to modify the copy, not the source.""",
        ))

        # Duplicate to produce a fire-rated variant
        samples.append(_s(
            "Duplicate every existing door type and create a fire-rated variant with '-FR' suffix and 'Fire Rating' set to '60 min'",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pFireRating = famMgr.get_Parameter("Fire Rating")
    ?? famMgr.AddParameter("Fire Rating", BuiltInParameterGroup.PG_FIRE_PROTECTION,
                            ParameterType.Text, false);

var originals = famMgr.Types.Cast<FamilyType>().ToList();

foreach (FamilyType ft in originals)
{
    string frName = ft.Name + "-FR";
    bool exists = famMgr.Types.Cast<FamilyType>().Any(t => t.Name == frName);
    if (exists) continue;

    famMgr.CurrentType = ft;
    FamilyType frType = famMgr.DuplicateCurrentType(frName);

    if (pFireRating != null)
        famMgr.Set(pFireRating, "60 min");
}""",
        ))

        return samples
