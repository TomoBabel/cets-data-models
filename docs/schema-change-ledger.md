# Development schema integration ledger

This independent clone anticipates upstream changes; no upstream publication is implied.

| Baseline | Revision | Disposition |
|---|---|---|
| upstream main | 5e2ba016047f0d9635c3670332a9bf945dfdf339 | preserved base |
| PR 28 | d63032aa705a48e07d40860f96d3d67340ddfe5c | CI integration |
| PR 32 | 4e9d88e30b999e05e46396efcd0a2d855aa074e9 | generator and mixins |
| PR 34 | b415e952d309ac1ec0dee01a3a5db639cb08bba5 | canonical transforms; retain implemented getters/setters over PR 32 stubs |
| PR 35 | af2a628f66f51672dfeaa0402b82122927669b92 | acquisition records; resolve generated-model conflict by regeneration |
| PR 25 | 545d41fb729d33e360fe7faee34d093ff282aa98 | reference only; not merged |

## Integration corrections

- Generation explicitly writes the public models module; a temporary-output check enforces reproducibility.
- Formatter failures are fatal. LinkML and Ruff versions are pinned in the development dependencies.
- Preserve optional fields and list defaults expected by the rigid codec.
- Resolve conflicts in schema and handwritten utilities, never by retaining stale generated output.

## Acceptance

Integration and feature validation results are recorded as they are run. Pending checks are not passes.

- LinkML 1.9.6 requires a compatible runtime: pin linkml-runtime 1.9.5 (1.10 removes Format.JSON). Its generator lacks the newer empty_list_for_multivalued_slots option; the generation hook supplies existing optional-list defaults instead.
- Restore get_image_info as a compatibility wrapper around the existing get_em_info dispatcher; the upstream suite still imports the former name.

## Integration validation (2026-09-10)

- Core schema suite: 56 passed; public-model regeneration reproduces exactly.
- Unmodified cets-aretomo3 suite: 8 passed.
- Unmodified cets-warpm suite (frozen arewarpion oracle supplied explicitly): 13 passed.
- Shared io/cets suites: 39 passed, 2 failures in constant-grid goldens. Those fixtures synthesize equal-dose Warp XML and fail in arewarpion's strict native loader before CETS evaluation; retain the tests unchanged and record the preserved-environment comparison.
