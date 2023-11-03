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


import tensorflow.keras as K
import tensorflow as tf


class QModel:
    """
    Encapsulates a function approximator and its training functionality
    """
    def __init__(self, hyperparameters, features):
        self.hyperparameters = hyperparameters
        self.features = features
        self.Q_model = self.build_model()

    def build_model(self):
        if self.hyperparameters.model:
            model = K.models.model_from_json(self.hyperparameters.model)
        else:
            state_action_features = K.Input(shape=(
                len(self.features.state_features()) + len(self.features.action_features()),))
            x = state_action_features
            for i in range(self.hyperparameters.network_depth):
                x = K.layers.Dense(
                    self.hyperparameters.network_width,
                    activation='tanh')(x)
                #x = K.layers.Dropout(0.5)(x)

            Q = K.layers.Dense(1, activation='linear')(x)
            model = K.Model(
                inputs=state_action_features,
                outputs=Q)
        # compile model
        model.compile(loss='mean_squared_error',
                      # optimizer='rmsprop')
                      optimizer=K.optimizers.RMSprop(learning_rate=0.001, rho=0.999))  # optimizer=K.optimizers.RMSprop(learning_rate=0.0001, rho=0.9))
        #TODO: Adam or Adagrad might be better because they assign different step sizes to different dimensions.

        # K.utils.plot_model(model, to_file='DQN_model.png')

        # converter = tf.lite.TFLiteConverter.from_keras_model(model)
        # converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        # converter.inference_input_type = tf.int8  # or tf.uint8
        # converter.inference_output_type = tf.int8  # or tf.uint8
        # tflite_model = converter.convert()
        #
        # with open('model.tflite', 'wb') as f:
        #     f.write(tflite_model)
        #     print("Wrote Model!")

        return model

    def serialize_model(self):
        return self.Q_model.get_weights()

    def deserialize_model(self, weights):
        self.Q_model.set_weights(weights)
