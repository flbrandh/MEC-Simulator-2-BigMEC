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


from abc import abstractmethod
from typing import Iterable, Optional
from .SimulationObserver import SimulationObserver
from INPsim.Network.network import CloudNetwork
from INPsim.Network.Service.service import Service
from INPsim.ServicePlacement.servicePlacementStrategy import ServicePlacementStrategy
from INPsim.Network.Nodes.cloud import Cloud
from INPsim.Network.User.user import User
from INPsim.Network.User.Manager import UserManager


class SimulationInterface:

    @abstractmethod
    def get_services(self) -> Iterable[Service]:
        """
        Returns an Iterable of all services in the current simulation state.
        :return: iterable of services
        """
        pass

    @abstractmethod
    def get_num_services(self) -> int:
        """
        Returns the number of services in the current simulation state.
        :return: non-negative number of services
        """
        pass

    @abstractmethod
    def get_clouds(self) -> Iterable[Cloud]:
        """
        Returns an Iterable of all clouds in the current simulation state
        :return: iterable of clouds
        """
        pass

    @abstractmethod
    def get_users(self) -> Iterable[User]:
        """
        Returns a Collection of all users in the current simulation state.
        :return: iterable of users
        """

    @abstractmethod
    def get_cloud_network(self) -> CloudNetwork:
        """
        Returns the cloud network that this simulation is using.
        :return: CloudNetwork obj of this simulation
        """

    @abstractmethod
    def get_current_step(self) -> int:
        """
        Returns the index of the current simulation step.
        :return: simulation step index
        """
        pass

    @abstractmethod
    def get_service_placement_strategy(self) -> ServicePlacementStrategy:
        """
        Returns the simulation's service placement_cost strategy
        :return: service placement_cost strategy
        """
        pass

    @abstractmethod
    def get_user_manager(self) -> UserManager:
        """
        Returns this simulation's user manager
        :return: UserManager obj of this simulation
        """
        pass

    @abstractmethod
    def simulate(self, num_steps: int, observer: Optional[SimulationObserver] = None) -> None:
        """
        Executes a specified number of configured_simulation steps.
        :param num_steps: number of steps to execute
        :param observer: a SimulationObserver Object that can be used to get callbacks before and after each configured_simulation step.
        :return: None
        """
