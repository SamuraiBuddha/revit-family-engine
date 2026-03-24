"""Training pipeline orchestrator for Revit Family Engine.

Stages: Collect -> Generate -> Parameterize -> Export

Usage:
    python training_pipeline/run_pipeline.py --output-dir output --format alpaca
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training_pipeline.generators.family_geometry_generator import FamilyGeometryGenerator
from training_pipeline.generators.family_parameter_generator import FamilyParameterGenerator
from training_pipeline.generators.family_type_generator import FamilyTypeGenerator
from training_pipeline.generators.gdt_annotation_generator import GDTAnnotationGenerator
from training_pipeline.generators.reference_constraint_generator import ReferenceConstraintGenerator
from training_pipeline.generators.dynamo_script_generator import DynamoScriptGenerator
from training_pipeline.generators.structural_family_generator import StructuralFamilyGenerator
from training_pipeline.generators.advanced_family_generator import AdvancedFamilyGenerator
from training_pipeline.generators.wall_family_generator import WallFamilyGenerator
from training_pipeline.generators.revit_api_reference_generator import RevitAPIReferenceGenerator
from training_pipeline.generators.building_code_compliance_generator import BuildingCodeComplianceGenerator
from training_pipeline.generators.mep_family_generator import MEPFamilyGenerator
from training_pipeline.parameterization_data_generator import ParameterizationDataGenerator

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

SAMPLE = Dict[str, Any]



# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(output_dir: str, fmt: str, max_per_space: int) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    all_samples: List[SAMPLE] = []

    generators = [
        ("FamilyGeometryGenerator",      FamilyGeometryGenerator()),
        ("FamilyParameterGenerator",     FamilyParameterGenerator()),
        ("GDTAnnotationGenerator",       GDTAnnotationGenerator()),
        ("ReferenceConstraintGenerator", ReferenceConstraintGenerator()),
        ("FamilyTypeGenerator",          FamilyTypeGenerator()),
        ("DynamoScriptGenerator",        DynamoScriptGenerator()),
        ("BuildingCodeComplianceGenerator", BuildingCodeComplianceGenerator()),
        ("WallFamilyGenerator",          WallFamilyGenerator()),
        ("StructuralFamilyGenerator",    StructuralFamilyGenerator()),
        ("MEPFamilyGenerator",           MEPFamilyGenerator()),
        ("AdvancedFamilyGenerator",      AdvancedFamilyGenerator()),
        ("RevitAPIReferenceGenerator",   RevitAPIReferenceGenerator()),
    ]

    for name, gen in generators:
        samples = gen.generate()
        logger.info("[OK] %s: %d samples", name, len(samples))
        all_samples.extend(samples)

    # Parameterization data (Cartesian product)
    param_gen = ParameterizationDataGenerator(max_combinations_per_space=max_per_space)
    param_samples = param_gen.generate_all()
    logger.info("[OK] ParameterizationDataGenerator: %d samples", len(param_samples))
    all_samples.extend(param_samples)

    logger.info("[OK] Total training samples: %d", len(all_samples))

    # Export
    if fmt == "alpaca":
        output_path = out / "revit_training_data.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_samples, f, indent=2, ensure_ascii=False)
    else:
        output_path = out / "revit_training_data.jsonl"
        with open(output_path, "w", encoding="utf-8") as f:
            for s in all_samples:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")

    logger.info("[OK] Saved to %s", output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Revit Family Engine training pipeline")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--format", choices=["alpaca", "jsonl"], default="alpaca")
    parser.add_argument("--max-per-space", type=int, default=200)
    args = parser.parse_args()
    run_pipeline(args.output_dir, args.format, args.max_per_space)


if __name__ == "__main__":
    main()
