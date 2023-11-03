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


from typing import List, Optional, Any, Iterable
from INPsim.Simulation.ConfigFileParser.simulationConfiguration import configure_simulation_from_configuration_file
from INPsim.Simulation.simulator import Simulation
from INPsim.Simulation import SimulationObserver, SimulationObserverList, SimulationInterface, StatisticsSimulationObserver
from INPsim.Network.Nodes import LimitedMemoryCloud
from INPsim.ServicePlacement import ServicePlacementStrategy, MyopicOptimalServicePlacementStrategy
from INPsim.ServicePlacement.Migration.Algorithms import MigrationAlgorithm, MigrationAlgorithmServicePlacementStrategy
from INPsim.ServicePlacement.Migration.Action import Action
from INPsim.ServicePlacement.Migration.Learning import DQNMigrationAlgorithm
import datetime
import time
import os
import argparse
import pickle

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# Construct the argument parser
ap = argparse.ArgumentParser()

# Add the arguments to the parser
ap.add_argument(
        "-x",
        "--headless",
        required=False,
        help="Disable all graphical output.",
        action='store_true')
ap.add_argument(
        "-c",
        "--configuration",
        required=False,
        help="Configuration file. If none is specified, interactive mode will be launched.",
        type=str)
ap.add_argument(
        "-o",
        "--output",
        required=False,
        help="Output directory.",
        type=str)
# ap.add_argument(
#         "-s",
#         "--snapshotting",
#         required=False,
#         help="Enable Snapshotting.",
#         type=str)
args = vars(ap.parse_args())

if args['headless']:
    enable_visualization = False
    enable_plots = False
else:
    enable_visualization = True
    enable_plots = True

# if args['snapshotting']:
#     enable_snapshotting = True
# else:
enable_snapshotting = False

if args['configuration']:
    configuration_file_name = args['configuration']
else:
    # interactive console to choose the configuration:
    from os import listdir
    from os.path import isfile, join

    default_experiment_configuration_path = 'defaultExperimentConfigurations'
    default_experiment_configuration_files = [
        f for f in listdir(default_experiment_configuration_path) if isfile(
                join(
                        default_experiment_configuration_path, f))]
    print("Choose one of the following default experiments:")
    for i, file_name in enumerate(default_experiment_configuration_files):
        print(str(i) + ") " + file_name)
    selected_option = int(input())
    configuration_file_name = 'defaultExperimentConfigurations/' + \
                              default_experiment_configuration_files[selected_option]

if args['output']:
    output_dir = args['output']
else:
    date_time = datetime.datetime.now()
    output_dir = 'output/sim_output_' + \
                 date_time.strftime("%d-%b-%Y_%H-%M-%S-%f")

try:
    os.makedirs(output_dir)
except FileExistsError:
    print("Directory", output_dir, "already exists!")

start_time = datetime.datetime.now()

# write configuration to the output directory for reference
with open(configuration_file_name, 'r') as in_file:
    with open(output_dir + '/configuration.json', 'w') as out_file:
        for line in in_file:
            out_file.write(line)
del line    # not used in this context afterwards.

# configure configured_simulation
configured_simulation: Simulation
num_simulation_steps: int

configured_simulation, simulation_statistics, num_simulation_steps = configure_simulation_from_configuration_file(
        configuration_file_name)

observers: List[SimulationObserver] = [simulation_statistics]

if enable_visualization:
    from INPsim.Visualization.simplot import SimPlotPygame
    from INPsim.vmath import AABB2

    sim_plt_pygame = SimPlotPygame(
            configured_simulation,
            '../../Datasets/SF_area_desaturated.png',
            AABB2(
                    542688.443644256,
                    556765.7262020159,
                    4161556.7164416737,
                    4185052.3668366373),
            output_dir)


    class PygameVisualizationSimulationObserver(SimulationObserver):
        def after_simulation_step(self, simulator: SimulationInterface, actions: Iterable[Action]) -> None:
            if simulator.get_current_step() % 5 == 0:
                sim_plt_pygame.plot(simulator, simulation_statistics)


    observers.append(PygameVisualizationSimulationObserver())

sp_strategy: ServicePlacementStrategy = configured_simulation.get_service_placement_strategy()
migration_algorithm: Optional[MigrationAlgorithm] = None
if isinstance(sp_strategy, MigrationAlgorithmServicePlacementStrategy):
    migration_algorithm = sp_strategy.get_migration_algorithm()

if enable_plots:
    from INPsim.Visualization.simplot import SimPlotLearning, SimPlotStats

    sim_plt: SimPlotStats
    if isinstance(migration_algorithm, DQNMigrationAlgorithm):# hasattr(migration_algorithm, 'shared_agent'):
        sim_plt = SimPlotLearning(output_dir)
    else:
        sim_plt = SimPlotStats(output_dir)


    class StatisticsPlottingSimulationObserver(SimulationObserver):
        def after_simulation_step(self, simulation: SimulationInterface, actions: Iterable[Action]) -> None:
            if simulation.get_current_step() % 5 == 0:
                sim_plt.plot(simulation, simulation_statistics)


    observers.append(StatisticsPlottingSimulationObserver())


class GeneralOutputObserver(SimulationObserver):
    def after_simulation_step(self, simulation: SimulationInterface, actions: Iterable[Action]) -> None:
        if simulation.get_current_step() % 5 == 0:
            # sanity check for available memory vs required memory
            total_required_memory: float = 0.0
            for service in simulation.get_services():
                total_required_memory += service.get_memory_requirement()
            total_available_memory = 0.0
            for cloud in simulation.get_clouds():
                if isinstance(cloud, LimitedMemoryCloud):
                    total_available_memory += cloud.memory_capacity()
                else:
                    raise Exception("GeneralOutputObserver expected Clouds of type LimitedMemoryCloud!")
            print('required m.:', total_required_memory, 'availale m.:', total_available_memory,
                  '(', 100 * (float(total_required_memory) / float(total_available_memory)), '%)')
            print("configured_simulation " + str(0.1 * int(1000 *
                                                           (simulation.get_current_step() / num_simulation_steps))) + "%")


# observers.append(GeneralOutputObserver())

if hasattr(migration_algorithm, 'shared_agent'):
    if hasattr(migration_algorithm.shared_agent, 'get_model_parameters'):

        class LoggingNNWeightsSimulationObserver(SimulationObserver):
            def after_simulation_step(self, simulation: SimulationInterface, actions: Iterable[Action]) -> None:
                if simulation.get_current_step() % 100 == 0:
                    filename = output_dir + '/weights_at_step_' + \
                               str(simulation.get_current_step()) + '.pickle'
                    with open(filename, "wb") as nn_weights_file:
                        pickle.dump(
                                migration_algorithm.shared_agent.get_model_parameters(), nn_weights_file)
                    print("dumped NN_weights to " + filename)


        observers.append(LoggingNNWeightsSimulationObserver())

if enable_snapshotting:
    import sys

    sys.setrecursionlimit(100000)


    class SnapshotObserver(SimulationObserver):
        def after_simulation_step(self, simulation: SimulationInterface, actions: Iterable[Action]) -> None:
            if simulation.get_current_step() % 10 == 0:
                filename = output_dir + '/snapshot_at_step_' + \
                           str(simulation.get_current_step()) + '.pickle'
                with open(filename, "wb") as snapshot_file:
                    pickle.dump(simulation, snapshot_file)

                with open(filename, "rb") as snapshot_file:
                    simulation.__dict__.update(pickle.load(snapshot_file).__dict__)
                print("snapshot saved")


    observers.append(SnapshotObserver())

log_file_name = output_dir + '/statistics.csv'
with open(log_file_name, 'w') as file:
    file.write(
            'global_cost, '
            'avg_latency, '
            'sim_time, '
            'num_migrations, '
            'num_services, '
            'num_services_at_cloud, '
            'mean_computation_time, '
            'mean_communication_time, '
            'mean_communication_time_service_at_cloud, '
            'mean_communication_time_service_at_edge,'
            'mean_training_time,\n')


class StatsLoggingSimulationObserver(SimulationObserver):
    def after_simulation_step(self, simulation: SimulationInterface, actions: Iterable[Action]) -> None:
        with open(log_file_name, 'a') as log_file:
            line_str = str(simulation_statistics.global_cost[-1]) + ','
            line_str += str(simulation_statistics.avg_latency[-1]) + ','
            line_str += str(datetime.datetime.now() - start_time).split('.')[0].replace(',', '') + ','
            line_str += str(simulation_statistics.num_migrations[-1]) + ','
            line_str += str(simulation_statistics.num_services[-1]) + ','
            line_str += str(simulation_statistics.num_services_at_cloud[-1]) + ','
            mean_computation_time = -1
            mean_communication_time = -1
            mean_communication_time_service_at_cloud = -1
            mean_communication_time_service_at_edge = -1
            sp_strategy: ServicePlacementStrategy = simulation.get_service_placement_strategy()
            migration_alg_shared_agent: Optional[Any]    # this is still too hacky... -> refactor when time available
            if isinstance(sp_strategy, MigrationAlgorithmServicePlacementStrategy) and hasattr(sp_strategy.get_migration_algorithm(), 'shared_agent'):
                migration_alg_shared_agent = sp_strategy.get_migration_algorithm().shared_agent
            else:
                migration_alg_shared_agent = None
            if migration_alg_shared_agent and hasattr(migration_alg_shared_agent, 'mean_computation_time'):
                mean_computation_time = migration_alg_shared_agent.mean_computation_time
            elif isinstance(sp_strategy, MyopicOptimalServicePlacementStrategy):
                mean_computation_time = sp_strategy.get_mean_computation_time()
                if mean_computation_time is None:
                    mean_computation_time = -1
            line_str += str(mean_computation_time) + ','
            if migration_alg_shared_agent and hasattr(migration_alg_shared_agent, 'mean_communication_time'):
                mean_communication_time = migration_alg_shared_agent.mean_communication_time
            elif isinstance(sp_strategy, MyopicOptimalServicePlacementStrategy):
                mean_communication_time = sp_strategy.get_mean_communication_time()
                if mean_communication_time is None:
                    mean_communication_time = -1
            line_str += str(mean_communication_time) + ','
            if migration_alg_shared_agent and hasattr(migration_alg_shared_agent, 'mean_communication_time_service_at_cloud'):
                mean_communication_time_service_at_cloud = migration_alg_shared_agent.mean_communication_time_service_at_cloud
            line_str += str(mean_communication_time_service_at_cloud) + ','
            if migration_alg_shared_agent and hasattr(migration_alg_shared_agent, 'mean_communication_time_service_at_edge'):
                mean_communication_time_service_at_edge = migration_alg_shared_agent.mean_communication_time_service_at_edge
            line_str += str(mean_communication_time_service_at_edge) + ','
            if migration_alg_shared_agent and hasattr(migration_alg_shared_agent, 'total_training_time') and hasattr(migration_alg_shared_agent, 'num_training_episodes'):
                mean_communication_time_service_at_edge = migration_alg_shared_agent.total_training_time/migration_alg_shared_agent.num_training_episodes
            line_str += str(mean_communication_time_service_at_edge) + ','
            log_file.write(line_str + '\n')


observers.append(StatsLoggingSimulationObserver())

if hasattr(migration_algorithm, 'shared_agent'):
    if hasattr(migration_algorithm.shared_agent, 'avg_rewards'):
        agent_log_file_name = output_dir + '/agent_statistics.csv'


        class AgentStatsLoggingSimulationObserver(SimulationObserver):
            def after_simulation_step(self, simulation: SimulationInterface, actions: Iterable[Action]) -> None:
                with open(agent_log_file_name, 'w') as agent_log_file:
                    agent_log_file.write('avg_rewards, losses, Qs\n')
                    avg_rewards = migration_algorithm.shared_agent.avg_rewards
                    if hasattr(migration_algorithm.shared_agent, 'losses'):
                        losses = migration_algorithm.shared_agent.losses
                    else:
                        losses = [-1 for _ in avg_rewards]
                    if hasattr(migration_algorithm.shared_agent, 'predicted_Qs'):
                        qs = migration_algorithm.shared_agent.predicted_Qs
                    else:
                        qs = [0 for _ in avg_rewards]
                    for r, l, q in zip(avg_rewards, losses, qs):
                        agent_log_file.write(str(r) + ',' + str(l) + ',' + str(q) + '\n')


        observers.append(AgentStatsLoggingSimulationObserver())


class ProgressPrintingSimulationObserver(SimulationObserver):
    def after_simulation_step(self, simulation: SimulationInterface, actions: Iterable[Action]) -> None:
        step = simulation.get_current_step()
        buffer_size_str = ""
        sp_strategy: ServicePlacementStrategy = simulation.get_service_placement_strategy()
        migration_algo: MigrationAlgorithm
        if isinstance(sp_strategy, MigrationAlgorithmServicePlacementStrategy):
            migration_algo = sp_strategy.get_migration_algorithm()
            if hasattr(
                    migration_algo.shared_agent,
                    'replay_memory') and migration_algo.hyperparameters.max_replay_memory_size > 0:
                buffer_size_str = "   buffer: " + str(len(migration_algo.shared_agent.replay_memory)) + \
                                 "/" + str(migration_algo.hyperparameters.max_replay_memory_size) + ' (' + str(
                        100 * (len(migration_algo.shared_agent.replay_memory) / float(
                            migration_algo.hyperparameters.max_replay_memory_size))) + '%)'
        print('step ', step, '/', num_simulation_steps, '(', 100 *
              (step / float(num_simulation_steps)), '%)' + buffer_size_str)

    # print("ma:", configured_simulation.get_service_placement_strategy().num_migration_actions, "nma:", configured_simulation.get_service_placement_strategy().num_no_migration_actions)


observers.append(ProgressPrintingSimulationObserver())


class HistogramOutputSimulationObserver(SimulationObserver):
    def after_simulation_step(self, simulation: SimulationInterface, actions: Iterable[Action]) -> None:
        if simulation.get_current_step() % 1 == 0:
            output_histograms = []

            sp_strategy: ServicePlacementStrategy = simulation.get_service_placement_strategy()
            migration_algo: MigrationAlgorithm
            if isinstance(sp_strategy, MigrationAlgorithmServicePlacementStrategy):
                migration_algo_sp_strategy: MigrationAlgorithmServicePlacementStrategy = sp_strategy
                migration_algo = migration_algo_sp_strategy.get_migration_algorithm()

                if migration_algo and hasattr(migration_algo.shared_agent, 'computation_time_histogram'):
                    computation_time_histogram = migration_algo.shared_agent.computation_time_histogram
                    output_histograms.append(("computation_time_histogram", computation_time_histogram))
                if migration_algo and hasattr(migration_algo.shared_agent, 'communication_time_histogram'):
                    communication_time_histogram = migration_algo.shared_agent.communication_time_histogram
                    output_histograms.append(("communication_time_histogram", communication_time_histogram))
                if migration_algo and hasattr(migration_algo.shared_agent, 'decision_time_histogram'):
                    decision_time_histogram = migration_algo.shared_agent.decision_time_histogram
                    output_histograms.append(("decision_time_histogram", decision_time_histogram))

                if migration_algo and hasattr(migration_algo.shared_agent, 'computation_time_histogram_service_at_cloud'):
                    computation_time_histogram_service_at_cloud = migration_algo.shared_agent.computation_time_histogram
                    output_histograms.append(("computation_time_histogram_service_at_cloud", computation_time_histogram_service_at_cloud))
                if migration_algo and hasattr(migration_algo.shared_agent, 'communication_time_histogram_service_at_cloud'):
                    communication_time_histogram_service_at_cloud = migration_algo.shared_agent.communication_time_histogram_service_at_cloud
                    output_histograms.append(("communication_time_histogram_service_at_cloud", communication_time_histogram_service_at_cloud))
                if migration_algo and hasattr(migration_algo.shared_agent, 'decision_time_histogram_service_at_cloud'):
                    decision_time_histogram_service_at_cloud = migration_algo.shared_agent.decision_time_histogram_service_at_cloud
                    output_histograms.append(("decision_time_histogram_service_at_cloud", decision_time_histogram_service_at_cloud))

                if migration_algo and hasattr(migration_algo.shared_agent, 'computation_time_histogram_service_at_edge'):
                    computation_time_histogram_service_at_edge = migration_algo.shared_agent.computation_time_histogram
                    output_histograms.append(("computation_time_histogram_service_at_edge", computation_time_histogram_service_at_edge))
                if migration_algo and hasattr(migration_algo.shared_agent, 'communication_time_histogram_service_at_edge'):
                    communication_time_histogram_service_at_edge = migration_algo.shared_agent.communication_time_histogram_service_at_edge
                    output_histograms.append(("communication_time_histogram_service_at_edge", communication_time_histogram_service_at_edge))
                if migration_algo and hasattr(migration_algo.shared_agent, 'decision_time_histogram_service_at_edge'):
                    decision_time_histogram_service_at_edge = migration_algo.shared_agent.decision_time_histogram_service_at_edge
                    output_histograms.append(("decision_time_histogram_service_at_edge", decision_time_histogram_service_at_edge))

                if len(output_histograms) > 0:
                    histogram_output_file = output_dir + '/histograms.json'
                    with open(histogram_output_file, 'w') as histogram_output_file:
                        histogram_output_file.write('{\n')
                        for hist_name, hist in output_histograms:
                            histogram_output_file.write('"' + hist_name + '": {\n')
                            histogram_output_file.write('    "num_buckets": ' + str(hist.num_buckets()) + ',\n')
                            histogram_output_file.write('    "lower_bound": ' + str(hist.lower_bound()) + ',\n')
                            histogram_output_file.write('    "upper_bound": ' + str(hist.upper_bound()) + ',\n')
                            histogram_output_file.write('    "buckets_absolute": [' + hist.to_string(cumulative=False, relative=False) + '],\n')
                            histogram_output_file.write('    "cdf":[' + hist.to_string(cumulative=True, relative=True) + ']\n}')
                            if hist != output_histograms[-1][1]:
                                histogram_output_file.write(',')
                            histogram_output_file.write('\n')
                        histogram_output_file.write('}\n')


observers.append(HistogramOutputSimulationObserver())

st = time.time()
configured_simulation.simulate(num_simulation_steps, SimulationObserverList(*observers))
print("----Simulation took %.2f seconds----"%(time.time()-st))