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


class Node:
    """
    This is a base class for Nodes in a network.
    It provides access to basic graph operations.
    """

    def __init__(self):
        """
        Constructs a new Node obj.
        """
        self._outgoing_connections = []

    def add_connection(self, connection):
        """
        Adds a directional outgoing connection to the node.
        :param connection: a Connection where src is this node and dst is another node.
        """
        assert connection.src() is self
        assert connection.dst() is not self
        # don't duplicate connections:
        if connection not in self._outgoing_connections:
            self._outgoing_connections.append(connection)
        else:
            print('deleting a duplicate connection')

    def get_connections(self):
        """
        Returns the list of outgoing connections from this node.
        :return: list of all outgoing connections
        """
        return self._outgoing_connections

    def get_neighbor_nodes(self):
        """
        Returns a generator that iterates over the destination nodes of all outgoing connections
        :return:
        """
        for connection in self._outgoing_connections:
            yield connection.dst()


class CloudNode(Node):
    """
    Implements a Node that can own a cloud and has an optional postion.
    """

    def __init__(self, pos=None):
        """
        Initializes the CloudNode with no cloud and an optional position.
        :param pos: A 2-tuple of numbers for a cartesian position. None, if there is no specified position.
        """
        super(CloudNode, self).__init__()
        self.pos = pos
        self.cloud = None

    def get_cloud(self):
        return self.cloud

    def set_cloud(self, cloud):
        self.cloud = cloud

    def get_pos(self):
        return self.pos


class CloudBaseStation(CloudNode):
    """
    Implements a base station that can accommodate a cloud.
    """

    def __init__(self, pos):
        """
        Initializes the CloudBaseStation.
        :param pos: A 2-tuple of numbers for a cartesian position. None, if there is no specified position.
        """
        super(CloudBaseStation, self).__init__(pos)

    def access_point_latency(self):
        """
        Returns the latency of wireless access ath this base station. Always 1 for now.
        :return: 1
        """
        return 1
