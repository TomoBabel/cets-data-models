import json
import pytest
from pathlib import Path
from pydantic import ValidationError

from cets_data_model.models.models import (
    Dataset,
    Region,
    MovieFrame,
    Tomogram,
    CoordinateSystem,
    Axis,
    Translation,
    Scale,
    Affine,
    Sequence,
    PointSet3D,
    ParticleMap,
    Average,
    AnnotatedObject,
    SegmentationLabel,
    SegmentationMask3D,
    ProbabilityMap3D,
    Spline3D,
    SegmentedFeatureType,
)


# ============================================================================
# 1. EXPECTED DATASET VALIDATION TESTS
# ============================================================================


class TestExpectedDatasetValidation:
    """Test that reference datasets remain valid against current schema"""

    @pytest.fixture
    def expected_dataset_path(self):
        return Path(__file__).parent / "test_data" / "expected_dataset.json"

    def test_expected_dataset_loads_successfully(self, expected_dataset_path):
        """Expected dataset should load without validation errors"""
        with open(expected_dataset_path) as f:
            data = json.load(f)

        # Will raise ValidationError if schema breaks compatibility
        dataset = Dataset(**data)

        # Basic sanity checks about structure/features of dataset
        assert dataset.name == "example_cets_dataset"
        assert len(dataset.regions) == 1
        assert len(dataset.averages) == 1

    def test_expected_dataset_structure(self, expected_dataset_path):
        """Verify expected structure of expected dataset"""
        with open(expected_dataset_path) as f:
            data = json.load(f)

        dataset = Dataset(**data)
        region = dataset.regions[0]

        # Verify region has all expected components
        assert region.id == "region_01"
        assert region.movie_stack_collection is not None
        assert len(region.tilt_series) == 1
        assert len(region.alignments) == 1
        assert len(region.tomograms) == 1
        assert len(region.annotations) == 7

    def test_expected_dataset_annotations(self, expected_dataset_path):
        """Verify all annotation types are present"""
        with open(expected_dataset_path) as f:
            data = json.load(f)

        dataset = Dataset(**data)
        region = dataset.regions[0]

        annotation_types = {ann.annotation_type for ann in region.annotations}
        annotation_ids = {ann.id for ann in region.annotations}

        # TODO: add new annotation types
        expected_types = {
            "point_set_3D",
            "point_vector_set_3D",
            "point_matrix_set_3D",
            "segmentation_mask_3D",
            "probability_map_3D",
            "point_set_2D",
            "tri_mesh",
        }

        assert annotation_types == expected_types
        assert "ribosome_picks" in annotation_ids
        assert region.annotations[0].source_tomogram_id == "tomogram_01"

        average = dataset.averages[0]
        assert average.particle_maps[0].source_region_id == "region_01"
        assert average.particle_maps[0].source_annotation_id == "ribosome_picks"

    def test_expected_dataset_transformations(self, expected_dataset_path):
        """Verify transformation types are present"""
        with open(expected_dataset_path) as f:
            data = json.load(f)

        dataset = Dataset(**data)
        region = dataset.regions[0]

        # Check alignment transformations
        proj_align = region.alignments[0].projection_alignments[0]
        assert len(proj_align.sequence) == 2
        assert proj_align.sequence[0].transformation_type == "translation"
        assert proj_align.sequence[1].transformation_type == "affine"

        # Check coordinate transformations on images
        tilt_image = region.tilt_series[0].images[0]
        if tilt_image.coordinate_transformations:
            assert (
                tilt_image.coordinate_transformations[0].transformation_type == "scale"
            )


# ============================================================================
# 2. ROUND-TRIP SERIALIZATION TESTS
# ============================================================================


class TestRoundTripSerialization:
    """Test that data survives serialization/deserialization unchanged"""

    def test_dataset_roundtrip_json(self):
        """Dataset should survive JSON round-trip unchanged"""
        original = Dataset(
            name="test_dataset",
            regions=[
                Region(
                    id="region_test",
                    tomograms=[
                        Tomogram(
                            id="tomo_test",
                            path="/data/tomo.mrc",
                            width=512,
                            height=512,
                            depth=256,
                        )
                    ],
                )
            ],
        )

        # Serialize and deserialize
        json_str = original.model_dump_json()
        reconstructed = Dataset.model_validate_json(json_str)

        # Should be identical
        assert original.model_dump() == reconstructed.model_dump()

    def test_annotation_roundtrip(self):
        """Annotations should survive round-trip with all fields"""
        original = PointSet3D(
            id="particle_coords_annotation",
            annotation_type="point_set_3D",
            source_tomogram_id="tomogram_01",
            origin3D=[[100.0, 200.0, 300.0], [150.0, 250.0, 350.0]],
            coordinate_systems=[
                CoordinateSystem(
                    name="particle_coords",
                    axes=[
                        Axis(name="x", axis_unit="angstrom", axis_type="space"),
                        Axis(name="y", axis_unit="angstrom", axis_type="space"),
                        Axis(name="z", axis_unit="angstrom", axis_type="space"),
                    ],
                )
            ],
        )

        json_str = original.model_dump_json()
        reconstructed = PointSet3D.model_validate_json(json_str)

        assert original.model_dump() == reconstructed.model_dump()
        assert len(reconstructed.origin3D) == 2
        assert reconstructed.coordinate_systems[0].name == "particle_coords"
        assert reconstructed.source_tomogram_id == "tomogram_01"

    def test_particle_map_coordinate_reference_roundtrip(self):
        """Particle maps should preserve links to source annotations"""
        original = ParticleMap(
            path="/data/subtomograms/particle_001.mrc",
            source_region_id="region_01",
            source_annotation_id="ribosome_picks",
            coord_index=3,
            width=64,
            height=64,
            depth=64,
        )

        json_str = original.model_dump_json()
        reconstructed = ParticleMap.model_validate_json(json_str)

        assert reconstructed.source_region_id == "region_01"
        assert reconstructed.source_annotation_id == "ribosome_picks"
        assert reconstructed.coord_index == 3

    def test_average_without_source_annotations_roundtrip(self):
        """Averages may contain particle maps without source annotation links"""
        original = Average(
            name="subtomograms_only",
            particle_maps=[
                ParticleMap(
                    path="/data/subtomograms/particle_001.mrc",
                    width=64,
                    height=64,
                    depth=64,
                )
            ],
        )

        json_str = original.model_dump_json()
        reconstructed = Average.model_validate_json(json_str)

        assert len(reconstructed.particle_maps) == 1
        assert reconstructed.particle_maps[0].source_region_id is None
        assert reconstructed.particle_maps[0].source_annotation_id is None
        assert reconstructed.particle_maps[0].coord_index is None

    def test_transformation_sequence_roundtrip(self):
        """Complex transformation sequences should survive round-trip"""
        original = Sequence(
            transformation_type="sequence",
            name="multi_step_transform",
            input="coord_a",
            output="coord_c",
            sequence=[
                Translation(
                    transformation_type="translation", translation=[10.0, 20.0, 30.0]
                ),
                Scale(transformation_type="scale", scale=[2.0, 2.0, 2.0]),
                Affine(
                    transformation_type="affine",
                    affine=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                ),
            ],
        )

        json_str = original.model_dump_json()
        reconstructed = Sequence.model_validate_json(json_str)

        assert len(reconstructed.sequence) == 3
        assert reconstructed.sequence[0].transformation_type == "translation"
        assert reconstructed.sequence[1].transformation_type == "scale"
        assert reconstructed.sequence[2].transformation_type == "affine"


# ============================================================================
# 3. CONSTRAINT VALIDATION TESTS
# ============================================================================


class TestConstraintValidation:
    """Test that invalid data is properly rejected"""

    def test_reject_invalid_vector_dimensions(self):
        """3D vectors must have exactly 3 elements"""
        with pytest.raises(ValidationError):
            PointSet3D(
                id="bad_point_set",
                annotation_type="point_set_3d",
                origin3D=[[1.0, 2.0]],  # Missing z coordinate
            )

    def test_reject_invalid_matrix_dimensions(self):
        """3x3 matrices must have correct shape"""
        with pytest.raises(ValidationError):
            Affine(
                transformation_type="affine",
                affine=[
                    [1.0, 0.0],  # Only 2 elements, should be 3
                    [0.0, 1.0],
                ],
            )

    def test_section_must_be_integer(self):
        """Section field must be integer, not string"""
        # This is valid
        frame = MovieFrame(
            path="/data/frame.tif",
            section=0,  # Integer
            width=4096,
            height=4096,
        )
        assert frame.section == 0
        assert isinstance(frame.section, int)

        # Note: Pydantic might coerce "0" to 0, so test with invalid string
        with pytest.raises(ValidationError):
            MovieFrame(
                path="/data/frame.tif", section="not_a_number", width=4096, height=4096
            )

    def test_affine_is_single_matrix_not_list(self):
        """Affine should accept single 3x3 matrix, not list of matrices"""
        # Correct format: single matrix
        affine = Affine(
            transformation_type="affine",
            affine=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        )
        assert len(affine.affine) == 3
        assert len(affine.affine[0]) == 3

        # This should fail (list of matrices)
        with pytest.raises(ValidationError):
            Affine(
                transformation_type="affine",
                affine=[
                    [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                    [[2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 2.0]],
                ],
            )

    def test_vector_list_length_constraints(self):
        """Point sets must have at least one point"""
        with pytest.raises(ValidationError):
            PointSet3D(
                id="empty_point_set",
                annotation_type="point_set_3D",
                origin3D=[],  # Empty list not allowed
            )

        # Should work with one point
        ps = PointSet3D(
            id="single_point_set",
            annotation_type="point_set_3D",
            origin3D=[[1.0, 2.0, 3.0]],
        )
        assert len(ps.origin3D) == 1


# ============================================================================
# 4. SEGMENTATION EXTENSIONS TESTS
# ============================================================================


MEMBRANE = {"feature_type": "membrane"}


class TestSegmentationExtensions:
    """Test the semantic/instance segmentation metadata (masks, probability maps and
    instance-grouped points)"""

    def test_legacy_annotations_still_valid(self):
        """Annotations without any of the new optional fields must keep validating"""
        mask = SegmentationMask3D(id="mask", path="mask.mrc")
        points = PointSet3D(id="points", origin3D=[[1.0, 2.0, 3.0]])
        assert mask.segmentation_type is None
        assert mask.labels == []  # multivalued fields default to an empty list
        assert points.instance_ids is None
        assert points.annotated_object is None

    def test_semantic_mask_with_labels_roundtrip(self):
        """A multi-class semantic mask keeps the meaning of each label value"""
        region = Region(
            id="region_01",
            annotations=[
                {
                    "id": "semantic_mask",
                    "annotation_type": "segmentation_mask_3D",
                    "path": "TS_01_semantic.mrc",
                    "source_tomogram_id": "TS_01",
                    "segmentation_type": "semantic",
                    "labels": [
                        {"label_value": 1, "annotated_object": MEMBRANE},
                        {
                            "label_value": 2,
                            "annotated_object": {"feature_type": "microtubule"},
                        },
                    ],
                }
            ],
        )
        reconstructed = Region.model_validate_json(region.model_dump_json())
        mask = reconstructed.annotations[0]
        assert isinstance(mask, SegmentationMask3D)
        assert mask.segmentation_type == "semantic"
        assert [label.label_value for label in mask.labels] == [1, 2]
        assert mask.labels[0].annotated_object.feature_type == "membrane"
        assert mask.labels[1].annotated_object.feature_type == "microtubule"

    def test_instance_mask_derived_from_another_annotation(self):
        """An instance (connected components) mask can point to the mask it derives from"""
        mask = SegmentationMask3D(
            id="instances",
            path="TS_01_instances.mrc",
            segmentation_type="instance",
            annotated_object=AnnotatedObject(**MEMBRANE),
            derived_from_annotation_id="semantic_mask",
        )
        reconstructed = SegmentationMask3D.model_validate_json(mask.model_dump_json())
        assert reconstructed == mask
        assert (
            reconstructed.annotated_object.feature_type == SegmentedFeatureType.membrane
        )

    def test_probability_map_value_type_and_threshold(self):
        """Probability maps record the kind of values and the segmentation threshold"""
        scores = ProbabilityMap3D(
            id="scores", path="TS_01_scores.mrc", value_type="logit", threshold=0.0
        )
        reconstructed = ProbabilityMap3D.model_validate_json(scores.model_dump_json())
        assert reconstructed.value_type == "logit"
        assert reconstructed.threshold == 0.0

    def test_point_set_grouped_into_instances(self):
        """Points of several instances (e.g. membranes) fit in a single PointSet3D"""
        points = PointSet3D(
            id="membrane_points",
            origin3D=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [5.0, 5.0, 5.0]],
            instance_ids=[0, 0, 1],
            annotated_object=AnnotatedObject(**MEMBRANE),
        )
        reconstructed = PointSet3D.model_validate_json(points.model_dump_json())
        assert reconstructed.instance_ids == [0, 0, 1]

    def test_spline_set_grouped_into_instances(self):
        """Several filaments fit in a single Spline3D, one spline per instance id"""
        splines = Spline3D(
            id="microtubules",
            origin3D=[[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [9.0, 0.0, 0.0]],
            instance_ids=[3, 3, 7],
            annotated_object=AnnotatedObject(
                feature_type=SegmentedFeatureType.microtubule
            ),
        )
        reconstructed = Spline3D.model_validate_json(splines.model_dump_json())
        assert reconstructed.instance_ids == [3, 3, 7]

    def test_reject_invalid_segmentation_metadata(self):
        """Invalid enum values, untyped objects and empty/non-integer ids are rejected"""
        with pytest.raises(ValidationError):
            SegmentationMask3D(id="mask", segmentation_type="panoptic")
        with pytest.raises(ValidationError):
            ProbabilityMap3D(id="scores", value_type="percentage")
        with pytest.raises(ValidationError):
            AnnotatedObject(name="membrane")  # feature_type is required
        with pytest.raises(ValidationError):
            AnnotatedObject(feature_type="lipid_droplet")  # not a SegmentedFeatureType
        with pytest.raises(ValidationError):
            AnnotatedObject(feature_type="membrane", ontology_id="membrane")  # removed
        with pytest.raises(ValidationError):
            SegmentationLabel(label_value=1)  # annotated_object is required
        with pytest.raises(ValidationError):
            PointSet3D(id="points", origin3D=[[1.0, 2.0, 3.0]], instance_ids=[])
        with pytest.raises(ValidationError):
            PointSet3D(id="points", origin3D=[[1.0, 2.0, 3.0]], instance_ids=[0.5])

    def test_other_feature_type_described_by_name(self):
        """Objects without a specific SegmentedFeatureType are annotated as other + name"""
        obj = AnnotatedObject(feature_type="other", name="lipid droplet")
        reconstructed = AnnotatedObject.model_validate_json(obj.model_dump_json())
        assert reconstructed.feature_type == SegmentedFeatureType.other
        assert reconstructed.name == "lipid droplet"
        assert obj.model_dump(mode="json")["feature_type"] == "other"
