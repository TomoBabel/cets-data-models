"""
Post-process generated Pydantic models to add discriminators and fix imports.
"""
import re
import sys
from pathlib import Path


def ensure_imports(content, imports_needed):
    """
    Ensure specific imports are present in the typing import statement.
    Handles both single-line and multi-line import formats.
    
    Args:
        content: The file content
        imports_needed: List of import names to ensure (e.g., ['Annotated', 'Literal'])
    
    Returns:
        Updated content with imports added
    """

    multiline_pattern = r'(from typing import\s*)(\([^)]+\))'
    singleline_pattern = r'(from typing import )([^\n]+)'
    
    multiline_match = re.search(multiline_pattern, content, re.DOTALL)
    if multiline_match:
        
        prefix = multiline_match.group(1)  
        paren_content = multiline_match.group(2)  
        inner_content = paren_content.strip('()').strip()
        
        existing_imports = [i.strip().rstrip(',') for i in inner_content.split('\n') if i.strip()]
        for import_name in imports_needed:
            if not any(import_name == imp.rstrip(',') for imp in existing_imports):
                existing_imports.append(import_name)
        
        formatted_imports = ',\n    '.join(existing_imports)
        replacement = f'{prefix}(\n    {formatted_imports}\n)'
        content = content.replace(multiline_match.group(0), replacement)
        
    else:

        def add_imports(match):
            prefix = match.group(1)
            existing_imports = match.group(2)
            imports_list = [i.strip() for i in existing_imports.split(',')]
            
            for import_name in imports_needed:
                if import_name not in imports_list:
                    imports_list.append(import_name)
            
            return f'{prefix}{", ".join(imports_list)}'
        
        content = re.sub(singleline_pattern, add_imports, content, count=1)
    
    return content


def fix_base_class_literal(content, class_name, field_name, literal_value, original_type):
    """
    Fix a base class to use Literal for its discriminator field.
    
    Args:
        content: The file content
        class_name: Name of the class to fix (e.g., 'Annotation')
        field_name: Name of the field to fix (e.g., 'type')
        literal_value: The literal value to use (e.g., 'annotation')
        original_type: The original type to replace (e.g., 'AnnotationTypeEnum')
    
    Returns:
        Updated content
    """
    # Pattern: class ClassName(...): ... field_name: OriginalType = Field(...)
    pattern = rf'(class {class_name}\([^)]+\):.*?)({field_name}: {original_type})(\s*=\s*Field\([^)]*\))'
    
    def replace_field(match):
        class_start = match.group(1)
        new_field = f'{field_name}: Literal["{literal_value}"]'
        field_def = match.group(3)
        return f'{class_start}{new_field}{field_def}'
    
    content = re.sub(pattern, replace_field, content, flags=re.DOTALL)
    return content


def add_discriminator_to_union(content, union_type_pattern, discriminator_field='type'):
    """
    Add Field(discriminator='...') to Union fields matching a pattern.
    
    Args:
        content: The file content
        union_type_pattern: Regex pattern to match the Union type (e.g., 'Annotation')
        discriminator_field: The field name to use as discriminator (default: 'type')
    
    Returns:
        Tuple of (updated_content, number_of_changes, list_of_modified_fields)
    """
    changes = 0
    modified_fields = []
    
    # Pattern to capture class name and field name
    # Matches: class ClassName(...): ... field_name: Optional[list[Union[...]]]
    class_field_pattern = rf'class\s+(\w+)\([^)]*\):.*?(\w+):\s*Optional\[list\[Union\[[^\]]*{union_type_pattern}[^\]]*\]\]\]'
    
    for match in re.finditer(class_field_pattern, content, re.DOTALL):
        class_name = match.group(1)
        field_name = match.group(2)
        modified_fields.append(f"{class_name}.{field_name}")
    
    # Handle Optional[list[Union[Pattern, ...]]]
    pattern = rf'(:\s*Optional\[list\[)(Union\[[^\]]*{union_type_pattern}[^\]]*\])(\]\])'
    
    def replace_union(match):
        nonlocal changes
        prefix = match.group(1)
        union_content = match.group(2)
        suffix = match.group(3)
        changes += 1
        return f'{prefix}Annotated[{union_content}, Field(discriminator="{discriminator_field}")]{suffix}'
    
    content = re.sub(pattern, replace_union, content)
    
    # Handle list[Union[Pattern, ...]]
    pattern_non_optional = rf'(:\s*list\[)(Union\[[^\]]*{union_type_pattern}[^\]]*\])(\])'
    
    def replace_union_non_optional(match):
        nonlocal changes
        prefix = match.group(1)
        union_content = match.group(2)
        suffix = match.group(3)
        changes += 1
        return f'{prefix}Annotated[{union_content}, Field(discriminator="{discriminator_field}")]{suffix}'
    
    content = re.sub(pattern_non_optional, replace_union_non_optional, content)
    
    return content, changes, modified_fields


def process_models(file_path):
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    total_changes = 0
    
    print(f"Processing {file_path}...")
    print()
    
    # 1. Fix Annotation base class to use Literal
    print("1. Fixing Annotation base class type field...")
    content = fix_base_class_literal(
        content,
        class_name='Annotation',
        field_name='type',
        literal_value='annotation',
        original_type='AnnotationTypeEnum'
    )
    
    # 2. Fix CoordinateTransformation base class to use Literal 
    print("2. Fixing CoordinateTransformation base class type field...")
    content = fix_base_class_literal(
        content,
        class_name='CoordinateTransformation',
        field_name='transformation_type',
        literal_value='coordinate_transformation',  # Adjust if different
        original_type='CoordinateTransformationTypeEnum'  # Adjust if different
    )
    
    # 3. Add discriminators to Annotation unions
    print("3. Adding discriminators to Annotation unions...")
    content, annotation_changes, annotation_fields = add_discriminator_to_union(
        content,
        union_type_pattern='Annotation',
        discriminator_field='type'
    )
    if annotation_changes > 0:
        print(f"   ✓ Added {annotation_changes} Annotation discriminator(s)")
        for field in annotation_fields:
            print(f"     - {field}")
        total_changes += annotation_changes
    else:
        print(f"   ℹ No Annotation unions found")

    # 4. Add discriminators to CoordinateTransformation unions
    print("4. Adding discriminators to CoordinateTransformation unions...")
    content, coord_changes, coord_fields = add_discriminator_to_union(
        content,
        union_type_pattern='CoordinateTransformation',
        discriminator_field='transformation_type'
    )
    if coord_changes > 0:
        print(f"   ✓ Added {coord_changes} CoordinateTransformation discriminator(s)")
        for field in coord_fields:
            print(f"     - {field}")
        total_changes += coord_changes
    else:
        print(f"   ℹ No CoordinateTransformation unions found")
    
    # 5. Ensure necessary imports are present
    print("5. Ensuring imports are present...")
    content = ensure_imports(content, ['Annotated', 'Literal'])
    print("   ✓ Imports updated")
    
    # Write back to file
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print()
        print(f"✓ Successfully processed {file_path}")
        print(f"  Total discriminators added: {total_changes}")
    else:
        print()
        print(f"ℹ No changes needed for {file_path}")


def main():
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    else:
        file_path = Path('src/cets_data_model/models/models.py')
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    
    process_models(file_path)


if __name__ == '__main__':
    main()