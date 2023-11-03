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


from typing import List
from INPsim.Network.Nodes.node import Node
from INPsim.Network.connection import Connection, ConstantLatencyConnection
from INPsim.Network.network import CloudNetwork
from INPsim.Network.Nodes.node import CloudNode, CloudBaseStation
from INPsim.Network.Nodes.cloud import LimitedMemoryCloud
import math
import random
import itertools
from INPsim.vmath import AABB2
import pyproj
import numpy as np
from scipy.spatial import Delaunay


def connect_hierarchical(rng, nodes, ConnectionClass, depth):

    num_iterations = 20

    class Cluster:

        def __init__(self, x, y, content):
            self.x = x
            self.y = y
            self.content = content

    clusters = []
    for node in nodes:
        x, y = node.get_pos()
        clusters.append(Cluster(x, y, node))
    min_x = math.inf
    max_x = -math.inf
    min_y = math.inf
    max_y = -math.inf
    for node in nodes:
        x, y = node.get_pos()
        min_x = min(min_x, x)
        max_x = max(max_x, x)
        min_y = min(min_y, y)
        max_y = max(max_y, y)

    assert min_x < max_x
    assert min_y < max_y

    cluster_size = int(len(nodes)**(1 / depth))
    for d in range(depth):
        # cluster K-means
        new_clusters = [Cluster(rng.uniform(min_x, max_x), rng.uniform(
            min_y, max_y), []) for i in range(cluster_size**(depth - d))]
        for i in range(num_iterations):
            # empty all new clusters
            for new_cluster in new_clusters:
                new_cluster.content = []
            # fill all new clusters again with their nearest clusters
            for cluster in clusters:
                # find nearest new cluster:
                nearest_new_cluster = 0
                nearest_new_cluster_sq_distance = math.inf
                for new_cluster in new_clusters:
                    sq_distance = (new_cluster.x - cluster.x)**2 + \
                        (new_cluster.y - cluster.y)**2
                    if sq_distance < nearest_new_cluster_sq_distance:
                        nearest_new_cluster_sq_distance = sq_distance
                        nearest_new_cluster = new_cluster
                nearest_new_cluster.content.append(cluster)
            # recompute new cluster centers
            for new_cluster in new_clusters:
                if len(new_cluster.content) > 0:
                    avg_x, avg_y = 0, 0
                    for cluster in new_cluster.content:
                        avg_x += cluster.x
                        avg_y += cluster.y
                    new_cluster.x = avg_x / len(new_cluster.content)
                    new_cluster.y = avg_y / len(new_cluster.content)

        # connect withing the new_clusters
        clusters = []
        for new_cluster in new_clusters:
            if len(new_cluster.content) > 0:
                # first find the center-most representative
                centermost_node = None
                centermost_node_sq_distance = math.inf
                for cluster in new_cluster.content:
                    sq_distance = (new_cluster.x - cluster.x) ** 2 + \
                        (new_cluster.y - cluster.y) ** 2
                    if sq_distance < centermost_node_sq_distance:
                        centermost_node_sq_distance = sq_distance
                        centermost_node = cluster.content
                for cluster in new_cluster.content:
                    a = cluster.content
                    b = centermost_node
                    if a != b:
                        a.add_connection(ConnectionClass.create_default(a, b))
                        b.add_connection(ConnectionClass.create_default(b, a))
                # replace list with representative node:
                new_cluster.content = centermost_node
                clusters.append(new_cluster)
        print('level', d, ':', len(clusters), 'clusters')

    # connect the final clusters:
    # first: find the center-most representative
    avg_x, avg_y = 0, 0
    for cluster in clusters:
        avg_x += cluster.x
        avg_y += cluster.y
    avg_x /= len(clusters)
    avg_y /= len(clusters)
    centermost_node = None
    centermost_node_sq_distance = math.inf
    for cluster in clusters:
        sq_distance = (avg_x - cluster.x) ** 2 + (avg_y - cluster.y) ** 2
        if sq_distance < centermost_node_sq_distance:
            centermost_node_sq_distance = sq_distance
            centermost_node = cluster.content
    # second: connect
    for cluster in clusters:
        a = cluster.content
        b = centermost_node
        if a != b:
            a.add_connection(ConnectionClass.create_default(a, b))
            b.add_connection(ConnectionClass.create_default(b, a))

    return centermost_node


def connect_nodes_delaunay(nodes, ConnectionClass):
    points = np.zeros((len(nodes), 2))
    for i, node in enumerate(nodes):
        points[i][0], points[i][1] = node.get_pos()
    delaunay_triangulation = Delaunay(points)
    for triangle in delaunay_triangulation.simplices:
        for i in range(3):
            a = nodes[triangle[i]]
            b = nodes[triangle[(i + 1) % 3]]
            a.add_connection(ConnectionClass.create_default(a, b))
            b.add_connection(ConnectionClass.create_default(b, a))


def connect_nodes_mst(nodes, ConnectionClass):
    points = np.zeros((len(nodes), 2))
    for i, node in enumerate(nodes):
        points[i][0], points[i][1] = node.get_pos()
    delaunay_triangulation = Delaunay(points)
    node_neighbors = dict([(node, set()) for node in nodes])
    for triangle in delaunay_triangulation.simplices:
        for i in range(3):
            a = nodes[triangle[i]]
            b = nodes[triangle[(i + 1) % 3]]
            ax, ay = a.get_pos()
            bx, by = b.get_pos()
            distance = (ax - bx)**2 + (ay - by)**2
            node_neighbors[a].add((b, distance))
            node_neighbors[b].add((a, distance))

    # TODO implement Kruskal
    free_nodes = nodes[1:]
    closed_nodes = nodes[0:1]
    while free_nodes:
        shortest_connection = math.inf
        shortest_connection_closed_node = None
        shortest_connection_free_node = None
        for closedNode, freeNode in itertools.product(closed_nodes,
                                                      free_nodes):
            distance = (closedNode.get_pos()[0] - freeNode.get_pos()[
                0]) ** 2 + (closedNode.get_pos()[1] -
                            freeNode.get_pos()[1]) ** 2
            if distance < shortest_connection:
                shortest_connection = distance
                shortest_connection_closed_node = closedNode
                shortest_connection_free_node = freeNode
        # TODO refactor to a connect(a,b) / connect_bidirectionally(a,b)
        # function taht also avoids duplicate connections
        shortest_connection_closed_node.add_connection(
            ConnectionClass.create_default(
                shortest_connection_closed_node,
                shortest_connection_free_node))
        shortest_connection_free_node.add_connection(
            ConnectionClass.create_default(
                shortest_connection_free_node,
                shortest_connection_closed_node))
        closed_nodes.append(shortest_connection_free_node)
        free_nodes.remove(shortest_connection_free_node)


def connect_nodes_mst_brute_force(nodes, ConnectionClass):
    """
    Builds a minimum spanning tree (MST) (euclidian distances) among a list of CloudNodes.
    :param nodes: a list of CloudNodes to be connected as a MST
    :param ConnectionClass: A Factory for the typ of connection between the nodes.
    :return:
    """
    free_nodes = nodes[1:]
    closed_nodes = nodes[0:1]
    while free_nodes:
        shortest_connection = math.inf
        shortest_connection_closed_node = None
        shortest_connection_free_node = None
        for closedNode, freeNode in itertools.product(closed_nodes,
                                                      free_nodes):
            distance = (closedNode.get_pos()[0] - freeNode.get_pos()[
                0]) ** 2 + (closedNode.get_pos()[1] -
                            freeNode.get_pos()[1]) ** 2
            if distance < shortest_connection:
                shortest_connection = distance
                shortest_connection_closed_node = closedNode
                shortest_connection_free_node = freeNode
        # TODO refactor to a connect(a,b) / connect_bidirectionally(a,b)
        # function that also avoids duplicate connections
        shortest_connection_closed_node.add_connection(
            ConnectionClass.create_default(
                shortest_connection_closed_node,
                shortest_connection_free_node))
        shortest_connection_free_node.add_connection(
            ConnectionClass.create_default(
                shortest_connection_free_node,
                shortest_connection_closed_node))
        closed_nodes.append(shortest_connection_free_node)
        free_nodes.remove(shortest_connection_free_node)


def connect_nodes_knn(nodes, K, ConnectionClass):
    """
    Connects a list of CloudNodes with its K Nearest Neighbors in the euclidian plane.
    :param nodes: the list of CloudNodes in the network
    :param K: the number of neighbors that is to be connected to each node
    :param ConnectionClass: A Factory for the type of connections between the nodes.
    :return:
    """
    for node in nodes:
        knn = []
        for i in range(K + 1):
            closest = None
            closest_sq_dist = math.inf
            for otherNode in nodes:
                if (otherNode is not node) and (otherNode not in knn):
                    sqDist = (node.get_pos()[0] - otherNode.get_pos()[
                        0]) ** 2 + \
                        (node.get_pos()[1] - otherNode.get_pos()[
                            1]) ** 2
                    if sqDist < closest_sq_dist:
                        closest_sq_dist = sqDist
                        closest = otherNode
            knn.append(closest)
            # TODO refactor to a connect(a,b) / connect_bidirectionally(a,b)
            # function that also avoids duplicate connections
            node.add_connection(ConnectionClass.create_default(node, closest))
            closest.add_connection(
                ConnectionClass.create_default(
                    closest, node))


def generate_random_cloud_network(
        aabb,
        num_base_stations,
        num_internal_nodes,
        num_clouds,
        random_seed):
    """
    Creates a random Network.
    :param aabb: physical scale of the network (defined by a aabb)
    :param num_base_stations: number of base stations
    :param num_internal_nodes: number of internal nodes
    :param num_clouds: number of clouds
    :param random_seed: random seed for the generation of the network
    :return: CloudNetwork
    """
    width = aabb.width()
    height = aabb.height()
    offset_x = aabb.min_x
    offset_y = aabb.min_y

    rng = random.Random(random_seed)
    base_stations = [
        CloudBaseStation(
            pos=(
                rng.uniform(
                    0,
                    width) +
                offset_x,
                rng.uniform(
                    0,
                    height) +
                offset_y)) for x in range(num_base_stations)]
    nodes: List[Node] = []
    nodes = base_stations + [
        CloudNode(
            pos=(
                rng.uniform(
                    0,
                    width) + offset_x,
                rng.uniform(
                    0,
                    height) + offset_y)) for x in range(num_internal_nodes)]
    connect_nodes_mst(nodes, Connection)
    connect_nodes_knn(nodes, 3, Connection)
    clouds = []

    # make sure that each node has at most one cloud
    cloud_memory_capacity = 3  # TODO don't hardcode
    for ci in range(min(num_clouds, len(nodes))):
        while True:
            node = nodes[rng.randint(0, len(nodes) - 1)]
            if not node.get_cloud():
                cloud = LimitedMemoryCloud(
                    node=node, memory_capacity=cloud_memory_capacity)
                clouds.append(cloud)
                node.set_cloud(cloud)
                break
    return CloudNetwork(nodes)


def generate_san_francisco_cloud_network(
        topology: str,
        num_clouds,
        cloudlet_memory_capacity,
        cloud_memory_capacity,
        random_seed):
    """
    Creates a network from the base stations in san francisco.
    :param topology: one of 'delaunay','2-tier-hierarchical'
    :param aabb: physical scale of the network (defined by a aabb)
    :param num_base_stations: number of base stations
    :param num_internal_nodes: number of internal nodes
    :param num_clouds: number of clouds
    :param random_seed: random seed for the generation of the network
    :return: CloudNetwork
    """
    aabb = AABB2(
        542688.443644256,
        556765.7262020159,
        4161556.7164416737,
        4185052.3668366373)
    width = aabb.width()
    height = aabb.height()
    offset_x = aabb.min_x
    offset_y = aabb.min_y

    rng = random.Random(random_seed)

    #base_stations = [CloudBaseStation(pos=(rng.uniform(0,width)+offset_x,rng.uniform(0,height)+offset_y)) for x in range(num_base_stations)]
    # the UTM zone (san francisco in this case) is needed to accurately
    # convert longitude and latitude to meters, acting as a reference point
    # for the planar projection
    utm_zone = "10"
    utm_san_francisco = pyproj.Proj("+proj=utm +zone=" + utm_zone +" +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs")
    #utm_san_francisco = pyproj.Proj(proj='utm', zone=utm_zone, ellps='WGS84', datum='WGS84', units='m')

    base_stations = []
    print('loading network...')
    with open('Datasets/openCellId/cell_towers_san_francisco.csv') as file:
        first_line = file.readline()
        for line in file:
            radio, mcc, net, area, cell, unit, lon, lat, rrange, samples, changeable, created, updated, average_signal = line.split(
                ',')
            mcc, net, area, cell, unit, rrange, samples, changeable, created, updated, average_signal = [int(
                x) for x in [mcc, net, area, cell, unit, rrange, samples, changeable, created, updated, average_signal]]
            lon, lat = float(lon), float(lat)

            x, y = utm_san_francisco(lon, lat)
            base_stations.append(CloudBaseStation(pos=(x, y)))

    print('network loaded. Connecting...')

    # testing the accelerated RAN-model. right now, it should always find itself
    # TODO(1) give it a blacklist to never find itself
    # TODO(2) make it find the KNN
    # ranModel = NearestNeighborRANModel(base_stations,200)
    # for bs_a in base_stations:
    #     foo = ranModel.get_closest_base_station(bs_a.get_pos(),[bs_a])
    #     #print('found itself:',foo is bs_a)

    nodes = []
    central_cloud_node = CloudNode(pos=(563011, 4184184))
    # + [CloudNode(pos=(rng.uniform(0, width)+offset_x, rng.uniform(0, height)+offset_y)) for x in range(num_internal_nodes)]
    nodes = base_stations + [central_cloud_node]

    if topology == 'delaunay':
        print('connecting delaunay')
        connect_nodes_delaunay(nodes, Connection)
    elif topology == '2-tier-hierarchical':
        print('connecting 2-tier-hierarchical')
        centermost_node = connect_hierarchical(rng, nodes, Connection, 2)
        central_cloud_distance = 10
        centermost_node.add_connection(
            ConstantLatencyConnection(
                centermost_node,
                central_cloud_node,
                central_cloud_distance))
        central_cloud_node.add_connection(
            ConstantLatencyConnection(
                central_cloud_node,
                centermost_node,
                central_cloud_distance))
    else:
        raise Exception(
            'Topology ' +
            str(topology) +
            ' is not a valid argument.')

    clouds = []

    central_cloud = LimitedMemoryCloud(
        node=central_cloud_node,
        memory_capacity=cloud_memory_capacity)
    clouds.append(central_cloud)
    central_cloud_node.set_cloud(central_cloud)

    # make sure that each node has at most one cloud
    for ci in range(min(num_clouds, len(nodes))):
        while True:
            node = nodes[rng.randint(0, len(nodes) - 1)]
            if not node.get_cloud():
                # if ci == 0:
                #     if topology == '2-tier-hierarchical':
                #         node = centermost_node #force the central cloud to be the center node, if hierarchically connected
                #     cloud = LimitedMemoryCloud(node=node, memory_capacity=cloud_memory_capacity)
                #     central_cloud = cloud
                # else:
                cloud = LimitedMemoryCloud(
                    node=node, memory_capacity=cloudlet_memory_capacity)

                clouds.append(cloud)
                node.set_cloud(cloud)
                break

    print('network loaded and connected')

    return CloudNetwork(nodes, central_cloud=central_cloud)
