"""Stub implementations of the array->physical scale derivations that back the
image-model convenience properties ``pixel_size`` / ``voxel_size``.

``PixelSizeMixin`` / ``VoxelSizeMixin`` (in ``cets_data_model.models.mixins``)
import from this module both for type checking (the ``PixelSize`` / ``VoxelSize``
result types) and, at property-access time, the ``compute_*`` helpers. These
stubs let those imports resolve so the properties evaluate to ``None`` instead
of raising ``ModuleNotFoundError``. The real derivation logic (from an image's
array->physical scale transformation) lands separately; until then the compute
functions are intentionally no-ops that return ``None``.
"""

from __future__ import annotations

from typing import Optional


class PixelSize:
    """Per-axis pixel size (x, y) in Angstrom. Stub placeholder for the real type."""


class VoxelSize:
    """Per-axis voxel size (x, y, z) in Angstrom. Stub placeholder for the real type."""


def compute_pixel_size(image: object) -> Optional[PixelSize]:
    """Stub: real array->physical derivation lands separately; returns ``None``."""
    pass


def compute_voxel_size(image: object) -> Optional[VoxelSize]:
    """Stub: real array->physical derivation lands separately; returns ``None``."""
    pass
