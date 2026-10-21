"""Read and update an image's canonical frame.

The frame is the transformation named ``array_to_physical``, from the ``array``
coordinate system to the ``physical`` one. It is a ``Sequence`` of an optional
``Rot90``, an optional ``Reflection``, a ``Translation`` and a ``Scale``, in that
order and each at most once. For column vectors, with ``R`` the Rot90 matrix and
``F`` the diagonal reflection matrix::

    physical = diag(spacing) @ (F @ R @ index + translation)

Indices, shapes and vectors are in x/y(/z) order. Translation is in pixels (or
voxels) along the oriented axes; spacing is in Angstrom along the final axes.

The alignment (Fourier) center of an image is ``floor(N/2)`` on every axis of
the oriented array. An array reversal moves the origin by ``N - 1``; centering
accounts for it in the translation.

These helpers read and write the serialized fields only. They do not import the
generated models: ``models.py`` imports the mixins that use them, and updates
are validated with the image's own class.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from math import isfinite
from numbers import Integral, Real
from typing import Any

from pydantic import BaseModel

from cets_data_model.models.transforms import validate_rot90

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


#: Right-handed quarter turn about each axis, for column vectors.
_QUARTER_TURNS = {
    "x": ((1, 0, 0), (0, 0, -1), (0, 1, 0)),
    "y": ((0, 0, 1), (0, 1, 0), (-1, 0, 0)),
    "z": ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
}


def quarter_turn_rotation(turns: int, *, ndim: int, axis: str = "z") -> list[list[int]]:
    """Return the Rot90 matrix for ``turns`` quarter turns about ``axis``.

    Turns are right-handed and counted modulo 4, so negative turns rotate the
    other way. A 2D rotation (``ndim=2``) turns in the x-y plane, about ``z``.
    """
    if isinstance(turns, bool) or not isinstance(turns, Integral):
        raise ValueError(f"turns must be an integer; got {turns!r}")
    if ndim not in (2, 3):
        raise ValueError(f"rotations have 2 or 3 axes; got ndim={ndim}")
    if axis not in _QUARTER_TURNS or (ndim == 2 and axis != "z"):
        allowed = "'z'" if ndim == 2 else "'x', 'y' or 'z'"
        raise ValueError(f"a {ndim}D rotation turns about {allowed}; got {axis!r}")
    turn = _QUARTER_TURNS[axis]
    block = [[int(row == column) for column in range(3)] for row in range(3)]
    for _ in range(int(turns) % 4):
        block = [
            [sum(turn[i][k] * block[k][j] for k in range(3)) for j in range(3)]
            for i in range(3)
        ]
    return [row[:ndim] for row in block[:ndim]]


def _shape(shape: object) -> tuple[int, ...]:
    values = list(shape) if isinstance(shape, Iterable) else []
    if len(values) not in (2, 3) or any(
        isinstance(n, bool) or not isinstance(n, Integral) or n <= 0 for n in values
    ):
        raise ValueError(
            f"shape requires 2 or 3 positive integers in x/y(/z) order; got {shape!r}"
        )
    return tuple(int(n) for n in values)


def alignment_center(shape: object) -> tuple[int, ...]:
    """Return the alignment (Fourier) center ``floor(N/2)`` of each axis.

    ``shape`` lists the sizes in x/y(/z) order.
    """
    return tuple(n // 2 for n in _shape(shape))


def _orientation(
    rotation: object, reflection: Iterable[str], ndim: int
) -> list[list[int]]:
    """Return ``F @ R``: the rotation, then the reflection."""
    matrix = identity_rotation(ndim) if rotation is None else _rotation(rotation, ndim)
    reflected = _reflection(reflection, ndim)
    return [
        [-entry if AXES[i] in reflected else entry for entry in row]
        for i, row in enumerate(matrix)
    ]


def centered_translation(
    shape: object, *, rotation: object = None, reflection: Iterable[str] = ()
) -> list[int]:
    """Return the translation that puts the alignment center at the origin.

    ``shape`` is the size of the stored array in x/y(/z) order; ``rotation`` is a
    Rot90 matrix (identity if ``None``) and ``reflection`` the
    reflected axes. With ``O = F @ R``, the oriented array has shape
    ``abs(O) @ shape``; an axis reversed by ``O`` starts at ``N - 1``, recorded
    in ``b``; and the result is ``b - floor(oriented_shape / 2)``.
    """
    sizes = _shape(shape)
    orientation = _orientation(rotation, reflection, len(sizes))
    translation = []
    for row in orientation:
        (column,) = (j for j, entry in enumerate(row) if entry != 0)
        size = sizes[column]
        start = size - 1 if row[column] < 0 else 0
        translation.append(start - size // 2)
    return translation


def _rotation(value: object, ndim: int) -> tuple[tuple[int, ...], ...]:
    """Return a validated Rot90 matrix for ``ndim`` axes."""
    rows = list(value) if isinstance(value, Iterable) else []
    entries = [
        list(row) if isinstance(row, Iterable) and not isinstance(row, str) else []
        for row in rows
    ]
    if len(entries) != ndim or any(len(row) != ndim for row in entries):
        raise ValueError(
            f"rotation of a {ndim}D image must be a {ndim}x{ndim} matrix; got {value!r}"
        )
    if any(
        isinstance(v, bool)
        or not isinstance(v, Real)
        or not (isinstance(v, Integral) or float(v).is_integer())
        for row in entries
        for v in row
    ):
        raise ValueError(f"rotation entries must be integers; got {value!r}")
    matrix = [[int(v) for v in row] for row in entries]
    validate_rot90(matrix)
    return tuple(tuple(row) for row in matrix)


def _reflection(value: object, ndim: int) -> tuple[str, ...]:
    """Return validated, distinct reflection axis names for ``ndim`` axes."""
    if isinstance(value, str) or not isinstance(value, Iterable):
        raise ValueError(f"reflection must be a list of axis names; got {value!r}")
    axes = tuple(_value(axis) for axis in value)
    if not set(axes) <= set(AXES[:ndim]) or len(set(axes)) != len(axes):
        raise ValueError(
            f"reflection of a {ndim}D image lists distinct axes from "
            f"{AXES[:ndim]}; got {list(axes)}"
        )
    return axes


def _image_shape(image: BaseModel, ndim: int) -> tuple[int, ...]:
    names = ("width", "height", "depth")[:ndim]
    try:
        return _shape([getattr(image, name, None) for name in names])
    except ValueError:
        raise ValueError(
            f"centering requires positive {'/'.join(names)}; got "
            f"{[getattr(image, name, None) for name in names]}"
        ) from None


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
    rotation: object = UNSET,
    reflection: object = UNSET,
    translation: object = UNSET,
    spacing: object = UNSET,
    center: bool = False,
) -> None:
    """Replace the supplied frame components and keep all others.

    ``rotation`` is a Rot90 matrix (the identity removes the step)
    and ``reflection`` a list of distinct axis names (an empty list removes the
    step). Translation accepts a finite scalar (applied to every axis) or
    ``ndim`` values; spacing must also be positive. With ``center``, the
    translation is recomputed from the image shape and the new orientation so
    that the alignment center is at the origin.
    """
    current = read_frame(image, ndim)
    frame = Frame(
        current.rotation if rotation is UNSET else _rotation(rotation, ndim),
        current.reflection if reflection is UNSET else _reflection(reflection, ndim),
        current.translation
        if translation is UNSET
        else _vector(translation, ndim, "translation"),
        current.spacing
        if spacing is UNSET
        else _vector(spacing, ndim, "spacing", positive=True),
    )
    if center:
        offset = centered_translation(
            _image_shape(image, ndim),
            rotation=frame.rotation,
            reflection=frame.reflection,
        )
        frame = Frame(
            frame.rotation, frame.reflection, tuple(map(float, offset)), frame.spacing
        )
    write_frame(image, ndim, frame)
