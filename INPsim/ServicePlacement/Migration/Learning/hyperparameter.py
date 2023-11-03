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


import random
import json


class QHyperparameters:
    def __init__(self,
                 default=True,
                 in_hparam=None,
                 max_num_neighbor_clouds=10,
                 max_num_services=10,
                 do_training=True,
                 model=None,
                 network_width=50,
                 network_depth=7,
                 discount_factor=0.9,
                 max_replay_memory_size=10000,
                 episode_length=100,
                 epsilon=0.1,
                 initial_exploration_boost=1000,
                 batch_fraction_of_replay_memory=0.1,
                 num_epochs=50,
                 target_model_update_frequency=1,
                 recursion_depth=2,
                 replay_buffer_sampling_rate = 1.0):
        if default:
            # problem-posing-related:
            self.max_num_neighbor_clouds = max_num_neighbor_clouds
            self.max_num_services = max_num_services
            self.do_training = do_training
            # NN-related:
            self.model = model  # if None: new model, acoding to the below parameters. String: JSON of a model.
            self.network_width = network_width
            self.network_depth = network_depth
            self.discount_factor = discount_factor
            self.max_replay_memory_size = max_replay_memory_size
            # training-related
            self.episode_length = episode_length
            self.epsilon = epsilon
            self.initial_exploration_boost = initial_exploration_boost
            self.batch_fraction_of_replay_memory = batch_fraction_of_replay_memory
            self.num_epochs = num_epochs
            self.replay_buffer_sampling_rate = replay_buffer_sampling_rate
            self.target_model_update_frequency = target_model_update_frequency  # if 1: no target network
            # displacement cost-related
            self.recursion_depth = recursion_depth
        else:
            if in_hparam is None:
                self.create_hyperparameters()

            else:
                with open(in_hparam + '.txt') as hparam_file:
                        hparam = json.load(hparam_file)
                        for h in hparam['node_related']:
                            self.max_num_neighbor_clouds = h['max_num_neighbor_clouds']
                            self.max_num_services = h['max_num_services']
                            self.do_training = h['do_training']
                        for h in hparam['nn_related']:
                            self.model = h['model']
                            self.network_width = h['network_width']
                            self.network_depth = h['network_depth']
                            self.discount_factor = h['discount_factor']
                            self.max_replay_memory_size = h['max_replay_memory_size']
                        for h in hparam['training_related']:
                            self.episode_length = h['episode_length']
                            self.epsilon = h['epsilon']
                            self.initial_exploration_boost = h['initial_exploration_boost']
                            self.batch_fraction_of_replay_memory = h['batch_fraction_of_replay_memory']
                            self.num_epochs = h['num_epochs']
                            self.target_model_update_frequency = h['target_model_update_frequency']
                        for h in hparam['displacement_cost_related']:
                            self.recursion_depth = h['recursion_depth']

    def create_hyperparameters(self):
        # cloud (node) related
        self.max_num_neighbor_clouds = random.randint(5, 100)
        self.max_num_services = random.randint(5, 100)
        self.do_training = True

        # nn related
        self.model = None
        self.network_width = random.randint(20, 300)
        self.network_depth = random.randint(1, 50)
        self.discount_factor = round(random.random(), 2)
        self.max_replay_memory_size = 10000

        # training related
        self.episode_length = random.randint(50, 500)
        self.epsilon = round(random.random(), 2)
        self.initial_exploration_boost = 1000
        self.batch_fraction_of_replay_memory = round(random.random(), 2)
        self.num_epochs = random.randint(50, 500)
        self.target_model_update_frequency = 1

        # displacement cost related
        self.recursion_depth = random.randint(0, 10)

    def get_serializable_dict(self):
        return self.__dict__