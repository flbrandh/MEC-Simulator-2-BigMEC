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


from INPsim.vmath import *


class MobilityTrace:
    """
    Represents a mobility trace: a series of positions at  points in time.
    """

    def __init__(self):
        self.time_points = []  # time in seconds
        self.positions = []  # 2d position Vec2s in meters, relative to some point of reference

    def add_data_point(self, time, position):
        #time in seconds
        assert (not self.time_points) or time >= self.time_points[-1]
        self.time_points.append(time)
        self.positions.append(position)

    def get_position(self, time):
        """
        Gets the position of this trace at an instant of time.
        :param time: time in seconds
        :return: 2d position Vec2 in meters, or None, if time lies outside the trace interval
        """
        # check if the trace has at least 2 data points (otherwise it's invalid)
        if len(self.time_points) < 2:
            return None
        # check if time is outside trace interval:
        if time < self.time_points[0] or time > self.time_points[-1]:
            return None
        else:
            # linear search:
            step = 0
            # TODO have cache for sequential access
            while self.time_points[step] < time:
                step += 1
            # do linear interpolation:
            time1 = self.time_points[step - 1]
            time2 = self.time_points[step]
            fraction = (time - time2) / (time2 - time1)
            pos1 = self.positions[step - 1]
            pos2 = self.positions[step]
            return pos1 * fraction + pos2 * (1 - fraction)

    def start_time(self):
        return self.time_points[0]

    def end_time(self):
        return self.time_points[-1]

    def min_x(self):
        min_x = math.inf
        for x, y in self.positions:
            if x < min_x:
                min_x = x
        return min_x

    def max_x(self):
        max_x = -math.inf
        for x, y in self.positions:
            if x > max_x:
                max_x = x

    def min_y(self):
        min_y = math.inf
        for x, y in self.positions:
            if y < min_y:
                min_y = y
        return min_y

    def max_y(self):
        max_y = -math.inf
        for x, y in self.positions:
            if y > max_y:
                max_y = y

    def __len__(self):
        return len(self.time_points)


class ImmutableMobilityTrace(MobilityTrace):
    """
    Represents an immutable mobility trace: a series of positions at  points in time.
    This class offers more efficient access to the position bounding box
    """

    def __init__(self, mobility_trace):
        self.time_points = mobility_trace.time_points.copy()  # time in seconds
        # 2d position tuples in meters, relative to some point of reference
        self.positions = mobility_trace.positions.copy()

        self._pos_aabb = AABB2.from_vectors(self.positions)

    def min_x(self):
        return self._pos_aabb.min_x

    def max_x(self):
        return self._pos_aabb.max_x

    def min_y(self):
        return self._pos_aabb.min_y

    def max_y(self):
        return self._pos_aabb.max_y

    def pos_aabb(self):
        return self._pos_aabb
