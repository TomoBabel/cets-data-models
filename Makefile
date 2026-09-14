
.PHONY: install
install:
	@echo "Installing Python dependencies"
	pip install .[all]

.PHONY: install-dev
install-dev:
	@echo "Installing development dependencies"
	pip install -e .[dev]

.PHONY: gen-python
gen-python:
	@echo "Generating Python model code from LinkML schema."
	python model_processing/generate_models.py src/cets_data_model/models/generated_models.py

.PHONY: compare-models
compare-models:
	@echo "Comparing model files"
	python scripts/compare_models.py src/cets_data_model/models/models.py src/cets_data_model/models/generated_models.py

.PHONY: compare-models-verbose
compare-models-verbose:
	@echo "Comparing model files (verbose)"
	python scripts/compare_models.py src/cets_data_model/models/models.py src/cets_data_model/models/generated_models.py --verbose

.PHONY: linkml-docs
linkml-docs:
	@echo "Generating documentation from linkml files"
	gen-markdown -d docs/linkml schema/linkml/entities.yaml
