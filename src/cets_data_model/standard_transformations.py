# Standard coordinate system and transformation names - The transformation or sequence
# of transformations that accomplish these tasks must have these specific names and 
# the endpoint coordinate system must have the associated name. 

# The actual transformation/sequence and coordinate system can vary as long as the
# correct string from below is used in the `name` field.

# Align calibration image to movie frame
ALIGN_CALIBRATION_IMAGE_TRANSFORMATION = "align_calibration_image_to_movie_frame"
ALIGN_CALIBRATION_IMAGE_COORDS = "aligned_calibration_image"

# Align movie frame to projection
ALIGN_MOVIE_FRAME_TRANSFORMATION = "align_movie_frame_to_projection"
ALIGN_MOVIE_FRAME_COORDS = "aligned_movie_frame"

# Align projection image to tomogram
ALIGN_PROJECTION_IMAGE_TRANSFORMATION = "align_projection_image_to_tomogram"
ALIGN_PROJECTION_IMAGE_COORDS = "aligned_projection_image"

# Align subtomogram to tomogram R3D
ALIGN_SUBTOMOGRAM_TRANSFORMATION = "align_subtomogram_to_tomogram"
ALIGN_SUBTOMOGRAM_COORDS = "aligned_subtomogram"

# Align map to tomogram
ALIGN_MAP_TRANSFORMATION = "align_map_to_tomogram"
ALIGN_MAP_COORDS = "aligned_map"

# Align annotation to tomogram
ALIGN_ANNOTATION_TRANSFORMATION = "align_annotation_to_tomogram"
ALIGN_ANNOTATION_COORDS = "aligned_annotation"


