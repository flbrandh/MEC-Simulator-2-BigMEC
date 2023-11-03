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


from INPsim.ServicePlacement.Migration.Learning.DQNAgent.agent import DQNAgent
from INPsim.ServicePlacement.Migration.Learning.model import QModel
import numpy as np


class ClippingDDQNAgent(DQNAgent):

    def _init_models(self):
        self.Q_a = QModel(self.hyperparameters, self.features).Q_model
        self.Q_a_target = QModel(self.hyperparameters, self.features).Q_model
        self.Q_a_target.set_weights(self.Q_a.get_weights())
        self.Q_b = QModel(self.hyperparameters, self.features).Q_model
        self.Q_b_target = QModel(self.hyperparameters, self.features).Q_model
        self.Q_b_target.set_weights(self.Q_b.get_weights())

    def __getstate__(self):
        """
        For pickling.
        :return:
        """
        state = self.__dict__.copy()
        state['Q_a'] = state['Q_a'].get_weights()
        state['Q_a_target'] = state['Q_a_target'].get_weights()
        state['Q_b'] = state['Q_b'].get_weights()
        state['Q_b_target'] = state['Q_b_target'].get_weights()
        return state

    def __setstate__(self, newstate):
        """
        For unpickling.
        :param newstate:
        :return:
        """
        self.__dict__.update(newstate)
        for model in ['Q_a', 'Q_a_target', 'Q_b', 'Q_b_target']:
            params = newstate[model]
            newstate[model] = QModel(
                self.hyperparameters, self.features).Q_model
            newstate[model].set_weights(params)
        self.__dict__.update(newstate)

    def get_prediction_model(self):
        return self.Q_a

    def get_model_parameters(self):
        return {"Q_a": self.Q_a.get_weights(),
                "Q_a_target": self.Q_a_target.get_weights(),
                "Q_b": self.Q_b.get_weights(),
                "Q_b_target": self.Q_b_target.get_weights()}

    def set_model_parameters(self, models):
        self.Q_a.set_weights(models["Q_a"])
        self.Q_a_target.set_weights(models["Q_a_target"])
        self.Q_b.set_weights(models["Q_b"])
        self.Q_b_target.set_weights(models["Q_b_target"])


    def _construct_training_outputs(self, minibatch_indices):
        minibatch_size = len(minibatch_indices)
        y = np.zeros(minibatch_size)

        nn_inputs = []
        for i, batch_sample in enumerate(minibatch_indices):
            qsample = self.replay_memory[batch_sample]
            state_features = qsample.state_features
            for action_features in qsample.possible_next_action_features:
                nn_inputs.append(state_features + action_features)

        nn_inputs = np.array(nn_inputs)
        nn_outputs_a = self.Q_a_target.predict(nn_inputs)
        nn_outputs_b = self.Q_b_target.predict(nn_inputs)

        print(
            'mean a:',
            np.mean(nn_outputs_a),
            'var a:',
            np.var(nn_outputs_a),
            'mean b:',
            np.mean(nn_outputs_b),
            'var b:',
            np.var(nn_outputs_b))
        r = []


        last_index = 0
        for i, batch_sample in enumerate(minibatch_indices):
            qsample = self.replay_memory[batch_sample]
            normalized_reward = self.normalize_reward(qsample.reward)
            num_possible_actions = len(qsample.possible_next_action_features)
            max_state_action_value = min(max(nn_outputs_a[last_index:last_index + num_possible_actions]),
                                         max(nn_outputs_b[last_index:last_index + num_possible_actions]))  # finding the value of the next action
            #print('max_a:',max(nn_outputs_a[last_index:last_index + num_possible_actions]), ' max_b:', max(nn_outputs_b[last_index:last_index + num_possible_actions]), ' min_a:',min(nn_outputs_a[last_index:last_index + num_possible_actions]), ' min_b:', min(nn_outputs_b[last_index:last_index + num_possible_actions]), ' minmax:', max_state_action_value)
            r.append(normalized_reward)
            y[i] = normalized_reward + self.hyperparameters.discount_factor * max_state_action_value  # bellman equation
            last_index += num_possible_actions
        print('mean_norm_rew.: ', np.mean(r), ' mean_discount_part:', np.mean(y)-np.mean(r))
        self.predicted_Qs.append(np.mean(y)-np.mean(r))
        return y

    def _train_minibatch(self, minibatch_indices):
        # construct x
        x = self._construct_training_inputs(minibatch_indices)
        y = self._construct_training_outputs(minibatch_indices)

        #self.predicted_Qs.append(np.mean(y))

        print('mean y:', np.mean(y), 'var y:', np.var(y))

        # train
        history = self.Q_b.fit(
            x,
            y,
            epochs=self.hyperparameters.num_epochs,
            batch_size=32,
            verbose=0)
        history = self.Q_a.fit(
            x,
            y,
            epochs=self.hyperparameters.num_epochs,
            batch_size=32,
            verbose=0)

        # target update
        tau = 1#0.1#001#0.00001
        update_frequency = 1

        def interpolate_weights(a, b):
            mlist = []
            for l1, l2 in zip(a, b):
                m = []
                for e1, e2 in zip(l1, l2):
                    if isinstance(e1, list):  # check if it's a 1d or 2d tensor
                        l = []
                        for e3, e4 in zip(e1, e2):
                            l.append(tau * e3 + (1 - tau) * e4)
                        m.append(l)
                    else:
                        m.append(tau * e1 + (1 - tau) * e2)
                mlist.append(np.array(m))
            return mlist

        if self.episode % update_frequency == 0:
            self.Q_a_target.set_weights(
                interpolate_weights(
                    self.Q_a.get_weights(),
                    self.Q_a_target.get_weights()))
            self.Q_b_target.set_weights(
                interpolate_weights(
                    self.Q_b.get_weights(),
                    self.Q_b_target.get_weights()))

        return history