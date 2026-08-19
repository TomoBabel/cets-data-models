"""Hand-written mixin classes injected into the generated Pydantic image models
for convenience.

These mixins are combined into the generated classes at generation time by
``model_processing/generate_models.py`` (driven by the ``injected_base_classes``
section of ``model_processing/patch_config.yaml``, via LinkML's ``after_generate_class``
lifecycle hook). They add non-serialized, settable convenience properties: the getter
derives the value from the model's ``array``->``physical`` scale transformation and the
setter writes that transformation back. The property is never a Pydantic field, so it
does not appear in ``model_fields``, ``model_dump()``, or the JSON schema.
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

    @pixel_size.setter
    def pixel_size(self, value: "float | list[float]") -> None:
        """Set the pixel size (2D): a scalar (broadcast to x, y) or an [x, y] list.
        Writes the canonical ``array_to_physical`` scale + coordinate systems."""
        from cets_data_model.utils.transforms import (  # type: ignore[import-untyped]
            set_pixel_size,
        )

        set_pixel_size(self, value)


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

    @voxel_size.setter
    def voxel_size(self, value: "float | list[float]") -> None:
        """Set the voxel size (3D): a scalar (broadcast to x, y, z) or an [x, y, z] list.
        Writes the canonical ``array_to_physical`` scale + coordinate systems."""
        from cets_data_model.utils.transforms import (  # type: ignore[import-untyped]
            set_voxel_size,
        )

        set_voxel_size(self, value)
