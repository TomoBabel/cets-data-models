# Standard coordinate system and transformation names - The transformation or sequence
# of transformations that accomplish these tasks must have these specific names and
# the endpoint coordinate system must have the associated name.

# The actual transformation/sequence and coordinate system can vary as long as the
# correct string from below is used in the `name` field.

# NAMES - for the globals coordinate systems always end with COORDS, transformations
# always end with XFORM

# basic logical coords
BASE_LOGICAL_COORDS_2D = "base_logical_coordinates_2D"
BASE_LOGICAL_COORDS_3D = "base_logical_coordinates_3D"

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
IMAGE_PIXEL_SIZE_XFROM = "image_pixel_size_transformation"
IMAGE_PIXEL_SIZE_COORDS = "image_pixel_size"

# set super res pixel size of image
IMAGE_SUPER_RES_PIXEL_SIZE_XFROM = "image_super_res_pixel_size_transformation"
IMAGE_SUPER_RES_PIXEL_SIZE_COORDS = "image_super_res_pixel_size"
