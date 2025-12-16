import sys
from deepdiff import DeepDiff
import importlib.util
import json


def load_module(path):
    spec = importlib.util.spec_from_file_location("module", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def print_schema_change(name, old_val, new_val, indent=2):
    """Pretty print schema changes with formatting for large defs"""
    prefix = " " * indent
    
    if isinstance(old_val, dict) and isinstance(new_val, dict):
        # For $defs, show what was added/removed/changed
        if name == "$defs":
            old_keys = set(old_val.keys())
            new_keys = set(new_val.keys())
            
            removed = old_keys - new_keys
            added = new_keys - old_keys
            changed = old_keys & new_keys
            
            if removed:
                print(f"{prefix}$defs REMOVED:")
                for key in sorted(removed):
                    print(f"{prefix}  - {key}")
            if added:
                print(f"{prefix}$defs ADDED:")
                for key in sorted(added):
                    print(f"{prefix}  + {key}")
            if changed:
                # Only show if there are actual differences
                diffs = []
                for key in sorted(changed):
                    if old_val[key] != new_val[key]:
                        diffs.append(key)
                if diffs:
                    print(f"{prefix}$defs MODIFIED:")
                    for key in diffs:
                        print(f"{prefix}  ~ {key}")
        else:
            # For other dicts, just show they changed
            print(f"{prefix}{name}: [complex object changed]")
    else:
        # Simple values or small changes
        print(f"{prefix}OLD: {json.dumps(old_val, indent=2)[:200]}")
        print(f"{prefix}NEW: {json.dumps(new_val, indent=2)[:200]}")


def compare_models(old_path, new_path, verbose=False):
    old = load_module(old_path)
    new = load_module(new_path)
    
    skip_classes = {'ConfiguredBaseModel', 'LinkMLMeta', 'BaseModel', 'RootModel'}
    
    old_classes = {
        name: cls for name, cls in vars(old).items() 
        if isinstance(cls, type) 
        and hasattr(cls, 'model_json_schema')
        and name not in skip_classes
        and not name.startswith('_')
    }
    new_classes = {
        name: cls for name, cls in vars(new).items() 
        if isinstance(cls, type) 
        and hasattr(cls, 'model_json_schema')
        and name not in skip_classes
        and not name.startswith('_')
    }
    
    added_classes = set()
    removed_classes = set()
    changed_classes = []
    
    for name in sorted(set(old_classes.keys()) | set(new_classes.keys())):
        if name not in old_classes:
            added_classes.add(name)
            print(f"+ NEW CLASS: {name}")
        elif name not in new_classes:
            removed_classes.add(name)
            print(f"- REMOVED CLASS: {name}")
        else:
            old_schema = old_classes[name].model_json_schema()
            new_schema = new_classes[name].model_json_schema()
            
            # Exclude $defs from main comparison if verbose is False
            if not verbose:
                old_compare = {k: v for k, v in old_schema.items() if k != '$defs'}
                new_compare = {k: v for k, v in new_schema.items() if k != '$defs'}
                
                # But note if $defs changed
                defs_changed = old_schema.get('$defs') != new_schema.get('$defs')
            else:
                old_compare = old_schema
                new_compare = new_schema
                defs_changed = False
            
            diff = DeepDiff(old_compare, new_compare, ignore_order=True)
            
            if diff or defs_changed:
                changed_classes.append(name)
                print(f"\n{'='*60}")
                print(f"CHANGED: {name}")
                print(f"{'='*60}")
                
                if defs_changed and not verbose:
                    old_defs = set(old_schema.get('$defs', {}).keys())
                    new_defs = set(new_schema.get('$defs', {}).keys())
                    
                    removed_defs = old_defs - new_defs
                    added_defs = new_defs - old_defs
                    
                    if removed_defs or added_defs:
                        print("$defs changes:")
                        if removed_defs:
                            print(f"  Removed: {', '.join(sorted(removed_defs))}")
                        if added_defs:
                            print(f"  Added: {', '.join(sorted(added_defs))}")
                        print()
                
                if diff:
                    print(diff.pretty())
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Classes added: {len(added_classes)}")
    print(f"Classes removed: {len(removed_classes)}")
    print(f"Classes changed: {len(changed_classes)}")
    
    if changed_classes:
        print(f"\nChanged classes: {', '.join(changed_classes)}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python compare_models.py <old_models.py> <new_models.py> [--verbose]")
        sys.exit(1)
    
    verbose = "--verbose" in sys.argv
    compare_models(sys.argv[1], sys.argv[2], verbose=verbose)
