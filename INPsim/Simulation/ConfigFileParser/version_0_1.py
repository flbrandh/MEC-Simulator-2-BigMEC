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


import os
import pickle
import random
from typing import Any, Dict, Tuple

from INPsim.ServicePlacement import ServicePlacementStrategy
from INPsim.Simulation import StatisticsSimulationObserver
from INPsim.ServicePlacement.Migration.Algorithms import InitialPlacementAtClosestCloudletWithAvailableResources, InitialPlacementAtCloud, \
    MigrationAlgorithm, evalMigrationAlgorithms, basicMigrationAlgorithms, MigrationAlgorithmServicePlacementStrategy, InitialPlacementStrategy
from INPsim.ServicePlacement.Migration.CostFunctions import PerServiceGlobalAverageCostFunction, ServiceCostFunction, basicCostFunctions, heterogeneousCostFunctions
from INPsim.ServicePlacement.Migration.Learning.Features import ConfigurableFeatures
from INPsim.ServicePlacement.Migration.Learning import QHyperparameters
from INPsim.ServicePlacement.Migration.Learning.learn import DQNMigrationAlgorithm
from INPsim.Network.Service import Service, ServiceModel, ConstantServiceModel, PrototypeBasedServiceConfigurator
from INPsim.Network.User.Manager import UserManager, ConstantRandomUserManager, MobilityTraceUserManager
from INPsim.Network.generator import generate_san_francisco_cloud_network
from INPsim.Network.network import CloudNetwork
from INPsim.Simulation import simulator
from INPsim.Simulation.ConfigFileParser.parsingUtilities import parse_bool, parse_int, parse_non_negative_float, parse_non_negative_int, \
    parse_object, parse_str, parse_str_options
from INPsim.vmath import AABB2


class Version_0_1:

    @staticmethod
    def configure_simulation(
            configuration: Dict[str, Any], configuration_path: str) -> Tuple[simulator.Simulation, StatisticsSimulationObserver, int]:
        """
        configures a configured_simulation from a containing_object of the 0.1 format.
        :param configuration: parsed json config
        :param configuration_path: path to which all paths in the config are relative to (typically the path of the containing_object file)
        :return: Tuple of a configured Simulation, StatisticsSimulationObserver, and number of simulation steps
        """
        num_simulation_steps = parse_non_negative_int(configuration, 'num_simulation_steps')

        # build network
        network, network_aabb = Version_0_1.configure_cloud_network(configuration)

        # configure the cost function
        service_cost_function = Version_0_1.configure_cost_function(configuration, network)

        # configure the user manager
        service_model = Version_0_1.configure_service_model(configuration)
        user_manager = Version_0_1.configure_user_manager(configuration, service_model, network_aabb)

        # configure the service placement_cost strategy (always a MigrationAlgorithmServicePlacementStrategy)
        service_placement_strategy = Version_0_1.configure_service_placement_strategy(configuration,
                                                                                      configuration_path,
                                                                                      network,
                                                                                      service_cost_function)

        simulation = simulator.Simulation(cloud_network=network,
                                          user_manager=user_manager,
                                          service_placement_strategy=service_placement_strategy)

        statistics_simulation_observer = StatisticsSimulationObserver(PerServiceGlobalAverageCostFunction(service_cost_function))

        return simulation, statistics_simulation_observer, num_simulation_steps

    @staticmethod
    def configure_cloud_network(configuration: Dict[str, Any]) -> Tuple[CloudNetwork, AABB2]:
        """
        Configures a simulation's cloud network.
        :param configuration: The root containing_object object.
        :return: a fully configured cloud network to be used in a simulation and its bounding box
        """
        network_config = parse_object(configuration, 'network_generator')
        network_type = parse_str_options(network_config, 'type', ['san_francisco'])
        if network_type == 'san_francisco':
            topology = parse_str_options(network_config, 'topology', ['delaunay', '2-tier-hierarchical'])
            num_clouds = parse_non_negative_int(network_config, 'num_clouds')
            cloudlet_memory_capacity = parse_non_negative_int(network_config, 'cloudlet_memory_capacity')
            cloud_memory_capacity = parse_non_negative_int(network_config, 'cloud_memory_capacity')
            random_seed = parse_non_negative_int(network_config, 'random_seed', default_value=42)
            network = generate_san_francisco_cloud_network(
                    topology=topology,
                    num_clouds=num_clouds,
                    cloudlet_memory_capacity=cloudlet_memory_capacity,
                    cloud_memory_capacity=cloud_memory_capacity,
                    random_seed=random_seed)
            network_aabb = AABB2(
                    542688.443644256,
                    556765.7262020159,
                    4161556.7164416737,
                    4185052.3668366373)  # Zone 10S, San Francisco (peninsula in the SF Bay)
            return network, network_aabb

    @staticmethod
    def configure_cost_function(configuration: Dict[str, Any], network: CloudNetwork) -> ServiceCostFunction:
        """
        Parses and configures a cost function.
        :param configuration: The root containing_object object.
        :param network: The CloudNetwork Object that is used in the simulation.
        :return: a configured ServiceCostFunction object
        """
        cost_function_config = parse_object(configuration, 'cost_function')
        cost_function_type = parse_str_options(cost_function_config,
                                               'type',
                                               ['latency',
                                                'squared_latency_with_migration_cost',
                                                'priority_based_latency_with_migration_cost',
                                                'sla'])

        if cost_function_type == 'latency':
            return basicCostFunctions.LatencyCostFunction(network)

        elif cost_function_type == 'squared_latency_with_migration_cost':
            migration_cost = parse_non_negative_float(
                    cost_function_config,
                    'migration_cost',
                    default_value=5.0)
            latency_cost_factor = parse_non_negative_float(
                    cost_function_config,
                    'latency_cost_factor',
                    default_value=1.0)
            return heterogeneousCostFunctions.SquaredLatencyPlusMigrationCost(network, migration_cost, latency_cost_factor)

        elif cost_function_type == 'priority_based_latency_with_migration_cost':
            migration_cost = parse_non_negative_float(
                    cost_function_config,
                    'migration_cost',
                    default_value=5.0)
            latency_cost_factor = parse_non_negative_float(
                    cost_function_config,
                    'latency_cost_factor',
                    default_value=1.0)
            return heterogeneousCostFunctions.PriorityBasedCostFunction(network, migration_cost, latency_cost_factor)

        elif cost_function_type == 'sla':
            migration_cost = parse_non_negative_float(
                    cost_function_config,
                    'migration_cost',
                    default_value=5.0)
            latency_cost_factor = parse_non_negative_float(
                    cost_function_config,
                    'latency_cost_factor',
                    default_value=1.0)
            return heterogeneousCostFunctions.SLACostFunction(network, migration_cost, latency_cost_factor)

    @staticmethod
    def configure_service_model(configuration: Dict[str, Any]) -> ServiceModel:
        """
        Parses and configures a service model.
        :param configuration: The root of the containing_object JSON object.
        :return: a configured ServiceModel Object.
        """
        service_model_config = parse_object(configuration, 'service_model')
        service_model_type = parse_str_options(
                service_model_config, 'type', ['constant'])

        if service_model_type == 'constant':
            services_per_user = parse_non_negative_int(
                    service_model_config, 'services_per_user')
            service_config = parse_object(
                    service_model_config,
                    'service_configuration')
            service_config_type = parse_str_options(
                    service_config, 'type', ['prototype'])

            if service_config_type == 'prototype':
                if 'memory_requirement' in service_config:
                    if 'min_memory_requirement' in service_config or 'max_memory_requirement' in service_config:
                        raise Exception("Error: redundant definition of memory requirements")
                    memory_req = parse_non_negative_int(service_config, 'memory_requirement')
                    min_memory_req = max_memory_req = memory_req
                else:
                    min_memory_req = parse_non_negative_int(service_config, 'min_memory_requirement')
                    max_memory_req = parse_non_negative_int(service_config, 'max_memory_requirement')
                min_priority = parse_non_negative_int(service_config, 'min_priority', default_value=1)
                max_priority = parse_non_negative_int(service_config, 'max_priority', default_value=100)

                if 'latency_requirement' in service_config:
                    if 'min_latency_requirement' in service_config or 'max_latency_requirement' in service_config:
                        raise Exception("Error: redundant definition of latency requirements")
                    latency_req = parse_non_negative_int(service_config, 'latency_requirement')
                    min_latency_req = max_latency_req = latency_req
                else:
                    min_latency_req = parse_non_negative_int(service_config, 'min_latency_requirement')
                    max_latency_req = parse_non_negative_int(service_config, 'max_latency_requirement')
                service_configurator = PrototypeBasedServiceConfigurator(
                        Service(memory_requirement=0,
                                latency_requirement=0),
                        min_priority=min_priority,
                        max_priority=max_priority,
                        min_memory_requirement=min_memory_req,
                        max_memory_requirement=max_memory_req,
                        min_latency_requirement=min_latency_req,
                        max_latency_requirement=max_latency_req)
                return ConstantServiceModel(
                        service_configurator=service_configurator,
                        services_per_user=services_per_user)

    @staticmethod
    def configure_user_manager(configuration: Dict[str, Any],
                               service_model: ServiceModel,
                               network_aabb: AABB2) -> UserManager:
        """
        Parses and configures a UserManager from a JSON containing_object.
        :param configuration: The root JSON object of the containing_object.
        :param service_model: The ServiceModel that specifies the user's service request patterns.
        :param network_aabb: The network's bounding box (may be required to box in random user movements)
        :return: A configured UserManager
        """
        user_model_config = parse_object(configuration, 'user_model')
        user_model_type = parse_str_options(
                user_model_config, 'type', [
                    'random_waypoints', 'random_brownian', 'cabspotting', 'cabspotting_one_day'])
        if user_model_type == 'random_waypoints' or user_model_type == 'random_brownian':
            movement_type_dict = {'random_waypoints': 'linear',
                                  'random_brownian':  'brownian'}
            movement_type = movement_type_dict[user_model_type]
            user_mobility_random_seed = parse_int(user_model_config, 'random_seed', default_value=42)
            num_users = parse_non_negative_int(user_model_config, 'num_users')
            waypoint_rng = random.Random()
            waypoint_rng.seed(user_mobility_random_seed)
            return ConstantRandomUserManager(service_model=service_model,
                                             rng=waypoint_rng,
                                             movement_type=movement_type,
                                             num_users=num_users,
                                             aabb=network_aabb)
        elif user_model_type == 'cabspotting' or user_model_type == 'cabspotting_one_day':
            dataset_name_dict = {'cabspotting':         'cabspotting_san_francisco',
                                 'cabspotting_one_day': 'cabspotting_san_francisco_one_day'}
            return MobilityTraceUserManager(
                    service_model=service_model, dataset=dataset_name_dict[user_model_type])

    @staticmethod
    def configure_migration_algorithm(containing_object: Dict[str, Any],
                                      configuration_path: str) -> MigrationAlgorithm:
        """
        Parses and configures a migration algorithm from a JSON containing_object.
        :param containing_object: The object that contains the 'migration_strategy' object.
        :param configuration_path: The path of the containing_object; May be needed to find files with relative paths.
        :return: a configured migration algorithm
        """
        migration_strategy_config = parse_object(
                containing_object, 'migration_strategy')
        migration_strategy_type = parse_str_options(
                migration_strategy_config, 'type', [
                    'never', 'always', 'always_neighborhood', 'isa_heuristic', 'highest_utility_greedy', 'highest_utility_displacing'])

        if migration_strategy_type == 'never':
            return basicMigrationAlgorithms.NeverMigrateAlgorithm()

        elif migration_strategy_type == 'always':
            comply_with_resource_constraints = parse_bool(
                    migration_strategy_config, 'comply_with_resource_constraints', True)
            return basicMigrationAlgorithms.AlwaysMigrateAlgorithm(comply_with_resource_constraints)

        elif migration_strategy_type == 'always_neighborhood':
            neighborhood_size = parse_non_negative_int(
                    migration_strategy_config, 'neighborhood_size')
            comply_with_resource_constraints = parse_bool(
                    migration_strategy_config, 'comply_with_resource_constraints', True)
            distance_metric = parse_str_options(migration_strategy_config,
                                                'distance_metric',
                                                ['euclidian', 'hops'])
            migration_direction = parse_str_options(migration_strategy_config, 'migration_direction', ['closest', 'furthest'])
            return basicMigrationAlgorithms.AlwaysMigrateToClosestInNeighborhoodAlgorithm(neighborhood_size,
                                                                                          comply_with_resource_constraints,
                                                                                          distance_measure=distance_metric,
                                                                                          furthest_cloud=migration_direction == 'furthest')

        elif migration_strategy_type == 'highest_utility_greedy' or migration_strategy_type == 'highest_utility_displacing':
            neighborhood_size = parse_non_negative_int(
                    migration_strategy_config, 'neighborhood_size')
            utility_fct_str = parse_str_options(migration_strategy_config, 'utility_function', ['priority_weighted_latency', 'squared_latency', 'priority_weighted_binary'],
                                                'priority_weighted_latency')
            utility_fct = {'priority_weighted_latency': evalMigrationAlgorithms.priority_weighted_latency_utility,
                           'squared_latency':           evalMigrationAlgorithms.squared_latency_utility,
                           'priority_weighted_binary':  evalMigrationAlgorithms.priority_weighted_binary_utility}

            return evalMigrationAlgorithms.AlwaysMigrateToHighestUtilityInNeighborhoodAlgorithm(num_neighbors=neighborhood_size,
                                                                                                service_displacement=migration_strategy_type == 'highest_utility_displacing',
                                                                                                utility_function=utility_fct[utility_fct_str])
        elif migration_strategy_type == 'isa_heuristic':

            feature_config = parse_object(migration_strategy_config, 'features')
            feature_user_last_base_station = parse_bool(
                    feature_config, 'user_last_base_station')
            feature_relative_positions = parse_bool(
                    feature_config, 'relative_positions')
            feature_absolute_positions = parse_bool(
                    feature_config, 'absolute_positions')
            feature_measured_latencies = parse_bool(
                    feature_config, 'measured_latencies')
            feature_latency_requirements = parse_bool(
                    feature_config, 'latency_requirements', default_value=False)

            features = ConfigurableFeatures(
                    use_user_last_base_station=feature_user_last_base_station,
                    use_relative_positions=feature_relative_positions,
                    use_absolute_positions=feature_absolute_positions,
                    use_measured_latencies=feature_measured_latencies,
                    use_latency_requirements=feature_latency_requirements)

            from tensorflow.compat.v1.keras import backend as K  # type: ignore
            import tensorflow.compat.v1 as tf  # type: ignore

            config = tf.ConfigProto(
                    log_device_placement=False,
                    allow_soft_placement=True,
                    device_count={
                        'CPU': 8},
                    intra_op_parallelism_threads=8,
                    inter_op_parallelism_threads=8)
            session = tf.Session(config=config)
            K.set_session(session)
            os.environ["OMP_NUM_THREADS"] = "8"
            os.environ["KMP_BLOCKTIME"] = "30"
            os.environ["KMP_SETTINGS"] = "1"
            os.environ["KMP_AFFINITY"] = "granularity=fine,verbose,compact,1,0"

            hparam = QHyperparameters()
            hparam.max_replay_memory_size = parse_non_negative_int(
                    migration_strategy_config,
                    'replay_memory_size',
                    default_value=1000000)  # 1000000 #1000
            batch_size = parse_non_negative_int(
                    migration_strategy_config,
                    'batch_size',
                    default_value=1000)
            hparam.batch_fraction_of_replay_memory = batch_size / hparam.max_replay_memory_size  # 0.0001  # 0.001 #1
            hparam.episode_length = parse_non_negative_int(
                    migration_strategy_config,
                    'episode_length',
                    default_value=1000)  # 1000#100#1000
            hparam.replay_buffer_sampling_rate = parse_non_negative_float(
                    migration_strategy_config, 'replay_buffer_sampling_rate', 1.0)
            hparam.num_epochs = 1  # 1  # 50
            # hparam.target_model_update_frequency = 5
            hparam.network_depth = parse_non_negative_int(
                    migration_strategy_config, 'network_depth')
            hparam.network_width = parse_non_negative_int(
                    migration_strategy_config, 'network_width')
            hparam.max_num_services = 3
            hparam.initial_exploration_boost = 1e4  # 1e4
            hparam.discount_factor = parse_non_negative_float(
                    migration_strategy_config,
                    'discount_factor',
                    default_value=0.99)  # 0#0.99#0.9999#0.99 #0.9
            hparam.target_model_update_frequency = 10  # 20  # 10
            hparam.recursion_depth = parse_non_negative_int(
                    migration_strategy_config, 'recursion_depth')
            hparam.epsilon = parse_non_negative_float(migration_strategy_config, 'epsilon')
            hparam.initial_exploration_boost = parse_non_negative_float(migration_strategy_config, 'exp_boost', 0)
            hparam.max_num_neighbor_clouds = parse_non_negative_int(
                    migration_strategy_config, 'neighborhood_size')
            enable_learning = parse_bool(
                    migration_strategy_config, 'enable_learning')
            if not enable_learning:
                # disable exploration
                hparam.initial_exploration_boost = 0
                hparam.epsilon = 0
                # disable learning
                hparam.do_training = False
                # disable sample collection
                hparam.max_replay_memory_size = 0
            verbose = parse_bool(
                    migration_strategy_config,
                    'verbose',
                    default_value=False)
            random_seed = parse_int(
                    migration_strategy_config,
                    'random_seed',
                    default_value=42)
            learning_rng = random.Random()
            learning_rng.seed(random_seed)
            dqn_migration_algorithm: DQNMigrationAlgorithm = DQNMigrationAlgorithm(
                    hparam, learning_rng, verbose=verbose)

            if 'weights' in migration_strategy_config:
                rel_weights_path = parse_str(migration_strategy_config, 'weights')
                weights_path = os.path.normpath(
                        os.path.join(
                                configuration_path,
                                rel_weights_path))
                dqn_migration_algorithm.shared_agent.set_model_parameters(
                        pickle.load(open(weights_path, "rb")))

            return dqn_migration_algorithm

    @staticmethod
    def configure_initial_placement_strategy(containing_object: Dict[str, Any]) -> InitialPlacementStrategy:
        """
        Parses and configures the initial placement_cost strategy from a containing_object JSON object.
        :param containing_object: The object that contains the 'migration_strategy' object.
        :return: a configured initial placement_cost strategy.
        """
        migration_strategy_config = parse_object(containing_object, 'migration_strategy')
        initial_placement_strategy = parse_str_options(migration_strategy_config,
                                                       'initial_placement_strategy',
                                                       ['central_cloud', 'closest_available'],
                                                       default_value='central_cloud')
        if initial_placement_strategy == 'central_cloud':
            return InitialPlacementAtCloud()
        elif initial_placement_strategy == 'closest_available':
            return InitialPlacementAtClosestCloudletWithAvailableResources()

    @staticmethod
    def configure_migration_trigger(containing_object: Dict[str, Any]) -> str:
        """
        Parses the migration trigger from a JSON containing_object object
        :param containing_object: The object that contains the 'migration_strategy' object.
        :return: The name of a migration trigger. One of 'always', 'bs_changed', 'latency_changed'.
        """
        migration_strategy_config = parse_object(containing_object, 'migration_strategy')
        return parse_str_options(migration_strategy_config,
                                 'migration_trigger',
                                 ['always', 'bs_changed', 'latency_changed'])

    @staticmethod
    def configure_service_placement_strategy(containing_object: Dict[str, Any],
                                             configuration_path: str,
                                             network: CloudNetwork,
                                             service_cost_function: ServiceCostFunction) -> ServicePlacementStrategy:
        """
        Parses and configures a MigrationAlgorithmServicePlacementStrategy.
        :param containing_object: The object that contains the 'migration_strategy' object.
        :param configuration_path: The path of the containing_object file.
        :param network: The CloudNetwork that the simulation is using.
        :param service_cost_function: The cost function of the services.
        :return: A configured service cost function
        """

        # configure the migration algorithm
        migration_algorithm = Version_0_1.configure_migration_algorithm(containing_object, configuration_path)

        # parse the migration trigger
        migration_trigger: str = Version_0_1.configure_migration_trigger(containing_object)

        # configure the initial placement_cost strategy
        initial_placement_strategy = Version_0_1.configure_initial_placement_strategy(containing_object)

        return MigrationAlgorithmServicePlacementStrategy(
                migration_algorithm=migration_algorithm,
                cloud_network=network,
                cost_function=service_cost_function,
                migration_trigger=migration_trigger,
                initial_placement_strategy=initial_placement_strategy)
