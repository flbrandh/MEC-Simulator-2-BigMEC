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


from typing import Tuple, Iterable
from .SimulationObserver import SimulationObserver
from .SimulationInterface import SimulationInterface
from INPsim.ServicePlacement.Migration.Action import Action


class SimulationObserverList (SimulationObserver):
    """
    This class allows the combination of multiple SimulationObserver Objects into a sequence.
    """

    def __init__(self, *simulation_observers: SimulationObserver):
        """
        Initializes the obj with a list of configured_simulation observers that are called sequentially for every method.
        """
        self.simulation_observers: Tuple[SimulationObserver] = simulation_observers

    def before_simulation_step(self, simulator: SimulationInterface) -> None:
        """
        This method is called before each configured_simulation step and forwards the call to all configured_simulation observers in sequence.
        :param simulator: Simulator that is observed
        :return: None
        """
        for simulation_observer in self.simulation_observers:
            simulation_observer.before_simulation_step(simulator)

    def after_simulation_step(self, simulator: SimulationInterface, actions: Iterable[Action]) -> None:
        """
        This method is called after each configured_simulation step and forwards the call to all configured_simulation observers in sequence.
        :param simulator: Simulator that is observed.
        :param actions: A list of all actions that happened during the step.
        :return: None
        """
        for simulation_observer in self.simulation_observers:
            simulation_observer.after_simulation_step(simulator, actions)
