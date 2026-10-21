# Image frames

An image's frame maps its array indices to physical coordinates in Angstrom.
`Image2D` and its subclasses expose it as `pixel_size`, and `Image3D` and its
subclasses as `voxel_size`. Both expose `rotation`, `reflection` and
`translation`, and the methods `center_origin()` and `set_centered_frame()`.
These are Python properties and methods over ordinary serialized coordinate
transformations. They add no data fields and do not appear in serialized data or
the JSON Schema.

## Stored representation

The frame is the transformation named `array_to_physical`, with
`input="array"` and `output="physical"`. It is a `Sequence` of these steps, in
this order and each at most once:

```text
[Rot90] -> [Reflection] -> Translation -> Scale
```

For column vectors, with `R` the `Rot90` matrix and `F` the diagonal matrix of
the `Reflection`:

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

## Orientation

`rotation` is the `Rot90` matrix of the frame (2x2 in 2D, 3x3 in 3D), and
`reflection` the list of axes negated after it. Setting either keeps the
other components and does not recenter. The identity rotation and an empty
reflection list remove their step. Getters return new lists.

```python
from cets_data_model.utils.image_frame import quarter_turn_rotation

quarter_turn_rotation(1, ndim=2)            # [[0, -1], [1, 0]]
quarter_turn_rotation(-1, ndim=3, axis="x")  # a quarter turn back about x
```

`quarter_turn_rotation(turns, *, ndim, axis="z")` returns right-handed quarter
turns, counted modulo 4; a 2D rotation turns about `z`. Any composition of
quarter turns is a valid rotation; a mirror image needs a reflection.

## Centering

**The alignment (Fourier) center is always `floor(N/2)` on each axis of the
oriented array.** A length-64 and a length-65 axis both have center index 32.
It is neither `(N - 1)/2` nor selectable per pipeline.

With `O = F @ R`, the oriented array has shape `n_out = abs(O) @ n_file`. An axis
that `O` reverses starts at `N - 1`: `b[i] = n_file[j] - 1` for a negative
`O[i, j]`, else 0. The centered translation is

```text
translation = b - floor(n_out / 2)
```

so that the file index at the oriented center maps to physical zero. Reversing a
length-6 z axis gives the centered coordinate `2 - z`: simply negating
coordinates centered at file index 3 would be off by one voxel.

```python
from cets_data_model.models.models import Tomogram
from cets_data_model.utils.image_frame import alignment_center, centered_translation

tomogram = Tomogram(id="tomo_01", width=64, height=65, depth=6)
tomogram.voxel_size = [2, 3, 4]
tomogram.reflection = ["z"]           # translation and spacing are kept
tomogram.center_origin()              # only the translation changes
assert tomogram.translation == [-32.0, -32.0, 2.0]

# Replace the supplied components and recenter, as one update.
tomogram.set_centered_frame(
    rotation=quarter_turn_rotation(-1, ndim=3, axis="x"),
    reflection=[],
    spacing=[2, 4, 3],
)
# The file shape (64, 65, 6) becomes the oriented shape (64, 6, 65).
assert tomogram.translation == [-32.0, -3.0, 32.0]
assert alignment_center((64, 65, 6)) == (32, 32, 3)
assert centered_translation((64, 65, 6), reflection=["z"]) == [-32, -32, 2]
```

`center_origin()` needs the image's width and height (and depth) and changes
only the translation. `set_centered_frame(*, rotation, reflection, spacing)`
keeps omitted components and recomputes the translation; everything is
validated before the image changes. Native registrations about another pivot
must be converted into an explicit translation in this convention; calling a
centering method deliberately replaces that offset with the centered one.

## Pipeline conventions

### RELION

RELION documents its alignment center as the integer `floor(N/2)` in its
[orientation conventions](https://relion.readthedocs.io/en/latest/Reference/Conventions.html#orientations).
Its [Fourier centering](https://github.com/3dem/relion/blob/210f68c865b28e6806c6b721f1a6ed3374c788d2/src/jaz/image/centering.h#L42)
uses integer half sizes, consistent with `numpy.fft.ifftshift`.

The tomogram handedness flag (`rlnTomoHand`) sets the sign of the
depth-dependent CTF defocus correction in
[Tomogram::getCtf](https://github.com/3dem/relion/blob/210f68c865b28e6806c6b721f1a6ed3374c788d2/src/jaz/tomography/tomogram.cpp#L270).
It is **not** an instruction to reflect the stored volume. Keep handedness
metadata separate from the frame; actual axis swaps and flips belong in it.

### AreTomo3

From AreTomo3 commit
[`8a068cf`](https://github.com/czimaginginstitute/AreTomo3/tree/8a068cf74cc25b8107a4dd1053689fe9f952b000):
both [WBP](https://github.com/czimaginginstitute/AreTomo3/blob/8a068cf74cc25b8107a4dd1053689fe9f952b000/AreTomo/Recon/CDoWbpRecon.cpp#L107)
and [SART](https://github.com/czimaginginstitute/AreTomo3/blob/8a068cf74cc25b8107a4dd1053689fe9f952b000/AreTomo/Recon/CDoSartRecon.cpp#L119)
reverse the reconstruction depth **before**
[mFlipVol](https://github.com/czimaginginstitute/AreTomo3/blob/8a068cf74cc25b8107a4dd1053689fe9f952b000/AreTomo/CAreTomoMain.cpp#L893)
calls [CTiltSeries::FlipVol](https://github.com/czimaginginstitute/AreTomo3/blob/8a068cf74cc25b8107a4dd1053689fe9f952b000/DataUtil/CTiltSeries.cpp#L286).
For file indices `(u, v, w)` and reconstruction depth `D`:

| FlipVol | File axis order | Reconstruction grid index | `rotation` | `reflection` |
| --- | --- | --- | --- | --- |
| 0 | XZY | `(u, w, D-1-v)` | `quarter_turn_rotation(-1, ndim=3, axis="x")` | `[]` |
| 1 | XYZ | `(u, v, w)` | identity | `[]` |
| 2 | XYZ | `(u, v, D-1-w)` | identity | `["z"]` |

Pass the written file's shape, this orientation and the final-axis spacing to
`set_centered_frame()`. FlipVol 1 and 2 give the same XYZ shape, so the flag must
come from run metadata. `tests/test_pipeline_frames.py` reproduces the storage
loops on small labeled volumes and compares every voxel for all three flags. It
does not run a reconstruction or establish a pipeline's absolute registration:
binning, cropping and reconstruction offsets still need converting by each
importer.

## Projection alignments

A projection alignment maps the tomogram's physical space (3 axes) to a
projection's (2 axes). Square matrices cannot change the number of axes, so the
projection is an explicit `ProjectAxis` step (OME-Zarr 0.6 `projectAxis`). An
`Affine` holds the linear part only, so the shift is its own `Translation` step:

```text
tilt: Affine 3x3 (3D) -> project: ProjectAxis dropping z -> in-plane rotation: Affine 2x2 (2D) -> shift: Translation (2D)
```

`dropped_inputs` lists the positions of input axes to drop and `created_outputs`
the positions of new output axes, whose coordinate is 0. The other axes keep
their order. With x, y, z at positions 0, 1, 2, `dropped_inputs: [2]` drops z. A
projection that drops an axis is not invertible. Writers that store only the 2D
in-plane part may omit the tilt and the projection.

## Scope

Consumers must recognize the `rot90`, `reflection` and `project_axis`
transformation types before reading data that contains them. The frame helpers
do not read or write projection alignments. Whether an alignment is local
(`is_local_alignment`) needs the nonrigid schema and is not derived here.
