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


class RANModel:
    """
    Abstract base class for the RAN-Model.
    """

    def update_user_access_points(self, user_manager, cloud_network):
        pass


class NearestNeighborRANModel(RANModel):
    """
    Assigns each user to the closest base station (euclidian distance)
    """

    def __init__(self, base_stations, grid_resolution):
        self._base_stations = base_stations
        self._grid_resolution = grid_resolution
        min_x, max_x, min_y, max_y = self._get_base_station_area_dimensions()
        max_dimension = max(max_x - min_x, max_y - min_y)
        self._tile_size = max_dimension / (self._grid_resolution - 1)
        self._inv_tile_size = 1.0 / self._tile_size
        self._grid_offset_x = min_x
        self._grid_offset_y = min_y

        self._initialize_grid()
        self._insert_base_stations_into_grid()

    def _insert_base_stations_into_grid(self):
        for base_station in self._base_stations:
            x, y = base_station.get_pos()
            cx, cy = self._world_coordinates_to_cell_index(x, y)
            assert (0 <= cx < self._grid_resolution and 0 <=
                    cy < self._grid_resolution)
            self._grid[cx][cy].append(base_station)

    def _initialize_grid(self):
        self._grid = []
        for ix in range(self._grid_resolution):
            row = []
            for iy in range(self._grid_resolution):
                cell = []
                row.append(cell)
            self._grid.append(row)

    def _world_to_grid_coordinates(self, x, y):
        # translating the coordinates to the grids origin.
        tx, ty = x - self._grid_offset_x, y - self._grid_offset_y
        # scaling the coordinates to the grid-scale
        return tx * self._inv_tile_size, ty * self._inv_tile_size

    def _world_coordinates_to_cell_index(self, x, y):
        """
        gets the cell index of a point in world-coordinates
        :param x: x-xoordinate of the point in world-coordinates
        :param y: y-coordinate of the point in world-coordinates
        :return: ix,iy, the cell-coordinates. Note that this might also be outside the allocated grid.
        """
        gx, gy = self._world_to_grid_coordinates(x, y)
        return int(gx), int(gy)

    def _get_base_station_area_dimensions(self):
        min_x = math.inf
        max_x = -math.inf
        min_y = math.inf
        max_y = -math.inf

        for base_station in self._base_stations:
            x, y = base_station.get_pos()
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)

        return min_x, max_x, min_y, max_y

    def _get_ring_cells(self, smaller_box, larger_box):
        """
        a generator that yields the cells of a ring in the grid.
        a ring is specified by a smaller and a larger ring.
        yield all cells that are part of the larger ring, but not the smaller.
        if there is no smaller ring, return the whole box.
        :param smaller_ring: (min_x, max_x, min_y, max_y) / None
        :param larger_ring: (min_x, max_x, min_y, max_y) : all int, s.t. the yielded cells are >=min_x and <max_x, y analogous
        :return: None, Yield the cells
        """
        larger_min_x, larger_max_x, larger_min_y, larger_max_y = larger_box
        if not smaller_box:
            for ix in range(max(0, larger_min_x), min(
                    self._grid_resolution, larger_max_x)):
                for iy in range(larger_min_y, larger_max_y):
                    if 0 <= ix < self._grid_resolution and 0 <= iy < self._grid_resolution:
                        yield self._grid[ix][iy]
        else:
            smaller_min_x, smaller_max_x, smaller_min_y, smaller_max_y = smaller_box
            for ix in range(max(0, larger_min_x), min(
                    self._grid_resolution, larger_max_x)):
                for iy in range(max(0, larger_min_y), min(
                        self._grid_resolution, larger_max_y)):
                    if not (smaller_min_x <= ix < smaller_max_x and smaller_min_y <= iy <
                            smaller_max_y):  # check if the cell is contained in the smaller box
                        if 0 <= ix < self._grid_resolution and 0 <= iy < self._grid_resolution:
                            yield self._grid[ix][iy]

    def get_closest_base_station(self, user_position, blacklist=[]):
        gx, gy = self._world_to_grid_coordinates(
            user_position[0], user_position[1])
        cx, cy = self._world_coordinates_to_cell_index(
            user_position[0], user_position[1])
        closest_base_station = None
        closest_base_station_sq_distance = math.inf
        smaller_box = None  # the smaller box of the next iteration
        # the larger box of the next iteration
        larger_box = (cx, cx + 1, cy, cy + 1)
        while smaller_box != larger_box:
            # get the closest base station from the next ring
            for cell in self._get_ring_cells(smaller_box, larger_box):
                for base_station in cell:
                    if base_station not in blacklist:
                        bs_x, bs_y = base_station.get_pos()
                        bs_gx, bs_gy = self._world_to_grid_coordinates(
                            bs_x, bs_y)
                        sq_distance = (bs_gx - gx)**2 + (bs_gy - gy)**2
                        if sq_distance < closest_base_station_sq_distance:
                            closest_base_station_sq_distance = sq_distance
                            closest_base_station = base_station
            smaller_box = larger_box

            if closest_base_station:  # a base station was found. no, make sue it's actually the closest one. There might be closer ones in the difference between the circle and the rectangle.
                # next iteration, check all cells that could contain a closer
                # base station than the one that's closest at the moment (all
                # cells that touch the circumference)
                closest_base_station_distance = math.sqrt(
                    closest_base_station_sq_distance)
                larger_box = (int(gx - closest_base_station_distance),
                              int(gx + closest_base_station_distance) + 1,
                              int(gy - closest_base_station_distance),
                              int(gy + closest_base_station_distance) + 1)
            else:  # no base station was found yet. => expand the search radius
                larger_box = (larger_box[0] - 1,
                              larger_box[1] + 1,
                              larger_box[2] - 1,
                              larger_box[3] + 1)
        return closest_base_station

    def _get_closest_base_station_brute_force(
            self, user_position, blacklist=[]):
        """
        Brute forces the estimation of the nearest base station
        :param user_position: position of the user (Vec2)
        :param cloud_network: cloud network that contains the base stations
        :return: The base station with the shorest euclidian distance from the user's position
        """
        closest_sq_distance = math.inf
        closest_sq_distance_base_station = None
        for base_station in self._base_stations:
            if base_station not in blacklist:
                sq_distance = (
                    Vec2.from_tuple(
                        base_station.get_pos()) -
                    Vec2.from_tuple(user_position)).sq_length()
                if sq_distance < closest_sq_distance:
                    closest_sq_distance = sq_distance
                    closest_sq_distance_base_station = base_station
        return closest_sq_distance_base_station

    def update_user_access_points(self, user_manager, cloud_network):
        for user in user_manager.users():
            user.set_base_station(
                self.get_closest_base_station(
                    Vec2.from_tuple(
                        user.get_movement_model().get_pos()),
                    cloud_network))
