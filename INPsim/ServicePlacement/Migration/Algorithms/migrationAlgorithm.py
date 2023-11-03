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


import abc
from INPsim.Network import CloudNetwork
from INPsim.Network.Service import Service
from INPsim.Network.Nodes import Cloud


class MigrationAlgorithm:

    class Instance:

        @abc.abstractmethod
        def process_migration_event(self, service: Service):
            """
            determines migration actions for a cloud at a migration event
            :param service: the service that this function was invoked for
            :return: MigrationEvent or NoMigrationEvent
            """
            pass

        def give_reward(self, reward: float):
            """
            This function gives an immediate reward for the last action. If this method isn't called, the reward for the last action is 0.
            :param reward: a numerical reward
            :return: None
            """
            pass

    @abc.abstractmethod
    def create_instance(self, cloud: Cloud, cloud_network: CloudNetwork):
        """
        This factory function creates an instance of a migration algorithm for a specific cloud.
        :param cloud: cloud of the created algorithm instance
        :param cloud_network: network that the instance operates in
        :return: an Algorithm Instance obj
        """