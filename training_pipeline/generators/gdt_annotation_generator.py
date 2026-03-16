"""Training data generator: GD&T annotations in Revit.

Maps ASME Y14.5-2018 geometric tolerances to Revit DimensionType
and annotation element properties.

Produces ~220+ Alpaca training pairs.
"""

from __future__ import annotations

from typing import Any, Dict, List

SAMPLE = Dict[str, Any]
MM_TO_FT = 1.0 / 304.8


def _s(instruction: str, output: str) -> SAMPLE:
    return {"instruction": instruction, "input": "", "output": output}


class GDTAnnotationGenerator:
    def generate(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []
        samples += self._tolerance_types()
        samples += self._geometric_characteristics()
        samples += self._datum_references()
        samples += self._surface_finish()
        samples += self._it_grades()
        samples += self._full_callouts()
        samples += self._tolerance_stacks()
        return samples

    # ------------------------------------------------------------------

    def _tolerance_types(self) -> List[SAMPLE]:
        samples = []

        # Symmetric tolerance (e.g., +/- 0.1)
        for tol_mm in [0.05, 0.1, 0.2, 0.5, 1.0]:
            tol_ft = tol_mm * MM_TO_FT
            samples.append(_s(
                f"Apply symmetric +/-{tol_mm}mm tolerance to a dimension in Revit",
                f"""\
using Autodesk.Revit.DB;
using System.Linq;

// Get or create a DimensionType
DimensionType dimType = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(DimensionType))
    .Cast<DimensionType>()
    .FirstOrDefault();

if (dimType != null)
{{
    using (Transaction tx = new Transaction(familyDoc, "Set Tolerance"))
    {{
        tx.Start();

        // Enable tolerance display
        dimType.get_Parameter(BuiltInParameter.DIM_TOL_SHOW).Set(1);

        // Tolerance type: 0=None, 1=Symmetric, 2=Deviation, 3=Limits, 4=Basic
        dimType.get_Parameter(BuiltInParameter.DIM_TOL_TYPE).Set(1); // Symmetric

        // Tolerance value in feet
        dimType.get_Parameter(BuiltInParameter.DIM_TOL_VALUE).Set({tol_ft:.8f}); // +/-{tol_mm} mm

        tx.Commit();
    }}
}}""",
            ))

        # Deviation tolerance (asymmetric)
        for (upper_mm, lower_mm) in [(0.2, -0.1), (0.3, -0.05), (0.1, -0.2)]:
            upper_ft = upper_mm * MM_TO_FT
            lower_ft = lower_mm * MM_TO_FT
            samples.append(_s(
                f"Apply asymmetric deviation tolerance +{upper_mm}/-{abs(lower_mm)}mm to a dimension",
                f"""\
using Autodesk.Revit.DB;
using System.Linq;

DimensionType dimType = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(DimensionType))
    .Cast<DimensionType>()
    .FirstOrDefault();

if (dimType != null)
{{
    using (Transaction tx = new Transaction(familyDoc, "Set Deviation Tolerance"))
    {{
        tx.Start();

        dimType.get_Parameter(BuiltInParameter.DIM_TOL_SHOW).Set(1);
        dimType.get_Parameter(BuiltInParameter.DIM_TOL_TYPE).Set(2); // Deviation

        // Upper tolerance (positive)
        dimType.get_Parameter(BuiltInParameter.DIM_TOL_VALUE).Set({upper_ft:.8f}); // +{upper_mm} mm

        // Lower tolerance (negative stored as positive magnitude)
        dimType.get_Parameter(BuiltInParameter.DIM_TOL_VALUE_LOW).Set({abs(lower_ft):.8f}); // -{abs(lower_mm)} mm

        tx.Commit();
    }}
}}""",
            ))

        # Limits tolerance
        for (nominal_mm, upper_mm, lower_mm) in [(50.0, 50.2, 49.9), (100.0, 100.5, 99.5)]:
            samples.append(_s(
                f"Apply limits tolerance ({lower_mm} / {upper_mm}) to a {nominal_mm}mm nominal dimension",
                f"""\
using Autodesk.Revit.DB;
using System.Linq;

DimensionType dimType = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(DimensionType))
    .Cast<DimensionType>()
    .FirstOrDefault();

if (dimType != null)
{{
    using (Transaction tx = new Transaction(familyDoc, "Set Limits Tolerance"))
    {{
        tx.Start();

        dimType.get_Parameter(BuiltInParameter.DIM_TOL_SHOW).Set(1);
        dimType.get_Parameter(BuiltInParameter.DIM_TOL_TYPE).Set(3); // Limits

        // Upper limit
        dimType.get_Parameter(BuiltInParameter.DIM_TOL_VALUE).Set({upper_mm * MM_TO_FT:.8f}); // {upper_mm} mm

        // Lower limit
        dimType.get_Parameter(BuiltInParameter.DIM_TOL_VALUE_LOW).Set({lower_mm * MM_TO_FT:.8f}); // {lower_mm} mm

        tx.Commit();
    }}
}}""",
            ))

        return samples

    # ------------------------------------------------------------------

    def _geometric_characteristics(self) -> List[SAMPLE]:
        samples = []
        characteristics = [
            ("flatness",       "Flatness",       0.05,  "flat surface within 0.05mm"),
            ("straightness",   "Straightness",   0.02,  "straight edge within 0.02mm"),
            ("circularity",    "Circularity",    0.03,  "circular feature within 0.03mm"),
            ("cylindricity",   "Cylindricity",   0.05,  "cylindrical surface within 0.05mm"),
            ("perpendicularity","Perpendicularity",0.1, "face perpendicular within 0.1mm to datum A"),
            ("parallelism",    "Parallelism",    0.1,   "face parallel within 0.1mm to datum B"),
            ("angularity",     "Angularity",     0.2,   "surface at 45deg within 0.2mm to datum A"),
            ("position",       "Position",       0.2,   "hole position within dia 0.2mm at MMC"),
            ("concentricity",  "Concentricity",  0.05,  "inner circle concentric within dia 0.05mm"),
            ("symmetry",       "Symmetry",       0.1,   "slot symmetric within 0.1mm to datum C"),
            ("runout",         "Circular Runout",0.05,  "circular runout 0.05mm to datum A"),
            ("total_runout",   "Total Runout",   0.1,   "total runout 0.1mm to datum A"),
            ("profile_line",   "Profile of a Line", 0.3, "profile of a line 0.3mm"),
            ("profile_surface","Profile of a Surface", 0.5, "profile of a surface 0.5mm"),
        ]
        for (key, char_name, tol_mm, desc) in characteristics:
            tol_ft = tol_mm * MM_TO_FT
            sym = GDTAnnotationGenerator._gdt_char_symbol(key)
            samples.append(_s(
                f"Add a GD&T annotation for {char_name} tolerance: {desc}",
                f"""\
using Autodesk.Revit.DB;
// GD&T: {char_name} tolerance {tol_mm}mm per ASME Y14.5-2018
// In Revit, geometric tolerances are applied via DimensionType or
// annotated using DetailLines and TextNotes in drafting views.

// For feature control frame via TextNote:
using (Transaction tx = new Transaction(familyDoc, "Add {char_name} Annotation"))
{{
    tx.Start();

    View activeView = familyDoc.ActiveView;

    // Feature control frame text: |char|tolerance|datum|
    // Position near the feature being toleranced
    XYZ position = new XYZ(0, 0, 0); // adjust to feature location

    TextNoteType noteType = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(TextNoteType))
        .Cast<TextNoteType>()
        .FirstOrDefault();

    string fcfText = "{sym} {tol_mm} | A"; // {char_name} {tol_mm}mm referenced to datum A
    TextNote.Create(familyDoc, activeView.Id, position, fcfText, noteType.Id);

    tx.Commit();
}}""",
            ))
        return samples

    # ------------------------------------------------------------------

    def _datum_references(self) -> List[SAMPLE]:
        samples = []
        for (datum_letter, desc, plane) in [
            ("A", "primary datum -- bottom face", "XY plane at Z=0"),
            ("B", "secondary datum -- left face",  "YZ plane at X=0"),
            ("C", "tertiary datum -- front face",  "XZ plane at Y=0"),
        ]:
            samples.append(_s(
                f"Create a datum reference '{datum_letter}' ({desc}) annotation",
                f"""\
using Autodesk.Revit.DB;

// Datum {datum_letter}: {desc} ({plane})
using (Transaction tx = new Transaction(familyDoc, "Add Datum {datum_letter}"))
{{
    tx.Start();

    View view = familyDoc.ActiveView;

    TextNoteType noteType = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(TextNoteType))
        .Cast<TextNoteType>()
        .FirstOrDefault();

    // Datum triangle annotation: -A- convention
    string datumText = "-{datum_letter}-";
    XYZ position = XYZ.Zero; // place at datum feature location

    TextNote datumNote = TextNote.Create(
        familyDoc, view.Id, position, datumText, noteType.Id);

    // Add a detail line as datum symbol underline
    XYZ lineStart = new XYZ(-0.1, -0.05, 0);
    XYZ lineEnd   = new XYZ( 0.1, -0.05, 0);
    DetailLine datumLine = familyDoc.FamilyCreate.NewDetailCurve(
        view, Line.CreateBound(lineStart, lineEnd)) as DetailLine;

    tx.Commit();
}}""",
            ))
        return samples

    # ------------------------------------------------------------------

    def _surface_finish(self) -> List[SAMPLE]:
        samples = []
        for (ra, desc) in [(0.8, "machined finish Ra 0.8"), (1.6, "standard machined Ra 1.6"),
                           (3.2, "rough machined Ra 3.2"), (6.3, "as-cast Ra 6.3")]:
            samples.append(_s(
                f"Add surface finish annotation {desc} (Ra {ra}um)",
                f"""\
using Autodesk.Revit.DB;

// Surface finish symbol: Ra {ra} um per ISO 1302
using (Transaction tx = new Transaction(familyDoc, "Add Surface Finish Ra{ra}"))
{{
    tx.Start();

    View view = familyDoc.ActiveView;
    TextNoteType noteType = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(TextNoteType))
        .Cast<TextNoteType>()
        .FirstOrDefault();

    // Surface finish notation
    string sfText = "Ra {ra}"; // micrometers
    XYZ position = XYZ.Zero;

    TextNote.Create(familyDoc, view.Id, position, sfText, noteType.Id);

    tx.Commit();
}}""",
            ))
        return samples

    # ------------------------------------------------------------------

    def _it_grades(self) -> List[SAMPLE]:
        samples = []
        # ISO 286 IT grades for common nominal sizes
        it_data = [
            ("IT6",  50,  0.016, "precision fit shaft"),
            ("IT7",  50,  0.025, "general engineering shaft"),
            ("IT8",  50,  0.039, "loose fit hole"),
            ("IT11", 50,  0.160, "blank allowance"),
            ("IT6",  100, 0.022, "precision 100mm bore"),
        ]
        for (grade, nom_mm, tol_mm, desc) in it_data:
            samples.append(_s(
                f"Apply {grade} tolerance ({tol_mm}mm) to a {nom_mm}mm feature ({desc})",
                f"""\
using Autodesk.Revit.DB;
using System.Linq;

// ISO 286 {grade} for {nom_mm}mm nominal: +/-{tol_mm/2}mm = total {tol_mm}mm band
DimensionType dimType = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(DimensionType))
    .Cast<DimensionType>()
    .FirstOrDefault();

if (dimType != null)
{{
    using (Transaction tx = new Transaction(familyDoc, "Apply {grade}"))
    {{
        tx.Start();

        dimType.get_Parameter(BuiltInParameter.DIM_TOL_SHOW).Set(1);
        dimType.get_Parameter(BuiltInParameter.DIM_TOL_TYPE).Set(1); // Symmetric

        // Half-tolerance in feet
        double halfTol = {(tol_mm / 2) * MM_TO_FT:.8f}; // {tol_mm / 2} mm
        dimType.get_Parameter(BuiltInParameter.DIM_TOL_VALUE).Set(halfTol);

        tx.Commit();
    }}
}}""",
            ))
        return samples

    # ------------------------------------------------------------------

    def _full_callouts(self) -> List[SAMPLE]:
        return [
            _s(
                "Create a full position tolerance callout: dia 0.2mm at MMC, referenced to datums A, B, C",
                """\
using Autodesk.Revit.DB;

// Full GD&T callout: |pos|dia0.2(M)|A|B|C|
// True position with maximum material condition modifier
using (Transaction tx = new Transaction(familyDoc, "Position Tolerance Callout"))
{
    tx.Start();

    View view = familyDoc.ActiveView;
    TextNoteType noteType = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(TextNoteType))
        .Cast<TextNoteType>()
        .FirstOrDefault();

    // Feature control frame (text approximation)
    // Full callout: position | dia 0.2 (M) | A | B | C
    string fcf = "[pos] [dia]0.2(M) | A | B | C";
    XYZ position = XYZ.Zero;

    TextNote.Create(familyDoc, view.Id, position, fcf, noteType.Id);

    // Datum references
    foreach ((string letter, XYZ pos) in new[] {
        ("-A-", new XYZ(0, -1, 0)),
        ("-B-", new XYZ(-1, 0, 0)),
        ("-C-", new XYZ(0, 1, 0))
    })
    {
        TextNote.Create(familyDoc, view.Id, pos, letter, noteType.Id);
    }

    tx.Commit();
}""",
            ),
            _s(
                "Apply perpendicularity tolerance 0.05mm to a boss face relative to datum A, with dimension",
                f"""\
using Autodesk.Revit.DB;
using System.Linq;

// Perpendicularity: surface must be within 0.05mm of perfect perpendicular to datum A
double tolFt = {0.05 * MM_TO_FT:.8f}; // 0.05mm

DimensionType dimType = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(DimensionType))
    .Cast<DimensionType>()
    .FirstOrDefault();

if (dimType != null)
{{
    using (Transaction tx = new Transaction(familyDoc, "Perpendicularity Tolerance"))
    {{
        tx.Start();

        dimType.get_Parameter(BuiltInParameter.DIM_TOL_SHOW).Set(1);
        dimType.get_Parameter(BuiltInParameter.DIM_TOL_TYPE).Set(1); // Symmetric
        dimType.get_Parameter(BuiltInParameter.DIM_TOL_VALUE).Set(tolFt);

        // Add FCF text note
        View view = familyDoc.ActiveView;
        TextNoteType noteType = new FilteredElementCollector(familyDoc)
            .OfClass(typeof(TextNoteType)).Cast<TextNoteType>().FirstOrDefault();
        string fcf = "[perp] 0.05 | A";
        TextNote.Create(familyDoc, view.Id, new XYZ(0.5, 0, 0), fcf, noteType.Id);

        tx.Commit();
    }}
}}""",
            ),
        ]

    # ------------------------------------------------------------------

    def _tolerance_stacks(self) -> List[SAMPLE]:
        return [
            _s(
                "Perform a 1D tolerance stack-up analysis: three dimensions each +/-0.1mm, compute worst case",
                """\
using System;
// Tolerance stack-up: 3 features each with +/-0.1mm
// Worst case method: simply add all tolerances
// Statistical method: RSS (root sum of squares)

double tol1 = 0.1; // mm
double tol2 = 0.1;
double tol3 = 0.1;

double worstCase = tol1 + tol2 + tol3;
double statistical = Math.Sqrt(tol1 * tol1 + tol2 * tol2 + tol3 * tol3);

// worstCase  = 0.3 mm
// statistical = 0.1732 mm (RSS)

// To annotate stack result in Revit:
using (Transaction tx = new Transaction(familyDoc, "Tolerance Stack Annotation"))
{
    tx.Start();

    View view = familyDoc.ActiveView;
    TextNoteType noteType = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(TextNoteType)).Cast<TextNoteType>().FirstOrDefault();

    string annotation = $"Stack: WC=+/-{worstCase:F3}mm RSS=+/-{statistical:F3}mm";
    TextNote.Create(familyDoc, view.Id, new XYZ(0, 1, 0), annotation, noteType.Id);

    tx.Commit();
}""",
            )
        ]

    # ------------------------------------------------------------------

    @staticmethod
    def _gdt_char_symbol(key: str) -> str:
        symbols = {
            "flatness": "[flat]",
            "straightness": "[str]",
            "circularity": "[circ]",
            "cylindricity": "[cyl]",
            "perpendicularity": "[perp]",
            "parallelism": "[par]",
            "angularity": "[ang]",
            "position": "[pos]",
            "concentricity": "[conc]",
            "symmetry": "[sym]",
            "runout": "[run]",
            "total_runout": "[trun]",
            "profile_line": "[prl]",
            "profile_surface": "[prs]",
        }
        return symbols.get(key, "[tol]")
