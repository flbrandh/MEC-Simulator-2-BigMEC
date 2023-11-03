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


import math

class Vec2:
    """
    2d-Vector
    """

    def __init__(self, x = 0, y = 0):
        self.x = x
        self.y = y

    @staticmethod
    def from_tuple( tuple):
        return Vec2(tuple[0],tuple[1])

    def as_tuple(self):
        return (self.x, self.y)

    def dot(self,other):
        return self.x*other.x + self.y*other.y

    def sq_length(self):
        return self.dot(self)

    def length(self):
        return math.sqrt(self.sq_length())

    def __add__(self, other):
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        return Vec2(self.x*scalar, self.y*scalar)

    def __truediv__(self, scalar):
        return Vec2(self.x/scalar, self.y/scalar)

    def __str__(self):
        return "Vec2({0},{1})".format(self.x, self.y)




class AABB2:
    """
    Axis-aligned 2d-bounding box.
    """

    def __init__(self, min_x, max_x, min_y, max_y):
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y

    @staticmethod
    def from_vectors(vectors):
        """
        Constructs an AABB2 from a list of vectors.
        :param vectors a non-empty list of vectors
        :return: An AABB2 that includes all vectors in the list and nothing more.
        """
        assert len(vectors) > 0
        min_x, min_y = max_x, max_y = vectors[0].as_tuple()
        for vec in vectors:
            if vec.x > max_x:
                max_x = vec.x
            elif vec.x < min_x:
                min_x = vec.x
            if vec.y > max_y:
                max_y = vec.y
            elif vec.y < min_y:
                min_y = vec.y
        return AABB2(min_x, max_x, min_y, max_y)

    def __add__(self, other):
        """
        Adding two bounding boxes results in a bounding box that contains both boxes.
        :param other: another AABB2
        :return: an AABB2 that contains this and other's bounding box
        """
        return AABB2(min(self.min_x, other.min_x),
                     max(self.max_x, other.max_x),
                     min(self.min_y, other.min_y),
                     max(self.max_y, other.max_y))

    def shift(self, direction):
        """
        Shifts the bounding ox as a whole.
        :param direction: Vec2 that represents the shift
        :return: None
        """
        self.min_x += direction.x
        self.max_x += direction.x
        self.min_y += direction.y
        self.max_y += direction.y

    def width(self):
        """
        Returns the AABB-dimensions along the x-axis (a.k.a. width)
        :return: width of the bounding box
        """
        return self.max_x - self.min_x

    def height(self):
        """
        Returns the AAB-dimension along the y-axix (a.k.a. height)
        :return:
        """
        return self.max_y - self.min_y

    def center(self):
        """
        Returns the center point of the AABB
        :return: Vec2 that marks the center of the bounding box
        """
        return Vec2(.5 * (self.min_x+self.max_x), .5 * 
                    (self.min_y + self.max_y))

    def intersects(self, other):
        """
        Checks if the bounding box intersects another, not counting touching boundaries.
        :param other: other AABB
        :return: True, if the AABBs truly intersect, False if not
        """
        center_dist = self.center() - other.center()
        return (abs(center_dist.x) * 2 < self.width() + other.width()) and \
               (abs(center_dist.y) * 2 < self.height() + other.height())

    def intersects_or_touches(self, other):
        """
        Checks if the bounding box intersects another, including touching boundaries.
        :param other:  the other AABB
        :return: True, if the AABBs intersect or touch, False otherwise
        """
        center_dist = self.center() - other.center()
        return (abs(center_dist.x) * 2 <= self.width() + other.width()) and \
               (abs(center_dist.y) * 2 <= self.height() + other.height())

    def includes_AABB2(self, other):
        """
        Checks if this AABB2 completely includes another AABB2.
        :param other: another AABB2
        :return: True, if other is included in self. False if not.
        """
        return self.min_x <= other.min_x and self.max_x >= other.max_x and \
               self.min_y <= other.min_y and self.max_y >= other.max_y

    def __str__(self):
        return "AABB2({0}~{1},{2}~{3})".format(
          self.min_x,self.max_x, self.min_y, self.max_y)