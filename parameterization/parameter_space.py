"""Revit Family Engine -- parameterization framework.

Mirrors the sw-semantic-engine pattern: ParameterSpace definitions drive
Cartesian-product training data generation.

CRITICAL: Revit internal units are FEET for length, RADIANS for angles.
All ParameterDefinition values here are in mm/degrees for human readability;
the resolver converts before emitting C# code.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, Iterator, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ParameterType(Enum):
    # Geometric dimensions
    LENGTH = auto()
    WIDTH = auto()
    HEIGHT = auto()
    DEPTH = auto()
    RADIUS = auto()
    DIAMETER = auto()
    ANGLE = auto()
    THICKNESS = auto()
    OFFSET_VALUE = auto()

    # Revit Family parameters
    INSTANCE_PARAM = auto()
    TYPE_PARAM = auto()
    MATERIAL_PARAM = auto()
    YES_NO_PARAM = auto()
    FAMILY_TYPE_PARAM = auto()
    INTEGER_PARAM = auto()
    TEXT_PARAM = auto()
    URL_PARAM = auto()
    NUMBER_PARAM = auto()

    # Constraints / references
    DIMENSION_CONSTRAINT = auto()
    ALIGNMENT_CONSTRAINT = auto()
    LOCK_CONSTRAINT = auto()
    EQUALITY_CONSTRAINT = auto()

    # Geometry operations
    EXTRUSION_DEPTH = auto()
    REVOLUTION_ANGLE = auto()
    BLEND_DEPTH = auto()
    SWEEP_PATH = auto()

    # GD&T
    TOLERANCE_VALUE = auto()
    DATUM_REFERENCE = auto()
    MATERIAL_MODIFIER = auto()
    GEOMETRIC_CHARACTERISTIC = auto()
    SURFACE_FINISH = auto()

    # Revit-specific
    SUBCATEGORY = auto()
    VISIBILITY_PARAM = auto()
    FORMULA = auto()

    # Dynamo
    NODE_INPUT = auto()
    NODE_OUTPUT = auto()
    GRAPH_VARIABLE = auto()


class ParameterDomain(Enum):
    FAMILY_GEOMETRY = "family_geometry"
    FAMILY_PARAMETERS = "family_parameters"
    CONSTRAINTS = "constraints"
    FAMILY_TYPES = "family_types"
    GDT = "gdt"
    DYNAMO = "dynamo"
    BUILDING_CODE = "building_code"


class ParameterConstraint(Enum):
    POSITIVE = "positive"
    NON_NEGATIVE = "non_negative"
    RANGE = "range"
    DISCRETE = "discrete"
    EXPRESSED = "expressed"


# ---------------------------------------------------------------------------
# Core data classes
# ---------------------------------------------------------------------------

@dataclass
class ParameterDefinition:
    name: str
    parameter_type: ParameterType
    domain: ParameterDomain
    default_value: Any
    constraint: ParameterConstraint = ParameterConstraint.RANGE
    min_value: float = 0.0
    max_value: float = 1000.0
    discrete_values: List[Any] = field(default_factory=list)
    unit: str = "mm"
    precision: int = 1
    tolerance_plus: float = 0.0
    tolerance_minus: float = 0.0
    description: str = ""
    source: str = ""
    dependent_on: List[str] = field(default_factory=list)
    affects: List[str] = field(default_factory=list)
    is_instance: bool = True

    def validate(self, value: Any) -> Tuple[bool, str]:
        if self.constraint == ParameterConstraint.POSITIVE:
            if float(value) <= 0:
                return False, f"{self.name} must be > 0"
        elif self.constraint == ParameterConstraint.NON_NEGATIVE:
            if float(value) < 0:
                return False, f"{self.name} must be >= 0"
        elif self.constraint == ParameterConstraint.RANGE:
            v = float(value)
            if not (self.min_value <= v <= self.max_value):
                return False, f"{self.name}={v} out of range [{self.min_value}, {self.max_value}]"
        elif self.constraint == ParameterConstraint.DISCRETE:
            if value not in self.discrete_values:
                return False, f"{self.name}={value} not in {self.discrete_values}"
        return True, ""

    def sample_values(self, n: int = 3) -> List[Any]:
        if self.constraint == ParameterConstraint.DISCRETE:
            return list(self.discrete_values)
        if self.constraint in (ParameterConstraint.RANGE, ParameterConstraint.POSITIVE,
                               ParameterConstraint.NON_NEGATIVE):
            lo = max(self.min_value, 1e-6 if self.constraint == ParameterConstraint.POSITIVE else 0)
            hi = self.max_value
            step = (hi - lo) / max(n - 1, 1)
            return [round(lo + i * step, self.precision) for i in range(n)]
        return [self.default_value]


@dataclass
class ParameterSpace:
    name: str
    description: str
    parameters: Dict[str, ParameterDefinition] = field(default_factory=dict)

    def add_parameter(self, param: ParameterDefinition) -> None:
        self.parameters[param.name] = param

    def get_parameter(self, name: str) -> Optional[ParameterDefinition]:
        return self.parameters.get(name)

    def get_parameters_by_domain(self, domain: ParameterDomain) -> List[ParameterDefinition]:
        return [p for p in self.parameters.values() if p.domain == domain]

    def parameter_count(self) -> int:
        return len(self.parameters)

    def combination_count(self, samples_per_param: int = 3) -> int:
        total = 1
        for p in self.parameters.values():
            total *= len(p.sample_values(samples_per_param))
        return total

    def cartesian_product(self, samples_per_param: int = 3) -> Iterator["ParameterAssignment"]:
        names = list(self.parameters.keys())
        value_lists = [self.parameters[n].sample_values(samples_per_param) for n in names]
        for combo in itertools.product(*value_lists):
            assignment = ParameterAssignment(parameter_space=self, values={})
            for name, value in zip(names, combo):
                assignment.values[name] = value
            yield assignment

    def validate_assignment(self, name: str, value: Any) -> Tuple[bool, str]:
        param = self.get_parameter(name)
        if param is None:
            return False, f"Unknown parameter: {name}"
        return param.validate(value)


@dataclass
class ParameterAssignment:
    parameter_space: ParameterSpace
    values: Dict[str, Any] = field(default_factory=dict)

    def set_value(self, name: str, value: Any) -> None:
        ok, err = self.parameter_space.validate_assignment(name, value)
        if not ok:
            raise ValueError(err)
        self.values[name] = value

    def get_value(self, name: str) -> Any:
        return self.values.get(name, self.parameter_space.parameters[name].default_value)

    def to_feet(self, name: str) -> float:
        """Return a length param converted to Revit internal units (feet)."""
        v = float(self.get_value(name))
        param = self.parameter_space.parameters.get(name)
        if param and param.unit == "mm":
            return v / 304.8
        if param and param.unit == "m":
            return v / 0.3048
        return v  # assume already in feet

    def to_radians(self, name: str) -> float:
        """Return an angle param converted to radians."""
        import math
        v = float(self.get_value(name))
        param = self.parameter_space.parameters.get(name)
        if param and param.unit in ("deg", "degrees"):
            return math.radians(v)
        return v

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.values)


# ---------------------------------------------------------------------------
# Predefined parameter spaces
# ---------------------------------------------------------------------------

def _wall_family_space() -> ParameterSpace:
    space = ParameterSpace(
        name="wall_family",
        description="Generic wall-hosted or face-based family with Width, Height, Thickness",
    )
    space.add_parameter(ParameterDefinition(
        name="Width", parameter_type=ParameterType.WIDTH,
        domain=ParameterDomain.FAMILY_PARAMETERS,
        default_value=1200, constraint=ParameterConstraint.RANGE,
        min_value=300, max_value=3000, unit="mm", precision=0,
        description="Family width", is_instance=False,
    ))
    space.add_parameter(ParameterDefinition(
        name="Height", parameter_type=ParameterType.HEIGHT,
        domain=ParameterDomain.FAMILY_PARAMETERS,
        default_value=2400, constraint=ParameterConstraint.RANGE,
        min_value=600, max_value=4500, unit="mm", precision=0,
        description="Family height", is_instance=False,
    ))
    space.add_parameter(ParameterDefinition(
        name="Thickness", parameter_type=ParameterType.THICKNESS,
        domain=ParameterDomain.FAMILY_PARAMETERS,
        default_value=200, constraint=ParameterConstraint.RANGE,
        min_value=50, max_value=600, unit="mm", precision=0,
        description="Family thickness / depth", is_instance=False,
    ))
    return space


def _door_family_space() -> ParameterSpace:
    space = ParameterSpace(
        name="door_family",
        description="Door family with Rough Width, Rough Height, Frame Depth",
    )
    space.add_parameter(ParameterDefinition(
        name="Rough Width", parameter_type=ParameterType.WIDTH,
        domain=ParameterDomain.FAMILY_PARAMETERS,
        default_value=914, constraint=ParameterConstraint.DISCRETE,
        discrete_values=[610, 762, 864, 914, 991, 1067],
        unit="mm", precision=0, is_instance=False,
    ))
    space.add_parameter(ParameterDefinition(
        name="Rough Height", parameter_type=ParameterType.HEIGHT,
        domain=ParameterDomain.FAMILY_PARAMETERS,
        default_value=2134, constraint=ParameterConstraint.DISCRETE,
        discrete_values=[1981, 2032, 2134, 2438],
        unit="mm", precision=0, is_instance=False,
    ))
    space.add_parameter(ParameterDefinition(
        name="Frame Depth", parameter_type=ParameterType.DEPTH,
        domain=ParameterDomain.FAMILY_PARAMETERS,
        default_value=90, constraint=ParameterConstraint.RANGE,
        min_value=60, max_value=150, unit="mm", precision=0, is_instance=True,
    ))
    return space


def _column_family_space() -> ParameterSpace:
    space = ParameterSpace(
        name="column_family",
        description="Structural column family (rectangular) with Width, Depth, b, d params",
    )
    for name, default, lo, hi in [
        ("b", 300, 150, 900),
        ("d", 300, 150, 900),
        ("Height", 3000, 1500, 9000),
    ]:
        space.add_parameter(ParameterDefinition(
            name=name, parameter_type=ParameterType.LENGTH,
            domain=ParameterDomain.FAMILY_PARAMETERS,
            default_value=default, constraint=ParameterConstraint.RANGE,
            min_value=lo, max_value=hi, unit="mm", precision=0, is_instance=False,
        ))
    space.add_parameter(ParameterDefinition(
        name="Concrete Grade", parameter_type=ParameterType.TEXT_PARAM,
        domain=ParameterDomain.FAMILY_PARAMETERS,
        default_value="C25/30", constraint=ParameterConstraint.DISCRETE,
        discrete_values=["C20/25", "C25/30", "C30/37", "C35/45", "C40/50"],
        unit="", is_instance=False,
    ))
    space.add_parameter(ParameterDefinition(
        name="Fire Rating", parameter_type=ParameterType.TEXT_PARAM,
        domain=ParameterDomain.FAMILY_PARAMETERS,
        default_value="1hr", constraint=ParameterConstraint.DISCRETE,
        discrete_values=["None", "1hr", "2hr", "3hr", "4hr"],
        unit="", is_instance=False,
    ))
    return space


def _window_family_space() -> ParameterSpace:
    space = ParameterSpace(
        name="window_family",
        description="Window family with Rough Width, Rough Height, Sill Height, Frame Width",
    )
    space.add_parameter(ParameterDefinition(
        name="Rough Width", parameter_type=ParameterType.WIDTH,
        domain=ParameterDomain.FAMILY_PARAMETERS,
        default_value=1200, constraint=ParameterConstraint.DISCRETE,
        discrete_values=[600, 900, 1200, 1500, 1800, 2400],
        unit="mm", precision=0, is_instance=False,
    ))
    space.add_parameter(ParameterDefinition(
        name="Rough Height", parameter_type=ParameterType.HEIGHT,
        domain=ParameterDomain.FAMILY_PARAMETERS,
        default_value=1200, constraint=ParameterConstraint.DISCRETE,
        discrete_values=[600, 900, 1200, 1500],
        unit="mm", precision=0, is_instance=False,
    ))
    space.add_parameter(ParameterDefinition(
        name="Sill Height", parameter_type=ParameterType.OFFSET_VALUE,
        domain=ParameterDomain.FAMILY_PARAMETERS,
        default_value=900, constraint=ParameterConstraint.RANGE,
        min_value=300, max_value=1200, unit="mm", precision=0, is_instance=True,
    ))
    space.add_parameter(ParameterDefinition(
        name="Frame Width", parameter_type=ParameterType.WIDTH,
        domain=ParameterDomain.FAMILY_PARAMETERS,
        default_value=60, constraint=ParameterConstraint.RANGE,
        min_value=40, max_value=120, unit="mm", precision=0, is_instance=False,
    ))
    return space


def _extrusion_solid_space() -> ParameterSpace:
    space = ParameterSpace(
        name="extrusion_solid",
        description="Generic solid extrusion with Width, Depth, Height and optional material",
    )
    space.add_parameter(ParameterDefinition(
        name="Width", parameter_type=ParameterType.WIDTH,
        domain=ParameterDomain.FAMILY_GEOMETRY,
        default_value=300, constraint=ParameterConstraint.RANGE,
        min_value=50, max_value=2000, unit="mm", precision=0, is_instance=False,
    ))
    space.add_parameter(ParameterDefinition(
        name="Depth", parameter_type=ParameterType.DEPTH,
        domain=ParameterDomain.FAMILY_GEOMETRY,
        default_value=300, constraint=ParameterConstraint.RANGE,
        min_value=50, max_value=2000, unit="mm", precision=0, is_instance=False,
    ))
    space.add_parameter(ParameterDefinition(
        name="Height", parameter_type=ParameterType.EXTRUSION_DEPTH,
        domain=ParameterDomain.FAMILY_GEOMETRY,
        default_value=600, constraint=ParameterConstraint.RANGE,
        min_value=100, max_value=4000, unit="mm", precision=0, is_instance=False,
    ))
    space.add_parameter(ParameterDefinition(
        name="Extrusion Direction", parameter_type=ParameterType.TEXT_PARAM,
        domain=ParameterDomain.FAMILY_GEOMETRY,
        default_value="Positive", constraint=ParameterConstraint.DISCRETE,
        discrete_values=["Positive", "Negative", "Symmetric"],
        unit="", is_instance=False,
    ))
    space.add_parameter(ParameterDefinition(
        name="Material", parameter_type=ParameterType.MATERIAL_PARAM,
        domain=ParameterDomain.FAMILY_PARAMETERS,
        default_value="Default", constraint=ParameterConstraint.DISCRETE,
        discrete_values=["Default", "Concrete", "Steel", "Wood", "Glass"],
        unit="", is_instance=True,
    ))
    return space


PREDEFINED_SPACES: Dict[str, ParameterSpace] = {
    "wall_family": _wall_family_space(),
    "door_family": _door_family_space(),
    "column_family": _column_family_space(),
    "window_family": _window_family_space(),
    "extrusion_solid": _extrusion_solid_space(),
}
