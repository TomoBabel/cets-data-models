# cets-data-models
Contains the data models of the standard for cryo-electron tomography

## Model generation
The makefile contains commands for installation and model generation. Dev dependencies via: 

    make install-dev

are required for model generation:

    make gen-python

**NOTE:** `make gen-python` writes the generated module to `src/cets_data_model/models/generated_models.py` (a git-ignored build artifact). The committed, imported model is `src/cets_data_model/models/models.py`; sync it from the generated file (e.g. `cp generated_models.py models.py`) once `make compare-models` confirms they agree.

### Generation-time transforms
LinkML's Pydantic generator cannot, on its own, express everything the model needs: discriminated unions, reusable constrained type aliases, injected mixin base classes, and dropping LinkML's `treat_empty_lists_as_none` serializer. Rather than post-processing the generated *text*, `model_processing/generate_models.py` subclasses LinkML's `PydanticGenerator` and applies these transforms **at generation time**, on the generator's object model via the documented `after_generate_class` lifecycle hook (plus its `injected_classes` / `imports` params and a serializer-free `base_model.py.jinja` template override). It also keeps `[]` (not `None`) defaults for optional multivalued slots via `empty_list_for_multivalued_slots=True`, which downstream consumers rely on.

Everything is driven declaratively by `model_processing/patch_config.yaml`:
- `injected_base_classes` — hand-written mixins (`src/cets_data_model/models/mixins.py`) to add as base classes of specific generated classes;
- `discriminated_fields` — fields to wrap in `Annotated[Union[...], Field(discriminator=...)]` (their discriminator fields become `Literal[...]` in subclasses);
- `type_aliases` — reusable constrained type aliases and the fields to substitute them into.

Because the transforms operate on LinkML's object model rather than regex over generated text, the project is **not** tied to a specific LinkML output format. If upgrading LinkML, run `make gen-python` (it fails loudly on any incompatible hook/object-model change) and `make compare-models-verbose` to confirm the output is unchanged.

### Comparing generations of models
When changes are made to either LinkML or the post-generation configuration and new models generated, the differences between new and old can be ascertained with the script `compare_models.py`. The script can be run with the Makefile commands:

    make compare-models
    make compare-models-verbose

for a succinct or wordier output, respectively. 

## Update process
1. PR on main data model repository.  
    *PR description has to mention all changed or added fields.*
2. PR needs a review from every dev group.  
    *There are 2 weeks to provide feedback, otherwise approval is assumed.*
3. Upon merge, a versioned schema directory is created that contains the updated schema. 

## Schema versioning
The CETS schema version is based on Semantic Versioning.

Major version is incremented when incompatible schema updates are introduced:
Renaming metadata fields
Deprecating metadata fields
Changing the type or format of a metadata field

Minor version is incremented when additive schema updates are introduced:
Adding metadata fields
Changing the validation requirements for a metadata field

Patch version is incremented for editorial updates.

All changes are documented in the schema Changelog.
