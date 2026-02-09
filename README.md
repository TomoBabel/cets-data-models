# cets-data-models
Contains the data models of the standard for cryo-electron tomography

## Model generation
The makefile contains commands for installation and model generation. Dev dependencies via: 

    make install-dev

are required for model generation:

    make gen-python

**NOTE:** currently the generated and patched (see *Post-generation script*, below) models are created at `src/cets_data_model/models/generated_models.py` and `src/cets_data_model/models/patched_models.py`, respectively, leaving *models.py* (i.e. at `src/cets_data_model/models/models.py`) untouched. This will be replaced in future iterations once tests are in place for validation of generated models. 

### Post-generation script
With just the LinkML, we cannot currently specify everything we'd like in the pydantic models. Thus, some post-generation augmentation and refinement is required. For this purpose, the script `patch_models.py` in `model_processing` adds type aliases and discriminated unions to the models. The file `patch_config.yaml` specifies where these modifications should happen, listing, for discriminated unions, the classes that should be in the union, and the fields and (optionally) classes to which they apply, and for type aliases, the name of it, its definition, and fields for which it should be used. Thus with the configuration in the yaml file, model patching can be extended, if need be. 

**NOTE:**This project pins `linkml==1.9.6` because the post-generation patching script depends on specific output format from LinkML's Pydantic generator. 

If upgrading LinkML:
1. Check changes to PydanticGenerator in LinkML release notes.
2. Update regex patterns in `model_processing/patch_models.py` if needed.
3. Run `make gen-python` and `make compare-models-verbose` to verify.

When the Makefile command described above, 

    make gen-python

is exceuted, the post-generation script, with its configuration, is also called. A summary of modifications is given as a printed output. 

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
