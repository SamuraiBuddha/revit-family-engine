"""Tests for parameterization/parameter_space.py"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from parameterization.parameter_space import (
    PREDEFINED_SPACES,
    ParameterAssignment,
    ParameterConstraint,
    ParameterDefinition,
    ParameterDomain,
    ParameterSpace,
    ParameterType,
)


def test_predefined_spaces_exist():
    for name in ("wall_family", "door_family", "column_family", "window_family", "extrusion_solid"):
        assert name in PREDEFINED_SPACES


def test_wall_family_has_three_params():
    space = PREDEFINED_SPACES["wall_family"]
    assert space.parameter_count() == 3
    assert "Width" in space.parameters
    assert "Height" in space.parameters
    assert "Thickness" in space.parameters


def test_door_family_discrete_values():
    space = PREDEFINED_SPACES["door_family"]
    rough_width = space.get_parameter("Rough Width")
    assert rough_width is not None
    assert rough_width.constraint == ParameterConstraint.DISCRETE
    assert 914 in rough_width.discrete_values


def test_column_family_has_concrete_grade():
    space = PREDEFINED_SPACES["column_family"]
    grade = space.get_parameter("Concrete Grade")
    assert grade is not None
    assert "C25/30" in grade.discrete_values


def test_combination_count_reasonable():
    for name, space in PREDEFINED_SPACES.items():
        count = space.combination_count(samples_per_param=3)
        assert count > 0, f"{name} has zero combinations"
        assert count <= 10_000, f"{name} has too many combinations: {count}"


def test_cartesian_product_yields_assignments():
    space = PREDEFINED_SPACES["extrusion_solid"]
    combos = list(space.cartesian_product(samples_per_param=2))
    assert len(combos) > 0
    for combo in combos:
        assert isinstance(combo, ParameterAssignment)
        assert len(combo.values) == space.parameter_count()


def test_validate_assignment_range_ok():
    space = PREDEFINED_SPACES["wall_family"]
    ok, err = space.validate_assignment("Width", 1000)
    assert ok, err


def test_validate_assignment_range_fail():
    space = PREDEFINED_SPACES["wall_family"]
    ok, err = space.validate_assignment("Width", 50000)
    assert not ok
    assert "out of range" in err


def test_validate_assignment_discrete_ok():
    space = PREDEFINED_SPACES["door_family"]
    ok, err = space.validate_assignment("Rough Width", 914)
    assert ok, err


def test_validate_assignment_discrete_fail():
    space = PREDEFINED_SPACES["door_family"]
    ok, err = space.validate_assignment("Rough Width", 999)
    assert not ok


def test_validate_unknown_param():
    space = PREDEFINED_SPACES["wall_family"]
    ok, err = space.validate_assignment("NonExistent", 100)
    assert not ok
    assert "Unknown" in err


def test_parameter_assignment_to_feet():
    space = PREDEFINED_SPACES["wall_family"]
    assignment = ParameterAssignment(parameter_space=space, values={"Width": 304.8})
    ft = assignment.to_feet("Width")
    assert abs(ft - 1.0) < 1e-6, f"Expected 1.0 ft, got {ft}"


def test_sample_values_range():
    param = ParameterDefinition(
        name="test", parameter_type=ParameterType.LENGTH,
        domain=ParameterDomain.FAMILY_GEOMETRY,
        default_value=100, constraint=ParameterConstraint.RANGE,
        min_value=10, max_value=100, unit="mm",
    )
    vals = param.sample_values(n=5)
    assert len(vals) == 5
    assert vals[0] == pytest.approx(10.0, abs=1.0)
    assert vals[-1] == pytest.approx(100.0, abs=1.0)


def test_sample_values_discrete():
    param = ParameterDefinition(
        name="test", parameter_type=ParameterType.DISCRETE,
        domain=ParameterDomain.FAMILY_PARAMETERS,
        default_value="A", constraint=ParameterConstraint.DISCRETE,
        discrete_values=["A", "B", "C"], unit="",
    )
    vals = param.sample_values(n=10)
    assert set(vals) == {"A", "B", "C"}
