"""Tests for parameterization/parameter_resolver.py"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from parameterization.parameter_space import PREDEFINED_SPACES, ParameterAssignment
from parameterization.parameter_resolver import ParameterResolver, MM_TO_FT


@pytest.fixture
def resolver():
    return ParameterResolver()


def test_resolver_produces_nonempty_code(resolver):
    for name, space in PREDEFINED_SPACES.items():
        assignment = next(space.cartesian_product())
        code = resolver.resolve(assignment)
        assert code.strip(), f"Empty code for space '{name}'"


def test_resolver_wall_family_contains_family_manager(resolver):
    space = PREDEFINED_SPACES["wall_family"]
    assignment = next(space.cartesian_product())
    code = resolver.resolve(assignment)
    assert "FamilyManager" in code or "famMgr" in code


def test_resolver_extrusion_contains_transaction(resolver):
    space = PREDEFINED_SPACES["extrusion_solid"]
    assignment = next(space.cartesian_product())
    code = resolver.resolve(assignment)
    assert "Transaction" in code


def test_resolver_converts_mm_to_feet(resolver):
    space = PREDEFINED_SPACES["wall_family"]
    # Use the default assignment with Width=1200mm
    assignment = ParameterAssignment(parameter_space=space, values={
        "Width": 1200, "Height": 2400, "Thickness": 200
    })
    code = resolver.resolve(assignment)
    # 1200 mm = 3.937008 ft
    expected_ft = f"{1200 * MM_TO_FT:.6f}"
    assert expected_ft in code, f"Expected {expected_ft} ft in code"


def test_resolver_extrusion_solid_contains_extrusion_api(resolver):
    space = PREDEFINED_SPACES["extrusion_solid"]
    assignment = next(space.cartesian_product())
    code = resolver.resolve(assignment)
    assert "NewExtrusion" in code or "Extrusion" in code


def test_resolver_all_spaces_no_exception(resolver):
    for name, space in PREDEFINED_SPACES.items():
        for assignment in list(space.cartesian_product())[:3]:
            try:
                code = resolver.resolve(assignment)
                assert isinstance(code, str)
            except Exception as exc:
                pytest.fail(f"Resolver raised exception for space '{name}': {exc}")
