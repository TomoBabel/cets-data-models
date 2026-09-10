"""Document reference checks shared by producers and consumers; no numerical backend."""
from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel


def document_to_dict(value: Any) -> Any:
    """Serialize ordinary core models without materializing an unknown legacy CTF hand.

    Discriminator defaults remain serialized. Only the historical, unspecified
    CTFMetadata.defocus_handedness default is suppressed when it was not supplied.
    """
    if isinstance(value, BaseModel):
        return {
            name: document_to_dict(getattr(value, name))
            for name in type(value).model_fields
            if getattr(value, name) is not None
            and not (
                type(value).__name__ == "CTFMetadata"
                and name == "defocus_handedness"
                and name not in value.model_fields_set
            )
        }
    if isinstance(value, dict):
        return {key: document_to_dict(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [document_to_dict(item) for item in value]
    return getattr(value, "value", value)


def _index(items, label):
    result = {}
    for item in items or []:
        key = getattr(item, "id", None)
        if key is None:
            continue
        if not key or key in result:
            raise ValueError(f"{label}: empty or duplicate id {key!r}")
        result[key] = item
    return result


def _reference(key, index, label, required=False):
    if key is None and not required:
        return None
    if key is None or key not in index:
        raise ValueError(f"{label}: unresolved reference {key!r}")
    return index[key]


def _unique(values, label):
    if any(not isinstance(v, str) or not v for v in values) or len(values) != len(set(values)):
        raise ValueError(f"{label}: identities must be nonempty and unique")


def _provenance(provenance):
    if provenance is None:
        return
    _unique([p.name for p in provenance.parameters or []], "native parameter names")
    for parameter in provenance.parameters or []:
        try:
            json.loads(parameter.value_json, parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"native parameter {parameter.name!r} is not finite JSON") from exc


def _descriptor(owner, rows, annotations, kind):
    descriptor = owner.non_rigid_alignment
    if descriptor is None:
        return
    if not owner.id:
        raise ValueError("an alignment with a non-rigid component requires an id")
    if descriptor.kind != kind:
        raise ValueError(f"alignment kind requires {kind!r}")
    ids = descriptor.tilt_image_ids if kind == "tilt-series-projection-residual" else owner.frame_ids
    _unique(ids or [], "payload row ids")
    if len(ids or []) != len(rows) or set(ids or []) != set(rows):
        raise ValueError("payload row ids must contain every owning image exactly once")
    if kind == "movie-frame-residual" and descriptor.tilt_image_ids:
        raise ValueError("movie descriptors use the parent frame_ids; tilt_image_ids must be absent")
    sampling = descriptor.sampling
    if sampling.kind == "grid":
        ndim = 3 if kind == "tilt-series-projection-residual" else 2
        if len(sampling.grid_shape) != ndim:
            raise ValueError(f"{kind} requires a {ndim}D sampling grid")
        if descriptor.heldout.method not in {"scrambled-sobol", "none"}:
            raise ValueError("grid held-out observations must use scrambled Sobol")
    else:
        if kind != "tilt-series-projection-residual":
            raise ValueError("particle sampling is a tilt-series capability")
        annotation = _reference(sampling.annotation_id, annotations, "sampling annotation", True)
        if annotation.annotation_type != "point_set_3D":
            raise ValueError("particle sampling requires a PointSet3D")
        point_ids = annotation.point_ids or []
        _unique(point_ids, "point ids")
        if not point_ids or len(point_ids) != len(annotation.origin3D or []):
            raise ValueError("particle point ids must match the annotation coordinate count")
        if annotation.source_tomogram_id != owner.reference_volume_id:
            raise ValueError("sampled point set must identify the alignment reference tomogram")
        if descriptor.heldout.method not in {"particle-subset", "none"}:
            raise ValueError("particle held-out observations must be a particle subset")
        _unique([a.name for a in annotation.point_attributes or []], "point attribute names")
        for attribute in annotation.point_attributes or []:
            columns = [attribute.numeric_values, attribute.string_values, attribute.boolean_values]
            populated = [v for v in columns if v]
            if len(populated) != 1 or len(populated[0]) != len(point_ids):
                raise ValueError(f"point attribute {attribute.name!r} requires one value per point")
    if descriptor.heldout.count and descriptor.heldout.method == "none":
        raise ValueError("heldout method none requires count zero")


def validate_document_references(document, *, processing: bool = False) -> None:
    """Check supplied IDs; processing additionally requires usable alignment bindings.

    Optional unbound fields in ordinary rigid documents remain valid. Numerical
    shape, frame and payload checks belong to the processing package.
    """
    instruments = _index(document.instruments, "instruments")
    sessions = _index(document.acquisition_sessions, "acquisition sessions")
    for session in sessions.values():
        _reference(session.instrument_id, instruments, "session instrument")
    _index(document.regions, "regions")
    for region in document.regions or []:
        series = _index(region.tilt_series, "tilt series")
        volumes = _index(region.tomograms, "tomograms")
        alignments = _index(region.alignments, "alignments")
        annotations = _index(region.annotations, "annotations")
        stacks = {}
        collection = region.movie_stack_collection
        for stack_series in (collection.movie_stacks or []) if collection is not None else []:
            _reference(stack_series.acquisition_session_id, sessions, "movie acquisition session")
            for key, stack in _index(stack_series.stacks, "movie stacks").items():
                if key in stacks:
                    raise ValueError(f"duplicate movie stack id {key!r}")
                stacks[key] = stack
        for ts in series.values():
            _reference(ts.acquisition_session_id, sessions, "tilt acquisition session")
            _index(ts.images, "tilt images")
            if ts.defocus_handedness == 0:
                raise ValueError("defocus handedness is +1, -1 or null, never zero")
            for image in ts.images or []:
                _reference(image.movie_stack_id, stacks, "tilt image movie stack")
                ctf = image.ctf_metadata
                if ctf is not None and "defocus_handedness" in ctf.model_fields_set:
                    hand = ctf.defocus_handedness
                    if hand is not None and ts.defocus_handedness is not None and hand != ts.defocus_handedness:
                        raise ValueError("explicit image and series CTF handedness disagree")
        for alignment in region.alignments or []:
            required = processing or alignment.non_rigid_alignment is not None
            ts = _reference(alignment.tilt_series_id, series, "alignment tilt series", required)
            _reference(alignment.reference_volume_id, volumes, "alignment reference volume", required)
            _provenance(alignment.provenance)
            if ts is None:
                continue
            images = _index(ts.images, "tilt images")
            projection_ids = []
            for projection in alignment.projection_alignments or []:
                _reference(projection.tilt_image_id, images, "projection image", required)
                if projection.tilt_image_id is not None:
                    projection_ids.append(projection.tilt_image_id)
            _unique(projection_ids, "projection image associations")
            for observation in alignment.tilt_angle_observations or []:
                _reference(observation.tilt_image_id, images, "source angle image", True)
            for exclusion in alignment.exclusions or []:
                _reference(exclusion.tilt_image_id, images, "excluded image", True)
                if exclusion.tilt_image_id in projection_ids:
                    raise ValueError("an excluded image cannot also have a projection alignment")
            _descriptor(alignment, images, annotations, "tilt-series-projection-residual")
        for volume in volumes.values():
            _reference(volume.alignment_id, alignments, "tomogram producing alignment")
            _reference(volume.tilt_series_id, series, "tomogram tilt series")
            _provenance(volume.provenance)
        for stack in stacks.values():
            frames = _index(stack.images, "movie frames")
            _index(stack.alignments, "movie alignments")
            for alignment in stack.alignments or []:
                if alignment.movie_stack_id != stack.id:
                    raise ValueError("movie alignment must reference its owning stack")
                _unique(alignment.frame_ids or [], "movie frame ids")
                if set(alignment.frame_ids or []) != set(frames) or len(frames) != len(stack.images or []):
                    raise ValueError("movie frame ids must cover every enumerated frame")
                associations = [frame.frame_id for frame in alignment.frame_alignments or []]
                _unique(associations, "frame alignment associations")
                for frame in alignment.frame_alignments or []:
                    _reference(frame.frame_id, frames, "frame alignment image", True)
                if alignment.gauge == "reference-frame":
                    _reference(alignment.reference_frame_id, frames, "reference frame", True)
                elif alignment.reference_frame_id is not None:
                    raise ValueError("native-origin gauge must not specify a reference frame")
                _provenance(alignment.provenance)
                _descriptor(alignment, frames, annotations, "movie-frame-residual")
