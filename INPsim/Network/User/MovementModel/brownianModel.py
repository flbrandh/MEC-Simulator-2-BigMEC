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


from INPsim.Network.User.MovementModel.interface import MovementModel


class BrownianMovementModel(MovementModel):
    """
    Implements a random, brownian movement model.
    """

    def __init__(self, initial_position, speed, rng):
        """
        Initializes the brownian movement model.
        :param initial_position: starting position of the user
        :param rng: random number generator to use for the movement generation
        """
        super(BrownianMovementModel, self).__init__(initial_position)
        self.rng = rng
        self.speed = speed

    def step(self, timestep):
        """
        performs one step of random movement
        :param timestep: the length of the time step in seconds
        :return:
        """
        self.pos = ((self.pos[0] + self.rng.uniform(-self.speed * timestep, self.speed * timestep)) %
                    1.0, (self.pos[1] + self.rng.uniform(-self.speed * timestep, self.speed * timestep)) % 1.0)