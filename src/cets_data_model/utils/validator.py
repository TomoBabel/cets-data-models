"""Check the ids and references of a serialized CETS dataset.

Ids are unique within a class: two tilt images cannot share an id, but a tilt
image and a tomogram can. A ``target_id`` names an entity of any class; the
typed reference fields must name an entity of their own class.

Usage: ``python -m cets_data_model.utils.validator dataset.json [...]``
"""

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from cets_data_model.models.models import Dataset

#: Reference field -> the class its value must name.
TYPED_REFERENCES = {
    "movie_stack_id": "MovieStack",
    "movie_stack_series_id": "MovieStackSeries",
    "tilt_series_id": "TiltSeries",
}


def _entities(node: Any, path: str = ""):
    """Yield ``(path, model)`` for every model in a validated document."""
    if isinstance(node, BaseModel):
        yield path or "<root>", node
        for name in type(node).model_fields:
            yield from _entities(getattr(node, name), f"{path}.{name}")
    elif isinstance(node, list):
        for index, item in enumerate(node):
            yield from _entities(item, f"{path}[{index}]")


def validate(filepath: str | Path) -> dict[str, list[tuple[str, str]]]:
    """Return the reference errors of a dataset file, by kind.

    The file must be a valid ``Dataset``. The result maps an error kind
    (``duplicate_id``, ``Unresolved <field>``, ``Wrong type``) to
    ``(value, path)`` pairs, and is empty for a consistent dataset.
    """
    document = Dataset.model_validate(json.loads(Path(filepath).read_text()))
    ids: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    references: list[tuple[str, str, str]] = []
    for path, entity in _entities(document):
        if getattr(entity, "id", None) is not None:
            ids[type(entity).__name__][str(entity.id)].append(path)
        for field in ("target_id", *TYPED_REFERENCES):
            value = getattr(entity, field, None)
            if value is not None:
                references.append((field, str(value), path))

    errors: dict[str, list[tuple[str, str]]] = {}
    for class_name, values in ids.items():
        for value, paths in values.items():
            if len(paths) > 1:
                errors.setdefault("duplicate_id", []).append(
                    (f"{class_name}: {value!r}", ", ".join(paths))
                )
    known = {value for values in ids.values() for value in values}
    for field, value, path in references:
        if value not in known:
            errors.setdefault(f"Unresolved {field}", []).append((value, path))
        elif field in TYPED_REFERENCES and value not in ids[TYPED_REFERENCES[field]]:
            errors.setdefault("Wrong type", []).append((f"{field}: {value!r}", path))
    return errors


def main(paths: list[str]) -> int:
    if not paths:
        print("Usage: python -m cets_data_model.utils.validator <dataset.json> [...]")
        return 1
    status = 0
    for path in paths:
        errors = validate(path)
        if errors:
            status = 1
            print(f"Errors found in {path}")
            for kind, items in errors.items():
                print(kind)
                for item in items:
                    print(f"  {item}")
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
