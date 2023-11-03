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


from typing import Dict, List, Optional
import gurobipy as grb
import numpy as np
import time
import copy

from .servicePlacementStrategy import ServicePlacementStrategy
from .Migration.Action import Action, InitialPlacementAction, MigrationAction, NoMigrationAction

from INPsim.Network.network import CloudNetwork
from INPsim.Network.Service import Service
from INPsim.Network.User.user import User
from INPsim.Network.User.serviceOwner import ServiceOwner
from INPsim.Network.User.Manager import UserManager
from INPsim.Network.Nodes.cloud import Cloud, LimitedMemoryCloud
from INPsim.ServicePlacement.Migration.CostFunctions import ServiceCostFunction
from INPsim.ServicePlacement.Migration.CloudCandidateSelector import DestinationCloudCandidateSelectorInterface
from INPsim.Utils.runningMean import RunningMean


class MyopicOptimalServicePlacementStrategy(ServicePlacementStrategy):

    def __init__(self, service_cost_function: ServiceCostFunction, update_interval: int, cloud_candidate_selector: Optional[DestinationCloudCandidateSelectorInterface] = None):
        """
        Initializes the Service Placement Strategy.
        :param service_cost_function: Per-service cost function that is used to evaluate each possible placement in order to find a global cost-optimum (only static placement cost is considered, not the transition cost!)
        :param update_interval: Placement will be updated every update_interval number of calls to update_service_placements()
        """
        self._service_cost_function = service_cost_function
        self._update_interval: int = update_interval
        self._steps_since_update: int = 0
        self._cloud_candidate_selector: Optional[DestinationCloudCandidateSelectorInterface] = cloud_candidate_selector
        self._mean_computation_time: RunningMean = RunningMean()
        self._mean_communication_time: Optional[float] = None

    def get_mean_computation_time(self) -> Optional[float]:
        """
        Returns the mean computation time.
        :return: The mean computation time if there is a mean. If not, None.
        """
        return self._mean_computation_time.get_mean()

    def get_mean_communication_time(self) -> Optional[float]:
        """
        Returns the mean communication time.
        :return: The mean communication time, if known.
        """
        return self._mean_communication_time

    def _calculate_mean_communication_time(self, cloud_network: CloudNetwork):
        cloud_node = cloud_network.central_cloud().node()
        max_cloud_hops = max([cloud_network.dist_to_node(cloud_node, c.node()) for c in cloud_network.clouds()])
        self._mean_communication_time = 2 * max_cloud_hops * 0.001  # also converting ms to s

    def update_service_placements(
            self,
            cloud_network: CloudNetwork,
            user_manager: UserManager,
            time_step: float) -> List[Action]:
        """
        Updates the service placement_cost if necessary in this step.
        :param cloud_network: the cloud network
        :param user_manager: the user manager
        :param time_step: the timestep between this call and the last call of this method
        :return: List of all updated services
        """

        if not self._mean_communication_time:
            self._calculate_mean_communication_time(cloud_network)

        # 1) Check if it's actually time to update the placement_cost and return if not.
        if self._steps_since_update != 0:
            # Ensure that even if no optimization is performed, every service is placed
            # (unplaced are assigned to the central cloud, all other placements remain as they were)
            return self._place_unplaced_services_at_central_cloud(cloud_network, user_manager)

        self._steps_since_update = (self._steps_since_update + 1) % self._update_interval

        # 2) Update the placement_cost.
        prev_placements: Dict[Service, Optional[Cloud]] = dict([(s, s.get_cloud()) for s in user_manager.services()])

        # 3) recompute and apply the service placement_cost using ILP

        start = time.time()
        self._execute_myopic_optimal_service_placement(cloud_network, user_manager)
        end = time.time()
        print("The optimization took ", end - start, "s.")
        self._mean_computation_time.add_sample(end - start)

        # 4) List the performed actions
        # TODO this is just a lower bound! To get an accurate understanding of the required migrations considering
        #  incremental space constraints would require searching for an optimal migration plan!
        actions: List[Action] = []
        for service in user_manager.services():
            if prev_placements[service] is None:
                actions.append(InitialPlacementAction(service, service.get_cloud()))
            elif service.get_cloud() == prev_placements[service]:
                actions.append(NoMigrationAction(service, service.get_cloud()))
            else:
                actions.append(MigrationAction(service, prev_placements[service], service.get_cloud()))
        return actions

    def _place_unplaced_services_at_central_cloud(self, cloud_network: CloudNetwork, user_manager: UserManager) -> List[Action]:
        """
        Places every unplaced service at the central cloud.
        :param cloud_network: the cloud network
        :param user_manager: the user manager
        :return: List of all actions that were incurred by the initial placement_cost
        """
        actions: List[Action] = []
        central_cloud: LimitedMemoryCloud = cloud_network.central_cloud()
        for service in user_manager.services():
            if not service.get_cloud():  # this means the service is new.
                owner = service.owner()
                if isinstance(owner, User):
                    user: User = owner
                else:
                    raise Exception('Class StaticGreedyServicePlacementStrategy expected a User as service owner.')
                central_cloud.add_service(service)
                actions.append(InitialPlacementAction(service, central_cloud))
        return actions

    def _execute_myopic_optimal_service_placement(self, cloud_network: CloudNetwork, user_manager: UserManager) -> None:
        """
        Calculates and applies a myopic optimal service placement_cost using an ILP solver.
        :param cloud_network: The cloud network containing the clouds and their connection lengths
        :param user_manager: The user manager containing users and associated services
        :return: Nothing; the new placement_cost is applied directly.
        """

        # 1) gather data
        services: List[Service] = list(user_manager.services())
        clouds: List[LimitedMemoryCloud] = cloud_network.clouds()
        num_services: int = len(services)
        num_clouds: int = len(clouds)
        memory_capacities: List[float] = [c.memory_capacity() for c in clouds]
        service_memory_requirements: List[float] = [s.get_memory_requirement() for s in services]

        def get_cost(s: Service, c: LimitedMemoryCloud) -> float:
            owner: ServiceOwner = s.owner()
            if isinstance(owner, User):
                # this is a hack to evaluate the service cost for positions that don't exist
                original_last_cloud = s.get_last_cloud()
                original_cloud = s.get_cloud()
                s.set_cloud(c)
                placement_cost: float = self._service_cost_function.calculate_cost(cloud_network, s, []).placement_cost()
                s.set_cloud(original_last_cloud)
                s.set_cloud(original_cloud)
                return placement_cost
                # return cloud_network.dist_to_node(owner.get_base_station(), c.node())
            else:
                raise Exception('Expected a User as ServiceOwner!')

        service_cloud_cost_matrix: List[List[float]] = [[get_cost(s, c) for c in clouds] for s in services]

        service_cloud_candidates: Dict[Service, List[Cloud]] = dict()
        service_cloud_candidate_indices: Dict[int, List[int]] = dict()
        for service_index, service in enumerate(services):
            cloud_candidates: List[Cloud] = []
            cloud_candidate_indices: List[int] = []
            for cloud_index, cloud in enumerate(clouds):
                if self._cloud_is_viable_candidate(cloud, service):
                    cloud_candidates.append(cloud)
                    cloud_candidate_indices.append(cloud_index)
            service_cloud_candidates[service] = cloud_candidates
            service_cloud_candidate_indices[service_index] = cloud_candidate_indices

        # 2) configure the optimization model
        opt_model = grb.Model(name="MIP Model")
        # placement_cost decision variables
        x_vars = {(s, c): opt_model.addVar(lb=0,  # lower bound
                                           ub=1,  # upper bound
                                           obj=0,  # objective coefficient (no idea what this is)
                                           vtype=grb.GRB.BINARY,  # variable type
                                           name="x_{0}_{1}".format(s, c),  # variable name
                                           column=None)  # column object that indicates the set of constraints in which the new variable participates
                  for s in range(num_services) for c in service_cloud_candidate_indices[s]}

        # every service placed constraint
        user_to_one_node_constraints = {s: opt_model.addConstr(grb.quicksum(x_vars[s, n] for n in service_cloud_candidate_indices[s]) == 1,
                                                               name="user_to_one_node_constraint_{0}".format(s))
                                        for s in range(num_services)}

        # memory constraint
        memory_constraints = {c: opt_model.addConstr(
                grb.quicksum(service_memory_requirements[s] * x_vars[s, c] for s in range(num_services) if c in service_cloud_candidate_indices[s]) <= memory_capacities[c],
                name="node_memory_constraint_{0}".format(c))
            for c in range(num_clouds)}

        # objective
        objective = grb.quicksum(x_vars[s, c] * service_cloud_cost_matrix[s][c]
                                 for s in range(num_services)
                                 for c in service_cloud_candidate_indices[s])
        opt_model.ModelSense = grb.GRB.MINIMIZE
        opt_model.setObjective(objective)

        # 3) solve the model
        opt_model.setParam(grb.GRB.Param.OutputFlag, 0)
        opt_model.optimize()

        # 4) apply the solution
        if opt_model.Status == grb.GRB.OPTIMAL:
            # register each service to its new cloud
            for service_index, service in enumerate(services):
                for c in service_cloud_candidate_indices[service_index]:
                    if x_vars[service_index, c].X > 0.5:
                        try:
                            clouds[c].add_service(service)
                        except LimitedMemoryCloud.CloudOverallocatedException:
                            pass  # ignore momentary cloud overallocation (could be an interesting statistic though)
                        break # stop since there can only be one cloud per service.
        else:
            print("model infeasible")
            # do nothing if optimization failed...

        # print("|")
        # print("V service, cloud ->")
        # col_sums = [0]*num_clouds
        # for si in range(num_services):
        #     line = ''
        #     line_sum = 0
        #     for ci in range(num_clouds):
        #         if not (si, ci) in x_vars:
        #             line += '- , '
        #         else:
        #             line += f'{int(x_vars[si, ci].X):01d} , '
        #             line_sum += x_vars[si, ci].X
        #             col_sums[ci] += x_vars[si, ci].X
        #     print(f's{si:02d}| ' + line + '= '+str(line_sum))
        # print('     '+"-"*num_clouds*3)
        # print('     '+''.join(f'{int(s):02d} ,' for s in col_sums))

        for cloud in clouds:
            assert cloud.memory_capacity() >= cloud.total_memory_requirement()
            assert cloud.total_memory_requirement() >= 0


    def _cloud_is_viable_candidate(self, cloud: Cloud, service: Service) -> bool:
        """
        Checks if a cloud is a viable placement candidate for a service.
        :param cloud:  Cloud for which should be determined, if it is viable for the service.
        :param service: Service that is to be placed.
        :return: True, if cloud is viable for service, False if not
        """
        if self._cloud_candidate_selector:
            return cloud in self._cloud_candidate_selector.get_candidate_clouds(service)
        else:
            return True
