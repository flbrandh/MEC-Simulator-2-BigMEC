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


from INPsim.ServicePlacement.Migration.Algorithms import MigrationAlgorithm, RewardAggregatorAgent
from INPsim.ServicePlacement.Migration.Action.migrationActionInterface import MigrationAction
from INPsim.ServicePlacement.Migration.Action.noMigrationActionInterface import NoMigrationAction
from INPsim.ServicePlacement.Migration.CloudCandidateSelector.destinationCloudCandidateSelector import KnnBaseStationNeighborhoodBasedCandidateSelector
import math
from collections import defaultdict


def priority_weighted_latency_utility(cloud_network, service, cloud):
    """
    Utility function that returns the negative latency, weighted with the service priority.
    :param cloud_network:
    :param service:
    :param cloud:
    :return:
    """
    return -service.priority*cloud_network.dist_to_node(service.owner().get_base_station(), cloud.node())

def squared_latency_utility(cloud_network, service, cloud):
    """
    Utility function that returns the negative latency, weighted with the service priority.
    :param cloud_network:
    :param service:
    :param cloud:
    :return:
    """
    return -(cloud_network.dist_to_node(service.owner().get_base_station(), cloud.node()))**2

def priority_weighted_binary_utility(cloud_network, service, cloud):
    """
    Utility function that returns if the latency requirement is fulfilled, weighted with the service priority.
    :param cloud_network:
    :param service:
    :param cloud:
    :return:
    """
    if cloud_network.dist_to_node(service.owner().get_base_station(), cloud.node()) > service.get_latency_requirement():
        return -service.priority
    else:
        return 0

class AlwaysMigrateToHighestUtilityInNeighborhoodAlgorithm(MigrationAlgorithm):
    """
    Always migrates services to the cloud that has the lowest utility to its user  in the Neighborhood.
    Will displace other services if necessary.
    Note that this will only work with the configured_simulation since it requires global knowledge about the entire topology.
    """

    def __init__(
            self,
            num_neighbors,
            service_displacement,
            utility_function = priority_weighted_latency_utility):
        """
        :param num_neighbors: number of neighbors cloudlets
        :param service_displacement: should there be service displacement or should it not be possible
        :param utility_function: a function that takes cloud network, service, cloud and outputs a service's utility.
        """
        self._num_neighbors = num_neighbors
        self._service_displacement = service_displacement
        self.shared_agent = RewardAggregatorAgent()
        self._utility_function = utility_function

        # to be initialized when creating the instances
        self._destination_cloud_candidate_selector = None

    def create_instance(self, cloud, cloud_network):
        if not self._destination_cloud_candidate_selector:
            self._destination_cloud_candidate_selector = KnnBaseStationNeighborhoodBasedCandidateSelector(
                self._num_neighbors, cloud_network)

        if self._service_displacement:
            return AlwaysMigrateToHighestUtilityInNeighborhoodAlgorithm.InstanceDisplacement(
                cloud,
                cloud_network,
                self._destination_cloud_candidate_selector,
                self.shared_agent,
                self._utility_function)
        else:
            return AlwaysMigrateToHighestUtilityInNeighborhoodAlgorithm.InstanceNoDisplacement(
                cloud,
                cloud_network,
                self._destination_cloud_candidate_selector,
                self.shared_agent,
                self._utility_function)

    class InstanceNoDisplacement(MigrationAlgorithm.Instance):
        def __init__(
                self,
                cloud,
                cloud_network,
                destination_cloud_candidate_selector,
                reward_aggregator,
                utility_function):
            self._cloud = cloud
            self._cloud_network = cloud_network
            self._destination_cloud_candidate_selector = destination_cloud_candidate_selector
            self.reward_aggregator = reward_aggregator
            self._utility_function = utility_function

        def give_reward(self, reward):
            self.reward_aggregator.add_reward(reward)

        def best_available_cloud(self, service):
            best_cloud = None
            best_cloud_utility = -math.inf
            for cloud in [self._cloud] + self._destination_cloud_candidate_selector.get_candidate_clouds(service):
                if cloud.total_memory_requirement() + service.get_memory_requirement() <= cloud.memory_capacity():
                    utility = self._utility_function(self._cloud_network, service, cloud)
                    if utility > best_cloud_utility:
                        best_cloud_utility = utility
                        best_cloud = cloud
            return best_cloud

        def process_migration_event(self, service):
            migration_actions = []
            if service.last_user_node is not service.owner().get_base_station():
                target_cloud = self.best_available_cloud(service)

                if target_cloud and target_cloud != self._cloud:
                    return [
                        MigrationAction(
                            service,
                            self._cloud,
                            target_cloud)]
            return [NoMigrationAction(service, self._cloud)]

    class InstanceDisplacement(MigrationAlgorithm.Instance):
        def __init__(
                self,
                cloud,
                cloud_network,
                destination_cloud_candidate_selector,
                reward_aggregator,
                utility_function):
            self._cloud = cloud
            self._cloud_network = cloud_network
            self._destination_cloud_candidate_selector = destination_cloud_candidate_selector
            self.reward_aggregator = reward_aggregator
            self._utility_function = utility_function

        def give_reward(self, reward):
            self.reward_aggregator.add_reward(reward)

        def best_cloud(self, service):
            best_cloud = None
            best_cloud_utility = -math.inf
            best_cloud_necessary_migrations = []

            for cloud in [self._cloud] + self._destination_cloud_candidate_selector.get_candidate_clouds(service):
                utility = self._utility_function(self._cloud_network, service, cloud)
                displacement_cost, necessary_migrations = self.displacement_cost(service.get_memory_requirement(), cloud)

                if utility - displacement_cost > best_cloud_utility:
                    best_cloud_utility = utility - displacement_cost
                    best_cloud = cloud
                    best_cloud_necessary_migrations = necessary_migrations
            return best_cloud, best_cloud_necessary_migrations

        def _select_displacement_options(self, memory_requirement, cloud, displacement_options):
            def density_key(displacement_option):
                s,c,u = displacement_option
                return u/s.get_memory_requirement()

            freed_memory = 0
            combined_utility_cost = 0
            necessary_migrations = []
            reserved_memory = defaultdict(int)
            migrated_services = set()
            for service, neighbor_cloud, utility_cost in sorted(displacement_options, key=density_key):
                if freed_memory > memory_requirement and utility_cost >= 0:
                    return (combined_utility_cost, necessary_migrations)
                if service not in migrated_services:
                    if neighbor_cloud.free_memory_capacity() >= service.get_memory_requirement() + reserved_memory[neighbor_cloud]:
                        freed_memory += service.get_memory_requirement()
                        combined_utility_cost += utility_cost
                        necessary_migrations.append((service, neighbor_cloud))
                        assert(cloud != neighbor_cloud)
                        reserved_memory[neighbor_cloud] += service.get_memory_requirement()
                        assert(neighbor_cloud.free_memory_capacity() >= reserved_memory[neighbor_cloud])
                        migrated_services.add(service)
            if freed_memory > memory_requirement:
                return (combined_utility_cost, necessary_migrations)
            else:
                return (math.inf, []) # no viable combination found

        def _select_optimal_displacement_options(self, memory_requirement, cloud, displacement_options):
            best_displacement_option_set = set()
            best_displacement_option_set_combined_utility = -math.inf

            def powerset(seq):
                """
                Returns all the subsets of this set. This is a generator.
                """
                if len(seq) <= 1:
                    yield seq
                    yield []
                else:
                    for item in powerset(seq[1:]):
                        yield [seq[0]] + item
                        yield item

            for displacement_option_set in powerset(displacement_options):
                combined_utility = 0
                reserved_memory = defaultdict(int)
                combined_freed_memory = 0
                for service, neighbor_cloud, utility_cost in displacement_option_set:
                    combined_utility += utility_cost
                    combined_freed_memory += service.get_memory_requirement()
                    reserved_memory[neighbor_cloud] += service.get_memory_requirement()
                is_valid = True
                if combined_freed_memory < memory_requirement:
                    is_valid = False
                else:
                    for neighbor_cloud, reserved_mem in reserved_memory.items():
                        if neighbor_cloud.free_memory_capacity() < reserved_memory[neighbor_cloud]:
                            is_valid = False

                if is_valid:
                    if combined_utility > best_displacement_option_set_combined_utility:
                        best_displacement_option_set = displacement_option_set
                        best_displacement_option_set_combined_utility = combined_utility
            print("solved one!")
            if len(best_displacement_option_set) > 0:
                return (best_displacement_option_set_combined_utility, [(s, n) for s,n,u in best_displacement_option_set])
            else:
                return(math.inf, [])  # no viable combination found


        def displacement_cost(self, memory_requirement, cloud):
            if memory_requirement <= cloud.free_memory_capacity():
                return (0,[])

            displacement_options = []
            for service in cloud.services():
                for neighbor_cloud in self._destination_cloud_candidate_selector.get_candidate_clouds(service):
                    if neighbor_cloud != cloud:
                        displacement_options.append((service,
                                                     neighbor_cloud,
                                                     self._utility_function(self._cloud_network, service, cloud) -
                                                     self._utility_function(self._cloud_network, service, neighbor_cloud)))

            return self._select_displacement_options(memory_requirement, cloud, displacement_options)



        def process_migration_event(self, service):
            migration_actions = []
            if service.last_user_node is not service.owner().get_base_station():
                target_cloud, necessary_migrations = self.best_cloud(service)

                if target_cloud and target_cloud != self._cloud:
                    return [MigrationAction(s, s.get_cloud(), tc) for s, tc in necessary_migrations]+ \
                           [MigrationAction(service, self._cloud, target_cloud)]

            return [NoMigrationAction(service, self._cloud)]