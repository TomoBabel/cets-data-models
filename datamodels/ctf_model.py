from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, RootModel


metamodel_version = "None"
version = "0.0.1"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True,
        validate_default=True,
        extra="forbid",
        arbitrary_types_allowed=True,
        use_enum_values=True,
        strict=False,
    )
    pass


class LinkMLMeta(RootModel):
    root: dict[str, Any] = {}
    model_config = ConfigDict(frozen=True)

    def __getattr__(self, key: str):
        return getattr(self.root, key)

    def __getitem__(self, key: str):
        return self.root[key]

    def __setitem__(self, key: str, value):
        self.root[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self.root


linkml_meta = None


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
