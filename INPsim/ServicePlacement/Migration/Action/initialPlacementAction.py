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


from .action import Action
from INPsim.Network.Service import  Service
from INPsim.Network.Nodes import Cloud



class InitialPlacementAction(Action):
    """
    Represents an initial placement_cost action.
    """

    def __init__(self, service: Service, cloud: Cloud):
        """
        Initializes the action with its parameters.
        :param service: The service that is placed.
        :param cloud: The that the service is placed to initially.
        """
        self._service = service
        self._cloud = cloud

    def get_service(self) -> Service:
        """
        Returns the service of this initial placement_cost action.
        :return: the service that is initially placed.
        """
        return self._service

    def get_cloud(self) -> Cloud:
        """
        Returns the cloud of this initial placement_cost action.
        :return: the cloud that the service is initially placed at
        """
        return self._cloud
