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


from typing import Iterable
from . import SimulationInterface
from INPsim.ServicePlacement.Migration.Action import Action


class SimulationObserver:

    def before_simulation_step(self, simulation: SimulationInterface) -> None:
        """
        This method is called before each configured_simulation step.
        :param simulation: Simulator that is observed
        :return: None
        """
        pass

    def after_simulation_step(self, simulation: SimulationInterface, actions: Iterable[Action]) -> None:
        """
        This method is called after each configured_simulation step.
        :param simulation: Simulator that is observed.
        :param actions: An Iterable of all actions that were performed during the service placement_cost.
        :return: None
        """
        pass
