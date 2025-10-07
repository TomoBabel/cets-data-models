
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
	@echo "Generating Python code from linkml files"
	gen-pydantic --meta None schema/linkml/entities.yaml > src/cets_data_model/models/models.py

.PHONY: linkml-docs
linkml-docs:
	@echo "Generating documentation from linkml files"
	gen-markdown -d docs/linkml schema/linkml/entities.yaml
