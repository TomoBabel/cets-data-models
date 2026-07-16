import ast
import importlib.util
import pytest
import re
import subprocess
from pathlib import Path
from pydantic import ValidationError


@pytest.fixture
def models_path():
    """Path to models file."""
    return Path("src/cets_data_model/models/models.py")


@pytest.fixture
def model_code(models_path):
    """Imported model code."""
    return models_path.read_text()


def test_models_are_valid_python(model_code):
    """
    Verify patched models have valid Python syntax.
    Uses ast.parse, as in validation in patching script,
        to catch syntax errors from regex patching.
    """

    try:
        ast.parse(model_code)
    except SyntaxError as e:
        pytest.fail(f"models.py has syntax error at line {e.lineno}: {e.msg}")


def test_models_can_be_imported(models_path):
    """
    Verify patched models can be imported without errors.
    Catches undefined names, circular imports, etc.
    """

    spec = importlib.util.spec_from_file_location("models", models_path)
    module = importlib.util.module_from_spec(spec)

    try:
        spec.loader.exec_module(module)
    except Exception as e:
        pytest.fail(f"Failed to import models.py: {e}")


def test_type_aliases_present(model_code):
    """
    Verify all expected type aliases were added by patching.
    These aliases are critical for array field validation.
    """

    expected_aliases = [
        "Vector2D",
        "Vector3D",
        "Matrix2x2",
        "Matrix3x3",
        "Radii",
        "Dimensions2D",
        "Dimensions3D",
    ]

    for alias in expected_aliases:
        assert f"{alias}: TypeAlias" in model_code, (
            f"Type alias {alias} should be present in patched models"
        )


def test_discriminated_unions_present(model_code):
    """
    Verify discriminated union fields exist in patched models.
    These are essential for proper Pydantic validation of polymorphic types.
    """

    discriminator_pattern = r'Field\(discriminator="[^"]+"\)'
    matches = re.findall(discriminator_pattern, model_code)

    assert len(matches) > 0, (
        "Should have at least one discriminated union field after patching"
    )


def test_literal_discriminator_fields_present(model_code):
    """
    Verify that discriminator fields in subclasses use Literal types.
    Pattern: transformation_type: Literal[TransformationType.identity]
    This ensures proper type narrowing in discriminated unions.
    """

    literal_pattern = r"Literal\[(TransformationType|AnnotationType)\.\w+\]"
    matches = re.findall(literal_pattern, model_code)

    assert len(matches) > 0, (
        "Should have Literal discriminator fields in subclasses after patching"
    )


def test_required_imports_present(model_code):
    """
    Verify that patching (and tidying with ruff) added necessary typing imports.
    Annotated, Union, Literal, TypeAlias are required for patched features.
    """

    typing_import_pattern = r"from typing import (?:\((.*?)\)|(.*?)$)"
    match = re.search(typing_import_pattern, model_code, re.DOTALL | re.MULTILINE)

    assert match, "Should have typing imports section"

    import_section = match.group(1) or match.group(2)
    required_imports = ["Annotated", "Union", "Literal", "TypeAlias"]

    for required in required_imports:
        assert required in import_section, (
            f"{required} should be imported from typing after patching"
        )


def test_key_classes_exist(models_path):
    """
    Verify that key model classes exist after patching.
    Spot-check some classes from different schema files.
    """
    spec = importlib.util.spec_from_file_location("models", models_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # TODO: add more or full list once models finalised
    expected_classes = [
        "Image2D",
        "Image3D",
        "CoordinateSystem",
        "CoordinateTransformation",
        "Identity",
        "Affine",
        "Sequence",
        "TiltSeries",
        "Tomogram",
        "MovieStack",
        "Annotation",
        "PointSet3D",
        "Region",
        "Dataset",
    ]

    for class_name in expected_classes:
        assert hasattr(module, class_name), (
            f"Class {class_name} should exist in patched models"
        )


def test_discriminated_union_validation_works(models_path):
    """
    Test that discriminated unions actually validate correctly at runtime.
    To ensure the patching produces functionally correct Pydantic models.
    """

    spec = importlib.util.spec_from_file_location("models", models_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # use coordinate transformation field as an example
    Identity = module.Identity
    Scale = module.Scale
    Image2D = module.Image2D

    # Should accept different transformation types in the same list
    img = Image2D(
        width=100,
        height=100,
        coordinate_transformations=[
            Identity(name="identity_transform"),
            Scale(scale=[2.0, 2.0], name="scale_transform"),
        ],
    )

    assert len(img.coordinate_transformations) == 2
    assert img.coordinate_transformations[0].transformation_type == "identity"
    assert img.coordinate_transformations[1].transformation_type == "scale"


def test_type_alias_validation_works(models_path):
    """
    Test that type aliases properly validate array shapes at runtime.
    """

    spec = importlib.util.spec_from_file_location("models", models_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    PointSet3D = module.PointSet3D

    valid_points = PointSet3D(
        annotation_type="point_set_3D",
        origin3D=[
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
        ],
    )
    assert len(valid_points.origin3D) == 2

    with pytest.raises(ValidationError):
        PointSet3D(
            annotation_type="point_set_3D",
            origin3D=[
                [1.0, 2.0],  # Only 2 elements, should be 3
            ],
        )

    with pytest.raises(ValidationError):
        PointSet3D(
            annotation_type="point_set_3D",
            origin3D=[
                [1.0, 2.0, 3.0, 4.0],  # 4 elements, should be 3
            ],
        )


@pytest.mark.skipif(
    not Path("schema/linkml").exists(), reason="Schema files not available"
)
def test_can_regenerate_models():
    """
    Integration test - verify full generation pipeline works.
    This ensures 'make gen-python' command succeeds.
    Skipped if schema files aren't available.
    """
    result = subprocess.run(["make", "gen-python"], capture_output=True, text=True)

    assert result.returncode == 0, f"Model generation failed:\n{result.stderr}"
    assert "Generated models validated" in result.stderr, (
        f"Generation should have validated successfully.\nFull stderr: {result.stderr}"
    )

    # the freshly generated module should carry all generation-time transforms
    generated = Path("src/cets_data_model/models/generated_models.py").read_text()
    assert "Field(discriminator=" in generated  # discriminated unions
    assert ": TypeAlias =" in generated  # type aliases
    assert "treat_empty_lists_as_none" not in generated  # serializer dropped
    assert "class Image2D(PixelSizeMixin," in generated  # mixin injected


# ---------------------------------------------------------------------------
# Injected mixin properties: PixelSizeMixin -> Image2D, VoxelSizeMixin -> Image3D
# (added as base classes at generation time by generate_models.py / the
# `injected_base_classes` registry in patch_config.yaml).
# ---------------------------------------------------------------------------


def _load_models(models_path):
    spec = importlib.util.spec_from_file_location("models", models_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_injected_size_properties_present(models_path):
    """Image2D exposes `pixel_size`, Image3D exposes `voxel_size` -- each a
    read-only property and NOT a Pydantic field."""
    m = _load_models(models_path)
    assert isinstance(m.Image2D.pixel_size, property)
    assert isinstance(m.Image3D.voxel_size, property)
    assert "pixel_size" not in m.Image2D.model_fields
    assert "voxel_size" not in m.Image3D.model_fields


def test_injected_size_properties_dimensional_split(models_path):
    """pixel_size only on 2D images, voxel_size only on 3D images."""
    m = _load_models(models_path)
    assert not hasattr(m.Image2D, "voxel_size")
    assert not hasattr(m.Image3D, "pixel_size")


def test_injected_size_properties_inherited_by_subclasses(models_path):
    """Subclasses inherit the size property matching their dimensionality."""
    m = _load_models(models_path)
    for name in ("MovieFrame", "TiltImage"):
        assert isinstance(getattr(m, name).pixel_size, property), name
    for name in ("Tomogram", "ParticleMap"):
        assert isinstance(getattr(m, name).voxel_size, property), name


def test_injected_size_properties_not_serialized(models_path):
    """Properties never appear in model_dump() or model_json_schema()."""
    m = _load_models(models_path)
    img2 = m.Image2D(width=4, height=4)
    img3 = m.Image3D(width=4, height=4, depth=4)
    assert "pixel_size" not in img2.model_dump()
    assert "voxel_size" not in img3.model_dump()
    assert "pixel_size" not in m.Image2D.model_json_schema().get("properties", {})
    assert "voxel_size" not in m.Image3D.model_json_schema().get("properties", {})
