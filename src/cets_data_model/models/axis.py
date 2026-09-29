"""Array-axis unit rule, injected into the generated ``Axis`` model.

``models.py`` imports this module, so enum members are compared by value.
"""

from typing import Any

from pydantic import model_validator


def _value(member: Any) -> Any:
    """Return an enum member's value and any other input unchanged."""
    return getattr(member, "value", member)


class ArrayAxisUnitMixin:
    """Array axes index a discrete grid, so their unit is ``pixel``.

    An array axis without a unit gets ``pixel`` instead of the schema default
    ``angstrom``; any other unit is rejected.
    """

    @model_validator(mode="before")
    @classmethod
    def _enforce_array_axis_unit(cls, data: Any) -> Any:
        if not isinstance(data, dict) or _value(data.get("axis_type")) != "array":
            return data
        unit = _value(data.get("axis_unit"))
        if unit is None:
            return {**data, "axis_unit": "pixel"}  # a copy: never edit caller data
        if unit != "pixel":
            raise ValueError(
                f"Array axes must use the 'pixel' unit (axis_type='array'); "
                f"got '{unit}'."
            )
        return data
