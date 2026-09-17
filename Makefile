PYTHON ?= python3

# Install the package.
.PHONY: install
install:
	@echo "Installing Python dependencies"
	$(PYTHON) -m pip install .[all]

# Install the package and development tools.
.PHONY: install-dev
install-dev:
	@echo "Installing development dependencies"
	$(PYTHON) -m pip install -e .[dev]

# Generate, format, and validate Python models.
.PHONY: gen-python
gen-python:
	@echo "Generating Python model code from LinkML schema."
	$(PYTHON) model_processing/generate_models.py src/cets_data_model/models/generated_models.py

# Summarize model schema differences.
.PHONY: compare-models
compare-models:
	@echo "Comparing model files"
	$(PYTHON) scripts/compare_models.py src/cets_data_model/models/models.py src/cets_data_model/models/generated_models.py

# Show detailed model schema differences.
.PHONY: compare-models-verbose
compare-models-verbose:
	@echo "Comparing model files (verbose)"
	$(PYTHON) scripts/compare_models.py src/cets_data_model/models/models.py src/cets_data_model/models/generated_models.py --verbose

# Generate schema documentation.
.PHONY: linkml-docs
linkml-docs:
	@echo "Generating documentation from linkml files"
	gen-markdown -d docs/linkml schema/linkml/entities.yaml

# Fail if regenerated Python models differ.
.PHONY: check-models
check-models: gen-python
	diff -u src/cets_data_model/models/models.py src/cets_data_model/models/generated_models.py

# Check Python, installed dependency compatibility, and required tools.
.PHONY: check-env
check-env:
	$(PYTHON) -c "import sys; sys.exit(0 if (3, 11) <= sys.version_info < (4,) else 'Activate Python 3.11+ or set PYTHON=/path/to/python.')"
	$(PYTHON) -m pip check
	$(PYTHON) -c "import cets_data_model, linkml.generators.pydanticgen, pytest, ruff"

# Check the environment, regenerate models, and run schema/model checks.
.PHONY: validate
validate: check-env
	$(MAKE) check-models
	$(PYTHON) -m pytest -q --ignore=tests/test_utils.py
