"""The example documents and the documentation code validate against the models."""

import json
import re
from pathlib import Path

import pytest
import yaml
from pydantic import BaseModel

from cets_data_model.models import models
from cets_data_model.utils.image_frame import centered_translation

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def load(path):
    text = path.read_text()
    return yaml.safe_load(text) if path.suffix == ".yaml" else json.loads(text)


def images(node):
    """Yield every Image2D/Image3D in a validated document."""
    if isinstance(node, (models.Image2D, models.Image3D)):
        yield node
    if isinstance(node, BaseModel):
        for name in type(node).model_fields:
            yield from images(getattr(node, name))
    elif isinstance(node, list):
        for item in node:
            yield from images(item)


def test_json_and_yaml_examples_are_the_same_document():
    assert load(EXAMPLES / "mock_named_transforms.json") == load(
        EXAMPLES / "mock_named_transforms.yaml"
    )


@pytest.mark.parametrize(
    "name", ["mock_named_transforms.json", "mock_named_transforms.yaml"]
)
def test_example_frames_are_valid_and_centered(name):
    dataset = models.Dataset.model_validate(load(EXAMPLES / name))
    framed = [image for image in images(dataset) if image.coordinate_transformations]
    assert len(framed) >= 8
    for image in framed:
        ndim = 2 if isinstance(image, models.Image2D) else 3
        shape = [getattr(image, name) for name in ("width", "height", "depth")[:ndim]]
        assert image.translation == centered_translation(
            shape, rotation=image.rotation, reflection=image.reflection
        )
    assert models.Dataset.model_validate_json(dataset.model_dump_json()) == dataset


def axes_after(step, axes):
    """Return the number of axes after ``step``, checking it accepts ``axes``."""
    if isinstance(step, models.Affine):
        assert len(step.affine) == axes, step.name
        return axes
    if isinstance(step, models.Translation):
        assert len(step.translation) == axes, step.name
        return axes
    assert isinstance(step, models.ProjectAxis), step.name
    assert all(position < axes for position in step.dropped_inputs), step.name
    axes += len(step.created_outputs) - len(step.dropped_inputs)
    assert all(position < axes for position in step.created_outputs), step.name
    return axes


def test_example_projection_alignments_compose_from_3d_to_2d():
    dataset = models.Dataset.model_validate(
        load(EXAMPLES / "mock_named_transforms.yaml")
    )
    alignments = [
        projection
        for region in dataset.regions
        for alignment in region.alignments
        for projection in alignment.projection_alignments
    ]
    assert alignments
    for projection in alignments:
        axes = 3  # the tomogram's physical space
        for previous, step in zip(projection.sequence, projection.sequence[1:]):
            assert previous.output == step.input
        for step in projection.sequence:
            axes = axes_after(step, axes)
        assert axes == 2, projection.id


def test_documentation_code_runs():
    text = (ROOT / "docs" / "image-frames.md").read_text()
    blocks = re.findall(r"```python\n(.*?)```", text, flags=re.DOTALL)
    assert len(blocks) >= 3
    namespace: dict = {}
    for block in blocks:
        exec(block, namespace)
