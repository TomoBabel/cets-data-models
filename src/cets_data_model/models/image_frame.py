"""Image-frame properties, injected into the generated image models.

The properties read and update the image's ``array_to_physical`` transformation
(see ``cets_data_model.utils.image_frame``). They are not fields, so they are
neither serialized nor part of the JSON Schema.
"""

from typing import ClassVar, cast

from pydantic import BaseModel

from cets_data_model.utils.image_frame import (
    PixelSize,
    VoxelSize,
    read_frame,
    update_frame,
)


class ImageFrameMixin:
    """The frame translation, shared by 2D and 3D images."""

    _frame_dimension: ClassVar[int]

    @property
    def translation(self) -> list[float]:
        """Offset in pixels (or voxels) along the oriented axes; zero by default.

        Setting it keeps the spacing and orientation. It accepts a finite scalar,
        applied to every axis, or one value per axis.
        """
        return list(
            read_frame(cast(BaseModel, self), self._frame_dimension).translation
        )

    @translation.setter
    def translation(self, value: object) -> None:
        update_frame(cast(BaseModel, self), self._frame_dimension, translation=value)


class PixelSizeMixin(ImageFrameMixin):
    """Frame properties of a 2D image."""

    _frame_dimension: ClassVar[int] = 2

    @property
    def pixel_size(self) -> PixelSize:
        """Spacing in Angstrom along the final x and y axes; one by default.

        Setting it keeps the translation and orientation. It accepts a finite
        positive scalar, two values, or a ``PixelSize``.
        """
        return PixelSize(*read_frame(cast(BaseModel, self), 2).spacing)

    @pixel_size.setter
    def pixel_size(self, value: object) -> None:
        update_frame(cast(BaseModel, self), 2, spacing=value)


class VoxelSizeMixin(ImageFrameMixin):
    """Frame properties of a 3D image."""

    _frame_dimension: ClassVar[int] = 3

    @property
    def voxel_size(self) -> VoxelSize:
        """Spacing in Angstrom along the final x, y and z axes; one by default.

        Setting it keeps the translation and orientation. It accepts a finite
        positive scalar, three values, or a ``VoxelSize``.
        """
        return VoxelSize(*read_frame(cast(BaseModel, self), 3).spacing)

    @voxel_size.setter
    def voxel_size(self, value: object) -> None:
        update_frame(cast(BaseModel, self), 3, spacing=value)
