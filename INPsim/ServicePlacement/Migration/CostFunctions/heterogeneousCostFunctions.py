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


from .costFunctionInterface import ServiceCostFunction
from INPsim.ServicePlacement.Migration.Action import MigrationAction
from INPsim.Network.network import CloudNetwork
from INPsim.Network.Service.service import Service
from INPsim.Network.Nodes.cloud import Cloud


class PriorityBasedCostFunction(ServiceCostFunction):
    """
    Cost is based on whether a migration takes place or not. should lead to the never-migrate policy (migration costt > 0) or always migrate policy (migration cost < 0)
    """

    def __init__(
            self,
            cloud_network: CloudNetwork,
            migration_cost=5,
            latency_cost_factor=1) -> None:
        self.migration_cost = migration_cost
        self.latency_cost_factor = latency_cost_factor

    def _get_service_priority(self, service):
        # if not hasattr(service,'priority'):
        #     service.__dict__['priority'] = random.randint(1,10)
        return service.priority

    def _get_latency_cost(self, service, cloud_network):
        return self.latency_cost_factor * service.measured_latency(cloud_network) * self._get_service_priority(service)

    def calculate_migration_action_transition_cost(
            self,
            cloud_network: CloudNetwork,
            action: MigrationAction) -> float:
        return self.migration_cost

    def calculate_static_cost(
            self,
            cloud_network: CloudNetwork,
            service: Service) -> float:
        return self._get_latency_cost(service, cloud_network)



class SquaredLatencyPlusMigrationCost(ServiceCostFunction):
    """
    Cost is based on whether a migration takes place or not. should lead to the never-migrate policy (migration costt > 0) or always migrate policy (migration cost < 0)
    """

    def __init__(
            self,
            cloud_network: CloudNetwork,
            migration_cost=5,
            latency_cost_factor=1) -> None:
        self.migration_cost = migration_cost
        self.latency_cost_factor = latency_cost_factor

    def _get_latency_cost(self, service, cloud_network):
        latency = self. latency_cost_factor * \
            service.measured_latency(cloud_network)
        return latency*latency

    def calculate_migration_action_transition_cost(
            self,
            cloud_network: CloudNetwork,
            action: MigrationAction) -> float:
        return self.migration_cost

    def calculate_static_cost(
            self,
            cloud_network: CloudNetwork,
            service: Service) -> float:
        return self._get_latency_cost(service, cloud_network)


class SLACostFunction(ServiceCostFunction):
    """
    Cost is based on whether a migration takes place or not. should lead to the never-migrate policy (migration cost > 0) or always migrate policy (migration cost < 0)
    """

    def __init__(
            self,
            cloud_network: CloudNetwork,
            migration_cost=5,
            latency_cost_factor=1) -> None:
        self.migration_cost = migration_cost
        self.latency_cost_factor = latency_cost_factor

    def _get_service_priority(self, service):
        return service.priority

    def _get_latency_cost(self, service, cloud_network):
        if service.latency_requirement_fulfilled(cloud_network):
            return 0
        else:
            return self.latency_cost_factor * self._get_service_priority(service) * 10

    def calculate_migration_action_transition_cost(
            self,
            cloud_network: CloudNetwork,
            action: MigrationAction) -> float:
        return self.migration_cost

    def calculate_static_cost(
            self,
            cloud_network: CloudNetwork,
            service: Service) -> float:
        return self._get_latency_cost(service, cloud_network)
