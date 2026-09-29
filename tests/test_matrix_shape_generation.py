"""Exercise schema-declared matrix alternatives through the production generator."""

import importlib.util
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "tests" / "test_data" / "matrix_shapes.yaml"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    return load_module(
        "cets_generator", ROOT / "model_processing" / "generate_models.py"
    )


@pytest.fixture(scope="module")
def matrix_models(generator, tmp_path_factory):
    output = tmp_path_factory.mktemp("matrix_models") / "models.py"
    output.write_text(generator.build_generator(SCHEMA).serialize())
    return load_module("matrix_models", output)


def identity(size):
    return [[float(row == col) for col in range(size)] for row in range(size)]


@pytest.mark.parametrize(
    "class_name,size", [("MatrixExample", 2), ("DerivedMatrixExample", 3)]
)
def test_accepts_declared_square_matrix_sizes(matrix_models, class_name, size):
    model = getattr(matrix_models, class_name)
    data = {"optional_matrix": identity(size), "required_matrix": identity(size)}
    instance = model(**data)
    assert instance.model_dump() == data
    assert model.model_validate_json(instance.model_dump_json()) == instance
    Draft202012Validator(model.model_json_schema()).validate(data)


@pytest.mark.parametrize(
    "field,matrix",
    [
        ("optional_matrix", identity(4)),
        ("required_matrix", identity(1)),
        ("optional_matrix", [[0.0] * 3 for _ in range(2)]),
        ("required_matrix", [[0.0] * 2 for _ in range(3)]),
        ("optional_matrix", [[0.0] * 3, [0.0] * 2, [0.0] * 3]),
        ("required_matrix", []),
        ("optional_matrix", [0.0, 0.0]),
    ],
    ids=["4x4", "1x1", "2x3", "3x2", "ragged", "empty", "vector"],
)
def test_rejects_invalid_matrix_shapes(matrix_models, field, matrix):
    model = matrix_models.MatrixExample
    data = {"required_matrix": identity(2), field: matrix}
    with pytest.raises(ValidationError):
        model(**data)
    assert not Draft202012Validator(model.model_json_schema()).is_valid(data)


def test_preserves_required_and_optional_fields(matrix_models):
    model = matrix_models.MatrixExample
    assert model(required_matrix=identity(2)).optional_matrix is None
    assert (
        model(optional_matrix=None, required_matrix=identity(2)).optional_matrix is None
    )
    for data in ({}, {"required_matrix": None}):
        with pytest.raises(ValidationError):
            model(**data)
        assert not Draft202012Validator(model.model_json_schema()).is_valid(data)


def test_matrix_sizes_come_from_schema(generator, tmp_path, monkeypatch):
    monkeypatch.setitem(generator.ALIAS_SUB, "optional_matrix", "Optional[Matrix2x2]")
    schema = yaml.safe_load(SCHEMA.read_text())
    alternatives = schema["classes"]["MatrixExample"]["attributes"]["optional_matrix"][
        "any_of"
    ]
    for dimension in alternatives[1]["array"]["dimensions"]:
        dimension["exact_cardinality"] = 5
    path = tmp_path / "schema.yaml"
    path.write_text(yaml.safe_dump(schema))
    output = tmp_path / "models.py"
    output.write_text(generator.build_generator(path).serialize())
    model = load_module("resized_matrix_models", output).MatrixExample
    # The YAML anchor shares the alternatives, so required_matrix changed too.
    assert model(
        optional_matrix=identity(5), required_matrix=identity(2)
    ).optional_matrix == identity(5)
    with pytest.raises(ValidationError):
        model(optional_matrix=identity(3), required_matrix=identity(2))


@pytest.mark.parametrize(
    "constraint",
    [
        "rectangle",
        "mixed_range",
        "parent_dimensions",
        "missing_array",
        "missing_dimension",
        "zero_size",
    ],
)
def test_unsupported_constraints_fail_generation(generator, tmp_path, constraint):
    schema = yaml.safe_load(SCHEMA.read_text())
    slot = schema["classes"]["MatrixExample"]["attributes"]["optional_matrix"]
    if constraint == "rectangle":
        slot["any_of"][0]["array"]["dimensions"][0]["exact_cardinality"] = 3
    elif constraint == "mixed_range":
        slot["any_of"][0]["range"] = "integer"
    elif constraint == "missing_array":
        slot["any_of"][0] = {"range": "float"}
    elif constraint == "missing_dimension":
        slot["any_of"][0]["array"]["dimensions"].pop()
    elif constraint == "zero_size":
        for dimension in slot["any_of"][0]["array"]["dimensions"]:
            dimension["exact_cardinality"] = 0
    else:
        slot["array"]["dimensions"] = [{"exact_cardinality": 3}] * 2
    path = tmp_path / "schema.yaml"
    path.write_text(yaml.safe_dump(schema))
    with pytest.raises(ValueError, match="optional_matrix:.*(matrix|array)"):
        generator.build_generator(path).serialize()
