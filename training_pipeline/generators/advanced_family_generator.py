"""Training data generator: Advanced Revit family patterns.

Produces ~250 Alpaca-format training pairs covering nested/shared families,
in-place families, arrays, mirrors, and complex multi-geometry patterns.
"""

from __future__ import annotations

from typing import Any, Dict, List

SAMPLE = Dict[str, Any]
MM_TO_FT = 1.0 / 304.8


def _s(instruction: str, output: str) -> SAMPLE:
    return {"instruction": instruction, "input": "", "output": output}


def _ft(mm: float) -> str:
    return f"{mm * MM_TO_FT:.6f}"


class AdvancedFamilyGenerator:
    """Generates training samples for advanced Revit family patterns."""

    def generate(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []
        samples += self._nested_families()
        samples += self._shared_families()
        samples += self._in_place_families()
        samples += self._linear_arrays()
        samples += self._mirror_elements()
        samples += self._multi_geometry()
        samples += self._parametric_patterns()
        return samples

    # ------------------------------------------------------------------
    # Nested families
    # ------------------------------------------------------------------

    def _nested_families(self) -> List[SAMPLE]:
        samples = []
        samples.append(_s("Load a nested column family into a structural frame family",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;

// Load nested family using forward slashes to avoid path escape issues
string nestedPath = "C:/ProgramData/Autodesk/RVT 2024/Libraries/US Metric/Structural/Columns/Concrete/M_Concrete-Rectangular-Column.rfa";

using (Transaction tx = new Transaction(familyDoc, "Load Nested Family"))
{{
    tx.Start();

    Family nestedFamily = null;
    familyDoc.LoadFamily(nestedPath, out nestedFamily);

    if (nestedFamily != null)
    {{
        FamilySymbol symbol = familyDoc.GetElement(
            nestedFamily.GetFamilySymbolIds().First()) as FamilySymbol;
        if (symbol != null)
        {{
            symbol.Activate();
            // Place nested instance at origin
            familyDoc.FamilyCreate.NewFamilyInstance(
                XYZ.Zero, symbol, StructuralType.Column);
        }}
    }}

    tx.Commit();
}}"""))

        samples.append(_s("Associate a nested family's parameter to the host family's parameter",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;
using System.Linq;

// Associate nested family parameter to host parameter
// Both host and nested must have a parameter with the same name,
// or use FamilyInstance parameter association

FamilyInstance nestedInst = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(FamilyInstance))
    .Cast<FamilyInstance>()
    .FirstOrDefault();

if (nestedInst != null)
{
    // Find the parameter on the nested instance to associate
    Parameter nestedParam = nestedInst.LookupParameter("Width");
    FamilyParameter hostParam = familyDoc.FamilyManager.get_Parameter("Width");

    if (nestedParam != null && hostParam != null)
    {
        // Associate: nested instance parameter is driven by host family parameter
        nestedInst.SetFamilyParameterAsParameter(nestedParam, hostParam);
    }
}"""))

        samples.append(_s("Place multiple nested family instances in a grid pattern",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;

using (Transaction tx = new Transaction(familyDoc, "Place Nested Grid"))
{{
    tx.Start();

    Family nestedFamily = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(Family))
        .Cast<Family>()
        .FirstOrDefault(f => !f.IsInPlace);

    if (nestedFamily != null)
    {{
        FamilySymbol sym = familyDoc.GetElement(
            nestedFamily.GetFamilySymbolIds().First()) as FamilySymbol;
        sym?.Activate();

        if (sym != null)
        {{
            double spacing = {_ft(600)}; // 600mm spacing
            for (int row = 0; row < 3; row++)
            {{
                for (int col = 0; col < 3; col++)
                {{
                    XYZ pt = new XYZ(col * spacing, row * spacing, 0);
                    familyDoc.FamilyCreate.NewFamilyInstance(
                        pt, sym, StructuralType.NonStructural);
                }}
            }}
        }}
    }}

    tx.Commit();
}}"""))

        samples.append(_s("Check if a nested family instance has all its parameters properly associated",
            """\
using Autodesk.Revit.DB;
using System.Collections.Generic;

FamilyManager famMgr = familyDoc.FamilyManager;
IList<FamilyParameter> hostParams = famMgr.GetParameters();

FamilyInstance nested = new FilteredElementCollector(familyDoc)
    .OfClass(typeof(FamilyInstance))
    .Cast<FamilyInstance>()
    .FirstOrDefault();

if (nested != null)
{
    foreach (FamilyParameter hp in hostParams)
    {
        // Check if this host parameter drives any nested parameter
        IList<Parameter> nestedParams = nested.GetParameters(hp.Definition.Name);
        bool isAssociated = nestedParams.Count > 0;
    }
}"""))
        return samples  # 4

    # ------------------------------------------------------------------
    # Shared families
    # ------------------------------------------------------------------

    def _shared_families(self) -> List[SAMPLE]:
        samples = []
        samples.append(_s("Set a nested family as shared so it can be scheduled independently",
            """\
using Autodesk.Revit.DB;

// IsShared must be set in the nested family's .rfa file itself
// Open the nested family document and set IsShared = true
Document nestedFamilyDoc = null; // open via app.OpenDocumentFile()

// When this family is nested into another, IsShared=true means
// instances can be tagged and scheduled separately from the host

using (Transaction tx = new Transaction(nestedFamilyDoc, "Set Shared"))
{
    tx.Start();
    nestedFamilyDoc.OwnerFamily.IsShared = true;
    tx.Commit();
}
nestedFamilyDoc.Save(new SaveOptions());"""))

        samples.append(_s("Check if a loaded family is marked as shared",
            """\
using Autodesk.Revit.DB;

Family family = new FilteredElementCollector(doc)
    .OfClass(typeof(Family))
    .Cast<Family>()
    .FirstOrDefault(f => f.Name == "M_Bolt");

if (family != null)
{
    bool isShared = family.IsShared;
    // isShared=true: instances can be scheduled/tagged individually
    // isShared=false: instances are subcomponents of the host only
}"""))
        return samples  # 2

    # ------------------------------------------------------------------
    # In-place families
    # ------------------------------------------------------------------

    def _in_place_families(self) -> List[SAMPLE]:
        samples = []
        samples.append(_s("Create an in-place family for a custom structural slab edge",
            """\
using Autodesk.Revit.DB;

// In-place family: create unique geometry within a project
// Category: Structural Framing
using (Transaction tx = new Transaction(doc, "Create In-Place Family"))
{
    tx.Start();

    FamilyItemFactory factory = doc.FamilyCreate;
    // doc.NewInPlaceFamily is available on Document in a project context
    // The in-place family opens in family editor mode

    Document inPlaceDoc = doc.NewInPlaceFamily(
        doc.Settings.Categories.get_Item(BuiltInCategory.OST_StructuralFraming));

    // In the returned document, create geometry using FamilyCreate
    // then call doc.CloseAndReloadIntoProject()

    tx.Commit();
}"""))

        samples.append(_s("Finish editing an in-place family and reload it into the project",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// After editing in-place family geometry:
// Close and reload using the UI API
// (In practice, the user clicks Finish Model in the ribbon)

// Programmatically: use UIDocument.CommitFamily()
UIDocument uidoc = null; // current UIDocument
if (uidoc != null)
{
    // The in-place family is active; commit finishes it
    uidoc.Document.Regenerate();
    // After Finish Model button (UI), the family is embedded in project
}"""))
        return samples  # 2

    # ------------------------------------------------------------------
    # Linear arrays
    # ------------------------------------------------------------------

    def _linear_arrays(self) -> List[SAMPLE]:
        samples = []
        array_cases = [
            (3, 600,  "X", "3 elements at 600mm spacing along X-axis"),
            (4, 500,  "X", "4 elements at 500mm spacing along X-axis"),
            (5, 400,  "X", "5 elements at 400mm spacing along X-axis"),
            (6, 300,  "Y", "6 elements at 300mm spacing along Y-axis"),
            (8, 1200, "X", "8 bolt holes at 1200mm spacing"),
            (10, 200, "X", "10 elements at 200mm spacing"),
        ]
        for (count, spacing_mm, axis, desc) in array_cases:
            if axis == "X":
                dir_vec = f"new XYZ({_ft(spacing_mm)}, 0, 0)"
            else:
                dir_vec = f"new XYZ(0, {_ft(spacing_mm)}, 0)"

            samples.append(_s(f"Create a linear array: {desc}",
                f"""\
using Autodesk.Revit.DB;

using (Transaction tx = new Transaction(familyDoc, "Create Linear Array"))
{{
    tx.Start();

    double spacing = {_ft(spacing_mm)}; // {spacing_mm} mm

    // First, create base element (e.g., extrusion)
    CurveArray loop = new CurveArray();
    double r = {_ft(50)};
    loop.Append(Line.CreateBound(new XYZ(-r,-r,0), new XYZ(r,-r,0)));
    loop.Append(Line.CreateBound(new XYZ(r,-r,0),  new XYZ(r,r,0)));
    loop.Append(Line.CreateBound(new XYZ(r,r,0),   new XYZ(-r,r,0)));
    loop.Append(Line.CreateBound(new XYZ(-r,r,0),  new XYZ(-r,-r,0)));
    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    Element baseElem = familyDoc.FamilyCreate.NewExtrusion(
        true, profile, sp, {_ft(100)});

    // Create array: {count} elements, spacing = {spacing_mm}mm
    LinearArray array = familyDoc.FamilyCreate.NewLinearArray(
        {count},
        new Transform {{ Origin = XYZ.Zero }},
        ArrayEqualSpacingRule.NumberAndSpacing,
        {dir_vec}); // direction vector * spacing

    tx.Commit();
}}"""))
        return samples  # 6

    # ------------------------------------------------------------------
    # Mirror elements
    # ------------------------------------------------------------------

    def _mirror_elements(self) -> List[SAMPLE]:
        samples = []
        mirror_cases = [
            ("YZ plane (X=0)", "XYZ.BasisX", "XYZ.Zero",  "mirror about the YZ plane"),
            ("XZ plane (Y=0)", "XYZ.BasisY", "XYZ.Zero",  "mirror about the XZ plane"),
            ("custom plane",   "new XYZ(1,1,0).Normalize()", f"new XYZ({_ft(300)}, 0, 0)", "mirror about a custom plane at 300mm offset"),
        ]
        for (plane_desc, normal, origin, instruction) in mirror_cases:
            samples.append(_s(f"Mirror geometry: {instruction}",
                f"""\
using Autodesk.Revit.DB;
using System.Collections.Generic;

using (Transaction tx = new Transaction(familyDoc, "Mirror Element"))
{{
    tx.Start();

    // Collect all geometry elements to mirror
    ICollection<ElementId> elemIds = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(GenericForm))
        .ToElementIds();

    if (elemIds.Count > 0)
    {{
        Plane mirrorPlane = Plane.CreateByNormalAndOrigin({normal}, {origin});
        ElementTransformUtils.MirrorElements(familyDoc, elemIds, mirrorPlane, true);
    }}

    tx.Commit();
}}"""))

        # Mirror about reference plane
        samples.append(_s("Mirror geometry about a named reference plane in the family editor",
            f"""\
using Autodesk.Revit.DB;
using System.Collections.Generic;
using System.Linq;

using (Transaction tx = new Transaction(familyDoc, "Mirror About Reference Plane"))
{{
    tx.Start();

    // Find the 'Center Left-Right' reference plane
    ReferencePlane centerPlane = new FilteredElementCollector(familyDoc)
        .OfClass(typeof(ReferencePlane))
        .Cast<ReferencePlane>()
        .FirstOrDefault(rp => rp.Name == "Center Left-Right");

    if (centerPlane != null)
    {{
        ICollection<ElementId> elemIds = new FilteredElementCollector(familyDoc)
            .OfClass(typeof(GenericForm))
            .ToElementIds();

        if (elemIds.Count > 0)
        {{
            Plane mirrorPlane = centerPlane.GetPlane();
            ElementTransformUtils.MirrorElements(familyDoc, elemIds, mirrorPlane, true);
        }}
    }}

    tx.Commit();
}}"""))
        return samples  # 3 + 1 = 4

    # ------------------------------------------------------------------
    # Multi-geometry families
    # ------------------------------------------------------------------

    def _multi_geometry(self) -> List[SAMPLE]:
        samples = []
        samples.append(_s("Create a bracket family with a base plate and a vertical web (two extrusions)",
            f"""\
using Autodesk.Revit.DB;

// Bracket: base plate 200x150x12mm + vertical web 150x100x10mm
using (Transaction tx = new Transaction(familyDoc, "Create Bracket"))
{{
    tx.Start();

    double bW = {_ft(200)}; double bD = {_ft(150)}; double bT = {_ft(12)};  // base plate
    double wH = {_ft(100)}; double wT = {_ft(10)};                           // web

    SketchPlane spBase = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // Base plate: extrude in Z direction
    CurveArray baseLp = new CurveArray();
    baseLp.Append(Line.CreateBound(new XYZ(-bW/2,-bD/2,0), new XYZ(bW/2,-bD/2,0)));
    baseLp.Append(Line.CreateBound(new XYZ(bW/2,-bD/2,0),  new XYZ(bW/2,bD/2,0)));
    baseLp.Append(Line.CreateBound(new XYZ(bW/2,bD/2,0),   new XYZ(-bW/2,bD/2,0)));
    baseLp.Append(Line.CreateBound(new XYZ(-bW/2,bD/2,0),  new XYZ(-bW/2,-bD/2,0)));
    CurveArrArray baseProf = new CurveArrArray();
    baseProf.Append(baseLp);
    familyDoc.FamilyCreate.NewExtrusion(true, baseProf, spBase, bT);

    // Web: extrude from top of base plate upward
    SketchPlane spWeb = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero)); // YZ plane
    CurveArray webLp = new CurveArray();
    webLp.Append(Line.CreateBound(new XYZ(0,-bD/2,bT),   new XYZ(0,bD/2,bT)));
    webLp.Append(Line.CreateBound(new XYZ(0,bD/2,bT),    new XYZ(0,bD/2,bT+wH)));
    webLp.Append(Line.CreateBound(new XYZ(0,bD/2,bT+wH), new XYZ(0,-bD/2,bT+wH)));
    webLp.Append(Line.CreateBound(new XYZ(0,-bD/2,bT+wH),new XYZ(0,-bD/2,bT)));
    CurveArrArray webProf = new CurveArrArray();
    webProf.Append(webLp);
    familyDoc.FamilyCreate.NewExtrusion(true, webProf, spWeb, wT);

    tx.Commit();
}}"""))

        samples.append(_s("Create a void extrusion to cut bolt holes in a base plate",
            f"""\
using Autodesk.Revit.DB;
using System;

// Void bolt holes: 4x M16 holes at 150mm bolt circle
using (Transaction tx = new Transaction(familyDoc, "Create Bolt Holes"))
{{
    tx.Start();

    double boltR  = {_ft(9)};    // 9mm radius (M16 clearance)
    double bcR    = {_ft(75)};   // 75mm bolt circle radius
    double thick  = {_ft(20)};   // plate thickness (void depth)
    int    n      = 4;            // 4 holes
    int    segs   = 16;           // polygon segments per hole

    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    for (int hole = 0; hole < n; hole++)
    {{
        double centerAngle = Math.PI / 2 * hole;
        double cx = bcR * Math.Cos(centerAngle);
        double cy = bcR * Math.Sin(centerAngle);

        CurveArray loop = new CurveArray();
        for (int i = 0; i < segs; i++)
        {{
            double a0 = 2 * Math.PI * i / segs;
            double a1 = 2 * Math.PI * (i + 1) / segs;
            loop.Append(Line.CreateBound(
                new XYZ(cx + boltR * Math.Cos(a0), cy + boltR * Math.Sin(a0), 0),
                new XYZ(cx + boltR * Math.Cos(a1), cy + boltR * Math.Sin(a1), 0)));
        }}
        CurveArrArray profile = new CurveArrArray();
        profile.Append(loop);
        // isSolid = false --> void cut
        familyDoc.FamilyCreate.NewExtrusion(false, profile, sp, thick);
    }}

    tx.Commit();
}}"""))

        samples.append(_s("Combine solid and void forms to create an L-bracket with a cut-out",
            f"""\
using Autodesk.Revit.DB;

// L-bracket: solid base + vertical flange, then void slot
using (Transaction tx = new Transaction(familyDoc, "Create L-Bracket"))
{{
    tx.Start();

    SketchPlane spXY = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));

    // Horizontal leg: 200x100mm, 10mm thick
    double lH = {_ft(200)}; double lD = {_ft(100)}; double t = {_ft(10)};
    CurveArray hLeg = new CurveArray();
    hLeg.Append(Line.CreateBound(new XYZ(0,0,0),   new XYZ(lH,0,0)));
    hLeg.Append(Line.CreateBound(new XYZ(lH,0,0),  new XYZ(lH,lD,0)));
    hLeg.Append(Line.CreateBound(new XYZ(lH,lD,0), new XYZ(0,lD,0)));
    hLeg.Append(Line.CreateBound(new XYZ(0,lD,0),  new XYZ(0,0,0)));
    CurveArrArray hProf = new CurveArrArray();
    hProf.Append(hLeg);
    familyDoc.FamilyCreate.NewExtrusion(true, hProf, spXY, t); // solid horizontal

    // Vertical flange: 100x150mm, 10mm thick (same thickness)
    SketchPlane spYZ = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisX, XYZ.Zero));
    double fH = {_ft(150)};
    CurveArray vFlg = new CurveArray();
    vFlg.Append(Line.CreateBound(new XYZ(0,0,t),    new XYZ(0,lD,t)));
    vFlg.Append(Line.CreateBound(new XYZ(0,lD,t),   new XYZ(0,lD,t+fH)));
    vFlg.Append(Line.CreateBound(new XYZ(0,lD,t+fH),new XYZ(0,0,t+fH)));
    vFlg.Append(Line.CreateBound(new XYZ(0,0,t+fH), new XYZ(0,0,t)));
    CurveArrArray vProf = new CurveArrArray();
    vProf.Append(vFlg);
    familyDoc.FamilyCreate.NewExtrusion(true, vProf, spYZ, t); // solid vertical

    tx.Commit();
}}"""))
        return samples  # 3

    # ------------------------------------------------------------------
    # Parametric patterns
    # ------------------------------------------------------------------

    def _parametric_patterns(self) -> List[SAMPLE]:
        samples = []
        samples.append(_s("Create a fully parametric rectangular column with Width, Depth, Height parameters",
            f"""\
using Autodesk.Revit.DB;

// Step 1: Add parameters (OUTSIDE Transaction)
FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pW = famMgr.AddParameter("Width",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pD = famMgr.AddParameter("Depth",  BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
FamilyParameter pH = famMgr.AddParameter("Height", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pW, {_ft(300)}); // 300 mm default width
famMgr.Set(pD, {_ft(300)}); // 300 mm default depth
famMgr.Set(pH, {_ft(3000)}); // 3000 mm default height

// Step 2: Create reference planes (in Transaction)
using (Transaction tx = new Transaction(familyDoc, "Create Parametric Column"))
{{
    tx.Start();
    View view = familyDoc.ActiveView;

    double halfW = {_ft(150)}; double halfD = {_ft(150)}; double h = {_ft(3000)};

    ReferencePlane rpLeft  = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ(-halfW,0,0), new XYZ(-halfW,1,0), XYZ.BasisZ, view);
    rpLeft.Name = "Left";
    ReferencePlane rpRight = familyDoc.FamilyCreate.NewReferencePlane(
        new XYZ( halfW,0,0), new XYZ( halfW,1,0), XYZ.BasisZ, view);
    rpRight.Name = "Right";

    // Extrusion profile driven by current parameter values
    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-halfW,-halfD,0), new XYZ(halfW,-halfD,0)));
    loop.Append(Line.CreateBound(new XYZ(halfW,-halfD,0),  new XYZ(halfW,halfD,0)));
    loop.Append(Line.CreateBound(new XYZ(halfW,halfD,0),   new XYZ(-halfW,halfD,0)));
    loop.Append(Line.CreateBound(new XYZ(-halfW,halfD,0),  new XYZ(-halfW,-halfD,0)));
    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero));
    familyDoc.FamilyCreate.NewExtrusion(true, profile, sp, h);

    tx.Commit();
}}"""))

        samples.append(_s("Add a formula-driven chamfer parameter: ChamferSize = Width / 10",
            f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;

// Ensure Width exists
FamilyParameter pW = famMgr.get_Parameter("Width")
    ?? famMgr.AddParameter("Width", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pW, {_ft(300)}); // 300 mm default

// Add ChamferSize driven by formula
FamilyParameter pC = famMgr.AddParameter(
    "ChamferSize", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);

// Formula: ChamferSize = Width / 10
famMgr.SetFormula(pC, "Width / 10");
// At Width=300mm -> ChamferSize = 30mm automatically"""))

        samples.append(_s("Create a parametric void extrusion controlled by a CutDepth parameter",
            f"""\
using Autodesk.Revit.DB;

FamilyManager famMgr = familyDoc.FamilyManager;
FamilyParameter pCut = famMgr.AddParameter(
    "CutDepth", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pCut, {_ft(50)}); // 50 mm default cut depth

FamilyParameter pCutW = famMgr.AddParameter(
    "CutWidth", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);
famMgr.Set(pCutW, {_ft(100)}); // 100 mm cut width

using (Transaction tx = new Transaction(familyDoc, "Create Parametric Void"))
{{
    tx.Start();

    double cutW = {_ft(100)}; double cutD = {_ft(50)}; double totalH = {_ft(300)};

    CurveArray loop = new CurveArray();
    loop.Append(Line.CreateBound(new XYZ(-cutW/2, 0, totalH - cutD),
                                  new XYZ( cutW/2, 0, totalH - cutD)));
    loop.Append(Line.CreateBound(new XYZ( cutW/2, 0, totalH - cutD),
                                  new XYZ( cutW/2, 0, totalH)));
    loop.Append(Line.CreateBound(new XYZ( cutW/2, 0, totalH),
                                  new XYZ(-cutW/2, 0, totalH)));
    loop.Append(Line.CreateBound(new XYZ(-cutW/2, 0, totalH),
                                  new XYZ(-cutW/2, 0, totalH - cutD)));

    CurveArrArray profile = new CurveArrArray();
    profile.Append(loop);
    SketchPlane sp = SketchPlane.Create(familyDoc,
        Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero));
    // isSolid = false --> void cut
    familyDoc.FamilyCreate.NewExtrusion(false, profile, sp, {_ft(200)});

    tx.Commit();
}}"""))
        return samples  # 3


if __name__ == "__main__":
    gen = AdvancedFamilyGenerator()
    samples = gen.generate()
    print(f"Generated {len(samples)} samples")
    assert all(set(s.keys()) == {"instruction", "input", "output"} for s in samples)
    print("[OK] All samples valid")
