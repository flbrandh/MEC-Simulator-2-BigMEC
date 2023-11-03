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


import abc


class DestinationCloudCandidateSelectorInterface:
    """
    Classes that implement this interface select a set of likely destination clouds for a given service.
    """

    @abc.abstractmethod
    def get_num_candidates(self):
        """
        Returns the number of candidates that are selected for each service.
        The return value must be constant throughout the lifetime of the obj.
        :return:
        """
        pass

    @abc.abstractmethod
    def get_candidate_clouds(self, service):
        """
        Returns a list of possible destination clouds for the given service.
        The number of element of the list must be the same as returned by get_num_candidates().
        The returned list must not include the current cloud of the service.
        :param service: the service, for which the possible migration targets should be returned.
        :return: list of likely destination clouds.
        """
        pass


class KnnCloudNeighborhoodBasedCandidateSelector(
        DestinationCloudCandidateSelectorInterface):  # TODO get rid of the Neighborhood classes
    """
    This class implements a destination cloud preselection based on the K-nearest neighbor clouds in the network to the current cloud of a service.
    """

    def __init__(self, num_neighbors, cloud_network):
        self._num_neighbors = num_neighbors
        self._cloud_network = cloud_network
        self._cloud_knn_neighborhoods = dict([(cloud, self._nearest_coulds_cloud(
            cloud) + [cloud_network.central_cloud()]) for cloud in cloud_network.clouds()])

    def _nearest_coulds_cloud(self, cloud):
        clouds = [cloud for cloud, _ in self._cloud_network.get_nearest_clouds(
            cloud.node(), self._num_neighbors - 1, include_src_node=False)]
        assert len(clouds) == self._num_neighbors - 1
        return clouds

    def get_num_candidates(self):
        return self._num_neighbors

    def get_candidate_clouds(self, service):
        service_cloud = service.get_cloud()
        return self._cloud_knn_neighborhoods[service_cloud]


class KnnBaseStationNeighborhoodBasedCandidateSelector(
        DestinationCloudCandidateSelectorInterface):
    """
    This class implements a destination cloud preselection based on the K-nearest neighbor clouds in the network to the current base station of a service.
    """

    def __init__(self, num_neighbors, cloud_network):
        self._num_neighbors = num_neighbors
        self._cloud_network = cloud_network
        self._base_station_knn_neighborhoods = dict([(base_station, self._nearest_coulds_to_base_station(
            base_station) + [cloud_network.central_cloud()]) for base_station in cloud_network.base_stations()])

    def _nearest_coulds_to_base_station(self, base_station):
        clouds = [cloud for cloud, _ in self._cloud_network.get_nearest_clouds(
            base_station, self._num_neighbors - 1, include_src_node=False)]
        assert len(clouds) == self._num_neighbors - 1
        return clouds

    def get_num_candidates(self):
        return self._num_neighbors

    def get_candidate_clouds(self, service):
        service_user_base_station = service.owner().get_base_station()
        return self._base_station_knn_neighborhoods[service_user_base_station]
