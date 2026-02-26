from cets_data_model.models.models import Axis, CoordinateSystem, AxisType
from typing import Optional

"""Helper functions for generating CoordinateSystem objects"""

# Axis definitions
X_AXIS_LOGICAL = Axis(name="logical coordinates x axis", axis_unit="pixel/voxel", axis_type=AxisType.space)
Y_AXIS_LOGICAL = Axis(name="logical coordinates y axis", axis_unit="pixel/voxel", axis_type=AxisType.space)
Z_AXIS_LOGICAL = Axis(name="logical coordinates z axis", axis_unit="pixel/voxel", axis_type=AxisType.space)

X_AXIS_PHYSICAL = Axis(name="physical coordinates x axis", axis_unit="Ångstrom", axis_type=AxisType.space)
Y_AXIS_PHYSICAL = Axis(name="physical coordinates y axis", axis_unit="Ångstrom", axis_type=AxisType.space)
Z_AXIS_PHYSICAL = Axis(name="physical coordinates z axis", axis_unit="Ångstrom", axis_type=AxisType.space)


def physical_coords(name: str, dim: int) -> CoordinateSystem:
    """Generate physical coordinates object"""
    axes = [X_AXIS_PHYSICAL, Y_AXIS_PHYSICAL]
    name = name
    if dim == 3:
        axes.append(Z_AXIS_PHYSICAL)
    elif dim not in (2, 3):
        raise ValueError(f"{dim} is not a valid dimension")
    return CoordinateSystem(name=name, axes=axes)


def logical_coords(name: Optional[str] = None, dim: int = 2) -> CoordinateSystem:
    """Generate a logical coordinates object

    Gives the base logical coordinates if no name specified
    """
    name = "logical coordinates 2d" if name is None else name
    axes = [X_AXIS_LOGICAL, Y_AXIS_LOGICAL]
    if dim == 3:
        name = "logical coordinates 3d"
        axes.append(Z_AXIS_LOGICAL)
    elif dim not in (2, 3):
        raise ValueError(f"{dim} is not a valid dimension")
    return CoordinateSystem(name=name, axes=axes)
