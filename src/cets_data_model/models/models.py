from enum import Enum
from typing import Any, Optional, Union, Annotated, Literal, TypeAlias
from pydantic import BaseModel, ConfigDict, Field, RootModel


metamodel_version = "None"
version = "0.0.1"


# -----------------------------------------------------------------------------
# Base configuration
# -----------------------------------------------------------------------------
class ConfiguredBaseModel(BaseModel):
    # Global Pydantic v2 config used across all models.
    # - extra='forbid' keeps schemas strict (unknown fields raise validation errors)
    # - use_enum_values=True ensures enums are serialized as their raw values (e.g., "affine")
    model_config = ConfigDict(
        validate_assignment=True,
        validate_default=True,
        extra="forbid",
        arbitrary_types_allowed=True,
        use_enum_values=True,
        strict=False,
    )


# -----------------------------------------------------------------------------
# Type Aliases (using Annotated for validation)
# -----------------------------------------------------------------------------
# Alias for vectors
Vector2D: TypeAlias = Annotated[list[float], Field(min_length=2, max_length=2)]
Vector3D: TypeAlias = Annotated[list[float], Field(min_length=3, max_length=3)]

# Alias for matrices
Matrix2x2: TypeAlias = Annotated[list[Vector2D], Field(min_length=2, max_length=2)]
Matrix3x3: TypeAlias = Annotated[list[Vector3D], Field(min_length=3, max_length=3)]


# -----------------------------------------------------------------------------
# LinkML meta wrapper (unchanged)
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------
class AxisType(str, Enum):
    """The type of axis."""

    space = "space"
    """A spatial axis."""
    array = "array"
    """An array axis."""


class TransformationType(str, Enum):
    """Supported transformation types."""

    identity = "identity"
    """The identity transformation."""
    mapAxis = "mapAxis"
    """Axis permutation transformation."""
    translation = "translation"
    """A translation transformation."""
    scale = "scale"
    """A scaling transformation."""
    affine = "affine"
    """An affine transformation."""
    sequence = "sequence"
    """A sequence of transformations."""


# -----------------------------------------------------------------------------
# Core image models
# -----------------------------------------------------------------------------
class Image2D(ConfiguredBaseModel):
    """A 2D image."""

    width: Optional[int] = Field(
        default=None, description="The width of the image (x-axis) in pixels"
    )
    height: Optional[int] = Field(
        default=None, description="The height of the image (y-axis) in pixels"
    )
    coordinate_systems: Optional[list["CoordinateSystem"]] = Field(
        default=None, description="Named coordinate systems for this entity"
    )
    # IMPORTANT: use the discriminated union alias "Transformation" instead of the base class
    coordinate_transformations: Optional[list["Transformation"]] = Field(
        default=None, description="Named coordinate systems for this entity"
    )


class Image3D(ConfiguredBaseModel):
    """A 3D image."""

    width: Optional[int] = Field(
        default=None, description="The width of the image (x-axis) in pixels"
    )
    height: Optional[int] = Field(
        default=None, description="The height of the image (y-axis) in pixels"
    )
    depth: Optional[int] = Field(
        default=None, description="The depth of the image (z-axis) in pixels"
    )
    coordinate_systems: Optional[list["CoordinateSystem"]] = Field(
        default=None, description="Named coordinate systems for this entity"
    )
    # IMPORTANT: use the discriminated union alias "Transformation"
    coordinate_transformations: Optional[list["Transformation"]] = Field(
        default=None, description="Named coordinate systems for this entity"
    )


class ImageStack2D(ConfiguredBaseModel):
    """A stack of 2D images."""

    images: Optional[list[Image2D]] = Field(
        default=None, description="The images in the stack"
    )


class ImageStack3D(ConfiguredBaseModel):
    """A stack of 3D images."""

    images: Optional[list[Image3D]] = Field(
        default=None, description="The images in the stack"
    )


# -----------------------------------------------------------------------------
# Coordinate systems
# -----------------------------------------------------------------------------
class Axis(ConfiguredBaseModel):
    """An axis in a coordinate system."""

    name: str = Field(default=...)
    axis_unit: Optional[str] = Field(default=None)
    axis_type: Optional[str] = Field(default=None)


class CoordinateSystem(ConfiguredBaseModel):
    """A coordinate system."""

    name: str = Field(default=..., description="The name of the coordinate system")
    axes: list[Axis] = Field(
        default=..., description="The axes of the coordinate system"
    )


# -----------------------------------------------------------------------------
# Transformations
# -----------------------------------------------------------------------------
class CoordinateTransformation(ConfiguredBaseModel):
    """Base class for coordinate transformations."""

    name: Optional[str] = Field(
        default=None, description="The name of the coordinate transformation"
    )
    input: Optional[str] = Field(
        default=None, description="The source coordinate system name"
    )
    output: Optional[str] = Field(
        default=None, description="The target coordinate system name"
    )


class Identity(CoordinateTransformation):
    """The identity transformation."""

    # Literal ensures discriminated union selection by "type"
    type: Literal["identity"] = Field(
        default="identity", description="The type of transformation"
    )


class AxisNameMapping(ConfiguredBaseModel):
    """Axis name to Axis name mapping."""

    axis1_name: Optional[str] = Field(
        default=None, description="The type of transformation"
    )
    axis2_name: Optional[str] = Field(
        default=None, description="The mapping of the axis names"
    )


class MapAxis(CoordinateTransformation):
    """Axis permutation transformation."""

    type: Literal["mapAxis"] = Field(
        default="mapAxis", description="The type of transformation"
    )
    mapAxis: Optional[list[AxisNameMapping]] = Field(
        default=None, description="The permutation of the axes"
    )


class Translation(CoordinateTransformation):
    """A translation transformation."""

    type: Literal["translation"] = Field(
        default="translation", description="The type of transformation"
    )
    translation: Optional[list[float]] = Field(
        default=None, description="The translation vector"
    )


class Scale(CoordinateTransformation):
    """A scaling transformation."""

    type: Literal["scale"] = Field(
        default="scale", description="The type of transformation"
    )
    scale: Optional[list[float]] = Field(default=None, description="The scaling vector")


class Affine(CoordinateTransformation):
    """An affine transformation (3x3 matrix)."""

    type: Literal["affine"] = Field(
        default="affine", description="The type of transformation"
    )
    affine: Optional[Matrix3x3] = Field(default=None, description="The affine matrix")


class Sequence(CoordinateTransformation):
    """A sequence (pipeline) of transformations."""

    type: Literal["sequence"] = Field(
        default="sequence", description="The type of transformation"
    )
    # IMPORTANT: allow nested discriminated union, not the base class
    sequence: Optional[list["Transformation"]] = Field(
        default=None, description="The sequence of transformations"
    )


# -----------------------------------------------------------------------------
# Discriminated union over all transformation subtypes
# -----------------------------------------------------------------------------
Transformation = Annotated[
    Union[
        Affine,
        Identity,
        MapAxis,
        Translation,
        Scale,
        Sequence,
    ],
    Field(discriminator="type"),
]


class ProjectionAlignment(Sequence):
    """The tomographic alignment for a single projection."""

    # No new fields are added; it inherits everything from Sequence.
    # This class exists for semantic clarity in the model.
    pass


# -----------------------------------------------------------------------------
# Alignment and CTF metadata
# -----------------------------------------------------------------------------
class Alignment(ConfiguredBaseModel):
    """The tomographic alignment for a tilt series."""

    projection_alignments: Optional[list[ProjectionAlignment]] = Field(
        default=None, description="alignment for a specific projection"
    )


class CTFMetadata(ConfiguredBaseModel):
    """A set of CTF parameters for an image."""

    defocus_u: Optional[float] = Field(
        default=None,
        description="Estimated defocus U for this image in Angstrom, underfocus positive.",
    )
    defocus_v: Optional[float] = Field(
        default=None,
        description="Estimated defocus V for this image in Angstrom, underfocus positive.",
    )
    defocus_angle: Optional[float] = Field(
        default=None, description="Estimated angle of astigmatism."
    )
    phase_shift: Optional[float] = Field(
        default=None,
        description="Phase shift value produced by the usage of a phase plate.",
    )
    defocus_handedness: Optional[int] = Field(
        default=-1,
        description=(
            "It is the handedness of the tilt geometry and it is used to describe "
            "whether the focus increases or decreases as a function of Z distance."
        ),
    )


class AcquisitionMetadataMixin(ConfiguredBaseModel):
    """Metadata concerning the acquisition process."""

    nominal_tilt_angle: Optional[float] = Field(
        default=None, description="The tilt angle reported by the microscope"
    )
    accumulated_dose: Optional[float] = Field(
        default=None, description="The pre-exposure up to this image in e-/A^2"
    )
    ctf_metadata: Optional[CTFMetadata] = Field(
        default=None, description="A set of CTF parameters for an image."
    )


# -----------------------------------------------------------------------------
# File-like models
# -----------------------------------------------------------------------------
class GainFile(Image2D):
    """A gain reference file."""

    path: Optional[str] = Field(default=None, description="Path to a file.")


class DefectFile(Image2D):
    """A detector defect file."""

    path: Optional[str] = Field(default=None, description="Path to a file.")


# -----------------------------------------------------------------------------
# Movie and projection images
# -----------------------------------------------------------------------------
class MovieFrame(AcquisitionMetadataMixin, Image2D):
    """An individual movie frame."""

    path: Optional[str] = Field(default=None, description="Path to a file.")
    section: Optional[str] = Field(
        default=None,
        description="0-based section index to the entity inside a stack.",
    )


class MovieStack(ConfiguredBaseModel):
    """A stack of movie frames."""

    images: Optional[list[MovieFrame]] = Field(
        default=None, description="The movie frames in the stack"
    )
    path: Optional[str] = Field(default=None)


class ProjectionImage(AcquisitionMetadataMixin, Image2D):
    """A projection image."""

    path: Optional[str] = Field(default=None, description="Path to a file.")
    section: Optional[int] = Field(
        default=None,
        description="0-based section index to the entity inside a stack.",
    )


class TiltImage(ProjectionImage):
    """A projection image that belongs to a tilt-series."""

    ts_id: Optional[str] = Field(
        default=None,
        description=(
            "Identifier of the tilt-series, normally the base name of the stack file."
        ),
    )
    acq_order: Optional[int] = Field(
        default=None, description="0-based acquisition order."
    )
    pixel_size: Optional[float] = Field(
        default=None, description="Sampling rate in angstroms / pixel"
    )
    ctf_corrected: Optional[bool] = Field(
        default=None,
        description=(
            "Flag to indicate if the tilt-series was reconstructed "
            "from a tilt-series with the ctf corrected."
        ),
    )
    even_path: Optional[str] = Field(
        default=None, description="Path of the even tilt-series file."
    )
    odd_path: Optional[str] = Field(
        default=None, description="Path of the odd tilt-series file."
    )


class MovieStackSeries(ConfiguredBaseModel):
    """A group of movie stacks that belong to a single tilt series."""

    stacks: Optional[list[MovieStack]] = Field(
        default=None, description="The movie stacks."
    )


class TiltSeries(ConfiguredBaseModel):
    """A stack of projection images."""

    images: Optional[list[ProjectionImage]] = Field(
        default=None, description="The projections in the stack"
    )
    path: Optional[str] = Field(default=None)


class SubProjectionImage(ProjectionImage):
    """A cropped projection image."""

    particle_index: Optional[int] = Field(
        default=None, description="Index of a particle inside a tomogram."
    )


# -----------------------------------------------------------------------------
# 3D volumes and maps
# -----------------------------------------------------------------------------
class Tomogram(Image3D):
    """A 3D tomogram."""

    path: Optional[str] = Field(default=None, description="Path to a file.")
    voxel_size: Optional[float] = Field(
        default=None, description="Sampling rate in angstroms / voxel"
    )
    ctf_corrected: Optional[bool] = Field(
        default=None,
        description=(
            "Flag to indicate if the tomogram was reconstructed "
            "from a tilt-series with the ctf corrected."
        ),
    )
    even_path: Optional[str] = Field(
        default=None, description="Path of the even tomogram file."
    )
    odd_path: Optional[str] = Field(
        default=None, description="Path of the odd tomogram file."
    )


class ParticleMap(Image3D):
    """A 3D particle density map."""

    path: Optional[str] = Field(default=None, description="Path to a file.")


# -----------------------------------------------------------------------------
# Annotations and coordinate metadata mixin
# -----------------------------------------------------------------------------
class CoordMetaMixin(ConfiguredBaseModel):
    """Coordinate system mixin for annotations."""

    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=None, description="Named coordinate systems for this entity"
    )
    coordinate_transformations: Optional[list[Transformation]] = Field(
        default=None, description="Named coordinate systems for this entity"
    )


class Annotation(ConfiguredBaseModel):
    """A primitive annotation."""

    path: Optional[str] = Field(default=None, description="Path to a file.")


class SegmentationMask2D(Annotation, Image2D):
    """An annotation image with categorical labels (2D)."""

    pass


class SegmentationMask3D(Annotation, Image3D):
    """An annotation volume with categorical labels (3D)."""

    pass


class ProbabilityMap2D(Annotation, Image2D):
    """An annotation image with real-valued labels (2D)."""

    pass


class ProbabilityMap3D(Annotation, Image3D):
    """An annotation volume with real-valued labels (3D)."""

    pass


class PointSet2D(Annotation, CoordMetaMixin):
    """A set of 2D point annotations."""

    origin2D: Optional[Annotated[list[Vector2D], Field(min_length=1)]] = Field(
        default=None, description="Location on a 2D image (Nx2)."
    )


class PointSet3D(Annotation, CoordMetaMixin):
    """A set of 3D point annotations."""

    origin3D: Optional[Annotated[list[Vector3D], Field(min_length=1)]] = Field(
        default=None, description="Location on a 3D image (Nx3)."
    )


class PointVectorSet2D(Annotation, CoordMetaMixin):
    """A set of 2D points with an associated direction vector."""

    origin2D: Optional[Annotated[list[Vector2D], Field(min_length=1)]] = Field(
        default=None, description="Location on a 2D image (Nx2)."
    )
    vector2D: Optional[Annotated[list[Vector2D], Field(min_length=1)]] = Field(
        default=None,
        description="Orientation vector associated with a point on a 2D image (Nx2).",
    )


class PointVectorSet3D(Annotation, CoordMetaMixin):
    """A set of 3D points with an associated direction vector."""

    origin3D: Optional[Annotated[list[Vector3D], Field(min_length=1)]] = Field(
        default=None, description="Location on a 3D image (Nx3)."
    )
    vector3D: Optional[Annotated[list[Vector3D], Field(min_length=1)]] = Field(
        default=None,
        description="Orientation vector associated with a point on a 3D image (Nx3).",
    )


class PointMatrixSet2D(Annotation, CoordMetaMixin):
    """A set of 2D points with an associated rotation matrix."""

    origin2D: Optional[Annotated[list[Vector2D], Field(min_length=1)]] = Field(
        default=None, description="Location on a 2D image (Nx2)."
    )
    matrix2D: Optional[Annotated[list[Matrix2x2], Field(min_length=1)]] = Field(
        default=None,
        description="Rotation matrix associated with a point on a 2D image (Nx2x2).",
    )


class PointMatrixSet3D(Annotation, CoordMetaMixin):
    """A set of 3D points with an associated rotation matrix."""

    origin3D: Optional[Annotated[list[Vector3D], Field(min_length=1)]] = Field(
        default=None, description="Location on a 3D image (Nx3)."
    )
    matrix3D: Optional[Annotated[list[Matrix3x3], Field(min_length=1)]] = Field(
        default=None,
        description="Rotation matrix associated with a point on a 3D image (Nx3x3).",
    )


class TriMesh(Annotation, CoordMetaMixin):
    """A mesh annotation."""

    pass


# -----------------------------------------------------------------------------
# Region, averaging, and dataset
# -----------------------------------------------------------------------------
class Region(ConfiguredBaseModel):
    """
    Raw data (movie stacks) and derived data (tilt series, tomograms, annotations)
    from a single region of a specimen.
    """

    movie_stack_collections: Optional[list["MovieStackCollection"]] = Field(
        default=None, description="The movie stack"
    )
    tilt_series: Optional[list[TiltSeries]] = Field(
        default=None, description="The tilt series"
    )
    alignments: Optional[list[Alignment]] = Field(
        default=None, description="The alignments"
    )
    tomograms: Optional[list[Tomogram]] = Field(
        default=None, description="The tomograms"
    )
    annotations: Optional[list[Annotation]] = Field(
        default=None, description="The annotations for this region"
    )


class Average(ConfiguredBaseModel):
    """A particle averaging experiment."""

    name: Optional[str] = Field(
        default=None, description="The name of the averaging experiment."
    )
    particle_maps: Optional[list[ParticleMap]] = Field(
        default=None, description="The particle maps"
    )
    annotations: Optional[list[Annotation]] = Field(
        default=None, description="The annotations"
    )


class MovieStackCollection(ConfiguredBaseModel):
    """A collection of movie stacks using the same gain and defect files."""

    movie_stacks: Optional[list[MovieStackSeries]] = Field(
        default=None, description="The movie stacks in the collection"
    )
    gain_file: Optional[GainFile] = Field(
        default=None, description="The gain file for the movie stacks"
    )
    defect_file: Optional[DefectFile] = Field(
        default=None, description="The defect file for the movie stacks"
    )


class Dataset(ConfiguredBaseModel):
    """A dataset."""

    name: Optional[str] = Field(default=None, description="The name of the dataset")
    regions: Optional[list[Region]] = Field(
        default=None, description="The regions in the dataset"
    )
    averages: Optional[list[Average]] = Field(
        default=None, description="The averages in the dataset"
    )


# -----------------------------------------------------------------------------
# Model rebuild (resolves forward references)
# -----------------------------------------------------------------------------
Image2D.model_rebuild()
Image3D.model_rebuild()
ImageStack2D.model_rebuild()
ImageStack3D.model_rebuild()
Axis.model_rebuild()
CoordinateSystem.model_rebuild()
CoordinateTransformation.model_rebuild()
Identity.model_rebuild()
AxisNameMapping.model_rebuild()
MapAxis.model_rebuild()
Translation.model_rebuild()
Scale.model_rebuild()
Affine.model_rebuild()
Sequence.model_rebuild()
ProjectionAlignment.model_rebuild()
Alignment.model_rebuild()
CTFMetadata.model_rebuild()
AcquisitionMetadataMixin.model_rebuild()
GainFile.model_rebuild()
DefectFile.model_rebuild()
MovieFrame.model_rebuild()
MovieStack.model_rebuild()
ProjectionImage.model_rebuild()
TiltImage.model_rebuild()
TiltSeries.model_rebuild()
MovieStackSeries.model_rebuild()
SubProjectionImage.model_rebuild()
Tomogram.model_rebuild()
ParticleMap.model_rebuild()
CoordMetaMixin.model_rebuild()
Annotation.model_rebuild()
SegmentationMask2D.model_rebuild()
SegmentationMask3D.model_rebuild()
ProbabilityMap2D.model_rebuild()
ProbabilityMap3D.model_rebuild()
PointSet2D.model_rebuild()
PointSet3D.model_rebuild()
PointVectorSet2D.model_rebuild()
PointVectorSet3D.model_rebuild()
PointMatrixSet2D.model_rebuild()
PointMatrixSet3D.model_rebuild()
TriMesh.model_rebuild()
Region.model_rebuild()
Average.model_rebuild()
MovieStackCollection.model_rebuild()
Dataset.model_rebuild()
