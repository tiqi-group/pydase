from typing import TypedDict

import pint

units: pint.UnitRegistry = pint.UnitRegistry(autoconvert_offset_to_baseunit=True)
units.formatter.default_format = "~P"  # pretty and short format

Quantity = pint.Quantity
Unit = units.Unit


class QuantityDict(TypedDict):
    magnitude: int | float
    unit: str


def convert_to_quantity(
    value: QuantityDict | float | Quantity, unit: str = ""
) -> Quantity:
    """
    Convert a given value into a pint.Quantity object with the specified unit.

    Args:
        value:
            The value to be converted into a Quantity object.

            - If value is a float or int, it will be directly converted to the specified
              unit.
            - If value is a dict, it must have keys 'magnitude' and 'unit' to represent
              the value and unit.
            - If value is a Quantity object, it will remain unchanged.\n
        unit:
            The target unit for conversion. If empty and value is not a Quantity object,
            it will assume a unitless quantity.

    Returns:
        The converted value as a pint.Quantity object with the specified unit.

    Examples:
        >>> convert_to_quantity(5, 'm')
        <Quantity(5.0, 'meters')>
        >>> convert_to_quantity({'magnitude': 10, 'unit': 'mV'})
        <Quantity(10.0, 'millivolt')>
        >>> convert_to_quantity(10.0 * u.units.V)
        <Quantity(10.0, 'volt')>

    Note:
        If unit is not provided and value is a float or int, the resulting Quantity will
        be unitless.
    """

    if isinstance(value, int | float):
        quantity = float(value) * Unit(unit)
    elif isinstance(value, dict):
        quantity = float(value["magnitude"]) * Unit(value["unit"])
    else:
        quantity = value
    return quantity
