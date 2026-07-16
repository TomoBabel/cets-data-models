"""Hand-written mixin classes injected into the generated Pydantic image models.

These mixins are combined into the generated ``Image2D`` / ``Image3D`` classes at
generation time by ``model_processing/generate_models.py`` (driven by the
``injected_base_classes`` section of ``model_processing/patch_config.yaml``, via
LinkML's ``after_generate_class`` lifecycle hook). They add read-only,
non-serialized convenience properties.

Each property delegates to a helper in :mod:`cets_data_model.utils.transforms`,
imported *lazily inside the property body* so that importing this module never
triggers a models <-> utils import cycle and does not require ``transforms`` to
exist yet. The properties are plain ``@property`` (not Pydantic fields and not
``@computed_field``), so they never appear in ``model_fields`` / ``model_dump()``
/ ``model_json_schema()``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:  # import for type-checkers/IDEs only; not executed at runtime
    # transforms is implemented separately; ignore until it lands (and is typed).
    from cets_data_model.utils.transforms import (  # type: ignore[import-untyped]
        PixelSize,
        VoxelSize,
    )


class PixelSizeMixin:
    """Adds a read-only ``pixel_size`` property to 2D image models (``Image2D``)."""

    @property
    def pixel_size(self) -> "Optional[PixelSize]":
        """Per-axis pixel size (x, y) in Angstrom, derived from this image's
        array->physical scale transformation. Computed on demand; not stored."""
        from cets_data_model.utils.transforms import (  # type: ignore[import-untyped]
            compute_pixel_size,
        )

        return compute_pixel_size(self)


class VoxelSizeMixin:
    """Adds a read-only ``voxel_size`` property to 3D image models (``Image3D``)."""

    @property
    def voxel_size(self) -> "Optional[VoxelSize]":
        """Per-axis voxel size (x, y, z) in Angstrom, derived from this image's
        array->physical scale transformation. Computed on demand; not stored."""
        from cets_data_model.utils.transforms import (  # type: ignore[import-untyped]
            compute_voxel_size,
        )

        return compute_voxel_size(self)
