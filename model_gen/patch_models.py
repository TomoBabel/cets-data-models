import re
import sys
import yaml
from pathlib import Path


def load_patch_config_yaml():

    config_path = Path(__file__).parent / "patch_config.yaml"
    with open(config_path, 'r') as f:
        config_yaml = yaml.safe_load(f)

    return config_yaml


def patch_discriminated_unions(model_def: str, unions: list) -> str:

    if not unions:
        return model_def

    for union_config in unions:
        print(f"  - Patching field '{union_config['field_name']}' with discriminator '{union_config['discriminator']}'")
        model_def = patch_field_with_union(
            model_def,
            union_config["field_name"],
            union_config["discriminator"],
            union_config.get("union_types", [])
        )
    
    return model_def


def patch_field_with_union(
    model_def: str, 
    field_name: str, 
    discriminator: str, 
    union_types: list[str]
) -> str:
    """
    Before: field_name: Optional[list[BaseClass]] ...
    After:  field_name: Optional[list[Annotated[Union[Type1, Type2, ...], Field(discriminator="...")]]] = None
    """

    pattern = rf'({field_name}:\s*Optional\[list\[)(\w+)(\]\])'

    if not union_types:
        # If no union_types specified, just wrap the existing type with Annotated
        replacement = rf'\1Annotated[\2, Field(discriminator="{discriminator}")]\3'
        return re.sub(pattern, replacement, model_def)
    
    union_str = "Union[" + ", ".join(union_types) + "]"
    replacement = rf'\1Annotated[{union_str}, Field(discriminator="{discriminator}")]\3'
    
    return re.sub(pattern, replacement, model_def)


def add_type_aliases(model_def: str, aliases: list[dict]) -> str:
    """
    Add TypeAlias definitions from config and substitute them in matching fields.
    """
    
    if not aliases:
        return model_def
    
    print(f"Processing {len(aliases)} type aliases...")
    
    # Step 1: Add the TypeAlias definitions
    alias_lines = ["\n# Type aliases"]
    for alias in aliases:
        alias_lines.append(f"{alias['name']}: TypeAlias = {alias['definition']}")
    
    alias_block = '\n'.join(alias_lines) + '\n\n'
    
    insertion_point = model_def.find('\nmetamodel_version = ')
    if insertion_point != -1:
        model_def = model_def[:insertion_point] + alias_block + model_def[insertion_point:]
    
    # Step 2: Substitute type aliases in fields
    for alias in aliases:
        if 'for_field' not in alias:
            continue
            
        field_names = alias['for_field']
        alias_name = alias['name']
        
        for field_name in field_names:
            test_pattern = f'{field_name}: Optional[conlist'
            if test_pattern in model_def:
                print(f"  - Found substring '{test_pattern}' for {field_name}")
                
                lines = model_def.split('\n')
                count = 0
                for i, line in enumerate(lines):
                    if test_pattern in line:
                        # Find where the type annotation ends (at )] = )
                        end_marker = ')] = Field'
                        if end_marker in line:
                            start = line.find(f'{field_name}: Optional[')
                            end = line.find(end_marker) + 1  # Include the ]
                            
                            if start != -1 and end != -1:
                                before = line[:start]
                                after = line[end:]
                                new_type = f'{field_name}: Optional[Annotated[list[{alias_name}], Field(min_length=1)]'
                                lines[i] = before + new_type + after
                                count += 1
                
                model_def = '\n'.join(lines)
                print(f"  - Replaced {count} occurrence(s) of '{field_name}'")
            else:
                print(f"  x Substring not found for '{field_name}'")
    
    return model_def


def ensure_typing_imports(model_def: str) -> str:
    """
    Ensure Annotated, Union, and TypeAlias are in the typing imports.
    """
    
    typing_section = model_def.split('from pydantic import')[0]
    
    needs_annotated = 'Annotated' not in typing_section
    needs_union = 'Union' not in typing_section
    needs_typealias = 'TypeAlias' not in typing_section 
    
    if not (needs_annotated or needs_union or needs_typealias):
        return model_def
    
    pattern = r'from typing import \((.*?)\)'
    match = re.search(pattern, model_def, re.DOTALL)
    
    if not match:
        print("Warning: Could not find typing imports")
        return model_def
    
    imports_to_add = []
    if needs_annotated:
        imports_to_add.append('    Annotated')
    if needs_union:
        imports_to_add.append('    Union')
    if needs_typealias:
        imports_to_add.append('    TypeAlias')
    
    old_block = match.group(0)
    new_block = old_block.rstrip('\n)').rstrip(',')
    new_block += ',\n' + ',\n'.join(imports_to_add) + '\n)'
    
    model_def = model_def.replace(old_block, new_block, 1)
    
    return model_def


def patch_models(input_path: Path, output_path: Path) -> None:
    
    model_def = input_path.read_text()
    patch_config = load_patch_config_yaml()

    model_def = ensure_typing_imports(model_def)

    for title, config in patch_config.items():
        if title == "type_aliases":
            model_def = add_type_aliases(model_def, config)
        if title == "discriminated_fields":
            model_def = patch_discriminated_unions(model_def, config)
    
    output_path.write_text(model_def)
    
    discriminated_union_field_names = [f["field_name"] for f in patch_config.get("discriminated_fields", [])]
    type_alias_names = [a["name"] for a in patch_config.get("type_aliases", [])]
    print(f"Patched {input_path} -> {output_path}")
    print(f"Added type aliases for: {', '.join(type_alias_names)}")
    print(f"Added discriminated unions for: {', '.join(discriminated_union_field_names)}")


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
