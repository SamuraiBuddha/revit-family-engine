"""Training data generator: Revit FamilyManager parameter operations.

Produces ~200+ Alpaca-format training pairs covering parameter creation,
type management, formulas, and type catalog patterns.

NOTE: FamilyManager operations must occur OUTSIDE Transaction blocks.
"""

from __future__ import annotations

from typing import Any, Dict, List

SAMPLE = Dict[str, Any]
MM_TO_FT = 1.0 / 304.8


def _s(instruction: str, output: str) -> SAMPLE:
    return {"instruction": instruction, "input": "", "output": output}


class FamilyParameterGenerator:
    def generate(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []
        samples += self._single_length_params()
        samples += self._multi_param_families()
        samples += self._yes_no_params()
        samples += self._material_params()
        samples += self._formula_params()
        samples += self._type_management()
        samples += self._type_catalog()
        samples += self._instance_vs_type()
        samples += self._parameter_groups()
        return samples

    # ------------------------------------------------------------------

    def _single_length_params(self) -> List[SAMPLE]:
        samples = []
        params = [
            ("Width",  "PG_GEOMETRY", 300, "width of the family"),
            ("Height", "PG_GEOMETRY", 2400, "overall height"),
            ("Depth",  "PG_GEOMETRY", 200, "extrusion depth"),
            ("Offset", "PG_GEOMETRY", 50,  "mounting offset from host"),
            ("Radius", "PG_GEOMETRY", 150, "corner radius"),
        ]
        for pname, group, default_mm, desc in params:
            default_ft = default_mm * MM_TO_FT
            samples.append(_s(
                f"Add a '{pname}' length parameter ({desc}) with default {default_mm}mm",
                f"""\
using Autodesk.Revit.DB;

// FamilyManager operations must be OUTSIDE any Transaction
FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter param{pname} = famMgr.AddParameter(
    "{pname}",
    BuiltInParameterGroup.{group},
    ParameterType.Length,
    false); // false = type parameter

// Set default value in feet (Revit internal units)
famMgr.Set(param{pname}, {default_ft:.6f}); // {default_mm} mm""",
            ))
        return samples

    # ------------------------------------------------------------------

    def _multi_param_families(self) -> List[SAMPLE]:
        return [
            _s(
                "Add Width, Depth, and Height type parameters to a structural column family",
                f"""\
using Autodesk.Revit.DB;

// All parameter additions outside Transaction
FamilyManager famMgr = familyDoc.FamilyManager;

// b = flange width, d = section depth, h = member height
FamilyParameter paramB = famMgr.AddParameter(
    "b", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter paramD = famMgr.AddParameter(
    "d", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter paramH = famMgr.AddParameter(
    "Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

// Defaults: 300x300mm section, 3000mm height
famMgr.Set(paramB, {300 * MM_TO_FT:.6f}); // 300 mm
famMgr.Set(paramD, {300 * MM_TO_FT:.6f}); // 300 mm
famMgr.Set(paramH, {3000 * MM_TO_FT:.6f}); // 3000 mm""",
            ),
            _s(
                "Add Rough Width, Rough Height, and Frame Depth parameters to a door family",
                f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter pRoughWidth = famMgr.AddParameter(
    "Rough Width",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pRoughHeight = famMgr.AddParameter(
    "Rough Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pFrameDepth = famMgr.AddParameter(
    "Frame Depth",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, true); // instance

famMgr.Set(pRoughWidth,  {914 * MM_TO_FT:.6f});  // 914 mm (36")
famMgr.Set(pRoughHeight, {2134 * MM_TO_FT:.6f}); // 2134 mm (84")
famMgr.Set(pFrameDepth,  {90 * MM_TO_FT:.6f});   // 90 mm""",
            ),
        ]

    # ------------------------------------------------------------------

    def _yes_no_params(self) -> List[SAMPLE]:
        samples = []
        cases = [
            ("Show Handle", "PG_GEOMETRY", "door handle visibility"),
            ("Has Transom", "PG_GEOMETRY", "transom light above door"),
            ("Fire Rated",  "PG_DATA",    "fire rating flag"),
            ("Accessible",  "PG_DATA",    "ADA accessibility flag"),
        ]
        for pname, group, desc in cases:
            samples.append(_s(
                f"Add a Yes/No parameter '{pname}' ({desc}) defaulting to Yes",
                f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter param = famMgr.AddParameter(
    "{pname}",
    BuiltInParameterGroup.{group},
    ParameterType.YesNo,
    true); // instance parameter

famMgr.Set(param, 1); // 1 = Yes, 0 = No""",
            ))
        return samples

    # ------------------------------------------------------------------

    def _material_params(self) -> List[SAMPLE]:
        samples = []
        for (pname, group, is_instance) in [
            ("Frame Material", "PG_MATERIALS", True),
            ("Body Material",  "PG_MATERIALS", True),
            ("Finish",         "PG_MATERIALS", False),
        ]:
            samples.append(_s(
                f"Add a material parameter '{pname}' to the family",
                f"""\
using Autodesk.Revit.DB;
using System.Linq;

FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter matParam = famMgr.AddParameter(
    "{pname}",
    BuiltInParameterGroup.{group},
    ParameterType.Material,
    {str(is_instance).lower()});

// Optionally set a default material by name
Material defaultMat = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(Material))
    .Cast<Material>()
    .FirstOrDefault(m => m.Name == "Default");

if (defaultMat != null)
    famMgr.Set(matParam, defaultMat.Id);""",
            ))
        return samples

    # ------------------------------------------------------------------

    def _formula_params(self) -> List[SAMPLE]:
        return [
            _s(
                "Set a formula on Height parameter so it equals Width * 3",
                """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;

// Ensure Width parameter exists
FamilyParameter pWidth  = famMgr.get_Parameter("Width")
    ?? famMgr.AddParameter("Width",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pHeight = famMgr.get_Parameter("Height")
    ?? famMgr.AddParameter("Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

famMgr.Set(pWidth, 0.984252); // 300 mm default

// Formula: Height is always 3x Width
famMgr.SetFormula(pHeight, "Width * 3");""",
            ),
            _s(
                "Create a computed area parameter using a formula based on Width and Depth",
                """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter pWidth = famMgr.get_Parameter("Width")
    ?? famMgr.AddParameter("Width", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pDepth = famMgr.get_Parameter("Depth")
    ?? famMgr.AddParameter("Depth", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pArea  = famMgr.AddParameter(
    "Section Area", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Area, false);

// Area = Width * Depth (Revit area units: sq ft)
famMgr.SetFormula(pArea, "Width * Depth");""",
            ),
            _s(
                "Add a diagonal parameter with formula = sqrt(Width^2 + Height^2)",
                """\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter pWidth    = famMgr.get_Parameter("Width")
    ?? famMgr.AddParameter("Width",    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pHeight   = famMgr.get_Parameter("Height")
    ?? famMgr.AddParameter("Height",   BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pDiagonal = famMgr.AddParameter(
    "Diagonal", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

// Revit formula syntax for sqrt
famMgr.SetFormula(pDiagonal, "sqrt(Width ^ 2 + Height ^ 2)");""",
            ),
        ]

    # ------------------------------------------------------------------

    def _type_management(self) -> List[SAMPLE]:
        return [
            _s(
                "Create multiple family types for a door family: 762x2032, 864x2134, 914x2134",
                f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;

FamilyParameter pWidth  = famMgr.get_Parameter("Rough Width")
    ?? famMgr.AddParameter("Rough Width",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pHeight = famMgr.get_Parameter("Rough Height")
    ?? famMgr.AddParameter("Rough Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

var types = new (string name, double w, double h)[]
{{
    ("762 x 2032", 762, 2032),
    ("864 x 2134", 864, 2134),
    ("914 x 2134", 914, 2134),
    ("991 x 2134", 991, 2134),
}};

foreach (var (name, wMm, hMm) in types)
{{
    FamilyType ft = famMgr.NewType(name);
    famMgr.CurrentType = ft;
    famMgr.Set(pWidth,  wMm / 304.8);
    famMgr.Set(pHeight, hMm / 304.8);
}}""",
            ),
            _s(
                "Iterate all family types and print their Width and Height values",
                """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using System.Text;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pWidth  = famMgr.get_Parameter("Width");
FamilyParameter pHeight = famMgr.get_Parameter("Height");

var sb = new StringBuilder();
sb.AppendLine("Family Types:");

foreach (FamilyType ft in famMgr.Types)
{
    famMgr.CurrentType = ft;
    double wMm = pWidth  != null ? famMgr.GetValue(pWidth)  as double? * 304.8 ?? 0 : 0;
    double hMm = pHeight != null ? famMgr.GetValue(pHeight) as double? * 304.8 ?? 0 : 0;
    sb.AppendLine($"  {ft.Name}: W={wMm:F0}mm H={hMm:F0}mm");
}

TaskDialog.Show("Family Types", sb.ToString());""",
            ),
        ]

    # ------------------------------------------------------------------

    def _type_catalog(self) -> List[SAMPLE]:
        return [
            _s(
                "Generate a type catalog CSV for a structural column family with b, d, and Height parameters",
                """\
using System.IO;
using System.Text;

// Revit type catalog format:
// First line: ##Type Name,Param1##units,Param2##units,...
// Subsequent lines: TypeName,value1,value2,...
// Length units in type catalogs: millimeters (not feet!)

var sb = new StringBuilder();
sb.AppendLine("##Type Name,b##LENGTH##MILLIMETERS,d##LENGTH##MILLIMETERS,Height##LENGTH##MILLIMETERS");

var types = new (string name, int b, int d, int h)[]
{
    ("300x300",  300,  300, 3000),
    ("300x450",  300,  450, 3000),
    ("450x450",  450,  450, 3000),
    ("450x600",  450,  600, 4000),
    ("600x600",  600,  600, 4000),
    ("600x800",  600,  800, 5000),
};

foreach (var (name, b, d, height) in types)
    sb.AppendLine($"{name},{b},{d},{height}");

// Save next to the .rfa file
string catalogPath = familyDoc.PathName.Replace(".rfa", ".txt");
File.WriteAllText(catalogPath, sb.ToString());""",
            )
        ]

    # ------------------------------------------------------------------

    def _instance_vs_type(self) -> List[SAMPLE]:
        return [
            _s(
                "Explain and demonstrate instance vs type parameters: Width as type, Offset as instance",
                f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;

// TYPE parameter: same value across all instances of a type
// isInstance = false
FamilyParameter pWidth = famMgr.AddParameter(
    "Width",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length,
    false); // type parameter -- controls geometry shape
famMgr.Set(pWidth, {600 * MM_TO_FT:.6f}); // 600 mm default

// INSTANCE parameter: can differ per placed instance
// isInstance = true
FamilyParameter pOffset = famMgr.AddParameter(
    "Elevation Offset",
    BuiltInParameterGroup.PG_GEOMETRY,
    ParameterType.Length,
    true); // instance parameter -- each placed instance sets its own value
famMgr.Set(pOffset, 0.0); // 0mm default""",
            )
        ]

    # ------------------------------------------------------------------

    def _parameter_groups(self) -> List[SAMPLE]:
        groups = [
            ("PG_GEOMETRY",      "Dimensions", "Width, Height, Depth"),
            ("PG_MATERIALS",     "Materials",  "Body Material, Finish"),
            ("PG_IDENTITY_DATA", "Identity Data", "Mark, Comments"),
            ("PG_ANALYSIS_RESULTS", "Structural Analysis", "Moment capacity"),
            ("PG_ELECTRICAL",    "Electrical", "Voltage, Phase"),
        ]
        samples = []
        for group, group_name, example in groups:
            samples.append(_s(
                f"Add a parameter to the '{group_name}' group (BuiltInParameterGroup.{group}): {example}",
                f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;

// Parameters appear under '{group_name}' in the Properties panel
FamilyParameter param = famMgr.AddParameter(
    "{example.split(',')[0].strip()}",
    BuiltInParameterGroup.{group},
    ParameterType.Length,
    true); // instance parameter""",
            ))
        return samples
