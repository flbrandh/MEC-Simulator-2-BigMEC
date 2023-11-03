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


from INPsim.Network.User.MovementModel.brownianModel import BrownianMovementModel
from INPsim.Network.User.MovementModel.linearModel import LinearMovementModel
from INPsim.Network.User.Manager.userManager import UserManager
from INPsim.vmath import AABB2


class ConstantRandomUserManager(UserManager):
    """
    Always has a constant number of random users within a unit square.
    All users are created at the beginning of the configured_simulation.
    """

    def __init__(
        self,
        service_model,
        rng,
        movement_type,
        num_users,
        aabb=AABB2(
            0,
            1,
            0,
            1)):
        """
        Initializes the usr manager.
        :param rng: random number generator for the randomized users
        :param movement_type: either 'brownian' or 'linear'
        """
        super(
            ConstantRandomUserManager,
            self).__init__(
            service_model=service_model)
        self._rng = rng
        self._movement_type = movement_type
        self._num_users = num_users

        self._aabb = aabb

        self._create_all_users()

    def _random_user_position(self):
        return (
            self._rng.uniform(
                self._aabb.min_x,
                self._aabb.max_x),
            self._rng.uniform(
                self._aabb.min_y,
                self._aabb.max_y))

    def _create_all_users(self):
        user_positions = [self._random_user_position()
                          for x in range(self._num_users)]

        for pos in user_positions:
            new_user = None
            if self._movement_type == 'brownian':
                # new_user = BrownianUser(pos=pos, base_station= self.get_closest_base_station(pos), rng = self.rng)
                self.create_user(BrownianMovementModel(pos, 0.1, self._rng))
            elif self._movement_type == 'linear':
                # new_user = LinearUser(pos=pos, base_station= self.get_closest_base_station(pos), rng = self.rng)
                self.create_user(LinearMovementModel(pos,
                                                     10,  # 10 m/s is approx. 36km/h,
                                                     self._rng,
                                                     self._aabb))
            else:
                raise ValueError(
                    "invalid movement model specified in parameter '_movement_model'. Valid options are 'brownian' and 'linear'.")