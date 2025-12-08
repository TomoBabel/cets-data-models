from typing import Tuple
from cets_data_model.models.models import (
    Scale,
    CoordinateSystem,
    CoordinateTransformation,
)
from cets_data_model.standard_names import (
    BASE_LOGICAL_COORDS_2D,
    IMAGE_PIXEL_SIZE_COORDS,
    IMAGE_PIXEL_SIZE_XFROM,
    IMAGE_SUPER_RES_PIXEL_SIZE_XFROM,
    IMAGE_SUPER_RES_PIXEL_SIZE_COORDS,
    ALIGN_CALIBRATION_IMAGE_XFROM,
    ALIGN_CALIBRATION_IMAGE_COORDS,
    ALIGN_MAP_XFROM,
    ALIGN_MAP_COORDS,
    ALIGN_MOVIE_FRAME_XFROM,
    ALIGN_MOVIE_FRAME_COORDS,
    ALIGN_SUBTOMOGRAM_XFROM,
    ALIGN_SUBTOMOGRAM_COORDS,
    ALIGN_ANNOTATION_XFROM,
    ALIGN_ANNOTATION_COORDS,
)
from cets_data_model.standard_coordinate_systems import logical_coords

# helper functions for generating transformations and their associated coordinate
# systems with the correct naming conventions. Each one returns the transformation
# and the final coordinate system.

# helper functions for scaling - just provide pixel size


def image_pixel_size(apix: float) -> Tuple[Scale, CoordinateSystem]:
    """Get the scale transformation obj and final coord system for image pixel size"""
    return (
        Scale(
            type="scale",
            name=IMAGE_PIXEL_SIZE_XFROM,
            input=BASE_LOGICAL_COORDS_2D,
            output=IMAGE_PIXEL_SIZE_COORDS,
            scale=[apix, apix],
        ),
        logical_coords(dim=2),
    )


def image_super_res_pixel_size(apix: float) -> Tuple[Scale, CoordinateSystem]:
    """Get the scale transformation obj and final coord system for superres image pixel
    size"""
    return (
        Scale(
            type="scale",
            name=IMAGE_SUPER_RES_PIXEL_SIZE_XFROM,
            input=BASE_LOGICAL_COORDS_2D,
            output=IMAGE_SUPER_RES_PIXEL_SIZE_COORDS,
            scale=[apix, apix],
        ),
        logical_coords(dim=2),
    )


# helper functions for transformations - provide the transformation(s). If more than
# one transformation is used make sure to provide a Sequence transformation object.
# Returns the transformation and the final coordinate system


def align_calibration_image_to_movie_frame(
    transformation: CoordinateTransformation,
) -> Tuple[CoordinateTransformation, CoordinateSystem]:
    transformation.name = ALIGN_CALIBRATION_IMAGE_XFROM
    transformation.input = BASE_LOGICAL_COORDS_2D
    transformation.output = ALIGN_CALIBRATION_IMAGE_COORDS
    coords = logical_coords(ALIGN_CALIBRATION_IMAGE_COORDS)
    return transformation, coords


def align_movie_frame_to_projection(
    transformation: CoordinateTransformation,
) -> Tuple[CoordinateTransformation, CoordinateSystem]:
    transformation.name = ALIGN_MOVIE_FRAME_XFROM
    transformation.input = BASE_LOGICAL_COORDS_2D
    transformation.output = ALIGN_MOVIE_FRAME_COORDS
    coords = logical_coords(ALIGN_MOVIE_FRAME_COORDS)
    return transformation, coords


def align_subtomogram_to_tomogram(
    transformation: CoordinateTransformation,
) -> Tuple[CoordinateTransformation, CoordinateSystem]:
    transformation.name = ALIGN_SUBTOMOGRAM_XFROM
    transformation.input = BASE_LOGICAL_COORDS_2D
    transformation.output = ALIGN_SUBTOMOGRAM_COORDS
    coords = logical_coords(ALIGN_SUBTOMOGRAM_COORDS)
    return transformation, coords


def align_map_to_tomogram(
    transformation: CoordinateTransformation,
) -> Tuple[CoordinateTransformation, CoordinateSystem]:
    transformation.name = ALIGN_MAP_XFROM
    transformation.input = BASE_LOGICAL_COORDS_2D
    transformation.output = ALIGN_MAP_COORDS
    coords = logical_coords(ALIGN_MAP_COORDS)
    return transformation, coords


def align_annotation_to_tomogram(
    transformation: CoordinateTransformation,
) -> Tuple[CoordinateTransformation, CoordinateSystem]:
    transformation.name = ALIGN_ANNOTATION_XFROM
    transformation.input = BASE_LOGICAL_COORDS_2D
    transformation.output = ALIGN_ANNOTATION_COORDS
    coords = logical_coords(ALIGN_ANNOTATION_COORDS)
    return transformation, coords
