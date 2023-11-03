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


from typing import Optional


class RunningMean:
    """
    Implements a running mean that doesn't store all the samples.
    """

    def __init__(self) -> None:
        self._num_samples: int = 0
        self._sum: float = 0.0

    def add_sample(self, sample: float) -> None:
        """
        Adds a sample to the running mean.
        :param sample: the value of the new sample
        """
        self._num_samples += 1
        self._sum += sample

    def get_mean(self) -> Optional[float]:
        """
        Returns the current mean if there is a mean.
        :return: Current mean. None, if there are no samples.
        """
        if self._num_samples == 0:
            return None
        else:
            return self._sum/self._num_samples
