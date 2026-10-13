"""Reference validation of serialized datasets."""

from pathlib import Path

from cets_data_model.utils.validator import validate

DATA = Path(__file__).parent / "test_data"


def test_expected_dataset_has_consistent_ids_and_references():
    assert validate(DATA / "expected_dataset.json") == {}


def test_reference_errors_are_reported_by_kind():
    assert validate(DATA / "expected_dataset_with_errors.json") == {
        "duplicate_id": [
            (
                "TiltImage: 'tilt_image_01'",
                ".regions[0].tilt_series[0].images[0], "
                ".regions[0].tilt_series[0].images[1]",
            )
        ],
        "Unresolved movie_stack_series_id": [
            ("no such series", ".regions[0].tilt_series[0]")
        ],
        "Unresolved target_id": [
            (
                "non-existent target",
                ".regions[0].alignments[0].projection_alignments[1]",
            )
        ],
        "Wrong type": [
            ("movie_stack_id: 'tomogram_01'", ".regions[0].tilt_series[0].images[0]")
        ],
    }
