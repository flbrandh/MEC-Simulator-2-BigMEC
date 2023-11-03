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


from INPsim.ServicePlacement.Migration.Algorithms.migrationAlgorithm import MigrationAlgorithm
from INPsim.ServicePlacement.Migration.CloudCandidateSelector.destinationCloudCandidateSelector import KnnBaseStationNeighborhoodBasedCandidateSelector
from INPsim.ServicePlacement.Migration.Learning.Features.configurable import ConfigurableFeatures
from INPsim.ServicePlacement.Migration.Learning.DQNAgent.clipping import ClippingDDQNAgent
import random


class DQNMigrationAlgorithm(MigrationAlgorithm):

    def __init__(
            self,
            hyperparameters,
            rng=random.Random(),
            features=None,
            verbose=False):
        self.hyperparameters = hyperparameters
        if features is None:
            self.features = ConfigurableFeatures()
        else:
            self.features = features
        self.rng = rng
        #self.shared_agent = DQNAgent(self.hyperparameters, self.features, rng, verbose)
        self.shared_agent = ClippingDDQNAgent(
            self.hyperparameters, self.features, rng, verbose)
        # to be initialized whn creating the instances
        self._destination_cloud_candidate_selector = None

    def get_name(self):
        return 'DQNMigrationAlgorithm'

    def create_instance(self, cloud, cloud_network):
        if not self._destination_cloud_candidate_selector:
            self._destination_cloud_candidate_selector = KnnBaseStationNeighborhoodBasedCandidateSelector(
                self.hyperparameters.max_num_neighbor_clouds, cloud_network)
        return DQNMigrationAlgorithm.Instance(
            cloud=cloud,
            shared_agent=self.shared_agent,
            hyperparameters=self.hyperparameters,
            destination_cloud_candidate_selector=self._destination_cloud_candidate_selector,
            cloud_network=cloud_network)

    class Instance(MigrationAlgorithm.Instance):
        def __init__(
                self,
                cloud,
                shared_agent,
                hyperparameters,
                destination_cloud_candidate_selector,
                cloud_network):
            self._cloud = cloud
            self._shared_agent = shared_agent
            self._destination_cloud_candidate_selector = destination_cloud_candidate_selector
            self._cloud_network = cloud_network

        def get_neighboring_clouds(self, service):
            nc = self._destination_cloud_candidate_selector.get_candidate_clouds(
                service)
            return nc

        def process_migration_event(self, service):
            return self._shared_agent.process_migration_event(
                service, self._cloud, self._cloud_network)

        def give_reward(self, reward):
            self._shared_agent.give_reward(reward)
