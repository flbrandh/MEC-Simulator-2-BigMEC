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


class OutOfHistogramBoundsError(RuntimeError):
    """
    Exception that can be thrown if a value that is entered into a
    histogram is outside the bounds of its buckets.
    """
    def __init__(self, histogram, message):
        self.message = message
        self.histogram = histogram


class EquidistantHistogram:
    """
    This class represents a histogram where equally sized buckets are distributed along one axis.
    """

    def __init__(self, num_buckets, lower_bound, upper_bound):
        """
        Constructor.
        :param num_buckets: number of Buckets > 0
        :param lower_bound: lower bound of the Histogram
        :param upper_bound: upper bound of the Histogram
        """

        if num_buckets <= 0 :
            raise ValueError('The number of buckets in a EquidistantHistogram may not be lower than 1.')
        if lower_bound >= upper_bound:
            raise ValueError('The upper bound of an EquidistantHistogram must be greater that the lower bound.')
        self._buckets = [0] * num_buckets
        self._lower_bound = float(lower_bound)
        self._upper_bound = float(upper_bound)
        self._range = self._upper_bound - self._lower_bound
        self._bucket_stride = self._range / num_buckets


    def add_value(self, value):
        """
        Adds a value to the histogram.
        :param value: a value within the range of the histogram
        :return: None
        """
        if value == self._upper_bound: # boundary case: ensure the upper bound is included in the last bucket!
            self._buckets[-1] += 1
        else:
            bucket = int((value - self._lower_bound) / self._bucket_stride)
            if bucket < 0 or bucket >= len(self._buckets):
                raise OutOfHistogramBoundsError(self,
                                                "Value " +
                                                str(value) +
                                                " is out of the histogram bounds (" +
                                                str(self._lower_bound) +
                                                "," +
                                                str(self._upper_bound) +
                                                ")")
            self._buckets[bucket] += 1

    def to_string(self, cumulative, relative, separator=","):
        """
        Outputs the histogram as text
        :param cumulative: True, if the cumulative distribution shall be returned, False for the density
        :param relative: True, if the buckets shall be normalized, False for the actual numbers
        :param separator: a String to separate the list of buckets in the string.
        :return:
        """
        buckets = self._buckets
        if relative:
            total = sum(buckets)
            if total == 0:
                return separator.join(['0.0']*len(self._buckets))
            total = float(total)
            buckets = [bucket/total for bucket in buckets]
        if cumulative:
            buckets = buckets.copy()
            for i in range(1, len(buckets)):
                buckets[i] += buckets[i-1]

        return separator.join([str(b) for b in buckets])


    def __str__(self):
        return self.to_string(False, False)

    def num_buckets(self):
        """
        Returns the number of buckets in this histogram.
        :return: number of buckets
        """
        return len(self._buckets)

    def lower_bound(self):
        """
        Returns the lower bound of the histogram's buckets.
        :return: histogram's lower bound
        """
        return self._lower_bound

    def upper_bound(self):
        """
        Returns the upper bound of the histogram's buckets.
        :return: upper bound
        """
        return self._upper_bound