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


class Features:
    """
    Encapsulates the features of the environment.
    """
    def __init__(self, hyperparameters):
        self.hyperparameters = hyperparameters

    def cloud_features(self, cloud=None):
        if cloud:
            return [cloud.memory_capacity() / 10,
                    cloud.totalMemoryRequirement() / 10,
                    cloud.node().get_pos()[0],
                    cloud.node().get_pos()[1]]
        else:
            return [0] * 4

    def service_features(self, service=None):
        if service:
            features = [service.get_memory_requirement() / 10,
                        service.get_latency_requirement() / 10,
                        service.owner().get_base_station().get_pos()[0],
                        service.owner().get_base_station().get_pos()[1]]
            last_cloud = service.get_last_cloud()
            if last_cloud:
                features += [last_cloud.get_pos()[0], last_cloud.get_pos()[1]]
            else:
                features += [0, 0]
            return features
        else:
            return [0] * 6

    def cloud_service_features(self, cloud):
        if cloud:
            services = cloud.services()
            features = []
            for i in range(self.hyperparameters.max_num_services):
                if i < len(services):
                    features += self.service_features(services[i])
                else:
                    features += self.service_features()
            return features
        else:
            return self.hyperparameters.max_num_services * self.service_features()

    def neighbor_features(self, neighbor_clouds=None):
        if neighbor_clouds:
            features = []
            for i in range(self.hyperparameters.max_num_neighbor_clouds):
                if i < len(neighbor_clouds):
                    features += self.cloud_features(neighbor_clouds[i])
                else:
                    features += self.cloud_features()
            return features
        else:
            return self.hyperparameters.max_num_neighbor_clouds * self.cloud_features()

    def action_features(self, dst_cloud=None, service=None):
        features = self.cloud_features(dst_cloud) + self.service_features(service)
        return features

    def state_features(self, cloud=None, neighbor_clouds=None):
        features = self.cloud_features(cloud)
        features += self.cloud_service_features(cloud)
        features += self.neighbor_features(neighbor_clouds)
        return features
