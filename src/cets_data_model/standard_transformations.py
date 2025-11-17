from cets_data_model.models.models import (
    CoordinateSystem,
    Axis,
    Translation,
    Sequence,
    Flip2D,
    Identity,
    Affine,
    Scale,
    Rotation2D,
)
from typing import List, Tuple, Optional, Union, Literal

# Axis definitions
x_axis_logical = Axis(name="logical coordinates x axis", axis_unit="pixel/voxel")
y_axis_logical = Axis(name="logical coordinates y axis", axis_unit="pixel/voxel")
z_axis_logical = Axis(name="logical coordinates z axis", axis_unit="pixel/voxel")

x_axis_physical = Axis(name="physical coordinates x axis", axis_unit="Ångstrom")
y_axis_physical = Axis(name="physical coordinates y axis", axis_unit="Ångstrom")
z_axis_physical = Axis(name="physical coordinates z axis", axis_unit="Ångstrom")


# Functions to generate coordinate systems - used internally
def physical_coords(name: str) -> CoordinateSystem:
    return CoordinateSystem(name=name, axes=[x_axis_physical, z_axis_physical])


def logical_coords(name: Optional[str] = None) -> CoordinateSystem:
    name = "base_logical_coordinates" if name is None else name
    return CoordinateSystem(name=name, axes=[x_axis_logical, z_axis_logical])


# functions to generate transformations - used internally by the creation functions
def generate_flip_transformation(
    name: str,
    input: str,
    output: str,
    axis: Optional[Literal["x", "y"]] = None,
) -> Flip2D:
    """Generate a 2-dimensional transformation that flips along one axis"""
    if axis is None:
        array = [[1, 0], [0, 1]]
    elif axis == "x":
        array = [[1, 0], [0, -1]]
    elif axis == "y":
        array = [[-1, 0], [0, 1]]
    else:
        raise ValueError("Axis must be 'x', 'y'")
    return Flip2D(name=name, input=input, output=output, flip2d=array)


def generate_translation_transformation(
    name: str,
    input: str,
    output: str,
    dim: int,
    trans_vector: Optional[List[float]] = None,
) -> Translation:
    trans_vector = [0] * dim if trans_vector is None else trans_vector
    if len(trans_vector) != dim:
        raise ValueError("Incorrect dimensionality of translation vector")
    return Translation(name=name, input=input, output=output, translation=trans_vector)


def generate_rotation_transformation(
    name: str,
    input: str,
    output: str,
    affine: Optional[List[List[float]]] = None,
) -> Union[Affine, Identity, Rotation2D]:
    if affine is None:
        return Identity(name=name, input=input, output=output)
    if len(affine) == 3:
        return Affine(name=name, input=input, output=output, affine=affine)
    if len(affine) == 2:
        return Rotation2D(name=name, input=input, output=output, rotation2d=affine)
    else:
        raise ValueError("Invalid matrix dimensions")


def generate_scale_transformation(
    name: str,
    input: str,
    output: str,
    scale: Optional[float] = None,
    dim: Optional[int] = None,
) -> Scale:
    if dim is None:
        raise ValueError("Dimension cannot be None")
    scale = 0.0 if scale is None else scale
    return Scale(name=name, input=input, output=output, scale=[scale] * dim)


# ----------------------------
# The standard transformations
# ----------------------------
# R2D, R3D: Rotations
# T: Translation
# S: Scale
# F: Flip
#
# Align calibration image to movie frame: F2D, R2D,
# Align movie frame to projection: T
# Align projection image to aligned tilt series: T, R3D
# Align subtomogram to tomogram R3D, T
# Align map to tomogram: S, R3D, T
# Align annotation to tomogram: S, T


def image_pixel_size(apix: float) -> Tuple[Scale, CoordinateSystem]:
    """Scaling transformation for defining the pixel size of an image

    Args:
        apix: Pixel size of the image Å/pixel

    Returns:
        Tuple[Scale, CoordinateSystem]: The Scale transformation applied to the
            image and the new coordinate system
    """
    name = "image_pixel_size"
    px_size_coords = physical_coords(name=name)

    return (
        Scale(
            name=name,
            input=logical_coords().name,
            output=px_size_coords.name,
            scale=[apix, apix],
        ),
        px_size_coords,
    )


def image_super_resolution_pixel_size(apix: float) -> Tuple[Scale, CoordinateSystem]:
    """Scaling transformation for defining the superresolution pixel size of an image

    Args:
        apix: Pixel size of the image Å/pixel

    Returns:
        Tuple[Scale, CoordinateSystem]: The Scale transformation applied to the
            image and the new coordinate system
    """

    name = "image_super_resolution_pixel_size"
    px_size_coords = physical_coords(name=name)

    return (
        Scale(
            name=name,
            input=logical_coords().name,
            output=px_size_coords.name,
            scale=[apix, apix],
        ),
        px_size_coords,
    )


# Align calibration image to movie
def aligned_calibration_image_to_micrograph(
    flip_axis: Optional[Literal["x", "y"]] = None,
    translation: Optional[List[float]] = None,
) -> Tuple[Sequence, List[CoordinateSystem]]:
    """
    Generate a sequence of transformations for alignment of a calibration image to
    a movie frame

    Args:
        flip_axis (Optional[Literal["x", "Y"]]): The matrix for any applied flips
        translation (Optional[List[float]]): Translation vector
    Returns:
        Tuple[Sequence, List[CoordinateSystem]]: The sequence of transformations and
            CoordinateSystems for those transformations
    """
    sequence_name = "Align calibration image to movie"
    flipped_coords = logical_coords("calibration_image_flipped")
    final = logical_coords("calibration_image_aligned")

    return (
        Sequence(
            name=sequence_name,
            input=logical_coords().name,
            output=final.name,
            sequence=[
                generate_flip_transformation(
                    name=sequence_name,
                    input=logical_coords().name,
                    output=flipped_coords.name,
                    axis=flip_axis,
                ),
                generate_translation_transformation(
                    name=sequence_name,
                    input=flipped_coords.name,
                    output=final.name,
                    trans_vector=translation,
                    dim=2,
                ),
            ],
        ),
        [flipped_coords, final],
    )


def aligned_movie_frame_to_projection(
    translation_vector: Optional[List[float]] = None,
) -> Tuple[Translation, List[CoordinateSystem]]:
    """Generate the translation to align a raw movie frame to the motion corrected
    micrograph

    Args:
        translation_vector (Optional[List[float]]): Translation vector

    Returns:
        Tuple[Translation, List[CoordinateSystem]]: The Translation vector and
        CoordinateSystems for the translation
    """

    sequence_name = "Align movie frame to projection"
    translated_coords = logical_coords("movie_frame_aligned")

    return (
        Translation(
            name=sequence_name,
            input=logical_coords().name,
            output=translated_coords.name,
            translation=translation_vector,
        ),
        [translated_coords],
    )


def aligned_projection_image_to_tilt_series(
    translation_vector: Optional[List[float]] = None,
    rotation_matrix: Optional[List[List[float]]] = None,
) -> Tuple[Sequence, List[CoordinateSystem]]:
    """
    Generate a sequence of transformations for alignment of a projection image to
    a tilt series

    Args:
        translation_vector (Optional[List[float]]: The 2D translation vector
        rotation_matrix (Optional[List[List[float]]]): The  Rotation matrix
    Returns:
        Tuple[Sequence, List[CoordinateSystem]]: The sequence of transformations and
            CoordinateSystems for those transformations
    """

    sequence_name = "Align projection image to tilt series"
    translated_cords = logical_coords("projection_image_translated")
    final = logical_coords("projection_image_aligned")

    return (
        Sequence(
            name=sequence_name,
            input=logical_coords().name,
            output=final.name,
            sequence=[
                generate_translation_transformation(
                    name=sequence_name,
                    input=logical_coords().name,
                    output=translated_cords.name,
                    trans_vector=translation_vector,
                    dim=2,
                ),
                generate_rotation_transformation(
                    name=sequence_name,
                    input=translated_cords.name,
                    output=final.name,
                    affine=rotation_matrix,
                ),
            ],
        ),
        [translated_cords, final],
    )


def aligned_subtomo_to_tomogram(
    rotation_matrix: Optional[List[List[float]]] = None,
    translation_vector: Optional[List[float]] = None,
) -> Tuple[Sequence, List[CoordinateSystem]]:
    sequence_name = "Align subtomo to tomogram"
    rotated_cords = logical_coords("subtomo_rotated")
    final = logical_coords("subtomo_aligned")

    return (
        Sequence(
            name=sequence_name,
            input=logical_coords().name,
            output=final.name,
            sequence=[
                generate_rotation_transformation(
                    name=sequence_name,
                    input=logical_coords().name,
                    output=rotated_cords.name,
                    affine=rotation_matrix,
                ),
                generate_translation_transformation(
                    name=sequence_name,
                    input=rotated_cords.name,
                    output=final.name,
                    trans_vector=translation_vector,
                    dim=3,
                ),
            ],
        ),
        [rotated_cords, final],
    )


def aligned_map_to_tomogram(
    scale: Optional[float],
    rotation_matrix: Optional[List[List[float]]] = None,
    translation_vector: Optional[List[float]] = None,
) -> Tuple[Sequence, List[CoordinateSystem]]:
    sequence_name = "Align map to tomogram"
    scaled_coords = logical_coords("map_scaled")
    rotated_cords = logical_coords("map_rotated")
    final = logical_coords("map_aligned")

    return (
        Sequence(
            name=sequence_name,
            input=logical_coords().name,
            output=final.name,
            sequence=[
                generate_scale_transformation(
                    name=sequence_name,
                    input=logical_coords().name,
                    output=scaled_coords.name,
                    scale=scale,
                    dim=3,
                ),
                generate_rotation_transformation(
                    name=sequence_name,
                    input=scaled_coords.name,
                    output=rotated_cords.name,
                    affine=rotation_matrix,
                ),
                generate_translation_transformation(
                    name=sequence_name,
                    input=rotated_cords.name,
                    output=final.name,
                    trans_vector=translation_vector,
                    dim=3,
                ),
            ],
        ),
        [scaled_coords, rotated_cords, final],
    )


def aligned_annotation_to_tomogram(
    scale: Optional[float], rotation_matrix: List[List[float]], translation: List[float]
) -> Tuple[Sequence, List[CoordinateSystem]]:
    sequence_name = "Align annotation to tomogram"
    scaled_coords = logical_coords("annotation_scaled")
    rotated_cords = logical_coords("annotation_rotated")
    final = logical_coords("annotation_aligned")

    return (
        Sequence(
            name=sequence_name,
            input=logical_coords().name,
            output=final.name,
            sequence=[
                generate_scale_transformation(
                    name=sequence_name,
                    input=logical_coords().name,
                    output=scaled_coords.name,
                    scale=scale,
                    dim=3,
                ),
                generate_rotation_transformation(
                    name=sequence_name,
                    input=scaled_coords.name,
                    output=rotated_cords.name,
                    affine=rotation_matrix,
                ),
                generate_translation_transformation(
                    name=sequence_name,
                    input=rotated_cords.name,
                    output=final.name,
                    trans_vector=translation,
                    dim=3,
                ),
            ],
        ),
        [scaled_coords, rotated_cords, final],
    )
