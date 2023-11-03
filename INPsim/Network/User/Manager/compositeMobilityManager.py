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


from INPsim.Network.User.Manager.userManager import UserManager


class CompositeMobilityManager(UserManager):
    def __init__(self, service_model, user_manager_list):
        """
        Allows to combine multiple other mobility managers under the same interface
        and the composition of different types of service mobilities in one system
        :param user_manager_list: list of user manager/ movement models which should be used
        """
        super(
            CompositeMobilityManager,
            self).__init__(
            service_model=service_model)
        self.user_manager_list = user_manager_list

    def step(self, time_step):
        for user_manager in self.user_manager_list:
            user_manager.step(time_step)

    def create_user(self, movement_model):
        for user_manager in self.user_manager_list:
            user_manager.create_user(movement_model)

    def remove_user(self, user):
        for user_manager in self.user_manager_list:
            user_manager.remove_user(user)

    def users(self):
        for user_manager in self.user_manager_list:
            user_manager.users()

    def services(self):
        for user_manager in self.user_manager_list:
            user_manager.services()

    def num_services(self):
        for user_manager in self.user_manager_list:
            user_manager.num_services()