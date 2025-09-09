from __future__ import annotations
from typing import Optional
from pydantic import Field
from datamodels import ConfiguredBaseModel


class CTFMetadata(ConfiguredBaseModel):
    """
    A set of CTF patameters for an image.
    """

    defocus_u: Optional[float] = Field(
        default=None,
        description="""Estimated defocus U for this image in Angstrom, underfocus positive.""",
    )
    defocus_v: Optional[float] = Field(
        default=None,
        description="""Estimated defocus V for this image in Angstrom, underfocus positive.""",
    )
    defocus_angle: Optional[float] = Field(
        default=None, description="""Estimated angle of astigmatism."""
    )
    phase_shift: Optional[float] = Field(
        default=None,
        description="""Phase shift value produced by the usage of a phase plate.""",
    )
    defocus_handedness: Optional[int] = Field(
        default=-1,
        description="""It is the handedness of the tilt geometry and it is used to describe 
        whether the focus increases or decreases as a function of Z distance.""",
    )


CTFMetadata.model_rebuild()
