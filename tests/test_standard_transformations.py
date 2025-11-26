import pytest
from cets_data_model.standard_transformations import (
    physical_coords,
    logical_coords,
    generate_flip_transformation,
    generate_translation_transformation,
    generate_rotation_transformation,
    generate_scale_transformation,
    image_pixel_size,
    image_super_resolution_pixel_size,
    aligned_calibration_image_to_micrograph,
    aligned_map_to_tomogram,
    aligned_projection_image_to_tilt_series,
    aligned_annotation_to_tomogram,
    aligned_subtomo_to_tomogram,
    aligned_movie_frame_to_projection,
)
from cets_data_model.models.models import (
    CoordinateSystem,
    Flip2D,
    Translation,
    Affine,
    Identity,
    Scale,
    Sequence,
    Rotation2D,
)


def test_create_physical_coords():
    pcoords = physical_coords(name="test")
    assert isinstance(pcoords, CoordinateSystem)
    assert pcoords.name == "test"
    assert pcoords.axes[0].axis_unit == "Ångstrom"


def test_create_base_logical_coords():
    pcoords = logical_coords()
    assert isinstance(pcoords, CoordinateSystem)
    assert pcoords.name == "base_logical_coordinates"
    assert pcoords.axes[0].axis_unit == "pixel/voxel"


def test_create_logical_coords_with_name():
    pcoords = logical_coords("test")
    assert isinstance(pcoords, CoordinateSystem)
    assert pcoords.name == "test"
    assert pcoords.axes[0].axis_unit == "pixel/voxel"


def test_generate_flip_transformation_no_axis():
    tf = generate_flip_transformation(
        name="no_flip", input="in", output="out", axis=None
    )

    assert isinstance(tf, Flip2D)
    assert tf.name == "no_flip"
    assert tf.input == "in"
    assert tf.output == "out"
    assert tf.flip2d == [[1, 0], [0, 1]]


def test_generate_flip_transformation_x_axis():
    tf = generate_flip_transformation(name="flip_x", input="in", output="out", axis="x")

    assert isinstance(tf, Flip2D)
    assert tf.flip2d == [[1, 0], [0, -1]]


def test_generate_flip_transformation_y_axis():
    """If axis is y, flip X direction: [[-1,0],[0,1]]"""
    tf = generate_flip_transformation(name="flip_y", input="in", output="out", axis="y")

    assert isinstance(tf, Flip2D)
    assert tf.flip2d == [[-1, 0], [0, 1]]


def test_generate_flip_transformation_invalid_axis():
    """Should raise ValueError for invalid axis."""
    with pytest.raises(ValueError):
        generate_flip_transformation(name="invalid", input="in", output="out", axis="q")


def test_generate_translation():
    tf = generate_translation_transformation(name="t0", input="in", output="out", dim=3)

    assert isinstance(tf, Translation)
    assert tf.name == "t0"
    assert tf.input == "in"
    assert tf.output == "out"
    assert tf.translation == [0, 0, 0]


def test_generate_translation_custom_vector():
    vector = [1.5, -2.0, 3.25]
    tf = generate_translation_transformation(
        name="t_custom", input="in", output="out", dim=3, trans_vector=vector
    )

    assert isinstance(tf, Translation)
    assert tf.translation == vector


@pytest.mark.parametrize(
    "dim, vector",
    [
        (2, [1]),  # too short
        (2, [1, 2, 3]),  # too long
    ],
)
def test_generate_translation_incorrect_dimension(dim, vector):
    with pytest.raises(ValueError):
        generate_translation_transformation(
            name="bad",
            input="in",
            output="out",
            dim=dim,
            trans_vector=vector,
        )


def test_generate_rotation_transformation_identity():
    tf = generate_rotation_transformation(name="rot0", input="in", output="out")

    assert isinstance(tf, Identity)
    assert tf.name == "rot0"
    assert tf.input == "in"
    assert tf.output == "out"


def test_generate_rotation_transformation_affine():
    matrix = [[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]
    tf = generate_rotation_transformation(
        name="rot90", input="in", output="out", affine=matrix
    )

    assert isinstance(tf, Affine)
    assert tf.affine == matrix
    assert tf.name == "rot90"
    assert tf.input == "in"
    assert tf.output == "out"


def test_generate_rotation_transformation_2d():
    tf = generate_rotation_transformation(
        name="rot902d",
        input="in",
        output="out",
        affine=[[-1, 0], [0, -1]],
    )
    assert isinstance(tf, Rotation2D)


def test_generate_scale_default_scale_zero():
    tf = generate_scale_transformation(
        name="scale0", input="in", output="out", scale=None, dim=3
    )

    assert isinstance(tf, Scale)
    assert tf.scale == [0.0, 0.0, 0.0]


def test_generate_scale_custom_scale():
    tf = generate_scale_transformation(
        name="scale2", input="in", output="out", scale=2.5, dim=3
    )

    assert isinstance(tf, Scale)
    assert tf.scale == [2.5, 2.5, 2.5]


def test_generate_scale_missing_dim():
    with pytest.raises(ValueError):
        generate_scale_transformation(
            name="bad", input="in", output="out", scale=1.0, dim=None
        )


def test_image_pixel_size():
    ipx = image_pixel_size(apix=1.6)
    assert isinstance(ipx[0], Scale)
    assert isinstance(ipx[1], CoordinateSystem)
    assert ipx[0].scale == [1.6, 1.6]


def test_image_super_resolution_pixel_size():
    ipx = image_super_resolution_pixel_size(apix=0.8)
    assert isinstance(ipx[0], Scale)
    assert isinstance(ipx[1], CoordinateSystem)
    assert ipx[0].scale == [0.8, 0.8]


def test_aligned_calibration_image_to_micrograph():
    acm = aligned_calibration_image_to_micrograph(flip_axis="x", translation=[1, 2])
    assert isinstance(acm[0], Sequence)
    assert len(acm[0].sequence) == 2
    assert isinstance(acm[0].sequence[0], Flip2D)
    assert isinstance(acm[0].sequence[1], Translation)
    assert len(acm[1]) == 2
    assert isinstance(acm[1][0], CoordinateSystem)
    assert isinstance(acm[1][1], CoordinateSystem)


def test_aligned_movie_frame_to_projection():
    tf = aligned_movie_frame_to_projection(translation_vector=[1, 2])

    assert isinstance(tf[0], Translation)
    assert isinstance(tf[1], list)
    assert len(tf[1]) == 1
    assert isinstance(tf[1][0], CoordinateSystem)


def test_aligned_projection_image_to_tilt_series():
    seq = aligned_projection_image_to_tilt_series(
        translation_vector=[1, 2], rotation_matrix=[[1, 0], [0, 1]]
    )

    assert isinstance(seq[0], Sequence)
    assert len(seq[0].sequence) == 2
    assert isinstance(seq[0].sequence[0], Translation)
    assert isinstance(seq[0].sequence[1], (Rotation2D, Identity))

    assert isinstance(seq[1], list)
    assert len(seq[1]) == 2
    assert isinstance(seq[1][0], CoordinateSystem)
    assert isinstance(seq[1][1], CoordinateSystem)


def test_aligned_subtomo_to_tomogram():
    seq = aligned_subtomo_to_tomogram(
        rotation_matrix=[[1, 0, 0], [0, 1, 0], [0, 0, 1]], translation_vector=[3, 4, 5]
    )

    assert isinstance(seq[0], Sequence)
    assert len(seq[0].sequence) == 2
    assert isinstance(seq[0].sequence[0], (Affine, Identity))
    assert isinstance(seq[0].sequence[1], Translation)

    assert isinstance(seq[1], list)
    assert len(seq[1]) == 2
    assert isinstance(seq[1][0], CoordinateSystem)
    assert isinstance(seq[1][1], CoordinateSystem)


def test_aligned_map_to_tomogram():
    seq = aligned_map_to_tomogram(
        scale=2.0,
        rotation_matrix=[[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        translation_vector=[1, 2, 3],
    )

    assert isinstance(seq[0], Sequence)
    assert len(seq[0].sequence) == 3
    assert isinstance(seq[0].sequence[0], Scale)
    assert isinstance(seq[0].sequence[1], (Affine, Identity))
    assert isinstance(seq[0].sequence[2], Translation)

    assert isinstance(seq[1], list)
    assert len(seq[1]) == 3
    assert isinstance(seq[1][0], CoordinateSystem)
    assert isinstance(seq[1][1], CoordinateSystem)
    assert isinstance(seq[1][2], CoordinateSystem)


def test_aligned_annotation_to_tomogram():
    seq = aligned_annotation_to_tomogram(
        scale=1.5,
        rotation_matrix=[[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        translation=[5, 6, 7],
    )

    assert isinstance(seq[0], Sequence)
    assert len(seq[0].sequence) == 3
    assert isinstance(seq[0].sequence[0], Scale)
    assert isinstance(seq[0].sequence[1], (Affine, Identity))
    assert isinstance(seq[0].sequence[2], Translation)

    assert isinstance(seq[1], list)
    assert len(seq[1]) == 3  # scaled, rotated, final
    assert isinstance(seq[1][0], CoordinateSystem)
    assert isinstance(seq[1][1], CoordinateSystem)
    assert isinstance(seq[1][2], CoordinateSystem)
