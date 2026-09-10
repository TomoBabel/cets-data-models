"""First-class non-rigid schema, compatibility and reference semantics."""
import copy
import json
import subprocess
import sys

import jsonschema
import pytest
from pydantic import ValidationError

from cets_data_model.models import models as m
from cets_data_model.utils.references import document_to_dict, validate_document_references


def descriptor(**changes):
    values = dict(profile_version="cets-nonrigid/0.1", kind="tilt-series-projection-residual",
                  tilt_image_ids=["im0", "im1"], payload_uri="data.nonrigid.zarr", payload_group="alignments/a",
                  sampling=m.GridSampling(grid_shape=[3, 3, 2]),
                  heldout=m.HeldoutSampling(method="scrambled-sobol", seed=20260828, count=64),
                  channels=m.NonRigidChannels(displacement_3d="zero_at_samples", ctf_depth="none"),
                  context_digest="0" * 64, digest_version=1)
    values.update(changes)
    return m.NonRigidAlignment(**values)


def document():
    return m.Dataset(regions=[m.Region(id="r", tilt_series=[m.TiltSeries(id="ts", images=[
        m.TiltImage(id="im0"), m.TiltImage(id="im1")])], tomograms=[m.Tomogram(id="v", path=None)],
        alignments=[m.Alignment(id="a", tilt_series_id="ts", reference_volume_id="v", non_rigid_alignment=descriptor())])])


def test_presence_is_derived_and_zero_component_is_present():
    owner = m.Alignment()
    assert not owner.has_non_rigid_alignment
    owner.non_rigid_alignment = descriptor()
    assert owner.has_non_rigid_alignment
    assert "has_non_rigid_alignment" not in owner.model_dump()
    assert "has_non_rigid_alignment" not in owner.model_json_schema()["properties"]
    assert m.MovieAlignment().has_non_rigid_alignment is False
    with pytest.raises(ValidationError):
        m.Alignment(has_non_rigid_alignment=True)


def test_old_rigid_document_optionality_and_null_reference_path():
    assert m.Alignment().tilt_series_id is None
    assert m.Alignment().projection_alignments == []
    data = document()
    validate_document_references(data)
    assert data.regions[0].tomograms[0].path is None
    restored = m.Dataset.model_validate_json(json.dumps(document_to_dict(data)))
    validate_document_references(restored)


@pytest.mark.parametrize("field,value", [("profile_version", "cets-nonrigid/99"), ("context_digest", "bad"),
                                        ("digest_version", 2), ("kind", "extension")])
def test_pydantic_and_json_schema_reject_invalid_descriptors(field, value):
    value_dict = descriptor().model_dump(mode="json")
    value_dict[field] = value
    with pytest.raises(ValidationError):
        m.NonRigidAlignment.model_validate(value_dict)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(value_dict, m.NonRigidAlignment.model_json_schema())


def test_grid_shape_constrains_items_and_array_length():
    for shape in ([3, -1, 2], [0, 2], [2], [1, 2, 3, 4]):
        with pytest.raises(ValidationError):
            m.GridSampling(grid_shape=shape)
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate({"kind": "grid", "grid_shape": shape}, m.GridSampling.model_json_schema())


def test_particle_sampling_has_a_scalar_discriminated_type():
    nr = descriptor(sampling=m.ParticleSampling(annotation_id="p"),
                    heldout=m.HeldoutSampling(method="particle-subset", seed=7, count=0))
    restored = m.NonRigidAlignment.model_validate_json(nr.model_dump_json())
    assert isinstance(restored.sampling, m.ParticleSampling)
    jsonschema.validate(nr.model_dump(mode="json"), m.NonRigidAlignment.model_json_schema())


def test_reference_checks_reject_dangling_or_incomplete_row_ids():
    data = document()
    data.regions[0].alignments[0].reference_volume_id = "missing"
    with pytest.raises(ValueError, match="reference volume"):
        validate_document_references(data)
    data = document()
    data.regions[0].alignments[0].non_rigid_alignment.tilt_image_ids = ["im0"]
    with pytest.raises(ValueError, match="every owning image"):
        validate_document_references(data)


def test_activity_belongs_to_each_alignment():
    data = document()
    first = data.regions[0].alignments[0]
    first.exclusions = [m.ProjectionExclusion(tilt_image_id="im0", reason="dark")]
    second = m.Alignment(id="b", tilt_series_id="ts", reference_volume_id="v",
                         projection_alignments=[m.ProjectionAlignment(id="p", tilt_image_id="im0")])
    data.regions[0].alignments.append(second)
    validate_document_references(data)
    first.projection_alignments = copy.deepcopy(second.projection_alignments)
    with pytest.raises(ValueError, match="excluded image"):
        validate_document_references(data)


def test_unset_legacy_ctf_handedness_does_not_become_known_on_serialization():
    ctf = m.CTFMetadata(defocus_u=12000)
    assert "defocus_handedness" not in document_to_dict(ctf)
    restored = m.CTFMetadata.model_validate(document_to_dict(ctf))
    assert "defocus_handedness" not in restored.model_fields_set
    assert document_to_dict(m.CTFMetadata(defocus_handedness=1))["defocus_handedness"] == 1


def test_core_import_has_no_numerical_backend_dependency():
    script = "from cets_data_model.models.models import Alignment; import sys; assert not ({'torch','warpylib','cets_nonrigid'} & set(sys.modules)); assert not Alignment().has_non_rigid_alignment"
    subprocess.run([sys.executable, "-c", script], check=True)
