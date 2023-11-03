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


from typing import List, Optional, Tuple
import numpy as np  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from matplotlib.offsetbox import OffsetImage, AnnotationBbox  # type:ignore
from INPsim.Simulation import SimulationInterface, StatisticsSimulationObserver
from INPsim.Network.Nodes.node import CloudBaseStation
from INPsim.Network.User.user import User
from INPsim.vmath import AABB2
from INPsim.ServicePlacement.Migration.Learning.learn import DQNMigrationAlgorithm
from INPsim.ServicePlacement.Migration.Algorithms import MigrationAlgorithmServicePlacementStrategy
import pygame  # type: ignore
import pygame.gfxdraw  # type: ignore
import math
import os
from datetime import datetime
from pytz import timezone

package_directory: str = os.path.dirname(os.path.abspath(__file__))


def package_relative_path(path: str) -> str:
    return os.path.join(package_directory, path)


class SimPlotStats:
    def __init__(self, title) -> None:
        self.title = title
        self.fig, self.axGraph = plt.subplots(1, 1)
        self.fig.canvas.manager.set_window_title(title)
        plt.ion()
        self.fig.show()
        self.fig.canvas.draw()

    def plot(self, sim: SimulationInterface, stats: StatisticsSimulationObserver) -> None:
        self.plot_statistics(sim, stats, self.fig, self.axGraph)

    def chunks_avg(self, l: List[float], n: int) -> List[float]:
        out: List[float] = []
        for i in range(0, len(l), n):
            out.append(sum(l[i:i + n]) / len(l[i:i + n]))
        return out

    def chunks_avg_zero_filtered(self, l: List[float], n: int) -> List[float]:
        out: List[float] = []
        for i in range(0, len(l), n):
            filtered = [x for x in l[i:i + n] if not x == 0]
            if len(filtered) == 0:
                out.append(0.0)
            else:
                out.append(sum(filtered) / len(filtered))
        return out

    def plot_statistics(
            self,
            sim: SimulationInterface,
            stats: StatisticsSimulationObserver,
            fig: plt.Figure,
            ax: plt.Axes) -> None:
        ax.clear()
        plt.sca(ax)

        avgInterval = 1
        #plt.plot(self.chunksAvg(stats.cost,avgInterval), 'r-', label='cost')
        #plt.plot(stats.inactiveRate, 'g.', label='inact. rate')
        #plt.plot(self.chunksAvg(stats.dissatisfactionRate,avgInterval),'b:', label='dissat. rate')
        # plt.plot(self.chunksAvg([m / 20 for m in stats.num_proposed_migrations],avgInterval), 'yP', label='# proposed migrations/20')
        # plt.plot(self.chunksAvg([m / 20 for m in stats.num_migrations],avgInterval), 'k+', label='# migrations/20')
        # plt.plot(self.chunksAvgZeroFiltered(stats.avg_migration_dist_to_user_bs,avgInterval), 'm*', label='avg. dist. after mig.')
        plt.plot(
            self.chunks_avg_zero_filtered(
                [10 * m for m in stats.avg_latency],
                avgInterval),
            color='g',
            linestyle='-',
            linewidth=1,
            label='avg. latency x10')
        plt.plot(
            self.chunks_avg_zero_filtered(
                [
                    m for m in stats.global_cost],
                avgInterval),
            color='r',
            linestyle='-',
            linewidth=1,
            label='global cost')
        #plt.plot(self.chunksAvgZeroFiltered([m for m in stats.avg_latency_lower_bound], avgInterval), color='k', linestyle='-', linewidth=1, label='avg. latency (lower bound)')

        #plt.plot([m/20 for m in stats.num_migration_events], 'g-', label='migration events/20')
        #plt.plot([a/b for a,b in zip(stats.num_proposed_migrations,stats.num_migration_events)], 'k-',  label='migration ratio')

        #ax.set_xlim(0, 1000)
        #ax.set_ylim(0, 1.1)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.2), ncol=5)
        ax.grid(color='y', linestyle=':')

        fig.canvas.draw()
        plt.pause(1e-7)


class SimPlotLearning(SimPlotStats):

    def __init__(self, title: str) -> None:
        self.title = title
        self.fig, [[self.axSimStatsGraph, self.axLearnStatsGraph],
                   [self.axLossGraph, self.axQs]] = plt.subplots(2, 2)
        self.fig.canvas.manager.set_window_title(title)
        plt.ion()
        self.fig.show()
        self.fig.canvas.draw()

    def plot(self, sim: SimulationInterface, stats: StatisticsSimulationObserver) -> None:
        sp_strategy = sim.get_service_placement_strategy()
        if isinstance(sp_strategy, MigrationAlgorithmServicePlacementStrategy):
            migration_algorithm = sp_strategy.get_migration_algorithm()
            if isinstance(migration_algorithm, DQNMigrationAlgorithm):
                learner: DQNMigrationAlgorithm = migration_algorithm
                self.plot_learning(learner, self.fig, self.axLearnStatsGraph)
                self.plot_loss(learner, self.fig, self.axLossGraph)
                self.plot_Qs(learner, self.fig, self.axQs)
                self.plot_statistics(sim, stats, self.fig, self.axSimStatsGraph)
                #self.fig.savefig("lastplot.pdf", bbox_inches='tight')

    def plot_learning(
            self,
            learner: DQNMigrationAlgorithm,
            fig: plt.Figure,
            ax: plt.Axes) -> None:
        ax.clear()
        plt.sca(ax)

        plt.plot(
            learner.shared_agent.avg_rewards,
            color='b',
            linestyle='-',
            linewidth=1,
            label='average rewards')

        # if hasattr(learner, 'maxRewards'):
        #    plt.plot(learner.maxRewards, 'g-',
        #             label='maximum reward')
        # if hasattr(learner, 'minRewards'):
        #    plt.plot(learner.minRewards, 'r-',
        #             label='minimum reward')

        #ax.set_xlim(0, 1000)
        #ax.set_ylim(0, 1.1)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=3)
        ax.grid(color='r', linestyle=':')

        # fig.canvas.draw()
        # plt.pause(1e-7)

    def plot_loss(
            self,
            learner: DQNMigrationAlgorithm,
            fig: plt.Figure,
            ax: plt.Axes) -> None:
        ax.clear()
        plt.sca(ax)

        if hasattr(learner.shared_agent, 'losses'):
            plt.plot(
                learner.shared_agent.losses,
                color='r',
                linestyle='-',
                linewidth=1,
                label='episode Q-loss')

        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=3)
        ax.grid(color='r', linestyle=':')
        ax.set_yscale("log")

    def plot_Qs(
            self,
            learner: DQNMigrationAlgorithm,
            fig: plt.Figure,
            ax: plt.Axes) -> None:
        ax.clear()
        plt.sca(ax)

        if hasattr(learner.shared_agent, 'predicted_Qs'):
            plt.plot(
                learner.shared_agent.predicted_Qs,
                color='g',
                linestyle='-',
                linewidth=1,
                label='predicted_Qs')

        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=3)
        ax.grid(color='r', linestyle=':')



# class SimPlot(SimPlotStats):
#     def __init__(self) -> None:
#         self.fig, [self.axNetwork, self.axGraph] = plt.subplots(1, 2)
#         plt.ion()
#         self.fig.show()
#         self.fig.canvas.draw()
#
#     def plot(self, configured_simulation : Simulation) -> None:
#         self.plotSimulation(configured_simulation, self.fig, self.axNetwork)
#         self.plotStatistics(configured_simulation, self.fig, self.axGraph)
#
#     def plotSimulation(self, configured_simulation : Simulation, fig : plt.Figure, ax : plt.Axes) -> None:
#         clouds = configured_simulation.get_clouds()
#         users = configured_simulation.get_users()
#         nodes = configured_simulation.get_nodes()
#
#         ax.clear()
#
#         scale = 1
#         ax.set_aspect('equal')
#         #ax.autoscale(False)
#
#         #plot connections between nodes
#         for node in nodes:
#             x1, y1 = node.get_pos()
#             for neighbor in node.getNeighbors():
#                 x2, y2 = neighbor.get_pos()
#                 ax.plot([x1,x2],[y1,y2],'b')
#
#
#         #plot connections to base stations
#         for user in users:
#             x1, y1 = user.get_pos()
#             x2, y2 = user.get_base_station().get_pos()
#             ax.plot([x1,x2],[y1,y2],'g')
#
#         # plot internal nodes
#         x = [node.get_pos()[0] for node in nodes if not isinstance(node, CloudBaseStation)]
#         y = [node.get_pos()[1] for node in nodes if not isinstance(node, CloudBaseStation)]
#
#         cloud_image_path = 'in.png'
#         self.imscatter(x, y, cloud_image_path, zoom=0.2 * scale, ax=ax)
#
#         # plot base stations
#         x = [node.get_pos()[0] for node in nodes if
#              isinstance(node, CloudBaseStation)]
#         y = [node.get_pos()[1] for node in nodes if
#              isinstance(node, CloudBaseStation)]
#
#         cloud_image_path = 'bs.png'
#         self.imscatter(x, y, cloud_image_path, zoom=0.2 * scale, ax=ax)
#
#         # plot clouds
#         x = [cloud.get_pos()[0] for cloud in clouds]
#         y = [cloud.get_pos()[1] for cloud in clouds]
#
#         cloud_image_path = 'ec.png'
#         self.imscatter(x, y, cloud_image_path, zoom=0.2*scale, ax=ax)
#
#
#         # plot users
#         x = [user.get_pos()[0] for user in users]
#         y = [user.get_pos()[1] for user in users]
#         cloud_image_path = 'ue.png'
#         self.imscatter(x, y, cloud_image_path, zoom=0.2*scale, ax=ax)
#
#         #print cloud utilization
#         for cloud in clouds:
#             ax.text(cloud.get_pos()[0], cloud.get_pos()[1] + 0.05, '{0:.2f}'.format((cloud.totalMemoryRequirement() / cloud.memoryCapacity) * 100) + "%", color='k', bbox=dict(boxstyle="round",
#                                                                                                                                                                                ec=(1., 0.5, 0.5),
#                                                                                                                                                                                fc=(1., 0.8, 0.8),
#                                                                                                                                                                                ))
#
#         ax.set_xlim(-0.1, 1.1)
#         ax.set_ylim(-0.1, 1.1)
#
#         fig.canvas.draw()
#         plt.pause(1e-7)
#         #plt.draw()
#         #plt.show()
#
#     def imscatter(self, x : , y, image, ax=None, zoom=1):
#         if ax is None:
#             ax = plt.gca()
#         try:
#             image = plt.imread(image)
#         except TypeError:
#             # Likely already an array...
#             pass
#         im = OffsetImage(image, zoom=zoom, interpolation='bicubic')
#         x, y = np.atleast_1d(x, y)
#         artists = []
#         for x0, y0 in zip(x, y):
#             ab = AnnotationBbox(im, (x0, y0), xycoords='data', frameon=False)
#             artists.append(ax.add_artist(ab))
#         ax.update_datalim(np.column_stack([x, y]))
#         ax.autoscale()
#         return artists


class SimPlotPygame:

    def __init__(
            self,
            sim: SimulationInterface,
            bg_filename: Optional[str] = None,
            bg_aabb: Optional[AABB2] = None,
            title="pygame") -> None:
        #self.n = 0
        #print("initializing Pygame thread")
        pygame.init()
        pygame.display.set_caption(title)
        self.screen = pygame.display.set_mode((1000, 1000))
        self.static_background = pygame.Surface((1000, 1000))
        self.last_origin_cam_coordinates = (0.0, 0.0)
        self.drag = False
        self.mouse_pos = (0, 0)
        self.quit = False

        icon_size = 16

        self.imgEC = pygame.transform.smoothscale(
            pygame.image.load(
                package_relative_path('gfx/ec.png')),
            (icon_size,
             icon_size),
            pygame.Surface(
                (icon_size,
                 icon_size),
                pygame.SRCALPHA))
        self.imgBS = pygame.transform.smoothscale(
            pygame.image.load(
                package_relative_path('gfx/bs.png')),
            (icon_size,
             icon_size),
            pygame.Surface(
                (icon_size,
                 icon_size),
                pygame.SRCALPHA))
        self.imgIN = pygame.transform.smoothscale(
            pygame.image.load(
                package_relative_path('gfx/in.png')),
            (icon_size,
             icon_size),
            pygame.Surface(
                (icon_size,
                 icon_size),
                pygame.SRCALPHA))
        self.imgUE = pygame.transform.smoothscale(
            pygame.image.load(
                package_relative_path('gfx/ue.png')),
            (icon_size,
             icon_size),
            pygame.Surface(
                (icon_size,
                 icon_size),
                pygame.SRCALPHA))

        self.bg_image = None
        self.bg_aabb = bg_aabb
        if bg_filename:
            assert(bg_aabb)
            self.bg_image = pygame.image.load(package_relative_path(bg_filename))

        network_aabb = sim.get_cloud_network().aabb()
        max_dimension_scale = max(network_aabb.width(), network_aabb.height())
        center = network_aabb.center()
        self.scale = 800 / max_dimension_scale
        self.offset = (-network_aabb.min_x,
                       network_aabb.min_y + 1000 / self.scale)  # (0.1,0.1)

        pygame.font.init()
        self.subscript_font = pygame.font.SysFont(
            package_relative_path('font/FreeSans.ttf'), 18)
        self.caption_font = pygame.font.SysFont(
            package_relative_path('font/FreeSans.ttf'), 40)

        self.display_histogram = False
        self.display_cloud_neighborhood = False
        self.display_cloud_services = False
        self.selected_cloud = 0
        self.display_service_cloud = True
        self.selected_service = 0

    def world_coords_to_cam_coords(self,
                              world_coords: Tuple[float,
                                                  float],
                              constant_offset: Tuple[float,
                                                     float] = (0,
                                                               0)) -> Tuple[float,
                                                                            float]:
        cam_coords = (int(self.scale * (world_coords[0] + self.offset[0]) +
                         constant_offset[0]),
                     int(self.scale * (-world_coords[1] + self.offset[1]) +
                         constant_offset[1]))
        return cam_coords

    def draw_image(self,
                   image: pygame.Surface,
                   world_coords: Tuple[float, float],
                   centered: bool = True,
                   constant_offset: Tuple[float, float] = (0, 0),
                   surface: Optional[pygame.Surface] = None) -> None:
        if not surface:
            surface = self.screen
        cam_coords = self.world_coords_to_cam_coords(world_coords, constant_offset)
        if centered:
            cam_coords = (
                cam_coords[0] -
                0.5 *
                image.get_rect().size[0],
                cam_coords[1] -
                0.5 *
                image.get_rect().size[1])
        surface.blit(image, cam_coords)

    def draw_world_space_circle(self,
                                radius: float,
                                color: pygame.Color,
                                worldCoords: Tuple[float, float],
                                constantOffset: Tuple[float, float] = (0, 0)) -> None:
        # TODO fix this function!
        pass
        """
        cam_coords = self.worldCoords2CamCoords(worldCoords,constantOffset)
        radius = radius*self.scale
        pygame.gfxdraw.aacircle(self.screen, cam_coords[0],cam_coords[1], int(radius), color)
        pygame.gfxdraw.aacircle(self.screen, cam_coords[0],
                                cam_coords[1], int(radius)-1, color)
        pygame.gfxdraw.aacircle(self.screen, cam_coords[0],
                                cam_coords[1], int(radius)-2, color)
        pygame.gfxdraw.aacircle(self.screen, cam_coords[0],
                                cam_coords[1], int(radius) - 3, color)
        """

    def draw_world_space_line(self,
                              world_coords_start: Tuple[float, float],
                              world_coords_end: Tuple[float, float],
                              color: pygame.Color,
                              width: int = 1,
                              surface: Optional[pygame.Surface] = None) -> None:
        if not surface:
            surface = self.screen
        cam_coords_start = self.world_coords_to_cam_coords(world_coords_start)
        cam_coords_end = self.world_coords_to_cam_coords(world_coords_end)
        pygame.draw.lines(surface, color, False,[cam_coords_start, cam_coords_end], width)
        #pygame.draw.aalines(surface, color, False,[cam_coords_start, cam_coords_end])

    def draw_transparent_box(self,
                             w: int,
                             h: int,
                             x: int,
                             y: int,
                             alpha: float,
                             color: pygame.Color) -> None:

        s = pygame.Surface((w, h))  # the size of your rect
        s.set_alpha(alpha)  # alpha level
        s.fill(color)  # this fills the entire surface
        self.screen.blit(s, (
            x, y))  # (0,0) are the top-left coordinates

    def draw_histogram(self,
                       bins: List[int],
                       labels: List[str],
                       scale: float,
                       caption: str,
                       print_bins: bool) -> None:

        axis_color = (0, 0, 0)
        background_color = (200, 200, 200)
        bar_color = (200, 0, 0)
        background_alpha = 230
        offset_y = 500
        offset_x = 30
        width = 800
        height = 400

        font_height = self.subscript_font.get_height()

        self.draw_transparent_box(
            width + 10,
            height + 10 + font_height,
            offset_x - 10,
            offset_y - height,
            background_alpha,
            background_color)

        num_bins = len(bins)
        for num, (bin, label) in enumerate(zip(bins, labels)):
            bin_w = width / num_bins
            bin_h = height * (bin / scale)
            bin_x_start = (width / num_bins) * num
            pygame.draw.rect(
                self.screen,
                bar_color,
                (offset_x + bin_x_start + 1,
                 offset_y - bin_h,
                 bin_w - 1,
                 math.ceil(bin_h)))
            bin_x_center = offset_x + bin_x_start + bin_w * 0.5
            if print_bins:
                text = self.subscript_font.render(str(bin), True, axis_color)
                label_w, label_h = text.get_size()
                self.screen.blit(text, (
                    bin_x_center - label_w * 0.5, offset_y - 12))
            if label:
                pygame.draw.lines(self.screen, axis_color, False,
                                  [(bin_x_center, offset_y + 10),
                                   (bin_x_center, offset_y)], 2)
                text = self.subscript_font.render(label, True, axis_color)
                label_w, label_h = text.get_size()
                self.screen.blit(
                    text, (bin_x_center - label_w * 0.5, offset_y + 10))

        pygame.draw.lines(self.screen, axis_color, False,
                          [(offset_x - 10, offset_y),
                           (offset_x + width, offset_y)], 2)
        pygame.draw.lines(self.screen, axis_color, False,
                          [(offset_x, offset_y + 10),
                           (offset_x, offset_y - height)], 2)

        img_caption = self.caption_font.render(caption, True, axis_color)
        caption_w, caption_h = img_caption.get_size()
        self.screen.blit(
            img_caption,
            (offset_x +
             width *
             0.5 -
             caption_w *
             0.5,
             offset_y -
             height))

        pygame.draw.rect(
            self.screen,
            axis_color,
            (offset_x - 10,
             offset_y - height,
             width + 10,
             height + 10 + font_height),
            True)

    def draw_cloud_neighborhood(self, sim: SimulationInterface) -> None:
        clouds = sim.get_cloud_network().clouds()
        cloud = clouds[self.selected_cloud % len(clouds)]
        get_neigbor_clouds = getattr(
            cloud.get_migration_algorithm_instance(),
            "get_neighbor_clouds",
            None)
        if callable(get_neigbor_clouds):
            neighbor_clouds = cloud.get_migration_algorithm_instance().get_neighbor_clouds()
            for neighbor_cloud in neighbor_clouds:
                self.draw_world_space_circle(
                    0.05, (255, 0, 0), neighbor_cloud.get_pos(), constantOffset=(
                        32, 32))

    def draw_cloud_services(self, sim: SimulationInterface) -> None:
        clouds = sim.get_cloud_network().clouds()
        cloud = clouds[self.selected_cloud % len(clouds)]
        for service in cloud.services():
            pos = service.owner().get_base_station().get_pos()
            self.draw_world_space_circle(0.05, (50, 100, 50), pos)

    def draw_cloud_annotations(self, sim: SimulationInterface) -> None:
        # mark the seected cloud
        if self.display_cloud_neighborhood or self.display_cloud_services:
            clouds = sim.get_cloud_network().clouds()
            cloud = clouds[self.selected_cloud % len(clouds)]
            self.draw_world_space_circle(
                0.05, (200, 0, 155), cloud.get_pos(), constantOffset=(
                    32, 32))

        if self.display_cloud_neighborhood:
            self.draw_cloud_neighborhood(sim)
        if self.display_cloud_services:
            self.draw_cloud_services(sim)

    def draw_service_annotations(self, sim: SimulationInterface) -> None:
        num_services = sim.get_num_services()
        if self.display_service_cloud and num_services > 0:
            services = list(sim.get_services())
            service = services[self.selected_service % num_services]
            service_owner = service.owner()
            if isinstance(service_owner, User):
                self.draw_world_space_circle(.05, (255, 0, 0), service_owner.get_movement_model().get_pos())
                self.draw_world_space_circle(.05, (0, 255, 0), service_owner.get_base_station().get_pos())
                self.draw_world_space_circle(.05, (255, 255, 0), service.get_cloud().get_pos(), constantOffset=(32, 32))

    def draw_multiline_text(self,
                            str: str,
                            font: pygame.font.Font,
                            x: int, y: int,
                            color: Tuple[int, int, int] = (0, 0, 0)) -> None:
        strs = str.split('\n')
        offset_y = y
        for str in strs:
            text = font.render(str, True, color)
            self.screen.blit(text, (x, y + offset_y))
            offset_y += text.get_size()[1]

    def redraw(self, sim: SimulationInterface, statistics: StatisticsSimulationObserver) -> None:
        # update
        #self.n += 10
        nodes = sim.get_cloud_network().nodes()
        clouds = sim.get_cloud_network().clouds()

        origin_cam_coordinates = self.world_coords_to_cam_coords((0, 0))
        if origin_cam_coordinates != self.last_origin_cam_coordinates:
            # if the picture was zoomed or panned, redraw the static part:
            self.last_origin_cam_coordinates = origin_cam_coordinates

            self.static_background.fill((255, 255, 255))

            # draw background image:
            if self.bg_image and self.bg_aabb:
                cam_coords_min = self.world_coords_to_cam_coords(
                    (self.bg_aabb.min_x, self.bg_aabb.min_y))
                cam_coords_max = self.world_coords_to_cam_coords(
                    (self.bg_aabb.max_x, self.bg_aabb.max_y))
                self.static_background.blit(
                    pygame.transform.smoothscale(
                        self.bg_image, (int(
                            (cam_coords_max[0] - cam_coords_min[0])), -int(
                            (cam_coords_max[1] - cam_coords_min[1])))), (cam_coords_min[0], cam_coords_max[1]))

            # draw grid
            for x in range(11):
                self.draw_world_space_line(
                    (0.1 * x, -1000), (0.1 * x, 1000), (230, 230, 255), surface=self.static_background)
            for y in range(11):
                self.draw_world_space_line(
                    (-1000, 0.1 * y), (1000, 0.1 * y), (230, 230, 255), surface=self.static_background)

            # plot connections between nodes

            for node in nodes:
                start = node.get_pos()
                for neighbor in node.get_neighbor_nodes():
                    end = neighbor.get_pos()
                    self.draw_world_space_line(
                        start, end, (0, 0, 200), 2, surface=self.static_background)

            # plot internal nodes
            for node in nodes:
                if not isinstance(node, CloudBaseStation):
                    self.draw_image(
                        self.imgIN,
                        node.get_pos(),
                        surface=self.static_background)

            # plot base stations
            for node in nodes:
                if isinstance(node, CloudBaseStation):
                    self.draw_image(
                        self.imgBS,
                        node.get_pos(),
                        surface=self.static_background)

            # plot edge clouds
            for cloud in clouds:
                self.draw_image(
                    self.imgEC,
                    cloud.get_pos(),
                    centered=True,
                    constant_offset=(
                        8,
                        8),
                    surface=self.static_background)

        self.screen.blit(self.static_background, (0, 0))

        # plot connections to base stations
        for user in sim.get_users():
            start = user.get_movement_model().get_pos()
            end = user.get_base_station().get_pos()
            self.draw_world_space_line(start, end, (200, 0, 0), 2)

        # plot users
        for user in sim.get_users():
            self.draw_image(
                self.imgUE,
                user.get_movement_model().get_pos(),
                centered=True)

        self.draw_cloud_annotations(sim)
        self.draw_service_annotations(sim)

        # plot resource usage histogram
        if self.display_histogram:
            num_bins = 10
            bin_size = 0.2
            upper_bound = num_bins * bin_size
            num_over_200_percent_utilized = 0
            resource_usages = [0] * num_bins
            resource_usages_labels = [str(int(i * bin_size * 100)) + '%-' + str(
                int((i + 1) * bin_size * 100)) + '%' for i in range(num_bins)]
            for cloud in sim.get_clouds():
                resource_available = cloud.memory_capacity()
                resource_used = cloud.total_memory_requirement()
                utilization = resource_used / resource_available
                bin = int((num_bins * (utilization / upper_bound)))
                if bin >= num_bins:
                    num_over_200_percent_utilized += 1
                else:
                    resource_usages[bin] += 1
            resource_usages.append(num_over_200_percent_utilized)
            resource_usages_labels.append('>200%')
            self.draw_histogram(
                resource_usages,
                resource_usages_labels,
                25,
                "Cloud Memory Utlization",
                True)

        selected_service_str = 'None'
        num_services = sim.get_num_services()
        if num_services > 0:
            selected_service_str = str(
                self.selected_service %
                num_services)

        usage_str = \
            'display usage histogram: U\n' +\
            'toggle neighborhood: N\n' + \
            'toggle services: S\n' + \
            'change selected cloud: <,>\n' + \
            'toggle service placement_cost: P\n' + \
            'change selected service: K,L\n' + \
            'selected cloud: ' + str(self.selected_cloud % len(clouds)) + '\n' + \
            'selected service: ' + selected_service_str

        self.draw_multiline_text(usage_str, self.subscript_font, 0, 0, (0, 0, 0))

        time_str = \
            "configured_simulation step: " + str(statistics.get_num_steps()) +  "\n"

        user_manager = sim.get_user_manager()
        if hasattr(
                user_manager,
                'current_time') and hasattr(
                user_manager,
                'start_time'):
            time_str += "configured_simulation time: " + str(
                datetime.fromtimestamp(
                    user_manager.current_time,
                    timezone('US/Pacific')).strftime("%b %d %Y %H:%M:%S")) + "local time\n"
            time_str += "elapsed configured_simulation time: " + \
                        str(datetime.fromtimestamp(user_manager.current_time) -
                            datetime.fromtimestamp(user_manager.start_time)) + \
                        "\n"

        time_str += "#users:" + str(len(user_manager.users())) + "\n"
        time_str += "#services:" + str(user_manager.num_services())
        self.draw_multiline_text(
            time_str, self.subscript_font, 300, 0, (255, 0, 0))

        pygame.display.update()

        return

    def plot(self, sim: SimulationInterface, statistics: StatisticsSimulationObserver) -> None:

        if pygame.event.get(pygame.QUIT):
            exit(0)

        for e in pygame.event.get():
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    self.drag = True
                if e.button == 4:
                    self.scale = self.scale * 1.1
                if e.button == 5:
                    self.scale = self.scale / 1.1

            if e.type == pygame.MOUSEBUTTONUP:
                self.drag = False

            if e.type == pygame.MOUSEMOTION:
                if self.drag:
                    delta_x, delta_y = e.pos
                    delta_x -= self.mouse_pos[0]
                    delta_y -= self.mouse_pos[1]
                    self.offset = (
                        self.offset[0] + delta_x / self.scale,
                        self.offset[1] + delta_y / self.scale)
                self.mouse_pos = e.pos

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_u:
                    self.display_histogram = not self.display_histogram

                elif e.key == pygame.K_n:
                    self.display_cloud_neighborhood = not self.display_cloud_neighborhood
                elif e.key == pygame.K_s:
                    self.display_cloud_services = not self.display_cloud_services
                elif e.key == pygame.K_COMMA:
                    self.selected_cloud -= 1
                elif e.key == pygame.K_PERIOD:
                    self.selected_cloud += 1

                elif e.key == pygame.K_p:
                    self.display_service_cloud = not self.display_service_cloud
                elif e.key == pygame.K_k:
                    self.selected_service -= 1
                elif e.key == pygame.K_l:
                    self.selected_service += 1

        self.redraw(sim, statistics)
        return