"""Public linear affine matrices and validation against named coordinate spaces."""

import math

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from cets_data_model.models import models
from cets_data_model.models.affine import AffineContextMixin


def identity(size):
    return [[float(row == column) for column in range(size)] for row in range(size)]


def coordinate_system(name, dimension):
    return {"name": name, "axes": [{"name": axis} for axis in "xyz"[:dimension]]}


@pytest.mark.parametrize("size", [2, 3])
def test_affine_round_trip_with_general_linear_matrix(size):
    matrix = identity(size)
    angle = math.radians(30)  # General affine rotations are not restricted to Rot90.
    matrix[0][:2] = [math.cos(angle), -math.sin(angle)]
    matrix[1][:2] = [math.sin(angle), math.cos(angle)]
    matrix[0][1] *= 1.5  # A shear keeps the matrix a general linear map.
    affine = models.Affine(affine=matrix, input="source", output="target")
    assert affine.affine == matrix
    assert models.Affine.model_validate_json(affine.model_dump_json()) == affine
    Draft202012Validator(models.Affine.model_json_schema()).validate(
        affine.model_dump(mode="json")
    )
    image = models.Image2D(coordinate_transformations=[affine])
    assert isinstance(image.coordinate_transformations[0], models.Affine)
    assert models.Image2D.model_validate_json(image.model_dump_json()) == image


def test_affine_remains_optional():
    for data in ({}, {"affine": None}):
        affine = models.Affine(**data)
        assert affine.affine is None
        assert models.Affine.model_validate_json(affine.model_dump_json()) == affine


@pytest.mark.parametrize(
    "matrix",
    [
        [[0.0] * 3 for _ in range(2)],
        [[0.0] * 2 for _ in range(3)],
        identity(4),
        [[1.0]],
        [[1.0, 0.0], [0.0]],
    ],
    ids=["2x3", "3x2", "4x4", "1x1", "ragged"],
)
def test_public_affine_rejects_other_shapes(matrix):
    data = {"affine": matrix}
    with pytest.raises(ValidationError):
        models.Affine(**data)
    assert not Draft202012Validator(models.Affine.model_json_schema()).is_valid(data)


def test_homogeneous_matrices_are_not_a_shape():
    # Neither 3x3-for-2D nor 4x4-for-3D is a homogeneous form here: a 3x3 is a
    # 3D linear map and a 4x4 has no meaning.
    schema = Draft202012Validator(models.Affine.model_json_schema())
    assert schema.is_valid({"affine": identity(3)})
    assert not schema.is_valid({"affine": identity(4)})


@pytest.mark.parametrize(
    "size,row,column,value",
    [(2, 0, 0, math.nan), (3, 0, -1, math.inf), (3, -1, -1, -math.inf)],
    ids=["nan", "inf", "negative-inf"],
)
def test_affine_rejects_nonfinite_entries(size, row, column, value):
    matrix = identity(size)
    matrix[row][column] = value
    with pytest.raises(ValidationError, match="finite"):
        models.Affine(affine=matrix)
    # JSON Schema encodes shapes; the injected Python validator adds semantics.


def test_relion_z_rotation_is_a_3d_matrix_stored_unchanged():
    # cets-relion/tests/test_data/results/proj_aligned.py, first z rotation.
    # Keep the numeric fixture so this regression needs no SciPy dependency.
    matrix = [
        [0.08658269165227545, -0.9962446674920009, 0.0],
        [0.9962446674920009, 0.08658269165227545, 0.0],
        [0.0, 0.0, 1.0000000000000002],
    ]
    affine = models.Affine(affine=matrix, input="volume")
    assert affine.affine == matrix  # No row is rewritten.
    assert models.Image3D(
        coordinate_systems=[coordinate_system("volume", 3)],
        coordinate_transformations=[affine],
    )


def test_2d_homogeneous_matrix_is_split_into_matrix_and_translation():
    # A 2D rotation stored as a 3x3 homogeneous matrix (cets-imod, cets-scipion
    # tilt series) is a 3D matrix here and contradicts a two-axis system.
    block = [[0.8, -0.6], [0.6, 0.8]]
    homogeneous = [row + [shift] for row, shift in zip(block, [12.5, -3.0])]
    homogeneous.append([0.0, 0.0, 1.0])
    with pytest.raises(
        ValidationError, match="3D affine.*plane.*2x2 block.*Translation"
    ):
        models.Image2D(
            coordinate_systems=[coordinate_system("plane", 2)],
            coordinate_transformations=[
                models.Affine(affine=homogeneous, input="plane")
            ],
        )
    split = models.Sequence(
        input="plane",
        output="plane",
        sequence=[
            models.Affine(affine=block),
            models.Translation(translation=[12.5, -3.0]),
        ],
    )
    image = models.Image2D(
        coordinate_systems=[coordinate_system("plane", 2)],
        coordinate_transformations=[split],
    )
    assert models.Image2D.model_validate_json(image.model_dump_json()) == image


@pytest.mark.parametrize(
    "invalid",
    [
        identity(4),
        [[math.inf, 0, 0], [0, 1, 0], [0, 0, 1]],
        [[1, 0, 0], [0, 1, 0]],
    ],
    ids=["4x4", "inf", "2x3"],
)
def test_invalid_matrix_assignment_preserves_previous_value(invalid):
    affine = models.Affine(affine=identity(3))
    with pytest.raises(ValidationError):
        affine.affine = invalid
    assert affine.affine == identity(3)
    affine.affine = identity(2)
    assert affine.affine == identity(2)


@pytest.mark.parametrize(
    "owner,endpoint",
    [
        (models.Image2D, "input"),
        (models.Image3D, "output"),
        (models.MovieFrame, "output"),
        (models.Tomogram, "input"),
        (models.PointMatrixSet3D, "output"),
    ],
)
def test_named_spaces_determine_rank_including_inherited_models(owner, endpoint):
    data = {
        "coordinate_systems": [coordinate_system("volume", 3)],
        "coordinate_transformations": [
            {"transformation_type": "affine", "affine": identity(3), endpoint: "volume"}
        ],
    }
    if "id" in owner.model_fields:
        data["id"] = "example"
    instance = owner(**data)
    assert owner.model_validate_json(instance.model_dump_json()) == instance
    data["coordinate_transformations"][0]["affine"] = identity(2)
    with pytest.raises(ValidationError, match="2D affine.*volume.*3 axes"):
        owner(**data)


@pytest.mark.parametrize("endpoint", ["input", "output"])
def test_named_sequence_boundaries(endpoint):
    affine = models.Affine(affine=identity(3))
    steps = (
        [affine, models.Identity()]
        if endpoint == "input"
        else [models.Identity(), affine]
    )
    with pytest.raises(ValidationError, match="3D affine.*plane.*2 axes"):
        models.Image2D(
            coordinate_systems=[coordinate_system("plane", 2)],
            coordinate_transformations=[
                models.Sequence(sequence=steps, **{endpoint: "plane"})
            ],
        )


def test_sequence_checks_interior_steps_by_their_own_names():
    with pytest.raises(ValidationError, match="3D affine.*plane.*2 axes"):
        models.Image2D(
            coordinate_systems=[coordinate_system("plane", 2)],
            coordinate_transformations=[
                models.Sequence(
                    sequence=[
                        models.Identity(),
                        models.Affine(affine=identity(3), input="plane"),
                        models.Identity(),
                    ]
                )
            ],
        )


def test_unresolved_names_and_sequence_interiors_do_not_infer_image_rank():
    instance = models.Image2D(
        coordinate_systems=[coordinate_system("plane", 2)],
        coordinate_transformations=[
            models.Affine(affine=identity(3), input="external_volume"),
            models.Sequence(
                input="plane",
                output="plane",
                sequence=[
                    models.Identity(),
                    models.Affine(affine=identity(3)),
                    models.Identity(),
                ],
            ),
        ],
    )
    assert models.Image2D.model_validate_json(instance.model_dump_json()) == instance


def test_context_list_replacements_validate_before_assignment():
    instance = models.Image2D(
        coordinate_systems=[coordinate_system("space", 2)],
        coordinate_transformations=[models.Affine(affine=identity(2), input="space")],
    )
    before = instance.model_dump()
    with pytest.raises(ValidationError, match="incompatible"):
        instance.coordinate_transformations = [
            models.Affine(affine=identity(3), input="space")
        ]
    assert instance.model_dump() == before
    with pytest.raises(ValidationError, match="incompatible"):
        instance.coordinate_systems = [coordinate_system("space", 3)]
    assert instance.model_dump() == before
    instance.coordinate_transformations = [
        models.Affine(affine=identity(2), output="space")
    ]
    assert instance.coordinate_transformations[0].output == "space"


@pytest.mark.parametrize("dimension", [2, 3])
def test_annotation_matrix_sizes_match_the_affine_sizes(dimension):
    model = getattr(models, f"PointMatrixSet{dimension}D")
    field = f"matrix{dimension}D"
    assert model(id="annotation", **{field: [identity(dimension)]})
    with pytest.raises(ValidationError):
        model(id="annotation", **{field: [identity(dimension + 1)]})


def test_every_model_with_transformations_checks_affine_context():
    owners = [
        cls
        for cls in vars(models).values()
        if isinstance(cls, type)
        and issubclass(cls, models.ConfiguredBaseModel)
        and "coordinate_transformations" in cls.model_fields
    ]
    missing = [
        cls.__name__ for cls in owners if not issubclass(cls, AffineContextMixin)
    ]
    assert owners and not missing


def test_unrelated_transform_validation_is_unchanged():
    # The affine checks leave other transformation types and their lengths alone.
    instance = models.Image2D(
        coordinate_systems=[coordinate_system("plane", 2)],
        coordinate_transformations=[
            models.Scale(scale=[-1, 0, 2], input="plane"),
            models.Translation(translation=[1, 2, 3], output="plane"),
        ],
    )
    assert models.Image2D.model_validate_json(instance.model_dump_json()) == instance
