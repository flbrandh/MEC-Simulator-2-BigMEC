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


import itertools
import pyproj
import matplotlib.pyplot as plt

utm_zone = "10"  # the UTM zone (beijing in this case) is needed to accurately convert longitude and latitude to meters, acting as a reference point for the planar projection
utm_san_francisco = pyproj.Proj("+proj=utm +zone=" + utm_zone + " +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs")

min_lon =-122.5164
max_lon =-122.3551
min_lat = 37.6001
max_lat = 37.8111
#https://render.openstreetmap.org/cgi-bin/export?bbox=-122.5164,37.6001,-122.3551,37.811&scale=50000&format=png

min_x, min_y = utm_san_francisco(min_lon, min_lat)
max_x, max_y = utm_san_francisco(max_lon, max_lat)

print("min_x:",min_x) # 542688.443644256
print("max_x:",max_x) # 556765.7262020159
print("min_y:",min_y) # 4161556.7164416737
print("max_y:",max_y) # 4185052.3668366373


bs_x = []
bs_y = []
lacs = []


with open('cell_towers_san_francisco.csv') as file:
    first_line = file.readline()
    for line in file:
        radio, mcc, net, area, cell, unit, lon, lat, range, samples, changeable, created, updated, average_signal = line.split(
            ',')
        mcc, net, area, cell, unit, range, samples, changeable, created, updated, average_signal = [
            int(x) for x in [
                mcc, net, area, cell, unit, range, samples, changeable, created, updated, average_signal]]
        lon, lat = float(lon), float(lat)

        x,y = utm_san_francisco(lon, lat)
        bs_x.append(x)
        bs_y.append(y)
        lacs.append(area)

sf_map = plt.imread('../SF_area.png')
fig, ax = plt.subplots()  # figsize = (8,7))
allLACs = set(lacs)
print("number of LACs: ", len(allLACs))
lac_colors = {}
colors = itertools.cycle(["r", "b", "g", "m", "y", "c", "w", "k"])
for lac in allLACs:
    lac_colors[lac] = next(colors)
bs_colors = [lac_colors[lac] for lac in lacs]
ax.scatter(bs_x, bs_y, zorder=1, alpha=1, c=bs_colors, s=5)
ax.set_title('San Francisco Verizon LTE base stations')
BBox = (min_x, max_x, min_y, max_y)
# ax.set_xlim(BBox[0],BBox[1])
# ax.set_ylim(BBox[2],BBox[3])
ax.imshow(sf_map, zorder=0, extent=BBox, aspect='equal')
plt.show()
