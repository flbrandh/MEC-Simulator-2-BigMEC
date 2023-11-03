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


class Connection:
    """
    This class implements the base class for (directed) connections between nodes.
    """

    def __init__(self, src, dst):
        """
        Creates a new Connection obj.
        :param src: the source Node
        :param dst: the destination Node
        """
        self._src = src
        self._dst = dst

    @classmethod
    def create_default(cls, src, dst):
        """
        This is a factory method to initialize a connection from the used nodes only.
        :param src: source Node
        :param dst: destination Node
        :return: Connection
        """
        return cls(src, dst)

    @classmethod
    def connect_default_bidirectional(cls, src, dst, no_duplicates=True):
        """
        This is a factory method that connects two nodes with a default bidirectional connection.
        :param src: the first node to connect
        :param dst: the second node to connect
        :param no_duplicates: True, if no redundant connections should be established.
        :return:
        """
        if dst not in src.get_neighbor_nodes():
            src.add_connection(cls.create_default(src, dst))
        if src not in dst.get_neighbor_nodes():
            dst.add_connection(cls.create_default(dst, src))

    def src(self):
        """
        Returns the source Node of this connection
        :return: source Node
        """
        return self._src

    def dst(self):
        """
        Returns the destinaton node of this connection
        :return: destination Node
        """
        return self._dst

    def weight(self):
        """
        The weight of this connection for graph operations like pathfinding, etc.
        :return: always 1 for this basic connection
        """
        return 1


class ConstantLatencyConnection(Connection):
    """
    This is a (directed) Connection with a constant immutable latency attribute.
    """

    def __init__(self, src, dst, latency):
        """
        Creates a new Connection with constant latency.
        :param src: source Node
        :param dst: destinaton Node
        :param latency: latency of information from src to dst
        """
        super(ConstantLatencyConnection, self).__init__(src, dst)
        self._latency = latency

    @classmethod
    def create_default(cls, src, dst):
        """
        This is a factory method to initialize a connection from the used nodes only.
        The latency of a connection is always 1 for now.
        :param src: source Node
        :param dst: destination Node
        :return: ConstantLatencyConnection
        """
        latency = 1
        return cls(src, dst, latency)

    def latency(self):
        """
        Returns the latency of this connection.
        :return: latency from src to dst
        """
        return self._latency

    def weight(self):
        """
        The weight of this connection, as measured by th constant latency; the delay of the information
        :return: latency
        """
        return self._latency
