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


from typing import Union
import abc
from typing import List
from .cost import Cost
from INPsim.ServicePlacement.Migration.Action import Action, MigrationAction, NoMigrationAction
from INPsim.Network.network import CloudNetwork
from INPsim.Network.User.Manager import UserManager
from INPsim.Network.Service.service import Service
from INPsim.Network.Nodes.cloud import Cloud


class GlobalCostFunction:
    """
    Abstract base class for global cost functions.
    """

    @abc.abstractmethod
    def calculate_global_cost(self, cloud_network: CloudNetwork, user_manager: UserManager, actions: List[Action]) -> Cost:
        """
        Calculates the global cost of the transition_cost from one service placement_cost configuration to the next.
        :param cloud_network: Cloud Network in Question
        :param user_manager: UserManager that contains the users and services in question
        :param actions: List of all actions to be included in the global cost calculation.
        :return: the global cost
        """
        pass


class ServiceCostFunction:
    """
    Abstract base class for per-service cost functions.
    """

    def calculate_cost(self,
                       cloud_network: CloudNetwork,
                       service: Service,
                       actions: List[Action]) -> Cost:
        """
        Calculates the cost for either a MigrationAction or a NoMigratonAction
        :param cloud_network: The cloud network on which the cost has to be calculated.
        :param service: The service for which the cost shall be calculated
        :param actions: the services's actions that are to be taken into account of the cost calculation
        :return: cost of this service (state cost + transition_cost cost)
        """
        static_cost: float = self.calculate_static_cost(cloud_network, service)
        transition_cost: float = 0.0
        for action in actions:
            assert action.get_service() == service
            transition_cost += self.calculate_action_transition_cost(cloud_network, action)
        return Cost(static_cost, transition_cost)
        # if isinstance(action, MigrationAction):
        #     return self.calculate_migration_action_transition_cost(
        #             cloud_network,
        #             action)
        # elif isinstance(action, NoMigrationAction):
        #     return self.calculate_static_cost(
        #             cloud_network, action)
        # else:
        #     raise ValueError(
        #             "Expected a MigrationAction or NoMigrationAction.")

    def calculate_action_transition_cost(self, cloud_network: CloudNetwork, action: Action) -> float:
        """
        Calculates the transition cost of an action.
        :param cloud_network: the cloud network within which the cost is calculated.
        :param action: the action for which the transition cost shall be evaluated
        :return: transition cost of the action in question
        """
        if isinstance(action, MigrationAction):
            return self.calculate_migration_action_transition_cost(cloud_network, action)
        else:
            return 0.0  # if there is ever an application where other actions have a transition cost, extend this here.

    @abc.abstractmethod
    def calculate_migration_action_transition_cost(
            self,
            cloud_network: CloudNetwork,
            action: MigrationAction) -> float:
        """
        Implement this method to calculate the cost of a migration action.
        Remember to check, if it failed.
        :param cloud_network: the cloud network within the cost is calculated
        :param action: the migration action
        :return: The Cost of the migration action.
        """
        pass

    @abc.abstractmethod
    def calculate_static_cost(self,
                              cloud_network: CloudNetwork,
                              service: Service) -> float:
        """
        Implement this method to calculate the static placement cost of a service.
        :param cloud_network: the cloud network within which the cost is calculated.
        :param service: The service for which the static cost shall be calculated.
        :return: The Cost of the service's state.
        """
        pass

