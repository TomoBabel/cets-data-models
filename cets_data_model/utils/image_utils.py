import mrcfile
from dataclasses import dataclass
from PIL import UnidentifiedImageError, Image
from typing import Optional, Tuple
from warnings import warn
from pathlib import Path


def check_file_is_mrc(file: str) -> bool:
    """Validate that a file is a mrc file

    Args:
        file (str): The path for the file to check, relative to the project directory

    Retuns:
        bool: The file is a valid mrc
    """
    try:
        mrcfile.open(file, header_only=True)
        return True
    except Exception:
        return False


def check_file_is_tif(file: str) -> bool:
    """Validate that a file is a tif file

    Args:
        file (str): The path for the file to check, relative to the project directory

    Retuns:
        bool: The file is a valid tif
    """
    try:
        with Image.open(file) as im:
            imgformat = im.format
    except (UnidentifiedImageError, OSError):
        return False
    if imgformat == "TIFF":
        return True
    return False


def get_mrc_dims(in_mrc: str) -> Tuple[int, int, int]:
    """Get the shape of a mrc file

    Args:
        in_mrc (str): The name of the file
    Returns:
        Tuple[int, int, int]: x,y,z size in pixels

    """
    with mrcfile.open(in_mrc, header_only=True) as mrc:
        return int(mrc.header.nx), int(mrc.header.ny), int(mrc.header.nz)


def get_tiff_dims(in_tiff: str) -> Tuple[int, int, int]:
    """Get the shape of a tiff file

    Args:
        in_tiff (str): The name of the file
    Returns:
        Tuple[int, int, int]: x,y,z size in pixels

    """
    with Image.open(in_tiff) as tif:
        height, width = tif.size[:2]
        return width, height, tif.n_frames


def get_image_dims(in_img: str) -> Tuple[int, int, int]:
    """Get dimensions of an image that might be tiff or mrc

    Args:
        in_img (str): Path to the image

    Returns:
        Tuple[int, int, int]: x,y,z size in pixels
    """
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


def get_tiff_info(in_tiff: str) -> ImageInfo:
    """Get statistics on a tif file

    Args:
        in_tiff (str): The name of the file

    Returns:
        ImageInfo: The requested info
    """
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


def get_mrc_info(in_mrc: str) -> ImageInfo:
    """Get statistics on a mrc file

    Args:
        in_mrc (str): The name of the file

    Returns:
        ImageInfo: The requested info
    """

    modes = {
        "0": "8-bit signed integer (range -128 to 127)",
        "1": "16-bit signed integer",
        "2": "32-bit signed real",
        "3": "transform : complex 16-bit integers",
        "4": "transform : complex 32-bit reals",
        "6": "16-bit unsigned integer",
        "12": "16-bit float (IEEE754)",
    }

    with mrcfile.mmap(in_mrc) as mrc:
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


def get_image_info(img_name: str) -> ImageInfo:
    """Get info about a mrc or tiff image

    Args:
        img_name (str): Path to the image file

    Returns:
        ImageInfo: Info about the image

    Raises:
        ValueError: If the image is not a valid mrc or tiff
    """

    if check_file_is_mrc(img_name):
        return get_mrc_info(img_name)
    elif check_file_is_tif(img_name):
        return get_tiff_info(img_name)
    else:
        raise ValueError(f"{img_name} is not a valid mrc or tif file")
