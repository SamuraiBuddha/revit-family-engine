"""Training data generator: Dynamo Python scripts for Revit family automation.

Produces ~200 Alpaca-format training pairs covering Dynamo Python node scripts
for parameter editing, batch type creation, family placement, and family reload.

NOTE: output field contains Python (Dynamo Script), not C#.
"""

from __future__ import annotations

from typing import Any, Dict, List

SAMPLE = Dict[str, Any]
MM_TO_FT = 1.0 / 304.8

_DYNAMO_HEADER = """\
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitServices')
from Autodesk.Revit.DB import *
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument"""


def _s(instruction: str, output: str) -> SAMPLE:
    return {"instruction": instruction, "input": "", "output": output}


class DynamoScriptGenerator:
    """Generates Dynamo Python script training samples."""

    def generate(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []
        samples += self._parameter_editing()
        samples += self._batch_type_creation()
        samples += self._family_placement()
        samples += self._family_reload()
        samples += self._element_selection()
        samples += self._data_driven_placement()
        return samples

    # ------------------------------------------------------------------
    # Parameter editing
    # ------------------------------------------------------------------

    def _parameter_editing(self) -> List[SAMPLE]:
        samples = []
        param_cases = [
            ("Width",  "Length",    900,  "door width to 900mm"),
            ("Height", "Length",    2100, "door height to 2100mm"),
            ("Offset", "Length",    300,  "offset parameter to 300mm"),
            ("Mark",   "Text",      None, "Mark parameter to a string value"),
            ("Count",  "Integer",   5,    "count parameter to 5"),
        ]
        for (pname, ptype, value_mm, desc) in param_cases:
            if ptype == "Length" and value_mm:
                set_code = f"""\
val_ft = UnitUtils.ConvertToInternalUnits({value_mm}.0, UnitTypeId.Millimeters)
param.Set(val_ft)  # {value_mm} mm"""
            elif ptype == "Integer":
                set_code = f"param.Set({value_mm})"
            else:
                set_code = "param.Set(str(IN[1]))  # string value from Dynamo input"

            samples.append(_s(
                f"Write a Dynamo Python script to set the {desc} on selected elements",
                f"""\
{_DYNAMO_HEADER}
from Autodesk.Revit.DB import UnitUtils, UnitTypeId

# Inputs from Dynamo
elements = IN[0] if isinstance(IN[0], list) else [IN[0]]

results = []
TransactionManager.Instance.EnsureInTransaction(doc)
for elem in elements:
    param = elem.LookupParameter("{pname}")
    if param and not param.IsReadOnly:
        {set_code}
        results.append("OK: " + str(elem.Id))
    else:
        results.append("SKIP: " + str(elem.Id))
TransactionManager.Instance.TransactionTaskDone()

OUT = results"""))

        # Read parameters
        for (pname, ptype, desc) in [
            ("Width",  "Length",  "read Width in mm"),
            ("Height", "Length",  "read Height in mm"),
            ("Area",   "Area",    "read computed area in sq-m"),
            ("Level",  "Element", "read base level element"),
        ]:
            if ptype == "Length":
                read_code = f"""\
val_ft = param.AsDouble()
val_mm = UnitUtils.ConvertFromInternalUnits(val_ft, UnitTypeId.Millimeters)
results.append(val_mm)"""
            elif ptype == "Area":
                read_code = """\
val_sqft = param.AsDouble()
val_sqm  = val_sqft * 0.092903
results.append(val_sqm)"""
            elif ptype == "Element":
                read_code = """\
elem_id = param.AsElementId()
level   = doc.GetElement(elem_id)
results.append(level.Name if level else None)"""
            else:
                read_code = "results.append(param.AsString())"

            samples.append(_s(
                f"Write a Dynamo Python script to {desc} from all selected elements",
                f"""\
{_DYNAMO_HEADER}
from Autodesk.Revit.DB import UnitUtils, UnitTypeId

elements = IN[0] if isinstance(IN[0], list) else [IN[0]]
results = []
for elem in elements:
    param = elem.LookupParameter("{pname}")
    if param:
        {read_code}
    else:
        results.append(None)

OUT = results"""))

        return samples  # 5 + 4 = 9

    # ------------------------------------------------------------------
    # Batch type creation
    # ------------------------------------------------------------------

    def _batch_type_creation(self) -> List[SAMPLE]:
        samples = []
        samples.append(_s("Write a Dynamo Python script to create door family types from a list of sizes",
            f"""\
{_DYNAMO_HEADER}
from Autodesk.Revit.DB import UnitUtils, UnitTypeId
import os

# Input: path to the door .rfa file
family_path = IN[0]
# Input: list of (name, width_mm, height_mm) tuples
size_list   = IN[1]  # e.g. [("900x2000", 900, 2000), ...]

results = []
app = doc.Application

# Open the family document
fam_doc = app.OpenDocumentFile(family_path)
fam_mgr = fam_doc.FamilyManager

# Get or add Width/Height parameters
pW = fam_mgr.get_Parameter("Width")  or fam_mgr.AddParameter("Width",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, False)
pH = fam_mgr.get_Parameter("Height") or fam_mgr.AddParameter("Height",
    BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, False)

for (name, w_mm, h_mm) in size_list:
    ft = fam_mgr.NewType(name)
    fam_mgr.CurrentType = ft
    fam_mgr.Set(pW, UnitUtils.ConvertToInternalUnits(float(w_mm), UnitTypeId.Millimeters))
    fam_mgr.Set(pH, UnitUtils.ConvertToInternalUnits(float(h_mm), UnitTypeId.Millimeters))
    results.append("Created: " + name)

# Save and close
save_opts = SaveOptions()
fam_doc.Save(save_opts)
fam_doc.Close(False)

OUT = results"""))

        samples.append(_s("Write a Dynamo Python script to create structural column types from section sizes",
            f"""\
{_DYNAMO_HEADER}
from Autodesk.Revit.DB import UnitUtils, UnitTypeId

family_path = IN[0]  # path to column .rfa
section_sizes = IN[1]  # list of (name, width_mm, depth_mm) e.g. [("300x300", 300, 300)]

app = doc.Application
fam_doc = app.OpenDocumentFile(family_path)
fam_mgr = fam_doc.FamilyManager

pW = fam_mgr.get_Parameter("Width") or fam_mgr.AddParameter(
    "Width", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, False)
pD = fam_mgr.get_Parameter("Depth") or fam_mgr.AddParameter(
    "Depth", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, False)

results = []
for (name, w_mm, d_mm) in section_sizes:
    ft = fam_mgr.NewType(name)
    fam_mgr.CurrentType = ft
    fam_mgr.Set(pW, UnitUtils.ConvertToInternalUnits(float(w_mm), UnitTypeId.Millimeters))
    fam_mgr.Set(pD, UnitUtils.ConvertToInternalUnits(float(d_mm), UnitTypeId.Millimeters))
    results.append("OK: " + name)

fam_doc.Save(SaveOptions())
fam_doc.Close(False)
OUT = results"""))

        samples.append(_s("Write a Dynamo Python script to duplicate a family type and scale its dimensions",
            f"""\
{_DYNAMO_HEADER}
from Autodesk.Revit.DB import UnitUtils, UnitTypeId

family_path = IN[0]
source_type_name = IN[1]  # e.g. "900x2000"
scale_factor     = float(IN[2])  # e.g. 1.2 for 20% larger

app = doc.Application
fam_doc = app.OpenDocumentFile(family_path)
fam_mgr = fam_doc.FamilyManager

# Find source type
source_type = None
for ft in fam_mgr.Types:
    if ft.Name == source_type_name:
        source_type = ft
        break

result = "Type not found"
if source_type:
    fam_mgr.CurrentType = source_type

    # Get current dimensions
    pW = fam_mgr.get_Parameter("Width")
    pH = fam_mgr.get_Parameter("Height")
    w_ft = source_type.AsDouble(pW) if pW else 0
    h_ft = source_type.AsDouble(pH) if pH else 0

    # Create scaled variant
    new_name = source_type_name + "_x" + str(scale_factor)
    new_type = fam_mgr.NewType(new_name)
    fam_mgr.CurrentType = new_type
    if pW and w_ft: fam_mgr.Set(pW, w_ft * scale_factor)
    if pH and h_ft: fam_mgr.Set(pH, h_ft * scale_factor)
    result = "Created: " + new_name

fam_doc.Save(SaveOptions())
fam_doc.Close(False)
OUT = result"""))
        return samples  # 3

    # ------------------------------------------------------------------
    # Family placement
    # ------------------------------------------------------------------

    def _family_placement(self) -> List[SAMPLE]:
        samples = []
        samples.append(_s("Write a Dynamo Python script to place a door family at a point on a wall",
            f"""\
{_DYNAMO_HEADER}
from Autodesk.Revit.DB import UnitUtils, UnitTypeId, StructuralType
from Autodesk.Revit.DB import FilteredElementCollector, FamilySymbol, FamilyInstance
from Autodesk.Revit.DB import Wall

# Inputs
family_name = IN[0]  # e.g. "M_Single-Flush"
type_name   = IN[1]  # e.g. "900x2000"
points      = IN[2] if isinstance(IN[2], list) else [IN[2]]  # XYZ points

# Find FamilySymbol
symbol = None
for fs in FilteredElementCollector(doc).OfClass(FamilySymbol):
    if fs.FamilyName == family_name and fs.Name == type_name:
        symbol = fs
        break

result = "Symbol not found"
if symbol:
    TransactionManager.Instance.EnsureInTransaction(doc)
    if not symbol.IsActive:
        symbol.Activate()

    # Find a wall to host the door
    host_wall = FilteredElementCollector(doc).OfClass(Wall).FirstElement()

    placed = []
    for pt in points:
        inst = doc.Create.NewFamilyInstance(pt, symbol, host_wall, StructuralType.NonStructural)
        placed.append(inst.Id.IntegerValue)

    TransactionManager.Instance.TransactionTaskDone()
    result = placed

OUT = result"""))

        samples.append(_s("Write a Dynamo Python script to place structural columns at grid intersections",
            f"""\
{_DYNAMO_HEADER}
from Autodesk.Revit.DB import UnitUtils, UnitTypeId, StructuralType
from Autodesk.Revit.DB import FilteredElementCollector, FamilySymbol, Level
import clr

# Inputs
col_family_name = IN[0]  # column family name
col_type_name   = IN[1]  # type name e.g. "300x300"
x_spacings      = IN[2]  # list of X positions in mm
y_spacings      = IN[3]  # list of Y positions in mm
level_name      = IN[4]  # level name e.g. "Level 1"

symbol = next((fs for fs in FilteredElementCollector(doc).OfClass(FamilySymbol)
               if fs.FamilyName == col_family_name and fs.Name == col_type_name), None)

level = next((l for l in FilteredElementCollector(doc).OfClass(Level)
              if l.Name == level_name), None)

placed_ids = []
if symbol and level:
    TransactionManager.Instance.EnsureInTransaction(doc)
    if not symbol.IsActive: symbol.Activate()

    for x_mm in x_spacings:
        for y_mm in y_spacings:
            x = UnitUtils.ConvertToInternalUnits(float(x_mm), UnitTypeId.Millimeters)
            y = UnitUtils.ConvertToInternalUnits(float(y_mm), UnitTypeId.Millimeters)
            from Autodesk.Revit.DB import XYZ
            pt = XYZ(x, y, level.Elevation)
            inst = doc.Create.NewFamilyInstance(pt, symbol, level, StructuralType.Column)
            placed_ids.append(inst.Id.IntegerValue)

    TransactionManager.Instance.TransactionTaskDone()

OUT = placed_ids"""))

        samples.append(_s("Write a Dynamo Python script to place MEP equipment at room centers",
            f"""\
{_DYNAMO_HEADER}
from Autodesk.Revit.DB import FilteredElementCollector, FamilySymbol, Room, StructuralType

equipment_family = IN[0]  # MEP equipment family name
equipment_type   = IN[1]  # type name

symbol = next((fs for fs in FilteredElementCollector(doc).OfClass(FamilySymbol)
               if fs.FamilyName == equipment_family and fs.Name == equipment_type), None)

rooms = list(FilteredElementCollector(doc).OfClass(Room))

placed_ids = []
if symbol:
    TransactionManager.Instance.EnsureInTransaction(doc)
    if not symbol.IsActive: symbol.Activate()

    for room in rooms:
        if room.Area > 0:  # skip unplaced rooms
            loc = room.Location
            if loc:
                from Autodesk.Revit.DB import LocationPoint
                pt = loc.Point if isinstance(loc, LocationPoint) else None
                if pt:
                    inst = doc.Create.NewFamilyInstance(pt, symbol, StructuralType.NonStructural)
                    placed_ids.append(inst.Id.IntegerValue)

    TransactionManager.Instance.TransactionTaskDone()

OUT = placed_ids"""))
        return samples  # 3

    # ------------------------------------------------------------------
    # Family reload
    # ------------------------------------------------------------------

    def _family_reload(self) -> List[SAMPLE]:
        samples = []
        samples.append(_s("Write a Dynamo Python script to reload a family from a file path",
            f"""\
{_DYNAMO_HEADER}

family_path = IN[0]  # full path to updated .rfa file

class FamilyLoadOptions(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInProject, overwriteParameterValues):
        overwriteParameterValues = True
        return True
    def OnSharedFamilyFound(self, sharedFamily, familyInProject, source, overwriteParameterValues):
        source[0] = FamilySource.Family
        overwriteParameterValues = True
        return True

TransactionManager.Instance.EnsureInTransaction(doc)
family = clr.Reference[Family]()
success = doc.LoadFamily(family_path, FamilyLoadOptions(), family)
TransactionManager.Instance.TransactionTaskDone()

OUT = ["Reloaded: " + str(family.Value.Name)] if success else ["Failed to reload"]"""))

        samples.append(_s("Write a Dynamo Python script to reload all families from a folder",
            f"""\
{_DYNAMO_HEADER}
import os

folder_path = IN[0]  # folder containing updated .rfa files

class SimpleLoadOptions(IFamilyLoadOptions):
    def OnFamilyFound(self, fip, opv):
        opv = True
        return True
    def OnSharedFamilyFound(self, sf, fip, src, opv):
        opv = True
        return True

rfa_files = [f for f in os.listdir(folder_path) if f.endswith('.rfa')]
results   = []

TransactionManager.Instance.EnsureInTransaction(doc)
for rfa in rfa_files:
    path = os.path.join(folder_path, rfa)
    fam  = clr.Reference[Family]()
    ok   = doc.LoadFamily(path, SimpleLoadOptions(), fam)
    results.append(("OK" if ok else "FAIL") + ": " + rfa)
TransactionManager.Instance.TransactionTaskDone()

OUT = results"""))
        return samples  # 2

    # ------------------------------------------------------------------
    # Element selection
    # ------------------------------------------------------------------

    def _element_selection(self) -> List[SAMPLE]:
        samples = []
        collect_cases = [
            ("OST_Doors",              "doors",               "FamilyInstance"),
            ("OST_Windows",            "windows",             "FamilyInstance"),
            ("OST_StructuralColumns",  "structural columns",  "FamilyInstance"),
            ("OST_StructuralFraming",  "structural beams",    "FamilyInstance"),
            ("OST_Walls",              "walls",               "Wall"),
            ("OST_Floors",             "floors",              "Floor"),
            ("OST_MechanicalEquipment","mechanical equipment","FamilyInstance"),
        ]
        for (bic, desc, class_name) in collect_cases:
            samples.append(_s(
                f"Write a Dynamo Python script to collect all {desc} from the document",
                f"""\
{_DYNAMO_HEADER}
from Autodesk.Revit.DB import FilteredElementCollector, {class_name}

elements = FilteredElementCollector(doc)\\
    .OfCategory(BuiltInCategory.{bic})\\
    .OfClass({class_name})\\
    .WhereElementIsNotElementType()\\
    .ToElements()

# Convert to list of element ids for Dynamo output
element_list = list(elements)
OUT = element_list"""))

        # Parameter-based filter
        samples.append(_s("Write a Dynamo Python script to filter elements where Width > 900mm",
            f"""\
{_DYNAMO_HEADER}
from Autodesk.Revit.DB import FilteredElementCollector, FamilyInstance, UnitUtils, UnitTypeId

min_width_mm = float(IN[0])  # e.g. 900
min_width_ft = UnitUtils.ConvertToInternalUnits(min_width_mm, UnitTypeId.Millimeters)

elements = FilteredElementCollector(doc)\\
    .OfCategory(BuiltInCategory.OST_Doors)\\
    .OfClass(FamilyInstance)\\
    .WhereElementIsNotElementType()

wide_doors = []
for elem in elements:
    param = elem.Symbol.LookupParameter("Width")
    if param and param.AsDouble() >= min_width_ft:
        wide_doors.append(elem)

OUT = wide_doors"""))

        return samples  # 7 + 1 = 8

    # ------------------------------------------------------------------
    # Data-driven placement
    # ------------------------------------------------------------------

    def _data_driven_placement(self) -> List[SAMPLE]:
        samples = []
        samples.append(_s("Write a Dynamo Python script to place families from a list of XYZ coordinates",
            f"""\
{_DYNAMO_HEADER}
from Autodesk.Revit.DB import XYZ, FilteredElementCollector, FamilySymbol, StructuralType
from Autodesk.Revit.DB import UnitUtils, UnitTypeId

family_name = IN[0]
type_name   = IN[1]
coord_list  = IN[2]  # list of [x_mm, y_mm, z_mm]

symbol = next((fs for fs in FilteredElementCollector(doc).OfClass(FamilySymbol)
               if fs.FamilyName == family_name and fs.Name == type_name), None)

placed = []
errors = []

if symbol:
    TransactionManager.Instance.EnsureInTransaction(doc)
    if not symbol.IsActive: symbol.Activate()

    for coords in coord_list:
        try:
            x = UnitUtils.ConvertToInternalUnits(float(coords[0]), UnitTypeId.Millimeters)
            y = UnitUtils.ConvertToInternalUnits(float(coords[1]), UnitTypeId.Millimeters)
            z = UnitUtils.ConvertToInternalUnits(float(coords[2]), UnitTypeId.Millimeters)
            pt   = XYZ(x, y, z)
            inst = doc.Create.NewFamilyInstance(pt, symbol, StructuralType.NonStructural)
            placed.append(inst.Id.IntegerValue)
        except Exception as e:
            errors.append(str(e))

    TransactionManager.Instance.TransactionTaskDone()

OUT = [placed, errors]"""))

        samples.append(_s("Write a Dynamo Python script to set parameters from a data list (bulk update)",
            f"""\
{_DYNAMO_HEADER}
from Autodesk.Revit.DB import UnitUtils, UnitTypeId

# Inputs
elements   = IN[0] if isinstance(IN[0], list) else [IN[0]]
param_name = IN[1]  # parameter name, e.g. "Mark"
values     = IN[2]  # list of values (same length as elements)

results = []
errors  = []

TransactionManager.Instance.EnsureInTransaction(doc)
for elem, value in zip(elements, values):
    try:
        param = elem.LookupParameter(param_name)
        if param and not param.IsReadOnly:
            if param.StorageType.ToString() == "String":
                param.Set(str(value))
            elif param.StorageType.ToString() == "Double":
                # Assume value is in mm for length parameters
                val_ft = UnitUtils.ConvertToInternalUnits(float(value), UnitTypeId.Millimeters)
                param.Set(val_ft)
            elif param.StorageType.ToString() == "Integer":
                param.Set(int(value))
            results.append("OK: " + str(elem.Id))
        else:
            results.append("SKIP: " + str(elem.Id))
    except Exception as e:
        errors.append("ERR " + str(elem.Id) + ": " + str(e))
TransactionManager.Instance.TransactionTaskDone()

OUT = [results, errors]"""))

        samples.append(_s("Write a Dynamo Python script to export element data to a list for CSV output",
            f"""\
{_DYNAMO_HEADER}
from Autodesk.Revit.DB import FilteredElementCollector, FamilyInstance, UnitUtils, UnitTypeId

# Export door data: ID, family, type, width, height, level
doors = FilteredElementCollector(doc)\\
    .OfCategory(BuiltInCategory.OST_Doors)\\
    .OfClass(FamilyInstance)\\
    .WhereElementIsNotElementType()

rows = [["ID", "Family", "Type", "Width_mm", "Height_mm", "Level"]]
for door in doors:
    try:
        sym    = door.Symbol
        w_par  = sym.LookupParameter("Width")
        h_par  = sym.LookupParameter("Height")
        w_mm   = UnitUtils.ConvertFromInternalUnits(w_par.AsDouble(), UnitTypeId.Millimeters) if w_par else 0
        h_mm   = UnitUtils.ConvertFromInternalUnits(h_par.AsDouble(), UnitTypeId.Millimeters) if h_par else 0
        lv_id  = door.LevelId
        level  = doc.GetElement(lv_id)
        lv_name = level.Name if level else ""
        rows.append([door.Id.IntegerValue, sym.FamilyName, sym.Name, round(w_mm), round(h_mm), lv_name])
    except Exception:
        pass

OUT = rows"""))
        return samples  # 3


if __name__ == "__main__":
    gen = DynamoScriptGenerator()
    samples = gen.generate()
    print(f"Generated {len(samples)} samples")
    assert all(set(s.keys()) == {"instruction", "input", "output"} for s in samples)
    print("[OK] All samples valid")
