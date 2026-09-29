"""Validators for affine matrices, injected into the generated models.

The mixin adds validators only. It declares no fields, so nothing is serialized.
``models.py`` imports this module, so the model classes cannot be imported here.
"""

from math import isfinite

from pydantic import field_validator

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
