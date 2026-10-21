"""Exercise generation hooks without shipping placeholder public properties."""

import importlib.util
import subprocess
import sys

import pytest
from pydantic import ValidationError, field_validator

from model_processing import generate_models


class ValueMixin:
    @property
    def doubled_value(self):
        return self.value * 2

    @doubled_value.setter
    def doubled_value(self, value):
        self.value = value / 2

    @field_validator("value", check_fields=False)
    @classmethod
    def nonnegative_value(cls, value):
        if value < 0:
            raise ValueError("value must be nonnegative")
        return value


def load_module(path):
    spec = importlib.util.spec_from_file_location("fixture_models", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def fixture_models(tmp_path_factory):
    directory = tmp_path_factory.mktemp("generation_hooks")
    schema = directory / "schema.yaml"
    schema.write_text(
        """id: https://example.org/generation-hooks
name: generation_hooks
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
classes:
  Sample:
    attributes:
      value:
        range: float
        required: true
      tags:
        range: string
        multivalued: true
  DerivedSample:
    is_a: Sample
  Unaffected:
    attributes:
      value:
        range: float
"""
    )
    with pytest.MonkeyPatch.context() as patch:
        patch.setitem(generate_models.INJECT_MAP, "Sample", ["ValueMixin"])
        patch.setitem(generate_models.MIXIN_IMPORTS, __name__, ["ValueMixin"])
        output = directory / "models.py"
        output.write_text(generate_models.build_generator(schema).serialize())
    return load_module(output)


@pytest.mark.parametrize("name", ["Sample", "DerivedSample"])
def test_injected_property_is_inherited_and_not_serialized(fixture_models, name):
    model = getattr(fixture_models, name)
    instance = model(value=3, tags=[])
    assert instance.doubled_value == 6
    instance.doubled_value = 10
    assert instance.value == 5
    assert instance.model_dump() == {"value": 5.0, "tags": []}
    assert "doubled_value" not in model.model_fields
    assert "doubled_value" not in model.model_json_schema()["properties"]
    assert model.model_validate_json(instance.model_dump_json()) == instance
    assert model(value=0).tags == []


@pytest.mark.parametrize("name", ["Sample", "DerivedSample"])
def test_injected_validator_rejects_invalid_input_and_assignment(fixture_models, name):
    model = getattr(fixture_models, name)
    with pytest.raises(ValidationError, match="nonnegative"):
        model(value=-1)
    instance = model(value=3)
    with pytest.raises(ValidationError, match="nonnegative"):
        instance.doubled_value = -2
    assert instance.value == 3


def test_injection_is_scoped_to_configured_classes(fixture_models):
    instance = fixture_models.Unaffected(value=-1)
    assert not hasattr(instance, "doubled_value")
    assert instance.value == -1


@pytest.mark.parametrize(
    "error", [FileNotFoundError("ruff"), subprocess.CalledProcessError(1, "ruff")]
)
def test_formatter_errors_are_fatal(monkeypatch, tmp_path, error):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(generate_models.subprocess, "run", fail)
    with pytest.raises(type(error)):
        generate_models._format_with_ruff(tmp_path / "models.py")


def test_formatter_uses_the_generator_interpreter(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        generate_models.subprocess, "run", lambda args, **kwargs: calls.append(args)
    )
    generate_models._format_with_ruff(tmp_path / "models.py")
    assert len(calls) == 2
    assert all(args[:3] == [sys.executable, "-m", "ruff"] for args in calls)
