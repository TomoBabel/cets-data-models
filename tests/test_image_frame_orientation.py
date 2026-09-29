"""Frame orientation (Rot90, Reflection) and alignment-center helpers of images."""

import itertools

import pytest

from cets_data_model.models import models
from cets_data_model.utils.image_frame import (
    alignment_center,
    centered_translation,
    quarter_turn_rotation,
)


def apply(block, vector):
    return [sum(entry * value for entry, value in zip(row, vector)) for row in block]


def determinant(block):
    if len(block) == 1:
        return block[0][0]
    return sum(
        (-1) ** column
        * block[0][column]
        * determinant([row[:column] + row[column + 1 :] for row in block[1:]])
        for column in range(len(block))
    )


def new_image(ndim, **shape):
    if ndim == 2:
        return models.Image2D(**shape)
    return models.Image3D(**shape)


def snapshot(image):
    return image.model_dump_json(), set(image.model_fields_set)


@pytest.mark.parametrize(
    "axis,source,target",
    [
        ("z", [1, 0, 0], [0, 1, 0]),
        ("x", [0, 1, 0], [0, 0, 1]),
        ("y", [0, 0, 1], [1, 0, 0]),
    ],
)
def test_quarter_turns_are_right_handed(axis, source, target):
    assert apply(quarter_turn_rotation(1, ndim=3, axis=axis), source) == target
    assert apply(quarter_turn_rotation(-1, ndim=3, axis=axis), target) == source


def test_quarter_turns_are_periodic_and_generate_all_rotations():
    assert quarter_turn_rotation(1, ndim=2) == [[0, -1], [1, 0]]
    for ndim, axis in [(2, "z"), (3, "x"), (3, "y"), (3, "z")]:
        turn = [quarter_turn_rotation(k, ndim=ndim, axis=axis) for k in range(-4, 9)]
        assert (
            turn[0]
            == turn[4]
            == turn[8]
            == turn[12]
            == [[int(i == j) for j in range(ndim)] for i in range(ndim)]
        )
        assert turn[3] == turn[7] and turn[5] == turn[9]
    rotations = set()
    for a, b, c in itertools.product(range(4), repeat=3):
        block = [[int(i == j) for j in range(3)] for i in range(3)]
        for axis, turns in (("x", a), ("y", b), ("z", c)):
            turn = quarter_turn_rotation(turns, ndim=3, axis=axis)
            block = [
                [sum(t * b for t, b in zip(row, col)) for col in zip(*block)]
                for row in turn
            ]
        rotations.add(tuple(map(tuple, block)))
    assert len(rotations) == 24
    assert all(determinant([list(row) for row in block]) == 1 for block in rotations)


@pytest.mark.parametrize(
    "turns,ndim,axis,message",
    [
        (1.5, 3, "z", "integer"),
        (True, 3, "z", "integer"),
        ("1", 3, "z", "integer"),
        (1, 4, "z", "2 or 3 axes"),
        (1, 3, "w", "about 'x', 'y' or 'z'"),
        (1, 2, "x", "about 'z'"),
    ],
)
def test_quarter_turn_rejects_invalid_arguments(turns, ndim, axis, message):
    with pytest.raises(ValueError, match=message):
        quarter_turn_rotation(turns, ndim=ndim, axis=axis)


@pytest.mark.parametrize("ndim", [2, 3])
def test_orientation_setters_keep_other_components(ndim):
    image = new_image(ndim)
    size = "pixel_size" if ndim == 2 else "voxel_size"
    setattr(image, size, [2.0, 3.0, 4.0][:ndim])
    image.translation = [5.0, 6.0, 7.0][:ndim]
    rotation = quarter_turn_rotation(1, ndim=ndim)
    image.rotation = rotation
    image.reflection = ["y", "x"]
    assert image.rotation == rotation and image.reflection == ["y", "x"]
    assert image.translation == [5.0, 6.0, 7.0][:ndim]
    assert getattr(image, size).as_list() == [2.0, 3.0, 4.0][:ndim]
    steps = image.coordinate_transformations[0].sequence
    assert [step.transformation_type for step in steps] == [
        "rot90",
        "reflection",
        "translation",
        "scale",
    ]
    image.rotation = quarter_turn_rotation(0, ndim=ndim)
    image.reflection = []
    steps = image.coordinate_transformations[0].sequence
    assert [step.transformation_type for step in steps] == ["translation", "scale"]
    assert image.translation == [5.0, 6.0, 7.0][:ndim]


def test_orientation_getters_are_detached():
    image = models.Image3D()
    image.rotation = quarter_turn_rotation(1, ndim=3, axis="x")
    image.reflection = ["z"]
    before = snapshot(image)
    image.rotation[0][0] = 5
    image.reflection.append("x")
    assert snapshot(image) == before


@pytest.mark.parametrize(
    "ndim,name,value,message",
    [
        (3, "rotation", [[-1, 0, 0], [0, 1, 0], [0, 0, 1]], "determinant"),
        (3, "rotation", quarter_turn_rotation(1, ndim=2), "3x3"),
        (2, "rotation", quarter_turn_rotation(1, ndim=3), "2x2"),
        (2, "rotation", [[0.5, 0], [0, 1]], "integers"),
        (2, "rotation", [[True, 0], [0, 1]], "integers"),
        (2, "rotation", "identity", "2x2"),
        (2, "reflection", "x", "list of axis names"),
        (2, "reflection", ["z"], "distinct axes from"),
        (3, "reflection", ["x", "x"], "distinct axes from"),
        (3, "reflection", ["w"], "distinct axes from"),
    ],
    ids=[
        "improper",
        "2d-in-3d",
        "3d-in-2d",
        "fraction",
        "boolean",
        "string",
        "bare-string",
        "z-in-2d",
        "duplicate",
        "unknown",
    ],
)
def test_invalid_orientation_leaves_the_image_unchanged(ndim, name, value, message):
    image = new_image(ndim)
    image.translation = 1
    before = snapshot(image)
    with pytest.raises(ValueError, match=message):
        setattr(image, name, value)
    assert snapshot(image) == before


def test_alignment_center_is_floor_half():
    assert alignment_center((64, 65, 6)) == (32, 32, 3)
    assert alignment_center([1, 2]) == (0, 1)
    for shape in [(0, 5), (5,), (1, 2, 3, 4), (2.5, 3), (True, 2), None]:
        with pytest.raises(ValueError, match="2 or 3 positive integers"):
            alignment_center(shape)


def proper_split(orientation):
    """Split a signed permutation O into a Rot90 R and reflected axes with F R = O."""
    reflected = [] if determinant(orientation) == 1 else ["x"]
    rotation = [
        [-entry if reflected and i == 0 else entry for entry in row]
        for i, row in enumerate(orientation)
    ]
    return rotation, reflected


@pytest.mark.parametrize("shape", [(4, 5), (5, 6), (4, 5, 6), (7, 6, 9)])
def test_centering_puts_the_oriented_center_at_the_origin(shape):
    ndim = len(shape)
    for columns in itertools.permutations(range(ndim)):
        for signs in itertools.product([1, -1], repeat=ndim):
            orientation = [[0] * ndim for _ in range(ndim)]
            for row, (column, sign) in enumerate(zip(columns, signs)):
                orientation[row][column] = sign
            rotation, reflection = proper_split(orientation)
            offset = centered_translation(
                shape, rotation=rotation, reflection=reflection
            )
            mapped = {
                tuple(q + t for q, t in zip(apply(orientation, index), offset))
                for index in itertools.product(*(range(n) for n in shape))
            }
            oriented = [shape[column] for column in columns]
            expected = set(
                itertools.product(*(range(-(n // 2), n - n // 2) for n in oriented))
            )
            assert mapped == expected, (orientation, offset)


def test_reversed_axis_includes_the_n_minus_1_offset():
    # Reversing a length-6 axis: file index 3 is not the centered voxel.
    assert centered_translation((1, 1, 6), reflection=["z"]) == [0, 0, 2]
    assert centered_translation((1, 1, 6)) == [0, 0, -3]


def test_center_origin_changes_only_the_translation():
    image = models.Image3D(width=64, height=65, depth=6)
    image.voxel_size = [2, 3, 4]
    image.reflection = ["z"]
    image.center_origin()
    assert image.translation == [-32.0, -32.0, 2.0]
    assert image.reflection == ["z"]
    assert image.voxel_size.as_list() == [2.0, 3.0, 4.0]


def test_set_centered_frame_replaces_supplied_components_and_recenters():
    image = models.Image3D(width=64, height=65, depth=6)
    image.voxel_size = [2, 3, 4]
    image.reflection = ["z"]
    image.set_centered_frame(
        rotation=quarter_turn_rotation(-1, ndim=3, axis="x"), reflection=[]
    )
    assert image.translation == [-32.0, -3.0, 32.0]
    assert image.voxel_size.as_list() == [2.0, 3.0, 4.0]  # omitted, kept
    image.set_centered_frame(spacing=5)
    assert image.rotation == quarter_turn_rotation(-1, ndim=3, axis="x")
    assert image.voxel_size.scalar == 5.0


@pytest.mark.parametrize(
    "shape,updates,message",
    [
        ({"width": 64, "height": 65}, {}, "centering requires positive"),
        ({"width": 64, "height": 65, "depth": 0}, {}, "centering requires positive"),
        ({"width": 4, "height": 4, "depth": 4}, {"spacing": -1}, "positive values"),
        (
            {"width": 4, "height": 4, "depth": 4},
            {"rotation": [[1, 0, 0], [0, 1, 0], [0, 0, -1]]},
            "determinant",
        ),
    ],
    ids=["missing-depth", "zero-depth", "spacing", "improper-rotation"],
)
def test_centering_failures_leave_the_image_unchanged(shape, updates, message):
    image = models.Image3D(**shape)
    image.translation = [1, 2, 3]
    before = snapshot(image)
    with pytest.raises(ValueError, match=message):
        image.set_centered_frame(reflection=["x"], **updates)
    if not updates:
        with pytest.raises(ValueError, match=message):
            image.center_origin()
    assert snapshot(image) == before
