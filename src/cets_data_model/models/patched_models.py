from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional, Union, Annotated, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, RootModel


# Type aliases
Vector2D: TypeAlias = Annotated[list[float], Field(min_length=2, max_length=2)]
Vector3D: TypeAlias = Annotated[list[float], Field(min_length=3, max_length=3)]
Matrix2x2: TypeAlias = Annotated[list[Vector2D], Field(min_length=2, max_length=2)]
Matrix3x3: TypeAlias = Annotated[list[Vector3D], Field(min_length=3, max_length=3)]


metamodel_version = "None"
version = "0.0.1"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias=True,
        validate_by_name=True,
        validate_assignment=True,
        validate_default=True,
        extra="forbid",
        arbitrary_types_allowed=True,
        use_enum_values=True,
        strict=False,
    )


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


class AxisType(str, Enum):
    """
    The type of axis
    """

    space = "space"
    """
    A spatial axis
    """
    array = "array"
    """
    An array axis
    """


class TransformationType(str, Enum):
    identity = "identity"
    """
    The identity transformation.
    """
    map_axis = "map_axis"
    """
    Axis permutation transformation
    """
    translation = "translation"
    """
    A translation transformation.
    """
    scale = "scale"
    """
    A scaling transformation.
    """
    affine = "affine"
    """
    An affine transformation.
    """
    sequence = "sequence"
    """
    A sequence of transformations.
    """
    projection_alignment = "projection_alignment"
    """
    A sequence specific to projection alignments.
    """


class AnnotationType(str, Enum):
    segmentation_mask_2D = "segmentation_mask_2D"
    """
    An annotation image with categorical labels.
    """
    segmentation_mask_3D = "segmentation_mask_3D"
    """
    An annotation volume with categorical labels.
    """
    probability_map_2D = "probability_map_2D"
    """
    An annotation image with real-valued labels.
    """
    probability_map_3D = "probability_map_3D"
    """
    An annotation volume with real-valued labels.
    """
    point_set_2D = "point_set_2D"
    """
    A set of 2D point annotations.
    """
    point_set_3D = "point_set_3D"
    """
    A set of 3D point annotations.
    """
    point_vector_set_2D = "point_vector_set_2D"
    """
    A set of 2D points with an associated direction vector.
    """
    point_vector_set_3D = "point_vector_set_3D"
    """
    A set of 3D points with an associated direction vector.
    """
    point_matrix_set_2D = "point_matrix_set_2D"
    """
    A set of 2D points with an associated rotation matrix.
    """
    point_matrix_set_3D = "point_matrix_set_3D"
    """
    A set of 3D points with an associated rotation matrix.
    """
    tri_mesh = "tri_mesh"
    """
    A mesh annotation.
    """


class Image2D(ConfiguredBaseModel):
    """
    A 2D image.
    """

    width: Optional[int] = Field(
        default=None, description="""The width of the image (x-axis) in pixels"""
    )
    height: Optional[int] = Field(
        default=None, description="""The height of the image (y-axis) in pixels"""
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )


class Image3D(ConfiguredBaseModel):
    """
    A 3D image.
    """

    width: Optional[int] = Field(
        default=None, description="""The width of the image (x-axis) in pixels"""
    )
    height: Optional[int] = Field(
        default=None, description="""The height of the image (y-axis) in pixels"""
    )
    depth: Optional[int] = Field(
        default=None, description="""The depth of the image (z-axis) in pixels"""
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )


class ImageStack2D(ConfiguredBaseModel):
    """
    A stack of 2D images.
    """

    images: Optional[list[Image2D]] = Field(
        default=[], description="""The images in the stack"""
    )


class ImageStack3D(ConfiguredBaseModel):
    """
    A stack of 3D images.
    """

    images: Optional[list[Image3D]] = Field(
        default=[], description="""The images in the stack"""
    )


class Axis(ConfiguredBaseModel):
    """
    An axis in a coordinate system
    """

    name: Optional[str] = Field(
        default=None,
        description="""A name, or title, human-readable, for this entity""",
    )
    axis_unit: Optional[str] = Field(
        default="angstrom", description="""The unit of the axis"""
    )
    axis_type: Optional[AxisType] = Field(
        default=None, description="""The type of axis"""
    )


class CoordinateSystem(ConfiguredBaseModel):
    """
    A coordinate system
    """

    name: str = Field(default=..., description="""The name of the coordinate system""")
    axes: list[Axis] = Field(
        default=..., description="""The axes of the coordinate system"""
    )


class CoordinateTransformation(ConfiguredBaseModel):
    """
    A coordinate transformation
    """

    transformation_type: TransformationType = Field(
        default=..., description="""The type of transformation."""
    )
    name: Optional[str] = Field(
        default=None,
        description="""A name, or title, human-readable, for this entity""",
    )
    input: Optional[str] = Field(
        default=None, description="""The source coordinate system name"""
    )
    output: Optional[str] = Field(
        default=None, description="""The target coordinate system name"""
    )


class Identity(CoordinateTransformation):
    """
    The identity transformation
    """

    transformation_type: Literal[TransformationType.identity] = Field(
        TransformationType.identity, description="""The type of transformation."""
    )
    name: Optional[str] = Field(
        default=None,
        description="""A name, or title, human-readable, for this entity""",
    )
    input: Optional[str] = Field(
        default=None, description="""The source coordinate system name"""
    )
    output: Optional[str] = Field(
        default=None, description="""The target coordinate system name"""
    )


class AxisNameMapping(ConfiguredBaseModel):
    """
    Axis name to Axis name mapping
    """

    axis1_name: Optional[str] = Field(
        default=None, description="""The type of transformation"""
    )
    axis2_name: Optional[str] = Field(
        default=None, description="""The mapping of the axis names"""
    )


class MapAxis(CoordinateTransformation):
    """
    Axis permutation transformation
    """

    map_axis: Optional[list[AxisNameMapping]] = Field(
        default=[], description="""The permutation of the axes"""
    )
    transformation_type: Literal[TransformationType.map_axis] = Field(
        TransformationType.map_axis, description="""The type of transformation."""
    )
    name: Optional[str] = Field(
        default=None,
        description="""A name, or title, human-readable, for this entity""",
    )
    input: Optional[str] = Field(
        default=None, description="""The source coordinate system name"""
    )
    output: Optional[str] = Field(
        default=None, description="""The target coordinate system name"""
    )


class Translation(CoordinateTransformation):
    """
    A translation transformation
    """

    translation: Optional[list[float]] = Field(
        default=[], description="""The translation vector"""
    )
    transformation_type: Literal[TransformationType.translation] = Field(
        TransformationType.translation, description="""The type of transformation."""
    )
    name: Optional[str] = Field(
        default=None,
        description="""A name, or title, human-readable, for this entity""",
    )
    input: Optional[str] = Field(
        default=None, description="""The source coordinate system name"""
    )
    output: Optional[str] = Field(
        default=None, description="""The target coordinate system name"""
    )


class Scale(CoordinateTransformation):
    """
    A scaling transformation
    """

    scale: Optional[list[float]] = Field(
        default=[], description="""The scaling vector"""
    )
    transformation_type: Literal[TransformationType.scale] = Field(
        TransformationType.scale, description="""The type of transformation."""
    )
    name: Optional[str] = Field(
        default=None,
        description="""A name, or title, human-readable, for this entity""",
    )
    input: Optional[str] = Field(
        default=None, description="""The source coordinate system name"""
    )
    output: Optional[str] = Field(
        default=None, description="""The target coordinate system name"""
    )


class Affine(CoordinateTransformation):
    """
    An affine transformation
    """

    affine: Optional[Matrix3x3] = Field(
        default=None, description="""The affine matrix"""
    )
    transformation_type: Literal[TransformationType.affine] = Field(
        TransformationType.affine, description="""The type of transformation."""
    )
    name: Optional[str] = Field(
        default=None,
        description="""A name, or title, human-readable, for this entity""",
    )
    input: Optional[str] = Field(
        default=None, description="""The source coordinate system name"""
    )
    output: Optional[str] = Field(
        default=None, description="""The target coordinate system name"""
    )


class Sequence(CoordinateTransformation):
    """
    A sequence of transformations
    """

    sequence: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(default=[], description="""The sequence of transformations""")
    transformation_type: Literal[TransformationType.sequence] = Field(
        TransformationType.sequence, description="""The type of transformation."""
    )
    name: Optional[str] = Field(
        default=None,
        description="""A name, or title, human-readable, for this entity""",
    )
    input: Optional[str] = Field(
        default=None, description="""The source coordinate system name"""
    )
    output: Optional[str] = Field(
        default=None, description="""The target coordinate system name"""
    )


class ProjectionAlignment(CoordinateTransformation):
    """
    The tomographic alignment for a single projection.
    """

    sequence: Optional[list[Union[Affine, Translation]]] = Field(
        default=[], description="""The sequence of transformations""", max_length=2
    )
    transformation_type: Literal[TransformationType.projection_alignment] = Field(
        TransformationType.projection_alignment,
        description="""The type of transformation.""",
    )
    name: Optional[str] = Field(
        default=None,
        description="""A name, or title, human-readable, for this entity""",
    )
    input: Optional[str] = Field(
        default=None, description="""The source coordinate system name"""
    )
    output: Optional[str] = Field(
        default=None, description="""The target coordinate system name"""
    )


class Alignment(ConfiguredBaseModel):
    """
    The tomographic alignment for a tilt series.
    """

    projection_alignments: Optional[list[ProjectionAlignment]] = Field(
        default=[], description="""alignment for a specific projection"""
    )


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
    defocus_handedness: Optional[int] = Field(
        default=-1,
        description="""The handedness of the tilt geometry used to describe whether the focus increases or decreases as a function of Z distance.""",
    )


class AcquisitionMetadataMixin(ConfiguredBaseModel):
    """
    Metadata concerning the acquisition process.
    """

    nominal_tilt_angle: Optional[float] = Field(
        default=None, description="""The tilt angle reported by the microscope"""
    )
    accumulated_dose: Optional[float] = Field(
        default=None, description="""The pre-exposure up to this image in e-/A^2"""
    )
    ctf_metadata: Optional[CTFMetadata] = Field(
        default=None, description="""A set of CTF patameters for an image."""
    )


class GainFile(Image2D):
    """
    A gain reference file.
    """

    path: Optional[str] = Field(default=None, description="""Path to a file.""")
    width: Optional[int] = Field(
        default=None, description="""The width of the image (x-axis) in pixels"""
    )
    height: Optional[int] = Field(
        default=None, description="""The height of the image (y-axis) in pixels"""
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )


class DefectFile(Image2D):
    """
    A detector defect file.
    """

    path: Optional[str] = Field(default=None, description="""Path to a file.""")
    width: Optional[int] = Field(
        default=None, description="""The width of the image (x-axis) in pixels"""
    )
    height: Optional[int] = Field(
        default=None, description="""The height of the image (y-axis) in pixels"""
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )


class MovieFrame(AcquisitionMetadataMixin, Image2D):
    """
    An individual movie frame
    """

    path: Optional[str] = Field(default=None, description="""Path to a file.""")
    section: Optional[int] = Field(
        default=None,
        description="""0-based section index to the entity inside a stack.""",
    )
    nominal_tilt_angle: Optional[float] = Field(
        default=None, description="""The tilt angle reported by the microscope"""
    )
    accumulated_dose: Optional[float] = Field(
        default=None, description="""The pre-exposure up to this image in e-/A^2"""
    )
    ctf_metadata: Optional[CTFMetadata] = Field(
        default=None, description="""A set of CTF patameters for an image."""
    )
    width: Optional[int] = Field(
        default=None, description="""The width of the image (x-axis) in pixels"""
    )
    height: Optional[int] = Field(
        default=None, description="""The height of the image (y-axis) in pixels"""
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )


class MovieStack(ConfiguredBaseModel):
    """
    A stack of movie frames.
    """

    id: str = Field(default=..., description="""Unique identifier for this entity""")
    path: Optional[str] = Field(default=None, description="""Path to a file.""")
    images: Optional[list[MovieFrame]] = Field(
        default=[], description="""The movie frames in the stack"""
    )


class MovieStackSeries(ConfiguredBaseModel):
    """
    A group of movie stacks that belong to a single tilt series.
    """

    id: str = Field(default=..., description="""Unique identifier for this entity""")
    stacks: Optional[list[MovieStack]] = Field(
        default=[], description="""The movie stacks."""
    )


class BaseProjectionImage(AcquisitionMetadataMixin, Image2D):
    """
    Base class for different projection image types, not for direct use.
    """

    path: Optional[str] = Field(default=None, description="""Path to a file.""")
    section: Optional[int] = Field(
        default=None,
        description="""0-based section index to the entity inside a stack.""",
    )
    nominal_tilt_angle: Optional[float] = Field(
        default=None, description="""The tilt angle reported by the microscope"""
    )
    accumulated_dose: Optional[float] = Field(
        default=None, description="""The pre-exposure up to this image in e-/A^2"""
    )
    ctf_metadata: Optional[CTFMetadata] = Field(
        default=None, description="""A set of CTF patameters for an image."""
    )
    width: Optional[int] = Field(
        default=None, description="""The width of the image (x-axis) in pixels"""
    )
    height: Optional[int] = Field(
        default=None, description="""The height of the image (y-axis) in pixels"""
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )


class ProjectionImage(BaseProjectionImage):
    """
    A projection image.
    """

    path: Optional[str] = Field(default=None, description="""Path to a file.""")
    section: Optional[int] = Field(
        default=None,
        description="""0-based section index to the entity inside a stack.""",
    )
    nominal_tilt_angle: Optional[float] = Field(
        default=None, description="""The tilt angle reported by the microscope"""
    )
    accumulated_dose: Optional[float] = Field(
        default=None, description="""The pre-exposure up to this image in e-/A^2"""
    )
    ctf_metadata: Optional[CTFMetadata] = Field(
        default=None, description="""A set of CTF patameters for an image."""
    )
    width: Optional[int] = Field(
        default=None, description="""The width of the image (x-axis) in pixels"""
    )
    height: Optional[int] = Field(
        default=None, description="""The height of the image (y-axis) in pixels"""
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )


class SubProjectionImage(ProjectionImage):
    """
    A croppecd projection image.
    """

    particle_index: Optional[int] = Field(
        default=None, description="""Index of a particle inside a tomogram."""
    )
    path: Optional[str] = Field(default=None, description="""Path to a file.""")
    section: Optional[int] = Field(
        default=None,
        description="""0-based section index to the entity inside a stack.""",
    )
    nominal_tilt_angle: Optional[float] = Field(
        default=None, description="""The tilt angle reported by the microscope"""
    )
    accumulated_dose: Optional[float] = Field(
        default=None, description="""The pre-exposure up to this image in e-/A^2"""
    )
    ctf_metadata: Optional[CTFMetadata] = Field(
        default=None, description="""A set of CTF patameters for an image."""
    )
    width: Optional[int] = Field(
        default=None, description="""The width of the image (x-axis) in pixels"""
    )
    height: Optional[int] = Field(
        default=None, description="""The height of the image (y-axis) in pixels"""
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )


class TiltImage(BaseProjectionImage):
    """
    A projection image that belongs to a tilt series.
    """

    movie_stack_id: Optional[str] = Field(
        default=None, description="""The ID of the movie stack for this tilt image."""
    )
    path: Optional[str] = Field(default=None, description="""Path to a file.""")
    section: Optional[int] = Field(
        default=None,
        description="""0-based section index to the entity inside a stack.""",
    )
    nominal_tilt_angle: Optional[float] = Field(
        default=None, description="""The tilt angle reported by the microscope"""
    )
    accumulated_dose: Optional[float] = Field(
        default=None, description="""The pre-exposure up to this image in e-/A^2"""
    )
    ctf_metadata: Optional[CTFMetadata] = Field(
        default=None, description="""A set of CTF patameters for an image."""
    )
    width: Optional[int] = Field(
        default=None, description="""The width of the image (x-axis) in pixels"""
    )
    height: Optional[int] = Field(
        default=None, description="""The height of the image (y-axis) in pixels"""
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )


class TiltSeries(ConfiguredBaseModel):
    """
    A stack of projection images.
    """

    id: str = Field(default=..., description="""Unique identifier for this entity""")
    path: Optional[str] = Field(default=None, description="""Path to a file.""")
    ctf_corrected: Optional[bool] = Field(
        default=None,
        description="""Flag to indicate if this was reconstructed from a tilt-series with the ctf corrected.""",
    )
    even_path: Optional[str] = Field(
        default=None, description="""Path of the even file."""
    )
    odd_path: Optional[str] = Field(
        default=None, description="""Path of the odd file."""
    )
    images: Optional[list[TiltImage]] = Field(
        default=[], description="""The projections in the stack."""
    )
    movie_stack_series_id: Optional[str] = Field(
        default=None,
        description="""The ID of the movie stack series for this tilt series.""",
    )


class Tomogram(Image3D):
    """
    A 3D tomogram.
    """

    id: str = Field(default=..., description="""Unique identifier for this entity""")
    path: Optional[str] = Field(default=None, description="""Path to a file.""")
    ctf_corrected: Optional[bool] = Field(
        default=None,
        description="""Flag to indicate if this was reconstructed from a tilt-series with the ctf corrected.""",
    )
    even_path: Optional[str] = Field(
        default=None, description="""Path of the even file."""
    )
    odd_path: Optional[str] = Field(
        default=None, description="""Path of the odd file."""
    )
    tilt_series_id: Optional[str] = Field(
        default=None, description="""The ID of the tilt series for this tomogram."""
    )
    width: Optional[int] = Field(
        default=None, description="""The width of the image (x-axis) in pixels"""
    )
    height: Optional[int] = Field(
        default=None, description="""The height of the image (y-axis) in pixels"""
    )
    depth: Optional[int] = Field(
        default=None, description="""The depth of the image (z-axis) in pixels"""
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )


class ParticleMap(Image3D):
    """
    A 3D particle density map.
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
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )


class CoordMetaMixin(ConfiguredBaseModel):
    """
    Coordinate system mixins for annotations.
    """

    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )


class Annotation(ConfiguredBaseModel):
    """
    A primitive annotation.
    """

    annotation_type: AnnotationType = Field(
        default=..., description="""The type of annotation."""
    )
    path: Optional[str] = Field(default=None, description="""Path to a file.""")


class SegmentationMask2D(Annotation, Image2D):
    """
    An annotation image with categorical labels.
    """

    width: Optional[int] = Field(
        default=None, description="""The width of the image (x-axis) in pixels"""
    )
    height: Optional[int] = Field(
        default=None, description="""The height of the image (y-axis) in pixels"""
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )
    annotation_type: Literal[AnnotationType.segmentation_mask_2D] = Field(
        AnnotationType.segmentation_mask_2D, description="""The type of annotation."""
    )
    path: Optional[str] = Field(default=None, description="""Path to a file.""")


class SegmentationMask3D(Annotation, Image3D):
    """
    An annotation volume with categorical labels.
    """

    width: Optional[int] = Field(
        default=None, description="""The width of the image (x-axis) in pixels"""
    )
    height: Optional[int] = Field(
        default=None, description="""The height of the image (y-axis) in pixels"""
    )
    depth: Optional[int] = Field(
        default=None, description="""The depth of the image (z-axis) in pixels"""
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )
    annotation_type: Literal[AnnotationType.segmentation_mask_3D] = Field(
        AnnotationType.segmentation_mask_3D, description="""The type of annotation."""
    )
    path: Optional[str] = Field(default=None, description="""Path to a file.""")


class ProbabilityMap2D(Annotation, Image2D):
    """
    An annotation image with real-valued labels.
    """

    width: Optional[int] = Field(
        default=None, description="""The width of the image (x-axis) in pixels"""
    )
    height: Optional[int] = Field(
        default=None, description="""The height of the image (y-axis) in pixels"""
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )
    annotation_type: Literal[AnnotationType.probability_map_2D] = Field(
        AnnotationType.probability_map_2D, description="""The type of annotation."""
    )
    path: Optional[str] = Field(default=None, description="""Path to a file.""")


class ProbabilityMap3D(Annotation, Image3D):
    """
    An annotation volume with real-valued labels.
    """

    width: Optional[int] = Field(
        default=None, description="""The width of the image (x-axis) in pixels"""
    )
    height: Optional[int] = Field(
        default=None, description="""The height of the image (y-axis) in pixels"""
    )
    depth: Optional[int] = Field(
        default=None, description="""The depth of the image (z-axis) in pixels"""
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )
    annotation_type: Literal[AnnotationType.probability_map_3D] = Field(
        AnnotationType.probability_map_3D, description="""The type of annotation."""
    )
    path: Optional[str] = Field(default=None, description="""Path to a file.""")


class PointSet2D(Annotation, CoordMetaMixin):
    """
    A set of 2D point annotations.
    """

    origin2D: Optional[Annotated[list[Vector2D], Field(min_length=1)]] = Field(
        default=None, description="""Location on a 2D image (Nx2)."""
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )
    annotation_type: Literal[AnnotationType.point_set_2D] = Field(
        AnnotationType.point_set_2D, description="""The type of annotation."""
    )
    path: Optional[str] = Field(default=None, description="""Path to a file.""")


class PointSet3D(Annotation, CoordMetaMixin):
    """
    A set of 3D point annotations.
    """

    origin3D: Optional[Annotated[list[Vector3D], Field(min_length=1)]] = Field(
        default=None, description="""Location on a 3D image (Nx3)."""
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )
    annotation_type: Literal[AnnotationType.point_set_3D] = Field(
        AnnotationType.point_set_3D, description="""The type of annotation."""
    )
    path: Optional[str] = Field(default=None, description="""Path to a file.""")


class PointVectorSet2D(Annotation, CoordMetaMixin):
    """
    A set of 2D points with an associated direction vector.
    """

    origin2D: Optional[Annotated[list[Vector2D], Field(min_length=1)]] = Field(
        default=None, description="""Location on a 2D image (Nx2)."""
    )
    vector2D: Optional[Annotated[list[Vector2D], Field(min_length=1)]] = Field(
        default=None,
        description="""Orientation vector associated with a point on a 2D image (Nx2).""",
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )
    annotation_type: Literal[AnnotationType.point_vector_set_2D] = Field(
        AnnotationType.point_vector_set_2D, description="""The type of annotation."""
    )
    path: Optional[str] = Field(default=None, description="""Path to a file.""")


class PointVectorSet3D(Annotation, CoordMetaMixin):
    """
    A set of 3D points with an associated direction vector.
    """

    origin3D: Optional[Annotated[list[Vector3D], Field(min_length=1)]] = Field(
        default=None, description="""Location on a 3D image (Nx3)."""
    )
    vector3D: Optional[Annotated[list[Vector3D], Field(min_length=1)]] = Field(
        default=None,
        description="""Orientation vector associated with a point on a 3D image (Nx3).""",
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )
    annotation_type: Literal[AnnotationType.point_vector_set_3D] = Field(
        AnnotationType.point_vector_set_3D, description="""The type of annotation."""
    )
    path: Optional[str] = Field(default=None, description="""Path to a file.""")


class PointMatrixSet2D(Annotation, CoordMetaMixin):
    """
    A set of 2D points with an associated rotation matrix.
    """

    origin2D: Optional[Annotated[list[Vector2D], Field(min_length=1)]] = Field(
        default=None, description="""Location on a 2D image (Nx2)."""
    )
    matrix2D: Optional[Annotated[list[Matrix2x2], Field(min_length=1)]] = Field(
        default=None,
        description="""Rotation matrix associated with a point on a 2D image (Nx2x2).""",
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )
    annotation_type: Literal[AnnotationType.point_matrix_set_2D] = Field(
        AnnotationType.point_matrix_set_2D, description="""The type of annotation."""
    )
    path: Optional[str] = Field(default=None, description="""Path to a file.""")


class PointMatrixSet3D(Annotation, CoordMetaMixin):
    """
    A set of 3D points with an associated rotation matrix.
    """

    origin3D: Optional[Annotated[list[Vector3D], Field(min_length=1)]] = Field(
        default=None, description="""Location on a 3D image (Nx3)."""
    )
    matrix3D: Optional[Annotated[list[Matrix3x3], Field(min_length=1)]] = Field(
        default=None,
        description="""Rotation matrix associated with a point on a 3D image (Nx3x3).""",
    )
    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )
    annotation_type: Literal[AnnotationType.point_matrix_set_3D] = Field(
        AnnotationType.point_matrix_set_3D, description="""The type of annotation."""
    )
    path: Optional[str] = Field(default=None, description="""Path to a file.""")


class TriMesh(Annotation, CoordMetaMixin):
    """
    A mesh annotation.
    """

    coordinate_systems: Optional[list[CoordinateSystem]] = Field(
        default=[], description="""Named coordinate systems for this entity"""
    )
    coordinate_transformations: Optional[
        list[
            Annotated[
                Union[Identity, MapAxis, Translation, Scale, Affine, Sequence],
                Field(discriminator="transformation_type"),
            ]
        ]
    ] = Field(
        default=[], description="""Named coordinate transformations for this entity"""
    )
    annotation_type: Literal[AnnotationType.tri_mesh] = Field(
        AnnotationType.tri_mesh, description="""The type of annotation."""
    )
    path: Optional[str] = Field(default=None, description="""Path to a file.""")


class Region(ConfiguredBaseModel):
    """
    Raw data (movie stacks) and derived data (tilt series, tomograms, annotations) from a single region of a specimen.
    """

    id: str = Field(default=..., description="""Unique identifier for this entity""")
    movie_stack_collection: Optional[MovieStackCollection] = Field(
        default=None, description="""The movie stack"""
    )
    tilt_series: Optional[list[TiltSeries]] = Field(
        default=[], description="""The tilt series"""
    )
    alignments: Optional[list[Alignment]] = Field(
        default=[], description="""The alignments"""
    )
    tomograms: Optional[list[Tomogram]] = Field(
        default=[], description="""The tomograms"""
    )
    annotations: Optional[
        list[
            Annotated[
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
                ],
                Field(discriminator="annotation_type"),
            ]
        ]
    ] = Field(default=[], description="""The annotations for this region""")


class Average(ConfiguredBaseModel):
    """
    A particle averaging experiment.
    """

    name: Optional[str] = Field(
        default=None,
        description="""A name, or title, human-readable, for this entity""",
    )
    particle_maps: Optional[list[ParticleMap]] = Field(
        default=[], description="""The particle maps"""
    )
    annotations: Optional[
        list[
            Annotated[
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
                ],
                Field(discriminator="annotation_type"),
            ]
        ]
    ] = Field(default=[], description="""The annotations""")


class MovieStackCollection(ConfiguredBaseModel):
    """
    A collection of movie stacks using the same gain and defect files.
    """

    movie_stacks: Optional[list[MovieStackSeries]] = Field(
        default=[], description="""The movie stacks in the collection"""
    )
    gain_file: Optional[GainFile] = Field(
        default=None, description="""The gain file for the movie stacks"""
    )
    defect_file: Optional[DefectFile] = Field(
        default=None, description="""The defect file for the movie stacks"""
    )


class Dataset(ConfiguredBaseModel):
    """
    A dataset
    """

    name: Optional[str] = Field(
        default=None,
        description="""A name, or title, human-readable, for this entity""",
    )
    regions: Optional[list[Region]] = Field(
        default=[], description="""The regions in the dataset"""
    )
    averages: Optional[list[Average]] = Field(
        default=[], description="""The averages in the dataset"""
    )


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
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
MovieStackSeries.model_rebuild()
BaseProjectionImage.model_rebuild()
ProjectionImage.model_rebuild()
SubProjectionImage.model_rebuild()
TiltImage.model_rebuild()
TiltSeries.model_rebuild()
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
