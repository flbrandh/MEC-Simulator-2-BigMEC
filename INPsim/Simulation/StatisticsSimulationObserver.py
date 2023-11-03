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


from typing import DefaultDict, Optional, List, Iterable
from collections import defaultdict
import numpy as np
from INPsim.Network.Service.service import Service
from INPsim.Network.User.user import User
from INPsim.Network.Nodes.cloud import Cloud
from INPsim.ServicePlacement.Migration.Action import Action, MigrationAction
from .SimulationObserver import SimulationObserver
from .SimulationInterface import SimulationInterface
from INPsim.ServicePlacement.Migration.CostFunctions import GlobalCostFunction


class StatisticsSimulationObserver(SimulationObserver):
    """
    A SimulationObserver that collects many useful statistics.
    TODO: separate this into many different classes for each statistic?
    """

    def __init__(self, global_cost_function: GlobalCostFunction) -> None:
        """
        Initializes all statistics.
        """
        self._global_cost_function = global_cost_function

        self.global_cost: List[float] = []
        self.dissatisfaction_rate: List[float] = []
        self.num_migrations: List[int] = []
        self.avg_latency: List[float] = []
        self.num_services: List[int] = []
        self.num_services_at_cloud: List[int] = []

        # temporary variable to snapshot the placement_cost config before a
        # step to compare against it afterwards:
        #self.previous_placement: DefaultDict[Service, Optional[Cloud]] = defaultdict(lambda: None)

    def before_simulation_step(self, simulator: SimulationInterface) -> None:
        """
        This method is called before each configured_simulation step.
        :param simulator: Simulator that is observed
        :return: None
        """
        #self.previous_placement = defaultdict(lambda: None, [(service, service.get_cloud()) for service in simulator.get_services()])
        pass

    def after_simulation_step(self, simulator: SimulationInterface, actions: Iterable[Action]) -> None:
        """
        This method is called after each configured_simulation step.
        :param simulator: Simulator that is observed.
        :return: None
        """
        self.__add_simulation_step(simulator, actions)

    @staticmethod
    def get_num_dissatisfied_services(sim: SimulationInterface) -> int:
        num_dissatisfied = 0
        for service in sim.get_services():
            if not service.latency_requirement_fulfilled(
                    sim.get_cloud_network()):
                num_dissatisfied += 1
        return num_dissatisfied

    @staticmethod
    def get_avg_latency(sim: SimulationInterface) -> float:
        services = sim.get_services()
        summed_latency = 0.0
        num_services = 0
        for service in services:
            summed_latency += service.measured_latency(
                    sim.get_cloud_network())
            num_services += 1
        if num_services > 0:
            return summed_latency / num_services
        else:
            return 0

    @staticmethod
    def get_avg_latency_lower_bound(sim: SimulationInterface) -> float:
        services = sim.get_services()
        summed_latency = 0
        num_services = 0
        for service in services:
            user = service.owner()
            if isinstance(user, User):
                user_node = user.get_base_station()
            else:
                raise Exception('StatisticsSimulationObserver expected ServiceOwners of type User.')
            [(_, closest_cloud_latency)] = sim.get_cloud_network(
                    ).get_nearest_clouds(user_node, 1)
            optimal_latency = closest_cloud_latency + user_node.access_point_latency()
            summed_latency += optimal_latency
            num_services += 1
        if num_services > 0:
            return summed_latency / num_services
        else:
            return 0

    def get_global_cost(self, sim: SimulationInterface,
                        actions: List[Action]) -> float:
        return self._global_cost_function.calculate_global_cost(sim.get_cloud_network(), sim.get_user_manager(), actions).total()

    @staticmethod
    def get_num_migrations(sim: SimulationInterface, actions: Iterable[Action]) -> int:
        num_migrations = 0
        for action in actions:
            if isinstance(action, MigrationAction):
                num_migrations += 1
        return num_migrations

    def __add_simulation_step(self, sim: SimulationInterface, actions: List[Action]) -> None:
        self.global_cost.append(self.get_global_cost(sim, actions))
        num_services = sim.get_num_services()
        if num_services > 0:
            self.dissatisfaction_rate.append(self.get_num_dissatisfied_services(sim) / num_services)
        else:
            self.dissatisfaction_rate.append(0)
        self.num_migrations.append(self.get_num_migrations(sim, actions))

        self.avg_latency.append(self.get_avg_latency(sim))
        print("avg avg latency:", np.mean(self.avg_latency))
        self.num_services.append(len(list(sim.get_services())))
        self.num_services_at_cloud.append(len(sim.get_cloud_network().central_cloud().services()))
        # self.avg_latency_lower_bound.append(self.get_avg_latency_lower_bound(configured_simulation))

    def get_num_steps(self) -> int:
        return len(self.global_cost)
