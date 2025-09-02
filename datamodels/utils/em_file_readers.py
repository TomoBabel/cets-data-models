from typing import Tuple
from pathlib import Path
import mrcfile

MRC_EXT = ".mrc"
MRCS_EXT = ".mrcs"


def read_mrc(file_path: Path) -> Tuple[int, int, int, float]:
    allowed_extensions = [MRC_EXT, MRCS_EXT]
    if file_path.suffix not in allowed_extensions:
        raise ValueError(
            f"Invalid file extension. Allowed extensions are: "
            f"{', '.join(allowed_extensions)}"
        )

    with mrcfile.open(file_path, mode="r+", header_only=True, permissive=True) as mrc:
        nx, ny, nz = int(mrc.header.nx), int(mrc.header.ny), int(mrc.header.nz)
        apix = float(mrc.voxel_size.x)

    return nx, ny, nz, apix
