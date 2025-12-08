from typing import Tuple, Optional
from cets_data_model.models.models import Scale, CoordinateSystem, Axis

# Standard coordinate system and transformation names - The transformation or sequence
# of transformations that accomplish these tasks must have these specific names and
# the endpoint coordinate system must have the associated name.

# The actual transformation/sequence and coordinate system can vary as long as the
# correct string from below is used in the `name` field.

# Axis definitions
x_axis_logical = Axis(name="logical coordinates x axis", axis_unit="pixel/voxel")
y_axis_logical = Axis(name="logical coordinates y axis", axis_unit="pixel/voxel")
z_axis_logical = Axis(name="logical coordinates z axis", axis_unit="pixel/voxel")

x_axis_physical = Axis(name="physical coordinates x axis", axis_unit="Ångstrom")
y_axis_physical = Axis(name="physical coordinates y axis", axis_unit="Ångstrom")
z_axis_physical = Axis(name="physical coordinates z axis", axis_unit="Ångstrom")

# NAMES - for the globals coordinate systems always end with COORDS, transformations
# always end with XFORM

# basic logical coords
BASE_LOGICAL_COORDS = "base_logical_coordinates"

# Align calibration image to movie frame
ALIGN_CALIBRATION_IMAGE_XFROM = "align_calibration_image_to_movie_frame"
ALIGN_CALIBRATION_IMAGE_COORDS = "aligned_calibration_image"

# Align movie frame to projection
ALIGN_MOVIE_FRAME_XFROM = "align_movie_frame_to_projection"
ALIGN_MOVIE_FRAME_COORDS = "aligned_movie_frame"

# Align projection image to tomogram
ALIGN_PROJECTION_IMAGE_XFROM = "align_projection_image_to_tomogram"
ALIGN_PROJECTION_IMAGE_COORDS = "aligned_projection_image"

# Align subtomogram to tomogram R3D
ALIGN_SUBTOMOGRAM_XFROM = "align_subtomogram_to_tomogram"
ALIGN_SUBTOMOGRAM_COORDS = "aligned_subtomogram"

# Align map to tomogram
ALIGN_MAP_XFROM = "align_map_to_tomogram"
ALIGN_MAP_COORDS = "aligned_map"

# Align annotation to tomogram
ALIGN_ANNOTATION_XFROM = "align_annotation_to_tomogram"
ALIGN_ANNOTATION_COORDS = "aligned_annotation"

# set pixel size of image
IMAGE_PIXEL_SIZE_XFROM = "image_pixel_size"
IMAGE_PIXEL_SIZE_COORDS = "image_pixel_size"

# set super res pixel size of image
IMAGE_SUPER_RES_PIXEL_SIZE_XFROM = "image_pixel_size"
IMAGE_SUPER_RES_PIXEL_SIZE_COORDS = "image_pixel_size"

# Helper functions


def physical_coords(name: str) -> CoordinateSystem:
    """Generate physical coordinates object"""
    return CoordinateSystem(name=name, axes=[x_axis_physical, z_axis_physical])


def logical_coords(name: Optional[str] = None) -> CoordinateSystem:
    """Generate physical coordinates object

    Gives the base logical coordinates if no name specified
    """

    name = BASE_LOGICAL_COORDS if name is None else name
    return CoordinateSystem(name=name, axes=[x_axis_logical, z_axis_logical])


def image_pixel_size(apix: float) -> Tuple[Scale, CoordinateSystem]:
    """Get the scale transformation obj and final coord system for image pixel size"""
    return (
        Scale(
            type="scale",
            name=IMAGE_PIXEL_SIZE_XFROM,
            input=BASE_LOGICAL_COORDS,
            output=IMAGE_PIXEL_SIZE_COORDS,
            scale=[apix, apix],
        ),
        logical_coords(),
    )


def image_super_res_pixel_size(apix: float) -> Tuple[Scale, CoordinateSystem]:
    """Get the scale transformation obj and final coord system for superres image pixel
    size"""
    return (
        Scale(
            type="scale",
            name=IMAGE_SUPER_RES_PIXEL_SIZE_XFROM,
            input=BASE_LOGICAL_COORDS,
            output=IMAGE_SUPER_RES_PIXEL_SIZE_COORDS,
            scale=[apix, apix],
        ),
        logical_coords(),
    )
