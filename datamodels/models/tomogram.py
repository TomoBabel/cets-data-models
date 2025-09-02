from pydantic import Field
from typing import Optional

from datamodels.models.models import Image3D, CoordinateSystem, CoordinateTransformation


class Tomogram(Image3D):
    """
    A 3D tomogram.
    """

    path: Optional[str] = Field(default=None, description="""Path to a file.""")
    width: Optional[int] = Field(
        default=None, description="""The width of the image (x-axis) in pixels"""
    )
    height: Optional[int] = Field(
        default=None, description="""The height of the image (y-axis) in pixels"""
    )
    depth: Optional[int] = Field(
        default=None, description="""The depth of the image (z-axis) in pixels"""
    )
    voxel_size: Optional[float] = Field(
        default=None, description="""Sampling rate in angstroms / voxel"""
    )
    ctf_corrected: Optional[bool] = Field(
        default=None, description="""Flag to indicate if the tomogram was reconstructed 
        from a tilt-series with the ctf corrected."""
    )
    even_path: Optional[str] = Field(
        default=None, description="""Path of the even tomogram file."""
    )
    odd_path: Optional[str] = Field(
        default=None, description="""Path of the odd tomogram file."""
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=None, description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[list[CoordinateTransformation]] = Field(
        default=None, description="""Named coordinate systems for this entity"""
    )


Tomogram.model_rebuild()