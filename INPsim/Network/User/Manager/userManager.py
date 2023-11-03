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


from INPsim.Network.User.user import User


class UserManager:
    """
    Manages user creation, destruction and movement.
    """

    def __init__(self, service_model):
        """
        Initializes a user manager.
        """
        self._users = set()
        self._service_model = service_model

    def step(self, time_step):
        """
        Advances th user configured_simulation one step.
        :param time_step: the length of time since the last step in seconds.
        :return:
        """
        for user in self._users:
            user.get_movement_model().step(time_step)

    def create_user(self, movement_model):
        """
        Adds a new user with services according to the service model.
        :param movement_model: movement model of the new user
        :return:
        """
        new_user = User(
            movement_model,
            self._service_model.create_user_services())
        self._users.add(new_user)
        return new_user

    def remove_user(self, user):
        """
        Removes a user and its associated services.
        :param user:
        :return:
        """
        user.remove_all_services()
        self._users.remove(user)

    def users(self):
        return self._users

    def services(self):
        for user in self._users:
            for service in user.services():
                yield service

    def num_services(self):
        sum = 0
        for user in self._users:
            sum += len(user.services())
        return sum

