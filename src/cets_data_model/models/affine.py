"""Validators for affine matrices, injected into the generated models.

The mixins add validators only. They declare no fields, so nothing is serialized.
``models.py`` imports this module, so the model classes cannot be imported here;
transformations are identified by their ``transformation_type`` value instead.
"""

from math import isfinite
from typing import Any

from pydantic import ValidationInfo, field_validator

SPLIT_2D_HINT = (
    "A 3x3 affine is a 3D linear map; store a 2D homogeneous 3x3 matrix as its "
    "2x2 block and a separate Translation."
)


class AffineValidationMixin:
    """Require finite entries in ``Affine.affine``."""

    @field_validator("affine", check_fields=False)
    @classmethod
    def _validate_affine(
        cls, matrix: list[list[float]] | None
    ) -> list[list[float]] | None:
        if matrix is None:
            return None
        # The generated field type has already enforced the 2x2 or 3x3 shape.
        if not all(isfinite(entry) for row in matrix for entry in row):
            raise ValueError("affine entries must be finite")
        return matrix


def _check_dimensions(
    transform: Any,
    systems: list[Any],
    sequence_input: str | None = None,
    sequence_output: str | None = None,
) -> None:
    """Raise if an affine's dimension differs from a coordinate system it names.

    An affine names a system through its own ``input``/``output``. The first and
    last step of a sequence also inherit the sequence's ``input`` and ``output``.
    Names that match no entry in ``systems`` are not checked. An n x n matrix
    requires n axes.
    """
    if transform.transformation_type == "sequence":
        steps = transform.sequence or []
        for index, step in enumerate(steps):
            _check_dimensions(
                step,
                systems,
                transform.input if index == 0 else None,
                transform.output if index == len(steps) - 1 else None,
            )
        return
    if transform.transformation_type != "affine" or transform.affine is None:
        return
    dimension = len(transform.affine)
    names = {transform.input, transform.output, sequence_input, sequence_output}
    for system in systems:
        axes = len(system.axes)
        if system.name in names and axes != dimension:
            message = (
                f"{dimension}D affine is incompatible with coordinate system "
                f"{system.name!r} ({axes} {'axis' if axes == 1 else 'axes'})"
            )
            if dimension == 3 and axes == 2:
                message += ". " + SPLIT_2D_HINT
            raise ValueError(message)


class AffineContextMixin:
    """Check affine dimensions against coordinate systems declared on the same model.

    Both lists are validated on construction and on replacement. In-place edits
    of either list bypass Pydantic and are not checked.
    """

    @field_validator("coordinate_transformations", check_fields=False)
    @classmethod
    def _validate_affine_transforms(
        cls, transforms: list[Any] | None, info: ValidationInfo
    ) -> list[Any] | None:
        systems = info.data.get("coordinate_systems") or []
        for transform in transforms or []:
            _check_dimensions(transform, systems)
        return transforms

    @field_validator("coordinate_systems", check_fields=False)
    @classmethod
    def _validate_affine_systems(
        cls, systems: list[Any] | None, info: ValidationInfo
    ) -> list[Any] | None:
        for transform in info.data.get("coordinate_transformations") or []:
            _check_dimensions(transform, systems or [])
        return systems
