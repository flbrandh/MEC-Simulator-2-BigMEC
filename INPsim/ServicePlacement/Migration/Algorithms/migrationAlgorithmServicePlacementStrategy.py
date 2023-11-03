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


from typing import Union, List
from INPsim.ServicePlacement.servicePlacementStrategy import IndependentServicePlacementStrategy
from INPsim.Network.Service.service import Service
from INPsim.Network.network import CloudNetwork
from INPsim.ServicePlacement.Migration.Algorithms import MigrationAlgorithm
from INPsim.ServicePlacement.Migration.Action import Action, MigrationAction, NoMigrationAction, InitialPlacementAction
from INPsim.ServicePlacement.Migration.CostFunctions import ServiceCostFunction
from INPsim.ServicePlacement.Migration.Algorithms.initialServicePlacementStrategy import InitialPlacementStrategy


class MigrationAlgorithmServicePlacementStrategy(IndependentServicePlacementStrategy):

    def __init__(self,
                 migration_algorithm: MigrationAlgorithm,
                 cloud_network: CloudNetwork,
                 cost_function: ServiceCostFunction,
                 migration_trigger: str,
                 initial_placement_strategy: InitialPlacementStrategy) -> None:
        """
        Initializes the service placement_cost strategy
        """
        super(MigrationAlgorithmServicePlacementStrategy, self).__init__()
        self._migration_algorithm: MigrationAlgorithm = migration_algorithm
        self._initialize_migration_algorithm_instances(cloud_network)
        self._cost_function = cost_function
        self._initial_placement_strategy = initial_placement_strategy

        self.num_migration_actions = 0
        self.num_no_migration_actions = 0

        def migration_trigger_always(service, cloud_network):
            return True

        def migration_trigger_user_bs_changed(service, cloud_network):
            service_user = service.owner()
            return service_user.get_previous_base_station() is not service_user.get_base_station()

        def migration_trigger_user_latency_changed(service, cloud_network):
            service_user = service.owner()
            if service_user.get_previous_base_station():
                prev_latency = cloud_network.dist_to_node(
                    service_user.get_previous_base_station(), service.get_cloud().node())
            else:
                prev_latency = 0  # special case: new user
            now_latency = cloud_network.dist_to_node(
                service_user.get_base_station(), service.get_cloud().node())
            return prev_latency != now_latency

        migration_triggers = {
            'always': migration_trigger_always,
            'bs_changed': migration_trigger_user_bs_changed,
            'latency_changed': migration_trigger_user_latency_changed}

        self._migration_trigger = migration_triggers[migration_trigger]

    def get_migration_algorithm(self) -> MigrationAlgorithm:
        return self._migration_algorithm

    def get_service_cost_function(self) -> ServiceCostFunction:
        return self._cost_function

    def _initialize_migration_algorithm_instances(
            self, cloud_network: CloudNetwork) -> None:
        for cloud in cloud_network.clouds():
            cloud.set_migration_algorithm_instance(
                self._migration_algorithm.create_instance(
                    cloud, cloud_network))

    def place_service_initially(self, service: Service, cloud_network: CloudNetwork) -> List[Action]:
        """
        Initially places services at the closest cloud and then performs a migration step.
        :param service: service to be assigned initially
        :param cloud_network: given cloud network
        :return: a list of actions that this initial service placement_cost incurred (always one InitialPlacementAction)
        """

        target_cloud = self._initial_placement_strategy.place_service_initially(service, cloud_network)
        target_cloud.add_service(service)
        actions: List[Action] = [InitialPlacementAction(service, target_cloud)]

        # trigger migration event
        actions.extend(self.trigger_migration_event(cloud_network, service))
        return actions

    def place_service(self,
                      service: Service,
                      cloud_network: CloudNetwork) -> List[Action]:
        """
        Performs a migration decision with a migration algorithm if
        the base station of a service's user changed or a time
        interval is over.
        :param service: service to be updated
        :param cloud_network: given cloud network
        :return: True, if the service placement_cost was updated
        """
        if self._migration_trigger(service, cloud_network):
            return self.trigger_migration_event(cloud_network, service)
        else:
            return []

    def get_reward(self,
                   cloud_network: CloudNetwork,
                   action: Union[MigrationAction,
                                 NoMigrationAction]) -> float:
        return -self._cost_function.calculate_cost(cloud_network, action.get_service(), [action]).total()

    def trigger_migration_event(
            self,
            cloud_network: CloudNetwork,
            service: Service) -> List[Action]:
        cloud = service.get_cloud()
        action_list: List[Union[MigrationAction, NoMigrationAction]] = cloud.get_migration_algorithm_instance().process_migration_event(service)
        # print('#migration actions:', len(action_list))
        if isinstance(action_list[-1], MigrationAction):
            before_services = action_list[-1].get_target_cloud().services().copy()
        assert len(action_list) >= 1
        if len(action_list) > 1:
            for action in action_list:
                assert isinstance(action, MigrationAction)
        for action in action_list:  # reversed(action_list):
            if isinstance(action, MigrationAction):
                self.execute_migration_action(cloud_network, action)
                self.num_migration_actions += 1
            else:
                self.num_no_migration_actions += 1
        assert action_list[-1].get_service() == service
        cloud.get_migration_algorithm_instance().give_reward(self.get_reward(cloud_network,
                                                                             action_list[-1]))
        return action_list

    def execute_migration_action(
            self,
            cloud_network: CloudNetwork,
            action: MigrationAction) -> None:
        service = action.get_service()
        cloud = action.get_target_cloud()
        assert service.get_memory_requirement() + cloud.total_memory_requirement() <= cloud.memory_capacity()
        assert cloud.total_memory_requirement() <= cloud.memory_capacity()
        cloud.add_service(action.get_service())
        assert cloud.total_memory_requirement() <= cloud.memory_capacity()
