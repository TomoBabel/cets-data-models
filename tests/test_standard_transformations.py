from cets_data_model.standard_coordinate_systems import (
    physical_coords,
    logical_coords,
    BASE_LOGICAL_COORDS_2D,
    BASE_LOGICAL_COORDS_3D,
)
from cets_data_model.models.models import (
    CoordinateSystem,
)


def test_create_physical_coords_2d():
    pcoords = physical_coords(name="test", dim=2)
    assert isinstance(pcoords, CoordinateSystem)
    assert pcoords.name == "test"
    assert len(pcoords.axes) == 2
    assert pcoords.axes[0].axis_unit == "Ångstrom"
    assert pcoords.axes[1].axis_unit == "Ångstrom"


def test_create_physical_coords_3d():
    pcoords = physical_coords(name="test", dim=3)
    assert isinstance(pcoords, CoordinateSystem)
    assert pcoords.name == "test"
    assert len(pcoords.axes) == 3
    assert pcoords.axes[0].axis_unit == "Ångstrom"
    assert pcoords.axes[1].axis_unit == "Ångstrom"
    assert pcoords.axes[2].axis_unit == "Ångstrom"


def test_create_base_logical_coords_2d():
    lcoords = logical_coords(dim=2)
    assert isinstance(lcoords, CoordinateSystem)
    assert lcoords.name == BASE_LOGICAL_COORDS_2D
    assert len(lcoords.axes) == 2
    assert lcoords.axes[0].axis_unit == "pixel/voxel"
    assert lcoords.axes[1].axis_unit == "pixel/voxel"


def test_create_base_logical_coords_3d():
    lcoords = logical_coords(dim=3)
    print(lcoords)
    assert isinstance(lcoords, CoordinateSystem)
    assert lcoords.name == BASE_LOGICAL_COORDS_3D
    assert len(lcoords.axes) == 3
    assert lcoords.axes[0].axis_unit == "pixel/voxel"
    assert lcoords.axes[1].axis_unit == "pixel/voxel"
    assert lcoords.axes[2].axis_unit == "pixel/voxel"


def test_create_base_logical_coords_2d_with_name():
    lcoords = logical_coords(dim=2, name="test")
    assert isinstance(lcoords, CoordinateSystem)
    assert isinstance(lcoords, CoordinateSystem)
    assert lcoords.name == "test"
    assert len(lcoords.axes) == 2
    assert lcoords.axes[0].axis_unit == "pixel/voxel"
    assert lcoords.axes[1].axis_unit == "pixel/voxel"
