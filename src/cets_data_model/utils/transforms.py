"""Derivation and construction of the canonical ``array``->``physical`` scale that
backs the image-model convenience properties ``pixel_size`` / ``voxel_size``.

``PixelSizeMixin`` / ``VoxelSizeMixin`` (in ``cets_data_model.models.mixins``) import
from this module both for type checking (the ``PixelSize`` / ``VoxelSize`` result
types) and, at property access/assignment time, the ``compute_*`` getters and
``set_*`` setters.

Design ("Direction B"): the pixel/voxel size is stored as an ordinary ``Scale``
transformation named ``array_to_physical`` (``input="array"`` -> ``output="physical"``),
living in the image's regular ``coordinate_transformations`` list — no cryoET-special
container. The *only* convention is the canonical name, so this module identifies the
scale by ``name == "array_to_physical"``.

This module is an import leaf: the getters are pure duck typing (no model imports), and
the setters construct model objects via LOCAL imports so importing this module never
closes the ``models -> mixins -> transforms`` cycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Union

# Canonical names (kept in sync with the LinkML enums CoordinateSpaceName /
# TransformationName in schema/linkml/coordinate_*.yaml).
ARRAY_TO_PHYSICAL = "array_to_physical"
ARRAY_CS_NAME = "array"
PHYSICAL_CS_NAME = "physical"

Number = Union[int, float]


@dataclass(frozen=True)
class PixelSize:
    """Per-axis pixel size (x, y) in Angstrom, derived from an image's
    ``array``->``physical`` scale."""

    x: float
    y: float

    @property
    def is_isotropic(self) -> bool:
        return self.x == self.y

    @property
    def scalar(self) -> Optional[float]:
        """The single value if isotropic, else ``None``."""
        return self.x if self.is_isotropic else None

    def as_list(self) -> list[float]:
        return [self.x, self.y]


@dataclass(frozen=True)
class VoxelSize:
    """Per-axis voxel size (x, y, z) in Angstrom, derived from an image's
    ``array``->``physical`` scale."""

    x: float
    y: float
    z: float

    @property
    def is_isotropic(self) -> bool:
        return self.x == self.y == self.z

    @property
    def scalar(self) -> Optional[float]:
        """The single value if isotropic, else ``None``."""
        return self.x if self.is_isotropic else None

    def as_list(self) -> list[float]:
        return [self.x, self.y, self.z]


# --------------------------------------------------------------------------- #
# Getters (duck-typed; no model imports)                                       #
# --------------------------------------------------------------------------- #


def _find_array_to_physical_scale(image: object) -> Optional[object]:
    """Return the ``Scale`` whose enclosing transform is named ``array_to_physical``,
    or ``None``. Accepts a direct ``Scale`` or a ``Sequence`` that contains exactly
    one ``Scale``. Duck-typed: reads attributes only."""
    for t in getattr(image, "coordinate_transformations", None) or []:
        if getattr(t, "name", None) != ARRAY_TO_PHYSICAL:
            continue
        ttype = str(getattr(t, "transformation_type", "") or "")
        if ttype == "scale":
            return t
        if ttype == "sequence":
            scales = [
                s
                for s in (getattr(t, "sequence", None) or [])
                if str(getattr(s, "transformation_type", "") or "") == "scale"
            ]
            if len(scales) == 1:
                return scales[0]
    return None


def _broadcast(scale: Optional[list[float]], ndim: int) -> Optional[list[float]]:
    """Normalise a stored scale vector to exactly ``ndim`` values, or ``None`` if
    absent/malformed. A single value is broadcast to every axis."""
    if not scale:
        return None
    if len(scale) == 1:
        return [float(scale[0])] * ndim
    if len(scale) == ndim:
        return [float(v) for v in scale]
    return None


def compute_pixel_size(image: object) -> Optional[PixelSize]:
    """Derive the (x, y) pixel size from ``image``'s ``array_to_physical`` scale."""
    scale = _find_array_to_physical_scale(image)
    vals = _broadcast(getattr(scale, "scale", None) if scale is not None else None, 2)
    return PixelSize(x=vals[0], y=vals[1]) if vals else None


def compute_voxel_size(image: object) -> Optional[VoxelSize]:
    """Derive the (x, y, z) voxel size from ``image``'s ``array_to_physical`` scale."""
    scale = _find_array_to_physical_scale(image)
    vals = _broadcast(getattr(scale, "scale", None) if scale is not None else None, 3)
    return VoxelSize(x=vals[0], y=vals[1], z=vals[2]) if vals else None


# --------------------------------------------------------------------------- #
# Setters (construct model objects via LOCAL imports to stay an import leaf)    #
# --------------------------------------------------------------------------- #


def _coerce_scale(value: Any, ndim: int) -> list[float]:
    """Accept a scalar (broadcast to ``ndim``) or a length-1/``ndim`` sequence."""
    if isinstance(value, (int, float)):
        return [float(value)] * ndim
    try:
        vals = [float(v) for v in value]  # type: ignore[union-attr]
    except TypeError as exc:  # not a number, not iterable
        raise TypeError(
            f"pixel/voxel size must be a number or a sequence of numbers, got {value!r}"
        ) from exc
    if len(vals) == 1:
        return vals * ndim
    if len(vals) == ndim:
        return vals
    raise ValueError(f"expected a scalar or {ndim} values, got {len(vals)}")


def set_pixel_size(image: Any, value: Any) -> None:
    """Set ``image``'s pixel size (2D) by writing the canonical ``array_to_physical`` scale."""
    _set_array_to_physical(image, _coerce_scale(value, 2), ndim=2)


def set_voxel_size(image: Any, value: Any) -> None:
    """Set ``image``'s voxel size (3D) by writing the canonical ``array_to_physical`` scale."""
    _set_array_to_physical(image, _coerce_scale(value, 3), ndim=3)


def _set_array_to_physical(image: Any, scale: list[float], ndim: int) -> None:
    """Replace (or create) the canonical ``array_to_physical`` ``Scale`` and ensure the
    ``array``/``physical`` coordinate systems exist on ``image``. Stored exactly like any
    other transformation."""
    # Local imports keep this module an import leaf at load time, breaking the
    # models -> mixins -> transforms (-> coordinate_systems -> models) cycle.
    from cets_data_model.models.models import Scale
    from cets_data_model.utils.coordinate_systems import (
        array_coords,
        physical_coords_canonical,
    )

    # 1) replace any existing array_to_physical transform, then append the new one.
    transforms = [
        t
        for t in (getattr(image, "coordinate_transformations", None) or [])
        if getattr(t, "name", None) != ARRAY_TO_PHYSICAL
    ]
    transforms.append(
        Scale(
            name=ARRAY_TO_PHYSICAL,
            input=ARRAY_CS_NAME,
            output=PHYSICAL_CS_NAME,
            scale=scale,
        )
    )
    image.coordinate_transformations = transforms

    # 2) ensure the two named coordinate systems exist (idempotent by name).
    systems = list(getattr(image, "coordinate_systems", None) or [])
    existing = {getattr(cs, "name", None) for cs in systems}
    if ARRAY_CS_NAME not in existing:
        systems.append(array_coords(ndim))
    if PHYSICAL_CS_NAME not in existing:
        systems.append(physical_coords_canonical(ndim))
    image.coordinate_systems = systems
