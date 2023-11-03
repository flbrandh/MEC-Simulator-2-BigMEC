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


from typing import Any, Dict, Tuple
from INPsim.Simulation import simulator
from INPsim.Simulation.StatisticsSimulationObserver import StatisticsSimulationObserver
from .parsingUtilities import parse_str_options
import json
import os

from .version_0_1 import Version_0_1
from .version_0_2 import Version_0_2


def configure_simulation(configuration: Dict[str, Any], configuration_path: str) -> Tuple[simulator.Simulation, StatisticsSimulationObserver, int]:
    """
    configures a configured_simulation from a containing_object
    :param configuration: parsed json config
    :param configuration_path: path to which all paths in the config are relative to (typically the path of the containing_object file)
    :return: A tuple of a configured Simulation, a configured StatisticsSimulationObserver, and the number of simulation steps
    """
    version = parse_str_options(configuration, 'version', ['0.1', '0.2'])
    newest_version = '0.2'
    if version != newest_version:
        print("Warning: Configuration file version ", version, " is deprecated. Please update to version ", newest_version, ".")

    if version == '0.1':
        return Version_0_1.configure_simulation(configuration, configuration_path)
    elif version == '0.2':
        return Version_0_2.configure_simulation(configuration, configuration_path)
    else:
        raise Exception('could not load version ' + version)


def configure_simulation_from_configuration_file(filename: str) -> Tuple[simulator.Simulation, StatisticsSimulationObserver, int]:
    """
    Configures a configured_simulation from a containing_object file
    :param filename: filename/path of the containing_object file
    :return: Tuple of a configured Simulation, a configured statisticsSimulationObserver and the number of steps to simulate
    """
    path = os.path.dirname(os.path.relpath(filename))
    return configure_simulation(load_configuration_from_file(filename), path)


def load_configuration_from_file(filename: str) -> Dict[str, Any]:
    """
    Loads a JSON object from a file
    :param filename: name of the file
    :return: JSON Object
    """
    json_file = open(filename)
    configuration = json.load(json_file)
    return configuration
