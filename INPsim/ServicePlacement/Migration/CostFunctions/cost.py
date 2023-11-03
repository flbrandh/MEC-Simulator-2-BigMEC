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


class Cost:
    """
    This class represents a placement_cost related cost, separated into
    placement_cost, and transition_cost
    """

    def __init__(self,
                 placement_cost: float,
                 transition_cost: float):
        """
        Initializes a cost.
        :param placement_cost: placement cost (cost of the state)
        :param transition_cost: transition cost
        """
        self._placement_cost = placement_cost
        self._transition_cost = transition_cost

    def placement_cost(self) -> float:
        """
        Gets the placement part of the cost.
        :return: placement cost (state cost)
        """
        return self._placement_cost

    def transition_cost(self) -> float:
        """
        Gets the transition part of the cost.
        :return: transition cost
        """
        return self._transition_cost

    def total(self) -> float:
        """
        Gets the total cost (placement cost + transition cost)
        :return: total cost
        """
        return self._placement_cost + self._transition_cost

    def __add__(self, other: 'Cost') -> 'Cost':
        """
        Adds two costs together
        :param other: the other cost
        :return: the new, added cost object
        """
        return Cost(self.placement_cost() + other.placement_cost(),
                    self.transition_cost() + other.transition_cost())

    def __truediv__(self, other: float) -> 'Cost':
        return Cost(self.placement_cost()/other, self.transition_cost()/other)