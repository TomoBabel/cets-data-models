"""Generate the CETS Pydantic models from the LinkML schema.

Replaces both the raw ``gen-pydantic`` CLI call *and* the former regex
post-processor (``patch_models.py``). All model transformations are applied at
generation time via LinkML's object model + documented lifecycle hooks (operating
on the generator's ``PydanticClass`` / ``PydanticAttribute`` template objects
rather than post-processing generated text). A ``CETSPydanticGenerator`` subclass:

  * injects configured hand-written mixin base classes;
  * wraps discriminated-union fields in ``Annotated[Union[...], Field(discriminator=...)]``;
  * converts subclass discriminator fields to ``Literal[...]``;
  * substitutes constrained-array fields with reusable type aliases;
  * preserves exact square-matrix alternatives declared with ``any_of``.

Module-level type-alias definitions and required imports are supplied via the
generator's ``injected_classes`` / ``imports`` params; the ``treat_empty_lists_as_none``
serializer is dropped via a serializer-free ``base_model.py.jinja`` template override.
Mixin and alias configuration comes from ``patch_config.yaml``; matrix shapes
come directly from the LinkML schema.

Writes the formatted module to the path given as argv[1] (default:
``src/cets_data_model/models/generated_models.py``).
"""

import subprocess
import sys
from pathlib import Path

import yaml
from linkml.generators.pydanticgen import PydanticGenerator
from linkml.generators.pydanticgen.array import ArrayRepresentation, ArrayValidator
from linkml.generators.pydanticgen.template import Import, Imports, ObjectImport

HERE = Path(__file__).parent
CONFIG_PATH = HERE / "patch_config.yaml"
SCHEMA_PATH = HERE.parent / "schema" / "linkml" / "entities.yaml"
TEMPLATE_DIR = HERE / "templates"
DEFAULT_OUTPUT = (
    HERE.parent / "src" / "cets_data_model" / "models" / "generated_models.py"
)

CONFIG = yaml.safe_load(CONFIG_PATH.read_text()) or {}

# --- base-class (mixin) injection registry ---------------------------------
INJECT_MAP: dict[str, list[str]] = {}  # class name -> [mixin names]
MIXIN_IMPORTS: dict[str, list[str]] = {}  # module -> [mixin names]
for _entry in CONFIG.get("injected_base_classes", []) or []:
    MIXIN_IMPORTS.setdefault(_entry["import_from"], []).append(_entry["mixin"])
    for _cname in _entry["into"]:
        INJECT_MAP.setdefault(_cname, []).append(_entry["mixin"])

# --- discriminated unions --------------------------------------------------
DISC_FIELDS = CONFIG.get("discriminated_fields", []) or []
DISCRIMINATORS = {d["discriminator"] for d in DISC_FIELDS}


def _discriminated_range(discriminator: str, union_types: list[str]) -> str:
    union = "Union[" + ", ".join(union_types) + "]"
    return f'Optional[list[Annotated[{union}, Field(discriminator="{discriminator}")]]]'


# --- type aliases ----------------------------------------------------------
ALIAS_DEFS: list[str] = []  # module-level "Name: TypeAlias = ..." lines
ALIAS_SUB: dict[str, str] = {}  # field name -> replacement range string
for _alias in CONFIG.get("type_aliases", []) or []:
    ALIAS_DEFS.append(f"{_alias['name']}: TypeAlias = {_alias['definition']}")
    _ff = _alias.get("for_field") or {}
    _as_list = _ff.get("as_list", []) if isinstance(_ff, dict) else list(_ff)
    _as_single = _ff.get("as_single", []) if isinstance(_ff, dict) else []
    for _f in _as_list or []:
        ALIAS_SUB[_f] = (
            f"Optional[Annotated[list[{_alias['name']}], Field(min_length=1)]]"
        )
    for _f in _as_single or []:
        ALIAS_SUB[_f] = f"Optional[{_alias['name']}]"


class CETSPydanticGenerator(PydanticGenerator):
    """PydanticGenerator that applies all CETS transforms via ``after_generate_class``."""

    def _matrix_union_range(self, slot, source_class):
        """Compile exact square array alternatives that LinkML 1.11.1 drops.

        Sizes come from the schema, not the alias registry. Restrict this hook to
        shape-only alternatives; unsupported constraints must not disappear.
        """
        if slot.multivalued or (
            slot.array is not None
            and (
                slot.array.dimensions
                or slot.array.exact_number_dimensions not in (None, 2)
                or slot.array.minimum_number_dimensions is not None
                or slot.array.maximum_number_dimensions is not None
            )
        ):
            raise ValueError(f"{slot.name}: put matrix dimensions inside any_of")
        scalar = self.generate_python_range(slot.range, slot, source_class)
        ranges = []
        for option in slot.any_of:
            array = option.array
            if any(
                value not in (None, [], {})
                for key, value in vars(option).items()
                if key != "array"
            ):
                raise ValueError(
                    f"{slot.name}: matrix alternatives must contain only array"
                )
            if (
                array is None
                or array.exact_number_dimensions != 2
                or len(array.dimensions) != 2
            ):
                raise ValueError(
                    f"{slot.name}: expected exact two-dimensional matrix alternatives"
                )
            sizes = [dimension.exact_cardinality for dimension in array.dimensions]
            if sizes[0] is None or sizes[0] <= 0 or sizes[0] != sizes[1]:
                raise ValueError(
                    f"{slot.name}: expected exact square matrix alternatives"
                )
            # Reuse LinkML's validation of contradictory dimension constraints.
            ArrayValidator.validate(array)
            size = sizes[0]
            row = f"Annotated[list[{scalar}], Field(min_length={size}, max_length={size})]"
            ranges.append(
                f"Annotated[list[{row}], Field(min_length={size}, max_length={size})]"
            )
        union = "Union[" + ", ".join(dict.fromkeys(ranges)) + "]"
        return (
            union
            if slot.required or slot.identifier or slot.key
            else f"Optional[{union}]"
        )

    def after_generate_class(self, cls, sv):
        c = cls.cls
        slots = {
            slot.alias or slot.name: slot
            for slot in sv.class_induced_slots(cls.source.name)
        }

        # 1) base-class (mixin) injection
        mixins = INJECT_MAP.get(c.name)
        if mixins:
            bases = [c.bases] if isinstance(c.bases, str) else list(c.bases)
            c.bases = list(mixins) + [b for b in bases if b not in mixins]

        for name, attr in (c.attributes or {}).items():
            # 2) schema matrix alternatives take precedence over fixed aliases.
            slot = slots[attr.alias or name]
            if any(option.array is not None for option in slot.any_of):
                attr.range = self._matrix_union_range(slot, cls.source)
            elif name in ALIAS_SUB:
                attr.range = ALIAS_SUB[name]

            # 3) discriminated-union field (honor `for_classes` scoping)
            for d in DISC_FIELDS:
                if d["field_name"] == name:
                    for_classes = d.get("for_classes")
                    if for_classes is None or c.name in for_classes:
                        attr.range = _discriminated_range(
                            d["discriminator"], d["union_types"]
                        )

            # 4) discriminator field in a *subclass* -> Literal[...]
            #    subclasses carry a concrete enum default via `predefined`; the
            #    abstract base has `default=...` (required) -> `predefined` unset -> skip.
            if (
                name in DISCRIMINATORS
                and attr.predefined
                and attr.predefined not in ("...", "[]", "None")
            ):
                attr.range = f"Literal[{attr.predefined}]"

        return cls


def _build_imports() -> Imports:
    imports = Imports()
    # typing names our injected type strings rely on (LinkML doesn't emit these)
    imports = imports + Import(
        module="typing",
        objects=[
            ObjectImport(name="Annotated"),
            ObjectImport(name="TypeAlias"),
            ObjectImport(name="Union"),
        ],
    )
    for module, names in MIXIN_IMPORTS.items():
        imports = imports + Import(
            module=module, objects=[ObjectImport(name=n) for n in names]
        )
    return imports


def build_generator(schema_path: Path = SCHEMA_PATH) -> CETSPydanticGenerator:
    return CETSPydanticGenerator(
        str(schema_path),
        # match the `gen-pydantic --meta None` CLI construction
        array_representations=[ArrayRepresentation.LIST],
        extra_fields="forbid",
        emit_metadata=True,
        genmeta=False,
        gen_classvars=True,
        gen_slots=True,
        black=False,
        metadata_mode="None",
        # keep `[]` defaults for optional multivalued slots (downstream relies on it)
        empty_list_for_multivalued_slots=True,
        # serializer-free base model (drops treat_empty_lists_as_none)
        template_dir=str(TEMPLATE_DIR),
        # module-level type-alias definitions + the imports they/the unions need
        # (joined into one block so they render grouped, not blank-line-separated)
        injected_classes=["\n".join(ALIAS_DEFS)] if ALIAS_DEFS else None,
        imports=_build_imports(),
    )


def _format_with_ruff(path: Path) -> None:
    """Sort/prune imports and format (replaces the former patch step's ruff pass)."""
    subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--select",
            "I,F401",
            "--fix",
            str(path),
        ],
        check=True,
    )
    subprocess.run([sys.executable, "-m", "ruff", "format", str(path)], check=True)


def _validate(path: Path) -> None:
    """Fail loudly if the generated module is not valid / importable."""
    import ast
    import importlib.util

    ast.parse(path.read_text())  # syntax
    spec = importlib.util.spec_from_file_location("cets_generated_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # imports + model_rebuild resolve


def main() -> None:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    out_path.write_text(build_generator().serialize())
    _format_with_ruff(out_path)
    try:
        _validate(out_path)
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: generated models failed validation: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Generated models validated -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
