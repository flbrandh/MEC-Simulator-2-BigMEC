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


from typing import Any, Tuple
from INPsim.Network.Nodes.node import CloudNode


class Cloud:

    def __init__(self, node: CloudNode) -> None:
        """
        Initializes the cloud.
        :param node: the CloudNode, at which the cloud is placed.
        """
        self._node = node
        self._services = []
        self._migration_algorithm_instance = None

    def get_migration_algorithm_instance(self) -> Any:
        return self._migration_algorithm_instance

    def set_migration_algorithm_instance(
            self, migration_algorithm_instance: Any) -> None:
        self._migration_algorithm_instance = migration_algorithm_instance

    def get_pos(self) -> Tuple[float, float]:
        return self._node.get_pos()

    def resources_for_service_available(self, service: Any) -> bool:
        """
        Determines if this cloud has the necessary resources to run an additional service.
        :param service: The service in question.
        :return: True, if there are sufficient resources to execute service. False, if not.
        """
        return True  # This basic cloud interface has no resources.

    def add_service(self, service: Any) -> None:
        if service in self._services:
            return  # do nothing

        if service.get_cloud():
            service.get_cloud().remove_service(service)

        service.set_cloud(self)
        self._services.append(service)

    def remove_service(self, service: Any) -> None:
        self._services.remove(service)

    def node(self) -> CloudNode:
        return self._node

    def services(self) -> Any:
        return self._services


class LimitedMemoryCloud(Cloud):

    class CloudOverallocatedException (Exception):
        def __init__(self):
            super().__init__("Cloud is over-allocated!")

    def __init__(self, node: CloudNode, memory_capacity: float) -> None:
        """
        Initializes a cloud with limited memory.
        :param node: The node thwt the cloud is placed at
        :param memory_capacity: the memory capacity of the cloud
        """
        super(LimitedMemoryCloud, self).__init__(node=node)
        self._memoryCapacity: float = memory_capacity
        self._total_memory_requirement: float = 0.0

    def add_service(self, service: Any) -> None:
        if service in self._services:
            return  # do nothing if the service is already at this cloud

        # remove the service from the previous cloud
        if service.get_cloud():
            service.get_cloud().remove_service(service)

        service.set_cloud(self)
        self._services.append(service)
        self._total_memory_requirement += service.get_memory_requirement()
        if self._total_memory_requirement > self._memoryCapacity:
            raise LimitedMemoryCloud.CloudOverallocatedException()

    def remove_service(self, service: Any) -> None:
        if service in self._services:
            self._total_memory_requirement -= service.get_memory_requirement()
            self._services.remove(service)
        assert self._total_memory_requirement >= 0

    # def __calculate_total_memory_requirement(self) -> float:
    #     memory_requirement: float = 0.0
    #     for service in self.services():
    #         memory_requirement += service.memory_requirement
    #     assert memory_requirement <= self._memoryCapacity
    #     return memory_requirement

    def total_memory_requirement(self) -> float:
        return self._total_memory_requirement

    def memory_capacity(self) -> float:
        return self._memoryCapacity

    def free_memory_capacity(self) -> float:
        return max(0.0, self._memoryCapacity - self._total_memory_requirement)
