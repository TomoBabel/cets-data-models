"""Frame properties of images: pixel/voxel size and translation."""

import importlib.util
import math
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from cets_data_model.models import models
from cets_data_model.utils.image_frame import (
    Frame,
    PixelSize,
    VoxelSize,
    _frame_transform,
    canonical_systems,
)

MODELS_PATH = Path(models.__file__)


def new_image(ndim, module=models):
    if ndim == 2:
        return module.Image2D(width=5, height=6)
    return module.Image3D(width=5, height=6, depth=7)


def size_property(ndim):
    return "pixel_size" if ndim == 2 else "voxel_size"


def frame(*steps, **overrides):
    return {
        "transformation_type": "sequence",
        "name": "array_to_physical",
        "input": "array",
        "output": "physical",
        "sequence": list(steps),
        **overrides,
    }


def step(kind, field, value, **metadata):
    return {"transformation_type": kind, field: value, **metadata}


def rot90(ndim):
    block = [[0, -1, 0], [1, 0, 0], [0, 0, 1]][:ndim]
    return [row[:ndim] for row in block]


def snapshot(image):
    return (
        image.model_dump_json(),
        set(image.model_fields_set),
        [id(item) for item in image.coordinate_systems],
        [id(item) for item in image.coordinate_transformations],
    )


@pytest.mark.parametrize("ndim", [2, 3])
def test_defaults_do_not_modify_the_image(ndim):
    image = new_image(ndim)
    before = snapshot(image)
    assert getattr(image, size_property(ndim)).as_list() == [1.0] * ndim
    assert image.translation == [0.0] * ndim
    image.translation[0] = 100.0  # a detached copy
    assert snapshot(image) == before


@pytest.mark.parametrize("ndim", [2, 3])
@pytest.mark.parametrize("size_first", [True, False])
def test_setters_keep_other_components_and_objects(ndim, size_first):
    size = size_property(ndim)
    spacing, offset = [2.0, 3.0, 4.0][:ndim], [-1.5, 2.0, 7.0][:ndim]
    image = new_image(ndim)
    image.coordinate_systems = [
        {"name": "native", "axes": [{"name": "u", "axis_unit": "nanometer"}]}
    ]
    image.coordinate_transformations = [
        {"transformation_type": "translation", "name": "shift", "translation": [7]}
    ]
    native, shift = image.coordinate_systems[0], image.coordinate_transformations[0]
    updates = [(size, spacing), ("translation", offset)]
    for name, value in updates if size_first else updates[::-1]:
        setattr(image, name, value)
    image.translation = offset  # repeated writes replace, not append
    assert getattr(image, size).as_list() == spacing
    assert image.translation == offset
    assert image.coordinate_systems[0] is native
    assert image.coordinate_transformations[0] is shift
    assert [system.name for system in image.coordinate_systems] == [
        "native",
        "array",
        "physical",
    ]
    stored = image.coordinate_transformations[1]
    assert [s.transformation_type for s in stored.sequence] == ["translation", "scale"]
    assert type(image).model_validate_json(image.model_dump_json()) == image


@pytest.mark.parametrize("ndim", [2, 3])
def test_setters_keep_orientation_steps_and_step_metadata(ndim):
    image = new_image(ndim)
    image.coordinate_transformations = [
        frame(
            step("rot90", "rot90", rot90(ndim), name="to scanner axes"),
            step("reflection", "axes", ["y"]),
            step("translation", "translation", [1.0] * ndim, name="origin"),
            step("scale", "scale", [2.0] * ndim),
        )
    ]
    setattr(image, size_property(ndim), 3)
    image.translation = 4
    steps = image.coordinate_transformations[0].sequence
    assert [(s.transformation_type, s.name) for s in steps] == [
        ("rot90", "to scanner axes"),
        ("reflection", None),
        ("translation", "origin"),
        ("scale", None),
    ]
    assert steps[0].rot90 == rot90(ndim)
    assert steps[1].axes == ["y"]
    assert steps[2].translation == [4.0] * ndim
    assert steps[3].scale == [3.0] * ndim


def test_every_image_class_has_its_frame_properties():
    classes = {
        name: cls
        for name, cls in vars(models).items()
        if isinstance(cls, type) and issubclass(cls, (models.Image2D, models.Image3D))
    }
    # Annotation images inherit the properties through LinkML mixins.
    assert {"SegmentationMask2D", "ProbabilityMap3D", "DensityMap"} <= set(classes)
    for name, cls in classes.items():
        ndim = 2 if issubclass(cls, models.Image2D) else 3
        image = cls(**({"id": "image"} if "id" in cls.model_fields else {}))
        assert not hasattr(image, size_property(5 - ndim)), name
        setattr(image, size_property(ndim), 2)
        image.translation = -3
        assert getattr(image, size_property(ndim)).scalar == 2.0, name
        assert image.translation == [-3.0] * ndim, name
        assert cls.model_validate_json(image.model_dump_json()) == image, name


@pytest.mark.parametrize("ndim", [2, 3])
def test_properties_are_not_serialized(ndim):
    image = new_image(ndim)
    setattr(image, size_property(ndim), 2)
    schema = type(image).model_json_schema()["properties"]
    for name in (size_property(ndim), "translation", "_frame_dimension"):
        assert name not in image.model_dump()
        assert name not in schema


def test_size_results_are_immutable_values():
    pixel = PixelSize(1.0, 2.0)
    assert not pixel.is_isotropic and pixel.scalar is None
    with pytest.raises(FrozenInstanceError):
        pixel.x = 3.0  # type: ignore[misc]
    pixel.as_list().append(0.0)
    assert pixel.as_list() == [1.0, 2.0]
    voxel = VoxelSize(2.0, 2.0, 2.0)
    assert voxel.is_isotropic and voxel.scalar == 2.0
    tomogram = models.Tomogram(id="tomogram")
    tomogram.voxel_size = VoxelSize(1.0, 2.0, 3.0)
    assert tomogram.voxel_size == VoxelSize(1.0, 2.0, 3.0)


def test_canonical_systems_are_fresh_and_2d_or_3d():
    first, second = canonical_systems(3), canonical_systems(3)
    assert first == second and first is not second
    first[0]["axes"][0]["axis_unit"] = "changed"
    assert canonical_systems(3) == second
    with pytest.raises(ValueError, match="2 or 3 axes"):
        canonical_systems(4)


@pytest.mark.parametrize("with_systems", [False, True])
@pytest.mark.parametrize("factors", [[1.35], [1.35, 1.35]])
def test_standalone_scale_is_read_and_promoted(with_systems, factors):
    legacy = {
        "transformation_type": "scale",
        "name": "array_to_physical",
        "input": "array",
        "output": "physical",
        "scale": factors,
    }
    image = models.Image2D(
        coordinate_systems=canonical_systems(2) if with_systems else [],
        coordinate_transformations=[legacy],
    )
    assert image.pixel_size == PixelSize(1.35, 1.35)
    image.translation = [-2, -3]
    assert image.coordinate_transformations[0].transformation_type == "sequence"
    assert image.pixel_size == PixelSize(1.35, 1.35)
    assert len(image.coordinate_systems) == 2


@pytest.mark.parametrize(
    "steps,translation,spacing",
    [
        ([], [0.0, 0.0], [1.0, 1.0]),
        ([step("scale", "scale", [2.0])], [0.0, 0.0], [2.0, 2.0]),
        ([step("translation", "translation", [1, 2])], [1.0, 2.0], [1.0, 1.0]),
    ],
    ids=["empty", "scale-only", "translation-only"],
)
def test_missing_steps_read_as_defaults(steps, translation, spacing):
    image = models.Image2D(coordinate_transformations=[frame(*steps)])
    assert image.translation == translation
    assert image.pixel_size.as_list() == spacing


def assert_reads_and_writes_fail(image, message):
    before = snapshot(image)
    with pytest.raises(ValueError, match=message):
        image.translation
    with pytest.raises(ValueError, match=message):
        image.translation = [0, 0]
    assert snapshot(image) == before


@pytest.mark.parametrize(
    "transforms,message",
    [
        (
            [
                frame(
                    step("scale", "scale", [1.0]),
                    step("translation", "translation", [0, 0]),
                )
            ],
            "steps must be",
        ),
        (
            [
                frame(
                    step("translation", "translation", [0, 0]),
                    step("translation", "translation", [0, 0]),
                )
            ],
            "steps must be",
        ),
        ([frame(step("affine", "affine", [[1, 0, 0], [0, 1, 0], [0, 0, 1]]))], "steps"),
        (
            [
                {
                    "transformation_type": "identity",
                    "name": "array_to_physical",
                    "input": "array",
                    "output": "physical",
                }
            ],
            "sequence or a scale",
        ),
        ([frame(step("rot90", "rot90", rot90(3)))], "2D image frame must be 2x2"),
        ([frame(step("reflection", "axes", ["z"]))], "may only name axes"),
        ([frame(step("translation", "translation", [1.0]))], "2 values"),
        ([frame(output="elsewhere")], "map input 'array' to output 'physical'"),
        ([frame(name=None)], "must be named so"),
        ([frame(), frame()], "at most one"),
    ],
    ids=[
        "order",
        "repeated",
        "other-step",
        "other-type",
        "rot90-size",
        "reflection-axis",
        "translation-length",
        "endpoint",
        "unnamed",
        "two-frames",
    ],
)
def test_malformed_frames_raise_on_read_and_write(transforms, message):
    image = models.Image2D(coordinate_transformations=transforms)
    assert_reads_and_writes_fail(image, message)


def axes(count, axis_type, unit):
    return [
        {"name": name, "axis_type": axis_type, "axis_unit": unit}
        for name in "xyz"[:count]
    ]


@pytest.mark.parametrize(
    "systems,message",
    [
        # Units outside the AxisUnit enum are rejected when the model is built.
        (
            [{"name": "physical", "axes": axes(2, "space", "nanometer")}],
            "in 'angstrom'",
        ),
        ([{"name": "physical", "axes": axes(3, "space", "angstrom")}], "2 axes"),
        ([{"name": "physical", "axes": axes(2, None, "angstrom")}], "type 'space'"),
        ([{"name": "array", "axes": axes(2, "array", "pixel")}] * 2, "duplicate"),
    ],
    ids=["nanometer", "axis-count", "untyped", "twice"],
)
def test_conflicting_canonical_systems_raise_on_read_and_write(systems, message):
    image = models.Image2D(coordinate_systems=systems)
    assert_reads_and_writes_fail(image, message)


INVALID_VECTORS = {
    "nan": math.nan,
    "inf": math.inf,
    "bool": True,
    "string": "1",
    "none": None,
    "short": [1, 2],
    "long": [1, 2, 3, 4],
}
NONPOSITIVE = {"zero": 0, "negative": -1.0, "one-negative": [1, 2, -3]}


@pytest.mark.parametrize(
    "name,value",
    [
        pytest.param("voxel_size", value, id=f"voxel_size-{label}")
        for label, value in {**INVALID_VECTORS, **NONPOSITIVE}.items()
    ]
    + [
        pytest.param("translation", value, id=f"translation-{label}")
        for label, value in INVALID_VECTORS.items()
    ],
)
def test_invalid_updates_leave_the_image_unchanged(name, value):
    tomogram = models.Tomogram(id="tomogram")
    tomogram.voxel_size = [1, 2, 3]
    tomogram.translation = [4, 5, 6]
    before = snapshot(tomogram)
    with pytest.raises(ValueError):
        setattr(tomogram, name, value)
    assert snapshot(tomogram) == before


def test_in_place_edits_are_caught_on_access():
    tomogram = models.Tomogram(id="tomogram")
    tomogram.voxel_size = 2
    tomogram.coordinate_transformations[0].sequence[1].scale[0] = -2.0
    before = snapshot(tomogram)
    with pytest.raises(ValueError, match="finite and positive"):
        tomogram.voxel_size
    with pytest.raises(ValueError, match="finite and positive"):
        tomogram.translation = 1
    assert snapshot(tomogram) == before


def test_setters_use_the_image_class_of_an_independent_module():
    spec = importlib.util.spec_from_file_location("independent_models", MODELS_PATH)
    module = importlib.util.module_from_spec(spec)
    # Not registered in sys.modules: updates must not look up public classes.
    spec.loader.exec_module(module)
    tomogram = module.Tomogram(id="tomogram")
    tomogram.voxel_size = [1, 2, 3]
    tomogram.translation = [4, 5, 6]
    assert isinstance(tomogram.coordinate_transformations[0], module.Sequence)
    assert isinstance(tomogram.coordinate_systems[0], module.CoordinateSystem)
    assert module.Tomogram.model_validate_json(tomogram.model_dump_json()) == tomogram


def test_frame_transform_keeps_other_fields_of_the_sequence():
    # A future schema may add fields to Sequence (for example a target id);
    # an update must carry them over, like it carries over step names.
    class Step:
        transformation_type = "scale"

        def model_dump(self):
            return {"transformation_type": "scale", "name": "spacing", "scale": [1]}

    class Original:
        transformation_type = "sequence"
        sequence = [Step()]

        def model_dump(self):
            return {
                "transformation_type": "sequence",
                "name": "array_to_physical",
                "input": "array",
                "output": "physical",
                "target_id": "tomogram_01",
                "sequence": [step.model_dump() for step in self.sequence],
            }

    frame = Frame(((1, 0), (0, 1)), (), (0.0, 0.0), (2.0, 2.0))
    data = _frame_transform(frame, 2, Original())
    assert data["target_id"] == "tomogram_01"
    assert [step["transformation_type"] for step in data["sequence"]] == [
        "translation",
        "scale",
    ]
    assert data["sequence"][1] == {
        "transformation_type": "scale",
        "name": "spacing",
        "scale": [2.0, 2.0],
    }
