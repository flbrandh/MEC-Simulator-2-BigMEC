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


from typing import Optional, Iterable, List
import numpy as np

from .SimulationInterface import SimulationInterface
from .SimulationObserver import SimulationObserver

from INPsim.Network.RANModel import NearestNeighborRANModel
from INPsim.Network.network import CloudNetwork
from INPsim.Network.Nodes.cloud import Cloud
from INPsim.ServicePlacement import ServicePlacementStrategy
from INPsim.Network.User.user import User
from INPsim.Network.User.Manager.userManager import UserManager
from INPsim.Network.Service.service import Service
from INPsim.ServicePlacement.Migration.Action import Action



class Simulation(SimulationInterface):

    def __init__(self,
                 cloud_network: CloudNetwork,
                 user_manager: UserManager,
                 service_placement_strategy: ServicePlacementStrategy) -> None:
        """
        Configures a simulation with a specific setup.
        :param self: self
        :param cloud_network: The cloud network that defines the clouds' positions and internetworking.
        :param user_manager: UserManager that manages users and their movement.
        :param service_placement_strategy: The service placement_cost strategy of the simulation.
        """
        self._time_step = 1  # time step is one second.
        self._current_step = 0
        self._user_manager = user_manager
        self._cloud_network = cloud_network
        self._ran_model = NearestNeighborRANModel(self._cloud_network.base_stations(), 40)
        self._service_placement_strategy = service_placement_strategy

    def get_service_placement_strategy(self) -> ServicePlacementStrategy:
        """
        Returns the service placement_cost strategy of this simulation.
        :return: ServicePlacementStrategy Object.
        """
        return self._service_placement_strategy

    def get_cloud_network(self) -> CloudNetwork:
        """
        Returns the cloud network that this simulation is using.
        :return: CloudNetwork obj of this simulation
        """
        return self._cloud_network

    def get_user_manager(self) -> UserManager:
        """
        Returns this simulation's user manager
        :return: UserManager obj of this simulation
        """
        return self._user_manager

    def get_clouds(self) -> Iterable[Cloud]:
        """
        Returns the clouds/cloudlets of in the Network that the simulation is running on.
        :return: Iterable of all clouds/cloudlets
        """
        return self._cloud_network.clouds()

    def get_users(self) -> Iterable[User]:
        """
        Returns the users in the simulation.
        :return: Iterable of all Users at the current step.
        """
        return self._user_manager.users()

    def get_services(self) -> Iterable[Service]:
        """
        Returns the services in the simulation.
        :return: Iterable of all Services at the current step.
        """
        return self._user_manager.services()

    def get_num_services(self) -> int:
        """
        Returns the number of services in the current simulation state.
        :return: non-negative number of services
        """
        return self._user_manager.num_services()

    def get_current_step(self) -> int:
        """
        Returns the index of the current/last finished step.
        :return: positive integer index of the step, starting at 0
        """
        return self._current_step

    def simulate(self, num_steps: int, observer: Optional[SimulationObserver] = None) -> None:
        """
        Executes a specified number of configured_simulation steps.
        :param num_steps: number of steps to execute
        :param observer: a SimulationObserver Object that can be used to get callbacks before and after each configured_simulation step.
        :return: None
        """
        for i in range(num_steps):
            self.step(observer)

    def __assign_users_to_base_stations(self, users: Iterable[User]) -> None:
        """
        Assigns the users to their new base stations if their closest base station changed since the last step.
        :param users: list of users
        """
        for user in users:
            new_closest_base_station = self._ran_model.get_closest_base_station(
                    user.get_movement_model().get_pos())
            assert new_closest_base_station
            if new_closest_base_station is not user.get_base_station():
                user.set_base_station(new_closest_base_station)

    def step(self, observer: Optional[SimulationObserver] = None) -> None:
        # notify the observer of the beginning of the step:
        if observer:
            observer.before_simulation_step(self)

        # move users one time step
        self._user_manager.step(self._time_step)

        # assign users to new base stations
        self.__assign_users_to_base_stations(self.get_users())

        # execute the service placement_cost strategy
        performed_actions: List[Action] = self._service_placement_strategy.update_service_placements(
                        cloud_network=self._cloud_network,
                        user_manager=self._user_manager,
                        time_step=self._time_step)

        # safety check: no cloud is over-allocated
        for cloud in self.get_cloud_network().clouds():
            assert cloud.memory_capacity() >= cloud.total_memory_requirement()
            assert cloud.total_memory_requirement() >= 0

        # notify the observer of the end of the step:
        if observer:
            observer.after_simulation_step(self, performed_actions)

        # some logging:
        central_cloud = self.get_cloud_network().central_cloud()
        # print("services @ cloud: ", 100*float(len(central_cloud.services()))/float(len(self.user_manager().users())),"%")
        print("mean priority @cloud: ", np.mean([s.priority for s in central_cloud.services()]), " #services @cloud:", len(central_cloud.services()))

        # increase step:
        self._current_step += 1
