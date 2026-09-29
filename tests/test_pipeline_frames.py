"""Pipeline conventions reproduced from pinned sources; see docs/image-frames.md.

These are index-level fixtures. They do not run a reconstruction or establish a
pipeline's absolute registration.
"""

import numpy as np
import pytest

from cets_data_model.models import models
from cets_data_model.utils.image_frame import alignment_center, quarter_turn_rotation


@pytest.mark.parametrize("n", [1, 5, 6, 64, 65])
def test_relion_fourier_center_matches_ifftshift(n):
    # Centering::humanFullToFftwFull: out(x) = in((x + w/2) % w), integer w/2.
    ramp = np.arange(n)
    native = np.array([ramp[(i + n // 2) % n] for i in range(n)])
    np.testing.assert_array_equal(native, np.fft.ifftshift(ramp))
    assert alignment_center((n, n)) == (int(native[0]), int(native[0]))
    image = models.Image2D(width=n, height=n)
    image.center_origin()
    assert image.translation == [-float(native[0])] * 2


def aretomo_written_volume(reconstruction, flag):
    """Reproduce how AreTomo3 stores a reconstruction for a FlipVol flag.

    CDoWbpRecon/CDoSartRecon::mGetReconResult write each XZ plane with reversed
    Z into frames indexed by Y (storage axes XZY). CTiltSeries::FlipVol swaps
    row and section; flag 1 also reverses the old row.
    """
    nx, ny, nz = reconstruction.shape
    stored = np.empty((nx, nz, ny), dtype=reconstruction.dtype)
    for y in range(ny):
        for z in range(nz):
            stored[:, nz - 1 - z, y] = reconstruction[:, y, z]
    if flag == 0:
        return stored
    result = np.empty((nx, ny, nz), dtype=reconstruction.dtype)
    for old_row in range(nz):
        new_section = nz - 1 - old_row if flag == 1 else old_row
        for old_section in range(ny):
            result[:, old_section, new_section] = stored[:, old_row, old_section]
    return result


@pytest.mark.parametrize("shape", [(4, 6, 8), (5, 7, 9), (5, 6, 7)])
@pytest.mark.parametrize("flag", [0, 1, 2])
def test_aretomo_flipvol_orientations_recover_every_voxel(shape, flag):
    reconstruction = np.arange(np.prod(shape)).reshape(shape)
    stored = aretomo_written_volume(reconstruction, flag)
    image = models.Image3D(**dict(zip(("width", "height", "depth"), stored.shape)))
    image.set_centered_frame(
        rotation=quarter_turn_rotation(-1 if flag == 0 else 0, ndim=3, axis="x"),
        reflection=["z"] if flag == 2 else [],
        spacing=[2, 3, 4],
    )
    orientation = np.array(image.rotation)
    for axis in image.reflection:
        orientation["xyz".index(axis)] *= -1
    center = np.array(shape) // 2
    for index in np.ndindex(stored.shape):
        centered = orientation @ index + image.translation
        grid = tuple((centered + center).astype(int))
        assert stored[index] == reconstruction[grid]


def test_relion_handedness_is_independent_of_the_image_frame():
    session = models.AcquisitionSession(id="session", handedness="right_handed")
    image = models.TiltImage(id="tilt", width=64, height=65)
    image.set_centered_frame(spacing=2, reflection=["y"])
    frame = [t.model_dump() for t in image.coordinate_transformations]
    # rlnTomoHand changes the sign of the depth-dependent defocus in
    # Tomogram::getCtf; it is acquisition metadata, not a reflection.
    session.handedness = "left_handed"
    assert [t.model_dump() for t in image.coordinate_transformations] == frame
    assert image.reflection == ["y"]
    restored = models.AcquisitionSession.model_validate_json(session.model_dump_json())
    assert restored.handedness == "left_handed"
