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


from .migrationAlgorithm import MigrationAlgorithm
from INPsim.ServicePlacement.Migration.Action import MigrationAction, NoMigrationAction
from INPsim.ServicePlacement.Migration.CloudCandidateSelector.destinationCloudCandidateSelector import KnnBaseStationNeighborhoodBasedCandidateSelector
import math
import numpy as np


class RewardAggregatorAgent:
    def __init__(self):
        self.avg_rewards = []
        self.reward_buffer = []

    def add_reward(self, reward):
        self.reward_buffer.append(reward)
        if len(self.reward_buffer) >= 100:
            self.avg_rewards.append(np.mean(self.reward_buffer))
            self.reward_buffer = []


class NeverMigrateAlgorithm(MigrationAlgorithm):
    """
    Never migrates any services.
    """

    def __init__(self):
        self.shared_agent = RewardAggregatorAgent()

    def create_instance(self, cloud, cloud_network):
        return NeverMigrateAlgorithm.Instance(cloud, self.shared_agent)

    class Instance(MigrationAlgorithm.Instance):
        def __init__(self, cloud, reward_aggregator):
            self._cloud = cloud
            self._reward_aggregator = reward_aggregator

        def process_migration_event(self, service):
            return [NoMigrationAction(service, self._cloud)]

        def give_reward(self, reward):
            self._reward_aggregator.add_reward(reward)


class AlwaysMigrateAlgorithm(MigrationAlgorithm):
    """
    Always migrates services to the cloud that has the lowest latency to its user (Assumes full connectivity!)
    Note that this will only work with the configured_simulation since it requires global knowledge about the entire topology.
    TODO: How about a simple algorithm that learns from experience which cloud has the lowest latency to which base station using a globally synchronized lookup table (aka. multi-armed bandit with epsilon-greedy updates)
    """

    def __init__(self, only_available_clouds):
        self.shared_agent = RewardAggregatorAgent()
        self._only_available_clouds = only_available_clouds

    def create_instance(self, cloud, cloud_network):
        return AlwaysMigrateAlgorithm.Instance(
            cloud, cloud_network, self.shared_agent, self._only_available_clouds)

    class Instance(MigrationAlgorithm.Instance):
        def __init__(
                self,
                cloud,
                cloud_network,
                reward_aggregator,
                only_available_clouds):
            self._cloud = cloud
            self._cloud_network = cloud_network
            self._reward_aggregator = reward_aggregator
            self._only_available_clouds = only_available_clouds

        def process_migration_event(self, service):
            migration_actions = []
            current_base_station = service.owner().get_base_station()
            if service.last_user_node is not current_base_station:
                target_cloud = None
                if self._only_available_clouds:
                    closest_available_cloud_with_distance = self._cloud_network.get_nearest_clouds(
                        current_base_station,
                        k=1,
                        cloud_filter=lambda cloud: (
                            cloud.total_memory_requirement() +
                            service.get_memory_requirement()) <= cloud.memory_capacity())
                    if closest_available_cloud_with_distance:
                        [(target_cloud, _)] = closest_available_cloud_with_distance
                    else:
                        target_cloud = self._cloud  # if there is no available cloud left, don't migrate
                    # [(target_cloud,_)] = self._cloud_network.get_nearest_clouds(current_base_station, k=1,cloud_filter=lambda cloud: (cloud.totalMemoryRequirement()+service.get_memory_requirement()) <= cloud.memory_capacity())
                    #target_cloud = self._sim[0].closestCloud(current_base_station,lambda cloud: (cloud.totalMemoryRequirement()+service.get_memory_requirement()) / cloud.memory_capacity() <=1)
                else:
                    [(target_cloud, _)] = self._cloud_network.get_nearest_clouds(
                        current_base_station, k=1)
                    #target_cloud = self._sim[0].closestCloud(current_base_station)
                if target_cloud is not self._cloud:  # don't migrate to yourself
                    return [
                        MigrationAction(
                            service,
                            self._cloud,
                            target_cloud)]
            return [NoMigrationAction(service, self._cloud)]

        def give_reward(self, reward):
            self._reward_aggregator.add_reward(reward)


class AlwaysMigrateToClosestInNeighborhoodAlgorithm(MigrationAlgorithm):
    """
    Always migrates services to the cloud that has the lowest latency to its user (Assumes full connectivity!)
    Note that this will only work with the configured_simulation since it requires global knowledge about the entire topology.
    TODO: How about a simple algorithm that learns from experience which cloud has the lowest latency to which base station using a globally synchronized lookup table (aka. multi-armed bandit with epsilon-greedy updates)
    """

    def __init__(
            self,
            num_neighbors,
            only_available_clouds,
            distance_measure='euclidian',
            furthest_cloud=False):
        """

        :param num_neighbors: number of neighbors cloudlets
        :param only_available_clouds: if True, no full clouds will be chosen as migration target
        :param distance_measure: either "euclidian" or "hops"
        :param furthest_cloud: if True, returns not the closest, but the furthest cloud in a neighborhood
        """
        self._num_neighbors = num_neighbors
        self._distance_measure = distance_measure
        if distance_measure not in ['euclidian', 'hops']:
            raise ValueError("invalid distance measure")
        self.shared_agent = RewardAggregatorAgent()
        self._only_available_clouds = only_available_clouds
        # to be initialized whn creating the instances
        self._destination_cloud_candidate_selector = None
        self._furthest_cloud = furthest_cloud

    def create_instance(self, cloud, cloud_network):
        if not self._destination_cloud_candidate_selector:
            self._destination_cloud_candidate_selector = KnnBaseStationNeighborhoodBasedCandidateSelector(
                self._num_neighbors, cloud_network)
        if self._distance_measure == 'euclidian':
            return AlwaysMigrateToClosestInNeighborhoodAlgorithm.InstanceEuclidian(
                cloud,
                cloud_network,
                self._destination_cloud_candidate_selector,
                self.shared_agent,
                self._only_available_clouds,
                self._furthest_cloud)
        elif self._distance_measure == 'hops':
            return AlwaysMigrateToClosestInNeighborhoodAlgorithm.InstanceHops(
                cloud,
                cloud_network,
                self._destination_cloud_candidate_selector,
                self.shared_agent,
                self._only_available_clouds,
                self._furthest_cloud)

    class InstanceEuclidian(MigrationAlgorithm.Instance):
        def __init__(
                self,
                cloud,
                cloud_network,
                destination_cloud_candidate_selector,
                reward_aggregator,
                only_available_clouds,
                furthest_cloud):
            self._cloud = cloud
            self._destination_cloud_candidate_selector = destination_cloud_candidate_selector
            self.reward_aggregator = reward_aggregator
            self._only_available_clouds = only_available_clouds
            self._furthest_cloud = furthest_cloud

        def give_reward(self, reward):
            self.reward_aggregator.add_reward(reward)

        def compute_distance(self, base_station, cloud):
            """
            computes the euclidian distance between a cloud and a base station
            :param base_station:
            :param cloud:
            :return:
            """
            user_x, user_y = base_station.get_pos()
            cloud_x, cloud_y = cloud.node().get_pos()
            return (user_x - cloud_x)**2 + (user_y - cloud_y)**2

        def closest_cloud(self, service):
            closest_cloud = None
            closest_cloud_distance_sq = math.inf
            for cloud in [
                    self._cloud] + self._destination_cloud_candidate_selector.get_candidate_clouds(service):
                if not self._only_available_clouds or (
                        self._only_available_clouds and (
                            cloud.total_memory_requirement() +
                            service.get_memory_requirement()) /
                        cloud.memory_capacity() <= 1):
                    distance = self.compute_distance(
                        service.owner().get_base_station(), cloud)
                    if distance < closest_cloud_distance_sq:
                        closest_cloud_distance_sq = distance
                        closest_cloud = cloud
            return closest_cloud

        def furthest_cloud(self, service):
            furthest_cloud = None
            furthest_cloud_distance_sq = -math.inf
            for cloud in [
                    self._cloud] + self._destination_cloud_candidate_selector.get_candidate_clouds(service):
                if not self._only_available_clouds or (
                        self._only_available_clouds and (
                            cloud.total_memory_requirement() +
                            service.get_memory_requirement()) /
                        cloud.memory_capacity() <= 1):
                    distance = self.compute_distance(
                        service.owner().get_base_station(), cloud)
                    if distance > furthest_cloud_distance_sq:
                        furthest_cloud_distance_sq = distance
                        furthest_cloud = cloud
            return furthest_cloud

        def least_occupied_cloud(self, service):
            user_x, user_y = service.owner().get_basestation().get_pos()
            least_occupied_cloud = None
            least_occupied_cloud_cloud_utilization = math.inf
            for cloud in [
                    self._cloud] + self._destination_cloud_candidate_selector.get_candidate_clouds(service):
                utilization = cloud.total_memory_requirement() / cloud.memory_capacity()
                if utilization < least_occupied_cloud_cloud_utilization:
                    least_occupied_cloud_cloud_utilization = utilization
                    least_occupied_cloud = cloud
            return least_occupied_cloud

        def process_migration_event(self, service):
            migration_actions = []
            if service.last_user_node is not service.owner().get_base_station():
                if self._furthest_cloud:
                    target_cloud = self.furthest_cloud(service)
                else:
                    target_cloud = self.closest_cloud(service)

                if target_cloud and target_cloud != self._cloud:
                    return [
                        MigrationAction(
                            service,
                            self._cloud,
                            target_cloud)]
            return [NoMigrationAction(service, self._cloud)]

    class InstanceHops(InstanceEuclidian):
        def __init__(
                self,
                cloud,
                cloud_network,
                destination_cloud_candidate_selector,
                reward_aggregator,
                only_available_clouds,
                furthest_cloud):
            super(
                AlwaysMigrateToClosestInNeighborhoodAlgorithm.InstanceHops,
                self).__init__(
                cloud,
                cloud_network,
                destination_cloud_candidate_selector,
                reward_aggregator,
                only_available_clouds,
                furthest_cloud)
            self._cloud_network = cloud_network

        def compute_distance(self, base_station, cloud):
            """
            computes the number of hops between a cloud and a base station
            :param base_station:
            :param cloud:
            :return:
            """
            return self._cloud_network.dist_to_node(
                base_station, cloud.node())



# class AlwaysMigrateToClosestAvailableInNeighborhoodAlgorithm(
#         MigrationAlgorithm):
#     """
#     Always migrates services to the cloud that has the lowest latency to its user (Assumes full connectivity!)
#     Note that this will only work with the configured_simulation since it requires global knowledge about the entire topology.
#     TODO: How about a simple algorithm that learns from experience which cloud has the lowest latency to which base station using a globally synchronized lookup table (aka. multi-armed bandit with epsilon-greedy updates)
#     """
#
#     def __init__(self, num_neighbors):
#         self._num_neighbors = num_neighbors
#         # to be initialized whn creating the instanc
#         self._destination_cloud_candidate_selector = None
#
#     def create_instance(self, cloud, cloud_network):
#         if not self._destination_cloud_candidate_selector:
#             self._destination_cloud_candidate_selector = KnnBaseStationNeighborhoodBasedCandidateSelector(
#                 self._num_neighbors, cloud_network)
#         return AlwaysMigrateToClosestAvailableInNeighborhoodAlgorithm.Instance(
#             cloud, self._destination_cloud_candidate_selector)
#
#     class Instance(MigrationAlgorithm.Instance):
#         def __init__(self, cloud, destination_cloud_candidate_selector):
#             self._cloud = cloud
#             self._destination_cloud_candidate_selector = destination_cloud_candidate_selector
#
#         def euclidian_closest_available_cloud(
#                 self, service, predicted_cloud_memory_requirement):
#             user_x, user_y = service.owner().get_base_station().get_pos()
#             closest_cloud = None
#             closest_cloud_distance_sq = math.inf
#             for cloud in [
#                     self._cloud] + self._destination_cloud_candidate_selector.get_candidate_clouds(service):
#                 cloud_x, cloud_y = cloud.node().get_pos()
#                 distance_sq = (user_x - cloud_x)**2 + (user_y - cloud_y)**2
#                 if cloud not in predicted_cloud_memory_requirement:
#                     predicted_cloud_memory_requirement[cloud] = cloud.total_memory_requirement(
#                     )
#                 predicted_utilization = (
#                     predicted_cloud_memory_requirement[cloud] + service.get_memory_requirement()) / cloud.memory_capacity()
#                 if predicted_utilization < 1 and distance_sq < closest_cloud_distance_sq:
#                     closest_cloud_distance_sq = distance_sq
#                     closest_cloud = cloud
#                     predicted_cloud_memory_requirement[cloud] += service.get_memory_requirement(
#                     )
#             return closest_cloud
#
#         def process_migration_event(self, configured_simulation):
#             migration_actions = []
#             for service in self._cloud.services():
#                 if service.last_user_node is not service.user.get_base_station():
#                     predicted_cloud_utilizations = {}
#                     target_cloud = self.euclidian_closest_available_cloud(
#                         service, predicted_cloud_utilizations)
#                     if target_cloud and not target_cloud == self._cloud:
#                         migration_actions.append(
#                             MigrationAction(service, target_cloud))
#             return MigrationAlgorithm.MigrationResult(migration_actions)