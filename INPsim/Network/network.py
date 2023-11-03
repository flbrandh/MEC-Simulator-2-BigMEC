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


from INPsim.Network.Nodes.node import CloudBaseStation
from INPsim.vmath import AABB2
import math

from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import floyd_warshall


class Network:
    """
    Encapsulates a Network, consisting of nodes and connections.
    This class must be treated as immutable. #TODO change this through refactoring?
    """

    def __init__(self, nodes):
        """
        Constructs a network with a set of connected Nodes.
        :param nodes: already finally connected set of Nodes
        """
        self.__nodes = nodes
        #self.__node_dist_cache = dict([(node, LRU(20)) for node in self.__nodes])
        #self.__node_dist_cache = dict([(node, LRU(len(self.__nodes))) for node in self.__nodes])

        self._node_ids = dict([(node, i)
                               for i, node in enumerate(self.__nodes)])

        graph = []
        for i in range(len(self.__nodes)):
            row = [0] * len(self.__nodes)
            connections = self.__nodes[i].get_connections()
            for connection in connections:
                idx = self._node_ids[connection.dst()]
                row[idx] = connection.weight()
            graph.append(row)
        csr_graph = csr_matrix(graph)
        self._dist_matrix = floyd_warshall(csgraph=csr_graph, directed=False)

    def __getstate__(self):
        """
        For pickling.
        :return:
        """
        state = self.__dict__.copy()
        return state

    def __setstate__(self, newstate):
        """
        For unpickling.
        :param newstate:
        :return:
        """
        self.__dict__.update(newstate)
        self.__dict__.update(newstate)

    def nodes(self):
        """
        Returns the list of all nodes of the network.
        :return:
        """
        return self.__nodes

    def dist_to_node(self, src_node, target_node, fallback_value=math.inf):
        i_src = self._node_ids[src_node]
        i_target = self._node_ids[target_node]
        return self._dist_matrix[i_src][i_target]

    def __calculate_dist_to_node(
            self,
            src_node,
            target_node,
            fallback_value=math.inf):
        """
        Determines the shortest distance to another Node.
        The distance is the sum of the Connection weights.
        :param target_node: The Node to which the distance should be computed.
        :param fallback_value: Value that is returned when no path exists. The default is math.inf.
        :return: The distance to the node in question. If no path exists, fallback_value is returned.
        """
        # dijkstra's algorithm:
        fringe = set()
        closed = set()
        shortest_distances = {}

        fringe.add(src_node)
        shortest_distances[src_node] = 0

        while fringe:
            next_node = None
            lowest_dist_in_fringe = math.inf
            # find closest node in fringe
            for node in fringe:
                d = shortest_distances[node]
                if d < lowest_dist_in_fringe:
                    lowest_dist_in_fringe = d
                    next_node = node
            # remove the closest node from the fringe and add it to the closed
            # nodes
            fringe.remove(next_node)
            dist_to_next_node = shortest_distances[next_node]
            if next_node is target_node:
                return dist_to_next_node
            closed.add(next_node)
            for connection in next_node.get_connections():
                neighbor = connection.dst()
                connection_weight = connection.weight()
                if neighbor not in closed:
                    if neighbor not in shortest_distances:
                        shortest_distances[neighbor] = dist_to_next_node + \
                            connection_weight
                    elif dist_to_next_node + connection_weight < shortest_distances[neighbor]:
                        shortest_distances[neighbor] = dist_to_next_node + \
                            connection_weight
                    if neighbor not in fringe:
                        fringe.add(neighbor)
        return fallback_value

    def get_nearest_nodes(
            self,
            src_node,
            k,
            include_src_node=False,
            node_filter=lambda node: True):
        """
        Returns the k nearest nodes from src.
        :param k: number of nearest nodes t be searched
        :param include_src_node: True, if the returned nodes should include the src-node. False, if only other nodes should be considered
        :param node_filter: a function that can filter the searched nodes, e.g. to exclude non-cloud nodes. It returns True for valid nodes and False for invalid ones
        :return: list of tuples (node, distance)
        """
        if k == 0:
            return []
        knn_nodes = []
        # djikstra's algorithm until knn_nodes are found
        fringe = set()
        closed = set()
        shortest_distances = {}

        fringe.add(src_node)
        shortest_distances[src_node] = 0

        while fringe:
            next_node = None
            lowest_dist_in_fringe = math.inf
            # find closest node in fringe
            for node in fringe:
                d = shortest_distances[node]
                if d < lowest_dist_in_fringe:
                    lowest_dist_in_fringe = d
                    next_node = node
            # remove the closest node from the fringe and add it to the closed
            # nodes
            fringe.remove(next_node)
            dist_to_next_node = shortest_distances[next_node]
            # collect node and return if enough clouds are collected
            if (include_src_node or ((not include_src_node)
                                     and src_node is not next_node)) and node_filter(next_node):
                knn_nodes.append(next_node)
                if len(knn_nodes) is k:
                    # established
                    if include_src_node:
                        if node_filter(
                                src_node):  # only include he node itself, if it passes the filte, of couse
                            assert src_node in knn_nodes
                    else:
                        assert src_node not in knn_nodes
                    return [(node, shortest_distances[node])
                            for node in knn_nodes]
            closed.add(next_node)
            for neighbor in next_node.get_neighbor_nodes():
                if neighbor not in closed:
                    if neighbor not in shortest_distances:
                        shortest_distances[
                            neighbor] = dist_to_next_node + 1
                    elif dist_to_next_node + 1 < shortest_distances[neighbor]:
                        shortest_distances[
                            neighbor] = dist_to_next_node + 1
                    if neighbor not in fringe:
                        fringe.add(neighbor)
        # in this case, the returned number of nodes is lower than k
        return [(node, shortest_distances[node]) for node in knn_nodes]


class CloudNetwork(Network):
    """
    Encapsulates a network with connected CloudNodes that can own a cloud.
    This class must be treated as immutable.
    """

    def __init__(self, cloud_nodes, central_cloud=None):
        """
        Initializes a Network of nodes that are already interconnected and assigned to clouds.
        :param cloud_nodes: the set of nodes with their clouds assigned.
        :param central_cloud: one of the clouds within the network that is the designated central cloud, where all services are to be created and which has  practically unlimited capacity.
        """
        super(CloudNetwork, self).__init__(cloud_nodes)
        self.__clouds = self.__collect_clouds(cloud_nodes)
        self.__central_cloud = central_cloud
        self.__base_stations = self.__collect_base_stations(cloud_nodes)

    def clouds(self):
        """
        Returns all clouds of the CloudNetwork.
        :return: All clouds that are in th CloudNetwork
        """
        return self.__clouds

    def central_cloud(self):
        return self.__central_cloud

    def aabb(self):

        min_x = min_y = math.inf
        max_x = max_y = -math.inf
        for node in self.nodes():
            x, y = node.get_pos()
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)

        return AABB2(min_x, max_x, min_y, max_y)

    def base_stations(self):
        """
        Returns the set of all base stations in the network.
        :return:
        """
        return self.__base_stations

    def __collect_clouds(self, cloud_nodes):
        """
        Collects all clouds from a set of nodes.
        :param cloud_nodes: A set of CloudNodes from which to collect the clouds.
        :return: The list of all clouds in cloud_nodes.
        """
        clouds = []
        for cloud_node in cloud_nodes:
            if cloud_node.get_cloud():
                clouds.append(cloud_node.get_cloud())
        return clouds

    def __collect_base_stations(self, cloud_nodes):
        """
        Collects all clouds from a set of nodes.
        :param cloud_nodes: A set of CloudNodes from which to collect the clouds.
        :return: The list of all base stations in cloud_nodes
        """
        base_stations = []
        for cloud_node in cloud_nodes:
            if isinstance(cloud_node, CloudBaseStation):
                base_stations.append(cloud_node)
        return base_stations

    def get_nearest_clouds(
            self,
            src_node,
            k,
            cloud_filter=lambda cloud: True,
            include_src_node=True):
        """
        :param node: the node from which to search for the closest cloud, including this node
        :return: a list of tuples of the k closest clouds and their distances
        """

        closest_cloud_node_tuples = self.get_nearest_nodes(
            src_node,
            k=k,
            include_src_node=include_src_node,
            node_filter=lambda node: node.get_cloud() is not None and cloud_filter(
                node.get_cloud()))  # filter away all nodes without clouds
        return [(node.get_cloud(), distance)
                for node, distance in closest_cloud_node_tuples]