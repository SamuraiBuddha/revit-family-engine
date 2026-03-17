"""
BuildingCodeComplianceGenerator: families with compliance parameters.
Focus: fire rating, egress width, ADA clearance, structural load params.
Produces ~200 Alpaca training pairs.
"""
from typing import Dict, List

SAMPLE = Dict[str, str]

MM_TO_FT = 1.0 / 304.8
INCH_TO_FT = 1.0 / 12.0


def _s(instruction: str, output: str) -> SAMPLE:
    return {"instruction": instruction, "input": "", "output": output}


def _ft(mm: float) -> str:
    return f"{mm * MM_TO_FT:.6f}"


def _in(inches: float) -> str:
    return f"{inches * INCH_TO_FT:.6f}"


class BuildingCodeComplianceGenerator:
    """Generates training samples for families that include compliance parameters."""

    def generate(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []
        samples.extend(self._fire_rating_params())
        samples.extend(self._egress_params())
        samples.extend(self._ada_clearance_params())
        samples.extend(self._structural_compliance_params())
        samples.extend(self._mep_clearance_params())
        samples.extend(self._occupancy_params())
        return samples

    # ------------------------------------------------------------------
    # Fire rating parameters
    # ------------------------------------------------------------------
    def _fire_rating_params(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        cases = [
            ("door", "M_Fire-Rated Door", "fire-rated door family",
             [("FireRating", "0-hour", "1-hour", "1.5-hour", "2-hour", "3-hour", "4-hour"),
              ("SmokeLabel", "S-Label", "S-Label"),
              ("FireDoorWidth_mm", "900", "760", "1200")]),
            ("wall", "M_Fire-Rated Wall Panel", "fire-rated wall family",
             [("FireRating", "1-hour", "2-hour", "3-hour", "4-hour"),
              ("FireResistanceLevel", "Class A", "Class B"),
              ("WallThickness_mm", "200", "150", "250")]),
            ("ceiling", "M_Fire-Rated Ceiling Panel", "fire-rated ceiling assembly",
             [("FireRating", "1-hour", "2-hour"),
              ("AcousticRating_STC", "40", "50", "55"),
              ("PanelWidth_mm", "600", "1200")]),
            ("floor", "M_Fire-Rated Floor Assembly", "fire-rated floor assembly",
             [("FireRating", "1-hour", "2-hour", "3-hour"),
              ("StructuralRating", "Composite", "Non-composite"),
              ("SlabThickness_mm", "150", "200", "250")]),
            ("column", "M_Fire-Rated Column Wrap", "fire-rated column enclosure family",
             [("FireRating", "1-hour", "2-hour", "3-hour", "4-hour"),
              ("InsulationThickness_mm", "25", "50", "75"),
              ("ColumnDepth_mm", "300", "400", "500")]),
        ]

        for elem_type, family_name, desc, param_groups in cases:
            param_block = "\n".join([
                f"// {pg[0]}: {', '.join(pg[1:])}" for pg in param_groups
            ])
            param_adds = "\n".join([
                f"FamilyParameter {pg[0].lower().replace('-','_').replace(' ','_')} = "
                f"famMgr.AddParameter(\"{pg[0]}\", BuiltInParameterGroup.PG_DATA, "
                f"ParameterType.Text, false);"
                for pg in param_groups
            ])
            samples.append(_s(
                f"Create a {desc} named '{family_name}' with fire rating compliance parameters "
                f"including: {', '.join(pg[0] for pg in param_groups)}.",
                f"```csharp\n"
                f"// Fire rating compliance parameters for {desc}\n"
                f"// Allowed values:\n"
                f"{param_block}\n\n"
                f"Document famDoc = app.OpenDocumentFile(@\"C:\\\\ProgramData\\\\Autodesk\\\\RVT 2024\\\\"
                f"Libraries\\\\{family_name}.rfa\");\n"
                f"FamilyManager famMgr = famDoc.FamilyManager;\n\n"
                f"// Add compliance parameters (no Transaction needed for FamilyManager):\n"
                f"{param_adds}\n\n"
                f"// Set default type values:\n"
                f"FamilyType defaultType = famMgr.CurrentType;\n"
                f"famMgr.Set(famMgr.get_Parameter(\"FireRating\"), \"1-hour\");\n\n"
                f"famDoc.Save();\n"
                f"famDoc.Close(false);\n"
                f"```",
            ))

        # Detailed fire door example
        samples.append(_s(
            "Create a fire-rated door family with IBC-compliant fire rating and smoke label parameters, "
            "and create three family types: 1-hour 900mm, 1.5-hour 900mm, 2-hour 900mm.",
            "```csharp\n"
            "double MM_TO_FT = 1.0 / 304.8;\n"
            "Document famDoc = app.OpenDocumentFile(\n"
            "    @\"C:\\\\ProgramData\\\\Autodesk\\\\RVT 2024\\\\Libraries\\\\M_Single-Flush.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "// Add IBC compliance parameters:\n"
            "FamilyParameter fireRating = famMgr.AddParameter(\n"
            "    \"FireRating\", BuiltInParameterGroup.PG_DATA, ParameterType.Text, false);\n"
            "FamilyParameter smokeLabel = famMgr.AddParameter(\n"
            "    \"SmokeLabel\", BuiltInParameterGroup.PG_DATA, ParameterType.YesNo, false);\n"
            "FamilyParameter positiveLatching = famMgr.AddParameter(\n"
            "    \"PositiveLatching\", BuiltInParameterGroup.PG_DATA, ParameterType.YesNo, false);\n"
            "FamilyParameter selfClosing = famMgr.AddParameter(\n"
            "    \"SelfClosing\", BuiltInParameterGroup.PG_DATA, ParameterType.YesNo, false);\n\n"
            "FamilyParameter width  = famMgr.get_Parameter(\"Width\");\n"
            "FamilyParameter height = famMgr.get_Parameter(\"Height\");\n\n"
            "// Type 1: 1-hour, 900x2100mm\n"
            "FamilyType t1 = famMgr.NewType(\"1hr-900x2100\");\n"
            "famMgr.CurrentType = t1;\n"
            "famMgr.Set(fireRating, \"1-hour\");\n"
            "famMgr.Set(smokeLabel, 1);\n"
            "famMgr.Set(positiveLatching, 1);\n"
            "famMgr.Set(selfClosing, 1);\n"
            "famMgr.Set(width,  900  * MM_TO_FT);\n"
            "famMgr.Set(height, 2100 * MM_TO_FT);\n\n"
            "// Type 2: 1.5-hour, 900x2100mm\n"
            "FamilyType t2 = famMgr.NewType(\"1.5hr-900x2100\");\n"
            "famMgr.CurrentType = t2;\n"
            "famMgr.Set(fireRating, \"1.5-hour\");\n"
            "famMgr.Set(smokeLabel, 1);\n"
            "famMgr.Set(positiveLatching, 1);\n"
            "famMgr.Set(selfClosing, 1);\n"
            "famMgr.Set(width,  900  * MM_TO_FT);\n"
            "famMgr.Set(height, 2100 * MM_TO_FT);\n\n"
            "// Type 3: 2-hour, 900x2100mm\n"
            "FamilyType t3 = famMgr.NewType(\"2hr-900x2100\");\n"
            "famMgr.CurrentType = t3;\n"
            "famMgr.Set(fireRating, \"2-hour\");\n"
            "famMgr.Set(smokeLabel, 1);\n"
            "famMgr.Set(positiveLatching, 1);\n"
            "famMgr.Set(selfClosing, 1);\n"
            "famMgr.Set(width,  900  * MM_TO_FT);\n"
            "famMgr.Set(height, 2100 * MM_TO_FT);\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        # Stairwell door fire separation
        samples.append(_s(
            "Add fire rating parameters to a stairwell door family per IBC Section 716. "
            "The door assembly needs FireRating (1-hour or 1.5-hour), CloserRequired, and PanicHardware fields.",
            "```csharp\n"
            "double MM_TO_FT = 1.0 / 304.8;\n"
            "double INCH_TO_FT = 1.0 / 12.0;\n"
            "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\StairwellDoor.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "// IBC 716 required parameters:\n"
            "FamilyParameter fireRating = famMgr.AddParameter(\n"
            "    \"FireRating\", BuiltInParameterGroup.PG_DATA, ParameterType.Text, false);\n"
            "FamilyParameter closerRequired = famMgr.AddParameter(\n"
            "    \"CloserRequired\", BuiltInParameterGroup.PG_DATA, ParameterType.YesNo, false);\n"
            "FamilyParameter panicHardware = famMgr.AddParameter(\n"
            "    \"PanicHardware\", BuiltInParameterGroup.PG_DATA, ParameterType.YesNo, false);\n"
            "FamilyParameter visionLiteMaxArea = famMgr.AddParameter(\n"
            "    \"VisionLiteMaxArea_sqin\", BuiltInParameterGroup.PG_DATA, ParameterType.Number, false);\n\n"
            "FamilyParameter width  = famMgr.get_Parameter(\"Width\");\n"
            "FamilyParameter height = famMgr.get_Parameter(\"Height\");\n\n"
            "// Minimum egress width per IBC: 32 inches clear\n"
            "FamilyType standard = famMgr.NewType(\"1.5hr-36x84in\");\n"
            "famMgr.CurrentType = standard;\n"
            "famMgr.Set(fireRating, \"1.5-hour\"); // IBC 716.5.3 - 1.5-hour for exit enclosures\n"
            "famMgr.Set(closerRequired, 1);\n"
            "famMgr.Set(panicHardware, 1);\n"
            "famMgr.Set(visionLiteMaxArea, 100); // max 100 sq in vision lite per IBC\n"
            "famMgr.Set(width,  36 * INCH_TO_FT); // 36 inches\n"
            "famMgr.Set(height, 84 * INCH_TO_FT); // 84 inches\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        return samples

    # ------------------------------------------------------------------
    # Egress parameters
    # ------------------------------------------------------------------
    def _egress_params(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        # Basic egress door
        samples.append(_s(
            "Create an egress door family with IBC-required parameters: clear width, clear height, "
            "OccupantLoad, and EgressDirection. Minimum clear width must be 32 inches.",
            "```csharp\n"
            "double INCH_TO_FT = 1.0 / 12.0;\n"
            "double MM_TO_FT   = 1.0 / 304.8;\n"
            "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\EgressDoor.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "// IBC egress compliance parameters:\n"
            "FamilyParameter clearWidth = famMgr.AddParameter(\n"
            "    \"ClearWidth\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter clearHeight = famMgr.AddParameter(\n"
            "    \"ClearHeight\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter occupantLoad = famMgr.AddParameter(\n"
            "    \"OccupantLoad\", BuiltInParameterGroup.PG_DATA, ParameterType.Integer, false);\n"
            "FamilyParameter egressDir = famMgr.AddParameter(\n"
            "    \"EgressDirection\", BuiltInParameterGroup.PG_DATA, ParameterType.Text, false);\n"
            "FamilyParameter isEgressDoor = famMgr.AddParameter(\n"
            "    \"IsEgressDoor\", BuiltInParameterGroup.PG_DATA, ParameterType.YesNo, false);\n\n"
            "// IBC minimum egress: 32 inch clear width, 80 inch clear height\n"
            "FamilyType egress32 = famMgr.NewType(\"Egress-32inClear\");\n"
            "famMgr.CurrentType = egress32;\n"
            "famMgr.Set(clearWidth,  32 * INCH_TO_FT);\n"
            "famMgr.Set(clearHeight, 80 * INCH_TO_FT);\n"
            "famMgr.Set(occupantLoad, 50);\n"
            "famMgr.Set(egressDir, \"Swing-Out\");\n"
            "famMgr.Set(isEgressDoor, 1);\n\n"
            "// IBC high-occupancy: 36 inch clear width\n"
            "FamilyType egress36 = famMgr.NewType(\"Egress-36inClear\");\n"
            "famMgr.CurrentType = egress36;\n"
            "famMgr.Set(clearWidth,  36 * INCH_TO_FT);\n"
            "famMgr.Set(clearHeight, 80 * INCH_TO_FT);\n"
            "famMgr.Set(occupantLoad, 150);\n"
            "famMgr.Set(egressDir, \"Swing-Out\");\n"
            "famMgr.Set(isEgressDoor, 1);\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        # Corridor width
        samples.append(_s(
            "Create a corridor family with egress width parameters. Per IBC Table 1005.1, "
            "minimum corridor width is 44 inches (or 36 inches for fewer than 50 occupants).",
            "```csharp\n"
            "double INCH_TO_FT = 1.0 / 12.0;\n"
            "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\Corridor.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "FamilyParameter corridorWidth = famMgr.AddParameter(\n"
            "    \"CorridorWidth\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter minEgressWidth = famMgr.AddParameter(\n"
            "    \"MinimumEgressWidth\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter designOccupantLoad = famMgr.AddParameter(\n"
            "    \"DesignOccupantLoad\", BuiltInParameterGroup.PG_DATA, ParameterType.Integer, false);\n"
            "FamilyParameter sprinklered = famMgr.AddParameter(\n"
            "    \"Sprinklered\", BuiltInParameterGroup.PG_DATA, ParameterType.YesNo, false);\n\n"
            "// Type A: High occupancy corridor (>50 occupants) - 44 inch min\n"
            "FamilyType typeA = famMgr.NewType(\"HighOcc-44in\");\n"
            "famMgr.CurrentType = typeA;\n"
            "famMgr.Set(corridorWidth,      48 * INCH_TO_FT);\n"
            "famMgr.Set(minEgressWidth,     44 * INCH_TO_FT); // IBC 1005.1\n"
            "famMgr.Set(designOccupantLoad, 100);\n"
            "famMgr.Set(sprinklered, 1);\n\n"
            "// Type B: Low occupancy corridor (<50 occupants) - 36 inch min\n"
            "FamilyType typeB = famMgr.NewType(\"LowOcc-36in\");\n"
            "famMgr.CurrentType = typeB;\n"
            "famMgr.Set(corridorWidth,      36 * INCH_TO_FT);\n"
            "famMgr.Set(minEgressWidth,     36 * INCH_TO_FT); // IBC 1005.1 exception\n"
            "famMgr.Set(designOccupantLoad, 30);\n"
            "famMgr.Set(sprinklered, 0);\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        # Stair family
        samples.append(_s(
            "Create a stair family with IBC-compliant compliance parameters: "
            "MinTreadDepth (11 inch min), MaxRiserHeight (7 inch max), MinWidth (44 inch min).",
            "```csharp\n"
            "double INCH_TO_FT = 1.0 / 12.0;\n"
            "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\Stair.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "// IBC Chapter 10 stair parameters:\n"
            "FamilyParameter treadDepth = famMgr.AddParameter(\n"
            "    \"TreadDepth\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter riserHeight = famMgr.AddParameter(\n"
            "    \"RiserHeight\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter stairWidth = famMgr.AddParameter(\n"
            "    \"StairWidth\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter handrailRequired = famMgr.AddParameter(\n"
            "    \"HandrailRequired\", BuiltInParameterGroup.PG_DATA, ParameterType.YesNo, false);\n"
            "FamilyParameter guardrailRequired = famMgr.AddParameter(\n"
            "    \"GuardrailRequired\", BuiltInParameterGroup.PG_DATA, ParameterType.YesNo, false);\n\n"
            "// Standard commercial stair - IBC compliant\n"
            "FamilyType commercial = famMgr.NewType(\"Commercial-IBC\");\n"
            "famMgr.CurrentType = commercial;\n"
            "famMgr.Set(treadDepth,       11 * INCH_TO_FT); // IBC 1011.5.2 min 11 in\n"
            "famMgr.Set(riserHeight,       7 * INCH_TO_FT); // IBC 1011.5.2 max 7 in\n"
            "famMgr.Set(stairWidth,       44 * INCH_TO_FT); // IBC 1011.2 min 44 in\n"
            "famMgr.Set(handrailRequired, 1);\n"
            "famMgr.Set(guardrailRequired, 1);\n\n"
            "// Residential stair - IRC compliant\n"
            "FamilyType residential = famMgr.NewType(\"Residential-IRC\");\n"
            "famMgr.CurrentType = residential;\n"
            "famMgr.Set(treadDepth,      10 * INCH_TO_FT); // IRC min 10 in with nosing\n"
            "famMgr.Set(riserHeight,      7.75 * INCH_TO_FT); // IRC max 7-3/4 in\n"
            "famMgr.Set(stairWidth,      36 * INCH_TO_FT); // IRC min 36 in\n"
            "famMgr.Set(handrailRequired, 1);\n"
            "famMgr.Set(guardrailRequired, 1);\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        # Exit sign
        samples.append(_s(
            "Create an exit sign family with IBC-required visibility parameters: "
            "ViewingDistance, IlluminationLevel, and BackupPowerDuration.",
            "```csharp\n"
            "double INCH_TO_FT = 1.0 / 12.0;\n"
            "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\ExitSign.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "FamilyParameter viewingDistance = famMgr.AddParameter(\n"
            "    \"ViewingDistance\", BuiltInParameterGroup.PG_DATA, ParameterType.Length, false);\n"
            "FamilyParameter illumination = famMgr.AddParameter(\n"
            "    \"IlluminationLevel_fc\", BuiltInParameterGroup.PG_DATA, ParameterType.Number, false);\n"
            "FamilyParameter backupPower = famMgr.AddParameter(\n"
            "    \"BackupPowerDuration_hr\", BuiltInParameterGroup.PG_DATA, ParameterType.Number, false);\n"
            "FamilyParameter letterHeight = famMgr.AddParameter(\n"
            "    \"LetterHeight\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n\n"
            "// IBC 1013 exit sign requirements\n"
            "FamilyType standard = famMgr.NewType(\"Standard-100ft\");\n"
            "famMgr.CurrentType = standard;\n"
            "famMgr.Set(viewingDistance, 100 * (1.0/3.2808)); // 100 ft in feet\n"
            "famMgr.Set(illumination, 5.0);    // 5 footcandles per NFPA 101\n"
            "famMgr.Set(backupPower, 1.5);     // 90 minutes min per IBC 1013.6.3\n"
            "famMgr.Set(letterHeight, 6 * INCH_TO_FT); // 6 inch letters per IBC 1013.4\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        # Occupant load factor
        samples.append(_s(
            "Add OccupantLoad and OccupancyClassification parameters to a room family per IBC Table 1004.5.",
            "```csharp\n"
            "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\Room.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "FamilyParameter occupancy = famMgr.AddParameter(\n"
            "    \"OccupancyClassification\", BuiltInParameterGroup.PG_DATA, ParameterType.Text, false);\n"
            "FamilyParameter loadFactor = famMgr.AddParameter(\n"
            "    \"OccupantLoadFactor_sqftPerOccupant\", BuiltInParameterGroup.PG_DATA,\n"
            "    ParameterType.Number, false);\n"
            "FamilyParameter calculatedLoad = famMgr.AddParameter(\n"
            "    \"CalculatedOccupantLoad\", BuiltInParameterGroup.PG_DATA, ParameterType.Integer, false);\n"
            "FamilyParameter floorArea = famMgr.AddParameter(\n"
            "    \"GrossFloorArea\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Area, false);\n\n"
            "// Occupancy types per IBC Table 1004.5:\n"
            "// Assembly - concentrated: 7 gross sf/occupant\n"
            "// Business: 150 gross sf/occupant\n"
            "// Educational - classroom: 20 net sf/occupant\n"
            "// Storage: 300 gross sf/occupant\n\n"
            "FamilyType assembly = famMgr.NewType(\"Assembly-Concentrated\");\n"
            "famMgr.CurrentType = assembly;\n"
            "famMgr.Set(occupancy, \"Assembly - Concentrated (IBC 1004.5)\");\n"
            "famMgr.Set(loadFactor, 7.0);\n"
            "famMgr.SetFormula(calculatedLoad, \"round(GrossFloorArea / (OccupantLoadFactor_sqftPerOccupant / 10.764))\");\n\n"
            "FamilyType business = famMgr.NewType(\"Business\");\n"
            "famMgr.CurrentType = business;\n"
            "famMgr.Set(occupancy, \"Business (IBC 1004.5)\");\n"
            "famMgr.Set(loadFactor, 150.0);\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        return samples

    # ------------------------------------------------------------------
    # ADA clearance parameters
    # ------------------------------------------------------------------
    def _ada_clearance_params(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        # ADA door
        samples.append(_s(
            "Create an ADA-compliant door family with accessibility parameters: "
            "ClearWidth (32 in min), ManeuveringClearance, and ThresholdHeight.",
            "```csharp\n"
            "double INCH_TO_FT = 1.0 / 12.0;\n"
            "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\ADAdoor.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "// ADA Standards 404.2 door parameters:\n"
            "FamilyParameter clearWidth = famMgr.AddParameter(\n"
            "    \"ClearWidth\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter approachClearance = famMgr.AddParameter(\n"
            "    \"ManeuveringClearance\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter thresholdHeight = famMgr.AddParameter(\n"
            "    \"ThresholdHeight\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter closingSpeed = famMgr.AddParameter(\n"
            "    \"ClosingSpeedMin_sec\", BuiltInParameterGroup.PG_DATA, ParameterType.Number, false);\n"
            "FamilyParameter isAccessible = famMgr.AddParameter(\n"
            "    \"IsADAAccessible\", BuiltInParameterGroup.PG_DATA, ParameterType.YesNo, false);\n\n"
            "// ADA minimum: 32 inch clear width (measured at 90-degree open position)\n"
            "FamilyType adaMin = famMgr.NewType(\"ADA-32inClear\");\n"
            "famMgr.CurrentType = adaMin;\n"
            "famMgr.Set(clearWidth,        32 * INCH_TO_FT); // ADA 404.2.3 min 32 in\n"
            "famMgr.Set(approachClearance, 18 * INCH_TO_FT); // ADA 404.2.4 latch-side clearance\n"
            "famMgr.Set(thresholdHeight,  0.5 * INCH_TO_FT); // ADA 404.2.5 max 1/2 in\n"
            "famMgr.Set(closingSpeed,     5.0);               // ADA 404.2.8 min 5 seconds\n"
            "famMgr.Set(isAccessible, 1);\n\n"
            "// Preferred: 36 inch clear width\n"
            "FamilyType adaPref = famMgr.NewType(\"ADA-36inClear\");\n"
            "famMgr.CurrentType = adaPref;\n"
            "famMgr.Set(clearWidth,        36 * INCH_TO_FT);\n"
            "famMgr.Set(approachClearance, 18 * INCH_TO_FT);\n"
            "famMgr.Set(thresholdHeight,  0.5 * INCH_TO_FT);\n"
            "famMgr.Set(closingSpeed,     5.0);\n"
            "famMgr.Set(isAccessible, 1);\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        # Accessible parking space
        samples.append(_s(
            "Create an accessible parking space family with ADA-required dimensions: "
            "SpaceWidth (96 in min for standard, 132 in for van-accessible), AisleWidth (60 in min).",
            "```csharp\n"
            "double INCH_TO_FT = 1.0 / 12.0;\n"
            "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\ParkingSpace.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "// ADA 502 parking space parameters:\n"
            "FamilyParameter spaceWidth = famMgr.AddParameter(\n"
            "    \"SpaceWidth\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter spaceLength = famMgr.AddParameter(\n"
            "    \"SpaceLength\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter aisleWidth = famMgr.AddParameter(\n"
            "    \"AccessAisleWidth\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter isVanAccessible = famMgr.AddParameter(\n"
            "    \"IsVanAccessible\", BuiltInParameterGroup.PG_DATA, ParameterType.YesNo, false);\n"
            "FamilyParameter vertClearance = famMgr.AddParameter(\n"
            "    \"VerticalClearance\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n\n"
            "// Standard accessible space: ADA 502.2\n"
            "FamilyType standard = famMgr.NewType(\"Accessible-Standard\");\n"
            "famMgr.CurrentType = standard;\n"
            "famMgr.Set(spaceWidth,      96 * INCH_TO_FT);  // ADA 502.2 min 96 in\n"
            "famMgr.Set(spaceLength,    240 * INCH_TO_FT);  // typical 20 ft\n"
            "famMgr.Set(aisleWidth,      60 * INCH_TO_FT);  // ADA 502.3 min 60 in\n"
            "famMgr.Set(isVanAccessible, 0);\n"
            "famMgr.Set(vertClearance,   98 * INCH_TO_FT);  // ADA 502.5 min 98 in\n\n"
            "// Van-accessible space: ADA 502.2 exception\n"
            "FamilyType van = famMgr.NewType(\"Accessible-Van\");\n"
            "famMgr.CurrentType = van;\n"
            "famMgr.Set(spaceWidth,     132 * INCH_TO_FT);  // ADA 502.2 van: 132 in\n"
            "famMgr.Set(spaceLength,    240 * INCH_TO_FT);\n"
            "famMgr.Set(aisleWidth,      60 * INCH_TO_FT);\n"
            "famMgr.Set(isVanAccessible, 1);\n"
            "famMgr.Set(vertClearance,   98 * INCH_TO_FT);\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        # Ramp
        samples.append(_s(
            "Create an ADA-compliant ramp family with slope, width, and landing parameters "
            "per ADA Standards 405.",
            "```csharp\n"
            "double INCH_TO_FT = 1.0 / 12.0;\n"
            "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\Ramp.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "// ADA 405 ramp parameters:\n"
            "FamilyParameter rampSlope = famMgr.AddParameter(\n"
            "    \"RampSlope_ratio\", BuiltInParameterGroup.PG_DATA, ParameterType.Number, false);\n"
            "FamilyParameter rampWidth = famMgr.AddParameter(\n"
            "    \"ClearWidth\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter maxRise = famMgr.AddParameter(\n"
            "    \"MaxRise\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter landingLength = famMgr.AddParameter(\n"
            "    \"LandingLength\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter edgeProtection = famMgr.AddParameter(\n"
            "    \"EdgeProtectionRequired\", BuiltInParameterGroup.PG_DATA, ParameterType.YesNo, false);\n\n"
            "// ADA compliant ramp:\n"
            "FamilyType adaRamp = famMgr.NewType(\"ADA-1-12slope\");\n"
            "famMgr.CurrentType = adaRamp;\n"
            "famMgr.Set(rampSlope,     1.0 / 12.0); // ADA 405.2 max 1:12 slope\n"
            "famMgr.Set(rampWidth,     36 * INCH_TO_FT); // ADA 405.5 min 36 in\n"
            "famMgr.Set(maxRise,       30 * INCH_TO_FT); // ADA 405.6 max 30 in rise\n"
            "famMgr.Set(landingLength, 60 * INCH_TO_FT); // ADA 405.7 min 60 in landing\n"
            "famMgr.Set(edgeProtection, 1);\n\n"
            "// Steeper allowed for space constraints (short runs):\n"
            "FamilyType steepRamp = famMgr.NewType(\"ADA-1-8slope-shortrun\");\n"
            "famMgr.CurrentType = steepRamp;\n"
            "famMgr.Set(rampSlope,     1.0 / 8.0); // ADA 405.2 max 1:8 for 3 inch max rise\n"
            "famMgr.Set(rampWidth,     36 * INCH_TO_FT);\n"
            "famMgr.Set(maxRise,        3 * INCH_TO_FT); // limited to 3 inches at 1:8\n"
            "famMgr.Set(landingLength, 60 * INCH_TO_FT);\n"
            "famMgr.Set(edgeProtection, 1);\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        # Restroom fixture
        samples.append(_s(
            "Create an ADA-compliant water closet family with required clearance parameters: "
            "SideWallClearance (60 in), FrontClearance (60 in), SeatHeight (17-19 in).",
            "```csharp\n"
            "double INCH_TO_FT = 1.0 / 12.0;\n"
            "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\WaterCloset.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "// ADA 604 water closet clearance parameters:\n"
            "FamilyParameter sideWallClear = famMgr.AddParameter(\n"
            "    \"SideWallClearance\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter frontClear = famMgr.AddParameter(\n"
            "    \"FrontClearance\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter seatHeight = famMgr.AddParameter(\n"
            "    \"SeatHeight\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter grabBarSide = famMgr.AddParameter(\n"
            "    \"GrabBarSideWall\", BuiltInParameterGroup.PG_DATA, ParameterType.YesNo, false);\n"
            "FamilyParameter grabBarRear = famMgr.AddParameter(\n"
            "    \"GrabBarRearWall\", BuiltInParameterGroup.PG_DATA, ParameterType.YesNo, false);\n\n"
            "// ADA 604 compliant type:\n"
            "FamilyType adaWC = famMgr.NewType(\"ADA-Compliant\");\n"
            "famMgr.CurrentType = adaWC;\n"
            "famMgr.Set(sideWallClear, 60 * INCH_TO_FT); // ADA 604.3.1 min 60 in from side wall\n"
            "famMgr.Set(frontClear,    60 * INCH_TO_FT); // ADA 604.3.1 min 60 in from front\n"
            "famMgr.Set(seatHeight,    17 * INCH_TO_FT); // ADA 604.4 min 17 in seat height\n"
            "famMgr.Set(grabBarSide,  1); // ADA 604.5 required\n"
            "famMgr.Set(grabBarRear,  1); // ADA 604.5 required\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        # Reach range
        samples.append(_s(
            "Add ADA reach range parameters to a casework family: "
            "MaxHighReach (48 in), MinLowReach (15 in), and ObstructedReach limits.",
            "```csharp\n"
            "double INCH_TO_FT = 1.0 / 12.0;\n"
            "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\Casework.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "// ADA 308 reach range parameters:\n"
            "FamilyParameter maxHighReach = famMgr.AddParameter(\n"
            "    \"MaxHighReach\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter minLowReach = famMgr.AddParameter(\n"
            "    \"MinLowReach\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter counterHeight = famMgr.AddParameter(\n"
            "    \"AccessibleCounterHeight\", BuiltInParameterGroup.PG_GEOMETRY,\n"
            "    ParameterType.Length, false);\n"
            "FamilyParameter kneeSpace = famMgr.AddParameter(\n"
            "    \"KneeClearanceHeight\", BuiltInParameterGroup.PG_GEOMETRY,\n"
            "    ParameterType.Length, false);\n\n"
            "// ADA standard reach ranges:\n"
            "FamilyType adaCasework = famMgr.NewType(\"ADA-Accessible\");\n"
            "famMgr.CurrentType = adaCasework;\n"
            "famMgr.Set(maxHighReach,     48 * INCH_TO_FT); // ADA 308.2 max 48 in\n"
            "famMgr.Set(minLowReach,      15 * INCH_TO_FT); // ADA 308.2 min 15 in\n"
            "famMgr.Set(counterHeight,    34 * INCH_TO_FT); // ADA 902.3 max 34 in\n"
            "famMgr.Set(kneeSpace,        27 * INCH_TO_FT); // ADA 306.3 min 27 in\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        return samples

    # ------------------------------------------------------------------
    # Structural compliance parameters
    # ------------------------------------------------------------------
    def _structural_compliance_params(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        samples.append(_s(
            "Add structural compliance parameters to a beam family: "
            "DesignLoad_kips, DeflectionLimit_ratio (L/360 live, L/240 total), "
            "CamberRequired, and FireRating.",
            "```csharp\n"
            "double INCH_TO_FT = 1.0 / 12.0;\n"
            "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\StructuralBeam.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "// AISC/IBC structural compliance parameters:\n"
            "FamilyParameter designLoad = famMgr.AddParameter(\n"
            "    \"DesignLoad_kips\", BuiltInParameterGroup.PG_STRUCTURAL, ParameterType.Number, false);\n"
            "FamilyParameter liveDeflection = famMgr.AddParameter(\n"
            "    \"LiveLoadDeflectionLimit\", BuiltInParameterGroup.PG_STRUCTURAL,\n"
            "    ParameterType.Number, false); // L/xxx ratio\n"
            "FamilyParameter totalDeflection = famMgr.AddParameter(\n"
            "    \"TotalLoadDeflectionLimit\", BuiltInParameterGroup.PG_STRUCTURAL,\n"
            "    ParameterType.Number, false);\n"
            "FamilyParameter camberRequired = famMgr.AddParameter(\n"
            "    \"CamberRequired\", BuiltInParameterGroup.PG_STRUCTURAL, ParameterType.YesNo, false);\n"
            "FamilyParameter fireRating = famMgr.AddParameter(\n"
            "    \"FireRating\", BuiltInParameterGroup.PG_DATA, ParameterType.Text, false);\n"
            "FamilyParameter seismicCategory = famMgr.AddParameter(\n"
            "    \"SeismicDesignCategory\", BuiltInParameterGroup.PG_DATA, ParameterType.Text, false);\n\n"
            "// Standard office floor beam:\n"
            "FamilyType officeBeam = famMgr.NewType(\"OfficeFloor-SDC-B\");\n"
            "famMgr.CurrentType = officeBeam;\n"
            "famMgr.Set(designLoad,       50.0);    // 50 kips\n"
            "famMgr.Set(liveDeflection,   360.0);   // L/360 for live load\n"
            "famMgr.Set(totalDeflection,  240.0);   // L/240 for total load\n"
            "famMgr.Set(camberRequired,   1);\n"
            "famMgr.Set(fireRating,       \"2-hour\");\n"
            "famMgr.Set(seismicCategory,  \"B\");\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        samples.append(_s(
            "Add seismic compliance parameters to a structural column family: "
            "SeismicDesignCategory, R_factor, OmegaFactor, and BraceRequired.",
            "```csharp\n"
            "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\StructuralColumn.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "// ASCE 7 seismic parameters:\n"
            "FamilyParameter sdc = famMgr.AddParameter(\n"
            "    \"SeismicDesignCategory\", BuiltInParameterGroup.PG_STRUCTURAL,\n"
            "    ParameterType.Text, false);\n"
            "FamilyParameter rFactor = famMgr.AddParameter(\n"
            "    \"R_ResponseModification\", BuiltInParameterGroup.PG_STRUCTURAL,\n"
            "    ParameterType.Number, false);\n"
            "FamilyParameter omega = famMgr.AddParameter(\n"
            "    \"Omega_Overstrength\", BuiltInParameterGroup.PG_STRUCTURAL,\n"
            "    ParameterType.Number, false);\n"
            "FamilyParameter braceRequired = famMgr.AddParameter(\n"
            "    \"BracingRequired\", BuiltInParameterGroup.PG_STRUCTURAL, ParameterType.YesNo, false);\n"
            "FamilyParameter systemType = famMgr.AddParameter(\n"
            "    \"LateralSystem\", BuiltInParameterGroup.PG_STRUCTURAL, ParameterType.Text, false);\n\n"
            "// Special Moment Frame (SMF) - SDC D:\n"
            "FamilyType smf = famMgr.NewType(\"SMF-SDC-D\");\n"
            "famMgr.CurrentType = smf;\n"
            "famMgr.Set(sdc,           \"D\");\n"
            "famMgr.Set(rFactor,       8.0); // ASCE 7 Table 12.2-1 SMF\n"
            "famMgr.Set(omega,         3.0);\n"
            "famMgr.Set(braceRequired, 0);\n"
            "famMgr.Set(systemType,    \"Special Moment Frame\");\n\n"
            "// Ordinary Braced Frame (OBF) - SDC B:\n"
            "FamilyType obf = famMgr.NewType(\"OBF-SDC-B\");\n"
            "famMgr.CurrentType = obf;\n"
            "famMgr.Set(sdc,           \"B\");\n"
            "famMgr.Set(rFactor,       3.25); // ASCE 7 Table 12.2-1 OBF\n"
            "famMgr.Set(omega,         2.0);\n"
            "famMgr.Set(braceRequired, 1);\n"
            "famMgr.Set(systemType,    \"Ordinary Concentrically Braced Frame\");\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        samples.append(_s(
            "Add wind load compliance parameters to a curtain wall family per ASCE 7 Chapter 30.",
            "```csharp\n"
            "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\CurtainWallPanel.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "// ASCE 7 Chapter 30 CWFS parameters:\n"
            "FamilyParameter windPressurePos = famMgr.AddParameter(\n"
            "    \"DesignWindPressure_pos_psf\", BuiltInParameterGroup.PG_STRUCTURAL,\n"
            "    ParameterType.Number, false);\n"
            "FamilyParameter windPressureNeg = famMgr.AddParameter(\n"
            "    \"DesignWindPressure_neg_psf\", BuiltInParameterGroup.PG_STRUCTURAL,\n"
            "    ParameterType.Number, false);\n"
            "FamilyParameter exposureCategory = famMgr.AddParameter(\n"
            "    \"ExposureCategory\", BuiltInParameterGroup.PG_STRUCTURAL,\n"
            "    ParameterType.Text, false);\n"
            "FamilyParameter riskCategory = famMgr.AddParameter(\n"
            "    \"RiskCategory\", BuiltInParameterGroup.PG_STRUCTURAL, ParameterType.Text, false);\n"
            "FamilyParameter deflectionLimit = famMgr.AddParameter(\n"
            "    \"DeflectionLimit_ratio\", BuiltInParameterGroup.PG_STRUCTURAL,\n"
            "    ParameterType.Number, false);\n\n"
            "// Exposure C, Risk Category II:\n"
            "FamilyType expC = famMgr.NewType(\"ExposureC-RiskII\");\n"
            "famMgr.CurrentType = expC;\n"
            "famMgr.Set(windPressurePos,   30.0); // +30 psf inward\n"
            "famMgr.Set(windPressureNeg,  -35.0); // -35 psf outward (suction)\n"
            "famMgr.Set(exposureCategory,  \"C\");\n"
            "famMgr.Set(riskCategory,      \"II\");\n"
            "famMgr.Set(deflectionLimit,   175.0); // L/175 per AAMA 501\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        return samples

    # ------------------------------------------------------------------
    # MEP clearance parameters
    # ------------------------------------------------------------------
    def _mep_clearance_params(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        samples.append(_s(
            "Add NEC clearance parameters to an electrical panel family: "
            "WorkingSpaceDepth (36 in min), WorkingSpaceWidth (30 in min), "
            "WorkingSpaceHeight (6.5 ft min), and Dedicated_Above clearance.",
            "```csharp\n"
            "double INCH_TO_FT = 1.0 / 12.0;\n"
            "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\ElectricalPanel.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "// NEC 110.26 working space clearance parameters:\n"
            "FamilyParameter workDepth = famMgr.AddParameter(\n"
            "    \"WorkingSpaceDepth\", BuiltInParameterGroup.PG_GEOMETRY,\n"
            "    ParameterType.Length, false);\n"
            "FamilyParameter workWidth = famMgr.AddParameter(\n"
            "    \"WorkingSpaceWidth\", BuiltInParameterGroup.PG_GEOMETRY,\n"
            "    ParameterType.Length, false);\n"
            "FamilyParameter workHeight = famMgr.AddParameter(\n"
            "    \"WorkingSpaceHeight\", BuiltInParameterGroup.PG_GEOMETRY,\n"
            "    ParameterType.Length, false);\n"
            "FamilyParameter dedicatedSpace = famMgr.AddParameter(\n"
            "    \"DedicatedSpaceAbove_ft\", BuiltInParameterGroup.PG_GEOMETRY,\n"
            "    ParameterType.Length, false);\n"
            "FamilyParameter voltageClass = famMgr.AddParameter(\n"
            "    \"VoltageClass\", BuiltInParameterGroup.PG_DATA, ParameterType.Text, false);\n\n"
            "// 0-150V to ground (Condition 1): 36 in depth\n"
            "FamilyType v150 = famMgr.NewType(\"0-150V-Cond1\");\n"
            "famMgr.CurrentType = v150;\n"
            "famMgr.Set(workDepth,     36 * INCH_TO_FT); // NEC 110.26(A)(1) Table\n"
            "famMgr.Set(workWidth,     30 * INCH_TO_FT); // NEC 110.26(A)(2)\n"
            "famMgr.Set(workHeight,     6.5);             // NEC 110.26(A)(3) 6.5 ft\n"
            "famMgr.Set(dedicatedSpace, 6.5);             // NEC 110.26(F) to structural ceiling\n"
            "famMgr.Set(voltageClass,  \"0-150V\");\n\n"
            "// 151-600V to ground (Condition 1): 42 in depth\n"
            "FamilyType v600 = famMgr.NewType(\"151-600V-Cond1\");\n"
            "famMgr.CurrentType = v600;\n"
            "famMgr.Set(workDepth,    42 * INCH_TO_FT); // NEC 110.26(A)(1) Table\n"
            "famMgr.Set(workWidth,    30 * INCH_TO_FT);\n"
            "famMgr.Set(workHeight,    6.5);\n"
            "famMgr.Set(dedicatedSpace, 6.5);\n"
            "famMgr.Set(voltageClass, \"151-600V\");\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        samples.append(_s(
            "Add plumbing clearance parameters to a water heater family per IPC: "
            "ServiceClearance (24 in front), FlueVentClearance, and ExpansionTankRequired.",
            "```csharp\n"
            "double INCH_TO_FT = 1.0 / 12.0;\n"
            "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\WaterHeater.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "// IPC / manufacturer clearance parameters:\n"
            "FamilyParameter frontClear = famMgr.AddParameter(\n"
            "    \"FrontServiceClearance\", BuiltInParameterGroup.PG_GEOMETRY,\n"
            "    ParameterType.Length, false);\n"
            "FamilyParameter sideClear = famMgr.AddParameter(\n"
            "    \"SideClearance\", BuiltInParameterGroup.PG_GEOMETRY,\n"
            "    ParameterType.Length, false);\n"
            "FamilyParameter flueClear = famMgr.AddParameter(\n"
            "    \"FlueClearanceToCombus\", BuiltInParameterGroup.PG_GEOMETRY,\n"
            "    ParameterType.Length, false);\n"
            "FamilyParameter expansionTank = famMgr.AddParameter(\n"
            "    \"ExpansionTankRequired\", BuiltInParameterGroup.PG_DATA,\n"
            "    ParameterType.YesNo, false);\n"
            "FamilyParameter tprValve = famMgr.AddParameter(\n"
            "    \"TPRValveRequired\", BuiltInParameterGroup.PG_DATA,\n"
            "    ParameterType.YesNo, false);\n\n"
            "FamilyType gasWH = famMgr.NewType(\"Gas-40gal\");\n"
            "famMgr.CurrentType = gasWH;\n"
            "famMgr.Set(frontClear,   24 * INCH_TO_FT); // typical service access\n"
            "famMgr.Set(sideClear,     6 * INCH_TO_FT);\n"
            "famMgr.Set(flueClear,     6 * INCH_TO_FT); // clearance to combustibles\n"
            "famMgr.Set(expansionTank, 1);               // required in closed systems\n"
            "famMgr.Set(tprValve,      1);               // IPC 504.6 required\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        samples.append(_s(
            "Add ASHRAE 62.1 ventilation parameters to a mechanical unit family: "
            "OutdoorAirFlow_cfm, ExhaustAirFlow_cfm, and OccupancyGroup.",
            "```csharp\n"
            "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\AHU.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "// ASHRAE 62.1 ventilation parameters:\n"
            "FamilyParameter oaFlow = famMgr.AddParameter(\n"
            "    \"OutdoorAirFlow_cfm\", BuiltInParameterGroup.PG_MECHANICAL,\n"
            "    ParameterType.Number, false);\n"
            "FamilyParameter exhaustFlow = famMgr.AddParameter(\n"
            "    \"ExhaustAirFlow_cfm\", BuiltInParameterGroup.PG_MECHANICAL,\n"
            "    ParameterType.Number, false);\n"
            "FamilyParameter occupancyGroup = famMgr.AddParameter(\n"
            "    \"OccupancyGroup\", BuiltInParameterGroup.PG_DATA, ParameterType.Text, false);\n"
            "FamilyParameter oaRatePerPerson = famMgr.AddParameter(\n"
            "    \"OA_cfmPerPerson\", BuiltInParameterGroup.PG_MECHANICAL,\n"
            "    ParameterType.Number, false);\n"
            "FamilyParameter oaRatePerArea = famMgr.AddParameter(\n"
            "    \"OA_cfmPerSqft\", BuiltInParameterGroup.PG_MECHANICAL,\n"
            "    ParameterType.Number, false);\n\n"
            "// ASHRAE 62.1 Table 6-1 - Office:\n"
            "FamilyType office = famMgr.NewType(\"Office-ASHRAE621\");\n"
            "famMgr.CurrentType = office;\n"
            "famMgr.Set(oaFlow,         1000.0); // design OA flow cfm\n"
            "famMgr.Set(exhaustFlow,     800.0);\n"
            "famMgr.Set(occupancyGroup, \"Office Space\");\n"
            "famMgr.Set(oaRatePerPerson, 5.0);  // ASHRAE 62.1 Table 6-1: 5 cfm/person\n"
            "famMgr.Set(oaRatePerArea,   0.06); // ASHRAE 62.1 Table 6-1: 0.06 cfm/sqft\n\n"
            "// ASHRAE 62.1 Table 6-1 - Conference Room:\n"
            "FamilyType conf = famMgr.NewType(\"Conference-ASHRAE621\");\n"
            "famMgr.CurrentType = conf;\n"
            "famMgr.Set(oaFlow,         2000.0);\n"
            "famMgr.Set(exhaustFlow,    1800.0);\n"
            "famMgr.Set(occupancyGroup, \"Conference/Meeting\");\n"
            "famMgr.Set(oaRatePerPerson, 7.5); // ASHRAE 62.1 Table 6-1: 7.5 cfm/person\n"
            "famMgr.Set(oaRatePerArea,   0.06);\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        return samples

    # ------------------------------------------------------------------
    # Occupancy parameters
    # ------------------------------------------------------------------
    def _occupancy_params(self) -> List[SAMPLE]:
        samples: List[SAMPLE] = []

        samples.append(_s(
            "Add IBC occupancy classification parameters to a space family: "
            "OccupancyGroup (A-1 through S-2), ConstructionType, and SprinklerRequired.",
            "```csharp\n"
            "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\Space.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "// IBC Chapter 3 occupancy parameters:\n"
            "FamilyParameter occGroup = famMgr.AddParameter(\n"
            "    \"OccupancyGroup\", BuiltInParameterGroup.PG_DATA, ParameterType.Text, false);\n"
            "FamilyParameter constType = famMgr.AddParameter(\n"
            "    \"ConstructionType\", BuiltInParameterGroup.PG_DATA, ParameterType.Text, false);\n"
            "FamilyParameter sprinklerReq = famMgr.AddParameter(\n"
            "    \"SprinklerRequired\", BuiltInParameterGroup.PG_DATA, ParameterType.YesNo, false);\n"
            "FamilyParameter maxOccupantLoad = famMgr.AddParameter(\n"
            "    \"MaxOccupantLoad\", BuiltInParameterGroup.PG_DATA, ParameterType.Integer, false);\n"
            "FamilyParameter maxTravelDist = famMgr.AddParameter(\n"
            "    \"MaxTravelDistance\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n\n"
            "double INCH_TO_FT = 1.0 / 12.0;\n\n"
            "// Assembly Group A-2 (restaurants/bars):\n"
            "FamilyType a2 = famMgr.NewType(\"A-2-Restaurant\");\n"
            "famMgr.CurrentType = a2;\n"
            "famMgr.Set(occGroup,        \"A-2\");\n"
            "famMgr.Set(constType,       \"Type I-A\");\n"
            "famMgr.Set(sprinklerReq,    1);\n"
            "famMgr.Set(maxOccupantLoad, 500);\n"
            "famMgr.Set(maxTravelDist,   250 * INCH_TO_FT * 12); // 250 ft with sprinklers\n\n"
            "// Business Group B:\n"
            "FamilyType b = famMgr.NewType(\"B-Office\");\n"
            "famMgr.CurrentType = b;\n"
            "famMgr.Set(occGroup,        \"B\");\n"
            "famMgr.Set(constType,       \"Type II-B\");\n"
            "famMgr.Set(sprinklerReq,    0);\n"
            "famMgr.Set(maxOccupantLoad, 100);\n"
            "famMgr.Set(maxTravelDist,   200 * INCH_TO_FT * 12); // 200 ft without sprinklers\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        samples.append(_s(
            "Create a family type catalog for a fire suppression sprinkler head with "
            "coverage area and K-factor compliance parameters.",
            "```csharp\n"
            "double INCH_TO_FT = 1.0 / 12.0;\n"
            "double MM_TO_FT = 1.0 / 304.8;\n"
            "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\SprinklerHead.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "// NFPA 13 sprinkler parameters:\n"
            "FamilyParameter kFactor = famMgr.AddParameter(\n"
            "    \"K_Factor\", BuiltInParameterGroup.PG_DATA, ParameterType.Number, false);\n"
            "FamilyParameter maxCoverage = famMgr.AddParameter(\n"
            "    \"MaxCoverageArea_sqft\", BuiltInParameterGroup.PG_DATA, ParameterType.Number, false);\n"
            "FamilyParameter tempRating = famMgr.AddParameter(\n"
            "    \"TemperatureRating_F\", BuiltInParameterGroup.PG_DATA, ParameterType.Number, false);\n"
            "FamilyParameter hazardGroup = famMgr.AddParameter(\n"
            "    \"HazardOccupancyGroup\", BuiltInParameterGroup.PG_DATA, ParameterType.Text, false);\n"
            "FamilyParameter minSpacing = famMgr.AddParameter(\n"
            "    \"MinSpacing\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n\n"
            "// K-5.6 Standard Response (Light Hazard):\n"
            "FamilyType k56 = famMgr.NewType(\"K5.6-LightHazard\");\n"
            "famMgr.CurrentType = k56;\n"
            "famMgr.Set(kFactor,       5.6);\n"
            "famMgr.Set(maxCoverage,   225.0); // NFPA 13 Table 8.6.2.2.1 LH: 225 sqft\n"
            "famMgr.Set(tempRating,    155.0); // 155F ordinary temperature rating\n"
            "famMgr.Set(hazardGroup,   \"Light Hazard\");\n"
            "famMgr.Set(minSpacing,    6 * INCH_TO_FT * 12); // 6 ft min spacing\n\n"
            "// K-8.0 Standard Response (Ordinary Hazard Group 1):\n"
            "FamilyType k80 = famMgr.NewType(\"K8.0-OrdinaryHazard1\");\n"
            "famMgr.CurrentType = k80;\n"
            "famMgr.Set(kFactor,       8.0);\n"
            "famMgr.Set(maxCoverage,   130.0); // NFPA 13 OH1: 130 sqft\n"
            "famMgr.Set(tempRating,    155.0);\n"
            "famMgr.Set(hazardGroup,   \"Ordinary Hazard Group 1\");\n"
            "famMgr.Set(minSpacing,    6 * INCH_TO_FT * 12);\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        samples.append(_s(
            "Add energy code compliance parameters to a window family per IECC: "
            "U_Factor, SHGC, and visible transmittance (VT).",
            "```csharp\n"
            "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\Window.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "// IECC / NFRC energy parameters:\n"
            "FamilyParameter uFactor = famMgr.AddParameter(\n"
            "    \"U_Factor\", BuiltInParameterGroup.PG_DATA, ParameterType.Number, false);\n"
            "FamilyParameter shgc = famMgr.AddParameter(\n"
            "    \"SHGC\", BuiltInParameterGroup.PG_DATA, ParameterType.Number, false);\n"
            "FamilyParameter vt = famMgr.AddParameter(\n"
            "    \"VisibleTransmittance\", BuiltInParameterGroup.PG_DATA, ParameterType.Number, false);\n"
            "FamilyParameter climateZone = famMgr.AddParameter(\n"
            "    \"IECCClimateZone\", BuiltInParameterGroup.PG_DATA, ParameterType.Text, false);\n"
            "FamilyParameter nfrcCertified = famMgr.AddParameter(\n"
            "    \"NFRCCertified\", BuiltInParameterGroup.PG_DATA, ParameterType.YesNo, false);\n\n"
            "// IECC 2021 Zone 4A (Mixed-Humid) commercial fenestration:\n"
            "FamilyType zone4a = famMgr.NewType(\"Zone4A-DoublePane\");\n"
            "famMgr.CurrentType = zone4a;\n"
            "famMgr.Set(uFactor,    0.29);  // IECC 2021 Table C402.4 Zone 4 max U=0.29\n"
            "famMgr.Set(shgc,       0.25);  // IECC 2021 Table C402.4 Zone 4 max SHGC=0.25\n"
            "famMgr.Set(vt,         0.40);\n"
            "famMgr.Set(climateZone, \"4A\");\n"
            "famMgr.Set(nfrcCertified, 1);\n\n"
            "// IECC 2021 Zone 1A (Hot-Humid) commercial:\n"
            "FamilyType zone1a = famMgr.NewType(\"Zone1A-LowSHGC\");\n"
            "famMgr.CurrentType = zone1a;\n"
            "famMgr.Set(uFactor,    0.50);\n"
            "famMgr.Set(shgc,       0.22);  // Zone 1-3 max SHGC\n"
            "famMgr.Set(vt,         0.35);\n"
            "famMgr.Set(climateZone, \"1A\");\n"
            "famMgr.Set(nfrcCertified, 1);\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        samples.append(_s(
            "Add life safety parameters to an exit lighting fixture family per IBC 1008: "
            "IlluminationLevel_fc (1 fc min), BackupDuration_hr (90 min min), and TestSwitch.",
            "```csharp\n"
            "double INCH_TO_FT = 1.0 / 12.0;\n"
            "Document famDoc = app.OpenDocumentFile(@\"C:\\\\path\\\\ExitLight.rfa\");\n"
            "FamilyManager famMgr = famDoc.FamilyManager;\n\n"
            "// IBC 1008 / NFPA 101 egress illumination parameters:\n"
            "FamilyParameter illumination = famMgr.AddParameter(\n"
            "    \"IlluminationLevel_fc\", BuiltInParameterGroup.PG_DATA, ParameterType.Number, false);\n"
            "FamilyParameter backupDuration = famMgr.AddParameter(\n"
            "    \"BackupDuration_hr\", BuiltInParameterGroup.PG_DATA, ParameterType.Number, false);\n"
            "FamilyParameter testSwitch = famMgr.AddParameter(\n"
            "    \"TestSwitchRequired\", BuiltInParameterGroup.PG_DATA, ParameterType.YesNo, false);\n"
            "FamilyParameter mountingHeight = famMgr.AddParameter(\n"
            "    \"MountingHeight\", BuiltInParameterGroup.PG_GEOMETRY, ParameterType.Length, false);\n"
            "FamilyParameter batteryBackup = famMgr.AddParameter(\n"
            "    \"BatteryBackup\", BuiltInParameterGroup.PG_DATA, ParameterType.YesNo, false);\n\n"
            "// IBC 1008.3 egress path luminaire:\n"
            "FamilyType egress = famMgr.NewType(\"Egress-IBC1008\");\n"
            "famMgr.CurrentType = egress;\n"
            "famMgr.Set(illumination,    1.0);              // IBC 1008.3 min 1 fc at floor\n"
            "famMgr.Set(backupDuration,  1.5);              // IBC 1008.3 90 min = 1.5 hr\n"
            "famMgr.Set(testSwitch,      1);\n"
            "famMgr.Set(mountingHeight,  8 * INCH_TO_FT * 12); // 8 ft mounting height\n"
            "famMgr.Set(batteryBackup,   1);\n\n"
            "famDoc.Save();\n"
            "famDoc.Close(false);\n"
            "```",
        ))

        return samples
