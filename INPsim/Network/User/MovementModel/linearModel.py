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
import math


class LinearMovementModel(MovementModel):
    """
    Implements a randomied linear movement model.
    """

    def __init__(self, initial_position, speed, rng, aabb):
        """
        Initializes the linear movement model.
        All movement destinations are within the unit square.
        :param initial_position: starting position of th user
        :param speed: speed of the user in meters per second
        :param rng: random number generator to use for the movement generation
        """
        super(LinearMovementModel, self).__init__(initial_position)
        self._rng = rng
        self._aabb = aabb
        self.speed = speed
        self.destination = self._new_destination()

    def _new_destination(self):
        """
        computes a new destination inside the unit square
        :return:
        """
        return (
            self._rng.uniform(
                self._aabb.min_x,
                self._aabb.max_x),
            self._rng.uniform(
                self._aabb.min_y,
                self._aabb.max_y))

    def step(self, timestep):
        """
        Performs one step of movement.
        :param timestep: Length of the timestep in seconds
        :return: nothing
        """
        x, y = self.get_pos()
        dx, dy = self.destination[0] - x, self.destination[1] - y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance < self.speed:
            self.pos = self.destination
            self.destination = self._new_destination()
        else:
            dx, dy = dx / distance, dy / distance
            self.pos = x + self.speed * timestep * dx, y + self.speed * timestep * dy