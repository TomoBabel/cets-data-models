"""Validators for coordinate transformations, injected into the generated models.

The mixins add validators only. They declare no fields, so nothing is serialized.
``models.py`` imports this module, so the model classes cannot be imported here;
transformations are identified by their ``transformation_type`` value instead,
and enum members by their ``value``.
"""

from math import isfinite
from typing import Any

from pydantic import ValidationInfo, field_validator

from cets_data_model.models.affine import SPLIT_2D_HINT

#: Position of each reflection axis name in a coordinate system.
REFLECTION_AXIS_INDEX = {"x": 0, "y": 1, "z": 2}


def _value(member: Any) -> Any:
    """Return an enum member's value and any other input unchanged."""
    return getattr(member, "value", member)


def _axis_count(count: int) -> str:
    return f"{count} axis" if count == 1 else f"{count} axes"


def _signed_permutation_columns(block: list[list[int]]) -> list[int] | None:
    """Return the column of each row's single nonzero entry (1 or -1).

    Returns ``None`` unless every row and every column of ``block`` has exactly
    one nonzero entry and that entry is 1 or -1.
    """
    columns = []
    for row in block:
        nonzero = [column for column, entry in enumerate(row) if entry != 0]
        if len(nonzero) != 1 or abs(row[nonzero[0]]) != 1:
            return None
        columns.append(nonzero[0])
    return columns if sorted(columns) == list(range(len(block))) else None


def _signed_permutation_determinant(block: list[list[int]], columns: list[int]) -> int:
    """Return the determinant of a signed permutation matrix (1 or -1)."""
    inversions = sum(
        1
        for i, first in enumerate(columns)
        for second in columns[i + 1 :]
        if first > second
    )
    determinant = -1 if inversions % 2 else 1
    for row, column in zip(block, columns):
        determinant *= row[column]
    return determinant


class Rot90ValidationMixin:
    """Restrict ``Rot90.rot90`` to rotations by quarter turns about axes."""

    @field_validator("rot90", mode="before", check_fields=False)
    @classmethod
    def _reject_non_numeric_entries(cls, matrix: Any) -> Any:
        # Lax integer parsing would otherwise read True as 1 and "1" as 1.
        rows = matrix if isinstance(matrix, (list, tuple)) else []
        for row in rows:
            if isinstance(row, (list, tuple)) and any(
                isinstance(entry, (bool, str)) for entry in row
            ):
                raise ValueError("rot90 entries must be numbers")
        return matrix

    @field_validator("rot90", check_fields=False)
    @classmethod
    def _validate_rot90(cls, matrix: list[list[int]]) -> list[list[int]]:
        # The generated field type has already enforced an integer 2x2 or 3x3.
        # A signed permutation with determinant +1 is exactly a composition of
        # quarter turns about coordinate axes.
        columns = _signed_permutation_columns(matrix)
        if columns is None:
            raise ValueError(
                "rot90 must have exactly one nonzero entry, 1 or -1, in each row "
                "and column"
            )
        if _signed_permutation_determinant(matrix, columns) != 1:
            raise ValueError(
                "rot90 must be a proper rotation (determinant +1); "
                "express a mirror image with Reflection"
            )
        return matrix


class ReflectionValidationMixin:
    """Require distinct axes in ``Reflection.axes``."""

    @field_validator("axes", check_fields=False)
    @classmethod
    def _validate_axes(cls, axes: list[Any]) -> list[Any]:
        names = [_value(axis) for axis in axes]
        if len(set(names)) != len(names):
            raise ValueError(f"reflection axes must be distinct; got {names}")
        return axes


class ScaleValidationMixin:
    """Require finite, strictly positive factors in ``Scale.scale``.

    The number of factors is not checked against coordinate systems: existing
    writers store a single factor for isotropic scaling.
    """

    @field_validator("scale", check_fields=False)
    @classmethod
    def _validate_scale(cls, factors: list[float] | None) -> list[float] | None:
        for factor in factors or []:
            if not (isfinite(factor) and factor > 0):
                raise ValueError(
                    f"scale factors must be finite and positive; got {factor}. "
                    "Express a reversed axis with Reflection."
                )
        return factors


class ProjectAxisValidationMixin:
    """Require distinct, non-negative positions in ``ProjectAxis``."""

    @field_validator(
        "dropped_inputs", "created_outputs", mode="before", check_fields=False
    )
    @classmethod
    def _reject_non_numeric_positions(cls, positions: Any) -> Any:
        # Lax integer parsing would otherwise read True as 1 and "1" as 1.
        if isinstance(positions, (list, tuple)) and any(
            isinstance(position, (bool, str)) for position in positions
        ):
            raise ValueError("axis positions must be integers")
        return positions

    @field_validator("dropped_inputs", "created_outputs", check_fields=False)
    @classmethod
    def _validate_positions(cls, positions: list[int] | None) -> list[int] | None:
        values = positions or []
        if any(position < 0 for position in values) or len(set(values)) != len(values):
            raise ValueError(
                f"axis positions must be distinct and non-negative; got {values}"
            )
        return positions


def _check_projection(transform: Any, inputs: list[Any], outputs: list[Any]) -> None:
    """Raise if a ProjectAxis does not fit its input and output systems."""
    dropped = transform.dropped_inputs or []
    created = transform.created_outputs or []
    for system in inputs:
        axes = len(system.axes)
        if any(position >= axes for position in dropped):
            raise ValueError(
                f"project_axis drops input positions {dropped}, but coordinate "
                f"system {system.name!r} has {_axis_count(axes)}"
            )
        for output in outputs:
            expected = axes - len(dropped) + len(created)
            if len(output.axes) != expected:
                raise ValueError(
                    f"project_axis maps {system.name!r} ({_axis_count(axes)}) to "
                    f"{_axis_count(expected)}, but coordinate system "
                    f"{output.name!r} has {_axis_count(len(output.axes))}"
                )
    for system in outputs:
        axes = len(system.axes)
        if any(position >= axes for position in created):
            raise ValueError(
                f"project_axis creates output positions {created}, but coordinate "
                f"system {system.name!r} has {_axis_count(axes)}"
            )


def _check_dimensions(
    transform: Any,
    systems: list[Any],
    sequence_input: str | None = None,
    sequence_output: str | None = None,
) -> None:
    """Raise if a transformation contradicts a coordinate system it names.

    A transformation names systems through its own ``input``/``output``. The
    first and last step of a sequence also inherit the sequence's ``input`` and
    ``output``. Names that match no entry in ``systems`` are not checked.

    Affine and Rot90 matrices of size n require n axes. A reflection requires
    enough axes for every reflected axis, and the same number on both sides. A
    ProjectAxis requires its positions to exist on each side, and the output to
    have the input's axes minus the dropped plus the created ones.
    """
    kind = transform.transformation_type
    if kind == "sequence":
        steps = transform.sequence or []
        for index, step in enumerate(steps):
            _check_dimensions(
                step,
                systems,
                transform.input if index == 0 else None,
                transform.output if index == len(steps) - 1 else None,
            )
        return
    if kind == "project_axis":
        inputs = {transform.input, sequence_input}
        outputs = {transform.output, sequence_output}
        _check_projection(
            transform,
            [system for system in systems if system.name in inputs],
            [system for system in systems if system.name in outputs],
        )
        return
    names = {transform.input, transform.output, sequence_input, sequence_output}
    named = [system for system in systems if system.name in names]
    if kind in ("affine", "rot90"):
        matrix = getattr(transform, kind)
        if matrix is None:
            return
        dimension = len(matrix)
        for system in named:
            axes = len(system.axes)
            if axes != dimension:
                message = (
                    f"{dimension}D {kind} is incompatible with coordinate system "
                    f"{system.name!r} ({_axis_count(axes)})"
                )
                if kind == "affine" and dimension == 3 and axes == 2:
                    message += ". " + SPLIT_2D_HINT
                raise ValueError(message)
    elif kind == "reflection":
        reflected = [_value(axis) for axis in transform.axes]
        needed = 1 + max(
            (REFLECTION_AXIS_INDEX[axis] for axis in reflected), default=-1
        )
        for system in named:
            axes = len(system.axes)
            if axes < needed:
                raise ValueError(
                    f"reflection of axes {reflected} is incompatible with "
                    f"coordinate system {system.name!r} ({_axis_count(axes)})"
                )
        if len({len(system.axes) for system in named}) > 1:
            counts = ", ".join(
                f"{system.name!r} ({_axis_count(len(system.axes))})" for system in named
            )
            raise ValueError(
                f"reflection must keep the number of axes; it names {counts}"
            )


class TransformContextMixin:
    """Check transformations against coordinate systems declared on the same model.

    Both lists are validated on construction and on replacement. In-place edits
    of either list bypass Pydantic and are not checked.
    """

    @field_validator("coordinate_transformations", check_fields=False)
    @classmethod
    def _validate_transforms_in_context(
        cls, transforms: list[Any] | None, info: ValidationInfo
    ) -> list[Any] | None:
        systems = info.data.get("coordinate_systems") or []
        for transform in transforms or []:
            _check_dimensions(transform, systems)
        return transforms

    @field_validator("coordinate_systems", check_fields=False)
    @classmethod
    def _validate_systems_in_context(
        cls, systems: list[Any] | None, info: ValidationInfo
    ) -> list[Any] | None:
        for transform in info.data.get("coordinate_transformations") or []:
            _check_dimensions(transform, systems or [])
        return systems
