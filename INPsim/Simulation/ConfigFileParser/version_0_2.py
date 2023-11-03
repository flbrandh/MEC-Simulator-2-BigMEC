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


from typing import Any, Dict, Tuple, Optional

from INPsim.Simulation import Simulation, StatisticsSimulationObserver
from INPsim.ServicePlacement import ServicePlacementStrategy, StaticGreedyServicePlacementStrategy, MyopicOptimalServicePlacementStrategy
from INPsim.Network.network import CloudNetwork
from INPsim.ServicePlacement.Migration.CostFunctions import PerServiceGlobalAverageCostFunction, ServiceCostFunction
from INPsim.Simulation.ConfigFileParser.parsingUtilities import parse_non_negative_int, parse_object, parse_str_options
from INPsim.ServicePlacement.Migration.CloudCandidateSelector import DestinationCloudCandidateSelectorInterface, KnnBaseStationNeighborhoodBasedCandidateSelector
from .version_0_1 import Version_0_1


class Version_0_2:

    @staticmethod
    def configure_simulation(
            configuration: Dict[str, Any], configuration_path: str) -> Tuple[Simulation, StatisticsSimulationObserver, int]:
        """
        Configures a configured_simulation from a containing_object of the 0.2 format.
        :param configuration: parsed json config
        :param configuration_path: path to which all paths in the config are relative to (typically the path of the containing_object file)
        :return: Tuple of configured Simulation, StatisticsSimulationObserver, and the number of simulation steps
        """
        num_simulation_steps = parse_non_negative_int(configuration, 'num_simulation_steps')

        # build network
        network, network_aabb = Version_0_1.configure_cloud_network(configuration)

        # configure the cost function
        service_cost_function = Version_0_1.configure_cost_function(configuration, network)

        # configure the user manager
        service_model = Version_0_1.configure_service_model(configuration)
        user_manager = Version_0_1.configure_user_manager(configuration, service_model, network_aabb)

        # configure the service placement_cost strategy
        service_placement_strategy = Version_0_2.configure_service_placement_strategy(configuration,
                                                                                      configuration_path,
                                                                                      network,
                                                                                      service_cost_function)

        simulation = Simulation(cloud_network=network,
                                user_manager=user_manager,
                                service_placement_strategy=service_placement_strategy)

        statistics_simulation_observer = StatisticsSimulationObserver(PerServiceGlobalAverageCostFunction(service_cost_function))

        return simulation, statistics_simulation_observer, num_simulation_steps

    @staticmethod
    def configure_service_placement_strategy(containing_object: Dict[str, Any],
                                             configuration_path: str,
                                             network: CloudNetwork,
                                             service_cost_function: ServiceCostFunction) -> ServicePlacementStrategy:
        """
        Parses and configures a ServicePlacementStrategy.
        :param containing_object: The object that contains the 'service_placement_strategy' object.
        :param configuration_path: The path of the containing_object file.
        :param network: The CloudNetwork that the simulation is using.
        :param service_cost_function: The cost function of the services.
        :return: A configured service cost function
        """

        service_placement_strategy_object: Dict[str, Any] = parse_object(containing_object, 'service_placement_strategy')
        strategy_type: str = parse_str_options(service_placement_strategy_object, 'type', ['independent', 'static-greedy', 'myopic-optimal'])

        if strategy_type == 'independent':
            return Version_0_1.configure_service_placement_strategy(service_placement_strategy_object,
                                                                    configuration_path,
                                                                    network,
                                                                    service_cost_function)
        elif strategy_type == 'static-greedy':
            return StaticGreedyServicePlacementStrategy()
        elif strategy_type == 'myopic-optimal':
            update_interval = parse_non_negative_int(service_placement_strategy_object, 'update-interval')
            neighborhood: Optional[DestinationCloudCandidateSelectorInterface] = None
            if "neighborhood_size" in service_placement_strategy_object:
                neighborhood_size = parse_non_negative_int(service_placement_strategy_object, "neighborhood_size")
                neighborhood = KnnBaseStationNeighborhoodBasedCandidateSelector(neighborhood_size, network)
            return MyopicOptimalServicePlacementStrategy(service_cost_function=service_cost_function,
                                                         update_interval=update_interval,
                                                         cloud_candidate_selector=neighborhood)
        else:
            raise Exception('Service placement_cost strategy "' + strategy_type + 'does not exist!')
