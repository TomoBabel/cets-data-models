# Image frames

An image's frame maps its array indices to physical coordinates in Angstrom.
`Image2D` and its subclasses expose it as `pixel_size` and `translation`;
`Image3D` and its subclasses as `voxel_size` and `translation`. These are Python
properties over ordinary serialized coordinate transformations. They add no data
fields and do not appear in serialized data or the JSON Schema.

## Stored representation

The frame is the transformation named `array_to_physical`, with
`input="array"` and `output="physical"`. It is a `Sequence` of these steps, in
this order and each at most once:

```text
[Rot90] -> [Reflection] -> Translation -> Scale
```

For column vectors, with `R` the spatial block of the `Rot90` and `F` the
diagonal matrix of the `Reflection`:

```text
physical = diag(spacing) @ (F @ R @ index + translation)
```

- Indices, shapes and vectors are in **x, y, z** order (column, row, section).
  A NumPy array is usually indexed **z, y, x**; reverse its shape first.
- `translation` is in pixels (or voxels) along the oriented axes, applied before
  scaling.
- `spacing` is the finite, positive pixel or voxel size in Angstrom along the
  **final** axes. An axis swap by `Rot90` does not permute it.
- `Rot90` and `Reflection` act about the coordinate origin. They carry no pivot;
  offsets belong in `translation`.

The coordinate systems are canonical:

| Name | Axes | `axis_type` | `axis_unit` |
| --- | --- | --- | --- |
| `array` | x, y(, z) | `array` | `pixel` |
| `physical` | x, y(, z) | `space` | `angstrom` |

`pixel` is used for 3D arrays as well; there is no separate voxel unit. Other
coordinate systems and transformations, including projection alignments, keep
their own names, units and rules.

## Reading

Without a frame, the properties report zero translation and unit spacing and do
not modify the image. A frame may omit any step; a missing step means no
rotation, no reflection, zero translation or unit spacing. A standalone `Scale`
named `array_to_physical`, as written by earlier helpers, is read as the spacing;
a single stored factor applies to every axis.

Reading raises `ValueError` rather than guessing when:

- an image has more than one frame, or its name and endpoints disagree;
- the steps are out of order, repeated, or of another type;
- a `Rot90` or `Reflection` step does not fit the image dimension;
- an existing `array` or `physical` system has a different number of axes, axis
  type or unit. For example, a `physical` system in `nanometer` is not converted;
  the spacing could not be confirmed to be in Angstrom.

Stored values are revalidated on every read, because in-place edits of nested
lists bypass Pydantic's assignment validation.

## Writing

```python
from cets_data_model.models.models import Tomogram

tomogram = Tomogram(id="tomo_01", width=64, height=65, depth=6)
tomogram.voxel_size = [2, 3, 4]       # Angstrom along the final x, y, z axes
tomogram.translation = [1, 2, 3]      # the voxel size is kept
tomogram.voxel_size = 5               # a scalar applies to every axis
assert tomogram.translation == [1.0, 2.0, 3.0]
assert tomogram.voxel_size.scalar == 5.0
```

A setter replaces its own component and keeps the others, any `Rot90` or
`Reflection` step, the metadata of existing steps, and all other transformations.
It accepts a finite scalar or one value per axis; spacing must be positive, and a
`PixelSize` or `VoxelSize` can be assigned back. The first write creates the frame
and any missing canonical coordinate system, and promotes a standalone `Scale` to
the full sequence. Repeated writes do not add steps.

Each update is validated as a whole with the image's own class before the image
changes, so an invalid value, or a conflicting coordinate system, leaves the
image unchanged. `PixelSize` and `VoxelSize` are immutable; `as_list()` returns a
new list, `is_isotropic` compares the axes, and `scalar` is the common spacing or
`None`.
