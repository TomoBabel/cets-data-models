"""Rot90, Reflection, and positive Scale in the public models."""

import itertools
import math

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from cets_data_model.models import models


def determinant(matrix):
    # Laplace expansion: an independent reference for small integer matrices.
    if len(matrix) == 1:
        return matrix[0][0]
    return sum(
        (-1) ** column
        * matrix[0][column]
        * determinant([row[:column] + row[column + 1 :] for row in matrix[1:]])
        for column in range(len(matrix))
    )


def signed_permutations(dimension):
    for columns in itertools.permutations(range(dimension)):
        for signs in itertools.product([1, -1], repeat=dimension):
            block = [[0] * dimension for _ in range(dimension)]
            for row, (column, sign) in enumerate(zip(columns, signs)):
                block[row][column] = sign
            yield block


def coordinate_system(name, dimension):
    return {"name": name, "axes": [{"name": axis} for axis in "xyz"[:dimension]]}


QUARTER_TURN_2D = [[0, -1], [1, 0]]
QUARTER_TURN_3D = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]
IDENTITY_4X4 = [[int(i == j) for j in range(4)] for i in range(4)]


@pytest.mark.parametrize("dimension,proper", [(2, 4), (3, 24)])
def test_rot90_accepts_exactly_the_proper_signed_permutations(dimension, proper):
    accepted = 0
    for matrix in signed_permutations(dimension):
        if determinant(matrix) == 1:
            assert models.Rot90(rot90=matrix).rot90 == matrix
            accepted += 1
        else:
            with pytest.raises(ValidationError, match="determinant \\+1.*Reflection"):
                models.Rot90(rot90=matrix)
    assert accepted == proper


@pytest.mark.parametrize("matrix", [QUARTER_TURN_2D, QUARTER_TURN_3D])
def test_rot90_round_trip_and_json_schema(matrix):
    rotation = models.Rot90(rot90=matrix, input="source", output="target")
    assert models.Rot90.model_validate_json(rotation.model_dump_json()) == rotation
    validator = Draft202012Validator(models.Rot90.model_json_schema())
    validator.validate(rotation.model_dump(mode="json"))
    assert not validator.is_valid({"rot90": IDENTITY_4X4})


def test_rot90_is_required():
    with pytest.raises(ValidationError):
        models.Rot90()


def test_rot90_coerces_integral_floats():
    matrix = [[float(entry) for entry in row] for row in QUARTER_TURN_2D]
    rotation = models.Rot90(rot90=matrix)
    assert rotation.rot90 == QUARTER_TURN_2D
    assert all(type(entry) is int for row in rotation.rot90 for entry in row)


@pytest.mark.parametrize(
    "matrix,message",
    [
        (
            [[math.cos(0.5), -math.sin(0.5)], [math.sin(0.5), math.cos(0.5)]],
            "integer",
        ),
        ([[1, 1], [0, 1]], "one nonzero entry"),
        ([[2, 0], [0, 1]], "one nonzero entry"),
        ([[0, 0], [0, 1]], "one nonzero entry"),
        # A 2D quarter turn padded to a 3x3 homogeneous matrix is a 3D matrix
        # here, and its translation column breaks the permutation.
        ([[0, -1, 5], [1, 0, 0], [0, 0, 1]], "one nonzero entry"),
        ([[1, 1e-13], [0, 1]], "integer"),
        ([[True, False], [0, 1]], "numbers"),
        ([["1", "0"], [0, 1]], "numbers"),
        ([[1]], "at least 2"),
        (IDENTITY_4X4, "at most 3"),
    ],
    ids=[
        "arbitrary-angle",
        "shear",
        "scaling",
        "singular",
        "homogeneous-2d",
        "roundoff",
        "booleans",
        "strings",
        "1x1",
        "4x4",
    ],
)
def test_rot90_rejects_other_matrices(matrix, message):
    with pytest.raises(ValidationError, match=message):
        models.Rot90(rot90=matrix)


@pytest.mark.parametrize("axes", [["x"], ["y", "x"], ["z"], ["x", "y", "z"]])
def test_reflection_round_trip(axes):
    reflection = models.Reflection(axes=axes)
    assert reflection.axes == axes
    assert (
        models.Reflection.model_validate_json(reflection.model_dump_json())
        == reflection
    )
    Draft202012Validator(models.Reflection.model_json_schema()).validate(
        reflection.model_dump(mode="json")
    )


@pytest.mark.parametrize(
    "axes,message",
    [
        ([], "at least 1"),
        (["x", "x"], "distinct"),
        (["w"], "'x', 'y' or 'z'"),
        (None, "valid list"),
    ],
    ids=["empty", "duplicate", "unknown", "missing"],
)
def test_reflection_rejects_invalid_axes(axes, message):
    with pytest.raises(ValidationError, match=message):
        models.Reflection(axes=axes)


def image(transforms, *systems):
    return models.Image3D(
        coordinate_systems=[coordinate_system(*system) for system in systems],
        coordinate_transformations=transforms,
    )


def sequence(*steps, **names):
    return models.Sequence(sequence=list(steps), **names)


@pytest.mark.parametrize(
    "transform",
    [
        models.Reflection(axes=["z"], input="plane"),
        models.Reflection(axes=["z"], output="plane"),
        sequence(models.Reflection(axes=["z"]), models.Scale(), input="plane"),
        sequence(models.Scale(), models.Reflection(axes=["z"]), output="plane"),
        sequence(models.Reflection(axes=["z"]), output="plane"),
    ],
    ids=["input", "output", "first-step", "last-step", "single-step"],
)
def test_reflection_axes_must_exist_in_named_systems(transform):
    with pytest.raises(ValidationError, match="reflection of axes \\['z'\\].*plane"):
        image([transform], ("plane", 2))


def test_reflection_keeps_the_number_of_axes():
    with pytest.raises(ValidationError, match="number of axes.*plane.*volume"):
        image(
            [models.Reflection(axes=["x"], input="plane", output="volume")],
            ("plane", 2),
            ("volume", 3),
        )
    with pytest.raises(ValidationError, match="number of axes"):
        image(
            [sequence(models.Reflection(axes=["x"], output="volume"), input="plane")],
            ("plane", 2),
            ("volume", 3),
        )


def test_reflection_context_accepts_matching_and_unresolved_systems():
    transforms = [
        models.Reflection(axes=["z"], input="volume", output="volume"),
        models.Reflection(axes=["z"], input="elsewhere"),
        # Interior steps without names are not given a dimension.
        sequence(
            models.Scale(),
            models.Reflection(axes=["z"]),
            models.Scale(),
            input="plane",
            output="plane",
        ),
    ]
    assert image(transforms, ("plane", 2), ("volume", 3))


@pytest.mark.parametrize(
    "matrix,system,message",
    [
        (QUARTER_TURN_2D, ("volume", 3), "2D rot90.*'volume' \\(3 axes\\)"),
        (QUARTER_TURN_3D, ("plane", 2), "3D rot90.*'plane' \\(2 axes\\)"),
        (QUARTER_TURN_3D, ("line", 1), "3D rot90.*'line' \\(1 axis\\)"),
    ],
)
def test_rot90_size_must_match_named_systems(matrix, system, message):
    with pytest.raises(ValidationError, match=message):
        image([models.Rot90(rot90=matrix, output=system[0])], system)
    with pytest.raises(ValidationError, match=message):
        image([sequence(models.Rot90(rot90=matrix), input=system[0])], system)


@pytest.mark.parametrize(
    "factors",
    [[0.0], [-1.0], [1.0, -2.0], [math.nan], [math.inf], [-math.inf]],
    ids=["zero", "negative", "signed", "nan", "inf", "-inf"],
)
def test_scale_factors_must_be_finite_and_positive(factors):
    with pytest.raises(ValidationError, match="finite and positive.*Reflection"):
        models.Scale(scale=factors)


@pytest.mark.parametrize(
    "data",
    [{}, {"scale": None}, {"scale": []}, {"scale": [1.35]}, {"scale": [1.0, 2.0, 3.0]}],
    ids=["omitted", "none", "empty", "single", "vector"],
)
def test_scale_keeps_optional_and_single_factor_forms(data):
    scale = models.Scale(**data)
    assert models.Scale.model_validate_json(scale.model_dump_json()) == scale


def test_orientation_steps_compose_in_images_annotations_and_sequences():
    frame = {
        "transformation_type": "sequence",
        "input": "array",
        "output": "physical",
        "sequence": [
            {"transformation_type": "rot90", "rot90": QUARTER_TURN_3D},
            {"transformation_type": "reflection", "axes": ["x", "z"]},
            {"transformation_type": "translation", "translation": [-32, -32, -16]},
            {"transformation_type": "scale", "scale": [10.8, 10.8, 10.8]},
        ],
    }
    systems = [coordinate_system("array", 3), coordinate_system("physical", 3)]
    for owner in (models.Tomogram, models.PointSet3D):
        instance = owner.model_validate(
            {
                "id": "owner",
                "coordinate_systems": systems,
                "coordinate_transformations": [frame],
            }
        )
        steps = instance.coordinate_transformations[0].sequence
        assert [type(step) for step in steps] == [
            models.Rot90,
            models.Reflection,
            models.Translation,
            models.Scale,
        ]
        assert owner.model_validate_json(instance.model_dump_json()) == instance
        Draft202012Validator(owner.model_json_schema()).validate(
            instance.model_dump(mode="json", exclude_none=True)
        )


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"dropped_inputs": [2]},
        {"created_outputs": [0, 1]},
        {"dropped_inputs": [0], "created_outputs": [0]},
    ],
    ids=["no-op", "drop", "create", "drop-and-create"],
)
def test_project_axis_round_trip(data):
    projection = models.ProjectAxis(**data)
    assert models.ProjectAxis.model_validate_json(projection.model_dump_json()) == (
        projection
    )
    Draft202012Validator(models.ProjectAxis.model_json_schema()).validate(
        projection.model_dump(mode="json")
    )


@pytest.mark.parametrize(
    "field,positions,message",
    [
        ("dropped_inputs", [1, 1], "distinct"),
        ("created_outputs", [-1], "non-negative"),
        ("dropped_inputs", [True], "integers"),
        ("created_outputs", ["0"], "integers"),
        ("dropped_inputs", [0.5], "integer"),
    ],
    ids=["duplicate", "negative", "boolean", "string", "fraction"],
)
def test_project_axis_rejects_invalid_positions(field, positions, message):
    with pytest.raises(ValidationError, match=message):
        models.ProjectAxis(**{field: positions})


def test_project_axis_follows_the_ome_zarr_examples():
    # OME-Zarr 0.6, projectAxis: "Adding multiple dimensions" and
    # "Adding and dropping dimensions".
    systems = [
        {"name": "in", "axes": [{"name": "i"}, {"name": "j"}]},
        {"name": "out", "axes": [{"name": n} for n in "czyx"]},
        {"name": "cij", "axes": [{"name": n} for n in "cij"]},
        {"name": "zyx", "axes": [{"name": n} for n in "zyx"]},
    ]
    assert models.Image3D(
        coordinate_systems=systems,
        coordinate_transformations=[
            models.ProjectAxis(created_outputs=[0, 1], input="in", output="out"),
            models.ProjectAxis(
                created_outputs=[0], dropped_inputs=[0], input="cij", output="zyx"
            ),
        ],
    )


@pytest.mark.parametrize(
    "transform,message",
    [
        (
            models.ProjectAxis(dropped_inputs=[2], input="plane"),
            "drops input positions \\[2\\].*'plane' has 2 axes",
        ),
        (
            models.ProjectAxis(created_outputs=[2], output="plane"),
            "creates output positions \\[2\\].*'plane' has 2 axes",
        ),
        (
            models.ProjectAxis(dropped_inputs=[2], input="volume", output="volume"),
            "maps 'volume' \\(3 axes\\) to 2 axes.*'volume' has 3 axes",
        ),
        (
            sequence(models.ProjectAxis(dropped_inputs=[2]), input="plane"),
            "drops input positions",
        ),
        (
            sequence(
                models.ProjectAxis(created_outputs=[0]),
                input="plane",
                output="plane",
            ),
            "maps 'plane' \\(2 axes\\) to 3 axes",
        ),
    ],
    ids=["dropped", "created", "count", "inherited-input", "inherited-both"],
)
def test_project_axis_must_fit_named_systems(transform, message):
    with pytest.raises(ValidationError, match=message):
        image([transform], ("plane", 2), ("volume", 3))


def test_projection_sequences_change_the_number_of_axes():
    tilt = [[0, 0, 1], [0, 1, 0], [-1, 0, 0]]
    projection = sequence(
        models.Affine(affine=tilt),
        models.ProjectAxis(dropped_inputs=[2]),
        models.Affine(affine=[[0, -1], [1, 0]]),
        models.Translation(translation=[12.0, -8.0]),
        input="volume",
        output="plane",
    )
    instance = image([projection], ("plane", 2), ("volume", 3))
    assert models.Image3D.model_validate_json(instance.model_dump_json()) == instance
    # The first step inherits the 3-axis input, so it must be 3x3.
    projection.sequence[0] = models.Affine(affine=[[0, -1], [1, 0]])
    with pytest.raises(ValidationError, match="2D affine.*'volume' \\(3 axes\\)"):
        image([projection], ("plane", 2), ("volume", 3))
