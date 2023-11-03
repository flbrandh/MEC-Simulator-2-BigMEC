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
import abc


class MobilityTraceMovementModel(MovementModel):
    """
    Encapsulates a movement model for users.
    """

    def __init__(self, mobility_trace):
        """
        Initializes the movement model with an initial position
        :param initial_position:
        """
        self._mobility_trace = mobility_trace
        self._trace_time = 0
        self._trace_length = mobility_trace.end_time() - mobility_trace.start_time()

    @abc.abstractmethod
    def step(self, timestep):
        """
        Advance the movement model by one step.
        :param timestep: the length of the step in seconds
        :return: nothing
        """
        self._trace_time += timestep
        if self._trace_time < self._trace_length:
            # update the position
            posV = self._mobility_trace.get_position(
                self._trace_time + self._mobility_trace.start_time())
            # todo change all vectors from tuples to the Vec2 class
            self.pos = (posV.x, posV.y)


