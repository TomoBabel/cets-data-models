from cets_data_model.models.models import (
    CoordinateSystem,
    Axis,
    Translation,
    Sequence,
    Flip2D,
)
from typing import List, Tuple, Optional

# Axis definitions
x_axis_logical = Axis(name="logical coordinates x axis", axis_unit="pixel/voxel")
y_axis_logical = Axis(name="logical coordinates y axis", axis_unit="pixel/voxel")
z_axis_logical = Axis(name="logical coordinates z axis", axis_unit="pixel/voxel")

x_axis_physical = Axis(name="physical coordinates x axis", axis_unit="Ångstrom")
y_axis_physical = Axis(name="physical coordinates y axis", axis_unit="Ångstrom")
z_axis_physical = Axis(name="physical coordinates z axis", axis_unit="Ångstrom")

# The base logical coords  0,0,0 is at the bottom left corner
LOGICAL_COORDS = CoordinateSystem(
    name="base logical coordinates",
    axes=[x_axis_logical, y_axis_logical, z_axis_logical],
)

# The base physical coordinate system. 0,0,0 is at the centre
PHYSICAL_COORDS = CoordinateSystem(
    name="base physical coordinates",
    axes=[x_axis_physical, y_axis_physical, z_axis_physical],
)


# Functions to generate coordinate systems
def physical_coords(name: str) -> CoordinateSystem:
    coords = LOGICAL_COORDS.model_copy()
    coords.name = name
    return coords


def logical_coords(name: str) -> CoordinateSystem:
    coords = PHYSICAL_COORDS.model_copy()
    coords.name = name
    return coords


# The standard transformations
# R2D, R3D: Rotations
# T: Translation
# S: Scale
# F: Flip
#
# Align calibration image to movie frame: F2D, R2D,
# Align movie frame to projection: T
# Align projection in aligned tilt series: T, R3D
# Align subtomogram to tomogram R3D, T
# Align annotation to tomogram: S, T
# Align map to tomogram: R3D, T


# Align calibration image to movie
def generate_aligned_calibration_image(
    flip_matrix: Optional[List[List[int]]] = None,
    translation: Optional[List[float]] = None,
) -> Tuple[Sequence, List[CoordinateSystem]]:
    """

    Generate a sequence of transformations for alignment of a calibration image to
    a movie frame

    Args:
        flip_matrix (Optional[List[List[int]]]): The matrix applied flips
        translation (Optional[List[float]]): Translation vector
    Returns:
        Tuple[Sequence, List[CoordinateSystem]]: The sequence if transformations and
            CoordinateSystems for those transformations
    """

    flipped_coords = logical_coords("calibration_image_flip")
    aligned_coords = logical_coords("calibration_image_aligned")

    def generate_flip_transformation(array: Optional[List[List[int]]] = None) -> Flip2D:
        array = [[1, 0], [0, 1]] if array is None else array
        return Flip2D(
            name="Align calibration image to movie",
            input="base logical coordinates",
            output="calibration_image_flip",
            flip2d=array,
        )

    def generate_translation_transformation(
        trans_vector: Optional[List[float]] = None,
    ) -> Translation:
        trans_vector = [0, 0] if trans_vector is None else trans_vector
        return Translation(
            name="Align calibration image to movie",
            input="calibration_image_flip",
            output="calibration_image_aligned",
            translation=trans_vector,
        )

    return (
        Sequence(
            name="Align calibration image to movie",
            input="base_logical_coords",
            output="calibration_image_aligned",
            sequence=[
                generate_flip_transformation(flip_matrix),
                generate_translation_transformation(translation),
            ],
        ),
        [flipped_coords, aligned_coords],
    )
