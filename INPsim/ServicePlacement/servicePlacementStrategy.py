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


import abc
import random
from typing import List
from INPsim.Network.Service import Service
from INPsim.Network import CloudNetwork
from INPsim.Network.User.Manager import UserManager
from INPsim.ServicePlacement.Migration.Action import Action


class ServicePlacementStrategy:
    """
    This is an abstract base class for a service placement_cost strategy.
    """

    @abc.abstractmethod
    def update_service_placements(
            self,
            cloud_network: CloudNetwork,
            user_manager: UserManager,
            time_step: float) -> List[Action]:
        """
        Updates the service placement_cost if necessary in this step.
        :param cloud_network: the cloud network
        :param user_manager: the user manager
        :param time_step: the time step between this call and the last call of this method
        :return: List of all performed actions
        """
        pass


class IndependentServicePlacementStrategy(ServicePlacementStrategy):
    """
    This is an abstract base class for a service strategy that places services independently of each other in random order(no joint optimization).
    Its purpose is to determine the service assignment at service instantiation and at each step during the configured_simulation.
    """

    def __init__(self):
        self.rng = random.Random()
        self.rng.seed(6151)

    def update_service_placements(
            self,
            cloud_network: CloudNetwork,
            user_manager: UserManager,
            time_step: float):
        """
        Updates the service placement_cost if necessary in this step.
        :param cloud_network: the cloud network
        :param user_manager: the user manager
        :param time_step: the timestep between this call and the last call of this method
        :return: List of all updated services
        """
        services_with_updated_placement = []
        services_in_random_order = list(user_manager.services())
        self.rng.shuffle(services_in_random_order)
        action_list: List[Action] = []
        for service in services_in_random_order:
            assert service.owner()  # safety check: make sure that there are no services whose owner is already destroyed

            if not service.get_cloud():  # this means the service is new.
                action_list.extend(self.place_service_initially(service, cloud_network))
            else:
                action_list.extend(self.place_service(service, cloud_network))

        return action_list

    @abc.abstractmethod
    def place_service_initially(self, service: Service, cloud_network: CloudNetwork) -> List[Action]:
        """
        Override this method to determine the initial assignment strategy of services
        :param service: service to be assigned initially
        :param cloud_network: given cloud network
        :return: a list of actions that the initial placement_cost incurred
        """
        pass

    @abc.abstractmethod
    def place_service(self, service: Service, cloud_network: CloudNetwork) -> List[Action]:
        """
        Override this method to update the assignment of a service if necessary.
        :param service: service to be updated
        :param cloud_network: given cloud network
        :return: a list of actions that the service placement_cost incurred
        """
        pass
