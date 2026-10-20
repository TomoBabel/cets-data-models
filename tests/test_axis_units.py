"""Axis units: array axes use pixel; other axes default to angstrom."""

import pytest
from pydantic import ValidationError

from cets_data_model.models import models


def test_array_axis_without_unit_gets_pixel_and_keeps_caller_data():
    data = {"name": "x", "axis_type": "array"}
    system = models.CoordinateSystem(name="array", axes=[data])
    assert system.axes[0].axis_unit == "pixel"
    assert data == {"name": "x", "axis_type": "array"}


@pytest.mark.parametrize("unit", ["angstrom", "nanometer", "micrometer"])
def test_array_axis_rejects_physical_units(unit):
    with pytest.raises(ValidationError, match="'pixel' unit"):
        models.Axis(name="x", axis_type="array", axis_unit=unit)


@pytest.mark.parametrize("unit", ["pixel/voxel", "voxel", "Ångstrom"])
def test_units_outside_the_enum_are_rejected(unit):
    with pytest.raises(ValidationError):
        models.Axis(name="x", axis_type="space", axis_unit=unit)


def test_other_axes_default_to_angstrom():
    assert models.Axis(name="x").axis_unit == "angstrom"
    assert models.Axis(name="x", axis_type="space").axis_unit == "angstrom"
    assert (
        models.Axis(name="x", axis_type="array", axis_unit="pixel").axis_unit == "pixel"
    )
