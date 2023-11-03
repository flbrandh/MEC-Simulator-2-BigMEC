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


min_lon =-122.5164
max_lon =-122.3551
min_lat = 37.6001
max_lat = 37.8111
#https://render.openstreetmap.org/cgi-bin/export?bbox=-122.5164,37.6001,-122.3551,37.811&scale=50000&format=png

sf_verizon_LTE_lines=[]

positions = set()


sf_coastline_polygon_long_lat =[
  	(-122.36253, 7.59590),
  	(-122.3753, 37.6074),
  	(-122.3713, 37.6140),
  	(-122.3584, 37.6086),
  	(-122.3542, 37.6151),
  	(-122.3660, 37.6215),
  	(-122.3643, 37.6288),
  	(-122.3791, 37.6309),
  	(-122.3853, 37.6415),
  	(-122.3722, 37.6562),
  	(-122.3791, 37.6652),
  	(-122.3770, 37.6785),
  	(-122.3836, 37.6774),
  	(-122.3903, 37.7089),
  	(-122.3698, 37.7088),
  	(-122.3773, 37.7234),
  	(-122.3610, 37.7142),
  	(-122.3541, 37.7295),
  	(-122.3698, 37.7353),
  	(-122.3655, 37.7409),
  	(-122.3731, 37.7492),
  	(-122.3848, 37.7781),
  	(-122.3856, 37.7898),
  	(-122.4044, 37.8101),
  	(-122.4326, 37.8087),
  	(-122.4605, 37.8058),
  	(-122.4778, 37.8116),
  	(-122.4869, 37.7899),
  	(-122.5065, 37.7883),
  	(-122.5147, 37.7821),
  	(-122.5077, 37.7233),
  	(-122.4963, 37.6839),
  	(-122.4977, 37.6104),
  	(-122.50693, 7.59630),
  	(-122.36253, 7.59590),
]
#sf_coastline_polygon_x_y = [utm_san_francisco(lon, lat) for lon,lat in sf_coastline_polygon_long_lat]

def point_inside_polygon(x,y,poly):
    #from http://www.ariel.com.au/a/python-point-int-poly.html
    n = len(poly)
    inside = False

    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


#file is from openCellID
with open('cell_towers_2019-12-11-T000000.csv') as file:
    first_line = file.readline()
    for line in file:
            for line in file:
        radio, mcc, net, area, cell, unit, lon, lat, rrange, samples, changeable, created, updated, average_signal = line.split(
            ',')
        mcc, net, area, cell, unit, rrange, samples, changeable, created, updated, average_signal = [
            int(x) for x in [
                mcc, net, area, cell, unit, rrange, samples, changeable, created, updated, average_signal]]
        lon, lat = float(lon), float(lat)

        if radio == 'LTE' and min_lon <= lon <= max_lon and min_lat <= lat <= max_lat and net in [
          		487,
          		590,
          		282,
          		287,
          		271,
          		481,
          		276,
          		486,
          		13,
          		281,
          		286,
          		270,
          		480,
          		275,
          		485,
          		12,
          		280,
          		110,
          		285,
          		390,
          		274,
          		484,
          		10,
          		279,
          		789,
          		910,
          		284,
          		289,
          		273,
          		483,
          		4,
          		278,
          		488,
          		890,
          		283,
          		288,
          		272,
          		482,
          		277] and mcc in [
          		310,
          		311] and samples > 2 and point_inside_polygon(
          		lon,
          		lat,
          		sf_coastline_polygon_long_lat):

            if (lon,lat) not in positions:
                sf_verizon_LTE_lines.append(line)
                positions.add((lon, lat))



print('there are',len(sf_verizon_LTE_lines),
      'unique base station sites in the selected san francisco area')


with open('cell_towers_san_francisco.csv','w') as file:
    file.write(first_line)
    for line in sf_verizon_LTE_lines:
        file.write(line)