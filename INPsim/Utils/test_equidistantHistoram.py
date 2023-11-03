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


from unittest import TestCase
import pytest
from .histogram import EquidistantHistogram,OutOfHistogramBoundsError

class TestEquidistantHistogram(TestCase):

    def test___init__(self):
        hist = EquidistantHistogram(3, -1, 2)
        assert hist.upper_bound() == 2
        assert hist.lower_bound() == -1
        assert hist.num_buckets() == 3

    def test__init__invalid_num_buckets(self):
        with pytest.raises(ValueError):
            hist = EquidistantHistogram(0, -2, 5)

        with pytest.raises(ValueError):
            hist = EquidistantHistogram(-3, -2, 5)

    def test__init__invalid_num_buckets_type(self):
        with pytest.raises(TypeError):
            hist = EquidistantHistogram(3.3, -2, 5)

    def test__init__equal_bounds(self):
        with pytest.raises(ValueError):
            hist = EquidistantHistogram(4, 3.14, 3.14)

    def test__init__reversed_bounds(self):
        with pytest.raises(ValueError):
            hist = EquidistantHistogram(4, 3.14, -3.14)

    def test_add_value(self):
        hist = EquidistantHistogram(3, -1, 2)
        hist.add_value(0.5)
        assert hist._buckets[0] == 0
        assert hist._buckets[1] == 1
        assert hist._buckets[2] == 0

    def test_add_value_below_lower_bound(self):
        hist = EquidistantHistogram(3, -1, 2)
        with pytest.raises(OutOfHistogramBoundsError) as e:
            hist.add_value(-42)
        assert e.value.histogram is hist
        assert "Value -42 is out of the histogram bounds (-1.0,2.0)" in str(e.value)
        assert hist._buckets[0] == 0
        assert hist._buckets[1] == 0
        assert hist._buckets[2] == 0

    def test_add_value_above_upper_bound(self):
        hist = EquidistantHistogram(3, -1, 2)
        with pytest.raises(OutOfHistogramBoundsError) as e:
            hist.add_value(42)
        assert e.value.histogram is hist
        assert "Value 42 is out of the histogram bounds (-1.0,2.0)" in str(e.value)
        assert hist._buckets[0] == 0
        assert hist._buckets[1] == 0
        assert hist._buckets[2] == 0

    def test_add_value_lower_bound(self):
        hist = EquidistantHistogram(3, -1, 2)
        hist.add_value(-1.0)
        assert hist._buckets[0] == 1
        assert hist._buckets[1] == 0
        assert hist._buckets[2] == 0

    def test_add_value_upper_bound(self):
        hist = EquidistantHistogram(3, -1, 2)
        hist.add_value(2.0)
        assert hist._buckets[0] == 0
        assert hist._buckets[1] == 0
        assert hist._buckets[2] == 1

    def test_add_value_internal_boundary(self):
        hist = EquidistantHistogram(3, -1, 2)
        hist.add_value(0)
        assert hist._buckets[0] == 0
        assert hist._buckets[1] == 1
        assert hist._buckets[2] == 0

    def test_to_string_non_cumulative_absolute(self):
        hist = EquidistantHistogram(3, -1, 2)
        hist.add_value(-0.3)
        hist.add_value(-0.999)
        hist.add_value(1.5)
        assert hist.to_string(False, False) == "2,0,1"

    def test_to_string_cumulative_absolute(self):
        hist = EquidistantHistogram(3, -1, 2)
        hist.add_value(-0.3)
        hist.add_value(-0.999)
        hist.add_value(1.5)
        assert hist.to_string(True, False) == "2,2,3"

    def test_to_string_cumulative_absolute_single_bucket(self):
        hist = EquidistantHistogram(1, -1, 2)
        hist.add_value(-0.3)
        hist.add_value(-0.999)
        hist.add_value(1.5)
        assert hist.to_string(True, False) == "3"

    def test_to_string_non_cumulative_relative(self):
        hist = EquidistantHistogram(3, -1, 2)
        hist.add_value(-0.3)
        hist.add_value(-0.999)
        hist.add_value(1.5)
        hist.add_value(0.5)
        assert hist.to_string(False, True) == "0.5,0.25,0.25"

    def test_to_string_cumulative_relative(self):
        hist = EquidistantHistogram(3, -1, 2)
        hist.add_value(-0.3)
        hist.add_value(-0.999)
        hist.add_value(1.5)
        hist.add_value(0.5)
        assert hist.to_string(True, True) == "0.5,0.75,1.0"

    def test_to_string_cumulative_relative_empty_histogram(self):
        hist = EquidistantHistogram(3, -1, 2)
        assert hist.to_string(True, True) == "0.0,0.0,0.0"

    def test___str__(self):
        hist = EquidistantHistogram(3, -1, 2)
        hist.add_value(-0.3)
        hist.add_value(-0.999)
        hist.add_value(1.5)
        assert str(hist) == "2,0,1"

    def test_num_buckets(self):
        hist = EquidistantHistogram(2, 5, 10)
        assert hist.num_buckets() == 2

    def test_lower_bound(self):
        hist = EquidistantHistogram(1, -1, 5)
        assert hist.lower_bound() == -1

    def test_upper_bound(self):
        hist = EquidistantHistogram(1, -1, 5)
        assert hist.upper_bound() == 5