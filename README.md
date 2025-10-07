# cets-data-models
Contains the data models of the standard for cryo-electron tomography

## Model generation
The makefile contains commands for installation and model generation. Dev dependencies via: 

    make install-dev

are required for model generation:

    make gen-python

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

