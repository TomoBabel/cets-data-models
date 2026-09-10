from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Literal, Optional, TypeAlias, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
)

from cets_data_model.models.mixins import (
    NonRigidPresenceMixin,
    PixelSizeMixin,
    VoxelSizeMixin,
)

metamodel_version = "1.11.0"
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


Vector2D: TypeAlias = Annotated[list[float], Field(min_length=2, max_length=2)]
Vector3D: TypeAlias = Annotated[list[float], Field(min_length=3, max_length=3)]
Matrix2x2: TypeAlias = Annotated[list[Vector2D], Field(min_length=2, max_length=2)]
Matrix3x3: TypeAlias = Annotated[list[Vector3D], Field(min_length=3, max_length=3)]
Radii: TypeAlias = Annotated[list[float], Field(min_length=1)]
Dimensions2D: TypeAlias = Annotated[list[float], Field(min_length=2, max_length=2)]
Dimensions3D: TypeAlias = Annotated[list[float], Field(min_length=3, max_length=3)]
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


class CoordinateSpaceName(str, Enum):
    """
    Canonical names for an entity's standard coordinate systems.
    """

    array = "array"
    """
    Discrete index space (integer pixel/voxel coordinates).
    """
    physical = "physical"
    """
    Continuous physical space in Ångström.
    """


class AxisUnit(str, Enum):
    """
    Allowable axis units.
    """

    pixel = "pixel"
    """
    2D array index unit.
    """
    voxel = "voxel"
    """
    3D array index unit.
    """
    angstrom = "angstrom"
    """
    Physical length in Ångström (the default).
    """
    nanometer = "nanometer"
    """
    Physical length in nanometers.
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


class TransformationName(str, Enum):
    """
    Canonical controlled-vocabulary names for the standard transformations (Direction B).
    """

    array_to_physical = "array_to_physical"
    """
    Sampling — an entity's array (pixel/voxel) space to its physical space.
    """
    calibration_to_movie_frame = "calibration_to_movie_frame"
    """
    Calibration image to movie frame.
    """
    movie_frame_to_projection = "movie_frame_to_projection"
    """
    Movie frame to projection.
    """
    sub_projection_to_projection = "sub_projection_to_projection"
    """
    Sub-projection to projection.
    """
    annotation_to_tomogram = "annotation_to_tomogram"
    """
    Annotation to tomogram.
    """
    subtomogram_to_tomogram = "subtomogram_to_tomogram"
    """
    Subtomogram to tomogram.
    """
    particle_map_to_subtomogram = "particle_map_to_subtomogram"
    """
    Particle map to subtomogram.
    """
    particle_map_to_tomogram = "particle_map_to_tomogram"
    """
    Particle map to tomogram (derived composition).
    """
    tomogram_to_projection = "tomogram_to_projection"
    """
    Tomogram to projection (the tomographic projection, per tilt).
    """


class NonRigidKind(str, Enum):
    tilt_series_projection_residual = "tilt-series-projection-residual"
    movie_frame_residual = "movie-frame-residual"


class SamplingKind(str, Enum):
    grid = "grid"
    particles = "particles"


class HeldoutMethod(str, Enum):
    scrambled_sobol = "scrambled-sobol"
    particle_subset = "particle-subset"
    none = "none"


class DisplacementAvailability(str, Enum):
    present = "present"
    zero_at_samples = "zero_at_samples"
    none = "none"


class DepthAvailability(str, Enum):
    present = "present"
    none = "none"


class SourceAngleKind(str, Enum):
    nominal = "nominal"
    effective = "effective"
    unknown = "unknown"


class MovieGauge(str, Enum):
    native_origin = "native-origin"
    reference_frame = "reference-frame"


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
    sphere_set = "sphere_set"
    """
    A set of spheres.
    """
    circle_set = "circle_set"
    """
    A set of circles.
    """
    cylinder_set = "cylinder_set"
    """
    A set of cylinders.
    """
    cuboid_set = "cuboid_set"
    """
    A set of oriented 3D boxes.
    """
    box_set = "box_set"
    """
    A set of 2D boxes.
    """
    spline_2D = "spline_2D"
    """
    A 2D spline.
    """
    spline_3D = "spline_3D"
    """
    A 3D spline.
    """
    density_map = "density_map"
    """
    A density map fit into a volume.
    """


class ElectronSource(str, Enum):
    """
    Type of electron source (mirrors OSC-EM permissible values).
    """

    FEG = "FEG"
    """
    Field emission gun
    """
    cold_FEG = "cold_FEG"
    """
    Cold field emission gun
    """
    LaB6 = "LaB6"
    """
    Lanthanum hexaboride
    """
    tungsten = "tungsten"
    """
    Tungsten filament
    """


class Image2D(PixelSizeMixin, ConfiguredBaseModel):
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


class Image3D(VoxelSizeMixin, ConfiguredBaseModel):
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
        default=None, description="""A human-readable name or title for this entity"""
    )
    axis_unit: Optional[AxisUnit] = Field(
        default=AxisUnit.angstrom, description="""The unit of the axis"""
    )
    axis_type: Optional[AxisType] = Field(
        default=None, description="""The type of axis"""
    )


class CoordinateSystem(ConfiguredBaseModel):
    """
    A coordinate system
    """

    name: str = Field(
        default=...,
        description="""The name of the coordinate system. Free-form to allow per-entity / intermediate systems; the canonical values are enumerated by CoordinateSpaceName.""",
    )
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
        default=None, description="""A human-readable name or title for this entity"""
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
        default=TransformationType.identity,
        description="""The type of transformation.""",
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
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
        default=TransformationType.map_axis,
        description="""The type of transformation.""",
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
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
        default=TransformationType.translation,
        description="""The type of transformation.""",
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
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
        default=TransformationType.scale, description="""The type of transformation."""
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
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
        default=TransformationType.affine, description="""The type of transformation."""
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
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
        default=TransformationType.sequence,
        description="""The type of transformation.""",
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
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

    id: str = Field(default=..., description="""Unique identifier for this entity""")
    tilt_image_id: Optional[str] = Field(
        default=None,
        description="""ID of the tilt-image this alignment applies to. Multiple alignments (e.g. produced  by different algorithms) may reference the same tilt-image.""",
    )
    sequence: Optional[list[Union[Affine, Translation]]] = Field(
        default=[],
        description="""The ordered tilt, in-plane rotation, and shift transformations.""",
        max_length=3,
    )
    transformation_type: Literal[TransformationType.projection_alignment] = Field(
        default=TransformationType.projection_alignment,
        description="""The type of transformation.""",
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    input: Optional[str] = Field(
        default=None, description="""The source coordinate system name"""
    )
    output: Optional[str] = Field(
        default=None, description="""The target coordinate system name"""
    )


class Alignment(NonRigidPresenceMixin, ConfiguredBaseModel):
    """
    The tomographic alignment for a tilt series.
    """

    tilt_series_id: Optional[str] = Field(
        default=None,
        description="""ID of the tilt-series this alignment set applies to. Multiple Alignments (e.g.  from different algorithms) may reference the same tilt-series.""",
    )
    projection_alignments: Optional[list[ProjectionAlignment]] = Field(
        default=[], description="""alignment for a specific projection"""
    )
    id: Optional[str] = Field(
        default=None,
        description="""Optional alignment identity; required by the non-rigid processing profile.""",
    )
    name: Optional[str] = Field(default=None)
    reference_volume_id: Optional[str] = Field(
        default=None,
        description="""ID of the Tomogram defining the shared reference physical frame; its path may be null.""",
    )
    non_rigid_alignment: Optional[NonRigidAlignment] = Field(default=None)
    tilt_angle_observations: Optional[list[TiltAngleObservation]] = Field(default=[])
    exclusions: Optional[list[ProjectionExclusion]] = Field(default=[])
    provenance: Optional[ProcessingProvenance] = Field(default=None)


class SamplingDescriptor(ConfiguredBaseModel):
    """
    Sampling identities; coordinates are stored in the payload.
    """

    kind: SamplingKind = Field(default=...)


class GridSampling(SamplingDescriptor):
    """
    Regular inclusive grid in the reference physical frame.
    """

    grid_shape: list[Annotated[int, Field(ge=1)]] = Field(
        default=...,
        description="""Grid counts in x,y[,z] order.""",
        min_length=2,
        max_length=3,
    )
    kind: Literal[SamplingKind.grid] = Field(default=SamplingKind.grid)


class ParticleSampling(SamplingDescriptor):
    """
    Samples bound to stable point identities in a CETS point set.
    """

    annotation_id: str = Field(
        default=...,
        description="""ID of the PointSet3D defining effective static particle coordinates.""",
    )
    kind: Literal[SamplingKind.particles] = Field(default=SamplingKind.particles)


class HeldoutSampling(ConfiguredBaseModel):
    """
    How held-out samples were selected; zero count is not evaluated.
    """

    method: HeldoutMethod = Field(default=...)
    seed: Optional[int] = Field(default=None, ge=0)
    count: int = Field(default=..., ge=0)
    fraction: Optional[float] = Field(
        default=None,
        description="""Requested particle held-out fraction.""",
        ge=0,
        le=1,
    )
    min_count: Optional[int] = Field(
        default=None,
        description="""Particle split minimum; too-small inputs have no held-out set.""",
        ge=0,
    )


class NonRigidChannels(ConfiguredBaseModel):
    """
    Independent availability of scientific channels.
    """

    displacement_3d: Optional[DisplacementAvailability] = Field(
        default=DisplacementAvailability.none
    )
    ctf_depth: Optional[DepthAvailability] = Field(default=DepthAvailability.none)


class NonRigidAlignment(ConfiguredBaseModel):
    """
    A lossy point-sampled non-rigid component owned by its alignment.
    """

    profile_version: Annotated[str, Field(pattern="^cets-nonrigid/0\\.1$")] = Field(
        default=...
    )
    kind: NonRigidKind = Field(default=...)
    tilt_image_ids: Optional[list[str]] = Field(
        default=[],
        description="""All tilt-image IDs in payload row order; movies use MovieAlignment.frame_ids.""",
    )
    payload_uri: str = Field(
        default=...,
        description="""Local Zarr path, relative to the document directory or absolute.""",
    )
    payload_group: str = Field(
        default=..., description="""Relative group key within the payload store."""
    )
    sampling: Annotated[
        Union[GridSampling, ParticleSampling], Field(discriminator="kind")
    ] = Field(default=...)
    heldout: HeldoutSampling = Field(default=...)
    channels: NonRigidChannels = Field(default=...)
    context_digest: Annotated[str, Field(pattern="^[0-9a-f]{64}$")] = Field(default=...)
    digest_version: int = Field(default=..., ge=1, le=1)


class NativeParameter(ConfiguredBaseModel):
    """
    Tool-specific parameter or provenance; never duplicate core geometry.
    """

    name: str = Field(default=...)
    value_json: str = Field(
        default=..., description="""JSON encoding of the parameter value."""
    )


class NativeArtifact(ConfiguredBaseModel):
    """
    Optional source artifact; processing never reopens it implicitly.
    """

    role: str = Field(default=...)
    uri: str = Field(default=...)
    sha256: Annotated[Optional[str], Field(pattern="^[0-9a-f]{64}$")] = Field(
        default=None
    )


class ProcessingProvenance(ConfiguredBaseModel):
    """
    Software and structured import/export provenance.
    """

    software_name: Optional[str] = Field(default=None)
    software_version: Optional[str] = Field(default=None)
    parameters: Optional[list[NativeParameter]] = Field(default=[])
    artifacts: Optional[list[NativeArtifact]] = Field(default=[])
    warnings: Optional[list[str]] = Field(default=[])
    dropped_information: Optional[list[str]] = Field(default=[])


class TiltAngleObservation(ConfiguredBaseModel):
    """
    A source angle attached to an alignment, including excluded images.
    """

    tilt_image_id: str = Field(default=...)
    value_degrees: float = Field(default=...)
    angle_kind: Optional[SourceAngleKind] = Field(default=SourceAngleKind.unknown)
    source: Optional[str] = Field(default=None)


class ProjectionExclusion(ConfiguredBaseModel):
    """
    Why an image has no projection alignment in this alignment instance.
    """

    tilt_image_id: str = Field(default=...)
    reason: str = Field(default=...)


class FrameAlignment(ConfiguredBaseModel):
    """
    Global map from corrected physical image coordinates to raw-frame coordinates in Angstrom.
    """

    frame_id: str = Field(default=...)
    transform: Translation = Field(default=...)


class MovieAlignment(NonRigidPresenceMixin, ConfiguredBaseModel):
    """
    Frame-series alignment with a first-class optional non-rigid component.
    """

    id: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    profile_version: Annotated[
        Optional[str], Field(pattern="^cets-nonrigid/0\\.1$")
    ] = Field(default=None)
    movie_stack_id: Optional[str] = Field(default=None)
    frame_ids: Optional[list[str]] = Field(
        default=[],
        description="""All enumerated movie-frame IDs in payload row order.""",
    )
    gauge: Optional[MovieGauge] = Field(default="native-origin")
    reference_frame_id: Optional[str] = Field(
        default=None,
        description="""Frame whose global drift defines the reference-frame gauge; local motion need not vanish.""",
    )
    frame_alignments: Optional[list[FrameAlignment]] = Field(default=[])
    non_rigid_alignment: Optional[NonRigidAlignment] = Field(default=None)
    provenance: Optional[ProcessingProvenance] = Field(default=None)


class PointAttribute(ConfiguredBaseModel):
    """
    Named per-point column; values follow the point-set identity order.
    """

    name: str = Field(default=...)
    numeric_values: Optional[list[float]] = Field(default=[])
    string_values: Optional[list[str]] = Field(default=[])
    boolean_values: Optional[list[bool]] = Field(default=[])


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
        default=None, description="""Estimated angle of astigmatism. Unit: degrees."""
    )
    phase_shift: Optional[float] = Field(
        default=None,
        description="""Phase shift value produced by the usage of a phase plate. Unit: degrees.""",
    )
    defocus_handedness: Optional[int] = Field(
        default=-1,
        description="""The handedness of the tilt geometry used to describe whether the focus increases or decreases as a function of Z distance.""",
    )
    fit_score: Optional[float] = Field(
        default=None,
        description="""Optional native CTF-fit quality score; interpretation is software-specific.""",
    )
    fit_resolution: Optional[float] = Field(
        default=None,
        description="""Optional native CTF-fit resolution limit in Angstrom.""",
        ge=0,
    )


class AcquisitionMetadataMixin(ConfiguredBaseModel):
    """
    Per-exposure acquisition metadata (varies from image to image).
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
    exposure_time: Optional[float] = Field(
        default=None, description="""Total exposure time per movie/record in seconds."""
    )
    acquisition_order: Optional[int] = Field(
        default=None,
        description="""Zero-based acquisition order, independent of storage order.""",
        ge=0,
    )
    exposure_dose: Optional[float] = Field(
        default=None,
        description="""Exposure during this image in electrons per square Angstrom.""",
        ge=0,
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
    id: Optional[str] = Field(
        default=None,
        description="""Optional stable identity; required when referenced by a movie alignment.""",
    )
    source_start_index: Optional[int] = Field(
        default=None,
        description="""Zero-based first raw input frame integrated into this image.""",
        ge=0,
    )
    source_frame_count: Optional[int] = Field(
        default=None,
        description="""Number of contiguous raw input frames integrated into this image.""",
        ge=1,
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
    exposure_time: Optional[float] = Field(
        default=None, description="""Total exposure time per movie/record in seconds."""
    )
    acquisition_order: Optional[int] = Field(
        default=None,
        description="""Zero-based acquisition order, independent of storage order.""",
        ge=0,
    )
    exposure_dose: Optional[float] = Field(
        default=None,
        description="""Exposure during this image in electrons per square Angstrom.""",
        ge=0,
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


class MovieStack(Image2D):
    """
    A stack of movie frames.
    """

    id: str = Field(default=..., description="""Unique identifier for this entity""")
    path: Optional[str] = Field(default=None, description="""Path to a file.""")
    images: Optional[list[MovieFrame]] = Field(
        default=[], description="""The movie frames in the stack"""
    )
    alignments: Optional[list[MovieAlignment]] = Field(default=[])
    raw_frame_count: Optional[int] = Field(
        default=None,
        description="""Total raw input frames, including excluded frames.""",
        ge=1,
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


class MovieStackSeries(ConfiguredBaseModel):
    """
    A group of movie stacks that belong to a single tilt series.
    """

    id: str = Field(default=..., description="""Unique identifier for this entity""")
    stacks: Optional[list[MovieStack]] = Field(
        default=[], description="""The movie stacks."""
    )
    acquisition_session_id: Optional[str] = Field(
        default=None,
        description="""The ID of the acquisition session this movie stack series was collected in.""",
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
    exposure_time: Optional[float] = Field(
        default=None, description="""Total exposure time per movie/record in seconds."""
    )
    acquisition_order: Optional[int] = Field(
        default=None,
        description="""Zero-based acquisition order, independent of storage order.""",
        ge=0,
    )
    exposure_dose: Optional[float] = Field(
        default=None,
        description="""Exposure during this image in electrons per square Angstrom.""",
        ge=0,
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
    exposure_time: Optional[float] = Field(
        default=None, description="""Total exposure time per movie/record in seconds."""
    )
    acquisition_order: Optional[int] = Field(
        default=None,
        description="""Zero-based acquisition order, independent of storage order.""",
        ge=0,
    )
    exposure_dose: Optional[float] = Field(
        default=None,
        description="""Exposure during this image in electrons per square Angstrom.""",
        ge=0,
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
    exposure_time: Optional[float] = Field(
        default=None, description="""Total exposure time per movie/record in seconds."""
    )
    acquisition_order: Optional[int] = Field(
        default=None,
        description="""Zero-based acquisition order, independent of storage order.""",
        ge=0,
    )
    exposure_dose: Optional[float] = Field(
        default=None,
        description="""Exposure during this image in electrons per square Angstrom.""",
        ge=0,
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

    id: str = Field(default=..., description="""Unique identifier for this entity""")
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
    exposure_time: Optional[float] = Field(
        default=None, description="""Total exposure time per movie/record in seconds."""
    )
    acquisition_order: Optional[int] = Field(
        default=None,
        description="""Zero-based acquisition order, independent of storage order.""",
        ge=0,
    )
    exposure_dose: Optional[float] = Field(
        default=None,
        description="""Exposure during this image in electrons per square Angstrom.""",
        ge=0,
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
    acquisition_session_id: Optional[str] = Field(
        default=None,
        description="""The ID of the acquisition session this tilt series was collected in.""",
    )
    defocus_handedness: Optional[int] = Field(
        default=None,
        description="""Sign of the defocus contribution of positive beam-depth displacement; unknown is null.""",
        ge=-1,
        le=1,
    )
    defocus_slope: Optional[float] = Field(
        default=None,
        description="""Dimensionless multiplier of the signed geometric depth contribution.""",
    )
    nominal_tilt_axis_angle: Optional[float] = Field(
        default=None,
        description="""Acquisition-stage tilt-axis angle in degrees, not a refined rotation.""",
    )
    collection_metadata_path: Optional[str] = Field(
        default=None,
        description="""Optional acquisition metadata artifact path or URI.""",
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
    alignment_id: Optional[str] = Field(
        default=None,
        description="""Alignment that produced this reconstructed tomogram.""",
    )
    provenance: Optional[ProcessingProvenance] = Field(default=None)
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
    source_region_id: Optional[str] = Field(
        default=None,
        description="""ID of the region containing the source annotation used to extract this particle map.""",
    )
    source_annotation_id: Optional[str] = Field(
        default=None,
        description="""ID of the source annotation used to extract this particle map.""",
    )
    coord_index: Optional[int] = Field(
        default=None,
        description="""0-based index of the coordinate inside the resolved source annotation.""",
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


class AssociatedFile(ConfiguredBaseModel):
    """
    File associated with this annotation
    """

    path: Optional[str] = Field(default=None, description="""Path to a file.""")


class Annotation(ConfiguredBaseModel):
    """
    A primitive annotation.
    """

    id: str = Field(default=..., description="""Unique identifier for this entity""")
    annotation_type: AnnotationType = Field(
        default=..., description="""The type of annotation."""
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    source_tomogram_id: Optional[str] = Field(
        default=None,
        description="""ID of the tomogram from which this annotation was derived, such as the tomogram containing picked coordinates.""",
    )


class SegmentationMask2D(Annotation, AssociatedFile, Image2D):
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
    path: Optional[str] = Field(default=None, description="""Path to a file.""")
    id: str = Field(default=..., description="""Unique identifier for this entity""")
    annotation_type: Literal[AnnotationType.segmentation_mask_2D] = Field(
        default=AnnotationType.segmentation_mask_2D,
        description="""The type of annotation.""",
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    source_tomogram_id: Optional[str] = Field(
        default=None,
        description="""ID of the tomogram from which this annotation was derived, such as the tomogram containing picked coordinates.""",
    )


class SegmentationMask3D(Annotation, AssociatedFile, Image3D):
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
    path: Optional[str] = Field(default=None, description="""Path to a file.""")
    id: str = Field(default=..., description="""Unique identifier for this entity""")
    annotation_type: Literal[AnnotationType.segmentation_mask_3D] = Field(
        default=AnnotationType.segmentation_mask_3D,
        description="""The type of annotation.""",
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    source_tomogram_id: Optional[str] = Field(
        default=None,
        description="""ID of the tomogram from which this annotation was derived, such as the tomogram containing picked coordinates.""",
    )


class ProbabilityMap2D(Annotation, AssociatedFile, Image2D):
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
    path: Optional[str] = Field(default=None, description="""Path to a file.""")
    id: str = Field(default=..., description="""Unique identifier for this entity""")
    annotation_type: Literal[AnnotationType.probability_map_2D] = Field(
        default=AnnotationType.probability_map_2D,
        description="""The type of annotation.""",
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    source_tomogram_id: Optional[str] = Field(
        default=None,
        description="""ID of the tomogram from which this annotation was derived, such as the tomogram containing picked coordinates.""",
    )


class ProbabilityMap3D(Annotation, AssociatedFile, Image3D):
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
    path: Optional[str] = Field(default=None, description="""Path to a file.""")
    id: str = Field(default=..., description="""Unique identifier for this entity""")
    annotation_type: Literal[AnnotationType.probability_map_3D] = Field(
        default=AnnotationType.probability_map_3D,
        description="""The type of annotation.""",
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    source_tomogram_id: Optional[str] = Field(
        default=None,
        description="""ID of the tomogram from which this annotation was derived, such as the tomogram containing picked coordinates.""",
    )


class PointSet2D(Annotation, CoordMetaMixin):
    """
    A set of 2D point annotations.
    """

    origin2D: Optional[Annotated[list[Vector2D], Field(min_length=1)]] = Field(
        default=None, description="""Location on a 2D image (Nx2)."""
    )
    point_ids: Optional[list[str]] = Field(
        default=[], description="""Stable IDs in coordinate order."""
    )
    point_attributes: Optional[list[PointAttribute]] = Field(default=[])
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
    id: str = Field(default=..., description="""Unique identifier for this entity""")
    annotation_type: Literal[AnnotationType.point_set_2D] = Field(
        default=AnnotationType.point_set_2D, description="""The type of annotation."""
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    source_tomogram_id: Optional[str] = Field(
        default=None,
        description="""ID of the tomogram from which this annotation was derived, such as the tomogram containing picked coordinates.""",
    )


class PointSet3D(Annotation, CoordMetaMixin):
    """
    A set of 3D point annotations.
    """

    origin3D: Optional[Annotated[list[Vector3D], Field(min_length=1)]] = Field(
        default=None, description="""Location on a 3D image (Nx3)."""
    )
    point_ids: Optional[list[str]] = Field(
        default=[], description="""Stable IDs in coordinate order."""
    )
    point_attributes: Optional[list[PointAttribute]] = Field(default=[])
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
    id: str = Field(default=..., description="""Unique identifier for this entity""")
    annotation_type: Literal[AnnotationType.point_set_3D] = Field(
        default=AnnotationType.point_set_3D, description="""The type of annotation."""
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    source_tomogram_id: Optional[str] = Field(
        default=None,
        description="""ID of the tomogram from which this annotation was derived, such as the tomogram containing picked coordinates.""",
    )


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
    id: str = Field(default=..., description="""Unique identifier for this entity""")
    annotation_type: Literal[AnnotationType.point_vector_set_2D] = Field(
        default=AnnotationType.point_vector_set_2D,
        description="""The type of annotation.""",
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    source_tomogram_id: Optional[str] = Field(
        default=None,
        description="""ID of the tomogram from which this annotation was derived, such as the tomogram containing picked coordinates.""",
    )


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
    id: str = Field(default=..., description="""Unique identifier for this entity""")
    annotation_type: Literal[AnnotationType.point_vector_set_3D] = Field(
        default=AnnotationType.point_vector_set_3D,
        description="""The type of annotation.""",
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    source_tomogram_id: Optional[str] = Field(
        default=None,
        description="""ID of the tomogram from which this annotation was derived, such as the tomogram containing picked coordinates.""",
    )


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
    id: str = Field(default=..., description="""Unique identifier for this entity""")
    annotation_type: Literal[AnnotationType.point_matrix_set_2D] = Field(
        default=AnnotationType.point_matrix_set_2D,
        description="""The type of annotation.""",
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    source_tomogram_id: Optional[str] = Field(
        default=None,
        description="""ID of the tomogram from which this annotation was derived, such as the tomogram containing picked coordinates.""",
    )


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
    id: str = Field(default=..., description="""Unique identifier for this entity""")
    annotation_type: Literal[AnnotationType.point_matrix_set_3D] = Field(
        default=AnnotationType.point_matrix_set_3D,
        description="""The type of annotation.""",
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    source_tomogram_id: Optional[str] = Field(
        default=None,
        description="""ID of the tomogram from which this annotation was derived, such as the tomogram containing picked coordinates.""",
    )


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
    id: str = Field(default=..., description="""Unique identifier for this entity""")
    annotation_type: Literal[AnnotationType.tri_mesh] = Field(
        default=AnnotationType.tri_mesh, description="""The type of annotation."""
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    source_tomogram_id: Optional[str] = Field(
        default=None,
        description="""ID of the tomogram from which this annotation was derived, such as the tomogram containing picked coordinates.""",
    )


class SphereSet(Annotation, CoordMetaMixin):
    """
    A set of spheres.
    """

    origin3D: Optional[Annotated[list[Vector3D], Field(min_length=1)]] = Field(
        default=None, description="""Location on a 3D image (Nx3)."""
    )
    radii: Optional[Radii] = Field(
        default=None, description="""Radii of circles, spheres, or cylinders (N)."""
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
    id: str = Field(default=..., description="""Unique identifier for this entity""")
    annotation_type: Literal[AnnotationType.sphere_set] = Field(
        default=AnnotationType.sphere_set, description="""The type of annotation."""
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    source_tomogram_id: Optional[str] = Field(
        default=None,
        description="""ID of the tomogram from which this annotation was derived, such as the tomogram containing picked coordinates.""",
    )


class CircleSet(Annotation, CoordMetaMixin):
    """
    A set of circles.
    """

    origin2D: Optional[Annotated[list[Vector2D], Field(min_length=1)]] = Field(
        default=None, description="""Location on a 2D image (Nx2)."""
    )
    radii: Optional[Radii] = Field(
        default=None, description="""Radii of circles, spheres, or cylinders (N)."""
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
    id: str = Field(default=..., description="""Unique identifier for this entity""")
    annotation_type: Literal[AnnotationType.circle_set] = Field(
        default=AnnotationType.circle_set, description="""The type of annotation."""
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    source_tomogram_id: Optional[str] = Field(
        default=None,
        description="""ID of the tomogram from which this annotation was derived, such as the tomogram containing picked coordinates.""",
    )


class CylinderSet(Annotation, CoordMetaMixin):
    """
    A set of cylinders,
    """

    vector3D: Optional[Annotated[list[Vector3D], Field(min_length=1)]] = Field(
        default=None,
        description="""Orientation vector associated with a point on a 3D image (Nx3).""",
    )
    radii: Optional[Radii] = Field(
        default=None, description="""Radii of circles, spheres, or cylinders (N)."""
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
    id: str = Field(default=..., description="""Unique identifier for this entity""")
    annotation_type: Literal[AnnotationType.cylinder_set] = Field(
        default=AnnotationType.cylinder_set, description="""The type of annotation."""
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    source_tomogram_id: Optional[str] = Field(
        default=None,
        description="""ID of the tomogram from which this annotation was derived, such as the tomogram containing picked coordinates.""",
    )


class CuboidSet(Annotation, CoordMetaMixin):
    """
    A set of oriented 3D boxes.
    """

    origin3D: Optional[Annotated[list[Vector3D], Field(min_length=1)]] = Field(
        default=None, description="""Location on a 3D image (Nx3)."""
    )
    matrix3D: Optional[Annotated[list[Matrix3x3], Field(min_length=1)]] = Field(
        default=None,
        description="""Rotation matrix associated with a point on a 3D image (Nx3x3).""",
    )
    dimensions3D: Optional[Annotated[list[Dimensions3D], Field(min_length=1)]] = Field(
        default=None, description="""Dimensions of 3D objects (x, y, z)."""
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
    id: str = Field(default=..., description="""Unique identifier for this entity""")
    annotation_type: Literal[AnnotationType.cuboid_set] = Field(
        default=AnnotationType.cuboid_set, description="""The type of annotation."""
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    source_tomogram_id: Optional[str] = Field(
        default=None,
        description="""ID of the tomogram from which this annotation was derived, such as the tomogram containing picked coordinates.""",
    )


class BoxSet(Annotation, CoordMetaMixin):
    """
    A set of 2D boxes.
    """

    origin2D: Optional[Annotated[list[Vector2D], Field(min_length=1)]] = Field(
        default=None, description="""Location on a 2D image (Nx2)."""
    )
    matrix2D: Optional[Annotated[list[Matrix2x2], Field(min_length=1)]] = Field(
        default=None,
        description="""Rotation matrix associated with a point on a 2D image (Nx2x2).""",
    )
    dimensions2D: Optional[Annotated[list[Dimensions2D], Field(min_length=1)]] = Field(
        default=None, description="""Dimensions of 2D objects (x, y)."""
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
    id: str = Field(default=..., description="""Unique identifier for this entity""")
    annotation_type: Literal[AnnotationType.box_set] = Field(
        default=AnnotationType.box_set, description="""The type of annotation."""
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    source_tomogram_id: Optional[str] = Field(
        default=None,
        description="""ID of the tomogram from which this annotation was derived, such as the tomogram containing picked coordinates.""",
    )


class Spline2D(Annotation, CoordMetaMixin):
    """
    A 2D spline.
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
    id: str = Field(default=..., description="""Unique identifier for this entity""")
    annotation_type: Literal[AnnotationType.spline_2D] = Field(
        default=AnnotationType.spline_2D, description="""The type of annotation."""
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    source_tomogram_id: Optional[str] = Field(
        default=None,
        description="""ID of the tomogram from which this annotation was derived, such as the tomogram containing picked coordinates.""",
    )


class Spline3D(Annotation, CoordMetaMixin):
    """
    A 3D spline.
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
    id: str = Field(default=..., description="""Unique identifier for this entity""")
    annotation_type: Literal[AnnotationType.spline_3D] = Field(
        default=AnnotationType.spline_3D, description="""The type of annotation."""
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    source_tomogram_id: Optional[str] = Field(
        default=None,
        description="""ID of the tomogram from which this annotation was derived, such as the tomogram containing picked coordinates.""",
    )


class DensityMap(Annotation, AssociatedFile, Image3D):
    """
    A density map fit into a volume.
    """

    matrix3D: Optional[Annotated[list[Matrix3x3], Field(min_length=1)]] = Field(
        default=None,
        description="""Rotation matrix associated with a point on a 3D image (Nx3x3).""",
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
    path: Optional[str] = Field(default=None, description="""Path to a file.""")
    id: str = Field(default=..., description="""Unique identifier for this entity""")
    annotation_type: Literal[AnnotationType.density_map] = Field(
        default=AnnotationType.density_map, description="""The type of annotation."""
    )
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    source_tomogram_id: Optional[str] = Field(
        default=None,
        description="""ID of the tomogram from which this annotation was derived, such as the tomogram containing picked coordinates.""",
    )


class Instrument(ConfiguredBaseModel):
    """
    A microscope/instrument used to acquire data. Physical, rarely-changing hardware.
    """

    id: str = Field(default=..., description="""Unique identifier for this entity""")
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    microscope_model: Optional[str] = Field(
        default=None,
        description="""Manufacturer/model of the microscope, e.g. \"Titan Krios G4\".""",
    )
    voltage: Optional[float] = Field(
        default=None, description="""Acceleration voltage of the microscope in kV."""
    )
    electron_source: Optional[ElectronSource] = Field(
        default=None, description="""Type of electron source."""
    )
    detector_model: Optional[str] = Field(
        default=None, description="""Manufacturer/model of the detector/camera."""
    )


class AcquisitionSession(ConfiguredBaseModel):
    """
    Parameters constant within one data-collection session; links to the Instrument used.
    """

    id: str = Field(default=..., description="""Unique identifier for this entity""")
    name: Optional[str] = Field(
        default=None, description="""A human-readable name or title for this entity"""
    )
    instrument_id: Optional[str] = Field(
        default=None,
        description="""ID of the Instrument used for this acquisition session.""",
    )
    dose_rate: Optional[float] = Field(
        default=None,
        description="""Dose rate on the specimen during acquisition in e-/A^2/s (pre-specimen fluence).""",
    )
    detector_dose_rate: Optional[float] = Field(
        default=None,
        description="""Dose rate at the detector in e-/pixel/s (post-specimen; counting-mode calibration).""",
    )
    amplitude_contrast: Optional[float] = Field(
        default=None,
        description="""Amplitude contrast fraction (dimensionless, typically 0.07-0.1). CTF-model parameter.""",
    )
    spherical_aberration: Optional[float] = Field(
        default=None,
        description="""Spherical aberration (Cs) of the objective lens in mm.""",
    )


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
                    SphereSet,
                    CircleSet,
                    CylinderSet,
                    CuboidSet,
                    BoxSet,
                    Spline2D,
                    Spline3D,
                    DensityMap,
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
        default=None, description="""A human-readable name or title for this entity"""
    )
    particle_maps: Optional[list[ParticleMap]] = Field(
        default=[], description="""The particle maps"""
    )


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
        default=None, description="""A human-readable name or title for this entity"""
    )
    instruments: Optional[list[Instrument]] = Field(
        default=[], description="""The instruments used in this dataset."""
    )
    acquisition_sessions: Optional[list[AcquisitionSession]] = Field(
        default=[], description="""The acquisition sessions in this dataset."""
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
SamplingDescriptor.model_rebuild()
GridSampling.model_rebuild()
ParticleSampling.model_rebuild()
HeldoutSampling.model_rebuild()
NonRigidChannels.model_rebuild()
NonRigidAlignment.model_rebuild()
NativeParameter.model_rebuild()
NativeArtifact.model_rebuild()
ProcessingProvenance.model_rebuild()
TiltAngleObservation.model_rebuild()
ProjectionExclusion.model_rebuild()
FrameAlignment.model_rebuild()
MovieAlignment.model_rebuild()
PointAttribute.model_rebuild()
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
AssociatedFile.model_rebuild()
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
SphereSet.model_rebuild()
CircleSet.model_rebuild()
CylinderSet.model_rebuild()
CuboidSet.model_rebuild()
BoxSet.model_rebuild()
Spline2D.model_rebuild()
Spline3D.model_rebuild()
DensityMap.model_rebuild()
Instrument.model_rebuild()
AcquisitionSession.model_rebuild()
Region.model_rebuild()
Average.model_rebuild()
MovieStackCollection.model_rebuild()
Dataset.model_rebuild()
