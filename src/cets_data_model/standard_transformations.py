from typing import Tuple
from cets_data_model.models.models import (
    Scale,
    CoordinateSystem,
)
from cets_data_model.standard_names import (
    BASE_LOGICAL_COORDS_2D,
    IMAGE_PIXEL_SIZE_COORDS,
    IMAGE_PIXEL_SIZE_XFROM,
    IMAGE_SUPER_RES_PIXEL_SIZE_XFROM,
    IMAGE_SUPER_RES_PIXEL_SIZE_COORDS,
)
from cets_data_model.standard_coordinate_systems import physical_coords


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
        physical_coords(name=IMAGE_PIXEL_SIZE_COORDS, dim=2),
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
        physical_coords(name=IMAGE_SUPER_RES_PIXEL_SIZE_COORDS, dim=2),
    )
