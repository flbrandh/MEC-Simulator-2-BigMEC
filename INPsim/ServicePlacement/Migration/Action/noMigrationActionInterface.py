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


from INPsim.Network.Service.service import Service
from INPsim.Network.Nodes import Cloud
from .action import Action


class NoMigrationAction(Action):
    """
    Represents a no-migration action (stay at cloud)
    """

    def __init__(self, service: Service, cloud: Cloud) -> None:
        self._service = service
        self._cloud = cloud
        assert self._service.get_cloud() is self._cloud

    def get_service(self) -> Service:
        return self._service

    def get_cloud(self) -> Cloud:
        return self._cloud
