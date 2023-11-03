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
from INPsim.Network.Nodes.node import Node
from INPsim.Network.connection import ConstantLatencyConnection


class TestNode(TestCase):

    def test_dist_to_node_chain(self):
        node1 = Node()
        node2 = Node()
        node3 = Node()
        ConstantLatencyConnection.connect_default_bidirectional(node1, node2)
        ConstantLatencyConnection.connect_default_bidirectional(node2, node3)

        # fowards
        self.assertEqual(0, node1.dist_to_node(node1))
        self.assertEqual(1, node1.dist_to_node(node2))
        self.assertEqual(2, node1.dist_to_node(node3))
        # backwards
        self.assertEqual(0, node1.dist_to_node(node1))
        self.assertEqual(1, node2.dist_to_node(node1))
        self.assertEqual(2, node3.dist_to_node(node1))

    def test_dist_to_node_diamond(self):
        node1 = Node()
        node2 = Node()
        node3 = Node()
        node4 = Node()
        ConstantLatencyConnection.connect_default_bidirectional(node1, node2)
        ConstantLatencyConnection.connect_default_bidirectional(node1, node3)
        ConstantLatencyConnection.connect_default_bidirectional(node2, node4)
        ConstantLatencyConnection.connect_default_bidirectional(node3, node4)

        # fowards
        self.assertEqual(1, node1.dist_to_node(node2))
        self.assertEqual(1, node1.dist_to_node(node3))
        self.assertEqual(2, node1.dist_to_node(node4))
        # backwards
        self.assertEqual(1, node4.dist_to_node(node3))
        self.assertEqual(1, node4.dist_to_node(node2))
        self.assertEqual(2, node4.dist_to_node(node1))

    def test_get_nearest_nodes_chain(self):
        node1 = Node()
        node2 = Node()
        node3 = Node()
        ConstantLatencyConnection.connect_default_bidirectional(node1, node2)
        ConstantLatencyConnection.connect_default_bidirectional(node2, node3)
        node1.valid = True
        node2.valid = False
        node3.valid = True

        # without condition
        #   including self
        self.assertEqual([(node1, 0)], node1.get_nearest_nodes(1, True))
        #   not including self
        self.assertEqual([(node2, 1)], node1.get_nearest_nodes(1, False))

        # with condition
        #   including self
        self.assertEqual([(node1, 0)], node1.get_nearest_nodes(
            1, True, lambda node: node.valid))
        #   not including self
        self.assertEqual([(node3, 2)], node1.get_nearest_nodes(
            1, False, lambda node: node.valid))

    def test_get_nearest_nodes_diamond(self):
        node1 = Node()
        node2 = Node()
        node3 = Node()
        node4 = Node()
        ConstantLatencyConnection.connect_default_bidirectional(node1, node2)
        ConstantLatencyConnection.connect_default_bidirectional(node1, node3)
        ConstantLatencyConnection.connect_default_bidirectional(node2, node4)
        ConstantLatencyConnection.connect_default_bidirectional(node3, node4)
        node1.valid = True
        node2.valid = False
        node3.valid = True
        node4.valid = True

        # without condition
        #   including self
        self.assertEqual([(node1, 0)], node1.get_nearest_nodes(1, True))
        self.assertEqual([(node1, 0), (node2, 1), (node3, 1)],
                         node1.get_nearest_nodes(3, True))
        #   not including self
        self.assertEqual([(node2, 1)], node1.get_nearest_nodes(1, False))
        self.assertEqual([(node2, 1), (node3, 1), (node4, 2)],
                         node1.get_nearest_nodes(3, False))

        # with condition
        #   including self
        self.assertEqual([(node1, 0)], node1.get_nearest_nodes(
            1, True, lambda node: node.valid))
        self.assertEqual([(node1, 0), (node3, 1)], node1.get_nearest_nodes(
            2, True, lambda node: node.valid))
        #   not including self
        self.assertEqual([(node3, 1)], node1.get_nearest_nodes(
            1, False, lambda node: node.valid))
        self.assertEqual([(node3, 1), (node4, 2)], node1.get_nearest_nodes(
            2, False, lambda node: node.valid))