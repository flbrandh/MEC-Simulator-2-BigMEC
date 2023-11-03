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


from INPsim.Network.User.serviceOwner import ServiceOwner
from .MovementModel.interface import MovementModel


class User(ServiceOwner):
    """
    Describes a user.
    """

    def __init__(self, movement_model: MovementModel, services):
        """
        initializes the user.
        :param movement_model: The movement model of the user
        :param services: the services that this user is initialized with.
        """
        super(User, self).__init__()
        self._base_station = None
        self._previous_base_station = None
        self._movement_model: MovementModel = movement_model

        for service in services:
            self.add_service(service)

    def get_movement_model(self) -> MovementModel:
        """
        Returns this User's movement model, which defines its location over time.
        :return: this user's MovementModel object
        """
        return self._movement_model

    def get_base_station(self):
        return self._base_station

    def get_previous_base_station(self):
        return self._previous_base_station

    def set_base_station(self, base_station):
        if base_station != self._base_station:  # ignore re-assignments of the same base station
            self._previous_base_station = self._base_station
            self._base_station = base_station
