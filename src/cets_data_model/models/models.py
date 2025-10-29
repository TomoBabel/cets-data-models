from enum import Enum
from typing import Any, Optional, Union, Annotated, Literal, TypeAlias
from pydantic import BaseModel, ConfigDict, Field, RootModel


metamodel_version = "None"
version = "0.0.1"


# -----------------------------------------------------------------------------
# Base configuration
# -----------------------------------------------------------------------------
class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True,
        validate_default=True,
        extra="forbid",
        arbitrary_types_allowed=True,
        use_enum_values=True,
        strict=False,
    )


# -----------------------------------------------------------------------------
# LinkML meta wrapper
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
    space = "space"
    array = "array"


class TransformationType(str, Enum):
    identity = "identity"
    mapAxis = "mapAxis"
    translation = "translation"
    scale = "scale"
    affine = "affine"
    sequence = "sequence"


class AxisUnit(str, Enum):
    pixel = "pixel/voxel"
    angstrom = "angstrom"


class SpaceAxis(str, Enum):
    X = "X"
    Y = "Y"
    Z = "Z"
    XY = "XY"
    XYZ = "XYZ"
    # The rest of combinations?


# -----------------------------------------------------------------------------
# Type Aliases (using Annotated for validation)
# -----------------------------------------------------------------------------
Vector2D: TypeAlias = Annotated[list[float], Field(min_length=2, max_length=2)]
Vector3D: TypeAlias = Annotated[list[float], Field(min_length=3, max_length=3)]
Matrix2x2: TypeAlias = Annotated[list[Vector2D], Field(min_length=2, max_length=2)]
Matrix3x3: TypeAlias = Annotated[list[Vector3D], Field(min_length=3, max_length=3)]


# -----------------------------------------------------------------------------
# Coordinate systems
# -----------------------------------------------------------------------------
class Axis(ConfiguredBaseModel):
    name: str
    axis_unit: Optional[AxisUnit] = None
    axis_type: Optional[AxisType] = None


class CoordinateSystem(ConfiguredBaseModel):
    name: str = Field(..., description="The name of the coordinate system")
    axes: list[Axis] = Field(..., description="The axes of the coordinate system")


# -----------------------------------------------------------------------------
# Transformations
# -----------------------------------------------------------------------------
class CoordinateTransformation(ConfiguredBaseModel):
    name: Optional[str] = Field(
        None, description="The name of the coordinate transformation"
    )
    input: Optional[str] = Field(None, description="The source coordinate system name")
    output: Optional[str] = Field(None, description="The target coordinate system name")


class Identity(CoordinateTransformation):
    type: Literal["identity"] = Field(
        "identity", description="The type of transformation"
    )


class AxisNameMapping(ConfiguredBaseModel):
    axis1_name: Optional[str] = Field(None, description="The type of transformation")
    axis2_name: Optional[str] = Field(None, description="The mapping of the axis names")


class MapAxis(CoordinateTransformation):
    type: Literal["mapAxis"] = Field(
        "mapAxis", description="The type of transformation"
    )
    mapAxis: Optional[list[AxisNameMapping]] = Field(
        None, description="The permutation of the axes"
    )


class Translation(CoordinateTransformation):
    type: Literal["translation"] = Field(
        "translation", description="The type of transformation"
    )
    translation: Optional[Vector3D] = Field(None, description="The translation vector")


class Scale(CoordinateTransformation):
    type: Literal["scale"] = Field("scale", description="The type of transformation")
    scale: Optional[list[float]] = Field(None, description="The scaling vector")


class Affine(CoordinateTransformation):
    type: Literal["affine"] = Field("affine", description="The type of transformation")
    affine: Optional[Matrix3x3] = Field(None, description="The affine matrix")


class Sequence(CoordinateTransformation):
    type: Literal["sequence"] = Field(
        "sequence", description="The type of transformation"
    )
    sequence: Optional[list["Transformation"]] = Field(
        None, description="The sequence of transformations"
    )


Transformation = Annotated[
    Union[Affine, Identity, MapAxis, Translation, Scale, Sequence],
    Field(discriminator="type"),
]


class ProjectionAlignment(Sequence):
    pass


# -----------------------------------------------------------------------------
# Core image models
# -----------------------------------------------------------------------------
class Image2D(ConfiguredBaseModel):
    width: Optional[int] = Field(
        None, description="The width of the image (x-axis) in pixels"
    )
    height: Optional[int] = Field(
        None, description="The height of the image (y-axis) in pixels"
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        None, description="Named coordinate systems for this entity"
    )
    coordinate_transformations: Optional[list[Transformation]] = Field(
        None, description="Named coordinate systems for this entity"
    )


class Image3D(ConfiguredBaseModel):
    width: Optional[int] = Field(
        None, description="The width of the image (x-axis) in pixels"
    )
    height: Optional[int] = Field(
        None, description="The height of the image (y-axis) in pixels"
    )
    depth: Optional[int] = Field(
        None, description="The depth of the image (z-axis) in pixels"
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        None, description="Named coordinate systems for this entity"
    )
    coordinate_transformations: Optional[list[Transformation]] = Field(
        None, description="Named coordinate systems for this entity"
    )


class ImageStack2D(ConfiguredBaseModel):
    images: Optional[list[Image2D]] = Field(None, description="The images in the stack")


class ImageStack3D(ConfiguredBaseModel):
    images: Optional[list[Image3D]] = Field(None, description="The images in the stack")


# -----------------------------------------------------------------------------
# Alignment and CTF metadata
# -----------------------------------------------------------------------------
class Alignment(ConfiguredBaseModel):
    projection_alignments: Optional[list[ProjectionAlignment]] = Field(
        None, description="alignment for a specific projection"
    )


class CTFMetadata(ConfiguredBaseModel):
    defocus_u: Optional[float] = Field(
        None,
        description="Estimated defocus U for this image in Angstrom, underfocus positive.",
    )
    defocus_v: Optional[float] = Field(
        None,
        description="Estimated defocus V for this image in Angstrom, underfocus positive.",
    )
    defocus_angle: Optional[float] = Field(
        None, description="Estimated angle of astigmatism."
    )
    phase_shift: Optional[float] = Field(
        None, description="Phase shift value produced by the usage of a phase plate."
    )
    defocus_handedness: Optional[int] = Field(
        -1,
        description="It is the handedness of the tilt geometry and it is used to describe whether the focus increases or decreases as a function of Z distance.",
    )
    acquisition_order: Optional[int] = Field(
        None, description="0-based acquisition order."
    )


class AcquisitionMetadataMixin(ConfiguredBaseModel):
    nominal_tilt_angle: Optional[float] = Field(
        None, description="The tilt angle reported by the microscope"
    )
    accumulated_dose: Optional[float] = Field(
        None, description="The pre-exposure up to this image in e-/A^2"
    )
    ctf_metadata: Optional[CTFMetadata] = Field(
        None, description="A set of CTF parameters for an image."
    )
    acquisition_order: Optional[int] = Field(
        None, description="0-based acquisition order."
    )


# -----------------------------------------------------------------------------
# File-like models
# -----------------------------------------------------------------------------
class GainFile(Image2D):
    path: Optional[str] = Field(None, description="Path to a file.")


class DefectFile(Image2D):
    path: Optional[str] = Field(None, description="Path to a file.")


# -----------------------------------------------------------------------------
# Movie and projection images
# -----------------------------------------------------------------------------
class MovieFrame(AcquisitionMetadataMixin, Image2D):
    path: Optional[str] = Field(None, description="Path to a file.")
    section: Optional[str] = Field(
        None, description="0-based section index to the entity inside a stack."
    )


class MovieStack(ConfiguredBaseModel):
    images: Optional[list[MovieFrame]] = Field(
        None, description="The movie frames in the stack"
    )
    path: Optional[str] = None


class _BaseProjectionImage(AcquisitionMetadataMixin, Image2D):
    """Base class for different projection image types, not for direct use."""

    path: Optional[str] = Field(None, description="Path to a file.")
    section: Optional[int] = Field(
        None, description="0-based section index to the entity inside a stack."
    )


class ProjectionImage(_BaseProjectionImage):
    """A generic projection image."""

    type: Literal["projection"] = Field(
        "projection", description="The type of projection image."
    )


class TiltImage(_BaseProjectionImage):
    """A projection image that belongs to a tilt-series."""

    type: Literal["tilt_image"] = Field(
        "tilt_image", description="The type of projection image."
    )
    ts_id: Optional[str] = Field(
        None,
        description="Identifier of the tilt-series, normally the base name of the stack file.",
    )
    even_path: Optional[str] = Field(
        None, description="Path of the even tilt-series file."
    )
    odd_path: Optional[str] = Field(
        None, description="Path of the odd tilt-series file."
    )


class SubProjectionImage(_BaseProjectionImage):
    """A cropped projection image."""

    type: Literal["subprojection"] = Field(
        "subprojection", description="The type of projection image."
    )
    particle_index: Optional[int] = Field(
        None, description="Index of a particle inside a tomogram."
    )


AnyProjectionImage = Annotated[
    Union[TiltImage, SubProjectionImage, ProjectionImage],
    Field(discriminator="type"),
]


class MovieStackSeries(ConfiguredBaseModel):
    stacks: Optional[list[MovieStack]] = Field(None, description="The movie stacks.")


class TiltSeries(ConfiguredBaseModel):
    path: Optional[str] = Field(None, description="Path to the stack file.")
    ts_id: Optional[str] = Field(
        None,
        description="Identifier of the tilt-series, normally the base name of the stack file.",
    )
    ctf_corrected: Optional[bool] = Field(
        None,
        description="Flag to indicate if the tilt-series was reconstructed from a tilt-series with the ctf corrected.",
    )
    images: Optional[list[AnyProjectionImage]] = Field(
        None, description="The projections in the stack"
    )


# -----------------------------------------------------------------------------
# 3D volumes and maps
# -----------------------------------------------------------------------------
class Tomogram(Image3D):
    path: Optional[str] = Field(None, description="Path to a file.")
    tomo_id: Optional[str] = Field(
        None,
        description="Identifier of the tomogram, normally the base name of the tomogram file.",
    )
    ctf_corrected: Optional[bool] = Field(
        None,
        description="Flag to indicate if the tomogram was reconstructed from a tilt-series with the ctf corrected.",
    )
    even_path: Optional[str] = Field(
        None, description="Path of the even tomogram file."
    )
    odd_path: Optional[str] = Field(None, description="Path of the odd tomogram file.")


class ParticleMap(Image3D):
    path: Optional[str] = Field(None, description="Path to a file.")


# -----------------------------------------------------------------------------
# Annotations and coordinate metadata mixin
# -----------------------------------------------------------------------------
class CoordMetaMixin(ConfiguredBaseModel):
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        None, description="Named coordinate systems for this entity"
    )
    coordinate_transformations: Optional[list[Transformation]] = Field(
        None, description="Named coordinate systems for this entity"
    )


class _BaseAnnotation(ConfiguredBaseModel):
    """Base class for annotations, not for direct use."""

    path: Optional[str] = Field(None, description="Path to a file.")


class Annotation(_BaseAnnotation):
    """A primitive annotation."""

    type: Literal["annotation"] = Field(
        "annotation", description="The type of annotation."
    )


class SegmentationMask2D(_BaseAnnotation, Image2D):
    type: Literal["segmentation_mask_2d"] = Field("segmentation_mask_2d")


class SegmentationMask3D(_BaseAnnotation, Image3D):
    type: Literal["segmentation_mask_3d"] = Field("segmentation_mask_3d")


class ProbabilityMap2D(_BaseAnnotation, Image2D):
    type: Literal["probability_map_2d"] = Field("probability_map_2d")


class ProbabilityMap3D(_BaseAnnotation, Image3D):
    type: Literal["probability_map_3d"] = Field("probability_map_3d")


class PointSet2D(_BaseAnnotation, CoordMetaMixin):
    type: Literal["point_set_2d"] = Field("point_set_2d")
    origin2D: Optional[Annotated[list[Vector2D], Field(min_length=1)]] = Field(
        None, description="Location on a 2D image (Nx2)."
    )


class PointSet3D(_BaseAnnotation, CoordMetaMixin):
    type: Literal["point_set_3d"] = Field("point_set_3d")
    origin3D: Optional[Annotated[list[Vector3D], Field(min_length=1)]] = Field(
        None, description="Location on a 3D image (Nx3)."
    )


class PointVectorSet2D(_BaseAnnotation, CoordMetaMixin):
    type: Literal["point_vector_set_2d"] = Field("point_vector_set_2d")
    origin2D: Optional[Annotated[list[Vector2D], Field(min_length=1)]] = Field(
        None, description="Location on a 2D image (Nx2)."
    )
    vector2D: Optional[Annotated[list[Vector2D], Field(min_length=1)]] = Field(
        None,
        description="Orientation vector associated with a point on a 2D image (Nx2).",
    )


class PointVectorSet3D(_BaseAnnotation, CoordMetaMixin):
    type: Literal["point_vector_set_3d"] = Field("point_vector_set_3d")
    origin3D: Optional[Annotated[list[Vector3D], Field(min_length=1)]] = Field(
        None, description="Location on a 3D image (Nx3)."
    )
    vector3D: Optional[Annotated[list[Vector3D], Field(min_length=1)]] = Field(
        None,
        description="Orientation vector associated with a point on a 3D image (Nx3).",
    )


class PointMatrixSet2D(_BaseAnnotation, CoordMetaMixin):
    type: Literal["point_matrix_set_2d"] = Field("point_matrix_set_2d")
    origin2D: Optional[Annotated[list[Vector2D], Field(min_length=1)]] = Field(
        None, description="Location on a 2D image (Nx2)."
    )
    matrix2D: Optional[Annotated[list[Matrix2x2], Field(min_length=1)]] = Field(
        None,
        description="Rotation matrix associated with a point on a 2D image (Nx2x2).",
    )


class PointMatrixSet3D(_BaseAnnotation, CoordMetaMixin):
    type: Literal["point_matrix_set_3d"] = Field("point_matrix_set_3d")
    origin3D: Optional[Annotated[list[Vector3D], Field(min_length=1)]] = Field(
        None, description="Location on a 3D image (Nx3)."
    )
    matrix3D: Optional[Annotated[list[Matrix3x3], Field(min_length=1)]] = Field(
        None,
        description="Rotation matrix associated with a point on a 3D image (Nx3x3).",
    )


class TriMesh(_BaseAnnotation, CoordMetaMixin):
    type: Literal["trimesh"] = Field("trimesh")


AnyAnnotation = Annotated[
    Union[
        SegmentationMask2D,
        SegmentationMask3D,
        ProbabilityMap2D,
        ProbabilityMap3D,
        PointSet2D,
        PointSet3D,
        PointVectorSet2D,
        PointVectorSet3D,
        PointMatrixSet2D,
        PointMatrixSet3D,
        TriMesh,
        Annotation,
    ],
    Field(discriminator="type"),
]


# -----------------------------------------------------------------------------
# Region, averaging, and dataset
# -----------------------------------------------------------------------------
class MovieStackCollection(ConfiguredBaseModel):
    movie_stacks: Optional[list[MovieStackSeries]] = Field(
        None, description="The movie stacks in the collection"
    )
    gain_file: Optional[GainFile] = Field(
        None, description="The gain file for the movie stacks"
    )
    defect_file: Optional[DefectFile] = Field(
        None, description="The defect file for the movie stacks"
    )


class Region(ConfiguredBaseModel):
    movie_stack_collections: Optional[list[MovieStackCollection]] = Field(
        None, description="The movie stack"
    )
    tilt_series: Optional[list[TiltSeries]] = Field(None, description="The tilt series")
    alignments: Optional[list[Alignment]] = Field(None, description="The alignments")
    tomograms: Optional[list[Tomogram]] = Field(None, description="The tomograms")
    annotations: Optional[list[AnyAnnotation]] = Field(
        None, description="The annotations for this region"
    )


class Average(ConfiguredBaseModel):
    name: Optional[str] = Field(
        None, description="The name of the averaging experiment."
    )
    particle_maps: Optional[list[ParticleMap]] = Field(
        None, description="The particle maps"
    )
    annotations: Optional[list[AnyAnnotation]] = Field(
        None, description="The annotations"
    )


class Dataset(ConfiguredBaseModel):
    name: Optional[str] = Field(None, description="The name of the dataset")
    regions: Optional[list[Region]] = Field(
        None, description="The regions in the dataset"
    )
    averages: Optional[list[Average]] = Field(
        None, description="The averages in the dataset"
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
_BaseProjectionImage.model_rebuild()
ProjectionImage.model_rebuild()
TiltImage.model_rebuild()
SubProjectionImage.model_rebuild()
TiltSeries.model_rebuild()
MovieStackSeries.model_rebuild()
Tomogram.model_rebuild()
ParticleMap.model_rebuild()
CoordMetaMixin.model_rebuild()
_BaseAnnotation.model_rebuild()
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
