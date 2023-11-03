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
from INPsim.Network.Nodes import cloud
from .action import Action


class MigrationAction(Action):
    """
    Represents a migration action
    """

    def __init__(
            self,
            service: Service,
            source_cloud: cloud,
            target_cloud: cloud) -> None:
        self._service = service
        self._target_cloud = target_cloud
        self._source_cloud = source_cloud
        #assert source_cloud is service.get_cloud()
        assert source_cloud is not target_cloud

    def get_service(self) -> Service:
        return self._service

    def get_target_cloud(self) -> cloud:
        return self._target_cloud
