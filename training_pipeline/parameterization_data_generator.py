"""Cartesian-product training data generator for Revit Family Engine.

One ParameterSpace definition --> hundreds of Alpaca training pairs
via itertools.product of all parameter sample values.
"""

from __future__ import annotations

import itertools
import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, Iterator, List

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parameterization.parameter_space import (
    PREDEFINED_SPACES,
    ParameterAssignment,
    ParameterConstraint,
    ParameterDefinition,
    ParameterSpace,
    ParameterType,
)
from parameterization.parameter_resolver import ParameterResolver

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

SAMPLE = Dict[str, Any]
MM_TO_FT = 1.0 / 304.8


class ParameterizationDataGenerator:
    def __init__(
        self,
        resolver: ParameterResolver | None = None,
        samples_per_param: int = 3,
        max_combinations_per_space: int = 200,
        seed: int = 42,
    ) -> None:
        self.resolver = resolver or ParameterResolver()
        self.samples_per_param = samples_per_param
        self.max_combinations_per_space = max_combinations_per_space
        self._rng = random.Random(seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_all(
        self, spaces: Dict[str, ParameterSpace] | None = None
    ) -> List[SAMPLE]:
        spaces = spaces or PREDEFINED_SPACES
        all_samples: List[SAMPLE] = []
        for space_name, space in spaces.items():
            n = min(space.combination_count(self.samples_per_param),
                    self.max_combinations_per_space)
            logger.info(
                "Generating samples for space '%s' (%d combinations)",
                space_name, space.combination_count(self.samples_per_param),
            )
            samples = self._generate_for_space(space, n)
            logger.info("  --> %d samples generated for '%s'", len(samples), space_name)
            all_samples.extend(samples)
        logger.info("Total samples generated: %d", len(all_samples))
        return all_samples

    def export_to_alpaca(self, samples: List[SAMPLE], output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(samples, f, indent=2, ensure_ascii=False)
        logger.info("Exported %d samples to %s", len(samples), path)
        return path

    def export_to_jsonl(self, samples: List[SAMPLE], output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for sample in samples:
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")
        logger.info("Exported %d samples (jsonl) to %s", len(samples), path)
        return path

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _generate_for_space(self, space: ParameterSpace, max_n: int) -> List[SAMPLE]:
        names = list(space.parameters.keys())
        value_lists = [
            space.parameters[n].sample_values(self.samples_per_param) for n in names
        ]
        combos = list(itertools.product(*value_lists))

        if len(combos) > max_n:
            combos = self._rng.sample(combos, max_n)

        samples: List[SAMPLE] = []
        for combo in combos:
            assignment = ParameterAssignment(parameter_space=space, values={})
            for name, value in zip(names, combo):
                assignment.values[name] = value

            instruction = self._generate_instruction(assignment)
            code = self.resolver.resolve(assignment)
            if code.strip():
                samples.append({
                    "instruction": instruction,
                    "input": "",
                    "output": code,
                })
        return samples

    def _generate_instruction(self, assignment: ParameterAssignment) -> str:
        space = assignment.parameter_space
        parts = [f"Create a '{space.name}' Revit family with the following parameters:"]
        for name, param in space.parameters.items():
            value = assignment.get_value(name)
            unit_str = f" {param.unit}" if param.unit else ""
            if param.parameter_type in (
                ParameterType.LENGTH, ParameterType.WIDTH, ParameterType.HEIGHT,
                ParameterType.DEPTH, ParameterType.THICKNESS, ParameterType.EXTRUSION_DEPTH,
                ParameterType.OFFSET_VALUE, ParameterType.RADIUS, ParameterType.DIAMETER,
            ):
                parts.append(f"  - {name} = {value}{unit_str}")
            elif param.parameter_type == ParameterType.MATERIAL_PARAM:
                parts.append(f"  - {name} = '{value}' material")
            elif param.parameter_type == ParameterType.YES_NO_PARAM:
                parts.append(f"  - {name} = {'Yes' if value else 'No'}")
            else:
                parts.append(f"  - {name} = {value}")

        parts.append("Generate compilable Revit API C# code.")
        return "\n".join(parts)
