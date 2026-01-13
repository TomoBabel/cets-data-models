from typing import Optional
from cets_data_model.models.models import Axis, CoordinateSystem

# Axis definitions
x_axis_logical = Axis(name="logical coordinates x axis", axis_unit="pixel/voxel")
y_axis_logical = Axis(name="logical coordinates y axis", axis_unit="pixel/voxel")
z_axis_logical = Axis(name="logical coordinates z axis", axis_unit="pixel/voxel")

x_axis_physical = Axis(name="physical coordinates x axis", axis_unit="Ångstrom")
y_axis_physical = Axis(name="physical coordinates y axis", axis_unit="Ångstrom")
z_axis_physical = Axis(name="physical coordinates z axis", axis_unit="Ångstrom")

# basic logical coords
BASE_LOGICAL_COORDS_2D = "base_logical_coordinates_2D"
BASE_LOGICAL_COORDS_3D = "base_logical_coordinates_3D"

# helper functions for generating coordinate systems


def physical_coords(name: str, dim: int) -> CoordinateSystem:
    """Generate physical coordinates object"""
    axes = [x_axis_physical, y_axis_physical]
    name = name
    if dim == 3:
        axes.append(z_axis_physical)
    elif dim not in (2, 3):
        raise ValueError(f"{dim} is not a valid dimension")
    return CoordinateSystem(name=name, axes=axes)


def logical_coords(name: Optional[str] = None, dim: int = 2) -> CoordinateSystem:
    """Generate physical coordinates object

    Gives the base logical coordinates if no name specified
    """
    name = BASE_LOGICAL_COORDS_2D if name is None else name
    axes = [x_axis_logical, y_axis_logical]
    if dim == 3:
        name = BASE_LOGICAL_COORDS_3D if name is None else name
        axes.append(z_axis_logical)
    elif dim not in (2, 3):
        raise ValueError(f"{dim} is not a valid dimension")
    return CoordinateSystem(name=name, axes=axes)
