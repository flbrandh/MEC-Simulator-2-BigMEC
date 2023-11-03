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

from INPsim.Network.Service.service import Service
from INPsim.Network.network import CloudNetwork
from INPsim.Network.Nodes.cloud import Cloud

class InitialPlacementStrategy:
    @abc.abstractmethod
    def place_service_initially(self,
                                service: Service,
                                cloud_network: CloudNetwork) -> Cloud:
        """
        Determines the initial placement_cost of a service.
        :param service: Service to be placed.
        :param cloud_network: current network.
        :return: cloud, where the service should be placed.
        """
        pass


class InitialPlacementAtCloud(InitialPlacementStrategy):

    def place_service_initially(self,
                                service: Service,
                                cloud_network: CloudNetwork) -> Cloud:
        """
        Determines the initial placement_cost of a service to always be the central cloud.
        :param service: Service to be placed.
        :param cloud_network: current network.
        :return: central cloud.
        """
        return cloud_network.central_cloud()


class InitialPlacementAtClosestCloudletWithAvailableResources(InitialPlacementStrategy):

    def place_service_initially(self,
                                service: Service,
                                cloud_network: CloudNetwork) -> Cloud:
        """
        Determines the initial placement_cost of a service to be the closest cloudlet with available resources.
        :param service: Service to be placed.
        :param cloud_network: current network.
        :return: the closest cloudlet with available resources.
        """
        service_owner_base_station = service.owner().get_base_station()
        closest_cloudlet_with_free_resources = cloud_network.central_cloud()
        closest_cloudlet_with_free_resources_distance = cloud_network.dist_to_node(service_owner_base_station, cloud_network.central_cloud().node())

        for cloud in cloud_network.clouds():
            if cloud.free_memory_capacity() >= service.get_memory_requirement():
                dist = cloud_network.dist_to_node(service_owner_base_station, cloud.node())
                if dist < closest_cloudlet_with_free_resources_distance:
                    closest_cloudlet_with_free_resources_distance = dist
                    closest_cloudlet_with_free_resources = cloud
        return closest_cloudlet_with_free_resources