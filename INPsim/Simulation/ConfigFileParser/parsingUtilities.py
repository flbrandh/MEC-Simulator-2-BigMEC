# Copyright (C) 2020 Florian Brandherm
# This file is part of flbrandh/MEC-Simulator-2-BigMEC <https://github.com/flbrandh/MEC-Simulator-2-BigMEC>.
#
# flbrandh/MEC-Simulator-2-BigMEC is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# flbrandh/MEC-Simulator-2-BigMEC is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with flbrandh/MEC-Simulator-2-BigMEC.  If not, see <http://www.gnu.org/licenses/>.


import math
from typing import Any, Dict, Collection, Optional, Union, cast

jsonType = Union[str, int, float, Dict[str, Any]]
jsonObject = Dict[str, jsonType]


def parse_bool(
        obj: jsonObject,
        name: str,
        default_value: Optional[bool] = None) -> bool:
    """
    Parses and verifies a boolean variable from a json object.
    :param obj: JSON object
    :param name: name of the boolean variable
    :param default_value: default value; if this is None, an exception is thrown if the value isn't present.
    :return: the verified value
    """
    if name not in obj:
        if default_value is not None:
            return default_value
        else:
            raise Exception('Boolean value ' + name + "wasn't defined!")
    bool_value = bool(obj[name])
    return bool_value


def parse_int(obj: jsonObject,
              name: str,
              lower_bound: Optional[int] = None,
              upper_bound: Optional[int] = None,
              default_value: Optional[int] = None) -> int:
    """
    Parses and verifies an integer variable from a json object.
    :param obj: JSON object
    :param name: name of the integer variable
    :param lower_bound: lower bound of the value. If the value is not None and below the lower bound, an exception is thrown.
    :param upper_bound: upper bound of the value. If the value is not None and above the upper bound, an exception is thrown.
    :param default_value: default value; if this is None, an exception is thrown if the value isn't present.
    :return: the verified value
    """
    if name not in obj:
        if default_value is not None:
            return default_value
        else:
            raise Exception('Integer value ' + name + " wasn't defined!")
    int_value = int(cast(int, obj[name]))  # type : ignore
    if lower_bound is not None and int_value < lower_bound:
        raise Exception(
                'Integer value ' +
                name +
                " (" +
                str(int_value) +
                ") must not be lower than " +
                str(lower_bound) +
                ".")
    if upper_bound is not None and int_value > upper_bound:
        raise Exception(
                'Integer value ' +
                name +
                " (" +
                str(int_value) +
                ") must not be higher than " +
                str(upper_bound) +
                ".")
    return int_value


def parse_non_negative_int(obj: jsonObject,
                           name: str,
                           default_value: Optional[int] = None) -> int:
    """
    Parses and verifies a non-negative integer variable from a json object (shorthand).
    An Exception is raised if the read value is negative.
    :param obj: JSON object
    :param name: name of the integer variable
    :param default_value: default value; if this is None, an exception is thrown if the value isn't present.
    :return: the verified value
    """
    return parse_int(obj, name, 0, default_value=default_value)


def parse_float(obj: jsonObject,
                name: str,
                lower_bound: float = -math.inf,
                upper_bound: float = math.inf,
                default_value: Optional[float] = None) -> float:
    """
    Parses and verifies a float variable from a json object.
    :param obj: JSON object
    :param name: name of the integer variable
    :param lower_bound: lower bound of the value. If below the lower bound, an exception is thrown.
    :param upper_bound: upper bound of the value. If above the upper bound, an exception is thrown.
    :param default_value: default value; if this is None, an exception is thrown if the value isn't present.
    :return: the verified value
    """
    if name not in obj:
        if default_value is not None:
            return default_value
        else:
            raise Exception('Float value ' + name + " wasn't defined!")
    float_value = float(cast(float, obj[name]))
    if float_value < lower_bound:
        raise Exception(
                'Float value ' +
                name +
                " (" +
                str(float_value) +
                ") must not be lower than " +
                str(lower_bound) +
                ".")
    if float_value > upper_bound:
        raise Exception(
                'Float value ' +
                name +
                " (" +
                str(float_value) +
                ") must not be higher than " +
                str(upper_bound) +
                ".")
    return float_value


def parse_non_negative_float(obj: jsonObject,
                             name: str,
                             default_value: Optional[float] = None) -> float:
    """
    Parses and verifies a non-negative float variable from a json object (shorthand).
    An Exception is raised if the read value is negative.
    :param obj: JSON object
    :param name: name of the float variable
    :param default_value: default value; if this is None, an exception is thrown if the value isn't present.
    :return: the verified value
    """
    return parse_float(obj, name, 0.0, default_value=default_value)


def parse_str(obj: jsonObject, name: str) -> str:
    """
    Parses and verifies an arbitrary string variable from a json object.
    :param obj: JSON object
    :param name: name of the integer variable
    :return: the verified value
    """
    if name not in obj:
        raise Exception('String value ' + name + "wasn't defined!")
    assert isinstance(obj[name], str)
    value = cast(str, obj[name])
    return value


def parse_str_options(obj: jsonObject,
                      name: str,
                      options: Collection[str],
                      default_value: Optional[str] = None) -> str:
    """
    Parses and verifies a string variable that must be one of a collection of options from a json object.
    :param obj: JSON object
    :param name: name of the integer variable
    :param options: a collection of allowed values for the parsed string; If the read value is anything else, an Exception is raised.
    :param default_value: default value; if this is None, an exception is thrown if the value isn't present.
    :return: the verified value
    """
    if name not in obj:
        if default_value:
            assert default_value in options
            return default_value
        else:
            raise Exception('String value ' + name + " wasn't defined!")
    assert isinstance(obj[name], str)
    value = cast(str, obj[name])
    if value not in options:
        raise Exception(
                'String value ' +
                name +
                '(' +
                ') must be one of ' +
                str(options) +
                '.')
    return value


def parse_object(obj: jsonObject, name: str) -> jsonObject:
    """
    Unpacks and verifies the presence of a json object value from a json object.
    Raises an Exception if the value is not present
    :param obj: JSON object
    :param name: name of the integer variable
    :return: the unpacked object
    """
    if name not in obj:
        raise Exception('Object value ' + name + " wasn't defined!")
    value = obj[name]
    if not isinstance(value, dict):
        raise Exception('Value ' + name + '(type: ' +
                        str(type(value)) + ') must be an obj.')
    return value
