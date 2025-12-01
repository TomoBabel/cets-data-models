import struct

import mrcfile
import os
from dataclasses import dataclass

import numpy as np
from PIL import UnidentifiedImageError, Image
from typing import Optional, Tuple, Union
from warnings import warn
from pathlib import Path


def check_file_is_mrc(file: Union[str, os.PathLike]) -> bool:
    """Validate that a file is a mrc file

    Args:
        file (Union[str, os.PathLike]): The path for the file to check, relative to the project directory

    Retuns:
        bool: The file is a valid mrc
    """
    file = str(file)
    try:
        mrcfile.open(file, header_only=True)
        return True
    except Exception:
        return False


def check_file_is_tif(file: Union[str, os.PathLike]) -> bool:
    """Validate that a file is a tif file

    Args:
        file (Union[str, os.PathLike]): The path for the file to check, relative to
            the project directory

    Retuns:
        bool: The file is a valid tif
    """
    file = str(file)
    try:
        with Image.open(file) as im:
            imgformat = im.format
    except (UnidentifiedImageError, OSError):
        return False
    if imgformat == "TIFF":
        return True
    return False


def get_mrc_dims(in_mrc: Union[str, os.PathLike]) -> Tuple[int, int, int]:
    """Get the shape of a mrc file

    Args:
        in_mrc (Union[str, os.PathLike]): The name of the file
    Returns:
        Tuple[int, int, int]: x,y,z size in pixels

    """
    in_mrc = str(in_mrc)
    with mrcfile.open(in_mrc, header_only=True) as mrc:
        return int(mrc.header.nx), int(mrc.header.ny), int(mrc.header.nz)


def get_tiff_dims(in_tiff: Union[str, os.PathLike]) -> Tuple[int, int, int]:
    """Get the shape of a tiff file

    Args:
        in_tiff (Union[str, os.PathLike]): The name of the file
    Returns:
        Tuple[int, int, int]: x,y,z size in pixels

    """
    in_tiff = str(in_tiff)
    with Image.open(str(in_tiff)) as tif:
        return tif.width, tif.height, tif.n_frames


def get_image_dims(in_img: Union[str, os.PathLike]) -> Tuple[int, int, int]:
    """Get dimensions of an image that might be tiff or mrc

    Args:
        in_img (Union[str, os.PathLike]): Path to the image

    Returns:
        Tuple[int, int, int]: x,y,z size in pixels
    """
    in_img = str(in_img)
    if not Path(in_img).is_file():
        raise ValueError(f"File not found: {in_img}")
    if check_file_is_mrc(in_img):
        return get_mrc_dims(in_img)
    elif check_file_is_tif(in_img):
        return get_tiff_dims(in_img)
    else:
        raise ValueError(f"{in_img} is not a valid mrc or tif file")


@dataclass
class ImageInfo:
    """Info about an image the doesn't require reading the image into memory to get"""

    size_x: int
    size_y: int
    size_z: int
    mode: str
    mode_desc: str
    apix_x: Optional[float]
    apix_y: Optional[float]
    apix_z: Optional[float]


def get_tiff_info(in_tiff: Union[str, os.PathLike]) -> ImageInfo:
    """Get statistics on a tif file

    Args:
        in_tiff (Union[str, os.PathLike]): The name of the file

    Returns:
        ImageInfo: The requested info
    """
    in_tiff = str(in_tiff)
    tiff_modes = {
        "1": "1-bit pixels, black and white, stored with one pixel per byte",
        "L": "8-bit unsigned pixels, grayscale",
        "P": "8-bit unsigned pixels, grayscale, mapped to any other mode using a color"
        " palette",
        "RGB": "3x8-bit pixels, true color",
        "RGBA": "4x8-bit pixels, true color with transparency mask",
        "CMYK": "4x8-bit pixels, color separation",
        "YCbCr": "3x8-bit pixels, color video format",
        "LAB": "3x8-bit pixels, the L*a*b color space",
        "HSV": "3x8-bit pixels, Hue, Saturation, Value color space",
        "I": "32-bit signed integer pixels",
        "F": "32-bit floating point pixels",
        "LA": "8-bit unsigned pixels, grayscale with alpha",
        "PA": "8-bit unsigned pixels, grayscale mapped to palette with alpha",
        "RGBX": "true color with padding",
        "RGBa": "true color with premultiplied alpha",
        "La": "8-bit unsigned pixels, grayscale with premultiplied alpha",
        "I;16": "16-bit unsigned integer pixels",
        "I;16L": "16-bit little endian unsigned integer pixels",
        "I;16B": "16-bit big endian unsigned integer pixels",
        "I;16N": "16-bit native endian unsigned integer pixels",
    }

    x_size, y_size, z_size = get_tiff_dims(in_tiff)
    with Image.open(in_tiff) as tif:
        # Calculate voxel size from resolution tags
        dpi = tif.info.get("dpi", None)
        if dpi is not None:
            # assume voxels are cubic
            apix = dpi[0] / 2.54e-8
        else:
            apix = None

        # get the mode and data type
        mode = tif.mode
        mode_desc = tiff_modes.get(mode, "Cannot determine TIFF mode")

    return ImageInfo(
        size_x=x_size,
        size_y=y_size,
        size_z=z_size,
        mode=mode,
        mode_desc=mode_desc,
        apix_x=apix,
        apix_y=apix,
        apix_z=None if z_size == 1 else apix,
    )


def get_mrc_info(in_mrc: Union[str, os.PathLike]) -> ImageInfo:
    """Get statistics on a mrc file

    Args:
        in_mrc (Union[str, os.PathLike]): The name of the file

    Returns:
        ImageInfo: The requested info
    """
    in_mrc = str(in_mrc)
    modes = {
        "0": "8-bit signed integer (range -128 to 127)",
        "1": "16-bit signed integer",
        "2": "32-bit signed real",
        "3": "transform : complex 16-bit integers",
        "4": "transform : complex 32-bit reals",
        "6": "16-bit unsigned integer",
        "12": "16-bit float (IEEE754)",
    }

    with mrcfile.open(in_mrc, header_only=True) as mrc:
        if not mrc.validate():
            warn(f"Validation errors were encountered reading {in_mrc}")
        head = mrc.header
        mode = str(head.mode)
        mode_desc = modes.get(mode, f"Unknown mode (data type): {mode}")
        return ImageInfo(
            size_x=int(head.nx),
            size_y=int(head.ny),
            size_z=int(head.nz),
            mode=str(mode),
            mode_desc=mode_desc,
            apix_x=head.cella.x / head.mx,
            apix_y=head.cella.y / head.my,
            apix_z=None if head.nz == 1 else head.cella.x / head.mx,  # assume cubic
        )


def get_em_file_info(in_em_file: Union[str, os.PathLike]) -> ImageInfo:
    """
    Get statistics on a .em from the classic TOM toolbox (e.g. used by Dynamo)

    Args:
        in_em_file (Union[str, os.PathLike]): The name of the file

    Returns:
        ImageInfo: The requested info
    """
    with open(in_em_file, "rb") as f:
        # Read the header (512 bytes)
        header_binary = f.read(512)

        # Byte 3: Data type
        data_type_code = header_binary[3]

        # Bytes 4-16: Dimensions X, Y, Z (integers of 4 bytes)
        nx, ny, nz = struct.unpack("<3i", header_binary[4:16])

        # Bytes 40, 44, and 48: physical dimensions (integers of 4 bytes)
        phys_x, phys_y, phys_z = struct.unpack("<3i", header_binary[40:52])

        # Sampling rate calculation:
        if phys_x > 0 and nx > 0:
            apix_x = phys_x / nx
            apix_y = phys_y / ny
            apix_z = phys_z / nz
        else:
            # Not stored in the header
            apix_x, apix_y, apix_z = (None, None, None)

        # Get the dtype
        dtype = np.float32
        if data_type_code == 1:
            dtype = np.int8
        elif data_type_code == 2:
            dtype = np.int16
        elif data_type_code == 4:
            dtype = np.int32
        elif data_type_code == 5:
            dtype = np.float32
        elif data_type_code == 8:
            dtype = np.complex64

        return ImageInfo(
            size_x=nx,
            size_y=ny,
            size_z=nz,
            mode=str(data_type_code),
            mode_desc=str(dtype),
            apix_x=apix_x,
            apix_y=apix_y,
            apix_z=apix_z,
        )


def get_em_info(img_name: Union[str, os.PathLike]) -> ImageInfo:
    """Get info about a mrc, em or tiff image

    Args:
        img_name (Union[str, os.PathLike]): Path to the image file

    Returns:
        ImageInfo: Info about the image

    Raises:
        ValueError: If the image is not a valid mrc or tiff
    """
    if not os.path.exists(img_name):
        raise FileNotFoundError(f"File {img_name} does not exist.")
    if check_file_is_mrc(img_name):
        return get_mrc_info(img_name)
    elif check_file_is_tif(img_name):
        return get_tiff_info(img_name)
    else:
        raise ValueError(f"{img_name} is not a valid mrc or tif file")
