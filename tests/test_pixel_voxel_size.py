"""Tests for the settable ``voxel_size`` / ``pixel_size`` convenience properties and
the canonical ``array_to_physical`` transform they read/write (Direction B), plus the
``AxisUnit`` enum binding.
"""

import pytest
from pydantic import ValidationError

from cets_data_model.models.models import Axis, Image2D, Tomogram


# --------------------------------------------------------------------------- #
# voxel_size (3D)                                                              #
# --------------------------------------------------------------------------- #


def test_voxel_size_scalar_roundtrip():
    tomo = Tomogram(id="tomo_1")
    tomo.voxel_size = 13.7
    vs = tomo.voxel_size
    assert vs.as_list() == [13.7, 13.7, 13.7]
    assert vs.is_isotropic
    assert vs.scalar == 13.7

    # stored as an ordinary Scale named array_to_physical between array/physical
    (ct,) = tomo.coordinate_transformations
    assert ct.name == "array_to_physical"
    assert ct.transformation_type == "scale"
    assert ct.input == "array"
    assert ct.output == "physical"
    assert ct.scale == [13.7, 13.7, 13.7]
    assert {cs.name for cs in tomo.coordinate_systems} >= {"array", "physical"}


def test_voxel_size_anisotropic():
    tomo = Tomogram(id="tomo_1")
    tomo.voxel_size = [1.0, 2.0, 3.0]
    assert tomo.voxel_size.as_list() == [1.0, 2.0, 3.0]
    assert not tomo.voxel_size.is_isotropic
    assert tomo.voxel_size.scalar is None


def test_voxel_size_absent_returns_none():
    assert Tomogram(id="tomo_1").voxel_size is None


def test_set_overwrites_existing_scale():
    tomo = Tomogram(id="tomo_1")
    tomo.voxel_size = 5.0
    tomo.voxel_size = 9.0
    scales = [
        c for c in tomo.coordinate_transformations if c.name == "array_to_physical"
    ]
    assert len(scales) == 1
    assert scales[0].scale == [9.0, 9.0, 9.0]
    # and the coordinate systems are not duplicated
    assert [cs.name for cs in tomo.coordinate_systems].count("array") == 1
    assert [cs.name for cs in tomo.coordinate_systems].count("physical") == 1


def test_voxel_size_not_serialized():
    tomo = Tomogram(id="tomo_1")
    tomo.voxel_size = 5.0
    assert "voxel_size" not in tomo.model_dump()
    assert "voxel_size" not in Tomogram.model_fields
    assert "voxel_size" not in Tomogram.model_json_schema().get("properties", {})


# --------------------------------------------------------------------------- #
# pixel_size (2D)                                                              #
# --------------------------------------------------------------------------- #


def test_pixel_size_2d_scalar():
    im = Image2D()
    im.pixel_size = 4.0
    assert im.pixel_size.as_list() == [4.0, 4.0]
    (ct,) = im.coordinate_transformations
    assert ct.name == "array_to_physical"
    assert ct.scale == [4.0, 4.0]


def test_pixel_size_absent_returns_none():
    assert Image2D().pixel_size is None


# --------------------------------------------------------------------------- #
# AxisUnit enum binding                                                        #
# --------------------------------------------------------------------------- #


def test_axis_unit_enum_accepts_canonical():
    for unit in ("angstrom", "pixel", "voxel", "nanometer"):
        Axis(name="x", axis_unit=unit, axis_type="space")


def test_axis_unit_enum_rejects_unknown():
    with pytest.raises(ValidationError):
        Axis(name="x", axis_unit="furlong", axis_type="space")
