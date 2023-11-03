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


from typing import Optional, DefaultDict, List
from collections import defaultdict
from .costFunctionInterface import GlobalCostFunction, ServiceCostFunction
from .cost import Cost
from INPsim.Network.network import CloudNetwork
from INPsim.Network.User.Manager import UserManager
from INPsim.ServicePlacement.Migration.Action import Action, MigrationAction, NoMigrationAction
from INPsim.Network.Service import Service
from INPsim.Network.Nodes import Cloud


class PerServiceGlobalAverageCostFunction(GlobalCostFunction):
    """
    A global cost function that globally averages the cost of ServiceCostFunctions.
    """

    def __init__(self, service_cost_function: ServiceCostFunction):
        """
        Initializes the global cost function with a per-service cost function that is applied to all services.
        :param service_cost_function: the ServiceCostFunction that defines the global cost
        """
        self._service_cost_function = service_cost_function

    def calculate_global_cost(self, cloud_network: CloudNetwork, user_manager: UserManager, actions: List[Action]) -> Cost:
        """
        Calculates the global cost of the transition_cost from one service placement_cost configuration to the next.
        :param cloud_network: Cloud Network in Question
        :param user_manager: UserManager that contains the users and services in question
        :param actions: all the actions that are to be incorporated into the cost calculation
        :return: the average cost of the per-service cost function applied to all services
        """
        # sort all actions according to which service they belong
        service_actions: DefaultDict[Service, List[Action]] = defaultdict(list)
        for action in actions:
            service = action.get_service()
            service_actions[service].append(action)
        # calculate the cost for each service, incorporating all its actions.
        global_cost: Cost = Cost(0, 0)
        for service in user_manager.services():
            global_cost += self._service_cost_function.calculate_cost(cloud_network, service, service_actions[service])
        return global_cost / user_manager.num_services()
