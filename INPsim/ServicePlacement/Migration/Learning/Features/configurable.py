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


from typing import List

class ConfigurableFeatures:
    """
    Encapsulates the features of the environment - less features than before
    """

    def __init__(self,
                 use_user_last_base_station=True,
                 use_relative_positions=True,
                 use_absolute_positions=True,
                 use_measured_latencies=True,
                 use_latency_requirements=False):
        self._use_user_last_base_station = use_user_last_base_station
        self._use_relative_positions = use_relative_positions
        self._use_absolute_positions = use_absolute_positions
        self._use_measured_latencies = use_measured_latencies
        self._use_latency_requirements = use_latency_requirements
        self._world_coordinate_scale = 0.0001
        self._world_coordinate_center = None


    def _absolute_node_position(self, node):
        if node is not None:
            x, y = node.get_pos()
            assert self._world_coordinate_center is not None
            return [self._world_coordinate_scale *
                    (x -
                     self._world_coordinate_center.x), self._world_coordinate_scale *
                    (y -
                     self._world_coordinate_center.y)]
        else:
            return [0] * 2

    def _absolute_user_position(self, user):
        if user is not None:
            x, y = user._movement_model.get_pos()
            return [self._world_coordinate_scale *
                    (x -
                     self._world_coordinate_center.x), self._world_coordinate_scale *
                    (y -
                     self._world_coordinate_center.y)]
        else:
            return [0] * 2

    def _relative_node_node_position(self, node1, node2):
        if node1 is not None:
            assert node2 is not None
            x1, y1 = node1.get_pos()
            x2, y2 = node2.get_pos()
            return [self._world_coordinate_scale * (x1 - x2),
                    self._world_coordinate_scale * (y1 - y2)]
        else:
            return [0] * 2

    def _relative_user_node_position(self, user, node):
        if user is not None:
            assert node is not None
            ux, uy = user._movement_model.get_pos()
            nx, ny = node.get_pos()
            return [self._world_coordinate_scale * (ux - nx),
                    self._world_coordinate_scale * (uy - ny)]
        else:
            return [0] * 2

    def _service_priority(self, service):
        if service is not None:
            return [0.01 * service.priority - 0.5]
        else:
            return [0.0]

    def action_features(
            self,
            dst_cloud=None,
            service=None,
            cloud_network=None):
        if self._world_coordinate_center is None:
            if cloud_network is not None:
                aabb = cloud_network.aabb()
                self._world_coordinate_center = aabb.center()

        if service is not None:
            user = service.owner()
            user_base_station = user.get_base_station()
            prev_user_base_station = user.get_previous_base_station()
            src_cloud = service.get_cloud()
            src_cloud_node = src_cloud.node()
            service_src_latency = service.measured_latency(cloud_network)
            service_latency_requirement = service.get_latency_requirement()
        else:
            user = None
            user_base_station = None
            prev_user_base_station = None
            src_cloud = None
            src_cloud_node = None
            service_src_latency = 0.0
            service_latency_requirement = 0.0

        if dst_cloud is not None:
            dst_cloud_node = dst_cloud.node()
            service_dst_latency = cloud_network.dist_to_node(
                dst_cloud.node(), user_base_station) + user_base_station.access_point_latency()
        else:
            dst_cloud_node = None
            service_dst_latency = 0.0

        if service is not None and service.get_cloud() == dst_cloud:
            dst_is_src = 1.0
        else:
            dst_is_src = -1.0

        features = []

        src_cloud_node_pos_x: float
        src_cloud_node_pos_y: float
        src_cloud_node_pos_x, src_cloud_node_pos_y = self._absolute_node_position(src_cloud_node)
        user_base_station_pos_x: float
        user_base_station_pos_y: float
        user_base_station_pos_x, user_base_station_pos_y = self._absolute_node_position(user_base_station)
        dst_cloud_node_pos_x: float
        dst_cloud_node_pos_y: float
        dst_cloud_node_pos_x, dst_cloud_node_pos_y = self._absolute_node_position(dst_cloud_node)
        user_pos_x: float
        user_pos_y: float
        user_pos_x, user_pos_y = self._absolute_user_position(user)
        prev_user_base_station_pos_x: float
        prev_user_base_station_pos_y: float
        prev_user_base_station_pos_x, prev_user_base_station_pos_y = self._absolute_node_position(prev_user_base_station)

        if self._use_relative_positions:
            features += [src_cloud_node_pos_x - user_base_station_pos_x, src_cloud_node_pos_y - user_base_station_pos_y]    # relative src-node/bs-position
            features += [dst_cloud_node_pos_x - user_base_station_pos_x, dst_cloud_node_pos_y - user_base_station_pos_y]  # relative dst-node/bs-position
            features += [user_pos_x - user_base_station_pos_x, user_pos_y - user_base_station_pos_y]  # relative user/bs-position
            if self._use_user_last_base_station:
                features += [prev_user_base_station_pos_x - user_base_station_pos_x, prev_user_base_station_pos_y - user_base_station_pos_y]
        if self._use_absolute_positions:
            features += [src_cloud_node_pos_x, src_cloud_node_pos_y]
            features += [dst_cloud_node_pos_x, dst_cloud_node_pos_y]
            features += [user_pos_x, user_pos_y]
            if self._use_user_last_base_station:
                features += self._absolute_node_position(
                    prev_user_base_station)
        if self._use_measured_latencies:
            features += [0.1 * service_src_latency]
            features += [0.1 * service_dst_latency]
        if self._use_latency_requirements:
            features += [0.1 * service_latency_requirement]
        features += self._service_priority(service)
        features += [dst_is_src]
        return features


    def deprecated_action_features(
            self,
            dst_cloud=None,
            service=None,
            cloud_network=None):
        if dst_cloud and service and cloud_network:
            user = service.owner()
            ux, uy = user.get_base_station().get_pos()
            src_cloud = service.get_cloud()
            features = []
            scale = 0.001
            features += [scale *
                         (src_cloud.get_pos()[0] -
                          ux), scale *
                         (src_cloud.get_pos()[1] -
                          uy)]  # rel. src cloud position (base station)
            features += [scale *
                         (dst_cloud.get_pos()[0] -
                          ux), scale *
                         (dst_cloud.get_pos()[1] -
                          uy)]  # rel. dst cloud position (base station)
            features += [scale *
                         (user._movement_model.get_pos()[0] -
                          ux), scale *
                         (user._movement_model.get_pos()[1] -
                          uy)]  # rel. user position (base station)
            features += [service.get_memory_requirement() /
                         10, service.get_latency_requirement() /
                         10]  # user requirements
            service_priority = service.priority
            features += [0.1 * service_priority]
            features += [0.1 * service.measured_latency(cloud_network)]
            user_node = service.owner().get_base_station()
            features += [0.1 *
                         (cloud_network.dist_to_node(dst_cloud.node(), user_node) +
                          user_node.access_point_latency())]
        else:
            features = 11 * [0]

        return features

    def state_features(self, cloud=None):
        #features = self.cloud_features(cloud)
        #return features
        return []