from cets_data_model.models.models import Axis, CoordinateSystem, AxisType, AxisUnit
from typing import Optional

"""Helper functions for generating CoordinateSystem objects.

`array_coords` / `physical_coords_canonical` build the canonical Direction-B systems
named ``array`` / ``physical`` (used by the pixel/voxel-size setters). The older
`logical_coords` / `physical_coords` remain for backwards compatibility.
"""

# Axis definitions (legacy helpers). Units use the AxisUnit enum values.
X_AXIS_LOGICAL = Axis(
    name="logical coordinates x axis",
    axis_unit=AxisUnit.pixel,
    axis_type=AxisType.array,
)
Y_AXIS_LOGICAL = Axis(
    name="logical coordinates y axis",
    axis_unit=AxisUnit.pixel,
    axis_type=AxisType.array,
)
Z_AXIS_LOGICAL = Axis(
    name="logical coordinates z axis",
    axis_unit=AxisUnit.pixel,
    axis_type=AxisType.array,
)

X_AXIS_PHYSICAL = Axis(
    name="physical coordinates x axis",
    axis_unit=AxisUnit.angstrom,
    axis_type=AxisType.space,
)
Y_AXIS_PHYSICAL = Axis(
    name="physical coordinates y axis",
    axis_unit=AxisUnit.angstrom,
    axis_type=AxisType.space,
)
Z_AXIS_PHYSICAL = Axis(
    name="physical coordinates z axis",
    axis_unit=AxisUnit.angstrom,
    axis_type=AxisType.space,
)


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


# Canonical Direction-B coordinate systems: the two reserved per-entity spaces
# ``array`` (discrete index) and ``physical`` (continuous Angstrom).


def array_coords(dim: int = 2) -> CoordinateSystem:
    """Canonical ``array`` coordinate system: axis_type=array, unit pixel (2D) / voxel (3D)."""
    if dim not in (2, 3):
        raise ValueError(f"{dim} is not a valid dimension")
    unit = AxisUnit.voxel if dim == 3 else AxisUnit.pixel
    axes = [Axis(name=n, axis_unit=unit, axis_type=AxisType.array) for n in "xyz"[:dim]]
    return CoordinateSystem(name="array", axes=axes)


def physical_coords_canonical(dim: int = 2) -> CoordinateSystem:
    """Canonical ``physical`` coordinate system: axis_type=space, unit angstrom."""
    if dim not in (2, 3):
        raise ValueError(f"{dim} is not a valid dimension")
    axes = [
        Axis(name=n, axis_unit=AxisUnit.angstrom, axis_type=AxisType.space)
        for n in "xyz"[:dim]
    ]
    return CoordinateSystem(name="physical", axes=axes)
