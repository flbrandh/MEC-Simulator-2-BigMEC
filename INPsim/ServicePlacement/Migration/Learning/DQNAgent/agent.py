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


from typing import Tuple, List, Dict, Any
from INPsim.Network.Nodes.cloud import LimitedMemoryCloud
from INPsim.Network.Service.service import Service
from INPsim.Network.network import CloudNetwork
from INPsim.ServicePlacement.Migration.Learning.model import QModel
from INPsim.ServicePlacement.Migration.Action.migrationActionInterface import MigrationAction
from INPsim.ServicePlacement.Migration.Action.noMigrationActionInterface import NoMigrationAction
import math
import numpy as np
import time
from INPsim.Utils.histogram import EquidistantHistogram, OutOfHistogramBoundsError


class DQNAgent:
    class QSample:
        """
        Represents one sample of the q-function : (s,a,r,s',[a'])
        """

        def __init__(self,
                     state_features,
                     action_features,
                     reward,
                     next_state_features,
                     possible_next_action_features):
            self.state_features = state_features
            self.action_features = action_features
            self.reward = reward
            self.next_state_features = next_state_features
            self.possible_next_action_features = possible_next_action_features

    def __init__(self, hyperparameters, features, rng, verbose):
        self.hyperparameters = hyperparameters
        self.rng = rng
        self.verbose = verbose

        self.features = features

        self.episode = 0
        self.iteration = 0

        self.last_service = None
        self.last_state_features = {}  # None
        self.last_action_features = {}  # None
        self.sample_last_experience = {}  # None
        self.last_reward = {}  # None
        self.replay_memory = []
        # statistics:
        self.total_episode_reward = 0
        self.avg_rewards = []
        self.max_episode_reward = -math.inf
        self.max_rewards = []
        self.min_episode_reward = math.inf
        self.min_rewards = []
        self.num_multiple_migration_actions = 0
        self.losses = []
        self.predicted_Qs = []

        self.num_received_rewards = 0
        self.mean_reward = 0
        self.reward_standard_deviation = 0

        self.num_decisions = 0
        self.num_decisions_service_at_cloud = 0
        self.num_decisions_service_at_edge = 0
        self.mean_computation_time = 0
        self.mean_communication_time = 0
        self.mean_communication_time_service_at_cloud = 0
        self.mean_communication_time_service_at_edge = 0
        self.num_training_episodes = 0
        self.total_training_time = 0
        histogram_length_ms = 1000
        self.communication_time_histogram = EquidistantHistogram(histogram_length_ms, 0, histogram_length_ms * 0.001)
        self.computation_time_histogram = EquidistantHistogram(histogram_length_ms, 0, histogram_length_ms * 0.001)
        self.decision_time_histogram = EquidistantHistogram(histogram_length_ms, 0, histogram_length_ms * 0.001)
        self.communication_time_histogram_service_at_cloud = EquidistantHistogram(histogram_length_ms, 0, histogram_length_ms * 0.001)
        self.computation_time_histogram_service_at_cloud = EquidistantHistogram(histogram_length_ms, 0, histogram_length_ms * 0.001)
        self.decision_time_histogram_service_at_cloud = EquidistantHistogram(histogram_length_ms, 0, histogram_length_ms * 0.001)
        self.communication_time_histogram_service_at_edge = EquidistantHistogram(histogram_length_ms, 0, histogram_length_ms * 0.001)
        self.computation_time_histogram_service_at_edge = EquidistantHistogram(histogram_length_ms, 0, histogram_length_ms * 0.001)
        self.decision_time_histogram_service_at_edge = EquidistantHistogram(histogram_length_ms, 0, histogram_length_ms * 0.001)

        self._init_models()

    def _init_models(self) -> None:
        self.Q_model = QModel(self.hyperparameters, self.features).Q_model
        self.Q_target_model = QModel(
                self.hyperparameters, self.features).Q_model

    def __getstate__(self):
        """
        For pickling.
        :return:
        """
        state = self.__dict__.copy()
        state['Q_model'] = state['Q_model'].get_weights()
        state['Q_target_model'] = state['Q_target_model'].get_weights()
        return state

    def __setstate__(self, newstate):
        """
        For unpickling.
        :param newstate:
        :return:
        """
        Q_model_weights = newstate['Q_model']
        Q_target_model_weights = newstate['Q_target_model']
        self.__dict__.update(newstate)
        newstate['Q_model'] = QModel(
                self.hyperparameters, self.features).Q_model
        newstate['Q_model'].set_weights(Q_model_weights)
        newstate['Q_target_model'] = QModel(
                self.hyperparameters, self.features).Q_model
        newstate['Q_target_model'].set_weights(Q_target_model_weights)
        self.__dict__.update(newstate)

    def get_model_parameters(self):
        return {"Q_model":        self.Q_model.get_weights(),
                "Q_target_model": self.Q_target_model.get_weights()}

    def set_model_parameters(self, models):
        self.Q_model.set_weights(models["Q_model"])
        self.Q_target_model.set_weights(models["Q_model"])

    def get_prediction_model(self):
        return self.Q_model

    def _construct_training_inputs(self, minibatch_indices):
        minibatch_size = len(minibatch_indices)
        x = np.zeros((minibatch_size,
                      len(self.features.state_features()) + len(
                              self.features.action_features())))
        for i, batch_sample in enumerate(minibatch_indices):
            qsample = self.replay_memory[batch_sample]
            x[i, :] = np.array(
                    qsample.state_features + qsample.action_features)
        return x

    def _construct_training_outputs(self, minibatch_indices):
        minibatch_size = len(minibatch_indices)
        y = np.zeros(minibatch_size)
        for i, batch_sample in enumerate(minibatch_indices):
            qsample = self.replay_memory[batch_sample]
            state_features = qsample.state_features
            nn_inputs = []
            for action_features in qsample.possible_next_action_features:
                nn_inputs.append(state_features + action_features)
            # max_state_action_value = max(self.Q_target_model.predict(np.array(nn_inputs)))  # finding the value of the next action
            max_state_action_value2 = max(self.Q_target_model(np.array(nn_inputs), training=False).numpy())
            # assert max_state_action_value == max_state_action_value2
            y[i] = qsample.reward + self.hyperparameters.discount_factor * \
                   max_state_action_value  # bellman equation
        return y

    def _train_minibatch(self, minibatch_indices):
        # construct x
        x = self._construct_training_inputs(minibatch_indices)
        y = self._construct_training_outputs(minibatch_indices)

        # train
        history = self.Q_model.fit(
                x,
                y,
                epochs=self.hyperparameters.num_epochs,
                batch_size=32,
                verbose=0)

        if 0 == self.episode % self.hyperparameters.target_model_update_frequency:
            self.Q_target_model.set_weights(self.Q_model.get_weights())
            if self.verbose:
                print('**** Updated the target model in iteration ' +
                      str(self.iteration) + '. ****')

        return history

    def train(self):
        # TODO factor the learning out into a separate learner, such that the
        # training data can be transmitted in a simple function call.
        """
        Performs one run of training the Q-function
        :return:
        """
        minibatch_size = min(len(self.replay_memory), int(
                self.hyperparameters.max_replay_memory_size * self.hyperparameters.batch_fraction_of_replay_memory))
        assert isinstance(minibatch_size, int)
        if self.verbose:
            print('minibatch_size: ', minibatch_size,
                  ' replay memory size:', len(self.replay_memory))
        if minibatch_size > 10:  # it's not worth it below that
            minibatch_indices = self.rng.sample(
                    range(len(self.replay_memory)), minibatch_size)

            history = self._train_minibatch(minibatch_indices)

            self.losses.append(history.history['loss'][0])

            if self.verbose:
                print(
                        'iteration=',
                        self.iteration,
                        ', epsilon=',
                        self.hyperparameters.epsilon,
                        ', discount factor=',
                        self.hyperparameters.discount_factor)

            self.episode += 1

    def create_feature_vectors(
            self,
            service,
            cloud,
            possible_migration_targets,
            cloud_network):
        state_feature_vector = self.features.state_features(cloud)
        migration_action_feature_vectors = []
        for possible_migration_target in possible_migration_targets:
            migration_action_feature_vectors.append(
                    self.features.action_features(
                            possible_migration_target, service, cloud_network))
        return state_feature_vector, migration_action_feature_vectors

    def gather_possible_migration_plans(self,
                                        service: Service,
                                        cloud: LimitedMemoryCloud,
                                        max_recursion_depth: int) -> List[List[Tuple[Service, LimitedMemoryCloud]]]:
        # get immediate neighborhood
        possible_migration_targets = cloud.get_migration_algorithm_instance(
                ).get_neighboring_clouds(service).copy()
        # add the current cloud to the neighborhood if it's not included already (to facilitate non-migration)
        if not cloud in possible_migration_targets:
            possible_migration_targets = possible_migration_targets + [cloud]
        assert len(possible_migration_targets) <= self.hyperparameters.max_num_neighbor_clouds + 1

        possible_migration_plans = []
        for target in possible_migration_targets:
            if target != cloud:  # cannot displace from the current cloud
                if max_recursion_depth > 0 or target.total_memory_requirement() + service.get_memory_requirement() <= target.memory_capacity():  # resource check in case there is no further recursion
                    possible_migration_plans.append((service, target, self.gather_possible_migration_plans_by_freeing_space_rec(service, target, max_recursion_depth)))
        possible_migration_plans.append((service, cloud, []))  # one plan is always to just stay

        # flatten the migration plan tree
        possible_migration_plans_flat = []

        def flatten_possible_migration_plans(possible_subplans, flat_plan_so_far=[]):
            for service, target, following_subplans in possible_subplans:
                if following_subplans == []:
                    possible_migration_plans_flat.append(flat_plan_so_far + [(service, target)])
                else:
                    flatten_possible_migration_plans(following_subplans, flat_plan_so_far + [(service, target)])

        flatten_possible_migration_plans(possible_migration_plans)

        return possible_migration_plans_flat

    def gather_possible_migration_plans_by_freeing_space_rec(self,
                                                             incoming_service,
                                                             cloud,
                                                             max_recursion_depth,
                                                             recursion_depth=0):
        # don't add any cloudlets if the maximum depth is reached.
        if recursion_depth == max_recursion_depth:
            return []
        assert recursion_depth <= max_recursion_depth

        # if there is enough space, no further migrations necessary. #TODO what if we still considered that case and leave not propagating as an option?
        if cloud.total_memory_requirement() + incoming_service.get_memory_requirement() <= cloud.memory_capacity():
            return []  # no displacement necessary

        possible_migration_plans = []
        for service in cloud.services():
            current_service_cloud = service.get_cloud()
            possible_migration_targets = cloud.get_migration_algorithm_instance().get_neighboring_clouds(service).copy()
            for target in possible_migration_targets:
                if (target is not current_service_cloud and  # not possible to displace from the current cloud
                        (recursion_depth + 1 < max_recursion_depth or
                         target.total_memory_requirement() + service.get_memory_requirement() <= target.memory_capacity())):  # TODO put the resource-checks here
                    possible_migration_plans.append((service,
                                                     target,
                                                     self.gather_possible_migration_plans_by_freeing_space_rec(service,
                                                                                                               target,
                                                                                                               max_recursion_depth,
                                                                                                               recursion_depth + 1)))
                else:
                    pass  # If not a viable migration target, don't add it to the possible plans
        return possible_migration_plans

    def gather_migration_queries(self, possible_migration_plans):
        migration_queries = set()
        for plan in possible_migration_plans:
            for (service, target) in plan:
                service_current_cloud = service.get_cloud()
                migration_queries.add((service, service_current_cloud))
                migration_queries.add((service, target))
        return list(migration_queries)

    def generate_migration_query_features(self, migration_queries: List[Tuple[Service, LimitedMemoryCloud]],
                                          cloud_network: CloudNetwork) -> Tuple[List[List[float]], List[List[float]]]:
        """
        Generates the features for migration queries.
        :param migration_queries: the migration queries (a list of service -> cloud pairs)
        :param cloud_network: the network within the services operate
        :return: a list of feature vectors for the state-features and a list of action-feature vectors for each migration query
        """
        state_feature_vectors: List[List[float]] = []
        action_feature_vectors: List[List[float]] = []
        for (service, target) in migration_queries:
            service_cloud = service.get_cloud()
            state_feature_vectors.append(self.features.state_features(service_cloud))
            action_feature_vectors.append(self.features.action_features(target, service, cloud_network))
        return state_feature_vectors, action_feature_vectors

    def process_migration_queries(self,
                                  migration_queries: List[Tuple[Service, LimitedMemoryCloud]],
                                  state_feature_vectors: List[List[float]],
                                  action_feature_vectors: List[List[float]]) -> Dict[Tuple[Service, LimitedMemoryCloud], Any]:
        """
        Processes migration queries, predicting the Q-values from the input features using the NN.
        :param migration_queries: list of migration queries (pairs of service -> dst-cloud)
        :param state_feature_vectors: list of corresponding state feature vectors
        :param action_feature_vectors: list of corresponding action feature vectors
        :return: a dictionary that assigns the Q-value to each migration query
        """
        nn_inputs = [sfv + afv for sfv, afv in zip(state_feature_vectors, action_feature_vectors)]
        outputs = self.get_prediction_model()(np.array(nn_inputs), training=False).numpy()
        #outputs = [self.get_prediction_model()(np.array([nn_input]), training=False).numpy() for nn_input in nn_inputs]
        return dict([(k, o.item()) for k, o in zip(migration_queries, outputs)])

    # def process_migration_queries_no_nn(self,
    #                               migration_queries: List[Tuple[Service, LimitedMemoryCloud]],
    #                               state_feature_vectors: List[List[float]],
    #                               action_feature_vectors: List[List[float]]) -> Dict[Tuple[Service, LimitedMemoryCloud], Any]:
    #
    #     for service, cloud in migration_queries:
    #         cost =


    def compute_global_advantages(self, possible_migration_plans, migration_query_Qs):
        global_advantages = []

        service = possible_migration_plans[0][0][0]
        stay_baseline = migration_query_Qs[(service, service.get_cloud())]

        for migration_plan in possible_migration_plans:
            global_advantage = 0

            for (service, target) in migration_plan:
                service_cloud = service.get_cloud()
                if len(migration_plan) > 1:
                    a = migration_query_Qs[(service, target)]
                    b = migration_query_Qs[(service, service_cloud)]
                global_advantage += migration_query_Qs[(service, target)] - migration_query_Qs[(service, service_cloud)]
            global_advantages.append(global_advantage + stay_baseline)
        return global_advantages

    def epsilon_greedy_policy(self,
                              possible_migration_plans,
                              global_advantages,
                              epsilon,
                              exp_boost,
                              iteration):

        if exp_boost != 0:
            epsilon += (1 - epsilon) * math.exp(-iteration / exp_boost)

        if self.rng.random() < epsilon:
            # choose random action:
            best_plan_per_action = {}  # action : (global_advantage, plan)
            for plan, global_advantage in zip(possible_migration_plans, global_advantages):
                first_action = plan[0]
                if first_action not in best_plan_per_action or best_plan_per_action[first_action][0] < global_advantage:
                    best_plan_per_action[first_action] = (global_advantage, plan)
            _, chosen_plan = self.rng.choice(list(best_plan_per_action.values()))
        else:
            ga_array = np.array(global_advantages)
            indices_of_maxima = (ga_array == ga_array.max()).nonzero()[0]
            # tie breaker 1: choose the plan that involves doing nothing if it's a maximum
            for i in indices_of_maxima:
                migration_plan = possible_migration_plans[i]
                if len(migration_plan):
                    service, target_cloud = migration_plan[0]
                    if service.get_cloud() is target_cloud:
                        return migration_plan
            # tie breaker 2: choose a random shortest plan
            min_length_of_maxima = math.inf
            for i in indices_of_maxima:
                if len(possible_migration_plans[i]) < min_length_of_maxima:
                    min_length_of_maxima = len(possible_migration_plans[i])
            indices_of_min_length_maxima = []
            for i in indices_of_maxima:
                if len(possible_migration_plans[i]) == min_length_of_maxima:
                    indices_of_min_length_maxima.append(i)
            chosen_plan_index = self.rng.choice(indices_of_min_length_maxima)
            chosen_plan = possible_migration_plans[chosen_plan_index]
            #chosen_plan = possible_migration_plans[np.argmax(global_advantages)]
        return chosen_plan

    def compute_communication_time(self, cloud_network, service, displacing):
        """
        Estimates the communication time of the decision
        model for the communication time:
        Assumption: Distance describes the round-trip-time for one simple request
          Greedy:
              1 message to neighbors, requesting info
              -> compute result
              1 message to communicate result
          Displacing:
              1 message to prim. neighbors, requesting info
              1 message to second. neighbors, requesting info
              -> compute secondary results
              -> compute primary results
              1 message to communicate result to prim. neighbors
              1 message to communicate result to second. neighbors
        :param cloud_network: the network
        :param service: the service to be migrated
        :param displacing: True, if displacing is activated, False if not
        :return:
        """
        primary_neighoborhood = service.get_cloud().get_migration_algorithm_instance().get_neighboring_clouds(service)
        max_total_comm_dist = 0
        for primary_neighbor in primary_neighoborhood:
            if not primary_neighbor == cloud_network.central_cloud():
                primary_neighbor_dist = cloud_network.dist_to_node(service.get_cloud().node(), primary_neighbor.node())
                total_comm_dist = primary_neighbor_dist
                # if displacement is enabled, add to the primary neighborhood distance the maximum secondary neighborhood distance.
                if displacing:
                    secondary_neighborhood = primary_neighbor.get_migration_algorithm_instance().get_neighboring_clouds(service)
                    max_secondary_neighbor_dist = 0
                    for secondary_neighbor in secondary_neighborhood:
                        if not secondary_neighbor == service.get_cloud() and not secondary_neighbor == cloud_network.central_cloud():
                            secondary_neighbor_dist = cloud_network.dist_to_node(primary_neighbor.node(), secondary_neighbor.node())
                            max_secondary_neighbor_dist = max(max_secondary_neighbor_dist, secondary_neighbor_dist)
                    total_comm_dist += max_secondary_neighbor_dist
                max_total_comm_dist = max(max_total_comm_dist, total_comm_dist)

        return 2 * max_total_comm_dist * 0.001  # also converting ms to s

    def process_migration_event(self, service, cloud, cloud_network):
        """
        :param service: the service at the cloud that this function was invoked for
        :param cloud: the cloud that this function was invoked for
        :param cloud_neighborhood: the neighborhood of the cloud
        :return: a list of migration actions, with the first one being the action of the service in question. If no action was taken, there is one NoMigrationAction in the list.
        """
        # initialize cache if necessary
        if service not in self.last_state_features:
            self.last_state_features[service] = None
            self.last_action_features[service] = None
            self.last_reward[service] = None
            self.sample_last_experience[service] = False

        start_time = time.process_time()
        possible_migration_plans: List[List[Tuple[Service, LimitedMemoryCloud]]] = self.gather_possible_migration_plans(service, cloud, self.hyperparameters.recursion_depth)
        migration_queries: List[Tuple[Service, LimitedMemoryCloud]] = self.gather_migration_queries(possible_migration_plans)
        state_feature_vectors: List[List[float]]
        action_feature_vectors: List[List[float]]
        state_feature_vectors, action_feature_vectors = self.generate_migration_query_features(migration_queries, cloud_network)
        migration_query_qs = self.process_migration_queries(migration_queries, state_feature_vectors, action_feature_vectors)
        global_advantages = self.compute_global_advantages(possible_migration_plans, migration_query_qs)
        #(reward + 500) / 300
        #print("qs: ", [v*300 -500 for v in migration_query_qs.values()])
        #print("global_advantages: ", global_advantages)
        sample_this_experience = self.rng.random() <= self.hyperparameters.replay_buffer_sampling_rate
        if sample_this_experience:
            epsilon = self.hyperparameters.epsilon
        else:
            epsilon = 0
        #epsilon = self.hyperparameters.epsilon

        chosen_plan = self.epsilon_greedy_policy(possible_migration_plans,
                                                 global_advantages,
                                                 epsilon,
                                                 self.hyperparameters.initial_exploration_boost,
                                                 self.iteration)

        # compute decision's computation, communication (distributed computation), and decision times
        end_time = time.process_time()
        computation_time = end_time - start_time
        self.num_decisions += 1
        communciation_time = self.compute_communication_time(cloud_network, service, self.hyperparameters.recursion_depth > 0)

        # TODO: for comparison: add an estimate of the communication time for a centralized system.

        # record decision's computation, communication (distributed computation), and decision times
        #    1) running averages
        self.mean_computation_time = self.mean_computation_time + (computation_time - self.mean_computation_time) / self.num_decisions
        self.mean_communication_time = self.mean_communication_time + communciation_time / self.num_decisions
        if service.get_cloud() is cloud_network.central_cloud():
            self.num_decisions_service_at_cloud += 1
            self.mean_communication_time_service_at_cloud = self.mean_communication_time_service_at_cloud + communciation_time / self.num_decisions_service_at_cloud
        else:
            self.num_decisions_service_at_edge += 1
            self.mean_communication_time_service_at_edge = self.mean_communication_time_service_at_edge + communciation_time / self.num_decisions_service_at_edge
        #    2) histograms
        try:
            self.computation_time_histogram.add_value(computation_time)
            self.communication_time_histogram.add_value(communciation_time)
            self.decision_time_histogram.add_value(computation_time + communciation_time)

            if service.get_cloud() is cloud_network.central_cloud():
                self.computation_time_histogram_service_at_cloud.add_value(computation_time)
                self.communication_time_histogram_service_at_cloud.add_value(communciation_time)
                self.decision_time_histogram_service_at_cloud.add_value(computation_time + communciation_time)
            else:
                self.computation_time_histogram_service_at_edge.add_value(computation_time)
                self.communication_time_histogram_service_at_edge.add_value(communciation_time)
                self.decision_time_histogram_service_at_edge.add_value(computation_time + communciation_time)
        except OutOfHistogramBoundsError as e:
            pass  # decisions taking more than one second are usually outliers, e.g. during debugging.



        # create immediate state and action features for archiving
        state_feature_vector = self.features.state_features(service.get_cloud())
        possible_migration_targets = set([t for s, t in migration_queries if s == service])
        #migration_action_feature_vectors = [self.features.action_features(target, service, cloud_network) for target in possible_migration_targets]
        migration_action_feature_vectors = [action_feature_vectors[migration_queries.index((service, target))] for target in possible_migration_targets]
        chosen_dst_cloud = chosen_plan[0][1]
        selected_migration_action_features = action_feature_vectors[migration_queries.index((service, chosen_dst_cloud))]
        #selected_migration_action_features = self.features.action_features(chosen_plan[0][1], service, cloud_network)
        assert chosen_plan[0][0] == service

        # enter sample into replay memory:
        self.last_service = service
        if self.last_state_features[service] is not None:
            assert self.last_action_features[service] is not None
            assert self.last_reward[service] is not None
            #if self.rng.random() <= self.hyperparameters.replay_buffer_sampling_rate:
            if self.sample_last_experience[service]:
                qsample = DQNAgent.QSample(
                        self.last_state_features[service],
                        self.last_action_features[service],
                        self.last_reward[service],
                        state_feature_vector,
                        migration_action_feature_vectors)
                self.replay_memory.append(qsample)
                if len(self.replay_memory) > self.hyperparameters.max_replay_memory_size:
                    self.replay_memory.pop(0)
        # buffer the features of the current state and the chosen action
        self.last_state_features[service] = state_feature_vector
        self.last_action_features[service] = selected_migration_action_features
        self.sample_last_experience[service] = sample_this_experience

        # train the network if the episode length has passed
        if self.hyperparameters.do_training and 0 == self.iteration % self.hyperparameters.episode_length:
            training_start_time = time.process_time()
            self.train()
            training_end_time = time.process_time()
            self.num_training_episodes += 1
            self.total_training_time += training_end_time - training_start_time

        # return the chosen action
        if chosen_plan[0][1] == cloud:
            assert cloud is not None
            return [NoMigrationAction(service, cloud)]
        else:
            assert cloud is not None
            return [MigrationAction(s, s.get_cloud(), t) for (s, t) in reversed(chosen_plan)]

    def normalize_reward(self, reward):
        # return (reward - self.mean_reward) / self.reward_standard_deviation
        return (reward + 500) / 300

    def give_reward(self, reward):
        """
        This function gives an immediate reward for the last action. If this method isn't called,
        the reward for the last action is 0.
        :param reward:
        :return: None
        """

        service = self.last_service
        # TODO see if this reward scaling works well
        # self.last_reward[service] = reward * (1 - self.hyperparameters.discount_factor) * (1/5500)#100

        # incremental computation of reward's mean and std. deviation
        self.num_received_rewards += 1
        self.mean_reward = self.mean_reward + (reward - self.mean_reward) / self.num_received_rewards
        deviation = abs(self.mean_reward - reward)
        self.reward_standard_deviation = self.reward_standard_deviation + (deviation - self.reward_standard_deviation) / self.num_received_rewards
        # print('mean reward:', self.mean_reward, 'reward std dev:', self.reward_standard_deviation)

        self.last_reward[service] = reward
        # print(self.last_reward[service])

        self.total_episode_reward += reward
        self.max_episode_reward = max(self.max_episode_reward, reward)
        self.min_episode_reward = min(self.min_episode_reward, reward)

        if self.hyperparameters.episode_length - \
                1 == self.iteration % self.hyperparameters.episode_length:
            if self.verbose:
                print(
                        'avg reward: ',
                        self.total_episode_reward /
                        self.hyperparameters.episode_length)
            # track statistics
            self.avg_rewards.append(
                    self.total_episode_reward /
                    self.hyperparameters.episode_length)
            self.max_rewards.append(self.max_episode_reward)
            self.min_rewards.append(self.min_episode_reward)
            self.total_episode_reward = 0
            self.max_episode_reward = -math.inf
            self.min_episode_reward = math.inf

        self.iteration += 1
