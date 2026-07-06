"""
Validation script for CETS dataset JSON files.

Checks:
  1. All `id` fields are unique across all objects in the document.
  2. All `target_id` fields refer to an `id` that actually exists.
  3. Typed reference fields refer to an `id` that exists on the correct object type:
       - `movie_stack_id`        -> MovieStack       (lives under "stacks")
       - `movie_stack_series_id` -> MovieStackSeries (lives under "movie_stacks")
       - `tilt_series_id`        -> TiltSeries       (lives under "tilt_series")
"""

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Tuple


# Maps reference field name -> the parent_key that identifies the expected object type
TYPED_REFS: dict[str, str] = {
    "movie_stack_id": "stacks",
    "movie_stack_series_id": "movie_stacks",
    "tilt_series_id": "tilt_series",
}

# Human-readable type names for error messages
TYPE_NAMES: dict[str, str] = {
    "stacks": "MovieStack",
    "movie_stacks": "MovieStackSeries",
    "tilt_series": "TiltSeries",
}


def collect(
    obj: object,
    parent_key: str = "",
    path: str = "",
    ids: dict[str, list[str]] | None = None,
    ids_by_parent_key: dict[str, set[str]] | None = None,
    target_ids: list[tuple[str, str]] | None = None,
    typed_refs: list[tuple[str, str, str]] | None = None,
) -> tuple[
    Dict[str, list[str]],
    Dict[str, set[str]],
    List[tuple[str, str]],
    List[tuple[str, str, str]],
]:
    """
    Recursively walk the parsed JSON, collecting:
      ids:               {id_value -> [paths]}
      ids_by_parent_key: {parent_key -> {id_values}}  — for type checking
      target_ids:        [(value, path)]
      typed_refs:        [(field_name, value, path)]
    """
    if ids is None:
        ids = defaultdict(list)
    if ids_by_parent_key is None:
        ids_by_parent_key = defaultdict(set)
    if target_ids is None:
        target_ids = []
    if typed_refs is None:
        typed_refs = []

    if isinstance(obj, dict):
        if "id" in obj and obj["id"] is not None:
            id_val = str(obj["id"])
            ids[id_val].append(path or "<root>")
            ids_by_parent_key[parent_key].add(id_val)

        if "target_id" in obj and obj["target_id"] is not None:
            target_ids.append((str(obj["target_id"]), path or "<root>"))

        for field, expected_parent_key in TYPED_REFS.items():
            if field in obj and obj[field] is not None:
                typed_refs.append((field, str(obj[field]), path or "<root>"))

        for key, value in obj.items():
            collect(
                value,
                key,
                f"{path}.{key}",
                ids,
                ids_by_parent_key,
                target_ids,
                typed_refs,
            )

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            collect(
                item,
                parent_key,
                f"{path}[{i}]",
                ids,
                ids_by_parent_key,
                target_ids,
                typed_refs,
            )

    return ids, ids_by_parent_key, target_ids, typed_refs


def validate(filepath: str | Path) -> Dict[str, List[Tuple[str, str]]]:
    path = Path(filepath)

    with open(path) as f:
        data = json.load(f)

    ids, ids_by_parent_key, target_ids, typed_refs = collect(data)

    errors: Dict[str, List[Tuple[str, str]]] = {}
    known_ids = set(ids.keys())

    # 1. Duplicate ids
    for id_value, paths in ids.items():
        if len(paths) > 1:
            errors.setdefault("duplicate_id", []).append((id_value, ", ".join(paths)))

    # 2. Unresolved target_ids
    for target_id_value, ref_path in target_ids:
        if target_id_value not in known_ids:
            errors.setdefault("Unresolved target_id", []).append(
                (target_id_value, ref_path)
            )

    # 3. Typed reference fields — must exist and point to the correct object type
    for field, ref_value, ref_path in typed_refs:
        expected_parent_key = TYPED_REFS[field]

        if ref_value not in known_ids:
            errors.setdefault(f"Unresolved {field}", []).append((ref_value, ref_path))

        elif ref_value not in ids_by_parent_key[expected_parent_key]:
            errors.setdefault("Wrong type", []).append(
                (f"{field}: {ref_value!r}", ref_path)
            )
    return errors


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_dataset.py <dataset.json> [<dataset2.json> ...]")
        sys.exit(1)
    return_code = 0
    for f in sys.argv[1:]:
        results = validate(f)
        if results:
            print(f"Errors found in {f}")
            return_code = 1
            for res in results:
                print(res)
                for error_item in results[res]:
                    print(f"  {error_item}")
    sys.exit(return_code)
