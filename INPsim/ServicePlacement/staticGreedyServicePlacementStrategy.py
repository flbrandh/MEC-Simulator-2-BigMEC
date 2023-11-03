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


from typing import Iterable, Tuple, List
from .servicePlacementStrategy import ServicePlacementStrategy
from INPsim.Network.network import CloudNetwork
from INPsim.Network.Service import Service
from INPsim.Network.User.user import User
from INPsim.Network.User.Manager import UserManager
from INPsim.Network.Nodes.cloud import LimitedMemoryCloud
from INPsim.ServicePlacement.Migration.Action import Action, InitialPlacementAction


class StaticGreedyServicePlacementStrategy(ServicePlacementStrategy):
    """
    This service placement_cost strategy statically assigns the lowest latency cloudlet to every service upon creation.
    """

    def update_service_placements(
            self,
            cloud_network: CloudNetwork,
            user_manager: UserManager,
            time_step: float) -> List[Action]:
        """
        Updates the service placement_cost if necessary in this step.
        :param cloud_network: the cloud network
        :param user_manager: the user manager
        :param time_step: the time step between this call and the last call of this method
        :return: List of all updated services
        """
        actions: List[Action] = []
        num_clouds = len(cloud_network.clouds())
        for service in user_manager.services():

            if not service.get_cloud():  # this means the service is new.
                owner = service.owner()
                if isinstance(owner, User):
                    user: User = owner
                else:
                    raise Exception('Class StaticGreedyServicePlacementStrategy expected a User as service owner.')
                nearest_clouds: Iterable[Tuple[LimitedMemoryCloud, float]] = cloud_network.get_nearest_clouds(user.get_base_station(), num_clouds)
                for cloud, distance in nearest_clouds:
                    if cloud.free_memory_capacity() >= service.get_memory_requirement():
                        cloud.add_service(service)
                        actions.append(InitialPlacementAction(service, cloud))
                        break

        return actions
