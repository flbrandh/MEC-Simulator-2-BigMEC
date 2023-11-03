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


from typing import Optional, cast
from INPsim.Network.network import Network
from INPsim.Network.Nodes import Node
from INPsim.Network.Nodes.cloud import Cloud
from INPsim.Network.User.serviceOwner import ServiceOwner
from INPsim.Network.User.user import User


class Service:

    def __init__(
            self,
            memory_requirement: float,
            latency_requirement: float,
            priority: float = 1) -> None:
        self.memory_requirement = memory_requirement  # 1#random.uniform(0.1,1)
        # 4#random.uniform(2,5) #hops
        self.latency_requirement = latency_requirement
        self._current_cloud: Optional[Cloud] = None
        self._last_cloud: Optional[Cloud] = None
        self._owner: Optional[ServiceOwner] = None
        # self.user.add_service(self)

        # a little optimization (caching the latency):
        self.last_service_node: Optional[Node] = None
        self.last_user_node: Optional[Node] = None
        self.last_measured_latency: Optional[float] = None

        self.priority = priority

    def __copy__(self) -> 'Service':
        return Service(
            self.memory_requirement,
            self.latency_requirement,
            self.priority)

    def measured_latency(self, network: Network) -> float:
        if self._current_cloud:
            service_node = self._current_cloud.node()
        else:
            raise Exception(
                'Cannot measure the Latency of a Service that is placed nowhere!')
        if self._owner:
            if isinstance(self._owner, User):
                user_node = self._owner.get_base_station()
            else:
                raise Exception(
                    'Cannot measure the Latency of a Service Owner that is not a User!')
        else:
            raise Exception(
                'Cannot measure the Latency of a Service that has no owner!')

        if service_node is self.last_service_node and user_node is self.last_user_node:
            num_hops = cast(float, self.last_measured_latency)
        else:
            num_hops = network.dist_to_node(
                service_node, user_node) + user_node.access_point_latency()
        self.last_measured_latency = num_hops
        self.last_user_node = user_node
        self.last_service_node = service_node
        return num_hops

    def latency_requirement_fulfilled(self, network: Network) -> bool:
        return self.measured_latency(network) <= self.latency_requirement

    def set_owner(self, new_owner: ServiceOwner) -> None:
        self._owner = new_owner

    def owner(self) -> Optional[ServiceOwner]:
        """
        The owner of a service is currently always user, but this may be subject to change, if services can own services.
        :return: the owner of this service
        """
        return self._owner

    def get_memory_requirement(self) -> float:
        return self.memory_requirement

    def get_latency_requirement(self) -> float:
        return self.latency_requirement

    def set_cloud(self, cloud: Cloud) -> None:
        self._last_cloud = self._current_cloud
        self._current_cloud = cloud

    def get_cloud(self) -> Optional[Cloud]:
        return self._current_cloud

    def get_last_cloud(self) -> Optional[Cloud]:
        return self._last_cloud
