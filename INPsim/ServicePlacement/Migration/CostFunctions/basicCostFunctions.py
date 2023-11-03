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


from INPsim.ServicePlacement.Migration.CostFunctions.costFunctionInterface import ServiceCostFunction
from INPsim.ServicePlacement.Migration.Action import MigrationAction
from INPsim.Network.network import CloudNetwork
from INPsim.Network.Service.service import Service

#
#
# class MigrationCostFunction(ServiceCostFunction):
#     """
#     Cost is based on whether a migration takes place or not. should lead to the never-migrate policy (migration costt > 0) or always migrate policy (migration cost < 0)
#     """
#
#     def __init__(self, migration_cost: float) -> None:
#         self.migration_cost = migration_cost
#
#     def calculate_migration_action_transition_cost(
#             self,
#             cloud_network: CloudNetwork,
#             action: MigrationAction) -> float:
#         return self.migration_cost
#
#     def calculate_static_cost(
#             self,
#             cloud_network: CloudNetwork,
#             service: Service) -> float:
#         return 0.0
#
#     # def get_name(self) -> str:
#     #     return 'MigrationCostFunction'


class LatencyCostFunction(ServiceCostFunction):
    """
    Cost is based on measured latency of the service.
    """

    def __init__(self, cloud_network: CloudNetwork) -> None:
        self._cloud_network = cloud_network

    def calculate_migration_action_transition_cost(
            self,
            cloud_network: CloudNetwork,
            action: MigrationAction) -> float:
        return 0.0

    def calculate_static_cost(
            self,
            cloud_network: CloudNetwork,
            service: Service) -> float:
        return service.measured_latency(self._cloud_network)

    # def get_name(self):
    #     return 'LatencyBasedCostFunction'


# class LatencyViolationCostFunction(ServiceCostFunction):
#     """
#     Cost is based on measured latency of the service.
#     """
#
#     def calculate_migration_action_transition_cost(
#             self,
#             cloud_network: CloudNetwork,
#             action: MigrationAction) -> float:
#
#         return 0.0
#
#     def calculate_static_cost(
#             self,
#             cloud_network: CloudNetwork,
#             service: Service) -> float:
#         if service.measured_latency(cloud_network) > 3:
#             return 1.0
#         else:
#             return 0.0



# class ProximityCostFunction(ServiceCostFunction):
#     """
#     Cost is based on measured latency of the service.
#     """
#
#     def distance(self, service: Service) -> float:
#         user_x, user_y = service.owner().get_base_station().get_pos()
#         cloud_x, cloud_y = service.get_cloud().get_pos()
#         distance = math.sqrt(
#             (user_x - cloud_x) ** 2 + (user_y - cloud_y) ** 2)
#         return distance
#
#     def calculate_migration_action_transition_cost(
#             self,
#             cloud_network: CloudNetwork,
#             service: Service,
#             target_cloud: Cloud,
#             failed: bool) -> float:
#         return self.distance(service)
#
#     def calculate_static_cost(
#             self,
#             cloud_network: CloudNetwork,
#             service: Service) -> float:
#         return self.distance(service)
#
#     # def get_name(self):
#     #     return 'ProximityCostFunction'


# class ComplexCostFunction(ServiceCostFunction):
#     """
#     Cost is based on latency and incorporates migration overhead. Also incorporates an activation cost.
#     """
#
#     def cloud_activation_cost(self, service: Service) -> float:
#         cloud = service.get_cloud()
#         single_cloud_activation_cost = 1  # equivalent to 1 hop of latency
#         return single_cloud_activation_cost / len(cloud.services())
#
#     def calculate_migration_action_transition_cost(
#             self,
#             cloud_network: CloudNetwork,
#             service: Service,
#             target_cloud: Cloud,
#             failed: bool) -> float:
#         migration_cost = 0.0
#         if not failed:
#             migration_cost = 1.0  # migration costs as much as 1 hop of latency
#         return service.measured_latency(
#             cloud_network) + migration_cost + self.cloud_activation_cost(service)
#
#     def calculate_static_cost(
#             self,
#             cloud_network: CloudNetwork,
#             service: Service) -> float:
#         return service.measured_latency(
#             cloud_network) + self.cloud_activation_cost(service)
#
#     # def get_name(self):
#     #     return 'ComplexCostFunction'


# class ComplexCostFunctionNoActivation(ServiceCostFunction):
#     """
#     Cost is based on latency and incorporates migration overhead.
#     """
#
#     def calculate_migration_action_transition_cost(
#             self,
#             cloud_network: CloudNetwork,
#             service: Service,
#             target_cloud: Cloud,
#             failed: bool) -> float:
#         migration_cost = 0
#         if not failed:
#             migration_cost = 1  # migration costs as much as 1 hop of latency
#         return service.measured_latency(cloud_network) + migration_cost
#
#     def calculate_static_cost(
#             self,
#             cloud_network: CloudNetwork,
#             service: Service) -> float:
#         return service.measured_latency(cloud_network)
#
#     # def get_name(self):
#     #     return 'ComplexCostFunctionNoActivation'
