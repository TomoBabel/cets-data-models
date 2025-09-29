from __future__ import annotations
from typing import Optional
from pydantic import Field
from cets_data_model.models.models import ProjectionImage


class TiltImage(ProjectionImage):
    ts_id: Optional[str] = Field(
        default=None,
        description="""Identifier of the tilt-series, normally the 
        base name of the stack file."""
    )
    acq_order: Optional[int] = Field(
        default=None,
        description="""0-based acquisition order."""
    )
    pixel_size: Optional[float] = Field(
        default=None,
        description="""Sampling rate in angstroms / pixel"""
    )
    ctf_corrected: Optional[bool] = Field(
        default=None,
        description="""Flag to indicate if the tilt-series was reconstructed 
        from a tilt-series with the ctf corrected.""",
    )
    even_path: Optional[str] = Field(
        default=None,
        description="""Path of the even tilt-series file."""
    )
    odd_path: Optional[str] = Field(
        default=None,
        description="""Path of the odd tilt-series file."""
    )