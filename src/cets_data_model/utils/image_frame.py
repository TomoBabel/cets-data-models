"""Read and update an image's canonical frame.

The frame is the transformation named ``array_to_physical``, from the ``array``
coordinate system to the ``physical`` one. It is a ``Sequence`` of an optional
``Rot90``, an optional ``Reflection``, a ``Translation`` and a ``Scale``, in that
order and each at most once. For column vectors, with ``R`` the Rot90 matrix and
``F`` the diagonal reflection matrix::

    physical = diag(spacing) @ (F @ R @ index + translation)

Indices, shapes and vectors are in x/y(/z) order. Translation is in pixels (or
voxels) along the oriented axes; spacing is in Angstrom along the final axes.

These helpers read and write the serialized fields only. They do not import the
generated models: ``models.py`` imports the mixins that use them, and updates
are validated with the image's own class.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from math import isfinite
from numbers import Real
from typing import Any

from pydantic import BaseModel

ARRAY = "array"
PHYSICAL = "physical"
ARRAY_TO_PHYSICAL = "array_to_physical"
AXES = ("x", "y", "z")

#: Frame steps in their required order.
STEP_ORDER = ("rot90", "reflection", "translation", "scale")

#: Axis type and unit of every axis in the canonical coordinate systems.
_CANONICAL_AXES = {ARRAY: ("array", "pixel"), PHYSICAL: ("space", "angstrom")}


class _Unset:
    """Marker for a frame component that an update keeps."""


UNSET: Any = _Unset()


@dataclass(frozen=True)
class PixelSize:
    """Pixel spacing in Angstrom along the final x and y axes."""

    x: float
    y: float

    @property
    def is_isotropic(self) -> bool:
        return self.x == self.y

    @property
    def scalar(self) -> float | None:
        """The spacing if it is isotropic, else ``None``."""
        return self.x if self.is_isotropic else None

    def as_list(self) -> list[float]:
        return [self.x, self.y]


@dataclass(frozen=True)
class VoxelSize:
    """Voxel spacing in Angstrom along the final x, y and z axes."""

    x: float
    y: float
    z: float

    @property
    def is_isotropic(self) -> bool:
        return self.x == self.y == self.z

    @property
    def scalar(self) -> float | None:
        """The spacing if it is isotropic, else ``None``."""
        return self.x if self.is_isotropic else None

    def as_list(self) -> list[float]:
        return [self.x, self.y, self.z]


@dataclass(frozen=True)
class Frame:
    """The components of a canonical frame for an image with ``ndim`` axes."""

    #: Rot90 matrix, ndim x ndim; identity if absent.
    rotation: tuple[tuple[int, ...], ...]
    #: Reflected axis names; empty if absent.
    reflection: tuple[str, ...]
    translation: tuple[float, ...]
    spacing: tuple[float, ...]


def identity_rotation(ndim: int) -> tuple[tuple[int, ...], ...]:
    """Return the ``ndim`` x ``ndim`` identity matrix."""
    return tuple(
        tuple(int(row == column) for column in range(ndim)) for row in range(ndim)
    )


def canonical_systems(ndim: int) -> list[dict[str, Any]]:
    """Return fresh ``array`` and ``physical`` coordinate systems for ``ndim`` axes."""
    if ndim not in (2, 3):
        raise ValueError(f"image frames have 2 or 3 axes; got {ndim}")
    return [
        {
            "name": name,
            "axes": [
                {"name": axis, "axis_type": axis_type, "axis_unit": unit}
                for axis in AXES[:ndim]
            ],
        }
        for name, (axis_type, unit) in _CANONICAL_AXES.items()
    ]


def _value(member: Any) -> Any:
    """Return an enum member's value and any other input unchanged."""
    return getattr(member, "value", member)


def _vector(
    value: object, ndim: int, label: str, *, positive: bool = False
) -> tuple[float, ...]:
    """Return ``ndim`` finite floats from a scalar (broadcast) or a sequence."""
    if isinstance(value, (PixelSize, VoxelSize)):
        value = value.as_list()
    if isinstance(value, Real):
        values = [value] * ndim
    elif isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        values = list(value)
    else:
        raise ValueError(f"{label} must be a number or a sequence of {ndim} numbers")
    if len(values) != ndim:
        raise ValueError(f"{label} requires a scalar or {ndim} values; got {values}")
    if any(
        isinstance(v, bool) or not isinstance(v, Real) or not isfinite(v)
        for v in values
    ):
        raise ValueError(f"{label} requires finite numbers; got {values}")
    if positive and any(v <= 0 for v in values):
        raise ValueError(f"{label} requires positive values; got {values}")
    return tuple(float(v) for v in values)


def _stored_spacing(factors: list[float] | None, ndim: int) -> tuple[float, ...]:
    # A single stored factor applies to every axis.
    if factors is not None and len(factors) == 1:
        factors = factors * ndim
    return _vector(factors, ndim, "array_to_physical scale", positive=True)


def _canonical_transform(image: BaseModel) -> Any | None:
    """Return the image's frame transformation, or ``None`` if it has none."""
    candidates = [
        transform
        for transform in getattr(image, "coordinate_transformations", None) or []
        if transform.name == ARRAY_TO_PHYSICAL
        or (transform.input == ARRAY and transform.output == PHYSICAL)
    ]
    if len(candidates) > 1:
        raise ValueError(
            f"an image has at most one {ARRAY_TO_PHYSICAL!r} transformation "
            f"(from {ARRAY!r} to {PHYSICAL!r}); found {len(candidates)}"
        )
    if not candidates:
        return None
    transform = candidates[0]
    if (transform.name, transform.input, transform.output) != (
        ARRAY_TO_PHYSICAL,
        ARRAY,
        PHYSICAL,
    ):
        raise ValueError(
            f"the {ARRAY_TO_PHYSICAL!r} transformation must be named so and map "
            f"input {ARRAY!r} to output {PHYSICAL!r}; got name={transform.name!r}, "
            f"input={transform.input!r}, output={transform.output!r}"
        )
    return transform


def _missing_systems(image: BaseModel, ndim: int) -> list[dict[str, Any]]:
    """Return the canonical systems the image lacks.

    Raise if an existing ``array`` or ``physical`` system differs from the
    canonical one in its number of axes, axis types or units. Axis names are not
    compared.
    """
    systems = getattr(image, "coordinate_systems", None) or []
    missing = []
    for expected in canonical_systems(ndim):
        name = expected["name"]
        matches = [system for system in systems if system.name == name]
        if len(matches) > 1:
            raise ValueError(f"duplicate {name!r} coordinate systems")
        if not matches:
            missing.append(expected)
            continue
        found = [
            (_value(axis.axis_type), _value(axis.axis_unit)) for axis in matches[0].axes
        ]
        wanted = [(axis["axis_type"], axis["axis_unit"]) for axis in expected["axes"]]
        if found != wanted:
            axis_type, unit = _CANONICAL_AXES[name]
            raise ValueError(
                f"coordinate system {name!r} must have {ndim} axes of type "
                f"{axis_type!r} in {unit!r} for the image frame; got "
                f"(type, unit) = {found}"
            )
    return missing


def read_frame(image: BaseModel, ndim: int) -> Frame:
    """Return the image's frame, or the default frame if it has none.

    The default frame has no rotation or reflection, zero translation and unit
    spacing; reading it does not modify the image. A standalone ``Scale`` in
    place of the sequence is read as the spacing. Stored values are revalidated,
    because in-place edits of nested lists bypass Pydantic validation.
    """
    _missing_systems(image, ndim)
    identity = identity_rotation(ndim)
    translation = (0.0,) * ndim
    spacing = (1.0,) * ndim
    transform = _canonical_transform(image)
    if transform is None:
        return Frame(identity, (), translation, spacing)
    transform = type(transform).model_validate(transform.model_dump())
    if transform.transformation_type == "scale":
        return Frame(identity, (), translation, _stored_spacing(transform.scale, ndim))
    if transform.transformation_type != "sequence":
        raise ValueError(
            f"the {ARRAY_TO_PHYSICAL!r} transformation must be a sequence or a "
            f"scale; got {transform.transformation_type!r}"
        )
    kinds = [step.transformation_type for step in transform.sequence or []]
    if not set(kinds) <= set(STEP_ORDER) or kinds != sorted(
        set(kinds), key=STEP_ORDER.index
    ):
        raise ValueError(
            f"{ARRAY_TO_PHYSICAL!r} steps must be [rot90] -> [reflection] -> "
            f"[translation] -> [scale], each at most once; got {kinds}"
        )
    steps = {step.transformation_type: step for step in transform.sequence or []}
    rotation = identity
    if "rot90" in steps:
        rotation = tuple(tuple(row) for row in steps["rot90"].rot90)
        if len(rotation) != ndim:
            raise ValueError(
                f"the rot90 step of a {ndim}D image frame must be "
                f"{ndim}x{ndim}; got {len(rotation)}x{len(rotation)}"
            )
    reflection: tuple[str, ...] = ()
    if "reflection" in steps:
        reflection = tuple(_value(axis) for axis in steps["reflection"].axes)
        if not set(reflection) <= set(AXES[:ndim]):
            raise ValueError(
                f"the reflection step of a {ndim}D image frame may only name "
                f"axes {AXES[:ndim]}; got {list(reflection)}"
            )
    if "translation" in steps:
        translation = _vector(
            steps["translation"].translation, ndim, "array_to_physical translation"
        )
    if "scale" in steps:
        spacing = _stored_spacing(steps["scale"].scale, ndim)
    return Frame(rotation, reflection, translation, spacing)


def _frame_transform(frame: Frame, ndim: int, original: Any | None) -> dict[str, Any]:
    """Return the serialized frame sequence.

    Fields of the existing sequence and of its steps that the frame does not
    define (for example a step's ``name``) are kept.
    """
    kept: dict[str, dict[str, Any]] = {}
    outer: dict[str, Any] = {}
    if original is not None and original.transformation_type == "sequence":
        outer = {k: v for k, v in original.model_dump().items() if k != "sequence"}
        kept = {
            step.transformation_type: step.model_dump() for step in original.sequence
        }
    payloads: list[tuple[str, str, Any]] = []
    if frame.rotation != identity_rotation(ndim):
        payloads.append(("rot90", "rot90", [list(row) for row in frame.rotation]))
    if frame.reflection:
        payloads.append(("reflection", "axes", list(frame.reflection)))
    payloads.append(("translation", "translation", list(frame.translation)))
    payloads.append(("scale", "scale", list(frame.spacing)))
    return {
        **outer,
        "transformation_type": "sequence",
        "name": ARRAY_TO_PHYSICAL,
        "input": ARRAY,
        "output": PHYSICAL,
        "sequence": [
            {**kept.get(kind, {"transformation_type": kind}), field: value}
            for kind, field, value in payloads
        ],
    }


def write_frame(image: BaseModel, ndim: int, frame: Frame) -> None:
    """Store ``frame`` as the image's frame, validating before any change.

    The new frame and any missing canonical coordinate system are built as
    serialized data; other transformations and systems are kept as they are.
    The candidate is validated with the image's own class, and only then are
    ``coordinate_systems`` and ``coordinate_transformations`` replaced together,
    so a failed update leaves the image unchanged. Existing objects are never
    modified.
    """
    original = _canonical_transform(image)
    frame_data = _frame_transform(frame, ndim, original)
    transforms: list[Any] = [
        frame_data if transform is original else transform
        for transform in getattr(image, "coordinate_transformations", None) or []
    ]
    if original is None:
        transforms.append(frame_data)
    systems: list[Any] = list(getattr(image, "coordinate_systems", None) or [])
    systems += _missing_systems(image, ndim)

    model = type(image)
    data = {name: getattr(image, name) for name in model.model_fields}
    data.update(coordinate_systems=systems, coordinate_transformations=transforms)
    candidate = model.model_validate(data)
    # Assign both fields without per-field assignment validation, which would
    # check each new list against the other, still old one.
    for name in ("coordinate_systems", "coordinate_transformations"):
        object.__setattr__(image, name, getattr(candidate, name))
    image.__pydantic_fields_set__.update(
        ("coordinate_systems", "coordinate_transformations")
    )


def update_frame(
    image: BaseModel,
    ndim: int,
    *,
    translation: object = UNSET,
    spacing: object = UNSET,
) -> None:
    """Replace the supplied frame components and keep all others.

    Translation accepts a finite scalar (applied to every axis) or ``ndim``
    values; spacing must also be positive.
    """
    current = read_frame(image, ndim)
    write_frame(
        image,
        ndim,
        Frame(
            current.rotation,
            current.reflection,
            current.translation
            if translation is UNSET
            else _vector(translation, ndim, "translation"),
            current.spacing
            if spacing is UNSET
            else _vector(spacing, ndim, "spacing", positive=True),
        ),
    )
