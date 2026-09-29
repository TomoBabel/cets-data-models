"""Image-frame properties and centering, injected into the generated image models.

The properties read and update the image's ``array_to_physical`` transformation
(see ``cets_data_model.utils.image_frame``). They are not fields, so they are
neither serialized nor part of the JSON Schema.
"""

from typing import ClassVar, cast

from pydantic import BaseModel

from cets_data_model.utils.image_frame import (
    UNSET,
    PixelSize,
    VoxelSize,
    read_frame,
    update_frame,
)


class ImageFrameMixin:
    """Frame orientation, translation and centering, shared by 2D and 3D images."""

    _frame_dimension: ClassVar[int]

    @property
    def rotation(self) -> list[list[int]]:
        """Rot90 matrix applied to array indices; identity by default.

        Setting it keeps the reflection, translation and spacing, and does not
        recenter. The identity removes the Rot90 step.
        """
        frame = read_frame(cast(BaseModel, self), self._frame_dimension)
        return [list(row) for row in frame.rotation]

    @rotation.setter
    def rotation(self, value: object) -> None:
        update_frame(cast(BaseModel, self), self._frame_dimension, rotation=value)

    @property
    def reflection(self) -> list[str]:
        """Axes reflected after the rotation; none by default.

        Setting it keeps the rotation, translation and spacing, and does not
        recenter. An empty list removes the Reflection step.
        """
        return list(read_frame(cast(BaseModel, self), self._frame_dimension).reflection)

    @reflection.setter
    def reflection(self, value: object) -> None:
        update_frame(cast(BaseModel, self), self._frame_dimension, reflection=value)

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

    def center_origin(self) -> None:
        """Set the translation that puts the alignment center at the origin.

        The alignment center is ``floor(N/2)`` on each axis of the oriented
        array. Only the translation changes; the image needs its width and
        height (and depth).
        """
        update_frame(cast(BaseModel, self), self._frame_dimension, center=True)

    def set_centered_frame(
        self,
        *,
        rotation: object = UNSET,
        reflection: object = UNSET,
        spacing: object = UNSET,
    ) -> None:
        """Replace the supplied components and center the origin, all at once.

        Omitted components keep their values. The translation is recomputed as
        in ``center_origin``. Nothing changes if any value is invalid.
        """
        update_frame(
            cast(BaseModel, self),
            self._frame_dimension,
            rotation=rotation,
            reflection=reflection,
            spacing=spacing,
            center=True,
        )


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
