"""Training data generator: Building code compliance validation.

Produces ~260 Alpaca-format training pairs covering IBC, NFPA, ADA, IMC, and
ICC A117.1 compliance checks implemented as Revit API C# code that reads family
parameters, compares against regulatory thresholds, and raises TaskDialog warnings.

Code sections cited:
  IBC 1005.1  -- egress width
  IBC 1010.1  -- door dimensions
  IBC 1011    -- stair geometry
  IBC 1015    -- guard/railing height
  NFPA 80     -- fire door assemblies
  NFPA 101    -- fire rating / means of egress
  ADA 404     -- accessible door clearance
  ADA 405     -- accessible ramp slope
  ICC A117.1  -- grab bars, maneuvering clearance
  IMC 403     -- ventilation / minimum OA
  IBC 1208    -- minimum room area and dimensions
"""

from __future__ import annotations

from typing import Any, Dict, List

SAMPLE = Dict[str, Any]
MM_TO_FT = 1.0 / 304.8
IN_TO_FT = 1.0 / 12.0


def _s(instruction: str, output: str) -> SAMPLE:
    return {"instruction": instruction, "input": "", "output": output}


def _ft(mm: float) -> str:
    return f"{mm * MM_TO_FT:.6f}"


def _in(inches: float) -> str:
    return f"{inches * IN_TO_FT:.6f}"


class BuildingCodeComplianceGenerator:
    """Generates training samples for building code compliance validation in Revit."""

    def generate(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []
        samples += self._egress_width()
        samples += self._door_dimensions()
        samples += self._stair_geometry()
        samples += self._guard_railing()
        samples += self._fire_ratings()
        samples += self._accessibility()
        samples += self._room_areas()
        samples += self._ventilation()
        samples += self._structural_clearances()
        return samples

    # ------------------------------------------------------------------
    # IBC 1005.1 -- Egress width
    # ------------------------------------------------------------------

    def _egress_width(self) -> List[SAMPLE]:
        samples = []

        # Basic stair egress width per occupant load (0.3 in/occupant = 0.025 ft/occupant)
        for occupants, desc in [
            (50, "small assembly room"),
            (100, "medium classroom"),
            (200, "large open office"),
            (500, "auditorium"),
        ]:
            min_stair_in = occupants * 0.3
            min_other_in = occupants * 0.2
            min_stair_ft = min_stair_in * IN_TO_FT
            min_other_ft = min_other_in * IN_TO_FT
            samples.append(_s(
                f"Validate IBC 1005.1 egress width for {occupants} occupants ({desc})",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1005.1: Egress width -- {occupants} occupants
// Stair egress: 0.3 in/occupant, Other egress: 0.2 in/occupant
// Required stair width: {min_stair_in:.1f} in ({min_stair_ft:.6f} ft)
// Required other width: {min_other_in:.1f} in ({min_other_ft:.6f} ft)
void ValidateEgressWidth(FamilyInstance inst)
{{
    int occupants = {occupants}; // {desc}

    // IBC 1005.1: 0.3 in per occupant for stairs
    double minStairFt = {min_stair_ft:.6f}; // {min_stair_in:.1f} in
    // IBC 1005.1: 0.2 in per occupant for other egress components
    double minOtherFt = {min_other_ft:.6f}; // {min_other_in:.1f} in
    // IBC 1005.1: Absolute minimum corridor width 44 in
    double absMinFt   = {44 * IN_TO_FT:.6f}; // 44 in

    Parameter pStairW = inst.LookupParameter("Stair Width");
    Parameter pCorrW  = inst.LookupParameter("Corridor Width");

    if (pStairW != null)
    {{
        double stairW = pStairW.AsDouble();
        if (stairW < minStairFt)
        {{
            TaskDialog.Show("IBC 1005.1 Violation",
                $"Stair width {{stairW * 12.0:F2}} in is less than required "
                + $"{{minStairFt * 12.0:F2}} in for {{occupants}} occupants. "
                + "Ref: IBC 1005.1 (0.3 in/occupant on stairs).");
        }}
    }}

    if (pCorrW != null)
    {{
        double corrW = pCorrW.AsDouble();
        double required = Math.Max(minOtherFt, absMinFt);
        if (corrW < required)
        {{
            TaskDialog.Show("IBC 1005.1 Violation",
                $"Corridor width {{corrW * 12.0:F2}} in is less than required "
                + $"{{required * 12.0:F2}} in. "
                + "Ref: IBC 1005.1 / IBC 1020.2 (44 in absolute minimum).");
        }}
    }}
}}""",
            ))

        # Corridor minimum 36 in (residential) vs 44 in (commercial)
        for (occ_type, min_in, code_ref) in [
            ("Residential R-2",  36, "IBC 1005.1 / IBC 1020.2 (R occupancy: 36 in min)"),
            ("Commercial B",     44, "IBC 1005.1 / IBC 1020.2 (non-residential: 44 in min)"),
            ("Assembly A-1",     44, "IBC 1005.1 (assembly: 44 in min corridor)"),
            ("Institutional I-2", 96, "IBC 1005.1 (health care: 96 in min corridor)"),
        ]:
            min_ft = min_in * IN_TO_FT
            samples.append(_s(
                f"Validate corridor minimum width for {occ_type} occupancy per IBC 1005.1",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// {code_ref}
void ValidateCorridorWidth_{occ_type.replace(' ', '_').replace('-', '_')}(FamilyInstance corridorInst)
{{
    double minWidthFt = {min_ft:.6f}; // {min_in} in
    // {code_ref}

    Parameter pWidth = corridorInst.LookupParameter("Corridor Width");
    if (pWidth == null) return;

    double actualWidthFt = pWidth.AsDouble();
    if (actualWidthFt < minWidthFt)
    {{
        TaskDialog.Show("IBC 1005.1 Violation",
            $"Corridor width {{actualWidthFt * 12.0:F2}} in is below the {min_in}-inch "
            + "minimum for {occ_type} occupancy. "
            + "Ref: {code_ref}");
    }}
}}""",
            ))

        # Egress capacity -- stairway must not be less than 44 in regardless of occupant load
        samples.append(_s(
            "Validate IBC 1005.1 absolute minimum stair width (44 in) regardless of occupant load",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1005.1: Stair minimum width is 44 in regardless of occupant count
// Exception: 36 in permitted where occupant load <= 50
void ValidateStairAbsoluteMinimum(FamilyInstance stairInst)
{{
    double absMinFt    = {44 * IN_TO_FT:.6f}; // 44 in -- IBC 1005.1
    double exceptionFt = {36 * IN_TO_FT:.6f}; // 36 in -- IBC 1005.1 exception (<=50 occ)

    Parameter pWidth = stairInst.LookupParameter("Stair Width");
    Parameter pOccupants = stairInst.LookupParameter("Occupant Load");
    if (pWidth == null) return;

    double width = pWidth.AsDouble();
    int occupants = pOccupants != null ? (int)pOccupants.AsDouble() : 999;

    double required = (occupants <= 50) ? exceptionFt : absMinFt;
    if (width < required)
    {{
        TaskDialog.Show("IBC 1005.1 Violation",
            $"Stair width {{width * 12.0:F2}} in is below the required "
            + $"{{required * 12.0:F2}} in minimum. "
            + "Ref: IBC 1005.1 (44 in min; 36 in exception for <=50 occupants).");
    }}
}}""",
        ))

        # Ramp egress width (0.2 in/occupant, min 44 in)
        for occupants in [75, 150, 300]:
            min_ft = max(occupants * 0.2, 44) * IN_TO_FT
            samples.append(_s(
                f"Validate IBC 1005.1 ramp egress width for {occupants} occupants",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1005.1: Ramp egress width = 0.2 in/occupant, min 44 in
void ValidateRampEgressWidth(FamilyInstance rampInst)
{{
    int occupants = {occupants};
    double calcMinFt = {occupants * 0.2 * IN_TO_FT:.6f}; // {occupants * 0.2:.1f} in (0.2 in/occ)
    double absMinFt  = {44 * IN_TO_FT:.6f}; // 44 in absolute minimum
    double required  = Math.Max(calcMinFt, absMinFt); // {max(occupants * 0.2, 44):.1f} in

    Parameter pWidth = rampInst.LookupParameter("Ramp Width");
    if (pWidth == null) return;

    double actual = pWidth.AsDouble();
    if (actual < required)
    {{
        TaskDialog.Show("IBC 1005.1 Violation",
            $"Ramp width {{actual * 12.0:F2}} in is below required "
            + $"{{required * 12.0:F2}} in for {{occupants}} occupants. "
            + "Ref: IBC 1005.1 (0.2 in/occupant ramp, 44 in min).");
    }}
}}""",
            ))

        # Egress through intervening rooms -- verify path is not through hazardous areas
        samples.append(_s(
            "Check IBC 1016.2 egress path continuity -- no travel through high-hazard areas",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1016.2: Exit access shall not pass through rooms with higher hazard occupancy
// Parameter "Hazard Level" encodes: 0=low, 1=medium, 2=high
void ValidateEgressPathHazard(FamilyInstance exitDoor)
{{
    Parameter pOriginHazard = exitDoor.LookupParameter("Origin Room Hazard Level");
    Parameter pTargetHazard = exitDoor.LookupParameter("Target Room Hazard Level");

    if (pOriginHazard == null || pTargetHazard == null) return;

    int originHazard = (int)pOriginHazard.AsDouble();
    int targetHazard = (int)pTargetHazard.AsDouble();

    // Egress cannot pass FROM lower hazard THROUGH higher hazard
    if (targetHazard > originHazard)
    {{
        TaskDialog.Show("IBC 1016.2 Violation",
            "Exit access path passes through a room with higher hazard classification. "
            + $"Origin hazard level: {{originHazard}}, Target hazard level: {{targetHazard}}. "
            + "Ref: IBC 1016.2 (egress path must not pass through rooms of higher hazard).");
    }}
}}""",
        ))

        # Travel distance checks
        for (occ, max_travel_ft, sprinklered_ft, desc) in [
            ("B",  200, 300, "office/business"),
            ("A",  200, 250, "assembly"),
            ("I-2", 150, 200, "institutional health care"),
        ]:
            samples.append(_s(
                f"Validate IBC 1017.1 maximum exit access travel distance for {desc} ({occ}) occupancy",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1017.1: Max travel distance to exit -- {occ} ({desc})
// Non-sprinklered: {max_travel_ft} ft, Sprinklered: {sprinklered_ft} ft
void ValidateTravelDistance_{occ.replace('-', '_')}(FamilyInstance room)
{{
    double maxDistFt      = {float(max_travel_ft):.1f}; // IBC 1017.1 non-sprinklered
    double maxSprinkledFt = {float(sprinklered_ft):.1f}; // IBC 1017.1 sprinklered

    Parameter pDist       = room.LookupParameter("Max Travel Distance");
    Parameter pSprinklered = room.LookupParameter("Sprinkler System");

    if (pDist == null) return;

    double actual      = pDist.AsDouble();
    bool sprinklered   = pSprinklered != null && pSprinklered.AsInteger() == 1;
    double limit       = sprinklered ? maxSprinkledFt : maxDistFt;

    if (actual > limit)
    {{
        TaskDialog.Show("IBC 1017.1 Violation",
            $"Travel distance {{actual:F1}} ft exceeds the {{limit:F1}} ft maximum "
            + $"for {occ} ({desc}) occupancy (sprinklered: {{sprinklered}}). "
            + "Ref: IBC 1017.1.");
    }}
}}""",
            ))

        # Dead-end corridor limit
        samples.append(_s(
            "Validate IBC 1020.4 dead-end corridor length (20 ft max, 50 ft sprinklered)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1020.4: Dead-end corridor maximum length
// Non-sprinklered: 20 ft, Sprinklered: 50 ft
void ValidateDeadEndCorridor(FamilyInstance corridorSegment)
{{
    double maxNonSprFt = 20.0; // IBC 1020.4 non-sprinklered
    double maxSprFt    = 50.0; // IBC 1020.4 sprinklered

    Parameter pDeadEnd    = corridorSegment.LookupParameter("Dead End Length");
    Parameter pSprinklered = corridorSegment.LookupParameter("Sprinkler System");
    if (pDeadEnd == null) return;

    double deadEndFt   = pDeadEnd.AsDouble();
    bool sprinklered   = pSprinklered != null && pSprinklered.AsInteger() == 1;
    double limit       = sprinklered ? maxSprFt : maxNonSprFt;

    if (deadEndFt > limit)
    {{
        TaskDialog.Show("IBC 1020.4 Violation",
            $"Dead-end corridor length {{deadEndFt:F1}} ft exceeds {{limit:F1}} ft maximum "
            + $"(sprinklered: {{sprinklered}}). "
            + "Ref: IBC 1020.4.");
    }}
}}""",
        ))

        # Number of exits required (IBC 1006.2 -- occupant load determines exits needed)
        for (occ_min, occ_max, exits, code) in [
            (1,   499,  2, "IBC 1006.3.3: 1-499 occupants require 2 exits"),
            (500, 999,  3, "IBC 1006.3.3: 500-999 occupants require 3 exits"),
            (1000, 9999, 4, "IBC 1006.3.3: 1000+ occupants require 4 exits"),
        ]:
            samples.append(_s(
                f"Validate IBC 1006.3.3 required number of exits for {occ_min}-{occ_max} occupant load",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// {code}
void ValidateExitCount_{occ_min}_{occ_max}(FamilyInstance floorInst)
{{
    int requiredExits = {exits}; // {code}

    Parameter pOccupants = floorInst.LookupParameter("Occupant Load");
    Parameter pExitCount = floorInst.LookupParameter("Exit Count");
    if (pOccupants == null || pExitCount == null) return;

    double occupants = pOccupants.AsDouble();
    int exits        = (int)pExitCount.AsDouble();

    if (occupants >= {occ_min} && occupants <= {occ_max} && exits < requiredExits)
    {{
        TaskDialog.Show("IBC 1006.3.3 Violation",
            $"{{occupants:F0}} occupants require {{requiredExits}} exits; only {{exits}} provided. "
            + "Ref: {code}");
    }}
}}""",
            ))

        # Common path of egress travel (IBC 1006.2.1 -- 75 ft non-sprinklered, 100 ft sprinklered)
        samples.append(_s(
            "Validate IBC 1006.2.1 common path of egress travel (75 ft non-sprinklered, 100 ft sprinklered)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1006.2.1: Common path of egress travel maximum distances
// Non-sprinklered: 75 ft, Sprinklered: 100 ft
void ValidateCommonPathEgress(FamilyInstance roomInst)
{
    double maxNonSprFt = 75.0;  // IBC 1006.2.1
    double maxSprFt    = 100.0; // IBC 1006.2.1 sprinklered

    Parameter pCommonPath  = roomInst.LookupParameter("Common Path of Egress Travel");
    Parameter pSprinklered = roomInst.LookupParameter("Sprinkler System");
    if (pCommonPath == null) return;

    double path = pCommonPath.AsDouble();
    bool spr    = pSprinklered != null && pSprinklered.AsInteger() == 1;
    double limit = spr ? maxSprFt : maxNonSprFt;

    if (path > limit)
    {
        TaskDialog.Show("IBC 1006.2.1 Violation",
            $"Common path of egress travel {path:F1} ft exceeds {limit:F0} ft maximum "
            + $"(sprinklered: {spr}). "
            + "Ref: IBC 1006.2.1.");
    }
}""",
        ))

        # Exit separation distance (IBC 1007.1.1 -- exits must be separated by 1/3 diagonal)
        samples.append(_s(
            "Validate IBC 1007.1.1 minimum separation distance between exits (1/3 diagonal, or 1/2 sprinklered)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using System;

// IBC 1007.1.1: Two exit doorways must be separated by >= 1/3 of diagonal of floor area
// Sprinklered buildings: separation >= 1/4 of diagonal
void ValidateExitSeparation(FamilyInstance floorInst)
{{
    Parameter pDiagonal   = floorInst.LookupParameter("Floor Diagonal");
    Parameter pSeparation = floorInst.LookupParameter("Exit Separation Distance");
    Parameter pSprinklered = floorInst.LookupParameter("Sprinkler System");
    if (pDiagonal == null || pSeparation == null) return;

    double diagonal   = pDiagonal.AsDouble();
    bool spr          = pSprinklered != null && pSprinklered.AsInteger() == 1;
    double minFraction = spr ? 1.0 / 4.0 : 1.0 / 3.0;
    double required   = diagonal * minFraction;
    double actual     = pSeparation.AsDouble();

    if (actual < required)
    {{
        TaskDialog.Show("IBC 1007.1.1 Violation",
            $"Exit separation {{actual:F1}} ft is less than required {{required:F1}} ft "
            + $"({{minFraction:P0}} of diagonal {{diagonal:F1}} ft). "
            + "Ref: IBC 1007.1.1.");
    }}
}}""",
        ))

        # Egress lighting (IBC 1008.1 -- 1 fc average, 0.1 fc minimum along path)
        samples.append(_s(
            "Validate IBC 1008.1 means of egress illumination (1 fc average, 0.1 fc minimum at floor level)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1008.1: Means of egress illumination
// Average: 1 footcandle at floor level
// Minimum: 0.1 footcandle at any point (ratio not to exceed 40:1)
void ValidateEgressLighting(FamilyInstance corridorInst)
{
    double minAvgFC  = 1.0;  // 1 fc average -- IBC 1008.1
    double minPointFC = 0.1; // 0.1 fc minimum -- IBC 1008.1
    double maxRatio  = 40.0; // 40:1 max/min ratio -- IBC 1008.1

    Parameter pAvgLight = corridorInst.LookupParameter("Average Illuminance (fc)");
    Parameter pMinLight = corridorInst.LookupParameter("Min Illuminance (fc)");
    if (pAvgLight == null) return;

    double avg = pAvgLight.AsDouble();
    if (avg < minAvgFC)
    {
        TaskDialog.Show("IBC 1008.1 Violation",
            $"Egress corridor average illuminance {avg:F2} fc is below required 1.0 fc. "
            + "Ref: IBC 1008.1.");
    }

    if (pMinLight != null)
    {
        double min = pMinLight.AsDouble();
        if (min < minPointFC)
        {
            TaskDialog.Show("IBC 1008.1 Violation",
                $"Egress corridor minimum illuminance {min:F3} fc is below required 0.1 fc. "
                + "Ref: IBC 1008.1.");
        }
        if (min > 0 && avg / min > maxRatio)
        {
            TaskDialog.Show("IBC 1008.1 Violation",
                $"Illuminance ratio {(avg/min):F1}:1 exceeds 40:1 maximum. "
                + "Ref: IBC 1008.1.");
        }
    }
}""",
        ))

        # Exit sign visibility (IBC 1013.1 -- legible at 100 ft)
        samples.append(_s(
            "Validate IBC 1013.1 exit sign placement -- visible from 100 ft and not blocked",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1013.1: Exit signs must be visible from the path of egress travel
// Letters must be legible from 100 ft
void ValidateExitSignVisibility(FamilyInstance exitSignInst)
{
    double maxDistFt = 100.0; // 100 ft viewing distance -- IBC 1013.1

    Parameter pViewDist = exitSignInst.LookupParameter("Max Viewing Distance");
    Parameter pIsBlocked = exitSignInst.LookupParameter("Is Obstructed");

    if (pIsBlocked != null && pIsBlocked.AsInteger() == 1)
    {
        TaskDialog.Show("IBC 1013.1 Violation",
            "Exit sign is obstructed and not visible from the path of egress travel. "
            + "Ref: IBC 1013.1.");
    }

    if (pViewDist != null && pViewDist.AsDouble() > maxDistFt)
    {
        TaskDialog.Show("IBC 1013.1 Violation",
            $"Exit sign viewing distance {pViewDist.AsDouble():F1} ft exceeds 100 ft maximum. "
            + "Ref: IBC 1013.1.");
    }
}""",
        ))

        # Horizontal exit capacity (IBC 1026 -- refuge area 3 sq ft/occupant)
        samples.append(_s(
            "Validate IBC 1026.4 horizontal exit refuge area (3 sq ft per occupant)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1026.4: Refuge area on each side of horizontal exit >= 3 sq ft per occupant
void ValidateHorizontalExitRefuge(FamilyInstance refugeAreaInst)
{
    double minSqFtPerPerson = 3.0; // IBC 1026.4

    Parameter pArea      = refugeAreaInst.LookupParameter("Refuge Area (sq ft)");
    Parameter pOccupants = refugeAreaInst.LookupParameter("Served Occupant Load");
    if (pArea == null || pOccupants == null) return;

    double area      = pArea.AsDouble();
    double occupants = pOccupants.AsDouble();
    double required  = occupants * minSqFtPerPerson;

    if (area < required)
    {
        TaskDialog.Show("IBC 1026.4 Violation",
            $"Refuge area {area:F1} sq ft is less than required {required:F1} sq ft "
            + $"({occupants:F0} occupants x 3 sq ft/person). "
            + "Ref: IBC 1026.4.");
    }
}""",
        ))

        # Two-exit distance rule for corridors (IBC 1006.2.1 -- common path)
        for (occ, max_ft, desc) in [
            ("I-2 health care",   100, "IBC 1006.2.1 exception: 100 ft health care"),
            ("H hazardous",        25, "IBC 1006.2.1 H occupancy: 25 ft limit"),
            ("R residential",     125, "IBC 1006.2.1 R sprinklered: 125 ft"),
        ]:
            samples.append(_s(
                f"Validate IBC 1006.2.1 common path of egress for {occ} occupancy ({max_ft} ft max)",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// {desc}
void ValidateCommonPathEgress_{occ.split(' ')[0]}(FamilyInstance roomInst)
{{
    double maxFt = {float(max_ft)};

    Parameter pPath = roomInst.LookupParameter("Common Path of Egress Travel");
    if (pPath == null) return;

    double path = pPath.AsDouble();
    if (path > maxFt)
    {{
        TaskDialog.Show("IBC 1006.2.1 Violation",
            $"Common path of egress {{path:F1}} ft exceeds {{maxFt:F0}} ft for {occ}. "
            + "Ref: {desc}");
    }}
}}""",
            ))

        # Area of refuge (IBC 1009.6 -- 15 sq ft per occupant, adjacent to stair enclosure)
        samples.append(_s(
            "Validate IBC 1009.6 area of refuge minimum size (15 sq ft per wheelchair space)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1009.6.3: Each wheelchair space in area of refuge must be >= 30 in x 48 in
// IBC 1009.6: Minimum 2 wheelchair spaces required in most buildings > 4 stories
void ValidateAreaOfRefuge(FamilyInstance refugeInst)
{
    double minSpaceW  = 30.0 / 12.0; // 30 in = 2.5 ft -- IBC 1009.6.3
    double minSpaceD  = 48.0 / 12.0; // 48 in = 4 ft   -- IBC 1009.6.3
    int    minSpaces  = 2;            // IBC 1009.6

    Parameter pSpaceW  = refugeInst.LookupParameter("Wheelchair Space Width");
    Parameter pSpaceD  = refugeInst.LookupParameter("Wheelchair Space Depth");
    Parameter pCount   = refugeInst.LookupParameter("Wheelchair Space Count");

    if (pSpaceW != null && pSpaceW.AsDouble() < minSpaceW)
        TaskDialog.Show("IBC 1009.6.3 Violation",
            $"Wheelchair space width {pSpaceW.AsDouble() * 12.0:F1} in < 30 in. Ref: IBC 1009.6.3.");

    if (pSpaceD != null && pSpaceD.AsDouble() < minSpaceD)
        TaskDialog.Show("IBC 1009.6.3 Violation",
            $"Wheelchair space depth {pSpaceD.AsDouble() * 12.0:F1} in < 48 in. Ref: IBC 1009.6.3.");

    if (pCount != null && pCount.AsDouble() < minSpaces)
        TaskDialog.Show("IBC 1009.6 Violation",
            $"Area of refuge has {pCount.AsDouble():F0} wheelchair spaces; {minSpaces} required. Ref: IBC 1009.6.");
}""",
        ))

        # Egress stair enclosure (IBC 1023.1 -- fire-resistance rating)
        samples.append(_s(
            "Validate IBC 1023.1 exit enclosure stair fire-resistance rating (1 hr <=4 floors, 2 hr >4 floors)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1023.1: Exit enclosures require fire-resistance-rated construction
// Buildings up to 4 stories: 1-hour rated enclosure
// Buildings more than 4 stories: 2-hour rated enclosure
void ValidateStairEnclosureRating(FamilyInstance stairEnclosureInst)
{
    Parameter pStories = stairEnclosureInst.LookupParameter("Building Stories");
    Parameter pRating  = stairEnclosureInst.LookupParameter("Fire Rating (hr)");
    if (pStories == null || pRating == null) return;

    int stories        = (int)pStories.AsDouble();
    double rating      = pRating.AsDouble();
    double requiredHr  = (stories > 4) ? 2.0 : 1.0;

    if (rating < requiredHr)
    {
        TaskDialog.Show("IBC 1023.1 Violation",
            $"Exit enclosure fire rating {rating} hr is below required {requiredHr} hr "
            + $"for {stories}-story building. "
            + "Ref: IBC 1023.1.");
    }
}""",
        ))

        # Return of egress width check across multiple occupants
        for (stair_in, occupants, expect_pass, desc) in [
            (44, 100, True,  "44-in stair width with 100 occupants -- compliant"),
            (36, 150, False, "36-in stair width with 150 occupants -- violation"),
            (60, 200, True,  "60-in stair width with 200 occupants -- compliant"),
        ]:
            min_required = max(occupants * 0.3, 44)
            stair_ft = stair_in * IN_TO_FT
            samples.append(_s(
                f"Validate IBC 1005.1 combined occupant load egress check: {desc}",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1005.1: Validate stair width for {occupants} occupants
// Required: max(0.3 in/occ, 44 in) = {min_required:.1f} in
// Provided: {stair_in} in
void ValidateStairWidthForOccupants(FamilyInstance stairInst)
{{
    int occupants     = {occupants};
    double stairW     = {stair_ft:.6f}; // {stair_in} in
    double calcMin    = {occupants * 0.3 * IN_TO_FT:.6f}; // {occupants * 0.3:.1f} in
    double absMin     = {44 * IN_TO_FT:.6f}; // 44 in
    double required   = Math.Max(calcMin, absMin); // {min_required:.1f} in

    if (stairW < required)
    {{
        TaskDialog.Show("IBC 1005.1 Violation",
            $"Stair width {{stairW * 12.0:F1}} in is insufficient for {{occupants}} occupants. "
            + $"Required: {{required * 12.0:F1}} in. "
            + "Ref: IBC 1005.1.");
    }}
}}""",
            ))

        # Egress balcony width (IBC 1021 -- exterior exit balcony)
        samples.append(_s(
            "Validate IBC 1021.1 exterior exit balcony minimum width (same as required egress width)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1021.1: Exterior exit balconies must have the same minimum width
// as the interior corridor or stair they serve
void ValidateExteriorExitBalcony(FamilyInstance balconyInst)
{{
    double absMinFt = {44 * IN_TO_FT:.6f}; // 44 in -- IBC 1021.1

    Parameter pWidth      = balconyInst.LookupParameter("Balcony Width");
    Parameter pServedWidth = balconyInst.LookupParameter("Served Egress Width");
    if (pWidth == null) return;

    double width    = pWidth.AsDouble();
    double served   = pServedWidth != null ? pServedWidth.AsDouble() : absMinFt;
    double required = Math.Max(served, absMinFt);

    if (width < required)
    {{
        TaskDialog.Show("IBC 1021.1 Violation",
            $"Exterior exit balcony width {{width * 12.0:F2}} in is less than required "
            + $"{{required * 12.0:F2}} in. "
            + "Ref: IBC 1021.1.");
    }}
}}""",
        ))

        # Egress capacity counter -- tabulate total egress width
        samples.append(_s(
            "Calculate and validate total egress capacity for a floor by summing all exit widths",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using System.Collections.Generic;
using System.Linq;

// IBC 1005.1: Total egress capacity must accommodate all occupants
// Verify sum of stair widths / 0.3 in + sum of other egress widths / 0.2 in >= occupant load
void ValidateTotalEgressCapacity(Document doc, int totalOccupants)
{
    // Collect all exit doors and stairs on this level
    var exits = new FilteredElementCollector(doc)
        .OfClass(typeof(FamilyInstance))
        .OfCategory(BuiltInCategory.OST_Doors)
        .Cast<FamilyInstance>()
        .Where(d => d.LookupParameter("Is Exit Door")?.AsInteger() == 1)
        .ToList();

    double stairCapacity = 0;
    double otherCapacity = 0;

    foreach (var exit in exits)
    {
        Parameter pW      = exit.LookupParameter("Clear Width");
        Parameter pIsStair = exit.LookupParameter("Serves Stair");
        if (pW == null) continue;

        double w = pW.AsDouble() * 12.0; // convert to inches
        if (pIsStair != null && pIsStair.AsInteger() == 1)
            stairCapacity += w / 0.3;
        else
            otherCapacity += w / 0.2;
    }

    double totalCapacity = stairCapacity + otherCapacity;
    if (totalCapacity < totalOccupants)
    {
        TaskDialog.Show("IBC 1005.1 Capacity Violation",
            $"Total egress capacity {totalCapacity:F0} is less than occupant load {totalOccupants}. "
            + "Ref: IBC 1005.1.");
    }
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # IBC 1010.1 -- Door dimensions
    # ------------------------------------------------------------------

    def _door_dimensions(self) -> List[SAMPLE]:
        samples = []

        # Minimum clear door width (32 in) and height (80 in)
        for (label, clear_w_in, height_in, code) in [
            ("standard egress door",    32, 80, "IBC 1010.1.1"),
            ("accessible door (ADA)",   32, 80, "IBC 1010.1.1 / ADA 404.2.3"),
            ("fire door assembly",      32, 80, "IBC 1010.1.1 / NFPA 80 S4.3"),
            ("hospital corridor door",  44, 80, "IBC 1010.1.1 (health care: 44 in min clear)"),
        ]:
            w_ft = clear_w_in * IN_TO_FT
            h_ft = height_in * IN_TO_FT
            samples.append(_s(
                f"Validate IBC 1010.1.1 minimum clear width and height for {label}",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// {code}: {label}
// Min clear width: {clear_w_in} in ({w_ft:.6f} ft)
// Min height:      {height_in} in ({h_ft:.6f} ft)
void ValidateDoorDimensions(FamilyInstance doorInst)
{{
    double minClearWidthFt = {w_ft:.6f}; // {clear_w_in} in clear
    double minHeightFt     = {h_ft:.6f}; // {height_in} in

    Parameter pClearW  = doorInst.LookupParameter("Clear Width");
    Parameter pHeight  = doorInst.LookupParameter("Door Height");

    if (pClearW != null)
    {{
        double clearW = pClearW.AsDouble();
        if (clearW < minClearWidthFt)
        {{
            TaskDialog.Show("{code} Violation",
                $"Clear door width {{clearW * 12.0:F2}} in is less than required "
                + $"{clear_w_in} in for {label}. "
                + "Ref: {code}.");
        }}
    }}

    if (pHeight != null)
    {{
        double ht = pHeight.AsDouble();
        if (ht < minHeightFt)
        {{
            TaskDialog.Show("{code} Violation",
                $"Door height {{ht * 12.0:F2}} in is less than required {height_in} in. "
                + "Ref: {code}.");
        }}
    }}
}}""",
            ))

        # Door swing clearance (IBC 1010.1.1.1 -- maneuvering clearance)
        for (side, req_in, desc) in [
            ("latch", 12, "latch-side maneuvering clearance (pull side)"),
            ("hinge", 0,  "hinge-side clearance (no minimum unless ADA)"),
            ("ADA latch pull", 18, "ADA 404.2.4 latch-side clearance pull side"),
            ("ADA latch push", 12, "ADA 404.2.4 latch-side clearance push side"),
        ]:
            if req_in == 0:
                continue
            req_ft = req_in * IN_TO_FT
            samples.append(_s(
                f"Validate door {desc} per IBC 1010.1 / ADA 404.2.4",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 404.2.4 / IBC 1010.1: {desc}
// Required: {req_in} in ({req_ft:.6f} ft) on the {side} side
void ValidateDoorManeuvering_{side.replace(' ', '_')}(FamilyInstance doorInst)
{{
    double minClearFt = {req_ft:.6f}; // {req_in} in

    Parameter pClear = doorInst.LookupParameter("{side.title()} Side Clearance");
    if (pClear == null) return;

    double actual = pClear.AsDouble();
    if (actual < minClearFt)
    {{
        TaskDialog.Show("ADA 404.2.4 / IBC 1010.1 Violation",
            $"{side.title()} side clearance {{actual * 12.0:F2}} in is less than "
            + $"required {req_in} in. "
            + "Ref: ADA 404.2.4, IBC 1010.1.");
    }}
}}""",
            ))

        # Door opening force (IBC 1010.1.3 -- max 5 lbf interior, 15 lbf exterior)
        samples.append(_s(
            "Validate IBC 1010.1.3 maximum door opening force (5 lbf interior, 15 lbf exterior)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1010.1.3: Maximum door-opening force
// Interior swinging doors (other than fire doors): 5 lbf
// Exterior doors: 15 lbf
void ValidateDoorOpeningForce(FamilyInstance doorInst)
{
    Parameter pForce    = doorInst.LookupParameter("Opening Force (lbf)");
    Parameter pExterior = doorInst.LookupParameter("Is Exterior");
    if (pForce == null) return;

    double force       = pForce.AsDouble();
    bool isExterior    = pExterior != null && pExterior.AsInteger() == 1;
    double maxForce    = isExterior ? 15.0 : 5.0;

    if (force > maxForce)
    {
        TaskDialog.Show("IBC 1010.1.3 Violation",
            $"Door opening force {force:F1} lbf exceeds the {maxForce} lbf maximum "
            + $"for {(isExterior ? "exterior" : "interior")} doors. "
            + "Ref: IBC 1010.1.3.");
    }
}""",
        ))

        # Threshold height (IBC 1010.1.8 -- 0.5 in max, 0.25 in if accessible)
        samples.append(_s(
            "Validate IBC 1010.1.8 maximum door threshold height (0.5 in standard, 0.25 in accessible)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1010.1.8: Door threshold height
// Standard: 0.5 in max ({0.5 * IN_TO_FT:.6f} ft)
// Accessible route: 0.25 in max ({0.25 * IN_TO_FT:.6f} ft) -- ADA 404.2.5
void ValidateThresholdHeight(FamilyInstance doorInst)
{{
    double maxStdFt    = {0.5  * IN_TO_FT:.6f}; // 0.5 in
    double maxAccessFt = {0.25 * IN_TO_FT:.6f}; // 0.25 in accessible

    Parameter pThresh  = doorInst.LookupParameter("Threshold Height");
    Parameter pAccess  = doorInst.LookupParameter("On Accessible Route");
    if (pThresh == null) return;

    double thresh    = pThresh.AsDouble();
    bool accessible  = pAccess != null && pAccess.AsInteger() == 1;
    double limit     = accessible ? maxAccessFt : maxStdFt;

    if (thresh > limit)
    {{
        TaskDialog.Show("IBC 1010.1.8 Violation",
            $"Threshold height {{thresh * 12.0:F3}} in exceeds the {{limit * 12.0:F3}} in maximum "
            + $"(accessible route: {{accessible}}). "
            + "Ref: IBC 1010.1.8 / ADA 404.2.5.");
    }}
}}""",
        ))

        # Door hardware height (ADA 404.2.7 -- 34-48 in above floor)
        samples.append(_s(
            "Validate ADA 404.2.7 door hardware height (34 in minimum, 48 in maximum above finish floor)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 404.2.7: Door hardware operable parts height
// Must be between 34 in and 48 in above finish floor
void ValidateDoorHardwareHeight(FamilyInstance doorInst)
{{
    double minHtFt = {34 * IN_TO_FT:.6f}; // 34 in AFF
    double maxHtFt = {48 * IN_TO_FT:.6f}; // 48 in AFF

    Parameter pHardwareHt = doorInst.LookupParameter("Hardware Height");
    if (pHardwareHt == null) return;

    double ht = pHardwareHt.AsDouble();
    if (ht < minHtFt || ht > maxHtFt)
    {{
        TaskDialog.Show("ADA 404.2.7 Violation",
            $"Door hardware height {{ht * 12.0:F2}} in AFF is outside the "
            + $"34 in - 48 in required range. "
            + "Ref: ADA 404.2.7.");
    }}
}}""",
        ))

        # Double-door coordination (clear width applies to each leaf)
        samples.append(_s(
            "Validate IBC 1010.1.1 clear width for double-leaf doors -- each active leaf must meet minimum",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1010.1.1: For double-leaf doors, the active leaf must provide
// minimum 32 in clear width on its own
void ValidateDoubleLeafClearWidth(FamilyInstance doorInst)
{{
    double minClearFt = {32 * IN_TO_FT:.6f}; // 32 in clear

    Parameter pActiveLeafW = doorInst.LookupParameter("Active Leaf Clear Width");
    Parameter pIsDouble    = doorInst.LookupParameter("Is Double Leaf");
    if (pActiveLeafW == null || pIsDouble == null) return;

    bool isDouble = pIsDouble.AsInteger() == 1;
    if (!isDouble) return;

    double activeW = pActiveLeafW.AsDouble();
    if (activeW < minClearFt)
    {{
        TaskDialog.Show("IBC 1010.1.1 Violation",
            $"Active leaf clear width {{activeW * 12.0:F2}} in is less than required "
            + "32 in for double-leaf doors. The active leaf alone must meet minimum. "
            + "Ref: IBC 1010.1.1.");
    }}
}}""",
        ))

        # Door check for corridors leading to exits (IBC 1020.2)
        samples.append(_s(
            "Validate IBC 1020.2 minimum door width for corridors that serve as exit access",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1020.2: Corridor doors must not obstruct required width
// Doors in corridors must have clear width >= required corridor exit access width
void ValidateCorridorDoorWidth(FamilyInstance doorInst)
{{
    double minCorridorFt = {44 * IN_TO_FT:.6f}; // 44 in IBC 1020.2 non-residential

    Parameter pClearW     = doorInst.LookupParameter("Clear Width");
    Parameter pInCorridor = doorInst.LookupParameter("In Exit Access Corridor");
    if (pClearW == null || pInCorridor == null) return;

    bool inCorridor = pInCorridor.AsInteger() == 1;
    if (!inCorridor) return;

    double clearW = pClearW.AsDouble();
    if (clearW < minCorridorFt)
    {{
        TaskDialog.Show("IBC 1020.2 Violation",
            $"Corridor door clear width {{clearW * 12.0:F2}} in is less than required "
            + "44 in for exit access corridor doors. "
            + "Ref: IBC 1020.2.");
    }}
}}""",
        ))

        # Door closer and check arm clearance (ADA 404.2.8 -- closer/latch on side nearest hinge)
        samples.append(_s(
            "Validate ADA 404.2.8 door closer compliance -- closing time at least 5 seconds from 90 degrees",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 404.2.8: Door closers on accessible doors must take >= 5 seconds
// to close from 90 degrees to a point 12 degrees from the latch
void ValidateDoorCloserSpeed(FamilyInstance doorInst)
{
    double minCloseSeconds = 5.0; // ADA 404.2.8

    Parameter pCloseTime = doorInst.LookupParameter("Door Closer Time (seconds)");
    Parameter pIsAccessible = doorInst.LookupParameter("On Accessible Route");
    if (pCloseTime == null || pIsAccessible == null) return;

    if (pIsAccessible.AsInteger() != 1) return;

    double closeTime = pCloseTime.AsDouble();
    if (closeTime < minCloseSeconds)
    {
        TaskDialog.Show("ADA 404.2.8 Violation",
            $"Door closer sweep time {closeTime:F1} seconds is less than required 5 seconds. "
            + "Ref: ADA 404.2.8.");
    }
}""",
        ))

        # Kick plate requirement for accessible doors (ADA 404.2.10 -- smooth surface 10 in from bottom)
        samples.append(_s(
            "Validate ADA 404.2.10 smooth surface requirement on bottom 10 in of accessible swinging doors",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 404.2.10: Swinging doors on accessible routes must have a smooth surface
// on the push side for the bottom 10 in of the door
void ValidateDoorKickPlate(FamilyInstance doorInst)
{{
    double kickPlateHeightFt = {10.0 * IN_TO_FT:.6f}; // 10 in -- ADA 404.2.10

    Parameter pIsAccessible  = doorInst.LookupParameter("On Accessible Route");
    Parameter pHasKickPlate  = doorInst.LookupParameter("Has Kick Plate");
    Parameter pKickPlateHt   = doorInst.LookupParameter("Kick Plate Height");
    if (pIsAccessible == null || pIsAccessible.AsInteger() != 1) return;

    bool hasKickPlate = pHasKickPlate != null && pHasKickPlate.AsInteger() == 1;
    if (!hasKickPlate)
    {{
        TaskDialog.Show("ADA 404.2.10 Violation",
            "Accessible door lacks smooth surface kick plate on push side. "
            + "Ref: ADA 404.2.10.");
        return;
    }}

    if (pKickPlateHt != null && pKickPlateHt.AsDouble() < kickPlateHeightFt)
    {{
        TaskDialog.Show("ADA 404.2.10 Violation",
            $"Kick plate height {{pKickPlateHt.AsDouble() * 12.0:F2}} in is less than required 10 in. "
            + "Ref: ADA 404.2.10.");
    }}
}}""",
        ))

        # Revolving door bypass (IBC 1010.1.1.1 -- adjacent accessible swinging door required)
        samples.append(_s(
            "Validate IBC 1010.1.1.1 revolving door compliance -- adjacent accessible swinging door required",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1010.1.1.1: Revolving doors must have an adjacent accessible swinging door
// that serves the same path of travel
void ValidateRevolvingDoorBypass(FamilyInstance revolvingDoorInst)
{
    Parameter pIsRevolving = revolvingDoorInst.LookupParameter("Is Revolving Door");
    Parameter pHasBypass   = revolvingDoorInst.LookupParameter("Has Adjacent Accessible Door");
    if (pIsRevolving == null || pIsRevolving.AsInteger() != 1) return;

    bool hasBypass = pHasBypass != null && pHasBypass.AsInteger() == 1;
    if (!hasBypass)
    {
        TaskDialog.Show("IBC 1010.1.1.1 Violation",
            "Revolving door must have an adjacent accessible swinging door. "
            + "Ref: IBC 1010.1.1.1.");
    }
}""",
        ))

        # Door vision panel (IBC 1010.1.2 -- hazardous locations require vision panel)
        samples.append(_s(
            "Validate IBC 1010.1.2 vision panel requirement for doors in hazardous locations",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1010.1.2: Doors in corridors and exit enclosures that swing toward egress travel
// shall have vision panels where they might conceal an approaching occupant
void ValidateDoorVisionPanel(FamilyInstance doorInst)
{
    Parameter pSwingDir      = doorInst.LookupParameter("Swing Direction");
    Parameter pInCorridor    = doorInst.LookupParameter("In Exit Corridor");
    Parameter pHasVisionPanel = doorInst.LookupParameter("Has Vision Panel");
    if (pSwingDir == null || pInCorridor == null) return;

    bool swingsToward = pSwingDir.AsString() == "Toward Egress";
    bool inCorridor   = pInCorridor.AsInteger() == 1;
    bool hasVision    = pHasVisionPanel != null && pHasVisionPanel.AsInteger() == 1;

    if (swingsToward && inCorridor && !hasVision)
    {
        TaskDialog.Show("IBC 1010.1.2 Violation",
            "Door swings toward egress travel in corridor and lacks required vision panel. "
            + "Ref: IBC 1010.1.2.");
    }
}""",
        ))

        # Max door leaf width (IBC 1010.1.1 -- 48 in max per leaf)
        samples.append(_s(
            "Validate IBC 1010.1.1 maximum single door leaf width (48 in)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1010.1.1: Maximum door leaf width is 48 in (single leaf)
void ValidateMaxDoorLeafWidth(FamilyInstance doorInst)
{{
    double maxLeafFt = {48 * IN_TO_FT:.6f}; // 48 in -- IBC 1010.1.1

    Parameter pLeafW = doorInst.LookupParameter("Door Leaf Width");
    if (pLeafW == null) return;

    double leafW = pLeafW.AsDouble();
    if (leafW > maxLeafFt)
    {{
        TaskDialog.Show("IBC 1010.1.1 Violation",
            $"Door leaf width {{leafW * 12.0:F2}} in exceeds 48 in maximum per leaf. "
            + "Ref: IBC 1010.1.1.");
    }}
}}""",
        ))

        # ADA 404.2.3.2 -- maneuvering clearance on approach side varies by swing/pull/push
        samples.append(_s(
            "Validate ADA 404.2.3.2 maneuvering clearance -- 60 in perpendicular depth on pull side",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 404.2.3.2: Forward approach, pull side: 60 in perpendicular clearance depth
// ADA 404.2.3.2: Forward approach, push side: 48 in perpendicular clearance depth
void ValidateManeuveringClearancePerpendicular(FamilyInstance doorInst)
{{
    double minPullDepthFt = {60 * IN_TO_FT:.6f}; // 60 in -- ADA 404.2.3.2
    double minPushDepthFt = {48 * IN_TO_FT:.6f}; // 48 in -- ADA 404.2.3.2

    Parameter pIsAccessible  = doorInst.LookupParameter("On Accessible Route");
    Parameter pApproachSide  = doorInst.LookupParameter("Approach Side");
    Parameter pPerpClearance = doorInst.LookupParameter("Perpendicular Maneuvering Clearance");
    if (pIsAccessible == null || pIsAccessible.AsInteger() != 1) return;
    if (pPerpClearance == null) return;

    string side   = pApproachSide != null ? pApproachSide.AsString() : "Pull";
    double limit  = side.Contains("Push") ? minPushDepthFt : minPullDepthFt;
    double actual = pPerpClearance.AsDouble();

    if (actual < limit)
    {{
        TaskDialog.Show("ADA 404.2.3.2 Violation",
            $"{{side}} side perpendicular maneuvering clearance {{actual * 12.0:F2}} in < required {{limit * 12.0:F2}} in. "
            + "Ref: ADA 404.2.3.2.");
    }}
}}""",
        ))

        # Sliding door operation force (ADA 309.4 -- 5 lbf max)
        samples.append(_s(
            "Validate ADA 309.4 operable part activation force for sliding doors (5 lbf maximum)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 309.4: Maximum force to operate sliding doors is 5 lbf
void ValidateSlidingDoorForce(FamilyInstance doorInst)
{
    Parameter pIsSliding    = doorInst.LookupParameter("Is Sliding Door");
    Parameter pOpForce      = doorInst.LookupParameter("Operating Force (lbf)");
    Parameter pIsAccessible = doorInst.LookupParameter("On Accessible Route");
    if (pIsSliding == null || pIsSliding.AsInteger() != 1) return;
    if (pIsAccessible == null || pIsAccessible.AsInteger() != 1) return;
    if (pOpForce == null) return;

    double force = pOpForce.AsDouble();
    if (force > 5.0)
    {
        TaskDialog.Show("ADA 309.4 Violation",
            $"Sliding door operating force {force:F1} lbf exceeds 5 lbf maximum. "
            + "Ref: ADA 309.4.");
    }
}""",
        ))

        # Door frame structural adequacy -- min 3x stud jack at openings (IRC R602.9)
        samples.append(_s(
            "Validate IRC R602.9 jack stud requirement at door openings (number of jacks by header span)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IRC R602.9 Table R602.9: Minimum jack studs supporting door headers
// Header span 0-3.5 ft: 1 jack, 3.5-7 ft: 2 jacks, > 7 ft: 3 jacks
void ValidateDoorHeaderJacks(FamilyInstance doorInst)
{
    Parameter pDoorWidth  = doorInst.LookupParameter("Rough Opening Width");
    Parameter pJackCount  = doorInst.LookupParameter("Jack Stud Count");
    if (pDoorWidth == null || pJackCount == null) return;

    double span   = pDoorWidth.AsDouble();
    int jacks     = (int)pJackCount.AsDouble();
    int required  = span <= 3.5 ? 1 : span <= 7.0 ? 2 : 3;

    if (jacks < required)
    {
        TaskDialog.Show("IRC R602.9 Violation",
            $"Door opening span {span:F2} ft requires {required} jack studs; {jacks} provided. "
            + "Ref: IRC R602.9 Table R602.9.");
    }
}""",
        ))

        # Door sill height at exterior (IBC 1013 / flashing requirements)
        samples.append(_s(
            "Validate IBC / flashing best practice minimum exterior door sill height above grade (4 in)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// Best practice / IBC 1404.4: Exterior door sill should be minimum 4 in above finished grade
// to prevent water infiltration; many codes require 6 in for masonry openings
void ValidateExteriorDoorSillHeight(FamilyInstance doorInst)
{{
    double minSillFt = {4 * IN_TO_FT:.6f}; // 4 in above grade -- IBC 1404.4

    Parameter pIsExterior = doorInst.LookupParameter("Is Exterior");
    Parameter pSillHeight = doorInst.LookupParameter("Sill Height Above Grade");
    if (pIsExterior == null || pIsExterior.AsInteger() != 1) return;

    if (pSillHeight != null && pSillHeight.AsDouble() < minSillFt)
    {{
        TaskDialog.Show("IBC 1404.4 Warning",
            $"Exterior door sill {{pSillHeight.AsDouble() * 12.0:F2}} in above grade < 4 in minimum. "
            + "Ref: IBC 1404.4 / ASTM E2112.");
    }}
}}""",
        ))

        # Vestibule dimensions for energy code (IECC C402.5.7 -- 7 ft min between doors)
        samples.append(_s(
            "Validate IECC C402.5.7 vestibule minimum distance between inner and outer doors (7 ft)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IECC C402.5.7: Vestibules required for climate zones 3-8
// Minimum 7 ft between the inner and outer door swings (measured at midpoint)
void ValidateVestibuleDimensions(FamilyInstance vestibuleInst)
{
    double minDoorSepFt = 7.0; // 7 ft -- IECC C402.5.7

    Parameter pIsVestibule = vestibuleInst.LookupParameter("Is Vestibule");
    Parameter pDoorSep     = vestibuleInst.LookupParameter("Inner-Outer Door Separation");
    if (pIsVestibule == null || pIsVestibule.AsInteger() != 1) return;

    if (pDoorSep != null && pDoorSep.AsDouble() < minDoorSepFt)
    {
        TaskDialog.Show("IECC C402.5.7 Violation",
            $"Vestibule door separation {pDoorSep.AsDouble():F2} ft < 7 ft minimum. "
            + "Ref: IECC C402.5.7.");
    }
}""",
        ))

        # Door rough opening width (typical -- nominal width + 2 in each side)
        samples.append(_s(
            "Validate standard door rough opening width (nominal door width + 2 in each side + 1/2 in shimming)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// Standard framing practice: Rough opening = door width + 2 in (frame) + 0.5 in (shim) each side
// RO width = nominal + 2.5 in (total)
void ValidateDoorRoughOpening(FamilyInstance doorInst)
{{
    double frameAdder = {2.5 * IN_TO_FT:.6f}; // 2.5 in each side total -- standard practice

    Parameter pNominal = doorInst.LookupParameter("Door Width");
    Parameter pRO      = doorInst.LookupParameter("Rough Opening Width");
    if (pNominal == null || pRO == null) return;

    double nominal  = pNominal.AsDouble();
    double ro       = pRO.AsDouble();
    double expected = nominal + frameAdder;

    // Allow +/- 1/4 in tolerance
    double tol = {0.25 * IN_TO_FT:.6f};
    if (Math.Abs(ro - expected) > tol)
    {{
        TaskDialog.Show("Rough Opening Warning",
            $"Rough opening {{ro * 12.0:F3}} in differs from expected {{expected * 12.0:F3}} in "
            + $"(nominal {{nominal * 12.0:F2}} in + 2.5 in). Verify framing dimensions.");
    }}
}}""",
        ))

        # Sliding glass door clear width (ADA 404.2.3 -- same 32 in min as swinging)
        samples.append(_s(
            "Validate ADA 404.2.3 sliding glass door minimum clear width (32 in) and operating hardware",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 404.2.3: Sliding doors must have 32 in min clear width
// Hardware: must be operable with one hand, not require tight grasping, pinching, or twisting
void ValidateSlidingGlassDoorClearWidth(FamilyInstance doorInst)
{{
    double minClearFt = {32 * IN_TO_FT:.6f}; // 32 in -- ADA 404.2.3

    Parameter pIsSliding    = doorInst.LookupParameter("Is Sliding Door");
    Parameter pIsAccessible = doorInst.LookupParameter("On Accessible Route");
    Parameter pClearW       = doorInst.LookupParameter("Clear Width");
    Parameter pHardwareType = doorInst.LookupParameter("Hardware Type");
    if (pIsSliding == null || pIsSliding.AsInteger() != 1) return;
    if (pIsAccessible == null || pIsAccessible.AsInteger() != 1) return;

    if (pClearW != null && pClearW.AsDouble() < minClearFt)
    {{
        TaskDialog.Show("ADA 404.2.3 Violation",
            $"Sliding door clear width {{pClearW.AsDouble() * 12.0:F2}} in < 32 in minimum. "
            + "Ref: ADA 404.2.3.");
    }}

    if (pHardwareType != null)
    {{
        string hw = pHardwareType.AsString();
        if (hw == "Round Knob" || hw == "Thumb Turn")
        {{
            TaskDialog.Show("ADA 309.4 Violation",
                $"Hardware type '{{hw}}' requires tight grasping/twisting and is not ADA compliant. "
                + "Use lever, loop, or push-pull hardware. Ref: ADA 309.4.");
        }}
    }}
}}""",
        ))

        # Exterior door wind load (ASCE 7 -- pressure design for glazing)
        samples.append(_s(
            "Validate ASCE 7-22 exterior door glazing design pressure for wind load resistance",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ASCE 7-22: Glazing in exterior doors must be designed for components & cladding wind pressure
// Minimum design pressure varies by zone; check that glazing unit rating >= calculated pressure
void ValidateDoorGlazingWindPressure(FamilyInstance doorInst)
{
    Parameter pDesignPressure = doorInst.LookupParameter("Design Wind Pressure (psf)");
    Parameter pGlazingRating  = doorInst.LookupParameter("Glazing Design Pressure (psf)");
    Parameter pIsExterior     = doorInst.LookupParameter("Is Exterior");
    if (pIsExterior == null || pIsExterior.AsInteger() != 1) return;
    if (pDesignPressure == null || pGlazingRating == null) return;

    double design = pDesignPressure.AsDouble();
    double rating = pGlazingRating.AsDouble();

    if (rating < design)
    {
        TaskDialog.Show("ASCE 7-22 Violation",
            $"Glazing design pressure rating {rating:F1} psf < required {design:F1} psf. "
            + "Ref: ASCE 7-22 Chapter 30 (Components and Cladding).");
    }
}""",
        ))

        # Fire door self-closing device (NFPA 80 S4.5 -- must be self-closing)
        samples.append(_s(
            "Validate NFPA 80 S4.5 fire door self-closing device requirement",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// NFPA 80 S4.5: Fire door assemblies must be equipped with a self-closing device
// The door must close and latch automatically when released from any open position
void ValidateFireDoorSelfClosing(FamilyInstance doorInst)
{
    Parameter pIsFireDoor     = doorInst.LookupParameter("Is Fire Door");
    Parameter pHasSelfCloser  = doorInst.LookupParameter("Has Self-Closing Device");
    Parameter pIsHoldOpen     = doorInst.LookupParameter("Has Hold-Open Device");
    Parameter pHasMagRelease  = doorInst.LookupParameter("Magnetic Release on Fire Alarm");
    if (pIsFireDoor == null || pIsFireDoor.AsInteger() != 1) return;

    bool hasSelfCloser = pHasSelfCloser != null && pHasSelfCloser.AsInteger() == 1;
    if (!hasSelfCloser)
    {
        TaskDialog.Show("NFPA 80 S4.5 Violation",
            "Fire door does not have a self-closing device. "
            + "Ref: NFPA 80 S4.5.");
    }

    // Hold-open devices permitted ONLY with magnetic release tied to fire alarm (NFPA 80 S4.7.3)
    bool isHoldOpen = pIsHoldOpen != null && pIsHoldOpen.AsInteger() == 1;
    bool hasMagRelease = pHasMagRelease != null && pHasMagRelease.AsInteger() == 1;
    if (isHoldOpen && !hasMagRelease)
    {
        TaskDialog.Show("NFPA 80 S4.7.3 Violation",
            "Fire door hold-open device must release automatically upon fire alarm signal. "
            + "Ref: NFPA 80 S4.7.3.");
    }
}""",
        ))

        # Door undercut -- accessible air transfer
        samples.append(_s(
            "Validate ASHRAE 62.2 door undercut or transfer grille for room air circulation (3/4 in undercut typical)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ASHRAE 62.2 / IMC 601: Interior doors require air transfer path
// Typical undercut 3/4 in or transfer grille to allow return air circulation
void ValidateDoorAirTransfer(FamilyInstance doorInst)
{{
    double minUndercutFt = {0.75 * IN_TO_FT:.6f}; // 3/4 in undercut typical

    Parameter pUndercut     = doorInst.LookupParameter("Door Undercut");
    Parameter pHasTransfer  = doorInst.LookupParameter("Has Transfer Grille");
    Parameter pIsInterior   = doorInst.LookupParameter("Is Interior Door");
    if (pIsInterior == null || pIsInterior.AsInteger() != 1) return;

    bool hasTransfer = pHasTransfer != null && pHasTransfer.AsInteger() == 1;
    if (hasTransfer) return; // Transfer grille satisfies requirement

    if (pUndercut != null && pUndercut.AsDouble() < minUndercutFt)
    {{
        TaskDialog.Show("ASHRAE 62.2 Warning",
            $"Door undercut {{pUndercut.AsDouble() * 12.0:F3}} in < 3/4 in recommended for air transfer. "
            + "Ref: ASHRAE 62.2 / IMC 601.");
    }}
}}""",
        ))

        # Panic hardware -- required when > 50 occupants in assembly (IBC 1010.1.10)
        samples.append(_s(
            "Validate IBC 1010.1.10 panic hardware requirement for assembly exit doors serving > 50 occupants",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1010.1.10: Panic hardware required on exit doors in A, E occupancies
// when occupant load > 50 and door is used as a means of egress
void ValidatePanicHardware(FamilyInstance doorInst)
{
    Parameter pOccupancy  = doorInst.LookupParameter("Room Occupancy Group");
    Parameter pOccupants  = doorInst.LookupParameter("Served Occupant Load");
    Parameter pHasPanic   = doorInst.LookupParameter("Has Panic Hardware");
    Parameter pIsExit     = doorInst.LookupParameter("Is Exit Door");
    if (pOccupancy == null || pIsExit == null || pIsExit.AsInteger() != 1) return;

    string occ = pOccupancy.AsString();
    double occupants = pOccupants != null ? pOccupants.AsDouble() : 0;
    bool hasPanic    = pHasPanic != null && pHasPanic.AsInteger() == 1;

    bool required = (occ.StartsWith("A") || occ == "E") && occupants > 50;
    if (required && !hasPanic)
    {
        TaskDialog.Show("IBC 1010.1.10 Violation",
            $"Exit door in {occ} occupancy with {occupants:F0} occupants requires panic hardware. "
            + "Ref: IBC 1010.1.10.");
    }
}""",
        ))

        # Automatic door opener accessibility (ADA 404.3 -- power-assisted or low-energy)
        samples.append(_s(
            "Validate ADA 404.3 automatic door opener requirements for high-traffic accessible entrances",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 404.3: Power-operated doors are permitted and must comply with ANSI/BHMA A156.19
// Required where opening force > 5 lbf on accessible routes in some jurisdictions
void ValidateAutomaticDoorOpener(FamilyInstance doorInst)
{
    Parameter pIsAuto      = doorInst.LookupParameter("Is Automatic Door");
    Parameter pANSIClass   = doorInst.LookupParameter("ANSI/BHMA Class");
    Parameter pIsAccessible = doorInst.LookupParameter("On Accessible Route");
    if (pIsAuto == null || pIsAuto.AsInteger() != 1) return;

    // Verify automatic doors comply with ANSI/BHMA A156.19
    if (pANSIClass != null)
    {
        string cls = pANSIClass.AsString();
        if (cls != "A156.19")
        {
            TaskDialog.Show("ADA 404.3 Warning",
                $"Automatic door ANSI class '{cls}' should comply with ANSI/BHMA A156.19 on accessible routes. "
                + "Ref: ADA 404.3.");
        }
    }
}""",
        ))

        # Balanced door / electromagnetic hold-open (IBC 1010.1.9 -- no lock in direction of egress)
        samples.append(_s(
            "Validate IBC 1010.1.9 egress door hardware -- no lock or latch requiring key, tool, or special knowledge in direction of egress",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1010.1.9: Egress doors must be openable from the egress side
// without use of a key, tool, or special knowledge
void ValidateEgressDoorLockability(FamilyInstance doorInst)
{
    Parameter pIsExit       = doorInst.LookupParameter("Is Exit Door");
    Parameter pLockType     = doorInst.LookupParameter("Lock Type");
    Parameter pRequiresKey  = doorInst.LookupParameter("Requires Key to Exit");
    if (pIsExit == null || pIsExit.AsInteger() != 1) return;

    bool requiresKey = pRequiresKey != null && pRequiresKey.AsInteger() == 1;
    if (requiresKey)
    {
        TaskDialog.Show("IBC 1010.1.9 Violation",
            "Exit door requires key to open from the egress side, which is not permitted. "
            + "Ref: IBC 1010.1.9.");
    }

    if (pLockType != null)
    {
        string lockType = pLockType.AsString();
        if (lockType == "Deadbolt" || lockType == "Padlock")
        {
            TaskDialog.Show("IBC 1010.1.9 Violation",
                $"Lock type '{lockType}' on exit door is not permitted without special exception. "
                + "Ref: IBC 1010.1.9.");
        }
    }
}""",
        ))

        # Screen door -- must not impede egress from exit doors (IBC 1010.1)
        samples.append(_s(
            "Validate IBC 1010.1 screen/storm door does not reduce required clear width of exit door",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1010.1: When screen/storm doors are installed, the combined clear width
// of the egress door + screen door must still meet minimum requirements
void ValidateScreenDoorClearWidth(FamilyInstance doorInst)
{{
    double minClearFt = {32 * IN_TO_FT:.6f}; // 32 in -- IBC 1010.1.1

    Parameter pHasScreen  = doorInst.LookupParameter("Has Screen Door");
    Parameter pEgressW    = doorInst.LookupParameter("Clear Width");
    Parameter pScreenW    = doorInst.LookupParameter("Screen Door Clear Width");
    if (pHasScreen == null || pHasScreen.AsInteger() != 1) return;

    double exitClear   = pEgressW    != null ? pEgressW.AsDouble()    : 0;
    double screenClear = pScreenW    != null ? pScreenW.AsDouble()    : 0;
    double minClear    = Math.Min(exitClear, screenClear > 0 ? screenClear : exitClear);

    if (minClear < minClearFt)
    {{
        TaskDialog.Show("IBC 1010.1 Violation",
            $"Screen door reduces clear egress width to {{minClear * 12.0:F2}} in, below 32 in minimum. "
            + "Ref: IBC 1010.1.1.");
    }}
}}""",
        ))

        # Door swing clearance in accessible toilet room (ADA 603.2.3)
        samples.append(_s(
            "Validate ADA 603.2.3 toilet room door swing -- door must not swing into required fixture clearance",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 603.2.3: Doors in toilet rooms cannot swing into required floor clearances
// of fixtures unless the door is outswing or sliding
void ValidateToiletRoomDoorSwing(FamilyInstance doorInst)
{{
    Parameter pIsToiletRoom = doorInst.LookupParameter("In Accessible Toilet Room");
    Parameter pSwingDir     = doorInst.LookupParameter("Swing Direction");
    Parameter pSwingIntoClr = doorInst.LookupParameter("Swings Into Fixture Clearance");
    if (pIsToiletRoom == null || pIsToiletRoom.AsInteger() != 1) return;

    bool swingsInto = pSwingIntoClr != null && pSwingIntoClr.AsInteger() == 1;
    if (swingsInto)
    {{
        string swing = pSwingDir != null ? pSwingDir.AsString() : "inswing";
        if (swing != "Outswing" && swing != "Sliding")
        {{
            TaskDialog.Show("ADA 603.2.3 Violation",
                "Accessible toilet room door swings into required fixture clearance. "
                + "Use outswing or sliding door. "
                + "Ref: ADA 603.2.3.");
        }}
    }}
}}""",
        ))

        # Fire door frame rating (NFPA 80 S5.2 -- frame and hardware must match door rating)
        samples.append(_s(
            "Validate NFPA 80 S5.2 fire door frame listing -- frame must be listed for same rating as door",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// NFPA 80 S5.2: Fire door assemblies (door + frame + hardware) must all be listed
// for the same or greater fire rating
void ValidateFireDoorFrameRating(FamilyInstance doorInst)
{
    Parameter pIsFireDoor  = doorInst.LookupParameter("Is Fire Door");
    Parameter pDoorRating  = doorInst.LookupParameter("Fire Rating (hr)");
    Parameter pFrameRating = doorInst.LookupParameter("Frame Fire Rating (hr)");
    Parameter pFrameListed = doorInst.LookupParameter("Frame Is Listed");
    if (pIsFireDoor == null || pIsFireDoor.AsInteger() != 1) return;

    if (pFrameListed != null && pFrameListed.AsInteger() != 1)
    {
        TaskDialog.Show("NFPA 80 S5.2 Violation",
            "Fire door frame is not listed for fire resistance. "
            + "Ref: NFPA 80 S5.2.");
    }

    if (pDoorRating != null && pFrameRating != null)
    {
        if (pFrameRating.AsDouble() < pDoorRating.AsDouble())
        {
            TaskDialog.Show("NFPA 80 S5.2 Violation",
                $"Frame fire rating {pFrameRating.AsDouble()} hr < door rating {pDoorRating.AsDouble()} hr. "
                + "Ref: NFPA 80 S5.2.");
        }
    }
}""",
        ))

        # Occupancy separation rating per IBC Table 508.4
        samples.append(_s(
            "Validate IBC Table 508.4 occupancy separation fire-resistance rating between adjacent occupancies",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC Table 508.4: Required fire-resistance rating between mixed occupancies
// Common case: A/B vs S-1 storage = 1 hr (non-sprinklered), NS = 2 hr
void ValidateOccupancySeparation(FamilyInstance wallInst)
{
    Parameter pOcc1    = wallInst.LookupParameter("Occupancy Type Side A");
    Parameter pOcc2    = wallInst.LookupParameter("Occupancy Type Side B");
    Parameter pRating  = wallInst.LookupParameter("Fire Rating (hr)");
    Parameter pSpr     = wallInst.LookupParameter("Sprinkler System");
    if (pOcc1 == null || pOcc2 == null || pRating == null) return;

    string occ1 = pOcc1.AsString();
    string occ2 = pOcc2.AsString();
    bool spr    = pSpr != null && pSpr.AsInteger() == 1;
    double actual = pRating.AsDouble();

    // Simplified: H (high-hazard) adjacent to other always requires 2-hr
    double required = 1.0; // Default 1-hr
    if (occ1.StartsWith("H") || occ2.StartsWith("H")) required = 2.0;
    if (!spr && (occ1.StartsWith("S") || occ2.StartsWith("S"))) required = 2.0;

    if (actual < required)
    {
        TaskDialog.Show("IBC Table 508.4 Violation",
            $"Occupancy separation between {occ1} and {occ2} requires {required} hr rating; "
            + $"provided {actual} hr. "
            + "Ref: IBC Table 508.4.");
    }
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # IBC 1011 -- Stair geometry
    # ------------------------------------------------------------------

    def _stair_geometry(self) -> List[SAMPLE]:
        samples = []

        # Riser height: 4 in min, 7 in max (IBC 1011.5.2)
        for (riser_in, expect_violation, scenario) in [
            (4.0, False, "minimum riser 4 in (compliant)"),
            (7.0, False, "maximum riser 7 in (compliant)"),
            (7.5, True,  "riser 7.5 in (violation)"),
            (3.5, True,  "riser 3.5 in below minimum (violation)"),
            (6.0, False, "typical riser 6 in (compliant)"),
        ]:
            riser_ft = riser_in * IN_TO_FT
            samples.append(_s(
                f"Validate IBC 1011.5.2 stair riser height: {scenario}",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1011.5.2: Riser height 4 in min, 7 in max
// Scenario: {scenario}
void ValidateRiserHeight(FamilyInstance stairInst)
{{
    double minRiserFt = {4.0 * IN_TO_FT:.6f}; // 4 in minimum -- IBC 1011.5.2
    double maxRiserFt = {7.0 * IN_TO_FT:.6f}; // 7 in maximum -- IBC 1011.5.2

    Parameter pRiser = stairInst.LookupParameter("Riser Height");
    if (pRiser == null) return;

    double riser = pRiser.AsDouble(); // {riser_ft:.6f} ft = {riser_in} in
    List<string> violations = new List<string>();

    if (riser > maxRiserFt)
        violations.Add($"Riser {{riser * 12.0:F2}} in exceeds 7 in maximum (IBC 1011.5.2).");
    if (riser < minRiserFt)
        violations.Add($"Riser {{riser * 12.0:F2}} in is below 4 in minimum (IBC 1011.5.2).");

    if (violations.Count > 0)
        TaskDialog.Show("IBC 1011.5.2 Violation", string.Join("\\n", violations));
}}""",
            ))

        # Tread depth: 11 in min (IBC 1011.5.2)
        for (tread_in, desc) in [
            (11.0, "minimum tread 11 in (compliant)"),
            (12.0, "standard tread 12 in (compliant)"),
            (10.0, "tread 10 in (violation)"),
        ]:
            tread_ft = tread_in * IN_TO_FT
            samples.append(_s(
                f"Validate IBC 1011.5.2 stair tread depth: {desc}",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1011.5.2: Tread depth minimum 11 in
void ValidateTreadDepth(FamilyInstance stairInst)
{{
    double minTreadFt = {11.0 * IN_TO_FT:.6f}; // 11 in minimum -- IBC 1011.5.2

    Parameter pTread = stairInst.LookupParameter("Tread Depth");
    if (pTread == null) return;

    double tread = pTread.AsDouble(); // {tread_ft:.6f} ft = {tread_in} in
    if (tread < minTreadFt)
    {{
        TaskDialog.Show("IBC 1011.5.2 Violation",
            $"Tread depth {{tread * 12.0:F2}} in is less than required 11 in minimum. "
            + "Ref: IBC 1011.5.2.");
    }}
}}""",
            ))

        # Stair headroom: 6 ft 8 in min (IBC 1011.3)
        headroom_min_ft = (6 * 12 + 8) * IN_TO_FT  # 80 in
        for (headroom_in, desc) in [
            (80, "minimum headroom 80 in (compliant)"),
            (84, "standard headroom 84 in (compliant)"),
            (78, "headroom 78 in (violation)"),
        ]:
            h_ft = headroom_in * IN_TO_FT
            samples.append(_s(
                f"Validate IBC 1011.3 stair headroom clearance: {desc}",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1011.3: Minimum headroom clearance 6 ft 8 in (80 in) measured vertically
// from the sloped plane of the stair nosing
void ValidateStairHeadroom(FamilyInstance stairInst)
{{
    double minHeadroomFt = {headroom_min_ft:.6f}; // 80 in = 6 ft 8 in -- IBC 1011.3

    Parameter pHeadroom = stairInst.LookupParameter("Headroom Clearance");
    if (pHeadroom == null) return;

    double headroom = pHeadroom.AsDouble(); // {h_ft:.6f} ft = {headroom_in} in
    if (headroom < minHeadroomFt)
    {{
        TaskDialog.Show("IBC 1011.3 Violation",
            $"Stair headroom {{headroom * 12.0:F2}} in is less than required 80 in (6 ft 8 in). "
            + "Ref: IBC 1011.3.");
    }}
}}""",
            ))

        # Riser/tread uniformity: max 3/8 in variation within a flight (IBC 1011.5.4)
        samples.append(_s(
            "Validate IBC 1011.5.4 stair riser and tread uniformity (max 3/8 in variation in a flight)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using System.Collections.Generic;
using System.Linq;

// IBC 1011.5.4: Max variation in riser height or tread depth within a flight = 3/8 in
void ValidateStairUniformity(FamilyInstance stairInst)
{{
    double maxVariationFt = {0.375 * IN_TO_FT:.6f}; // 3/8 in -- IBC 1011.5.4

    Parameter pMaxRiser = stairInst.LookupParameter("Max Riser Height");
    Parameter pMinRiser = stairInst.LookupParameter("Min Riser Height");
    Parameter pMaxTread = stairInst.LookupParameter("Max Tread Depth");
    Parameter pMinTread = stairInst.LookupParameter("Min Tread Depth");

    if (pMaxRiser != null && pMinRiser != null)
    {{
        double variation = pMaxRiser.AsDouble() - pMinRiser.AsDouble();
        if (variation > maxVariationFt)
        {{
            TaskDialog.Show("IBC 1011.5.4 Violation",
                $"Riser height variation {{variation * 12.0:F3}} in exceeds 3/8 in max. "
                + "Ref: IBC 1011.5.4.");
        }}
    }}

    if (pMaxTread != null && pMinTread != null)
    {{
        double variation = pMaxTread.AsDouble() - pMinTread.AsDouble();
        if (variation > maxVariationFt)
        {{
            TaskDialog.Show("IBC 1011.5.4 Violation",
                $"Tread depth variation {{variation * 12.0:F3}} in exceeds 3/8 in max. "
                + "Ref: IBC 1011.5.4.");
        }}
    }}
}}""",
        ))

        # Stair landing depth (IBC 1011.6 -- min = stair width, max 48 in door swing OK)
        samples.append(_s(
            "Validate IBC 1011.6 stair landing depth equals or exceeds stair width",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1011.6: Landing depth >= stair width (min 44 in for egress stairs)
void ValidateStairLandingDepth(FamilyInstance stairInst)
{{
    double absMinFt = {44 * IN_TO_FT:.6f}; // 44 in absolute minimum

    Parameter pStairW   = stairInst.LookupParameter("Stair Width");
    Parameter pLandingD = stairInst.LookupParameter("Landing Depth");
    if (pStairW == null || pLandingD == null) return;

    double stairW   = pStairW.AsDouble();
    double landingD = pLandingD.AsDouble();
    double required = Math.Max(stairW, absMinFt);

    if (landingD < required)
    {{
        TaskDialog.Show("IBC 1011.6 Violation",
            $"Landing depth {{landingD * 12.0:F2}} in is less than required "
            + $"{{required * 12.0:F2}} in (must equal stair width, min 44 in). "
            + "Ref: IBC 1011.6.");
    }}
}}""",
        ))

        # Handrail height (IBC 1011.11 -- 34-38 in above stair nosing)
        samples.append(_s(
            "Validate IBC 1011.11 handrail height above stair nosing (34 in min, 38 in max)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1011.11: Handrail height 34 in to 38 in above stair nosing
void ValidateHandrailHeight(FamilyInstance stairInst)
{{
    double minHrFt = {34 * IN_TO_FT:.6f}; // 34 in -- IBC 1011.11
    double maxHrFt = {38 * IN_TO_FT:.6f}; // 38 in -- IBC 1011.11

    Parameter pHrHt = stairInst.LookupParameter("Handrail Height");
    if (pHrHt == null) return;

    double ht = pHrHt.AsDouble();
    if (ht < minHrFt || ht > maxHrFt)
    {{
        TaskDialog.Show("IBC 1011.11 Violation",
            $"Handrail height {{ht * 12.0:F2}} in is outside required range of 34-38 in. "
            + "Ref: IBC 1011.11.");
    }}
}}""",
        ))

        # Stair width including handrail intrusion (IBC 1011.2 -- handrail may project 4.5 in each side)
        samples.append(_s(
            "Validate IBC 1011.2 net stair width accounting for handrail projection (4.5 in each side)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1011.2: Handrail may project 4.5 in max on each side into required stair width
// Net clear width = stair width - handrail projections
void ValidateNetStairWidth(FamilyInstance stairInst)
{{
    double minNetFt       = {44 * IN_TO_FT:.6f}; // 44 in net minimum
    double maxHrProjectFt = {4.5 * IN_TO_FT:.6f}; // 4.5 in per side -- IBC 1011.2

    Parameter pStairW   = stairInst.LookupParameter("Stair Width");
    Parameter pHrLeft   = stairInst.LookupParameter("Left Handrail Projection");
    Parameter pHrRight  = stairInst.LookupParameter("Right Handrail Projection");
    if (pStairW == null) return;

    double stairW     = pStairW.AsDouble();
    double hrLeft     = pHrLeft  != null ? Math.Min(pHrLeft.AsDouble(),  maxHrProjectFt) : 0.0;
    double hrRight    = pHrRight != null ? Math.Min(pHrRight.AsDouble(), maxHrProjectFt) : 0.0;
    double netWidth   = stairW - hrLeft - hrRight;

    if (netWidth < minNetFt)
    {{
        TaskDialog.Show("IBC 1011.2 Violation",
            $"Net stair width {{netWidth * 12.0:F2}} in (after handrail projections) "
            + "is less than required 44 in. "
            + "Ref: IBC 1011.2.");
    }}
}}""",
        ))

        # Stair slope angle (IBC 1011.5 -- stairs between 20 and 45 degrees)
        for (angle_deg, compliant, desc) in [
            (30, True,  "typical residential 30-degree stair"),
            (45, True,  "steep 45-degree stair (max)"),
            (50, False, "50-degree stair exceeds 45 degrees max"),
            (18, False, "18-degree stair shallower than 20-degree min"),
        ]:
            samples.append(_s(
                f"Validate IBC 1011.5 stair angle between 20 and 45 degrees: {desc}",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using System;

// IBC 1011.5: Stair slope between 20 and 45 degrees (derived from riser/tread ratios)
// angle = atan(riser / tread); compliant range 20-45 deg
void ValidateStairAngle_{int(angle_deg)}deg(FamilyInstance stairInst)
{{
    double minAngleDeg = 20.0; // IBC 1011.5
    double maxAngleDeg = 45.0; // IBC 1011.5

    Parameter pRiser = stairInst.LookupParameter("Riser Height");
    Parameter pTread = stairInst.LookupParameter("Tread Depth");
    if (pRiser == null || pTread == null) return;

    double riser  = pRiser.AsDouble();
    double tread  = pTread.AsDouble();
    double angle  = Math.Atan2(riser, tread) * 180.0 / Math.PI; // degrees

    if (angle < minAngleDeg || angle > maxAngleDeg)
    {{
        TaskDialog.Show("IBC 1011.5 Violation",
            $"Stair angle {{angle:F1}} degrees is outside 20-45 degree range. "
            + "Ref: IBC 1011.5.");
    }}
}}""",
            ))

        # Stair tread surface -- slip resistance (ASTM C1028 / ADA 302)
        samples.append(_s(
            "Validate ADA 302 / ASTM C1028 stair tread slip-resistance coefficient (SCOF >= 0.6)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 302.1 / ASTM C1028: Accessible stair treads must have slip-resistant surface
// Minimum static coefficient of friction (SCOF) = 0.6 (accessible), 0.5 (stairs general)
void ValidateStairTreadSlipResistance(FamilyInstance stairInst)
{
    double minSCOF       = 0.6; // ADA 302.1 accessible requirement
    double minSCOFGeneral = 0.5; // ASTM C1028 general stair

    Parameter pSCOF       = stairInst.LookupParameter("Tread Slip Coefficient (SCOF)");
    Parameter pIsAccessible = stairInst.LookupParameter("On Accessible Route");
    if (pSCOF == null) return;

    double scof         = pSCOF.AsDouble();
    bool isAccessible   = pIsAccessible != null && pIsAccessible.AsInteger() == 1;
    double required     = isAccessible ? minSCOF : minSCOFGeneral;

    if (scof < required)
    {
        TaskDialog.Show("ADA 302 / ASTM C1028 Violation",
            $"Stair tread SCOF {scof:F2} < {required:F1} minimum "
            + $"(accessible: {isAccessible}). "
            + "Ref: ADA 302.1 / ASTM C1028.");
    }
}""",
        ))

        # Stair intermediate handrail (IBC 1011.10 -- required if width > 88 in)
        samples.append(_s(
            "Validate IBC 1011.10 intermediate handrail requirement for stairs wider than 88 in",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1011.10: Stairs wider than 88 in require intermediate handrail(s)
// Intermediate rails divide the stair width into segments <= 88 in
void ValidateIntermediateHandrail(FamilyInstance stairInst)
{{
    double maxWidthPerLaneFt = {88 * IN_TO_FT:.6f}; // 88 in -- IBC 1011.10

    Parameter pWidth      = stairInst.LookupParameter("Stair Width");
    Parameter pRailCount  = stairInst.LookupParameter("Total Handrail Count");
    if (pWidth == null) return;

    double width = pWidth.AsDouble();
    if (width <= maxWidthPerLaneFt) return; // No intermediate rail needed

    // Required lanes = ceil(width / 88 in)
    int requiredLanes = (int)Math.Ceiling(width / maxWidthPerLaneFt);
    int requiredRails = requiredLanes + 1; // Rails = lanes + 1 (sides)
    int providedRails = pRailCount != null ? (int)pRailCount.AsDouble() : 2;

    if (providedRails < requiredRails)
    {{
        TaskDialog.Show("IBC 1011.10 Violation",
            $"Stair width {{width * 12.0:F1}} in requires {{requiredRails}} handrails; {{providedRails}} provided. "
            + "Ref: IBC 1011.10.");
    }}
}}""",
        ))

        # Spiral stair minimum width and tread (IBC 1011.10 -- 26 in radius, 7.5 in tread at walk line)
        samples.append(_s(
            "Validate IBC 1011.10 spiral stair minimum clear width (26 in) and tread depth (7.5 in at walk line)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1011.10: Spiral stairs (permitted only for limited occupancy)
// Clear width: 26 in minimum, Tread depth at walk line: 7.5 in minimum
// Walk line: 12 in from narrower edge
void ValidateSpiralStair(FamilyInstance stairInst)
{{
    double minWidthFt    = {26  * IN_TO_FT:.6f}; // 26 in -- IBC 1011.10
    double minTreadFt    = {7.5 * IN_TO_FT:.6f}; // 7.5 in at walk line -- IBC 1011.10
    double maxRiserFt    = {9.5 * IN_TO_FT:.6f}; // 9.5 in max riser -- IBC 1011.10

    Parameter pIsSpiral  = stairInst.LookupParameter("Is Spiral Stair");
    Parameter pWidth     = stairInst.LookupParameter("Clear Width");
    Parameter pTread     = stairInst.LookupParameter("Tread Depth at Walk Line");
    Parameter pRiser     = stairInst.LookupParameter("Riser Height");
    if (pIsSpiral == null || pIsSpiral.AsInteger() != 1) return;

    if (pWidth != null && pWidth.AsDouble() < minWidthFt)
        TaskDialog.Show("IBC 1011.10 Violation",
            $"Spiral stair clear width {{pWidth.AsDouble() * 12.0:F2}} in < 26 in. Ref: IBC 1011.10.");

    if (pTread != null && pTread.AsDouble() < minTreadFt)
        TaskDialog.Show("IBC 1011.10 Violation",
            $"Spiral stair tread at walk line {{pTread.AsDouble() * 12.0:F2}} in < 7.5 in. Ref: IBC 1011.10.");

    if (pRiser != null && pRiser.AsDouble() > maxRiserFt)
        TaskDialog.Show("IBC 1011.10 Violation",
            $"Spiral stair riser {{pRiser.AsDouble() * 12.0:F2}} in > 9.5 in max. Ref: IBC 1011.10.");
}}""",
        ))

        # Run/rise relationship for comfortable stair angle (2R+T = 24-25 in rule)
        samples.append(_s(
            "Validate 2R+T stair comfort formula (2 x riser + tread = 24-25 in for comfort)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// CSFM / Best Practice: 2R + T should be between 24 and 25 in for comfortable stairs
// (Not a code requirement but a standard design check)
void ValidateStairRiseTreadFormula(FamilyInstance stairInst)
{
    double minFormula = 24.0 / 12.0; // 24 in in feet
    double maxFormula = 25.0 / 12.0; // 25 in in feet

    Parameter pRiser = stairInst.LookupParameter("Riser Height");
    Parameter pTread = stairInst.LookupParameter("Tread Depth");
    if (pRiser == null || pTread == null) return;

    double r = pRiser.AsDouble();
    double t = pTread.AsDouble();
    double formula = 2 * r + t;

    if (formula < minFormula || formula > maxFormula)
    {
        TaskDialog.Show("Stair Comfort Warning",
            $"2R+T = {formula * 12.0:F2} in is outside the 24-25 in comfort range "
            + $"(R={r * 12.0:F2} in, T={t * 12.0:F2} in). "
            + "Not a code violation but a design comfort check.");
    }
}""",
        ))

        # Stair run maximum -- 12 ft between horizontal level (IBC 1011.6 reminder with count)
        samples.append(_s(
            "Validate IBC 1011.5.2 stair riser/tread ratio using IBC graphical limits (R+T and 2R+T)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1011.5.2: Riser and tread dimensional limits
// Also: R + T must be between 17 and 21 in (practical rule)
// 2R + T must be between 24 and 25 in (comfort rule, common design check)
void ValidateRiserTreadRatio(FamilyInstance stairInst)
{
    Parameter pRiser = stairInst.LookupParameter("Riser Height");
    Parameter pTread = stairInst.LookupParameter("Tread Depth");
    if (pRiser == null || pTread == null) return;

    double r = pRiser.AsDouble() * 12.0; // convert to inches
    double t = pTread.AsDouble() * 12.0;

    // IBC 1011.5.2 dimensional limits
    if (r > 7.0) TaskDialog.Show("IBC 1011.5.2 Violation", $"Riser {r:F2} in > 7 in max. Ref: IBC 1011.5.2.");
    if (r < 4.0) TaskDialog.Show("IBC 1011.5.2 Violation", $"Riser {r:F2} in < 4 in min. Ref: IBC 1011.5.2.");
    if (t < 11.0) TaskDialog.Show("IBC 1011.5.2 Violation", $"Tread {t:F2} in < 11 in min. Ref: IBC 1011.5.2.");

    // R+T design check
    double rt = r + t;
    if (rt < 17.0 || rt > 21.0)
        TaskDialog.Show("Stair Design Warning",
            $"R+T = {rt:F2} in is outside recommended 17-21 in range. "
            + $"Riser={r:F2} in, Tread={t:F2} in.");
}""",
        ))

        # Winder stair geometry (IBC 1011.5.3 -- 6 in min tread at walk line)
        samples.append(_s(
            "Validate IBC 1011.5.3 winder stair minimum tread depth (6 in at walk line, 10 in at 12 in from narrow edge)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1011.5.3: Winder stairs
// Minimum tread at walk line (12 in from narrow end): 10 in
// Minimum tread at 6 in from narrow end: 6 in
void ValidateWinderStairTread(FamilyInstance stairInst)
{{
    double minAtWalkLineFt = {10.0 * IN_TO_FT:.6f}; // 10 in at walk line -- IBC 1011.5.3
    double minAt6InFt      = {6.0  * IN_TO_FT:.6f}; // 6 in at narrow end -- IBC 1011.5.3

    Parameter pWinderW12 = stairInst.LookupParameter("Winder Tread at Walk Line");
    Parameter pWinderW6  = stairInst.LookupParameter("Winder Tread at 6in");
    Parameter pIsWinder  = stairInst.LookupParameter("Is Winder Stair");
    if (pIsWinder == null || pIsWinder.AsInteger() != 1) return;

    if (pWinderW12 != null && pWinderW12.AsDouble() < minAtWalkLineFt)
    {{
        TaskDialog.Show("IBC 1011.5.3 Violation",
            $"Winder tread {{pWinderW12.AsDouble() * 12.0:F2}} in at walk line < 10 in. "
            + "Ref: IBC 1011.5.3.");
    }}
    if (pWinderW6 != null && pWinderW6.AsDouble() < minAt6InFt)
    {{
        TaskDialog.Show("IBC 1011.5.3 Violation",
            $"Winder tread {{pWinderW6.AsDouble() * 12.0:F2}} in at 6-in point < 6 in. "
            + "Ref: IBC 1011.5.3.");
    }}
}}""",
        ))

        # Nosing projection (IBC 1011.5.5 -- 0.75 in to 1.25 in overhang)
        samples.append(_s(
            "Validate IBC 1011.5.5 stair nosing projection (0.75 in minimum, 1.25 in maximum)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1011.5.5: Stair nosing projection 0.75 in to 1.25 in beyond riser face
void ValidateNosingProjection(FamilyInstance stairInst)
{{
    double minNosingFt = {0.75 * IN_TO_FT:.6f}; // 0.75 in -- IBC 1011.5.5
    double maxNosingFt = {1.25 * IN_TO_FT:.6f}; // 1.25 in -- IBC 1011.5.5

    Parameter pNosing = stairInst.LookupParameter("Nosing Projection");
    if (pNosing == null) return;

    double nosing = pNosing.AsDouble();
    if (nosing < minNosingFt || nosing > maxNosingFt)
    {{
        TaskDialog.Show("IBC 1011.5.5 Violation",
            $"Nosing projection {{nosing * 12.0:F3}} in is outside the 0.75-1.25 in range. "
            + "Ref: IBC 1011.5.5.");
    }}
}}""",
        ))

        # Curved stair (IBC 1011.9 -- 10 in min tread depth at walk line)
        samples.append(_s(
            "Validate IBC 1011.9 curved stair minimum tread depth (10 in at walk line 12 in from narrow end)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1011.9: Curved stair -- minimum tread at walk line (12 in from narrow edge) = 10 in
// Smaller end must be >= 6 in
void ValidateCurvedStairTread(FamilyInstance stairInst)
{{
    double minTreadWalkFt = {10.0 * IN_TO_FT:.6f}; // 10 in at walk line -- IBC 1011.9
    double minTreadNarrow = {6.0  * IN_TO_FT:.6f};  // 6 in at narrow end -- IBC 1011.9

    Parameter pIsCurved  = stairInst.LookupParameter("Is Curved Stair");
    Parameter pTreadWalk = stairInst.LookupParameter("Tread Depth at Walk Line");
    Parameter pTreadNarr = stairInst.LookupParameter("Tread Depth Narrow End");
    if (pIsCurved == null || pIsCurved.AsInteger() != 1) return;

    if (pTreadWalk != null && pTreadWalk.AsDouble() < minTreadWalkFt)
    {{
        TaskDialog.Show("IBC 1011.9 Violation",
            $"Curved stair tread {{pTreadWalk.AsDouble() * 12.0:F2}} in at walk line < 10 in. "
            + "Ref: IBC 1011.9.");
    }}
    if (pTreadNarr != null && pTreadNarr.AsDouble() < minTreadNarrow)
    {{
        TaskDialog.Show("IBC 1011.9 Violation",
            $"Curved stair narrow tread {{pTreadNarr.AsDouble() * 12.0:F2}} in < 6 in minimum. "
            + "Ref: IBC 1011.9.");
    }}
}}""",
        ))

        # Alternating tread device (IBC 1011.14 -- 8.5 in tread depth, 30-35 deg angle)
        samples.append(_s(
            "Validate IBC 1011.14 alternating tread device geometry (8.5 in tread, 50-70 degree angle)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1011.14: Alternating tread devices
// Tread depth: 8.5 in (projected), Angle: 50 to 70 degrees from horizontal
void ValidateAlternatingTreadDevice(FamilyInstance stairInst)
{{
    double minTreadFt   = {8.5  * IN_TO_FT:.6f}; // 8.5 in -- IBC 1011.14
    double minAngleDeg  = 50.0; // degrees -- IBC 1011.14
    double maxAngleDeg  = 70.0; // degrees -- IBC 1011.14

    Parameter pIsATD   = stairInst.LookupParameter("Is Alternating Tread Device");
    Parameter pTread   = stairInst.LookupParameter("Tread Depth");
    Parameter pAngle   = stairInst.LookupParameter("Stair Angle (degrees)");
    if (pIsATD == null || pIsATD.AsInteger() != 1) return;

    if (pTread != null && pTread.AsDouble() < minTreadFt)
    {{
        TaskDialog.Show("IBC 1011.14 Violation",
            $"ATD tread {{pTread.AsDouble() * 12.0:F2}} in < 8.5 in minimum. "
            + "Ref: IBC 1011.14.");
    }}
    if (pAngle != null)
    {{
        double angle = pAngle.AsDouble();
        if (angle < minAngleDeg || angle > maxAngleDeg)
        {{
            TaskDialog.Show("IBC 1011.14 Violation",
                $"ATD angle {{angle:F1}} deg is outside required 50-70 degree range. "
                + "Ref: IBC 1011.14.");
        }}
    }}
}}""",
        ))

        # Stair run length limit -- max 12 ft rise without landing (IBC 1011.6)
        samples.append(_s(
            "Validate IBC 1011.6 maximum vertical rise between landings (12 ft)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1011.6: Maximum vertical rise of a flight between landings = 12 ft
void ValidateMaxRiseBetweenLandings(FamilyInstance stairFlightInst)
{{
    double maxRiseFt = 12.0; // 12 ft -- IBC 1011.6

    Parameter pRise = stairFlightInst.LookupParameter("Flight Rise Height");
    if (pRise == null) return;

    double rise = pRise.AsDouble();
    if (rise > maxRiseFt)
    {{
        TaskDialog.Show("IBC 1011.6 Violation",
            $"Stair flight vertical rise {{rise:F2}} ft exceeds 12 ft maximum between landings. "
            + "Ref: IBC 1011.6.");
    }}
}}""",
        ))

        # Stair handrail continuity (IBC 1011.11.4 -- continuous full length of flight)
        samples.append(_s(
            "Validate IBC 1011.11.4 stair handrail continuity -- must run full length of stair flight",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1011.11.4: Handrail must be continuous for full length of stair flight
// Must extend 12 in beyond top riser and 12 in sloped below bottom riser
void ValidateHandrailContinuity(FamilyInstance stairInst)
{
    Parameter pFlightLength = stairInst.LookupParameter("Flight Length");
    Parameter pHandrailLen  = stairInst.LookupParameter("Handrail Length");
    Parameter pTopExtension = stairInst.LookupParameter("Handrail Top Extension");
    Parameter pBotExtension = stairInst.LookupParameter("Handrail Bottom Extension");

    double minTopExt = 12.0 / 12.0; // 12 in -- IBC 1011.11.6
    double minBotExt = 12.0 / 12.0; // 12 in sloped -- IBC 1011.11.6

    if (pTopExtension != null && pTopExtension.AsDouble() < minTopExt)
    {
        TaskDialog.Show("IBC 1011.11.6 Violation",
            $"Handrail top extension {pTopExtension.AsDouble() * 12.0:F2} in < required 12 in. "
            + "Ref: IBC 1011.11.6.");
    }
    if (pBotExtension != null && pBotExtension.AsDouble() < minBotExt)
    {
        TaskDialog.Show("IBC 1011.11.6 Violation",
            $"Handrail bottom extension {pBotExtension.AsDouble() * 12.0:F2} in < required 12 in. "
            + "Ref: IBC 1011.11.6.");
    }
}""",
        ))

        # Accessible stair -- ADA 504 (IBC 1011 + ADA requirements)
        samples.append(_s(
            "Validate ADA 504 accessible stair -- uniform riser 4-7 in, tread 11 in min, no open risers",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 504: Accessible stair compliance
// Riser height: 4-7 in, Tread depth: 11 in min, Open risers not permitted
void ValidateADAStair(FamilyInstance stairInst)
{{
    double minRiserFt = {4.0  * IN_TO_FT:.6f}; // 4 in -- ADA 504.2
    double maxRiserFt = {7.0  * IN_TO_FT:.6f}; // 7 in -- ADA 504.2
    double minTreadFt = {11.0 * IN_TO_FT:.6f}; // 11 in -- ADA 504.3

    Parameter pRiser    = stairInst.LookupParameter("Riser Height");
    Parameter pTread    = stairInst.LookupParameter("Tread Depth");
    Parameter pOpenRiser = stairInst.LookupParameter("Has Open Risers");
    Parameter pIsADA    = stairInst.LookupParameter("On Accessible Route");
    if (pIsADA == null || pIsADA.AsInteger() != 1) return;

    if (pRiser != null)
    {{
        double r = pRiser.AsDouble();
        if (r < minRiserFt || r > maxRiserFt)
            TaskDialog.Show("ADA 504.2 Violation",
                $"Riser {{r * 12.0:F2}} in outside 4-7 in range. Ref: ADA 504.2.");
    }}
    if (pTread != null && pTread.AsDouble() < minTreadFt)
        TaskDialog.Show("ADA 504.3 Violation",
            $"Tread {{pTread.AsDouble() * 12.0:F2}} in < 11 in minimum. Ref: ADA 504.3.");

    if (pOpenRiser != null && pOpenRiser.AsInteger() == 1)
        TaskDialog.Show("ADA 504.4 Violation",
            "Open risers not permitted on accessible stairs. Ref: ADA 504.4.");
}}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # IBC 1015 -- Guards and railings
    # ------------------------------------------------------------------

    def _guard_railing(self) -> List[SAMPLE]:
        samples = []

        # Guard height: 42 in min above walking surface where drop > 30 in (IBC 1015.3)
        for (height_in, drop_in, desc) in [
            (42, 36, "standard guard 42 in (compliant)"),
            (36, 36, "guard 36 in (violation -- below 42 in min)"),
            (48, 48, "tall guard 48 in (compliant)"),
            (42, 24, "guard where drop is 24 in -- no guard required"),
        ]:
            h_ft = height_in * IN_TO_FT
            drop_ft = drop_in * IN_TO_FT
            samples.append(_s(
                f"Validate IBC 1015.3 guard height: {desc}",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1015.3: Guard required where drop > 30 in; minimum height 42 in
// IBC 1015.2: Guards required on open sides of walking surfaces > 30 in above floor/grade
void ValidateGuardHeight(FamilyInstance guardInst)
{{
    double minHeightFt   = {42 * IN_TO_FT:.6f}; // 42 in -- IBC 1015.3
    double triggerDropFt = {30 * IN_TO_FT:.6f}; // 30 in drop triggers guard requirement

    Parameter pHeight = guardInst.LookupParameter("Guard Height");
    Parameter pDrop   = guardInst.LookupParameter("Adjacent Drop");
    if (pHeight == null) return;

    double height = pHeight.AsDouble(); // {h_ft:.6f} ft = {height_in} in
    double drop   = pDrop != null ? pDrop.AsDouble() : {drop_ft:.6f}; // {drop_in} in

    if (drop > triggerDropFt && height < minHeightFt)
    {{
        TaskDialog.Show("IBC 1015.3 Violation",
            $"Guard height {{height * 12.0:F2}} in is below required 42 in minimum "
            + $"where adjacent drop is {{drop * 12.0:F2}} in. "
            + "Ref: IBC 1015.2 / IBC 1015.3.");
    }}
}}""",
            ))

        # Guard opening limitations: 4 in max residential (IBC 1015.4)
        for (occ, max_in, code) in [
            ("Residential R-2/R-3", 4, "IBC 1015.4 (residential: 4 in sphere test)"),
            ("Commercial/Assembly", 4, "IBC 1015.4 (commercial: 4 in sphere test)"),
            ("Occupancies above 200 in", 8, "IBC 1015.4 exception (elevated > 200 in)"),
        ]:
            max_ft = max_in * IN_TO_FT
            samples.append(_s(
                f"Validate IBC 1015.4 guard opening size for {occ}",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// {code}
// Max opening that a sphere can pass through: {max_in} in
void ValidateGuardOpenings_{occ.split('/')[0].replace(' ', '_').replace('-', '_')}(FamilyInstance guardInst)
{{
    double maxOpeningFt = {max_ft:.6f}; // {max_in} in sphere -- {code}

    Parameter pMaxOpening = guardInst.LookupParameter("Max Opening Size");
    if (pMaxOpening == null) return;

    double opening = pMaxOpening.AsDouble();
    if (opening > maxOpeningFt)
    {{
        TaskDialog.Show("IBC 1015.4 Violation",
            $"Guard opening {{opening * 12.0:F2}} in allows passage of a sphere larger "
            + $"than {max_in} in. "
            + "Ref: {code}");
    }}
}}""",
            ))

        # Glass guard -- thickness requirement (IBC 2407)
        samples.append(_s(
            "Validate IBC 2407 glass guard minimum thickness (1/2 in tempered or laminated)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 2407: Glass used in guards must be safety glazing (tempered or laminated)
// Minimum thickness: 1/2 in (0.5 in) for tempered glass in guards
void ValidateGlassGuardThickness(FamilyInstance guardInst)
{{
    double minThickFt = {0.5 * IN_TO_FT:.6f}; // 0.5 in -- IBC 2407

    Parameter pIsGlass  = guardInst.LookupParameter("Is Glass Guard");
    Parameter pThick    = guardInst.LookupParameter("Glass Thickness");
    Parameter pGlazType = guardInst.LookupParameter("Glazing Type");
    if (pIsGlass == null || pIsGlass.AsInteger() != 1) return;

    if (pThick != null)
    {{
        double thick = pThick.AsDouble();
        if (thick < minThickFt)
        {{
            TaskDialog.Show("IBC 2407 Violation",
                $"Glass guard thickness {{thick * 12.0:F3}} in is less than required 0.5 in. "
                + "Ref: IBC 2407.");
        }}
    }}

    if (pGlazType != null)
    {{
        string glazType = pGlazType.AsString();
        if (glazType != "Tempered" && glazType != "Laminated")
        {{
            TaskDialog.Show("IBC 2407 Violation",
                $"Glass guard glazing type '{{glazType}}' is not permitted. "
                + "Must be tempered or laminated safety glazing. "
                + "Ref: IBC 2407.");
        }}
    }}
}}""",
        ))

        # Residential guard height -- 36 in for decks < 30 in above grade (IRC R312)
        samples.append(_s(
            "Validate IRC R312.1.1 residential guard height for decks/porches (36 in min, 42 in above 30 in)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IRC R312.1.1: Residential guards required where drop > 30 in
// Height: 36 in minimum for decks < 30 in, 42 in above
// Note: IBC 1015.3 requires 42 in (commercial); IRC R312 allows 36 in residential
void ValidateResidentialGuardHeight(FamilyInstance guardInst)
{{
    double minResGuardFt = {36 * IN_TO_FT:.6f}; // 36 in -- IRC R312.1.3
    double triggerFt     = {30 * IN_TO_FT:.6f}; // 30 in drop triggers requirement

    Parameter pHeight    = guardInst.LookupParameter("Guard Height");
    Parameter pDrop      = guardInst.LookupParameter("Adjacent Drop");
    Parameter pIsResidential = guardInst.LookupParameter("Is Residential");
    if (pIsResidential == null || pIsResidential.AsInteger() != 1) return;
    if (pHeight == null) return;

    double ht   = pHeight.AsDouble();
    double drop = pDrop != null ? pDrop.AsDouble() : {36 * IN_TO_FT:.6f};

    if (drop > triggerFt && ht < minResGuardFt)
    {{
        TaskDialog.Show("IRC R312.1.3 Violation",
            $"Residential guard height {{ht * 12.0:F2}} in < 36 in minimum where drop > 30 in. "
            + "Ref: IRC R312.1.3.");
    }}
}}""",
        ))

        # Handrail return end (IBC 1011.11.7 -- returns must not be a hazard projection)
        samples.append(_s(
            "Validate IBC 1011.11.7 handrail return end -- must return to wall/post, not create projection hazard",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1011.11.7: Handrail ends must not create a projection hazard
// Must return to wall, guard, or post, OR terminate in a newel/safety terminal
void ValidateHandrailReturn(FamilyInstance railInst)
{
    Parameter pEndType  = railInst.LookupParameter("Handrail End Type");
    if (pEndType == null) return;

    string endType = pEndType.AsString();
    // Valid: "Wall Return", "Guard Return", "Newel Post", "Safety Terminal"
    string[] validEnds = { "Wall Return", "Guard Return", "Newel Post", "Safety Terminal" };
    bool isValid = System.Array.Exists(validEnds, t => t == endType);

    if (!isValid)
    {
        TaskDialog.Show("IBC 1011.11.7 Violation",
            $"Handrail end type '{endType}' may create a projection hazard. "
            + "Must return to wall, guard, newel post, or safety terminal. "
            + "Ref: IBC 1011.11.7.");
    }
}""",
        ))

        # Intermediate guard post spacing (structural adequacy -- IBC 1607.9.1, 200 lb point load)
        samples.append(_s(
            "Validate IBC 1607.9.1 guard rail post spacing for 200-lb concentrated load at top rail",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1607.9.1: Guards must resist 200 lb concentrated load at top in any direction
// Typical post spacing checked against structural capacity -- generally <= 6 ft
void ValidateGuardPostSpacing(FamilyInstance guardInst)
{
    double maxPostSpacingFt = 6.0; // ft -- structural rule of thumb for 200-lb load

    Parameter pPostSpacing = guardInst.LookupParameter("Post Spacing");
    if (pPostSpacing == null) return;

    double spacing = pPostSpacing.AsDouble();
    if (spacing > maxPostSpacingFt)
    {
        TaskDialog.Show("IBC 1607.9.1 Warning",
            $"Guard post spacing {spacing:F2} ft may be excessive for 200-lb concentrated load. "
            + "Verify structural capacity. "
            + "Ref: IBC 1607.9.1.");
    }
}""",
        ))

        # Pool barrier fence height (IBC Appendix G / IRC R326 -- 48 in min)
        samples.append(_s(
            "Validate IBC Appendix G pool barrier fence minimum height (48 in) and self-closing gate",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC Appendix G / IRC R326: Swimming pool barrier
// Fence height: 48 in minimum, Max opening: 4 in sphere, Self-closing / self-latching gate
void ValidatePoolBarrier(FamilyInstance fenceInst)
{{
    double minFenceFt   = {48 * IN_TO_FT:.6f}; // 48 in -- IRC R326
    double maxOpeningFt = {4  * IN_TO_FT:.6f};  // 4 in sphere -- IRC R326

    Parameter pIsPoolFence   = fenceInst.LookupParameter("Is Pool Barrier");
    Parameter pHeight        = fenceInst.LookupParameter("Fence Height");
    Parameter pMaxOpening    = fenceInst.LookupParameter("Max Opening Size");
    Parameter pHasSelfClose  = fenceInst.LookupParameter("Gate Is Self-Closing");
    if (pIsPoolFence == null || pIsPoolFence.AsInteger() != 1) return;

    if (pHeight != null && pHeight.AsDouble() < minFenceFt)
        TaskDialog.Show("IRC R326 Violation",
            $"Pool fence height {{pHeight.AsDouble() * 12.0:F1}} in < 48 in minimum. Ref: IRC R326.");

    if (pMaxOpening != null && pMaxOpening.AsDouble() > maxOpeningFt)
        TaskDialog.Show("IRC R326 Violation",
            $"Pool fence opening {{pMaxOpening.AsDouble() * 12.0:F2}} in > 4 in. Ref: IRC R326.");

    if (pHasSelfClose != null && pHasSelfClose.AsInteger() != 1)
        TaskDialog.Show("IRC R326 Violation",
            "Pool barrier gate must be self-closing and self-latching. Ref: IRC R326.");
}}""",
        ))

        # Roof edge guardrail (OSHA 1926.502 -- construction, 39-45 in height)
        samples.append(_s(
            "Validate OSHA 1926.502(b) construction roof edge guardrail height (39-45 in from walking surface)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// OSHA 1926.502(b): Construction guardrails for workers at roof edges
// Height: 39 in to 45 in above walking surface
// Top rail must withstand 200 lb outward/downward force
void ValidateOSHARoofEdgeGuardrail(FamilyInstance railInst)
{{
    double minHtFt = {39 * IN_TO_FT:.6f}; // 39 in -- OSHA 1926.502(b)
    double maxHtFt = {45 * IN_TO_FT:.6f}; // 45 in -- OSHA 1926.502(b)

    Parameter pIsOSHA = railInst.LookupParameter("Is OSHA Construction Rail");
    Parameter pHeight = railInst.LookupParameter("Guard Height");
    if (pIsOSHA == null || pIsOSHA.AsInteger() != 1) return;

    if (pHeight != null)
    {{
        double ht = pHeight.AsDouble();
        if (ht < minHtFt || ht > maxHtFt)
            TaskDialog.Show("OSHA 1926.502(b) Violation",
                $"Construction guardrail height {{ht * 12.0:F2}} in outside 39-45 in range. "
                + "Ref: OSHA 1926.502(b).");
    }}
}}""",
        ))

        # Mid-rail requirement (IBC 1015.3 -- midrail at 21 in when guard > 42 in)
        samples.append(_s(
            "Validate IBC 1015.3 intermediate (mid) rail requirement when guard height exceeds 42 in",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1015.3 / OSHA 1926.502: When guard exceeds 42 in, mid-rail required
// Mid-rail at approximately half the guard height (21 in typical)
void ValidateMidRail(FamilyInstance guardInst)
{{
    double midRailHeightFt = {21 * IN_TO_FT:.6f}; // ~21 in -- mid-rail position
    double requiresMidAboveFt = {42 * IN_TO_FT:.6f}; // mid-rail needed if guard > 42 in

    Parameter pGuardHt  = guardInst.LookupParameter("Guard Height");
    Parameter pHasMidRail = guardInst.LookupParameter("Has Mid Rail");
    if (pGuardHt == null) return;

    double guardHt = pGuardHt.AsDouble();
    bool hasMidRail = pHasMidRail != null && pHasMidRail.AsInteger() == 1;

    if (guardHt > requiresMidAboveFt && !hasMidRail)
    {{
        TaskDialog.Show("IBC 1015.3 Warning",
            $"Guard height {{guardHt * 12.0:F1}} in > 42 in; verify mid-rail requirement for opening limitations. "
            + "Ref: IBC 1015.3 / 1015.4.");
    }}
}}""",
        ))

        # Cable rail spacing (IBC 1015.4 -- 4 in sphere test, verify cable tension)
        samples.append(_s(
            "Validate IBC 1015.4 cable railing system -- 4 in sphere test and maximum 4 in vertical spacing",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1015.4: Cable guardrail systems must pass 4-inch sphere test
// Typical cable spacing: <= 3 in clear (vertical orientation)
void ValidateCableRailing(FamilyInstance railInst)
{{
    double maxSpacingFt = {3.5 * IN_TO_FT:.6f}; // 3.5 in clear (conservative for sphere test)

    Parameter pIsCable  = railInst.LookupParameter("Is Cable Railing");
    Parameter pSpacing  = railInst.LookupParameter("Cable Spacing");
    if (pIsCable == null || pIsCable.AsInteger() != 1) return;

    if (pSpacing != null && pSpacing.AsDouble() > maxSpacingFt)
    {{
        TaskDialog.Show("IBC 1015.4 Violation",
            $"Cable spacing {{pSpacing.AsDouble() * 12.0:F2}} in may allow 4-inch sphere passage. "
            + "Verify deflection under load does not increase gap beyond 4 in. "
            + "Ref: IBC 1015.4.");
    }}
}}""",
        ))

        # Stair handrail graspability (IBC 1011.11.5 -- 1.25-2 in diameter round, or 4-6.25 in perimeter non-round)
        samples.append(_s(
            "Validate IBC 1011.11.5 handrail graspability (round 1.25-2 in diameter, or non-round 4-6.25 in perimeter)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1011.11.5: Handrail graspability
// Type I (round): 1.25 in to 2 in diameter
// Type II (non-round): perimeter 4 in to 6.25 in, max cross-section 2.25 in
void ValidateHandrailGraspability(FamilyInstance railInst)
{{
    double minDiaFt   = {1.25 * IN_TO_FT:.6f}; // 1.25 in -- IBC 1011.11.5 Type I
    double maxDiaFt   = {2.0  * IN_TO_FT:.6f}; // 2.00 in -- IBC 1011.11.5 Type I
    double minPerimFt = {4.0  * IN_TO_FT:.6f}; // 4.00 in perimeter -- Type II
    double maxPerimFt = {6.25 * IN_TO_FT:.6f}; // 6.25 in perimeter -- Type II

    Parameter pDia   = railInst.LookupParameter("Handrail Diameter");
    Parameter pPerim = railInst.LookupParameter("Handrail Perimeter");
    Parameter pType  = railInst.LookupParameter("Handrail Type");
    if (pType == null) return;

    string hrType = pType.AsString();
    if (hrType == "Round" && pDia != null)
    {{
        double dia = pDia.AsDouble();
        if (dia < minDiaFt || dia > maxDiaFt)
        {{
            TaskDialog.Show("IBC 1011.11.5 Violation",
                $"Round handrail diameter {{dia * 12.0:F3}} in is outside 1.25-2.0 in range. "
                + "Ref: IBC 1011.11.5 Type I.");
        }}
    }}
    else if (hrType == "Non-Round" && pPerim != null)
    {{
        double perim = pPerim.AsDouble();
        if (perim < minPerimFt || perim > maxPerimFt)
        {{
            TaskDialog.Show("IBC 1011.11.5 Violation",
                $"Non-round handrail perimeter {{perim * 12.0:F3}} in is outside 4.0-6.25 in range. "
                + "Ref: IBC 1011.11.5 Type II.");
        }}
    }}
}}""",
        ))

        # Guard loading requirement (IBC 1607.9.1 -- 200 lbf at top, 50 lbf/ft infill)
        samples.append(_s(
            "Validate IBC 1607.9.1 guardrail design load (200 lbf concentrated at top rail, 50 lb/ft infill)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1607.9.1: Guards must resist 200 lbf concentrated at top in any direction
// and 50 lb/ft linear load on infill
void ValidateGuardLoadDesign(FamilyInstance guardInst)
{
    double minTopRailLbf  = 200.0; // 200 lbf -- IBC 1607.9.1
    double minInfillLbFt  = 50.0;  // 50 lb/lf -- IBC 1607.9.1

    Parameter pTopRailCap = guardInst.LookupParameter("Top Rail Capacity (lbf)");
    Parameter pInfillCap  = guardInst.LookupParameter("Infill Capacity (lb/lf)");

    if (pTopRailCap != null && pTopRailCap.AsDouble() < minTopRailLbf)
        TaskDialog.Show("IBC 1607.9.1 Violation",
            $"Top rail capacity {pTopRailCap.AsDouble():F0} lbf < 200 lbf required. "
            + "Ref: IBC 1607.9.1.");

    if (pInfillCap != null && pInfillCap.AsDouble() < minInfillLbFt)
        TaskDialog.Show("IBC 1607.9.1 Violation",
            $"Infill capacity {pInfillCap.AsDouble():F0} lb/lf < 50 lb/lf required. "
            + "Ref: IBC 1607.9.1.");
}""",
        ))

        # Guardrail at bleachers/tiered seating (IBC 1015.2.2 -- 26 in where seats face)
        samples.append(_s(
            "Validate IBC 1015.2.2 guardrail height at bleacher/tiered seating front row (26 in minimum)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1015.2.2: Guards at bleachers and tiered seating
// Front row seats: guard height 26 in min
// Open sides: guard height 42 in min
void ValidateBleacherGuard(FamilyInstance bleacherInst)
{{
    double minFrontFt = {26 * IN_TO_FT:.6f}; // 26 in front row -- IBC 1015.2.2
    double minSideFt  = {42 * IN_TO_FT:.6f}; // 42 in open side -- IBC 1015.3

    Parameter pFrontHt = bleacherInst.LookupParameter("Front Row Guard Height");
    Parameter pSideHt  = bleacherInst.LookupParameter("Open Side Guard Height");

    if (pFrontHt != null && pFrontHt.AsDouble() < minFrontFt)
        TaskDialog.Show("IBC 1015.2.2 Violation",
            $"Bleacher front guard {{pFrontHt.AsDouble() * 12.0:F2}} in < 26 in minimum. "
            + "Ref: IBC 1015.2.2.");

    if (pSideHt != null && pSideHt.AsDouble() < minSideFt)
        TaskDialog.Show("IBC 1015.3 Violation",
            $"Bleacher open side guard {{pSideHt.AsDouble() * 12.0:F2}} in < 42 in minimum. "
            + "Ref: IBC 1015.3.");
}}""",
        ))

        # Stair nosing visibility contrast (ADA 504.5 -- contrasting strip 2 in deep x 12 in wide)
        samples.append(_s(
            "Validate ADA 504.5 accessible stair nosing visual contrast strip (2 in deep minimum)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 504.5: Stair nosings on accessible routes must have a contrasting strip
// Depth: 2 in measured horizontally, Width: full tread width
void ValidateStairNosingContrast(FamilyInstance stairInst)
{{
    double minContrastDepthFt = {2.0 * IN_TO_FT:.6f}; // 2 in -- ADA 504.5

    Parameter pIsAccessible   = stairInst.LookupParameter("On Accessible Route");
    Parameter pHasContrast    = stairInst.LookupParameter("Has Nosing Contrast Strip");
    Parameter pContrastDepth  = stairInst.LookupParameter("Contrast Strip Depth");
    if (pIsAccessible == null || pIsAccessible.AsInteger() != 1) return;

    if (pHasContrast == null || pHasContrast.AsInteger() != 1)
    {{
        TaskDialog.Show("ADA 504.5 Violation",
            "Accessible stair nosings lack required visual contrast strip. "
            + "Ref: ADA 504.5.");
        return;
    }}

    if (pContrastDepth != null && pContrastDepth.AsDouble() < minContrastDepthFt)
    {{
        TaskDialog.Show("ADA 504.5 Violation",
            $"Nosing contrast strip depth {{pContrastDepth.AsDouble() * 12.0:F2}} in < 2 in. "
            + "Ref: ADA 504.5.");
    }}
}}""",
        ))

        # Handrail bracket spacing (AISC -- max 48-60 in bracket centers)
        samples.append(_s(
            "Validate handrail bracket spacing for wall-mounted rails (48 in maximum center-to-center)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// Best practice / structural design: Handrail wall brackets spaced <= 48 in
// to support 200-lb concentrated load per IBC 1607.9.1
void ValidateHandrailBracketSpacing(FamilyInstance railInst)
{{
    double maxBracketFt = {48 * IN_TO_FT:.6f}; // 48 in -- structural best practice

    Parameter pBracketSpacing = railInst.LookupParameter("Bracket Spacing");
    if (pBracketSpacing == null) return;

    double spacing = pBracketSpacing.AsDouble();
    if (spacing > maxBracketFt)
    {{
        TaskDialog.Show("Handrail Bracket Spacing Warning",
            $"Handrail bracket spacing {{spacing * 12.0:F1}} in > 48 in recommended maximum. "
            + "Verify structural capacity for 200-lb load. Ref: IBC 1607.9.1.");
    }}
}}""",
        ))

        # Guard at elevated mechanical equipment (IBC 1015.7 -- mechanical equipment walk areas)
        samples.append(_s(
            "Validate IBC 1015.7 guardrail at roof mechanical equipment access walkways",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1015.7: Roof access catwalks and equipment platforms > 30 in above roof
// require guards per IBC 1015.2 / 1015.3
void ValidateMechanicalEquipmentGuard(FamilyInstance catwalkInst)
{{
    double minGuardFt    = {42 * IN_TO_FT:.6f}; // 42 in -- IBC 1015.3
    double triggerDropFt = {30 * IN_TO_FT:.6f}; // 30 in -- IBC 1015.2

    Parameter pElevation = catwalkInst.LookupParameter("Catwalk Elevation Above Roof");
    Parameter pHasGuard  = catwalkInst.LookupParameter("Has Guard");
    Parameter pGuardHt   = catwalkInst.LookupParameter("Guard Height");
    if (pElevation == null) return;

    double elev = pElevation.AsDouble();
    if (elev <= triggerDropFt) return;

    bool hasGuard = pHasGuard != null && pHasGuard.AsInteger() == 1;
    if (!hasGuard)
    {{
        TaskDialog.Show("IBC 1015.7 Violation",
            $"Mechanical equipment catwalk {{elev * 12.0:F1}} in above roof requires guard. "
            + "Ref: IBC 1015.7.");
    }}
    else if (pGuardHt != null && pGuardHt.AsDouble() < minGuardFt)
    {{
        TaskDialog.Show("IBC 1015.3 Violation",
            $"Catwalk guard height {{pGuardHt.AsDouble() * 12.0:F2}} in < 42 in minimum. "
            + "Ref: IBC 1015.3.");
    }}
}}""",
        ))

        # Guard at elevated floor opening (IBC 1015.2 -- open-sided walking surfaces)
        samples.append(_s(
            "Validate IBC 1015.2 guard requirement at open-sided walking surface (drop > 30 in)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1015.2: Guards are required at open sides of walking surfaces
// where the drop is more than 30 in below the walking surface
void ValidateGuardRequired(FamilyInstance slabEdgeInst)
{{
    double triggerFt = {30 * IN_TO_FT:.6f}; // 30 in -- IBC 1015.2

    Parameter pDrop     = slabEdgeInst.LookupParameter("Drop Height");
    Parameter pHasGuard = slabEdgeInst.LookupParameter("Has Guard");
    if (pDrop == null) return;

    double drop     = pDrop.AsDouble();
    bool hasGuard   = pHasGuard != null && pHasGuard.AsInteger() == 1;

    if (drop > triggerFt && !hasGuard)
    {{
        TaskDialog.Show("IBC 1015.2 Violation",
            $"Open-sided walking surface with {{drop * 12.0:F1}} in drop requires a guard. "
            + "Ref: IBC 1015.2.");
    }}
}}""",
        ))

        # Guard at stair intermediate landing (IBC 1015.3 -- 42 in required)
        samples.append(_s(
            "Validate IBC 1015.3 guard height at stair intermediate landing and mezzanine (42 in min)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1015.3: Guards at mezzanines, equipment platforms, balconies, etc.
// Minimum guard height: 42 in for occupancies other than residential
void ValidateGuardAtMezzanine(FamilyInstance mezzanineInst)
{{
    double minGuardFt = {42 * IN_TO_FT:.6f}; // 42 in -- IBC 1015.3

    Parameter pGuardHt = mezzanineInst.LookupParameter("Guard Height");
    Parameter pHasGuard = mezzanineInst.LookupParameter("Has Perimeter Guard");
    if (pHasGuard != null && pHasGuard.AsInteger() != 1)
    {{
        TaskDialog.Show("IBC 1015.3 Violation",
            "Mezzanine perimeter guard is missing. "
            + "Ref: IBC 1015.3.");
        return;
    }}
    if (pGuardHt != null && pGuardHt.AsDouble() < minGuardFt)
    {{
        TaskDialog.Show("IBC 1015.3 Violation",
            $"Guard height {{pGuardHt.AsDouble() * 12.0:F2}} in < 42 in minimum at mezzanine. "
            + "Ref: IBC 1015.3.");
    }}
}}""",
        ))

        # ICC A117.1 S406 -- curb ramp flare slope
        samples.append(_s(
            "Validate ICC A117.1 S406.3 curb ramp flare maximum slope (1:10)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ICC A117.1 S406.3: Curb ramp flares shall not exceed 1:10 slope
void ValidateCurbRampFlare(FamilyInstance curbRampInst)
{
    double maxFlareSlopeFt = 1.0 / 10.0; // 1:10 -- ICC A117.1 S406.3

    Parameter pFlareSlope = curbRampInst.LookupParameter("Flare Slope");
    if (pFlareSlope == null) return;

    double flare = pFlareSlope.AsDouble();
    if (flare > maxFlareSlopeFt)
    {
        TaskDialog.Show("ICC A117.1 S406.3 Violation",
            $"Curb ramp flare slope 1:{(1.0/flare):F1} ({flare:P1}) exceeds 1:10 maximum. "
            + "Ref: ICC A117.1 S406.3.");
    }
}""",
        ))

        # Roof access guard (IBC 1015 -- roof walking surfaces require guard if accessible)
        samples.append(_s(
            "Validate IBC 1015 guard requirement on accessible roof walking surfaces (drop > 30 in)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1015: Accessible roof walking surfaces with drops > 30 in require guards
// Same 42 in minimum height applies
void ValidateRoofGuard(FamilyInstance roofAccessInst)
{{
    double minGuardFt  = {42 * IN_TO_FT:.6f}; // 42 in -- IBC 1015.3
    double triggerDropFt = {30 * IN_TO_FT:.6f}; // 30 in -- IBC 1015.2

    Parameter pIsAccessible = roofAccessInst.LookupParameter("Accessible Roof Area");
    Parameter pEdgeDrop     = roofAccessInst.LookupParameter("Edge Drop Height");
    Parameter pGuardHt      = roofAccessInst.LookupParameter("Guard Height");
    if (pIsAccessible == null || pIsAccessible.AsInteger() != 1) return;

    double drop = pEdgeDrop != null ? pEdgeDrop.AsDouble() : 0;
    if (drop <= triggerDropFt) return;

    if (pGuardHt == null)
    {{
        TaskDialog.Show("IBC 1015 Violation",
            $"Accessible roof area with {{drop * 12.0:F1}} in drop requires 42 in guard. "
            + "Ref: IBC 1015.3.");
    }}
    else if (pGuardHt.AsDouble() < minGuardFt)
    {{
        TaskDialog.Show("IBC 1015.3 Violation",
            $"Roof guard height {{pGuardHt.AsDouble() * 12.0:F2}} in < 42 in minimum. "
            + "Ref: IBC 1015.3.");
    }}
}}""",
        ))

        # Intermediate rail (IBC 1015.3 -- baluster spacing test)
        samples.append(_s(
            "Validate IBC 1015.4 guard baluster spacing with 4-inch sphere test using parameter loop",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1015.4: Guard infill must prevent passage of a 4-inch sphere
// Check baluster spacing parameter (clear distance between balusters)
void ValidateBalusterSpacing(FamilyInstance guardInst)
{{
    double maxSpacingFt = {4.0 * IN_TO_FT:.6f}; // 4 in clear -- IBC 1015.4

    Parameter pSpacing  = guardInst.LookupParameter("Baluster Clear Spacing");
    Parameter pCount    = guardInst.LookupParameter("Baluster Count");
    Parameter pLength   = guardInst.LookupParameter("Guard Length");
    Parameter pBalWidth = guardInst.LookupParameter("Baluster Width");

    if (pSpacing != null)
    {{
        double spacing = pSpacing.AsDouble();
        if (spacing > maxSpacingFt)
        {{
            TaskDialog.Show("IBC 1015.4 Violation",
                $"Baluster clear spacing {{spacing * 12.0:F2}} in exceeds 4 in maximum. "
                + "Ref: IBC 1015.4 (4-inch sphere test).");
        }}
    }}
    else if (pCount != null && pLength != null && pBalWidth != null)
    {{
        // Calculate from geometry
        int n          = (int)pCount.AsDouble();
        double length  = pLength.AsDouble();
        double balW    = pBalWidth.AsDouble();
        double clear   = (n > 1) ? (length - n * balW) / (n - 1) : length;

        if (clear > maxSpacingFt)
        {{
            TaskDialog.Show("IBC 1015.4 Violation",
                $"Calculated baluster clear spacing {{clear * 12.0:F2}} in exceeds 4 in. "
                + "Ref: IBC 1015.4.");
        }}
    }}
}}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # NFPA 80 / NFPA 101 -- Fire ratings
    # ------------------------------------------------------------------

    def _fire_ratings(self) -> List[SAMPLE]:
        samples = []

        # Fire door rating based on wall rating (NFPA 80 / IBC Table 716.1)
        for (wall_hr, door_hr, code_ref) in [
            (4, 3,   "IBC Table 716.1(2): 4-hr wall requires 3-hr door"),
            (3, 3,   "IBC Table 716.1(2): 3-hr wall requires 3-hr door"),
            (2, 1.5, "IBC Table 716.1(2): 2-hr wall requires 1.5-hr door"),
            (1, 0.75,"IBC Table 716.1(2): 1-hr wall requires 3/4-hr door"),
            (0.5, 0.5,"IBC Table 716.1(3): corridor wall 1/2-hr door"),
        ]:
            samples.append(_s(
                f"Validate NFPA 80 fire door rating for {wall_hr}-hour fire-rated wall",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// {code_ref}
// {wall_hr}-hr wall requires minimum {door_hr}-hr rated door assembly
void ValidateFireDoorRating(FamilyInstance doorInst)
{{
    double requiredDoorHr = {door_hr}; // {code_ref}

    Parameter pWallRating = doorInst.LookupParameter("Adjacent Wall Fire Rating (hr)");
    Parameter pDoorRating = doorInst.LookupParameter("Fire Rating (hr)");
    if (pWallRating == null || pDoorRating == null) return;

    double wallRating = pWallRating.AsDouble();
    double doorRating = pDoorRating.AsDouble();

    // Check only if the wall is rated at {wall_hr} hr
    if (Math.Abs(wallRating - {wall_hr}) < 0.01)
    {{
        if (doorRating < requiredDoorHr)
        {{
            TaskDialog.Show("NFPA 80 / IBC 716 Violation",
                $"Wall fire rating {{wallRating}} hr requires door rating >= {{requiredDoorHr}} hr. "
                + $"Actual door rating: {{doorRating}} hr. "
                + "Ref: {code_ref}");
        }}
    }}
}}""",
            ))

        # Fire door clearance -- max 1/8 in clearance top/sides, 3/4 in at bottom (NFPA 80 S4.8.4)
        samples.append(_s(
            "Validate NFPA 80 S4.8.4 fire door clearances (1/8 in top/sides, 3/4 in bottom)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// NFPA 80 S4.8.4: Maximum clearances for fire door assemblies
// Top / sides: 1/8 in max
// Bottom (without threshold): 3/4 in max
// Bottom (with threshold): 3/8 in max
void ValidateFireDoorClearance(FamilyInstance doorInst)
{{
    double maxTopSideFt = {0.125 * IN_TO_FT:.6f}; // 1/8 in -- NFPA 80 S4.8.4
    double maxBottomFt  = {0.75  * IN_TO_FT:.6f}; // 3/4 in -- NFPA 80 S4.8.4
    double maxBottomThreshFt = {0.375 * IN_TO_FT:.6f}; // 3/8 in with threshold

    Parameter pTopClear    = doorInst.LookupParameter("Top Clearance");
    Parameter pSideClear   = doorInst.LookupParameter("Side Clearance");
    Parameter pBottomClear = doorInst.LookupParameter("Bottom Clearance");
    Parameter pHasThresh   = doorInst.LookupParameter("Has Threshold");
    Parameter pIsFireDoor  = doorInst.LookupParameter("Is Fire Door");

    if (pIsFireDoor == null || pIsFireDoor.AsInteger() != 1) return;

    bool hasThreshold = pHasThresh != null && pHasThresh.AsInteger() == 1;

    if (pTopClear != null && pTopClear.AsDouble() > maxTopSideFt)
    {{
        TaskDialog.Show("NFPA 80 S4.8.4 Violation",
            $"Fire door top clearance {{pTopClear.AsDouble() * 12.0:F3}} in exceeds 1/8 in. "
            + "Ref: NFPA 80 S4.8.4.");
    }}
    if (pSideClear != null && pSideClear.AsDouble() > maxTopSideFt)
    {{
        TaskDialog.Show("NFPA 80 S4.8.4 Violation",
            $"Fire door side clearance {{pSideClear.AsDouble() * 12.0:F3}} in exceeds 1/8 in. "
            + "Ref: NFPA 80 S4.8.4.");
    }}
    if (pBottomClear != null)
    {{
        double bottomLimit = hasThreshold ? maxBottomThreshFt : maxBottomFt;
        if (pBottomClear.AsDouble() > bottomLimit)
        {{
            TaskDialog.Show("NFPA 80 S4.8.4 Violation",
                $"Fire door bottom clearance {{pBottomClear.AsDouble() * 12.0:F3}} in exceeds "
                + $"{{bottomLimit * 12.0:F3}} in. "
                + "Ref: NFPA 80 S4.8.4.");
        }}
    }}
}}""",
        ))

        # Fire-rated wall minimum thickness by rating (IBC Table 722)
        for (hr, min_in_conc, min_in_cmu, code) in [
            (1, 3.5, 4,  "IBC Table 722.5.2(1): 1-hr fire rating"),
            (2, 4.5, 6,  "IBC Table 722.5.2(1): 2-hr fire rating"),
            (3, 6.0, 8,  "IBC Table 722.5.2(1): 3-hr fire rating"),
            (4, 7.0, 10, "IBC Table 722.5.2(1): 4-hr fire rating"),
        ]:
            samples.append(_s(
                f"Validate IBC Table 722 fire-rated wall minimum thickness for {hr}-hour rating",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// {code}
// Concrete min thickness: {min_in_conc} in
// CMU min thickness:      {min_in_cmu} in
void ValidateFireRatedWallThickness_{hr}hr(FamilyInstance wallInst)
{{
    double minConcFt = {min_in_conc * IN_TO_FT:.6f}; // {min_in_conc} in concrete
    double minCmuFt  = {min_in_cmu  * IN_TO_FT:.6f}; // {min_in_cmu} in CMU

    Parameter pRating   = wallInst.LookupParameter("Fire Rating (hr)");
    Parameter pThick    = wallInst.LookupParameter("Wall Thickness");
    Parameter pMaterial = wallInst.LookupParameter("Wall Material");
    if (pRating == null || pThick == null) return;

    if (Math.Abs(pRating.AsDouble() - {hr}) > 0.01) return;

    double thick    = pThick.AsDouble();
    string material = pMaterial != null ? pMaterial.AsString() : "Concrete";
    double minThick = material.Contains("CMU") ? minCmuFt : minConcFt;

    if (thick < minThick)
    {{
        TaskDialog.Show("IBC Table 722 Violation",
            $"Wall thickness {{thick * 12.0:F2}} in is below the {hr}-hour fire rating minimum "
            + $"{{minThick * 12.0:F2}} in for {{material}}. "
            + "Ref: {code}");
    }}
}}""",
            ))

        # Fire stopping penetration validation (IBC 714)
        samples.append(_s(
            "Validate IBC 714 fire-stop for penetrations through fire-rated walls",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 714: Penetrations of fire-rated walls must be protected with listed fire-stop systems
// F-rating of the fire-stop must equal or exceed the wall fire rating
void ValidateFireStopPenetration(FamilyInstance penetrationInst)
{
    Parameter pWallRating    = penetrationInst.LookupParameter("Wall Fire Rating (hr)");
    Parameter pFStopRating   = penetrationInst.LookupParameter("Fire-Stop F-Rating (hr)");
    Parameter pHasFireStop   = penetrationInst.LookupParameter("Has Fire-Stop");

    if (pWallRating == null) return;

    double wallRating = pWallRating.AsDouble();
    if (wallRating <= 0) return; // Non-rated wall -- no requirement

    bool hasFireStop = pHasFireStop != null && pHasFireStop.AsInteger() == 1;
    if (!hasFireStop)
    {
        TaskDialog.Show("IBC 714 Violation",
            $"Penetration through {wallRating}-hour fire-rated wall has no fire-stop system. "
            + "Ref: IBC 714.4.");
        return;
    }

    if (pFStopRating != null)
    {
        double fRating = pFStopRating.AsDouble();
        if (fRating < wallRating)
        {
            TaskDialog.Show("IBC 714 Violation",
                $"Fire-stop F-rating {fRating} hr is less than wall fire rating {wallRating} hr. "
                + "Ref: IBC 714.4.1.");
        }
    }
}""",
        ))

        # Smoke compartment area limit (NFPA 101 S19.2.5 -- health care)
        samples.append(_s(
            "Validate NFPA 101 S19.2.5 smoke compartment maximum area (22,500 sq ft health care)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// NFPA 101 S19.2.5: Health care smoke compartments max 22,500 sq ft
// and max 200 ft in any direction
void ValidateSmokeCompartmentArea(FamilyInstance compartmentInst)
{{
    double maxAreaFt2  = 22500.0; // sq ft -- NFPA 101 S19.2.5
    double maxDimFt    = 200.0;   // ft any direction -- NFPA 101 S19.2.5

    Parameter pArea  = compartmentInst.LookupParameter("Smoke Compartment Area");
    Parameter pLength = compartmentInst.LookupParameter("Max Compartment Dimension");
    if (pArea == null) return;

    double area = pArea.AsDouble(); // sq ft (Revit area in sq ft)
    if (area > maxAreaFt2)
    {{
        TaskDialog.Show("NFPA 101 S19.2.5 Violation",
            $"Smoke compartment area {{area:F0}} sq ft exceeds 22,500 sq ft maximum. "
            + "Ref: NFPA 101 S19.2.5.");
    }}

    if (pLength != null)
    {{
        double dim = pLength.AsDouble();
        if (dim > maxDimFt)
        {{
            TaskDialog.Show("NFPA 101 S19.2.5 Violation",
                $"Smoke compartment dimension {{dim:F1}} ft exceeds 200 ft maximum. "
                + "Ref: NFPA 101 S19.2.5.");
        }}
    }}
}}""",
        ))

        # Automatic sprinkler coverage area per head (NFPA 13)
        samples.append(_s(
            "Validate NFPA 13 S8.6 sprinkler head maximum coverage area (light hazard 225 sq ft, ordinary 130 sq ft)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// NFPA 13 S8.6: Maximum area of coverage per sprinkler head
// Light hazard: 225 sq ft (standard) / 200 sq ft (sidewall)
// Ordinary hazard: 130 sq ft
void ValidateSprinklerCoverage(FamilyInstance sprinklerInst)
{
    Parameter pOccHazard = sprinklerInst.LookupParameter("Occupancy Hazard");
    Parameter pCovArea   = sprinklerInst.LookupParameter("Coverage Area (sq ft)");
    if (pOccHazard == null || pCovArea == null) return;

    string hazard = pOccHazard.AsString();
    double maxArea = hazard.Contains("Light")    ? 225.0
                   : hazard.Contains("Ordinary") ? 130.0
                   : hazard.Contains("Extra")    ?  100.0
                   : 225.0;

    double coverage = pCovArea.AsDouble();
    if (coverage > maxArea)
    {
        TaskDialog.Show("NFPA 13 S8.6 Violation",
            $"Sprinkler coverage area {coverage:F0} sq ft exceeds {maxArea:F0} sq ft max "
            + $"for {hazard} hazard occupancy. "
            + "Ref: NFPA 13 S8.6.");
    }
}""",
        ))

        # Egress door fire rating in exit enclosure (IBC 1023.4 -- 1.5 hr doors in 2-hr enclosure)
        samples.append(_s(
            "Validate IBC 1023.4 fire door assembly rating in exit enclosure (1.5 hr for 2-hr, 1 hr for 1-hr)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1023.4: Openings in exit enclosures must have fire door assemblies
// 2-hr enclosure: 1.5-hr rated door assembly
// 1-hr enclosure: 1-hr rated door assembly
void ValidateExitEnclosureDoorRating(FamilyInstance doorInst)
{
    Parameter pInExit      = doorInst.LookupParameter("In Exit Enclosure");
    Parameter pEnclosureHr = doorInst.LookupParameter("Exit Enclosure Rating (hr)");
    Parameter pDoorRating  = doorInst.LookupParameter("Fire Rating (hr)");
    if (pInExit == null || pInExit.AsInteger() != 1) return;

    double enclosure = pEnclosureHr != null ? pEnclosureHr.AsDouble() : 2.0;
    double doorRating = pDoorRating != null ? pDoorRating.AsDouble() : 0;
    double required   = (enclosure >= 2.0) ? 1.5 : 1.0;

    if (doorRating < required)
    {
        TaskDialog.Show("IBC 1023.4 Violation",
            $"Door rating {doorRating} hr < required {required} hr for {enclosure}-hr exit enclosure. "
            + "Ref: IBC 1023.4.");
    }
}""",
        ))

        # NFPA 72 smoke detector spacing (15 ft radius / 900 sq ft per detector)
        samples.append(_s(
            "Validate NFPA 72 S17.6.3 smoke detector maximum spacing (30 ft between detectors, 15 ft from walls)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// NFPA 72 S17.6.3.1: Smoke detector maximum spacing = 30 ft center-to-center
// Maximum distance to wall = 15 ft (half the listed spacing)
void ValidateSmokeDetectorSpacing(FamilyInstance detectorInst)
{
    double maxSpacingFt  = 30.0; // ft -- NFPA 72 S17.6.3
    double maxWallDistFt = 15.0; // ft -- NFPA 72 S17.6.3.1

    Parameter pSpacing   = detectorInst.LookupParameter("Detector Spacing");
    Parameter pWallDist  = detectorInst.LookupParameter("Distance to Nearest Wall");

    if (pSpacing != null && pSpacing.AsDouble() > maxSpacingFt)
        TaskDialog.Show("NFPA 72 S17.6.3 Violation",
            $"Smoke detector spacing {pSpacing.AsDouble():F1} ft > 30 ft maximum. "
            + "Ref: NFPA 72 S17.6.3.");

    if (pWallDist != null && pWallDist.AsDouble() > maxWallDistFt)
        TaskDialog.Show("NFPA 72 S17.6.3 Violation",
            $"Smoke detector {pWallDist.AsDouble():F1} ft from wall > 15 ft maximum. "
            + "Ref: NFPA 72 S17.6.3.1.");
}""",
        ))

        # Fire extinguisher travel distance (IBC 906.3 -- 75 ft to class A, 50 ft to class B)
        samples.append(_s(
            "Validate IBC 906.3 fire extinguisher travel distance (75 ft to Class A, 50 ft to Class B:C)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 906.3: Maximum travel distance to portable fire extinguisher
// Class A (ordinary combustible): 75 ft
// Class B (flammable liquid): 50 ft
void ValidateFireExtinguisherTravel(FamilyInstance extinguisherInst)
{
    double maxDistClassAFt = 75.0; // Class A -- IBC 906.3.1
    double maxDistClassBFt = 50.0; // Class B -- IBC 906.3.2

    Parameter pMaxTravel = extinguisherInst.LookupParameter("Max Travel Distance");
    Parameter pClass     = extinguisherInst.LookupParameter("Extinguisher Class");
    if (pMaxTravel == null) return;

    double travel    = pMaxTravel.AsDouble();
    string extClass  = pClass != null ? pClass.AsString() : "A";
    double limit     = extClass.Contains("B") ? maxDistClassBFt : maxDistClassAFt;

    if (travel > limit)
    {
        TaskDialog.Show("IBC 906.3 Violation",
            $"Travel distance to Class {extClass} extinguisher {travel:F1} ft > {limit:F0} ft maximum. "
            + "Ref: IBC 906.3.");
    }
}""",
        ))

        # Fire rating of structural frame (IBC Table 601 -- by construction type)
        for (construction_type, beam_hr, column_hr, desc) in [
            ("Type I-A", 3, 3, "IBC Table 601: Type I-A structural frame 3-hr"),
            ("Type I-B", 2, 2, "IBC Table 601: Type I-B structural frame 2-hr"),
            ("Type II-A", 1, 1, "IBC Table 601: Type II-A structural frame 1-hr"),
            ("Type II-B", 0, 0, "IBC Table 601: Type II-B unprotected"),
        ]:
            samples.append(_s(
                f"Validate IBC Table 601 structural frame fire-resistance rating for {construction_type}",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// {desc}
// Beam/girder: {beam_hr}-hr, Column: {column_hr}-hr
void ValidateStructuralFrameRating_{construction_type.replace(' ', '_').replace('-', '_')}(FamilyInstance memberInst)
{{
    double requiredBeamHr   = {float(beam_hr)};
    double requiredColumnHr = {float(column_hr)};

    Parameter pMemberType   = memberInst.LookupParameter("Structural Member Type");
    Parameter pRating       = memberInst.LookupParameter("Fire Rating (hr)");
    Parameter pConstrType   = memberInst.LookupParameter("Construction Type");
    if (pRating == null || pConstrType == null) return;

    if (pConstrType.AsString() != "{construction_type}") return;

    double rating   = pRating.AsDouble();
    string memType  = pMemberType != null ? pMemberType.AsString() : "Beam";
    double required = memType == "Column" ? requiredColumnHr : requiredBeamHr;

    if (rating < required)
    {{
        TaskDialog.Show("IBC Table 601 Violation",
            $"{{memType}} fire rating {{rating}} hr < required {{required}} hr for {construction_type}. "
            + "Ref: {desc}");
    }}
}}""",
            ))

        # Fire damper in duct penetration (IMC 607 / IBC 716)
        samples.append(_s(
            "Validate IBC 716.5 fire damper requirement for duct penetrations of fire-rated walls",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 716.5: Ducts penetrating fire-rated walls require fire dampers
// Damper rating must be at least the wall rating
void ValidateFireDamper(FamilyInstance ductInst)
{
    Parameter pWallRating    = ductInst.LookupParameter("Penetrated Wall Rating (hr)");
    Parameter pHasDamper     = ductInst.LookupParameter("Has Fire Damper");
    Parameter pDamperRating  = ductInst.LookupParameter("Fire Damper Rating (hr)");
    if (pWallRating == null) return;

    double wallRating = pWallRating.AsDouble();
    if (wallRating <= 0) return;

    bool hasDamper = pHasDamper != null && pHasDamper.AsInteger() == 1;
    if (!hasDamper)
    {
        TaskDialog.Show("IBC 716.5 Violation",
            $"Duct penetrating {wallRating}-hr wall requires a fire damper. "
            + "Ref: IBC 716.5.");
        return;
    }

    if (pDamperRating != null && pDamperRating.AsDouble() < wallRating)
    {
        TaskDialog.Show("IBC 716.5 Violation",
            $"Fire damper rating {pDamperRating.AsDouble()} hr is less than wall rating {wallRating} hr. "
            + "Ref: IBC 716.5.");
    }
}""",
        ))

        # Corridor fire rating (IBC 1020.1 -- 1-hr rated corridor if >10 occupants)
        samples.append(_s(
            "Validate IBC 1020.1 fire-resistance rating for exit access corridors serving >10 occupants",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1020.1: Exit access corridors must be of 1-hr fire-resistance-rated construction
// when they serve an occupant load of more than 10 persons
// Exception: in fully sprinklered buildings, rating not required in some occupancies
void ValidateCorridorFireRating(FamilyInstance corridorInst)
{
    Parameter pOccupants  = corridorInst.LookupParameter("Served Occupant Load");
    Parameter pRating     = corridorInst.LookupParameter("Fire Rating (hr)");
    Parameter pSprinklered = corridorInst.LookupParameter("Sprinkler System");
    if (pOccupants == null || pRating == null) return;

    double occupants  = pOccupants.AsDouble();
    double rating     = pRating.AsDouble();
    bool spr          = pSprinklered != null && pSprinklered.AsInteger() == 1;

    if (occupants > 10 && !spr && rating < 1.0)
    {
        TaskDialog.Show("IBC 1020.1 Violation",
            $"Exit access corridor serving {occupants:F0} occupants requires 1-hr rating. "
            + $"Provided: {rating} hr (non-sprinklered). "
            + "Ref: IBC 1020.1.");
    }
}""",
        ))

        # Fire wall vs fire barrier distinction (IBC 706 vs 707)
        samples.append(_s(
            "Validate IBC 706.2 fire wall continuity -- must extend from foundation to 30 in above roof",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 706.2: Fire walls must extend from foundation through the roof
// and project 30 in above the roof unless the roof is non-combustible
void ValidateFireWallContinuity(FamilyInstance fireWallInst)
{{
    double minParapetFt = {30 * IN_TO_FT:.6f}; // 30 in above roof -- IBC 706.6

    Parameter pIsFireWall     = fireWallInst.LookupParameter("Is Fire Wall");
    Parameter pExtendsFdn     = fireWallInst.LookupParameter("Extends to Foundation");
    Parameter pParapetHeight  = fireWallInst.LookupParameter("Parapet Height");
    Parameter pRoofNonCombust = fireWallInst.LookupParameter("Adjacent Roof Non-Combustible");
    if (pIsFireWall == null || pIsFireWall.AsInteger() != 1) return;

    if (pExtendsFdn != null && pExtendsFdn.AsInteger() != 1)
    {{
        TaskDialog.Show("IBC 706.2 Violation",
            "Fire wall must extend continuously from the foundation. "
            + "Ref: IBC 706.2.");
    }}

    bool roofNonCombust = pRoofNonCombust != null && pRoofNonCombust.AsInteger() == 1;
    if (!roofNonCombust && pParapetHeight != null && pParapetHeight.AsDouble() < minParapetFt)
    {{
        TaskDialog.Show("IBC 706.6 Violation",
            $"Fire wall parapet {{pParapetHeight.AsDouble() * 12.0:F2}} in < required 30 in above roof. "
            + "Ref: IBC 706.6.");
    }}
}}""",
        ))

        # Area separation wall openings (IBC 706.8 -- protected openings only)
        samples.append(_s(
            "Validate IBC 706.8 fire wall opening protection -- no unprotected openings permitted",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 706.8: Openings in fire walls must be protected with fire door assemblies
// No unprotected openings are permitted in fire walls
void ValidateFireWallOpenings(FamilyInstance openingInst)
{
    Parameter pInFireWall   = openingInst.LookupParameter("In Fire Wall");
    Parameter pIsProtected  = openingInst.LookupParameter("Is Protected Opening");
    Parameter pFireDoorRating = openingInst.LookupParameter("Fire Door Rating (hr)");
    Parameter pWallRating   = openingInst.LookupParameter("Wall Fire Rating (hr)");
    if (pInFireWall == null || pInFireWall.AsInteger() != 1) return;

    bool isProtected = pIsProtected != null && pIsProtected.AsInteger() == 1;
    if (!isProtected)
    {
        TaskDialog.Show("IBC 706.8 Violation",
            "Unprotected opening in fire wall is not permitted. "
            + "Ref: IBC 706.8.");
        return;
    }

    if (pFireDoorRating != null && pWallRating != null)
    {
        double doorRating = pFireDoorRating.AsDouble();
        double wallRating = pWallRating.AsDouble();
        if (doorRating < wallRating * 0.75)
        {
            TaskDialog.Show("IBC 706.8 Violation",
                $"Fire door rating {doorRating} hr is insufficient for {wallRating} hr fire wall. "
                + "Ref: IBC 706.8.");
        }
    }
}""",
        ))

        # Sprinkler system requirement by building area (IBC 903.2)
        samples.append(_s(
            "Validate IBC 903.3 automatic sprinkler system installation standards (NFPA 13 for commercial)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 903.3: Sprinkler systems shall be installed per NFPA 13 (commercial)
// or NFPA 13R / 13D for residential occupancies
// Check whether building area exceeds threshold requiring sprinklers
void ValidateSprinklerRequired(FamilyInstance buildingInst)
{
    Parameter pOccupancy = buildingInst.LookupParameter("Occupancy Group");
    Parameter pArea      = buildingInst.LookupParameter("Total Floor Area (sq ft)");
    Parameter pSpr       = buildingInst.LookupParameter("Sprinkler System");
    if (pOccupancy == null || pArea == null) return;

    string occ    = pOccupancy.AsString();
    double area   = pArea.AsDouble();
    bool hasSpr   = pSpr != null && pSpr.AsInteger() == 1;

    // IBC 903.2.8: S-1 storage > 12,000 sq ft requires sprinklers (simplified)
    bool required = false;
    if (occ == "S-1" && area > 12000) required = true;
    // IBC 903.2.1.1: A occupancy > 12,000 sq ft sprinkler required
    if (occ.StartsWith("A") && area > 12000) required = true;

    if (required && !hasSpr)
    {
        TaskDialog.Show("IBC 903.2 Violation",
            $"{occ} occupancy with {area:F0} sq ft requires automatic sprinkler system. "
            + "Ref: IBC 903.2.");
    }
}""",
        ))

        # Interior finish flame spread (IBC Table 803.13 -- Class A, B, C by occupancy)
        samples.append(_s(
            "Validate IBC Table 803.13 interior finish flame spread index for exit enclosures (Class A required)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC Table 803.13: Interior wall/ceiling finish in exit enclosures must be Class A
// Class A: Flame spread 0-25, Smoke developed 0-450
// Class B: Flame spread 26-75
// Class C: Flame spread 76-200
void ValidateInteriorFinishClass(FamilyInstance wallInst)
{
    Parameter pInExit    = wallInst.LookupParameter("In Exit Enclosure");
    Parameter pFlameSpd  = wallInst.LookupParameter("Flame Spread Index");
    Parameter pSmokeDev  = wallInst.LookupParameter("Smoke Developed Index");
    if (pInExit == null || pInExit.AsInteger() != 1) return;

    if (pFlameSpd != null)
    {
        double fs = pFlameSpd.AsDouble();
        if (fs > 25)
        {
            TaskDialog.Show("IBC Table 803.13 Violation",
                $"Interior finish flame spread index {fs:F0} exceeds Class A limit of 25 "
                + "for exit enclosure. "
                + "Ref: IBC Table 803.13.");
        }
    }
    if (pSmokeDev != null && pSmokeDev.AsDouble() > 450)
    {
        TaskDialog.Show("IBC Table 803.13 Violation",
            $"Smoke developed index {pSmokeDev.AsDouble():F0} exceeds 450 Class A limit. "
            + "Ref: IBC Table 803.13.");
    }
}""",
        ))

        # Concealed space fire blocking (IBC 718 -- 10 ft max horizontal run)
        samples.append(_s(
            "Validate IBC 718.2 fire blocking in concealed spaces -- 10 ft maximum horizontal run",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 718.2: Fire blocking required in concealed stud walls and partitions
// at ceiling and floor levels, and every 10 ft (horizontal)
void ValidateFireBlocking(FamilyInstance wallInst)
{
    double maxRunFt = 10.0; // 10 ft -- IBC 718.2.1

    Parameter pHasConcealed = wallInst.LookupParameter("Has Concealed Space");
    Parameter pRunLength    = wallInst.LookupParameter("Max Horizontal Run Without Fire Blocking");
    if (pHasConcealed == null || pHasConcealed.AsInteger() != 1) return;

    if (pRunLength != null && pRunLength.AsDouble() > maxRunFt)
    {
        TaskDialog.Show("IBC 718.2 Violation",
            $"Concealed space horizontal run {pRunLength.AsDouble():F1} ft > 10 ft max without fire blocking. "
            + "Ref: IBC 718.2.1.");
    }
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # ADA / ICC A117.1 -- Accessibility
    # ------------------------------------------------------------------

    def _accessibility(self) -> List[SAMPLE]:
        samples = []

        # Ramp slope: 1:12 max (ADA 405.2)
        for (run, rise, desc) in [
            (12, 1,   "1:12 slope (compliant maximum)"),
            (16, 1,   "1:16 slope (compliant)"),
            (10, 1,   "1:10 slope (violation)"),
            (8,  1,   "1:8 slope (violation)"),
            (20, 1,   "1:20 slope (compliant)"),
        ]:
            slope = rise / run
            samples.append(_s(
                f"Validate ADA 405.2 accessible ramp slope: {desc}",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 405.2: Running slope of accessible ramps shall not exceed 1:12
// {desc}
void ValidateRampSlope(FamilyInstance rampInst)
{{
    double maxSlope = 1.0 / 12.0; // ADA 405.2

    Parameter pRise = rampInst.LookupParameter("Ramp Rise");
    Parameter pRun  = rampInst.LookupParameter("Ramp Run");
    if (pRise == null || pRun == null) return;

    double rise  = pRise.AsDouble();
    double run   = pRun.AsDouble();
    double slope = (run > 0) ? rise / run : 1.0;

    if (slope > maxSlope)
    {{
        TaskDialog.Show("ADA 405.2 Violation",
            $"Ramp slope 1:{{(run / rise):F1}} ({{slope:P1}}) exceeds maximum 1:12. "
            + "Ref: ADA 405.2.");
    }}
}}""",
            ))

        # Ramp cross-slope: 1:48 max (ADA 405.3)
        samples.append(_s(
            "Validate ADA 405.3 ramp cross-slope maximum (1:48)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 405.3: Cross slope of accessible ramps shall not exceed 1:48
void ValidateRampCrossSlope(FamilyInstance rampInst)
{
    double maxCrossSlope = 1.0 / 48.0; // ADA 405.3

    Parameter pCrossSlope = rampInst.LookupParameter("Cross Slope");
    if (pCrossSlope == null) return;

    double cs = pCrossSlope.AsDouble();
    if (cs > maxCrossSlope)
    {
        TaskDialog.Show("ADA 405.3 Violation",
            $"Ramp cross slope 1:{(1.0/cs):F1} ({cs:P1}) exceeds maximum 1:48. "
            + "Ref: ADA 405.3.");
    }
}""",
        ))

        # Ramp landing size: 60x60 in minimum at top and bottom (ADA 405.7)
        samples.append(_s(
            "Validate ADA 405.7 ramp landing dimensions (60 in x 60 in minimum)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 405.7: Ramp landings at top and bottom must be at least 60 in x 60 in
void ValidateRampLanding(FamilyInstance rampInst)
{{
    double minLandingFt = {60 * IN_TO_FT:.6f}; // 60 in -- ADA 405.7

    Parameter pLandW = rampInst.LookupParameter("Landing Width");
    Parameter pLandD = rampInst.LookupParameter("Landing Depth");
    if (pLandW == null || pLandD == null) return;

    double landW = pLandW.AsDouble();
    double landD = pLandD.AsDouble();

    if (landW < minLandingFt || landD < minLandingFt)
    {{
        TaskDialog.Show("ADA 405.7 Violation",
            $"Ramp landing {{landW * 12.0:F1}} in x {{landD * 12.0:F1}} in is below "
            + "required 60 in x 60 in minimum. "
            + "Ref: ADA 405.7.");
    }}
}}""",
        ))

        # Grab bar position: ADA 609 (33-36 in AFF, 42 in side wall, 36 in back wall)
        for (bar_type, req_in, param_name, code) in [
            ("side wall (toilet)",       42, "Grab Bar Length Side",  "ADA 609.4 / ICC A117.1 S604.5"),
            ("back wall (toilet)",       36, "Grab Bar Length Back",  "ADA 609.4 / ICC A117.1 S604.5"),
            ("shower (horizontal)",      36, "Grab Bar Length Shower","ADA 608.3"),
        ]:
            req_ft = req_in * IN_TO_FT
            samples.append(_s(
                f"Validate {code} grab bar minimum length: {bar_type}",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// {code}: {bar_type} grab bar minimum length {req_in} in
void ValidateGrabBarLength_{bar_type.split(' ')[0]}(FamilyInstance grabBarInst)
{{
    double minLengthFt = {req_ft:.6f}; // {req_in} in -- {code}

    Parameter pLength = grabBarInst.LookupParameter("{param_name}");
    if (pLength == null)
        pLength = grabBarInst.LookupParameter("Grab Bar Length");
    if (pLength == null) return;

    double length = pLength.AsDouble();
    if (length < minLengthFt)
    {{
        TaskDialog.Show("{code} Violation",
            $"Grab bar length {{length * 12.0:F2}} in is less than required {req_in} in "
            + "for {bar_type}. "
            + "Ref: {code}");
    }}
}}""",
            ))

        # Grab bar mounting height (ADA 609.4 -- 33-36 in AFF)
        samples.append(_s(
            "Validate ADA 609.4 grab bar mounting height (33 in to 36 in above finish floor)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 609.4: Grab bars installed at 33 in to 36 in above finish floor
void ValidateGrabBarHeight(FamilyInstance grabBarInst)
{{
    double minHtFt = {33 * IN_TO_FT:.6f}; // 33 in -- ADA 609.4
    double maxHtFt = {36 * IN_TO_FT:.6f}; // 36 in -- ADA 609.4

    Parameter pHt = grabBarInst.LookupParameter("Mounting Height");
    if (pHt == null) return;

    double ht = pHt.AsDouble();
    if (ht < minHtFt || ht > maxHtFt)
    {{
        TaskDialog.Show("ADA 609.4 Violation",
            $"Grab bar height {{ht * 12.0:F2}} in AFF is outside required 33-36 in range. "
            + "Ref: ADA 609.4.");
    }}
}}""",
        ))

        # Accessible route clear width: 36 in min, 44 in for corridors (ADA 403.5)
        for (route, min_in, code) in [
            ("accessible route (general)", 36, "ADA 403.5.1"),
            ("accessible corridor",        44, "IBC 1020.2 / ADA 403.5.1"),
            ("wheelchair turning space",   60, "ADA 304.3 (60 in diameter turn)"),
        ]:
            min_ft = min_in * IN_TO_FT
            samples.append(_s(
                f"Validate {code} minimum clear width for {route}",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// {code}: {route} minimum clear width {min_in} in
void ValidateClearWidth_{route.split(' ')[0]}(FamilyInstance element)
{{
    double minClearFt = {min_ft:.6f}; // {min_in} in -- {code}

    Parameter pClearW = element.LookupParameter("Clear Width");
    if (pClearW == null)
        pClearW = element.LookupParameter("Corridor Width");
    if (pClearW == null) return;

    double clearW = pClearW.AsDouble();
    if (clearW < minClearFt)
    {{
        TaskDialog.Show("{code} Violation",
            $"Clear width {{clearW * 12.0:F2}} in is less than required {min_in} in "
            + "for {route}. "
            + "Ref: {code}");
    }}
}}""",
            ))

        # Parking space dimensions: ADA 502 (96 in wide, 240 in deep with 60 in access aisle)
        samples.append(_s(
            "Validate ADA 502 accessible parking space dimensions (96 in wide, 60 in access aisle)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 502.2: Accessible parking space -- 96 in (8 ft) wide minimum
// ADA 502.3: Access aisle -- 60 in wide minimum adjacent to space
// ADA 502.4: Floor or ground surface -- slope max 1:48 in all directions
void ValidateAccessibleParking(FamilyInstance spaceInst)
{{
    double minSpaceWidthFt = {96 * IN_TO_FT:.6f};  // 96 in -- ADA 502.2
    double minAisleFt      = {60 * IN_TO_FT:.6f};  // 60 in access aisle -- ADA 502.3
    double minLengthFt     = {240 * IN_TO_FT:.6f}; // 240 in (20 ft) depth -- ADA 502.2
    double maxSlopeFt      = 1.0 / 48.0;           // ADA 502.4

    Parameter pWidth  = spaceInst.LookupParameter("Stall Width");
    Parameter pLength = spaceInst.LookupParameter("Stall Length");
    Parameter pAisle  = spaceInst.LookupParameter("Access Aisle Width");
    Parameter pSlope  = spaceInst.LookupParameter("Floor Slope");

    if (pWidth != null && pWidth.AsDouble() < minSpaceWidthFt)
        TaskDialog.Show("ADA 502.2 Violation",
            $"Parking stall width {{pWidth.AsDouble() * 12.0:F1}} in < 96 in min. Ref: ADA 502.2.");

    if (pAisle != null && pAisle.AsDouble() < minAisleFt)
        TaskDialog.Show("ADA 502.3 Violation",
            $"Access aisle {{pAisle.AsDouble() * 12.0:F1}} in < 60 in min. Ref: ADA 502.3.");

    if (pLength != null && pLength.AsDouble() < minLengthFt)
        TaskDialog.Show("ADA 502.2 Violation",
            $"Stall length {{pLength.AsDouble() * 12.0:F1}} in < 240 in min. Ref: ADA 502.2.");

    if (pSlope != null && pSlope.AsDouble() > maxSlopeFt)
        TaskDialog.Show("ADA 502.4 Violation",
            $"Floor slope {{pSlope.AsDouble():P2}} exceeds 1:48 max. Ref: ADA 502.4.");
}}""",
        ))

        # Knee clearance (ADA 306 -- 27 in high, 30 in wide, 19 in deep)
        samples.append(_s(
            "Validate ADA 306 knee clearance dimensions (27 in high, 30 in wide, 19 in deep minimum)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 306: Knee clearance required under accessible work surfaces / counters
// Min height: 27 in, Min width: 30 in, Min depth: 19 in
void ValidateKneeClearance(FamilyInstance surfaceInst)
{{
    double minHeightFt = {27 * IN_TO_FT:.6f}; // 27 in -- ADA 306.3.1
    double minWidthFt  = {30 * IN_TO_FT:.6f}; // 30 in -- ADA 306.2
    double minDepthFt  = {19 * IN_TO_FT:.6f}; // 19 in -- ADA 306.2

    Parameter pKneeH = surfaceInst.LookupParameter("Knee Clearance Height");
    Parameter pKneeW = surfaceInst.LookupParameter("Knee Clearance Width");
    Parameter pKneeD = surfaceInst.LookupParameter("Knee Clearance Depth");

    if (pKneeH != null && pKneeH.AsDouble() < minHeightFt)
        TaskDialog.Show("ADA 306 Violation",
            $"Knee clearance height {{pKneeH.AsDouble() * 12.0:F2}} in < 27 in. Ref: ADA 306.3.1.");

    if (pKneeW != null && pKneeW.AsDouble() < minWidthFt)
        TaskDialog.Show("ADA 306 Violation",
            $"Knee clearance width {{pKneeW.AsDouble() * 12.0:F2}} in < 30 in. Ref: ADA 306.2.");

    if (pKneeD != null && pKneeD.AsDouble() < minDepthFt)
        TaskDialog.Show("ADA 306 Violation",
            $"Knee clearance depth {{pKneeD.AsDouble() * 12.0:F2}} in < 19 in. Ref: ADA 306.2.");
}}""",
        ))

        # Reach range (ADA 308 -- forward/side reach 15-48 in AFF)
        samples.append(_s(
            "Validate ADA 308 reach range for accessible controls (15 in min, 48 in max AFF)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 308.2: Forward reach range 15 in (min) to 48 in (max) above finish floor
// ADA 308.3: Side reach range 15 in (min) to 48 in (max) above finish floor
void ValidateReachRange(FamilyInstance controlInst)
{{
    double minReachFt = {15 * IN_TO_FT:.6f}; // 15 in -- ADA 308.2/308.3
    double maxReachFt = {48 * IN_TO_FT:.6f}; // 48 in -- ADA 308.2/308.3

    Parameter pReachHt = controlInst.LookupParameter("Mounting Height");
    if (pReachHt == null) return;

    double ht = pReachHt.AsDouble();
    if (ht < minReachFt || ht > maxReachFt)
    {{
        TaskDialog.Show("ADA 308 Violation",
            $"Control mounting height {{ht * 12.0:F2}} in AFF is outside "
            + "the 15-48 in accessible reach range. "
            + "Ref: ADA 308.2 / ADA 308.3.");
    }}
}}""",
        ))

        # Floor surface slope on accessible route (ADA 402.2 -- 1:48 max in all directions)
        samples.append(_s(
            "Validate ADA 402.2 accessible route floor surface slope (1:48 max in any direction)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 402.2: Floor surfaces of accessible routes must be firm, stable, and slip-resistant
// Running slope: 1:20 max on level paths, cross slope: 1:48 max
void ValidateAccessibleFloorSlope(FamilyInstance floorInst)
{
    double maxRunSlope  = 1.0 / 20.0; // 1:20 running (if not ramp) -- ADA 402.2
    double maxCrossSlope = 1.0 / 48.0; // 1:48 cross slope -- ADA 402.2

    Parameter pRunSlope   = floorInst.LookupParameter("Running Slope");
    Parameter pCrossSlope = floorInst.LookupParameter("Cross Slope");
    Parameter pIsAccessible = floorInst.LookupParameter("On Accessible Route");
    if (pIsAccessible == null || pIsAccessible.AsInteger() != 1) return;

    if (pRunSlope != null && pRunSlope.AsDouble() > maxRunSlope)
        TaskDialog.Show("ADA 402.2 Violation",
            $"Running slope {pRunSlope.AsDouble():P2} > 1:20 maximum on accessible route. "
            + "Ref: ADA 402.2.");

    if (pCrossSlope != null && pCrossSlope.AsDouble() > maxCrossSlope)
        TaskDialog.Show("ADA 402.2 Violation",
            $"Cross slope {pCrossSlope.AsDouble():P2} > 1:48 maximum on accessible route. "
            + "Ref: ADA 402.2.");
}""",
        ))

        # Accessible parking van space (ADA 502.2 -- 132 in wide with 60 in aisle OR 96 in wide with 96 in aisle)
        samples.append(_s(
            "Validate ADA 502.2 van-accessible parking space (132 in wide or 96 in with 96 in access aisle)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 502.2: Van-accessible spaces -- one per 6 accessible spaces required
// Option A: 132 in (11 ft) wide with 60 in access aisle
// Option B: 96 in (8 ft) wide with 96 in access aisle
void ValidateVanAccessibleParking(FamilyInstance spaceInst)
{{
    double optionAWidthFt = {132 * IN_TO_FT:.6f}; // 132 in -- ADA 502.2
    double optionAaisleFt = {60  * IN_TO_FT:.6f};  // 60 in aisle
    double optionBWidthFt = {96  * IN_TO_FT:.6f};  // 96 in -- ADA 502.2
    double optionBAisleFt = {96  * IN_TO_FT:.6f};  // 96 in aisle

    Parameter pIsVan   = spaceInst.LookupParameter("Is Van Accessible");
    Parameter pWidth   = spaceInst.LookupParameter("Stall Width");
    Parameter pAisle   = spaceInst.LookupParameter("Access Aisle Width");
    if (pIsVan == null || pIsVan.AsInteger() != 1) return;
    if (pWidth == null || pAisle == null) return;

    double w = pWidth.AsDouble();
    double a = pAisle.AsDouble();

    bool optA = w >= optionAWidthFt && a >= optionAaisleFt;
    bool optB = w >= optionBWidthFt && a >= optionBAisleFt;

    if (!optA && !optB)
    {{
        TaskDialog.Show("ADA 502.2 Violation",
            $"Van-accessible stall ({{w * 12.0:F1}} in wide, {{a * 12.0:F1}} in aisle) does not meet "
            + "Option A (132/60 in) or Option B (96/96 in) requirements. "
            + "Ref: ADA 502.2.");
    }}
}}""",
        ))

        # Tactile warning surface at curb ramp (ADA 406.8 -- truncated dome field)
        samples.append(_s(
            "Validate ADA 406.8 detectable warning surface at curb ramp (truncated domes, 24 in deep min)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 406.8: Curb ramps must have detectable warning surface
// Width: full width of ramp, Depth: 24 in (min) in direction of travel
// Truncated dome pattern per ADA 705
void ValidateDetectableWarning(FamilyInstance curbRampInst)
{{
    double minDepthFt = {24 * IN_TO_FT:.6f}; // 24 in -- ADA 406.8

    Parameter pHasDW     = curbRampInst.LookupParameter("Has Detectable Warning");
    Parameter pDWDepth   = curbRampInst.LookupParameter("Detectable Warning Depth");
    Parameter pRampWidth = curbRampInst.LookupParameter("Ramp Width");
    Parameter pDWWidth   = curbRampInst.LookupParameter("Detectable Warning Width");

    if (pHasDW == null || pHasDW.AsInteger() != 1)
    {{
        TaskDialog.Show("ADA 406.8 Violation",
            "Curb ramp lacks required detectable warning surface. "
            + "Ref: ADA 406.8.");
        return;
    }}

    if (pDWDepth != null && pDWDepth.AsDouble() < minDepthFt)
        TaskDialog.Show("ADA 406.8 Violation",
            $"Detectable warning depth {{pDWDepth.AsDouble() * 12.0:F2}} in < 24 in minimum. "
            + "Ref: ADA 406.8.");

    if (pRampWidth != null && pDWWidth != null && pDWWidth.AsDouble() < pRampWidth.AsDouble())
        TaskDialog.Show("ADA 406.8 Violation",
            "Detectable warning must span the full width of the curb ramp. "
            + "Ref: ADA 406.8.");
}}""",
        ))

        # Protruding objects ADA 307 -- objects between 27 and 80 in AFF must not protrude > 4 in
        samples.append(_s(
            "Validate ADA 307.2 protruding object limit -- wall-mounted objects 27-80 in AFF may not protrude more than 4 in",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 307.2: Objects with leading edges between 27 in and 80 in AFF
// must not protrude more than 4 in from a wall into the circulation path
void ValidateProtrudingObject(FamilyInstance objectInst)
{{
    double minHeightFt  = {27 * IN_TO_FT:.6f}; // 27 in -- ADA 307.2
    double maxHeightFt  = {80 * IN_TO_FT:.6f}; // 80 in -- ADA 307.2
    double maxProtrudeFt = {4 * IN_TO_FT:.6f};  // 4 in -- ADA 307.2

    Parameter pLeadingEdge = objectInst.LookupParameter("Leading Edge Height");
    Parameter pProtrusion  = objectInst.LookupParameter("Protrusion from Wall");
    if (pLeadingEdge == null || pProtrusion == null) return;

    double edge = pLeadingEdge.AsDouble();
    if (edge >= minHeightFt && edge <= maxHeightFt)
    {{
        double protrusion = pProtrusion.AsDouble();
        if (protrusion > maxProtrudeFt)
        {{
            TaskDialog.Show("ADA 307.2 Violation",
                $"Wall-mounted object protrudes {{protrusion * 12.0:F2}} in at {{edge * 12.0:F1}} in AFF, "
                + "exceeding 4 in maximum. "
                + "Ref: ADA 307.2.");
        }}
    }}
}}""",
        ))

        # Accessible toilet stall clear floor space (ADA 604.3 -- 60 in wide x 56-59 in deep)
        samples.append(_s(
            "Validate ADA 604.3 accessible toilet compartment clear floor space (60 in wide x 56 in deep min)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 604.3: Accessible toilet compartment dimensions
// Width: 60 in minimum, Depth: 56 in (wall-hung) or 59 in (floor-mount) minimum
void ValidateToiletStallDimensions(FamilyInstance stallInst)
{{
    double minWidthFt    = {60 * IN_TO_FT:.6f}; // 60 in -- ADA 604.3
    double minDepthWHFt  = {56 * IN_TO_FT:.6f}; // 56 in wall-hung -- ADA 604.3
    double minDepthFlrFt = {59 * IN_TO_FT:.6f}; // 59 in floor-mount -- ADA 604.3

    Parameter pWidth     = stallInst.LookupParameter("Stall Width");
    Parameter pDepth     = stallInst.LookupParameter("Stall Depth");
    Parameter pIsWallHung = stallInst.LookupParameter("Is Wall-Hung Fixture");
    if (pWidth == null || pDepth == null) return;

    double width   = pWidth.AsDouble();
    double depth   = pDepth.AsDouble();
    bool wallHung  = pIsWallHung != null && pIsWallHung.AsInteger() == 1;
    double minDepth = wallHung ? minDepthWHFt : minDepthFlrFt;

    if (width < minWidthFt)
        TaskDialog.Show("ADA 604.3 Violation",
            $"Toilet stall width {{width * 12.0:F2}} in < 60 in minimum. Ref: ADA 604.3.");

    if (depth < minDepth)
        TaskDialog.Show("ADA 604.3 Violation",
            $"Toilet stall depth {{depth * 12.0:F2}} in < {{minDepth * 12.0:F0}} in minimum. Ref: ADA 604.3.");
}}""",
        ))

        # Elevator cab dimensions (ADA 407.4 -- 80 in wide x 51 in deep minimum)
        samples.append(_s(
            "Validate ADA 407.4 elevator cab inside clear dimensions (80 in wide x 51 in deep minimum)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 407.4.1: Elevator cab inside dimensions minimum 80 in wide x 51 in deep
// (for 2500-lb capacity elevator serving accessible route)
void ValidateElevatorCabDimensions(FamilyInstance elevatorInst)
{{
    double minWidthFt = {80 * IN_TO_FT:.6f}; // 80 in -- ADA 407.4.1
    double minDepthFt = {51 * IN_TO_FT:.6f}; // 51 in -- ADA 407.4.1

    Parameter pWidth = elevatorInst.LookupParameter("Cab Width");
    Parameter pDepth = elevatorInst.LookupParameter("Cab Depth");

    if (pWidth != null && pWidth.AsDouble() < minWidthFt)
        TaskDialog.Show("ADA 407.4.1 Violation",
            $"Elevator cab width {{pWidth.AsDouble() * 12.0:F2}} in < 80 in minimum. "
            + "Ref: ADA 407.4.1.");

    if (pDepth != null && pDepth.AsDouble() < minDepthFt)
        TaskDialog.Show("ADA 407.4.1 Violation",
            $"Elevator cab depth {{pDepth.AsDouble() * 12.0:F2}} in < 51 in minimum. "
            + "Ref: ADA 407.4.1.");
}}""",
        ))

        # Countertop height for accessible work surface (ADA 902 -- 28-34 in AFF)
        samples.append(_s(
            "Validate ADA 902.3 accessible counter height (28 in minimum, 34 in maximum AFF)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 902.3: Accessible dining surfaces and work surfaces
// Height range: 28 in to 34 in above finish floor
void ValidateAccessibleCounterHeight(FamilyInstance counterInst)
{{
    double minHtFt = {28 * IN_TO_FT:.6f}; // 28 in -- ADA 902.3
    double maxHtFt = {34 * IN_TO_FT:.6f}; // 34 in -- ADA 902.3

    Parameter pHt           = counterInst.LookupParameter("Counter Height");
    Parameter pIsAccessible = counterInst.LookupParameter("Is Accessible Counter");
    if (pIsAccessible == null || pIsAccessible.AsInteger() != 1) return;

    if (pHt == null) return;
    double ht = pHt.AsDouble();
    if (ht < minHtFt || ht > maxHtFt)
    {{
        TaskDialog.Show("ADA 902.3 Violation",
            $"Accessible counter height {{ht * 12.0:F2}} in AFF is outside required 28-34 in range. "
            + "Ref: ADA 902.3.");
    }}
}}""",
        ))

        # Ramp edge protection (ADA 405.9 -- edge protection 2 in curb or rail)
        samples.append(_s(
            "Validate ADA 405.9 ramp edge protection -- 2 in minimum curb or railing required",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 405.9: Accessible ramps must have edge protection on open sides
// Curb: 2 in minimum, or rail/barrier system
void ValidateRampEdgeProtection(FamilyInstance rampInst)
{{
    double minCurbFt = {2 * IN_TO_FT:.6f}; // 2 in minimum curb -- ADA 405.9

    Parameter pHasEdge    = rampInst.LookupParameter("Has Edge Protection");
    Parameter pEdgeType   = rampInst.LookupParameter("Edge Protection Type");
    Parameter pCurbHeight = rampInst.LookupParameter("Curb Height");
    if (pHasEdge == null || pHasEdge.AsInteger() != 1)
    {{
        TaskDialog.Show("ADA 405.9 Violation",
            "Accessible ramp lacks required edge protection on open sides. "
            + "Ref: ADA 405.9.");
        return;
    }}

    string edgeType = pEdgeType != null ? pEdgeType.AsString() : "Curb";
    if (edgeType == "Curb" && pCurbHeight != null && pCurbHeight.AsDouble() < minCurbFt)
    {{
        TaskDialog.Show("ADA 405.9 Violation",
            $"Ramp curb height {{pCurbHeight.AsDouble() * 12.0:F2}} in < 2 in minimum. "
            + "Ref: ADA 405.9.");
    }}
}}""",
        ))

        # Accessible parking count (ADA 208 -- 1 per 25 standard spaces up to first 100)
        samples.append(_s(
            "Validate ADA 208.2 minimum number of accessible parking spaces in a parking facility",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ADA 208.2: Minimum accessible spaces
// 1-25 total: 1 accessible, 26-50: 2, 51-75: 3, 76-100: 4, etc.
void ValidateAccessibleParkingCount(FamilyInstance lotInst)
{
    Parameter pTotal  = lotInst.LookupParameter("Total Parking Spaces");
    Parameter pAccess = lotInst.LookupParameter("Accessible Parking Spaces");
    if (pTotal == null || pAccess == null) return;

    int total    = (int)pTotal.AsDouble();
    int provided = (int)pAccess.AsDouble();
    int required;

    if      (total <= 25)  required = 1;
    else if (total <= 50)  required = 2;
    else if (total <= 75)  required = 3;
    else if (total <= 100) required = 4;
    else if (total <= 150) required = 5;
    else if (total <= 200) required = 6;
    else                   required = 6 + (total - 200) / 100 + 1;

    if (provided < required)
    {
        TaskDialog.Show("ADA 208.2 Violation",
            $"Parking lot with {total} spaces requires {required} accessible spaces; "
            + $"{provided} provided. "
            + "Ref: ADA 208.2.");
    }
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # IBC 1208 -- Minimum room areas and dimensions
    # ------------------------------------------------------------------

    def _room_areas(self) -> List[SAMPLE]:
        samples = []

        # Minimum habitable room area (IBC 1208.3 -- 70 sq ft, 7 ft min dimension)
        samples.append(_s(
            "Validate IBC 1208.3 minimum habitable room area (70 sq ft) and dimension (7 ft)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1208.3: Every habitable room must have >= 70 sq ft area
// and no horizontal dimension less than 7 ft
void ValidateHabitableRoomArea(FamilyInstance roomInst)
{
    double minAreaFt2    = 70.0;  // sq ft -- IBC 1208.3
    double minDimensionFt = 7.0;  // ft -- IBC 1208.3

    Parameter pArea   = roomInst.LookupParameter("Room Area");
    Parameter pWidth  = roomInst.LookupParameter("Room Width");
    Parameter pDepth  = roomInst.LookupParameter("Room Depth");

    if (pArea != null)
    {
        double area = pArea.AsDouble(); // sq ft
        if (area < minAreaFt2)
        {
            TaskDialog.Show("IBC 1208.3 Violation",
                $"Habitable room area {area:F1} sq ft is below required 70 sq ft. "
                + "Ref: IBC 1208.3.");
        }
    }

    if (pWidth != null && pWidth.AsDouble() < minDimensionFt)
        TaskDialog.Show("IBC 1208.3 Violation",
            $"Room width {pWidth.AsDouble() * 12.0:F1} in < 7 ft (84 in) minimum. "
            + "Ref: IBC 1208.3.");

    if (pDepth != null && pDepth.AsDouble() < minDimensionFt)
        TaskDialog.Show("IBC 1208.3 Violation",
            $"Room depth {pDepth.AsDouble() * 12.0:F1} in < 7 ft (84 in) minimum. "
            + "Ref: IBC 1208.3.");
}""",
        ))

        # Minimum ceiling height (IBC 1208.2 -- 7 ft 6 in habitable, 7 ft corridors)
        for (space_type, min_in, code) in [
            ("habitable room",        90, "IBC 1208.2 (7 ft 6 in = 90 in)"),
            ("corridor / hallway",    84, "IBC 1208.2 (7 ft 0 in = 84 in)"),
            ("bathroom / toilet room", 80, "IBC 1208.2 (6 ft 8 in = 80 in)"),
            ("mechanical room",       72, "IBC 1208.2 exception (6 ft 0 in)"),
        ]:
            min_ft = min_in * IN_TO_FT
            samples.append(_s(
                f"Validate IBC 1208.2 minimum ceiling height for {space_type}",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// {code}
void ValidateCeilingHeight_{space_type.split('/')[0].strip().replace(' ', '_')}(FamilyInstance roomInst)
{{
    double minCeilingFt = {min_ft:.6f}; // {min_in} in -- {code}

    Parameter pCeiling = roomInst.LookupParameter("Ceiling Height");
    if (pCeiling == null) return;

    double ceilingHt = pCeiling.AsDouble();
    if (ceilingHt < minCeilingFt)
    {{
        TaskDialog.Show("IBC 1208.2 Violation",
            $"Ceiling height {{ceilingHt * 12.0:F1}} in for {space_type} is below required "
            + $"{min_in} in. "
            + "Ref: {code}");
    }}
}}""",
            ))

        # Kitchen minimum dimensions (IRC R306 -- 5 ft x 8 ft minimum clear)
        samples.append(_s(
            "Validate IRC R306 kitchen minimum clear floor area (5 ft x 8 ft)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IRC R306: Kitchen work area minimum 5 ft x 8 ft clear floor
void ValidateKitchenMinimumDimensions(FamilyInstance kitchenInst)
{{
    double minWidthFt  = 5.0; // 5 ft -- IRC R306
    double minDepthFt  = 8.0; // 8 ft -- IRC R306

    Parameter pW = kitchenInst.LookupParameter("Clear Width");
    Parameter pD = kitchenInst.LookupParameter("Clear Depth");

    if (pW != null && pW.AsDouble() < minWidthFt)
        TaskDialog.Show("IRC R306 Violation",
            $"Kitchen clear width {{pW.AsDouble():F2}} ft < 5 ft minimum. Ref: IRC R306.");

    if (pD != null && pD.AsDouble() < minDepthFt)
        TaskDialog.Show("IRC R306 Violation",
            $"Kitchen clear depth {{pD.AsDouble():F2}} ft < 8 ft minimum. Ref: IRC R306.");
}}""",
        ))

        # Office minimum floor area per occupant (IBC Table 1004.1.2 -- 100 sq ft/person)
        for (occ_type, sf_per_person, desc) in [
            ("Business (offices)",        100,  "IBC Table 1004.5 business 100 sq ft/person"),
            ("Assembly (standing)",        5,   "IBC Table 1004.5 assembly standing 5 sq ft/person"),
            ("Assembly (fixed seats)",     15,  "IBC Table 1004.5 assembly 15 sq ft/person"),
            ("Educational (classroom)",    20,  "IBC Table 1004.5 classroom 20 sq ft/person"),
        ]:
            samples.append(_s(
                f"Validate IBC Table 1004.5 occupant load factor: {desc}",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// {desc}
// Max occupant load = floor area / {sf_per_person} sq ft per person
void ValidateOccupantLoad_{occ_type.split('(')[0].strip().replace(' ', '_')}(FamilyInstance roomInst)
{{
    double sfPerPerson = {float(sf_per_person):.1f}; // sq ft/person -- IBC Table 1004.5

    Parameter pArea         = roomInst.LookupParameter("Room Area");
    Parameter pOccupantLoad = roomInst.LookupParameter("Occupant Load");
    if (pArea == null) return;

    double area           = pArea.AsDouble(); // sq ft
    double maxOccupants   = area / sfPerPerson;

    if (pOccupantLoad != null)
    {{
        double declared = pOccupantLoad.AsDouble();
        if (declared > maxOccupants)
        {{
            TaskDialog.Show("IBC Table 1004.5 Violation",
                $"Declared occupant load {{declared:F0}} exceeds calculated maximum {{maxOccupants:F0}} "
                + $"({{{sf_per_person:.0f}}} sq ft/person for {occ_type}). "
                + "Ref: IBC Table 1004.5.");
        }}
    }}
}}""",
            ))

        # Gross floor area vs net leasable area (building efficiency ratio)
        samples.append(_s(
            "Calculate building efficiency ratio (net leasable area / gross floor area) and validate against target",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// Building programming check: efficiency ratio = net leasable area / gross floor area
// Typical targets: office 75-85%, residential 75-90%
void ValidateBuildingEfficiencyRatio(FamilyInstance buildingInst)
{
    double minEfficiencyOffice = 0.75; // 75% -- typical office
    double maxEfficiencyOffice = 0.90; // 90% -- maximum practical

    Parameter pGross  = buildingInst.LookupParameter("Gross Floor Area (sq ft)");
    Parameter pNet    = buildingInst.LookupParameter("Net Leasable Area (sq ft)");
    Parameter pOccType = buildingInst.LookupParameter("Occupancy Type");
    if (pGross == null || pNet == null) return;

    double gross     = pGross.AsDouble();
    double net       = pNet.AsDouble();
    double efficiency = (gross > 0) ? net / gross : 0;

    if (efficiency > maxEfficiencyOffice)
    {
        TaskDialog.Show("Programming Warning",
            $"Building efficiency {efficiency:P1} ({net:F0}/{gross:F0} sf) may be unrealistically high. "
            + "Verify program areas include circulation, walls, and mechanical.");
    }
    if (efficiency < minEfficiencyOffice)
    {
        TaskDialog.Show("Programming Warning",
            $"Building efficiency {efficiency:P1} is below 75% target. "
            + "Review for unusually high circulation or mechanical space ratios.");
    }
}""",
        ))

        # Daylight requirement by room type (IBC 1205 -- window area 8% of floor area)
        for (room_type, pct, code) in [
            ("habitable room",       8.0, "IBC 1205.2 (8% floor area glazing)"),
            ("commercial office",    2.0, "IBC 1205.1 (artificial light permitted, 2% minimum natural if provided)"),
        ]:
            samples.append(_s(
                f"Validate {code} glazing area requirement for {room_type}",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// {code}
void ValidateDaylightGlazing_{room_type.replace(' ', '_')}(FamilyInstance roomInst)
{{
    double minGlazingFraction = {pct / 100.0:.4f}; // {pct}% of floor area -- {code}

    Parameter pArea    = roomInst.LookupParameter("Room Area");
    Parameter pGlazing = roomInst.LookupParameter("Total Glazing Area");
    if (pArea == null || pGlazing == null) return;

    double area    = pArea.AsDouble();
    double glazing = pGlazing.AsDouble();
    double minGlaz = area * minGlazingFraction;

    if (glazing < minGlaz)
    {{
        TaskDialog.Show("{code.split('(')[0].strip()} Violation",
            $"{room_type} glazing area {{glazing:F2}} sq ft < required {{minGlaz:F2}} sq ft "
            + $"({pct}% of {{area:F1}} sq ft floor area). "
            + "Ref: {code}");
    }}
}}""",
            ))

        # Minimum toilet room area -- single occupancy ADA (ICC A117.1 S603)
        samples.append(_s(
            "Validate ICC A117.1 S603 single-occupancy accessible toilet room minimum dimensions",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ICC A117.1 S603: Single-user accessible toilet room
// Width: 60 in min, Depth: 60 in min (for turning radius)
void ValidateAccessibleToiletRoomSize(FamilyInstance roomInst)
{{
    double minWidthFt = {60 * IN_TO_FT:.6f}; // 60 in -- ICC A117.1 S603
    double minDepthFt = {60 * IN_TO_FT:.6f}; // 60 in -- ICC A117.1 S603

    Parameter pIsSingle = roomInst.LookupParameter("Is Single-User Toilet Room");
    Parameter pWidth    = roomInst.LookupParameter("Room Width");
    Parameter pDepth    = roomInst.LookupParameter("Room Depth");
    if (pIsSingle == null || pIsSingle.AsInteger() != 1) return;

    if (pWidth != null && pWidth.AsDouble() < minWidthFt)
        TaskDialog.Show("ICC A117.1 S603 Violation",
            $"Accessible toilet room width {{pWidth.AsDouble() * 12.0:F2}} in < 60 in minimum. "
            + "Ref: ICC A117.1 S603.");

    if (pDepth != null && pDepth.AsDouble() < minDepthFt)
        TaskDialog.Show("ICC A117.1 S603 Violation",
            $"Accessible toilet room depth {{pDepth.AsDouble() * 12.0:F2}} in < 60 in minimum. "
            + "Ref: ICC A117.1 S603.");
}}""",
        ))

        # Mixed-use building area tabulation
        samples.append(_s(
            "Calculate and validate total building area against zoning setback and FAR requirements",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// Zoning: Floor Area Ratio (FAR) = Gross Floor Area / Lot Area
// Typical commercial FAR: 2.0-10.0 depending on zone
void ValidateFARCompliance(FamilyInstance buildingInst)
{
    Parameter pGFA     = buildingInst.LookupParameter("Gross Floor Area (sq ft)");
    Parameter pLotArea = buildingInst.LookupParameter("Lot Area (sq ft)");
    Parameter pAllowedFAR = buildingInst.LookupParameter("Allowed FAR");
    if (pGFA == null || pLotArea == null || pAllowedFAR == null) return;

    double gfa        = pGFA.AsDouble();
    double lot        = pLotArea.AsDouble();
    double allowedFAR = pAllowedFAR.AsDouble();
    double actualFAR  = (lot > 0) ? gfa / lot : 0;

    if (actualFAR > allowedFAR)
    {
        TaskDialog.Show("Zoning FAR Violation",
            $"Floor Area Ratio {actualFAR:F2} exceeds allowed FAR {allowedFAR:F2}. "
            + $"({gfa:F0} GFA / {lot:F0} lot). "
            + "Ref: Local Zoning Ordinance.");
    }
}""",
        ))

        # Corridor width minimum by special occupancy (IBC 1020.2 -- health care 96 in)
        samples.append(_s(
            "Validate IBC 1020.2 health care occupancy corridor minimum width (96 in for patient movement)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1020.2: Corridors in Group I-2 health care occupancies
// Must be minimum 96 in (8 ft) wide for patient bed movement
void ValidateHealthCareCorridor(FamilyInstance corridorInst)
{{
    double minWidthFt = {96 * IN_TO_FT:.6f}; // 96 in = 8 ft -- IBC 1020.2

    Parameter pOccupancy = corridorInst.LookupParameter("Served Occupancy");
    Parameter pWidth     = corridorInst.LookupParameter("Corridor Width");
    if (pOccupancy == null || pWidth == null) return;

    string occ = pOccupancy.AsString();
    if (!occ.Contains("I-2") && !occ.Contains("Health Care")) return;

    double width = pWidth.AsDouble();
    if (width < minWidthFt)
    {{
        TaskDialog.Show("IBC 1020.2 Violation",
            $"Health care corridor width {{width * 12.0:F2}} in < 96 in (8 ft) minimum. "
            + "Ref: IBC 1020.2.");
    }}
}}""",
        ))

        # Egress width of room doorway vs room occupancy (IBC 1030.1)
        samples.append(_s(
            "Validate IBC 1030.1 assembly occupancy egress -- minimum 3 exits for > 300 occupants in room",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1030.1: Assembly occupancies with > 300 persons require >= 3 exits/exit access doors
// > 1,000 persons require >= 4 exits from the space
void ValidateAssemblyRoomExits(FamilyInstance roomInst)
{
    Parameter pOccupants = roomInst.LookupParameter("Occupant Load");
    Parameter pExitDoors = roomInst.LookupParameter("Exit Door Count");
    Parameter pIsAssembly = roomInst.LookupParameter("Is Assembly Occupancy");
    if (pIsAssembly == null || pIsAssembly.AsInteger() != 1) return;
    if (pOccupants == null || pExitDoors == null) return;

    double occ   = pOccupants.AsDouble();
    int exits    = (int)pExitDoors.AsDouble();
    int required = occ > 1000 ? 4 : occ > 300 ? 3 : 2;

    if (exits < required)
    {
        TaskDialog.Show("IBC 1030.1 Violation",
            $"Assembly space with {occ:F0} occupants requires {required} exits; {exits} provided. "
            + "Ref: IBC 1030.1.");
    }
}""",
        ))

        # Minimum storage room area (practical -- no code min, but fire code limits)
        samples.append(_s(
            "Validate IBC 903.2.9 storage occupancy area thresholds for automatic sprinkler system",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 903.2.9: Automatic fire-extinguishing systems required in storage occupancies
// S-1 (moderate hazard): >12,000 sq ft or > 2,500 sq ft above grade
// S-2 (low hazard): >12,000 sq ft or storage > 12 ft high
void ValidateStorageOccupancySprinkler(FamilyInstance roomInst)
{
    Parameter pIsStorage  = roomInst.LookupParameter("Is Storage Occupancy");
    Parameter pArea       = roomInst.LookupParameter("Room Area");
    Parameter pStorageHt  = roomInst.LookupParameter("Storage Height");
    Parameter pHasSpr     = roomInst.LookupParameter("Sprinkler System");
    if (pIsStorage == null || pIsStorage.AsInteger() != 1) return;

    double area      = pArea != null ? pArea.AsDouble() : 0;
    double storageHt = pStorageHt != null ? pStorageHt.AsDouble() : 0;
    bool hasSpr      = pHasSpr != null && pHasSpr.AsInteger() == 1;

    bool required = area > 12000 || (storageHt > 12.0);
    if (required && !hasSpr)
    {
        TaskDialog.Show("IBC 903.2.9 Violation",
            $"Storage occupancy {area:F0} sq ft / {storageHt:F1} ft high requires sprinklers. "
            + "Ref: IBC 903.2.9.");
    }
}""",
        ))

        # Bathroom minimum dimensions (IRC R307 -- 21 in clearance in front of toilet)
        samples.append(_s(
            "Validate IRC R307.1 bathroom fixture clearance (21 in in front of toilet, 15 in to side wall)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IRC R307.1: Bathroom fixture clearances
// Min clearance in front of toilet: 21 in
// Min side clearance (toilet to wall/fixture): 15 in
void ValidateBathroomFixtureClearance(FamilyInstance bathroomInst)
{{
    double minFrontFt = {21 * IN_TO_FT:.6f}; // 21 in front -- IRC R307.1
    double minSideFt  = {15 * IN_TO_FT:.6f}; // 15 in side -- IRC R307.1

    Parameter pFront = bathroomInst.LookupParameter("Toilet Front Clearance");
    Parameter pSide  = bathroomInst.LookupParameter("Toilet Side Clearance");

    if (pFront != null && pFront.AsDouble() < minFrontFt)
        TaskDialog.Show("IRC R307.1 Violation",
            $"Toilet front clearance {{pFront.AsDouble() * 12.0:F2}} in < 21 in minimum. "
            + "Ref: IRC R307.1.");

    if (pSide != null && pSide.AsDouble() < minSideFt)
        TaskDialog.Show("IRC R307.1 Violation",
            $"Toilet side clearance {{pSide.AsDouble() * 12.0:F2}} in < 15 in minimum. "
            + "Ref: IRC R307.1.");
}}""",
        ))

        # Bedroom minimum area (IRC R304 -- 70 sq ft, 7 ft min dimension)
        samples.append(_s(
            "Validate IRC R304.1 bedroom minimum floor area (70 sq ft) and minimum dimension (7 ft)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IRC R304.1: Sleeping rooms (bedrooms) minimum area = 70 sq ft
// IRC R304.2: Minimum horizontal dimension = 7 ft
void ValidateBedroomMinimum(FamilyInstance roomInst)
{
    double minAreaFt2 = 70.0; // sq ft -- IRC R304.1
    double minDimFt   = 7.0;  // ft -- IRC R304.2

    Parameter pIsBedroom = roomInst.LookupParameter("Is Bedroom");
    Parameter pArea      = roomInst.LookupParameter("Room Area");
    Parameter pMinDim    = roomInst.LookupParameter("Min Room Dimension");
    if (pIsBedroom == null || pIsBedroom.AsInteger() != 1) return;

    if (pArea != null && pArea.AsDouble() < minAreaFt2)
        TaskDialog.Show("IRC R304.1 Violation",
            $"Bedroom area {pArea.AsDouble():F1} sq ft < 70 sq ft minimum. "
            + "Ref: IRC R304.1.");

    if (pMinDim != null && pMinDim.AsDouble() < minDimFt)
        TaskDialog.Show("IRC R304.2 Violation",
            $"Bedroom minimum dimension {pMinDim.AsDouble() * 12.0:F1} in < 7 ft (84 in). "
            + "Ref: IRC R304.2.");
}""",
        ))

        # Dwelling unit area -- efficiency apartment minimums (HUD standards)
        samples.append(_s(
            "Validate HUD minimum floor area for efficiency dwelling unit (220 sq ft for 1 person)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// HUD Minimum Property Standards: Efficiency units
// 1 person: 220 sq ft minimum gross floor area
// 2 persons: 320 sq ft minimum
void ValidateEfficiencyUnitArea(FamilyInstance unitInst)
{
    Parameter pPersons = unitInst.LookupParameter("Intended Occupants");
    Parameter pArea    = unitInst.LookupParameter("Gross Floor Area (sq ft)");
    Parameter pIsEff   = unitInst.LookupParameter("Is Efficiency Unit");
    if (pIsEff == null || pIsEff.AsInteger() != 1) return;
    if (pArea == null) return;

    int persons  = pPersons != null ? (int)pPersons.AsDouble() : 1;
    double minSF = persons <= 1 ? 220.0 : 320.0;
    double area  = pArea.AsDouble();

    if (area < minSF)
    {
        TaskDialog.Show("HUD MPS Violation",
            $"Efficiency unit {area:F0} sq ft < {minSF:F0} sq ft minimum for {persons}-person occupancy. "
            + "Ref: HUD Minimum Property Standards.");
    }
}""",
        ))

        # Commercial kitchen area per code (health dept -- typical 200 sq ft min)
        samples.append(_s(
            "Validate minimum commercial kitchen area and hood clearance (200 sq ft, 18 in min hood-to-equipment)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// Health department / IMC 507: Commercial kitchen minimum area and hood clearance
// Min area: ~200 sq ft, Hood clearance above equipment: 18 in minimum (IMC 507.2)
void ValidateCommercialKitchenArea(FamilyInstance kitchenInst)
{{
    double minAreaFt2     = 200.0; // typical health dept minimum
    double minHoodClrFt   = {18 * IN_TO_FT:.6f}; // 18 in -- IMC 507.2

    Parameter pArea      = kitchenInst.LookupParameter("Kitchen Area (sq ft)");
    Parameter pHoodClr   = kitchenInst.LookupParameter("Hood Clearance");
    Parameter pIsComm    = kitchenInst.LookupParameter("Is Commercial Kitchen");
    if (pIsComm == null || pIsComm.AsInteger() != 1) return;

    if (pArea != null && pArea.AsDouble() < minAreaFt2)
        TaskDialog.Show("Health Dept Violation",
            $"Commercial kitchen area {{pArea.AsDouble():F0}} sq ft < 200 sq ft minimum. "
            + "Ref: Local health department standards.");

    if (pHoodClr != null && pHoodClr.AsDouble() < minHoodClrFt)
        TaskDialog.Show("IMC 507.2 Violation",
            $"Hood clearance above equipment {{pHoodClr.AsDouble() * 12.0:F2}} in < 18 in minimum. "
            + "Ref: IMC 507.2.");
}}""",
        ))

        # Conference room area per person (IBC Table 1004.5 -- 15 sq ft/person)
        samples.append(_s(
            "Calculate IBC Table 1004.5 conference room occupant load and validate against posted capacity",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC Table 1004.5: Conference rooms = 15 sq ft per person (assembly-unconcentrated)
// Validate: posted occupancy must not exceed calculated maximum
void ValidateConferenceRoomOccupancy(FamilyInstance roomInst)
{
    double sfPerPerson    = 15.0; // IBC Table 1004.5 assembly unconcentrated

    Parameter pArea      = roomInst.LookupParameter("Room Area");
    Parameter pPosted    = roomInst.LookupParameter("Posted Occupancy");
    Parameter pIsConf    = roomInst.LookupParameter("Is Conference Room");
    if (pIsConf == null || pIsConf.AsInteger() != 1) return;
    if (pArea == null) return;

    double area       = pArea.AsDouble();
    double maxAllowed = area / sfPerPerson;

    if (pPosted != null && pPosted.AsDouble() > maxAllowed)
    {
        TaskDialog.Show("IBC Table 1004.5 Violation",
            $"Conference room posted occupancy {pPosted.AsDouble():F0} exceeds "
            + $"calculated maximum {maxAllowed:F0} ({area:F0} sf / 15 sf/person). "
            + "Ref: IBC Table 1004.5.");
    }
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # IMC 403 -- Ventilation
    # ------------------------------------------------------------------

    def _ventilation(self) -> List[SAMPLE]:
        samples = []

        # Minimum outside air per occupant (IMC Table 403.3.1.1)
        for (space, cfm_per_person, cfm_per_ft2, code) in [
            ("office (general)",             5,  0.06, "IMC Table 403.3.1.1"),
            ("conference room",             5,  0.06, "IMC Table 403.3.1.1"),
            ("classroom (age 9+)",           10, 0.12, "IMC Table 403.3.1.1"),
            ("retail sales floor",           7,  0.12, "IMC Table 403.3.1.1"),
            ("restaurant dining",           7,  0.18, "IMC Table 403.3.1.1"),
            ("health care patient room",    25,  0.12, "IMC Table 403.3.1.1"),
        ]:
            samples.append(_s(
                f"Validate {code} minimum outside air for {space} ({cfm_per_person} cfm/person + {cfm_per_ft2} cfm/sq ft)",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// {code}: {space}
// Outdoor air rate: {cfm_per_person} cfm/person + {cfm_per_ft2} cfm/sq ft
void ValidateOutsideAir_{space.replace(' ', '_').replace('(', '').replace(')', '').replace('+', 'plus').replace('/', '_')}(FamilyInstance spaceInst)
{{
    double cfmPerPerson  = {float(cfm_per_person)};   // cfm/person -- {code}
    double cfmPerSqFt    = {float(cfm_per_ft2)};      // cfm/sq ft -- {code}

    Parameter pArea      = spaceInst.LookupParameter("Room Area");
    Parameter pOccupants = spaceInst.LookupParameter("Occupant Count");
    Parameter pOAFlow    = spaceInst.LookupParameter("Outside Air Flow (cfm)");
    if (pArea == null || pOccupants == null || pOAFlow == null) return;

    double area      = pArea.AsDouble();       // sq ft
    double occupants = pOccupants.AsDouble();
    double minOA     = occupants * cfmPerPerson + area * cfmPerSqFt;
    double actual    = pOAFlow.AsDouble();

    if (actual < minOA)
    {{
        TaskDialog.Show("{code} Violation",
            $"Outside air {{actual:F1}} cfm is below required {{minOA:F1}} cfm "
            + $"({{occupants:F0}} persons x {cfm_per_person} cfm + {{area:F0}} sq ft x {cfm_per_ft2} cfm/sf). "
            + "Ref: {code} ({space}).");
    }}
}}""",
            ))

        # Natural ventilation -- window area ratio (IBC 1203.5 -- 8% of floor area)
        samples.append(_s(
            "Validate IBC 1203.5 natural ventilation opening area (minimum 4% of floor area, openable)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1203.5: Natural ventilation -- openable area >= 4% of floor area
// Total window area >= 8% of floor area (IBC 1205.2 for light as well)
void ValidateNaturalVentilation(FamilyInstance roomInst)
{
    double minOpenableRatio = 0.04; // 4% of floor area -- IBC 1203.5
    double minWindowRatio   = 0.08; // 8% of floor area -- IBC 1205.2 (daylight)

    Parameter pFloorArea     = roomInst.LookupParameter("Room Area");
    Parameter pOpenableArea  = roomInst.LookupParameter("Openable Window Area");
    Parameter pWindowArea    = roomInst.LookupParameter("Total Window Area");
    if (pFloorArea == null) return;

    double floorArea    = pFloorArea.AsDouble();
    double minOpenable  = floorArea * minOpenableRatio;
    double minWindow    = floorArea * minWindowRatio;

    if (pOpenableArea != null)
    {
        double openable = pOpenableArea.AsDouble();
        if (openable < minOpenable)
        {
            TaskDialog.Show("IBC 1203.5 Violation",
                $"Openable window area {openable:F2} sq ft is below required "
                + $"{minOpenable:F2} sq ft (4% of {floorArea:F1} sq ft). "
                + "Ref: IBC 1203.5.");
        }
    }

    if (pWindowArea != null)
    {
        double winArea = pWindowArea.AsDouble();
        if (winArea < minWindow)
        {
            TaskDialog.Show("IBC 1205.2 Violation",
                $"Total window area {winArea:F2} sq ft is below required "
                + $"{minWindow:F2} sq ft (8% of {floorArea:F1} sq ft for daylight). "
                + "Ref: IBC 1205.2.");
        }
    }
}""",
        ))

        # Exhaust requirements (IMC 403.7 -- bathrooms, kitchens)
        for (space, exhaust_cfm, code) in [
            ("residential bathroom (intermittent)", 50,  "IMC Table 403.3.1.1 / ASHRAE 62.2"),
            ("residential kitchen (continuous)",    100, "IMC Table 403.3.1.1 / ASHRAE 62.2"),
            ("commercial kitchen hood",             None, "IMC 507 (size-dependent)"),
        ]:
            if exhaust_cfm is None:
                continue
            samples.append(_s(
                f"Validate {code} minimum exhaust rate for {space}",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// {code}: {space} minimum exhaust = {exhaust_cfm} cfm
void ValidateExhaustRate_{space.split(' ')[0].replace('/', '_')}(FamilyInstance spaceInst)
{{
    double minExhaustCfm = {float(exhaust_cfm)}; // cfm -- {code}

    Parameter pExhaust = spaceInst.LookupParameter("Exhaust Flow (cfm)");
    if (pExhaust == null) return;

    double actual = pExhaust.AsDouble();
    if (actual < minExhaustCfm)
    {{
        TaskDialog.Show("{code} Violation",
            $"Exhaust rate {{actual:F1}} cfm is below required {exhaust_cfm} cfm "
            + "for {space}. "
            + "Ref: {code}");
    }}
}}""",
            ))

        # CO2-based demand-controlled ventilation setpoint (IMC 403.4.4 -- 1100 ppm max)
        samples.append(_s(
            "Validate IMC 403.4.4 demand-controlled ventilation CO2 setpoint (1100 ppm maximum)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IMC 403.4.4: Demand-controlled ventilation (DCV) required for occupancies > 40 persons
// CO2 setpoint for ventilation increase: 1100 ppm maximum above outdoor CO2 (~400 ppm)
void ValidateDCVSetpoint(FamilyInstance airSystemInst)
{
    double maxCO2Setpoint = 1100.0; // ppm above outdoor -- IMC 403.4.4

    Parameter pSetpoint   = airSystemInst.LookupParameter("CO2 Setpoint (ppm)");
    Parameter pHasDCV     = airSystemInst.LookupParameter("Has DCV");
    Parameter pOccupants  = airSystemInst.LookupParameter("Design Occupancy");
    if (pSetpoint == null) return;

    bool hasDCV       = pHasDCV != null && pHasDCV.AsInteger() == 1;
    double occupants  = pOccupants != null ? pOccupants.AsDouble() : 0;

    // IMC 403.4.4: DCV required for > 40 persons in a single zone
    if (!hasDCV && occupants > 40)
    {
        TaskDialog.Show("IMC 403.4.4 Violation",
            $"Zone with {occupants:F0} occupants requires demand-controlled ventilation. "
            + "Ref: IMC 403.4.4.");
    }

    double setpoint = pSetpoint.AsDouble();
    if (setpoint > maxCO2Setpoint)
    {
        TaskDialog.Show("IMC 403.4.4 Violation",
            $"CO2 setpoint {setpoint:F0} ppm exceeds 1100 ppm maximum. "
            + "Ref: IMC 403.4.4.");
    }
}""",
        ))

        # Duct insulation (IMC 604 -- R-6 for supply, R-4.2 for return)
        samples.append(_s(
            "Validate IMC 604 minimum duct insulation R-values (R-6 supply, R-4.2 return)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IMC 604: Duct insulation minimum R-values
// Supply ductwork in unconditioned space: R-6
// Return ductwork in unconditioned space: R-4.2
void ValidateDuctInsulation(FamilyInstance ductInst)
{
    double minSupplyR = 6.0;  // R-6 supply -- IMC 604.3
    double minReturnR = 4.2;  // R-4.2 return -- IMC 604.3

    Parameter pIsSupply  = ductInst.LookupParameter("Is Supply Duct");
    Parameter pRValue    = ductInst.LookupParameter("Insulation R-Value");
    Parameter pUnconditioned = ductInst.LookupParameter("In Unconditioned Space");
    if (pRValue == null || pUnconditioned == null) return;

    bool inUnconditioned = pUnconditioned.AsInteger() == 1;
    if (!inUnconditioned) return; // No requirement in conditioned space

    bool isSupply  = pIsSupply != null && pIsSupply.AsInteger() == 1;
    double required = isSupply ? minSupplyR : minReturnR;
    double actual   = pRValue.AsDouble();

    if (actual < required)
    {
        TaskDialog.Show("IMC 604 Violation",
            $"{(isSupply ? "Supply" : "Return")} duct R-value {actual:F1} is below "
            + $"required R-{required:F1} in unconditioned space. "
            + "Ref: IMC 604.3.");
    }
}""",
        ))

        # IMC 401.4 -- toilet exhaust separate from other systems
        samples.append(_s(
            "Validate IMC 401.4 toilet room exhaust system independence (must not recirculate to occupied spaces)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IMC 401.4: Air exhausted from toilet rooms and bathrooms must not be recirculated
// to occupied spaces; must be exhausted directly to the outdoors
void ValidateToiletExhaustIndependence(FamilyInstance bathroomInst)
{
    Parameter pIsToilet      = bathroomInst.LookupParameter("Is Toilet Room");
    Parameter pExhaustType   = bathroomInst.LookupParameter("Exhaust System Type");
    Parameter pRecirculates  = bathroomInst.LookupParameter("Exhaust Recirculates");
    if (pIsToilet == null || pIsToilet.AsInteger() != 1) return;

    bool recirculates = pRecirculates != null && pRecirculates.AsInteger() == 1;
    if (recirculates)
    {
        TaskDialog.Show("IMC 401.4 Violation",
            "Toilet room exhaust must not be recirculated to occupied spaces. "
            + "Must exhaust directly outdoors. "
            + "Ref: IMC 401.4.");
    }

    if (pExhaustType != null && pExhaustType.AsString() == "Return Air")
    {
        TaskDialog.Show("IMC 401.4 Violation",
            "Toilet room exhaust cannot be returned through the HVAC system. "
            + "Ref: IMC 401.4.");
    }
}""",
        ))

        # ASHRAE 55 thermal comfort -- operative temperature range
        samples.append(_s(
            "Validate ASHRAE 55 thermal comfort operative temperature range (68-76 F winter, 73-79 F summer)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ASHRAE 55: Occupied spaces must be within thermal comfort zone
// Winter (clothing 1.0 clo): 68-76 F (20-24.4 C) operative temperature
// Summer (clothing 0.5 clo): 73-79 F (22.8-26.1 C) operative temperature
void ValidateThermalComfortTemperature(FamilyInstance spaceInst)
{
    double minWinterF = 68.0; // F -- ASHRAE 55 winter
    double maxWinterF = 76.0;
    double minSummerF = 73.0; // F -- ASHRAE 55 summer
    double maxSummerF = 79.0;

    Parameter pSetpointHeat = spaceInst.LookupParameter("Heating Setpoint (F)");
    Parameter pSetpointCool = spaceInst.LookupParameter("Cooling Setpoint (F)");

    if (pSetpointHeat != null)
    {
        double heat = pSetpointHeat.AsDouble();
        if (heat < minWinterF || heat > maxWinterF)
            TaskDialog.Show("ASHRAE 55 Warning",
                $"Heating setpoint {heat:F1} F is outside ASHRAE 55 winter comfort range {minWinterF}-{maxWinterF} F. "
                + "Ref: ASHRAE 55.");
    }

    if (pSetpointCool != null)
    {
        double cool = pSetpointCool.AsDouble();
        if (cool < minSummerF || cool > maxSummerF)
            TaskDialog.Show("ASHRAE 55 Warning",
                $"Cooling setpoint {cool:F1} F is outside ASHRAE 55 summer comfort range {minSummerF}-{maxSummerF} F. "
                + "Ref: ASHRAE 55.");
    }
}""",
        ))

        # Duct velocity limits (SMACNA -- low pressure < 2000 fpm, medium 2000-2500 fpm)
        for (duct_type, max_fpm, code) in [
            ("main supply trunk",    2500, "SMACNA HVAC Duct Construction: 2500 fpm max supply"),
            ("branch supply duct",   1500, "SMACNA: 1500 fpm max branch supply"),
            ("return main",          2000, "SMACNA: 2000 fpm max return air main"),
            ("outside air intake",   500,  "SMACNA: 500 fpm max OA louver velocity"),
        ]:
            samples.append(_s(
                f"Validate {code} maximum duct velocity for {duct_type}",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// {code}
void ValidateDuctVelocity_{duct_type.replace(' ', '_')}(FamilyInstance ductInst)
{{
    double maxVelocityFpm = {float(max_fpm)};

    Parameter pVelocity = ductInst.LookupParameter("Air Velocity (fpm)");
    Parameter pDuctType = ductInst.LookupParameter("Duct Type");
    if (pVelocity == null) return;

    double velocity = pVelocity.AsDouble();
    if (velocity > maxVelocityFpm)
    {{
        TaskDialog.Show("SMACNA Duct Velocity Warning",
            $"{{duct_type}} velocity {{velocity:F0}} fpm > {max_fpm} fpm maximum. "
            + "May cause excessive noise and pressure drop. "
            + "Ref: {code}");
    }}
}}""",
            ))

        # IMC 505 exhaust discharge clearances (10 ft from property line, windows, etc.)
        samples.append(_s(
            "Validate IMC 505.1 exhaust system discharge clearances (10 ft from openings, 3 ft from property line)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IMC 505.1: Exhaust air discharge location requirements
// Min 10 ft from any air intake, door, or operable window
// Min 3 ft from property lines
void ValidateExhaustDischargeLocation(FamilyInstance exhaustOutletInst)
{
    double minFromIntakeFt    = 10.0; // 10 ft -- IMC 505.1
    double minFromPropertyFt  = 3.0;  // 3 ft  -- IMC 505.1

    Parameter pDistIntake   = exhaustOutletInst.LookupParameter("Distance to Nearest Intake");
    Parameter pDistProperty = exhaustOutletInst.LookupParameter("Distance to Property Line");

    if (pDistIntake != null && pDistIntake.AsDouble() < minFromIntakeFt)
        TaskDialog.Show("IMC 505.1 Violation",
            $"Exhaust discharge {pDistIntake.AsDouble():F1} ft from nearest intake < 10 ft minimum. "
            + "Ref: IMC 505.1.");

    if (pDistProperty != null && pDistProperty.AsDouble() < minFromPropertyFt)
        TaskDialog.Show("IMC 505.1 Violation",
            $"Exhaust discharge {pDistProperty.AsDouble():F1} ft from property line < 3 ft minimum. "
            + "Ref: IMC 505.1.");
}""",
        ))

        # Plenum air pressure (SMACNA -- return air plenum clearances)
        samples.append(_s(
            "Validate IMC 602.1 ceiling plenum requirements -- no combustible materials, rated construction",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IMC 602.1: Ceiling plenums used for return air must comply with:
// - Combustible materials not permitted in plenum
// - Electrical wiring must be plenum-rated (CMP)
// - Minimum 12 in clearance for access and maintenance
void ValidatePlenumCompliance(FamilyInstance plenumInst)
{
    double minClearanceFt = 12.0 / 12.0; // 12 in -- IMC 602.1

    Parameter pClearance  = plenumInst.LookupParameter("Plenum Clearance");
    Parameter pHasCombust = plenumInst.LookupParameter("Has Combustible Materials");
    Parameter pWiringType = plenumInst.LookupParameter("Electrical Wiring Type");

    if (pHasCombust != null && pHasCombust.AsInteger() == 1)
        TaskDialog.Show("IMC 602.1 Violation",
            "Combustible materials are not permitted in return air plenums. "
            + "Ref: IMC 602.1.");

    if (pClearance != null && pClearance.AsDouble() < minClearanceFt)
        TaskDialog.Show("IMC 602.1 Violation",
            $"Plenum clearance {pClearance.AsDouble() * 12.0:F1} in < 12 in minimum for maintenance. "
            + "Ref: IMC 602.1.");

    if (pWiringType != null && pWiringType.AsString() != "CMP" && pWiringType.AsString() != "Plenum-Rated")
        TaskDialog.Show("NEC 300.22 Violation",
            $"Wiring type '{pWiringType.AsString()}' is not plenum-rated. Use CMP cable in return air plenums. "
            + "Ref: NEC 300.22(C).");
}""",
        ))

        # Bathroom exhaust duration (ASHRAE 62.2 -- continuous or intermittent with controls)
        samples.append(_s(
            "Validate ASHRAE 62.2 bathroom ventilation strategy -- continuous vs intermittent with controls",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ASHRAE 62.2 Table 4: Bathroom local exhaust
// Continuous rate: 20 cfm minimum; Intermittent rate: 50 cfm minimum
// Intermittent exhaust must have automatic controls (humidity or timer)
void ValidateBathroomExhaustStrategy(FamilyInstance bathroomInst)
{
    double contMinCfm = 20.0;  // cfm continuous -- ASHRAE 62.2 Table 4
    double interMinCfm = 50.0; // cfm intermittent -- ASHRAE 62.2 Table 4

    Parameter pExhaust   = bathroomInst.LookupParameter("Exhaust Flow (cfm)");
    Parameter pIsCont    = bathroomInst.LookupParameter("Is Continuous Exhaust");
    Parameter pHasCtrl   = bathroomInst.LookupParameter("Has Automatic Control");
    if (pExhaust == null) return;

    double cfm       = pExhaust.AsDouble();
    bool isCont      = pIsCont != null && pIsCont.AsInteger() == 1;
    bool hasCtrl     = pHasCtrl != null && pHasCtrl.AsInteger() == 1;
    double required  = isCont ? contMinCfm : interMinCfm;

    if (cfm < required)
    {
        TaskDialog.Show("ASHRAE 62.2 Violation",
            $"{(isCont ? "Continuous" : "Intermittent")} bathroom exhaust {cfm:F1} cfm < {required:F0} cfm. "
            + "Ref: ASHRAE 62.2 Table 4.");
    }

    if (!isCont && !hasCtrl)
    {
        TaskDialog.Show("ASHRAE 62.2 Violation",
            "Intermittent bathroom exhaust requires automatic humidity or timer control. "
            + "Ref: ASHRAE 62.2 S6.4.");
    }
}""",
        ))

        # Minimum outdoor air per ASHRAE 62.1 breathing zone
        samples.append(_s(
            "Calculate ASHRAE 62.1-2019 breathing zone outdoor airflow (Vbz = Rp*Pz + Ra*Az)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ASHRAE 62.1 Eq 6-1: Vbz = Rp * Pz + Ra * Az
// Rp = people outdoor air rate (cfm/person)
// Ra = area outdoor air rate (cfm/sq ft)
// Pz = zone population, Az = zone floor area
void ValidateBreathingZoneOA(FamilyInstance spaceInst)
{
    // Office defaults from ASHRAE 62.1 Table 6-1
    double rp    = 5.0;   // cfm/person -- ASHRAE 62.1 Table 6-1 office
    double ra    = 0.06;  // cfm/sq ft  -- ASHRAE 62.1 Table 6-1 office

    Parameter pArea   = spaceInst.LookupParameter("Room Area");
    Parameter pOccup  = spaceInst.LookupParameter("Occupant Count");
    Parameter pOAFlow = spaceInst.LookupParameter("Outside Air Flow (cfm)");
    if (pArea == null || pOccup == null || pOAFlow == null) return;

    double az  = pArea.AsDouble();
    double pz  = pOccup.AsDouble();
    double vbz = rp * pz + ra * az;
    double provided = pOAFlow.AsDouble();

    if (provided < vbz)
    {
        TaskDialog.Show("ASHRAE 62.1 Violation",
            $"Outdoor air {provided:F1} cfm < required breathing zone Vbz={vbz:F1} cfm "
            + $"({pz:F0} persons x {rp} + {az:F1} sf x {ra}). "
            + "Ref: ASHRAE 62.1 Eq 6-1.");
    }
}""",
        ))

        # Ventilation in garage (IMC 404 -- 1.5 cfm/sq ft or 100 cfm/car)
        samples.append(_s(
            "Validate IMC 404 enclosed parking garage ventilation (1.5 cfm/sq ft or 100 cfm/vehicle space)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IMC 404: Enclosed parking garages require mechanical ventilation
// Continuous: 1.5 cfm per sq ft of floor area
// Or: 100 cfm per vehicle space (if CO sensor-based intermittent)
void ValidateParkingGarageVentilation(FamilyInstance garageInst)
{
    double cfmPerSqFt  = 1.5;   // cfm/sq ft -- IMC 404
    double cfmPerCar   = 100.0; // cfm/vehicle -- IMC 404 CO-based

    Parameter pArea     = garageInst.LookupParameter("Garage Floor Area (sq ft)");
    Parameter pCars     = garageInst.LookupParameter("Vehicle Spaces");
    Parameter pExhaust  = garageInst.LookupParameter("Exhaust Flow (cfm)");
    Parameter pHasCO    = garageInst.LookupParameter("Has CO Sensor Control");
    if (pArea == null || pExhaust == null) return;

    double area    = pArea.AsDouble();
    double cars    = pCars != null ? pCars.AsDouble() : 0;
    bool hasCO     = pHasCO != null && pHasCO.AsInteger() == 1;
    double actual  = pExhaust.AsDouble();

    double required = hasCO && cars > 0 ? cars * cfmPerCar : area * cfmPerSqFt;
    if (actual < required)
    {
        TaskDialog.Show("IMC 404 Violation",
            $"Parking garage exhaust {actual:F0} cfm < required {required:F0} cfm "
            + $"({(hasCO ? $"{cars:F0} vehicles x 100 cfm" : $"{area:F0} sf x 1.5 cfm/sf")}). "
            + "Ref: IMC 404.");
    }
}""",
        ))

        # Kitchen hood capture velocity (IMC 507.2 -- 100 fpm minimum)
        samples.append(_s(
            "Validate IMC 507.2 commercial kitchen hood face velocity (minimum 100 fpm capture velocity)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IMC 507.2: Commercial kitchen exhaust hood minimum capture velocity = 100 fpm
// at hood face (lowest edge of hood perimeter)
void ValidateHoodFaceVelocity(FamilyInstance hoodInst)
{
    double minVelocityFpm = 100.0; // fpm -- IMC 507.2

    Parameter pVelocity = hoodInst.LookupParameter("Hood Face Velocity (fpm)");
    if (pVelocity == null) return;

    double velocity = pVelocity.AsDouble();
    if (velocity < minVelocityFpm)
    {
        TaskDialog.Show("IMC 507.2 Violation",
            $"Kitchen hood face velocity {velocity:F0} fpm < 100 fpm minimum. "
            + "Ref: IMC 507.2.");
    }
}""",
        ))

        # ERV/HRV ventilation rate check (ASHRAE 90.1 requirement for energy recovery)
        samples.append(_s(
            "Validate ASHRAE 90.1 S6.5.6 energy recovery ventilator requirement (>= 70% effectiveness)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ASHRAE 90.1 S6.5.6: Energy recovery required when exhaust flow >= 5,000 cfm
// and outdoor air fraction >= 70%, or specific climate/occupancy conditions
// Minimum sensible heat recovery effectiveness: 70%
void ValidateEnergyRecovery(FamilyInstance airHandlerInst)
{
    double minEffectiveness = 0.70; // 70% -- ASHRAE 90.1 S6.5.6
    double erThresholdCfm   = 5000.0; // 5,000 cfm threshold

    Parameter pExhaust    = airHandlerInst.LookupParameter("Design Exhaust (cfm)");
    Parameter pHasERV     = airHandlerInst.LookupParameter("Has Energy Recovery");
    Parameter pEffective  = airHandlerInst.LookupParameter("Sensible Effectiveness");
    if (pExhaust == null) return;

    double exhaust  = pExhaust.AsDouble();
    bool hasERV     = pHasERV != null && pHasERV.AsInteger() == 1;

    if (exhaust >= erThresholdCfm && !hasERV)
    {
        TaskDialog.Show("ASHRAE 90.1 S6.5.6 Violation",
            $"Air handler with {exhaust:F0} cfm exhaust requires energy recovery ventilation. "
            + "Ref: ASHRAE 90.1 S6.5.6.");
    }

    if (hasERV && pEffective != null && pEffective.AsDouble() < minEffectiveness)
    {
        TaskDialog.Show("ASHRAE 90.1 S6.5.6 Violation",
            $"ERV sensible effectiveness {pEffective.AsDouble():P0} < 70% required. "
            + "Ref: ASHRAE 90.1 S6.5.6.");
    }
}""",
        ))

        return samples

    # ------------------------------------------------------------------
    # Structural clearances and headroom
    # ------------------------------------------------------------------

    def _structural_clearances(self) -> List[SAMPLE]:
        samples = []

        # General headroom clearance: 7 ft 0 in (84 in) per IBC 1208.2
        for (space, min_in, code) in [
            ("general interior space",  84, "IBC 1208.2 (7 ft 0 in)"),
            ("parking structure",       84, "IBC 406.4.1 (7 ft 0 in)"),
            ("accessible route",        80, "ADA 307.4 (6 ft 8 in vertical clearance)"),
            ("exit enclosure stair",    80, "IBC 1011.3 (6 ft 8 in stair)"),
            ("mechanical room",         72, "IBC 1208.2 exception (6 ft 0 in service space)"),
        ]:
            min_ft = min_in * IN_TO_FT
            samples.append(_s(
                f"Validate {code} minimum structural headroom for {space}",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// {code}
// Minimum headroom: {min_in} in ({min_in / 12.0:.2f} ft)
void ValidateHeadroom_{space.split(' ')[0].replace('/', '_')}(FamilyInstance element)
{{
    double minHeadroomFt = {min_ft:.6f}; // {min_in} in -- {code}

    Parameter pHeadroom = element.LookupParameter("Headroom Clearance");
    if (pHeadroom == null)
        pHeadroom = element.LookupParameter("Clear Height");
    if (pHeadroom == null) return;

    double headroom = pHeadroom.AsDouble();
    if (headroom < minHeadroomFt)
    {{
        TaskDialog.Show("{code.split('(')[0].strip()} Violation",
            $"Headroom clearance {{headroom * 12.0:F2}} in for {space} is below required "
            + $"{min_in} in. "
            + "Ref: {code}");
    }}
}}""",
            ))

        # Beam clear depth below structural member (AISC practical -- 2 in clearance to MEP)
        samples.append(_s(
            "Validate minimum structural beam clearance to ceiling/MEP (2 in below bottom of beam)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// Practical structural clearance: minimum 2 in from bottom of beam to ceiling or MEP
// This prevents conflict between structural members and mechanical/electrical systems
void ValidateBeamClearance(FamilyInstance beamInst)
{{
    double minClearFt = {2.0 * IN_TO_FT:.6f}; // 2 in minimum clearance

    Parameter pBeamBot   = beamInst.LookupParameter("Bottom of Beam Elevation");
    Parameter pCeilingHt = beamInst.LookupParameter("Ceiling Elevation");
    if (pBeamBot == null || pCeilingHt == null) return;

    double beamBot  = pBeamBot.AsDouble();
    double ceilingHt = pCeilingHt.AsDouble();
    double clearance = beamBot - ceilingHt;

    if (clearance < minClearFt)
    {{
        TaskDialog.Show("Structural Clearance Warning",
            $"Beam bottom to ceiling clearance {{clearance * 12.0:F2}} in is below "
            + "recommended 2 in minimum. Review for MEP coordination.");
    }}
}}""",
        ))

        # Column base plate clearance to slab edge (ACI 318 -- min 1.5 x anchor bolt diameter from edge)
        samples.append(_s(
            "Validate ACI 318 column anchor bolt minimum edge distance (1.5x bolt diameter from concrete edge)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ACI 318 Table 17.7.1: Anchor bolt minimum edge distance
// Cast-in anchor (headed bolt): min edge distance = 6 * diameter
// or 1.5 * hef (embedment depth), whichever is greater
void ValidateAnchorEdgeDistance(FamilyInstance columnInst)
{{
    Parameter pBoltDia    = columnInst.LookupParameter("Anchor Bolt Diameter");
    Parameter pEdgeDist   = columnInst.LookupParameter("Edge Distance");
    Parameter pEmbedDepth = columnInst.LookupParameter("Embedment Depth");
    if (pBoltDia == null || pEdgeDist == null) return;

    double boltDia  = pBoltDia.AsDouble();
    double edgeDist = pEdgeDist.AsDouble();
    double embedMin = pEmbedDepth != null ? 1.5 * pEmbedDepth.AsDouble() : 0;
    double diaMin   = 6.0 * boltDia;
    double required = Math.Max(diaMin, embedMin);

    if (edgeDist < required)
    {{
        TaskDialog.Show("ACI 318 Table 17.7.1 Violation",
            $"Anchor bolt edge distance {{edgeDist * 12.0:F2}} in is below required "
            + $"{{required * 12.0:F2}} in (6x bolt dia = {{diaMin * 12.0:F2}} in). "
            + "Ref: ACI 318 Table 17.7.1.");
    }}
}}""",
        ))

        # Structural slab minimum thickness (ACI 318 Table 8.3.1.1 -- l/20 two-way)
        samples.append(_s(
            "Validate ACI 318 Table 8.3.1.1 minimum slab thickness for two-way flat plate (l/30)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// ACI 318 Table 8.3.1.1: Two-way flat plate minimum slab thickness
// Without drop panels: h_min = ln / 30 (fy=60 ksi)
// ln = longer clear span
void ValidateSlabMinThickness(FamilyInstance slabInst)
{{
    Parameter pLongestSpan = slabInst.LookupParameter("Longest Clear Span");
    Parameter pThickness   = slabInst.LookupParameter("Slab Thickness");
    if (pLongestSpan == null || pThickness == null) return;

    double ln     = pLongestSpan.AsDouble(); // feet
    double minH   = ln / 30.0;               // ACI 318 Table 8.3.1.1 (fy=60 ksi, flat plate)
    double actual = pThickness.AsDouble();

    if (actual < minH)
    {{
        TaskDialog.Show("ACI 318 Table 8.3.1.1 Violation",
            $"Slab thickness {{actual * 12.0:F2}} in is below minimum {{minH * 12.0:F2}} in "
            + $"(ln={{ln:F1}} ft / 30 for two-way flat plate). "
            + "Ref: ACI 318 Table 8.3.1.1.");
    }}
}}""",
        ))

        # Beam depth-to-span ratio for deflection control (ACI 318 Table 9.3.1.1 -- l/18.5)
        for (condition, ratio, desc) in [
            ("simply supported",    16,   "ACI 318 Table 9.3.1.1 simply supported"),
            ("one end continuous",  18.5, "ACI 318 Table 9.3.1.1 one end continuous"),
            ("both ends continuous", 21,  "ACI 318 Table 9.3.1.1 both ends continuous"),
            ("cantilever",          8,    "ACI 318 Table 9.3.1.1 cantilever"),
        ]:
            samples.append(_s(
                f"Validate ACI 318 Table 9.3.1.1 minimum beam depth for {condition} (l/{ratio:.1f})",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// {desc}: minimum beam depth = span / {ratio:.1f}
void ValidateBeamDepth_{condition.replace(' ', '_')}(FamilyInstance beamInst)
{{
    double ratio = {ratio}; // {desc}

    Parameter pSpan  = beamInst.LookupParameter("Clear Span");
    Parameter pDepth = beamInst.LookupParameter("Beam Depth");
    if (pSpan == null || pDepth == null) return;

    double span    = pSpan.AsDouble();
    double minDepth = span / ratio;
    double actual  = pDepth.AsDouble();

    if (actual < minDepth)
    {{
        TaskDialog.Show("ACI 318 Table 9.3.1.1 Warning",
            $"Beam depth {{actual * 12.0:F2}} in may be insufficient for deflection control. "
            + $"Minimum recommended: {{minDepth * 12.0:F2}} in (span/{{ratio}} for {condition}). "
            + "Ref: ACI 318 Table 9.3.1.1. Verify with deflection calculation.");
    }}
}}""",
            ))

        # Expansion joint spacing (rule of thumb -- 100 ft concrete, 200 ft steel)
        for (material, max_spacing_ft, ref) in [
            ("concrete",  100, "ACI 224.3R: contraction joint max ~100 ft concrete"),
            ("steel",     200, "AISC: expansion joint max ~200 ft steel frame"),
            ("masonry",    50, "TMS 402: control joint max ~25-50 ft masonry"),
        ]:
            samples.append(_s(
                f"Validate {ref} maximum expansion joint spacing for {material} structure",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// {ref}
// Maximum expansion joint spacing: {max_spacing_ft} ft for {material}
void ValidateExpansionJointSpacing_{material}(FamilyInstance jointInst)
{{
    double maxSpacingFt = {float(max_spacing_ft)}; // ft -- {ref}

    Parameter pSpacing = jointInst.LookupParameter("Joint Spacing");
    if (pSpacing == null) return;

    double spacing = pSpacing.AsDouble();
    if (spacing > maxSpacingFt)
    {{
        TaskDialog.Show("Expansion Joint Spacing Warning",
            $"{{material.capitalize()}} expansion joint spacing {{spacing:F1}} ft exceeds "
            + $"recommended {{maxSpacingFt:F0}} ft maximum. "
            + "Ref: {ref}");
    }}
}}""",
            ))

        # Concrete cover for reinforcement (ACI 318 Table 20.6.1.3.1 -- 1.5 in to 3 in)
        for (exposure, cover_in, code) in [
            ("cast against earth",     3.0, "ACI 318 Table 20.6.1.3.1 (3 in cast against earth)"),
            ("exposed to weather",     2.0, "ACI 318 Table 20.6.1.3.1 (2 in weathering)"),
            ("interior slab/beam",     0.75,"ACI 318 Table 20.6.1.3.1 (3/4 in interior slab)"),
            ("column tie/stirrup",     1.5, "ACI 318 Table 20.6.1.3.1 (1.5 in column tie)"),
        ]:
            cover_ft = cover_in * IN_TO_FT
            samples.append(_s(
                f"Validate {code} minimum concrete cover for reinforcement",
                f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// {code}
// Minimum concrete cover: {cover_in} in for {exposure}
void ValidateConcreteCover_{exposure.replace(' ', '_')}(FamilyInstance structInst)
{{
    double minCoverFt = {cover_ft:.6f}; // {cover_in} in -- {code}

    Parameter pCover    = structInst.LookupParameter("Concrete Cover");
    Parameter pExposure = structInst.LookupParameter("Exposure Condition");
    if (pCover == null) return;

    double cover = pCover.AsDouble();
    if (cover < minCoverFt)
    {{
        TaskDialog.Show("{code.split('(')[0].strip()} Violation",
            $"Concrete cover {{cover * 12.0:F3}} in < required {cover_in} in for {exposure}. "
            + "Ref: {code}");
    }}
}}""",
            ))

        # Steel column base plate minimum size (AISC design guide)
        samples.append(_s(
            "Validate AISC minimum base plate bearing area for steel column (plate must cover full column footprint)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// AISC Design Guide 1: Base plate dimensions must be >= column footprint
// Minimum N = d + 2*(n+0.8*bf) where n and bf are design variables
// Simplified check: plate area >= column area x 2 for bearing
void ValidateColumnBasePlate(FamilyInstance columnInst)
{
    Parameter pColDepth  = columnInst.LookupParameter("Column Depth");
    Parameter pColFlange = columnInst.LookupParameter("Column Flange Width");
    Parameter pPlateN    = columnInst.LookupParameter("Base Plate Depth");
    Parameter pPlateB    = columnInst.LookupParameter("Base Plate Width");
    if (pColDepth == null || pPlateN == null || pPlateB == null) return;

    double colDepth  = pColDepth.AsDouble();
    double colFlange = pColFlange != null ? pColFlange.AsDouble() : colDepth * 0.6;

    // Simplified: plate must extend beyond column face each side
    double minN = colDepth  + 2 * (1.0 / 12.0); // 1 in overhang each side (min)
    double minB = colFlange + 2 * (1.0 / 12.0);

    if (pPlateN.AsDouble() < minN)
    {
        TaskDialog.Show("AISC Base Plate Warning",
            $"Base plate N={pPlateN.AsDouble() * 12.0:F2} in < column depth + 2 in ({minN * 12.0:F2} in). "
            + "Ref: AISC Design Guide 1.");
    }
    if (pPlateB.AsDouble() < minB)
    {
        TaskDialog.Show("AISC Base Plate Warning",
            $"Base plate B={pPlateB.AsDouble() * 12.0:F2} in < flange width + 2 in ({minB * 12.0:F2} in). "
            + "Ref: AISC Design Guide 1.");
    }
}""",
        ))

        # Minimum pile embedment (IBC 1810.2.1 -- 3 ft into bearing stratum)
        samples.append(_s(
            "Validate IBC 1810.2.1 minimum pile embedment into bearing stratum (3 ft minimum)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1810.2.1: Driven piles must penetrate into firm bearing stratum
// Minimum embedment into bearing stratum: 3 ft
void ValidatePileEmbedment(FamilyInstance pileInst)
{
    double minEmbedFt = 3.0; // 3 ft -- IBC 1810.2.1

    Parameter pEmbedment = pileInst.LookupParameter("Embedment into Bearing Stratum");
    if (pEmbedment == null) return;

    double embed = pEmbedment.AsDouble();
    if (embed < minEmbedFt)
    {
        TaskDialog.Show("IBC 1810.2.1 Violation",
            $"Pile embedment {embed:F2} ft < 3 ft minimum into bearing stratum. "
            + "Ref: IBC 1810.2.1.");
    }
}""",
        ))

        # Footing depth below frost line (IBC 1809.5 -- frost depth per location)
        samples.append(_s(
            "Validate IBC 1809.5 footing minimum depth below frost line (varies by climate zone)",
            """\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// IBC 1809.5: Footings must extend below frost depth for the site
// Frost depth varies: 12-18 in (mild), 36-42 in (northern US), 48+ in (northern)
void ValidateFootingFrostDepth(FamilyInstance footingInst)
{
    Parameter pFrostDepth  = footingInst.LookupParameter("Design Frost Depth");
    Parameter pFootingDepth = footingInst.LookupParameter("Footing Bottom Elevation Below Grade");
    if (pFrostDepth == null || pFootingDepth == null) return;

    double frostDepth   = pFrostDepth.AsDouble();
    double footingDepth = pFootingDepth.AsDouble();

    if (footingDepth < frostDepth)
    {
        TaskDialog.Show("IBC 1809.5 Violation",
            $"Footing bottom {footingDepth * 12.0:F1} in below grade is shallower than "
            + $"frost depth {frostDepth * 12.0:F1} in. "
            + "Ref: IBC 1809.5.");
    }
}""",
        ))

        # Steel beam web crippling clearance (AISC -- concentrated load on beam web)
        samples.append(_s(
            "Validate AISC beam web bearing length for concentrated loads (minimum 3.5 in for bearing plates)",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// AISC 360 J10: Beam webs subject to concentrated loads
// Minimum bearing length for end reactions: 2.5 in (flanged)
// Minimum bearing plate length under concentrated load: typically 3.5 in
void ValidateBeamBearingLength(FamilyInstance beamInst)
{{
    double minBearingFt = {3.5 * IN_TO_FT:.6f}; // 3.5 in -- AISC 360 J10

    Parameter pBearingLen = beamInst.LookupParameter("End Bearing Length");
    if (pBearingLen == null) return;

    double bearing = pBearingLen.AsDouble();
    if (bearing < minBearingFt)
    {{
        TaskDialog.Show("AISC 360 J10 Warning",
            $"Beam end bearing length {{bearing * 12.0:F2}} in < 3.5 in minimum. "
            + "Verify web crippling per AISC 360 J10. "
            + "Ref: AISC 360 J10.");
    }}
}}""",
        ))

        # Floor-to-floor height vs structural depth check
        samples.append(_s(
            "Validate that floor-to-floor height accommodates structural depth plus MEP plus finished ceiling",
            f"""\
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

// Check: floor-to-floor height >= structural depth + MEP plenum + finished ceiling + finished floor
// Typical breakdown: 4 in slab + beam depth + 18 in MEP plenum + 2 in ceiling + 1 in flooring
void ValidateFloorToFloorClearance(FamilyInstance floorInst)
{{
    double minClearFt  = {84 * IN_TO_FT:.6f}; // 84 in net occupiable clear height -- IBC 1208.2

    Parameter pF2F     = floorInst.LookupParameter("Floor to Floor Height");
    Parameter pBeamD   = floorInst.LookupParameter("Structural Depth");
    Parameter pMEP     = floorInst.LookupParameter("MEP Plenum Depth");
    Parameter pCeiling = floorInst.LookupParameter("Ceiling Depth");
    Parameter pSlab    = floorInst.LookupParameter("Slab Thickness");
    if (pF2F == null) return;

    double f2f         = pF2F.AsDouble();
    double beamD       = pBeamD    != null ? pBeamD.AsDouble()    : {18 * IN_TO_FT:.6f};  // 18 in default
    double mepPlenum   = pMEP      != null ? pMEP.AsDouble()      : {18 * IN_TO_FT:.6f};  // 18 in default
    double ceilingD    = pCeiling  != null ? pCeiling.AsDouble()  : {2  * IN_TO_FT:.6f};  // 2 in default
    double slab        = pSlab     != null ? pSlab.AsDouble()     : {4  * IN_TO_FT:.6f};  // 4 in default
    double occupiable  = f2f - beamD - mepPlenum - ceilingD - slab;

    if (occupiable < minClearFt)
    {{
        TaskDialog.Show("IBC 1208.2 Structural Clearance Warning",
            $"Occupiable clear height {{occupiable * 12.0:F2}} in is below required 84 in. "
            + $"Floor-to-floor: {{f2f * 12.0:F1}} in, Structural: {{beamD * 12.0:F1}} in, "
            + $"MEP: {{mepPlenum * 12.0:F1}} in, Ceiling: {{ceilingD * 12.0:F1}} in, Slab: {{slab * 12.0:F1}} in. "
            + "Ref: IBC 1208.2.");
    }}
}}""",
        ))

        return samples
