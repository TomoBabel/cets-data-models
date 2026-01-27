import json
import pytest
from pathlib import Path
from pydantic import ValidationError

from cets_data_model.models.patched_models import (
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
        assert len(region.annotations) == 7  # All annotation types

    def test_expected_dataset_annotations(self, expected_dataset_path):
        """Verify all annotation types are present"""
        with open(expected_dataset_path) as f:
            data = json.load(f)

        dataset = Dataset(**data)
        region = dataset.regions[0]

        annotation_types = {ann.annotation_type for ann in region.annotations}

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
            annotation_type="point_set_3D",
            path="/data/particles.star",
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
                annotation_type="point_set_3D",
                origin3D=[],  # Empty list not allowed
            )

        # Should work with one point
        ps = PointSet3D(annotation_type="point_set_3D", origin3D=[[1.0, 2.0, 3.0]])
        assert len(ps.origin3D) == 1
