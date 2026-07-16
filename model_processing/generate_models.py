"""Generate the CETS Pydantic models from the LinkML schema.

Replaces both the raw ``gen-pydantic`` CLI call *and* the former regex
post-processor (``patch_models.py``). All model transformations are applied at
generation time via LinkML's object model + documented lifecycle hooks (operating
on the generator's ``PydanticClass`` / ``PydanticAttribute`` template objects
rather than post-processing generated text). A ``CETSPydanticGenerator`` subclass:

  * injects hand-written mixin base classes (Pixel/VoxelSizeMixin) into Image2D/3D;
  * wraps discriminated-union fields in ``Annotated[Union[...], Field(discriminator=...)]``;
  * converts subclass discriminator fields to ``Literal[...]``;
  * substitutes constrained-array fields with reusable type aliases.

Module-level type-alias definitions and required imports are supplied via the
generator's ``injected_classes`` / ``imports`` params; the ``treat_empty_lists_as_none``
serializer is dropped via a serializer-free ``base_model.py.jinja`` template override.
Everything is driven by ``patch_config.yaml`` (same config the regex patcher used).

Writes the formatted module to the path given as argv[1] (default:
``src/cets_data_model/models/generated_models.py``).
"""

import subprocess
import sys
from pathlib import Path

import yaml
from linkml.generators.pydanticgen import PydanticGenerator
from linkml.generators.pydanticgen.array import ArrayRepresentation
from linkml.generators.pydanticgen.template import Import, Imports, ObjectImport

HERE = Path(__file__).parent
CONFIG_PATH = HERE / "patch_config.yaml"
SCHEMA_PATH = HERE.parent / "schema" / "linkml" / "entities.yaml"
TEMPLATE_DIR = HERE / "templates"
DEFAULT_OUTPUT = HERE.parent / "src" / "cets_data_model" / "models" / "generated_models.py"

CONFIG = yaml.safe_load(CONFIG_PATH.read_text()) or {}

# --- base-class (mixin) injection registry ---------------------------------
INJECT_MAP: dict[str, list[str]] = {}       # class name -> [mixin names]
MIXIN_IMPORTS: dict[str, list[str]] = {}    # module -> [mixin names]
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
ALIAS_DEFS: list[str] = []          # module-level "Name: TypeAlias = ..." lines
ALIAS_SUB: dict[str, str] = {}      # field name -> replacement range string
for _alias in CONFIG.get("type_aliases", []) or []:
    ALIAS_DEFS.append(f"{_alias['name']}: TypeAlias = {_alias['definition']}")
    _ff = _alias.get("for_field") or {}
    _as_list = _ff.get("as_list", []) if isinstance(_ff, dict) else list(_ff)
    _as_single = _ff.get("as_single", []) if isinstance(_ff, dict) else []
    for _f in _as_list or []:
        ALIAS_SUB[_f] = f"Optional[Annotated[list[{_alias['name']}], Field(min_length=1)]]"
    for _f in _as_single or []:
        ALIAS_SUB[_f] = f"Optional[{_alias['name']}]"


class CETSPydanticGenerator(PydanticGenerator):
    """PydanticGenerator that applies all CETS transforms via ``after_generate_class``."""

    def after_generate_class(self, cls, sv):
        c = cls.cls

        # 1) base-class (mixin) injection
        mixins = INJECT_MAP.get(c.name)
        if mixins:
            bases = [c.bases] if isinstance(c.bases, str) else list(c.bases)
            c.bases = list(mixins) + [b for b in bases if b not in mixins]

        for name, attr in (c.attributes or {}).items():
            # 2) constrained-array field -> reusable type alias
            if name in ALIAS_SUB:
                attr.range = ALIAS_SUB[name]

            # 3) discriminated-union field (honor `for_classes` scoping)
            for d in DISC_FIELDS:
                if d["field_name"] == name:
                    for_classes = d.get("for_classes")
                    if for_classes is None or c.name in for_classes:
                        attr.range = _discriminated_range(d["discriminator"], d["union_types"])

            # 4) discriminator field in a *subclass* -> Literal[...]
            #    subclasses carry a concrete enum default via `predefined`; the
            #    abstract base has `default=...` (required) -> `predefined` unset -> skip.
            if name in DISCRIMINATORS and attr.predefined and attr.predefined not in ("...", "[]", "None"):
                attr.range = f"Literal[{attr.predefined}]"

        return cls


def _build_imports() -> Imports:
    imports = Imports()
    # typing names our injected type strings rely on (LinkML doesn't emit these)
    imports = imports + Import(
        module="typing",
        objects=[ObjectImport(name="Annotated"), ObjectImport(name="TypeAlias")],
    )
    for module, names in MIXIN_IMPORTS.items():
        imports = imports + Import(module=module, objects=[ObjectImport(name=n) for n in names])
    return imports


def build_generator() -> CETSPydanticGenerator:
    return CETSPydanticGenerator(
        str(SCHEMA_PATH),
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
    try:
        subprocess.run(
            ["ruff", "check", "--select", "I,F401", "--fix", str(path)],
            capture_output=True, text=True, check=True,
        )
        subprocess.run(["ruff", "format", str(path)], capture_output=True, text=True, check=True)
    except FileNotFoundError:
        print("WARNING: ruff not found; output left unformatted", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"WARNING: ruff failed: {e.stderr}", file=sys.stderr)


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
