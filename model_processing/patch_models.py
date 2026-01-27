import re
import sys
import yaml
from pathlib import Path


def load_patch_config_yaml():
    config_path = Path(__file__).parent / "patch_config.yaml"
    with open(config_path, "r") as f:
        config_yaml = yaml.safe_load(f)

    return config_yaml


def patch_discriminated_unions(model_def: str, unions: list) -> str:
    if not unions:
        return model_def

    print(f"Patching {len(unions)} discriminated union fields...")

    for union_config in unions:
        field_name = union_config["field_name"]
        discriminator = union_config["discriminator"]
        for_classes = union_config.get("for_classes", None)

        if for_classes:
            print(
                f"  - Patching field '{field_name}' in classes {for_classes} "
                f"with discriminator '{discriminator}'"
            )
        else:
            print(
                f"  - Patching field '{field_name}' (all classes) "
                f"with discriminator '{discriminator}'"
            )

        model_def = patch_field_with_union(
            model_def,
            union_config["field_name"],
            union_config["discriminator"],
            union_config.get("union_types", []),
            union_config.get("for_classes", None),
        )

    return model_def


def patch_field_with_union(
    model_def: str,
    field_name: str,
    discriminator: str,
    union_types: list[str],
    for_classes: list[str] | None = None,
) -> str:
    """
    Before: field_name: Optional[list[BaseClass]] ...
    After:  field_name: Optional[list[Annotated[Union[Type1, Type2, ...], Field(discriminator="...")]]] = None

    Args:
        model_def: The model definition string
        field_name: Name of the field to patch
        discriminator: Discriminator field name
        union_types: List of types to include in the union
        for_classes: Optional list of class names to restrict patching to.
                     If None, patches all occurrences of the field.
    """

    if for_classes is None:
        return _patch_field_global(model_def, field_name, discriminator, union_types)
    else:
        return _patch_field_in_classes(
            model_def, field_name, discriminator, union_types, for_classes
        )


def _patch_field_global(
    model_def: str, field_name: str, discriminator: str, union_types: list[str]
) -> str:
    """Patch field globally (all classes) - original behavior"""
    pattern = rf"({field_name}:\s*Optional\[list\[)(\w+)(\]\])"

    if not union_types:
        # If no union_types specified, just wrap the existing type with Annotated
        replacement = rf'\1Annotated[\2, Field(discriminator="{discriminator}")]\3'
        return re.sub(pattern, replacement, model_def)

    union_str = "Union[" + ", ".join(union_types) + "]"
    replacement = rf'\1Annotated[{union_str}, Field(discriminator="{discriminator}")]\3'

    return re.sub(pattern, replacement, model_def)


def _patch_field_in_classes(
    model_def: str,
    field_name: str,
    discriminator: str,
    union_types: list[str],
    class_names: list[str],
) -> str:
    """Patch field only in specified classes"""
    lines = model_def.split("\n")

    # Track which class we're currently in
    current_class = None
    patched_count = 0

    for i, line in enumerate(lines):
        # Detect class definition
        class_match = re.match(r"^class (\w+)\(", line)
        if class_match:
            current_class = class_match.group(1)
            continue

        # Reset current class when we dedent back to module level
        if current_class and line and not line[0].isspace():
            current_class = None
            continue

        # Only process if we're in one of the target classes
        if current_class not in class_names:
            continue

        # Look for the field pattern
        pattern = rf"(\s*)({field_name}:\s*Optional\[list\[)(\w+)(\]\])"
        match = re.search(pattern, line)

        if match:
            indent = match.group(1)
            field_prefix = match.group(2)
            base_type = match.group(3)
            field_suffix = match.group(4)

            if union_types:
                union_str = "Union[" + ", ".join(union_types) + "]"
                new_type = (
                    f'Annotated[{union_str}, Field(discriminator="{discriminator}")]'
                )
            else:
                # Just wrap existing type
                new_type = (
                    f'Annotated[{base_type}, Field(discriminator="{discriminator}")]'
                )

            # Reconstruct the line
            rest_of_line = line[match.end() :]
            lines[i] = f"{indent}{field_prefix}{new_type}{field_suffix}{rest_of_line}"
            patched_count += 1
            print(
                f"    ✓ Patched '{field_name}' in class '{current_class}' (line {i + 1})"
            )

    if patched_count == 0:
        print(f"    ⚠ Warning: Field '{field_name}' not found in classes {class_names}")

    return "\n".join(lines)


def patch_discriminator_fields_to_literal(model_def: str, unions: list) -> str:
    """
    Convert discriminator fields from Enum types to Literal types in subclasses.

    Base class: transformation_type: EnumType = Field(default=..., ...)  [leave as-is]
    Subclasses: transformation_type: EnumType = Field(default=EnumType.value, ...)
    Convert to: transformation_type: Literal[EnumType.value] = Field(EnumType.value, ...)
    """

    if not unions:
        return model_def

    discriminators = {field["discriminator"] for field in unions}

    print(f"Converting discriminator fields to Literal: {', '.join(discriminators)}")

    for discriminator in discriminators:
        lines = model_def.split("\n")
        for i, line in enumerate(lines):
            if f"{discriminator}: " in line and " = Field(" in line:
                # Skip base class (has default=...)
                if "default=..." in line:
                    continue

                # Match: transformation_type: TransformationType = Field(default=TransformationType.identity, ...)
                match = re.search(
                    rf"{discriminator}: (\w+) = Field\(default=(\w+\.\w+)", line
                )
                if match:
                    enum_type = match.group(1)  # TransformationType
                    enum_value = match.group(2)  # TransformationType.identity

                    # Replace: EnumType with Literal[EnumType.value] and remove default=
                    old_pattern = (
                        f"{discriminator}: {enum_type} = Field(default={enum_value}"
                    )
                    new_pattern = (
                        f"{discriminator}: Literal[{enum_value}] = Field({enum_value}"
                    )

                    if old_pattern in line:
                        lines[i] = line.replace(old_pattern, new_pattern)
                        print(
                            f"  - Converted {discriminator} from {enum_type} to Literal on line {i}"
                        )

        model_def = "\n".join(lines)

    return model_def


def add_type_aliases(model_def: str, aliases: list[dict]) -> str:
    """
    Add TypeAlias definitions from config and substitute them in matching fields.
    """

    if not aliases:
        return model_def

    print(f"Processing {len(aliases)} type aliases...")

    alias_lines = ["\n# Type aliases"]
    for alias in aliases:
        alias_lines.append(f"{alias['name']}: TypeAlias = {alias['definition']}")

    alias_block = "\n".join(alias_lines) + "\n\n"

    insertion_point = model_def.find("\nmetamodel_version = ")
    if insertion_point != -1:
        model_def = (
            model_def[:insertion_point] + alias_block + model_def[insertion_point:]
        )

    for alias in aliases:
        if "for_field" not in alias:
            continue

        alias_name = alias["name"]
        for_field = alias["for_field"]

        if isinstance(for_field, dict):
            as_list_fields = for_field.get("as_list", [])
            as_single_fields = for_field.get("as_single", [])

            for field_name in as_list_fields:
                model_def = substitute_field_type(
                    model_def, field_name, alias_name, as_list=True
                )

            for field_name in as_single_fields:
                model_def = substitute_field_type(
                    model_def, field_name, alias_name, as_list=False
                )
        else:
            for field_name in for_field:
                model_def = substitute_field_type(
                    model_def, field_name, alias_name, as_list=True
                )

    return model_def


def substitute_field_type(
    model_def: str, field_name: str, alias_name: str, as_list: bool
) -> str:
    """
    Substitute a field's type with a type alias.

    Args:
        model_def: The model definition string
        field_name: Name of the field to replace
        alias_name: Name of the type alias to use
        as_list: If True, wraps in list with min_length=1. If False, uses alias directly.

    Returns:
        Updated model definition
    """
    test_pattern = f"{field_name}: Optional[conlist"

    if test_pattern not in model_def:
        print(f"  x Substring not found for '{field_name}'")
        return model_def

    print(f"  - Found substring '{test_pattern}' for {field_name} (as_list={as_list})")

    lines = model_def.split("\n")
    count = 0

    for i, line in enumerate(lines):
        if test_pattern in line:
            # Find where the type annotation ends (at )] = )
            end_marker = ")] = Field"
            if end_marker in line:
                start = line.find(f"{field_name}: Optional[")
                end = line.find(end_marker) + 1  # Include the ]

                if start != -1 and end != -1:
                    before = line[:start]
                    after = line[end:]

                    if as_list:
                        # Wrap in list with min_length constraint
                        new_type = f"{field_name}: Optional[Annotated[list[{alias_name}], Field(min_length=1)]"
                    else:
                        # Use alias directly (single value)
                        new_type = f"{field_name}: Optional[{alias_name}"

                    lines[i] = before + new_type + after
                    count += 1

    model_def = "\n".join(lines)
    print(f"  - Replaced {count} occurrence(s) of '{field_name}' (as_list={as_list})")

    return model_def


def ensure_typing_imports(model_def: str) -> str:
    """
    Ensure Annotated, Union, TypeAlias, and Literal are in the typing imports.
    """

    typing_section = model_def.split("from pydantic import")[0]

    needs_annotated = "Annotated" not in typing_section
    needs_union = "Union" not in typing_section
    needs_typealias = "TypeAlias" not in typing_section
    needs_literal = "Literal" not in typing_section

    if not (needs_annotated or needs_union or needs_typealias or needs_literal):
        return model_def

    pattern = r"from typing import \((.*?)\)"
    match = re.search(pattern, model_def, re.DOTALL)

    if not match:
        print("Warning: Could not find typing imports")
        return model_def

    imports_to_add = []
    if needs_annotated:
        imports_to_add.append("    Annotated")
    if needs_union:
        imports_to_add.append("    Union")
    if needs_typealias:
        imports_to_add.append("    TypeAlias")
    if needs_literal:
        imports_to_add.append("    Literal")

    old_block = match.group(0)
    new_block = old_block.rstrip("\n)").rstrip(",")
    new_block += ",\n" + ",\n".join(imports_to_add) + "\n)"

    model_def = model_def.replace(old_block, new_block, 1)

    return model_def


def remove_treat_empty_lists_serializer(model_def: str) -> str:
    """
    Remove the treat_empty_lists_as_none model_serializer method that causes mypy errors.
    This is a LinkML-generated method that we don't need.
    """

    print("Removing treat_empty_lists_as_none serializer...")

    lines = model_def.split("\n")
    new_lines = []
    skip = False

    for i, line in enumerate(lines):
        if (
            "@model_serializer(mode=" in line
            and i + 1 < len(lines)
            and "treat_empty_lists_as_none" in lines[i + 1]
        ):
            skip = True
            print(f"  - Found serializer at line {i}, removing...")
            continue

        if skip and "return handler(_instance, info)" in line:
            skip = False
            continue

        if not skip:
            new_lines.append(line)

    return "\n".join(new_lines)


def patch_models(input_path: Path, output_path: Path) -> None:
    model_def = input_path.read_text()
    patch_config = load_patch_config_yaml()

    model_def = ensure_typing_imports(model_def)
    model_def = remove_treat_empty_lists_serializer(model_def)

    for title, config in patch_config.items():
        if title == "type_aliases":
            model_def = add_type_aliases(model_def, config)
        if title == "discriminated_fields":
            model_def = patch_discriminated_unions(model_def, config)
            model_def = patch_discriminator_fields_to_literal(model_def, config)

    output_path.write_text(model_def)

    discriminated_union_field_names = [
        f["field_name"] for f in patch_config.get("discriminated_fields", [])
    ]
    type_alias_names = [a["name"] for a in patch_config.get("type_aliases", [])]
    print(f"Patched {input_path} -> {output_path}")
    print(f"Added type aliases for: {', '.join(type_alias_names)}")
    print(
        f"Added discriminated unions for: {', '.join(discriminated_union_field_names)}"
    )


def main():
    if len(sys.argv) < 3:
        print("Usage: patch_models.py <input_file> <output_file>")
        print("Example: patch_models.py gen_models.py models.py")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])

    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    patch_models(input_file, output_file)


if __name__ == "__main__":
    main()
