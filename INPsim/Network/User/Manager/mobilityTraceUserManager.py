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


from INPsim.Network.User.Manager.userManager import UserManager
from INPsim.Network.User.MovementModel.MobilityTraces.mobilityTraceModel import MobilityTraceMovementModel
from INPsim.Network.User.MovementModel.MobilityTraces import MobilityTrace, ImmutableMobilityTrace
from INPsim.vmath import AABB2, Vec2
import math
import pickle
import pyproj
import os
import datetime
import gzip

class MobilityTraceUserManager(UserManager):
    """
    Always has a constant number of random users within a unit square.
    All users are created at the beginning of the configured_simulation.
    """

    def __init__(self, service_model, dataset):
        """
        Initializes the user manager and loads the traces.
        """
        super(MobilityTraceUserManager, self).__init__(service_model)
        mobility_traces = None
        if dataset == 'geolife_beijing':
            mobility_traces = self.load_geolife_traces(reduced_data_set=True)
        elif dataset == 'cabspotting_san_francisco':
            mobility_traces = self.load_cabspotting_traces()
        elif dataset == 'cabspotting_san_francisco_one_day':
            mobility_traces = self.load_one_day_cabspotting_traces()
        else:
            raise ValueError('please specify a valid dataset')

        # extract metadata from the traces:
        self.start_time = math.inf
        self.next_trace_idx = 0
        self.end_time = -math.inf
        self._trace_aabb = None
        num_traces = 0
        self.active_traces = set()
        for trace in mobility_traces:
            num_traces += 1
            self.start_time = min(self.start_time, trace.start_time())
            self.end_time = max(self.end_time, trace.end_time())
            if self._trace_aabb:
                self._trace_aabb += trace.pos_aabb()
            else:
                self._trace_aabb = trace.pos_aabb()
        self.start_time -= 1
        print(
            "start_time: ",
            self.start_time,
            " end_time: ",
            self.end_time,
            " #traces: ",
            num_traces)

        # sort traces according to start time
        def sort_trace_start_key(trace):
            return trace.start_time()
        self.sorted_traces = mobility_traces
        self.sorted_traces.sort(key=sort_trace_start_key)
        self.current_time = self.start_time

    def trace_aabb(self):
        return self._trace_aabb

    def step(self, time_step):
        self.current_time += time_step
        while self.next_trace_idx < len(self.sorted_traces) and \
                self.sorted_traces[self.next_trace_idx].start_time() <= self.current_time:

            new_trace = self.sorted_traces[self.next_trace_idx]
            # create user and its services
            new_user = self.create_user(MobilityTraceMovementModel(new_trace))

            # start trace
            self.active_traces.add((new_trace,
                                    new_trace.end_time(),
                                    new_user))

            self.next_trace_idx += 1
            #print('started trace')

        traces_to_be_removed = []
        for active_trace_tuple in self.active_traces:
            trace, end_time, user = active_trace_tuple
            if end_time <= self.current_time:
                # end trace
                traces_to_be_removed.append(active_trace_tuple)
                # destroy user and its services
                self.remove_user(user)
                #print('stopped trace')

        # actually remove the ended traces from the list of active traces
        for active_trace_with_endtime in traces_to_be_removed:
            self.active_traces.remove(active_trace_with_endtime)

        super(MobilityTraceUserManager, self).step(time_step)

    def load_geolife_traces(self, reduced_data_set=False):
        """
        Either parses the geolife traces from the raw dataset (slow, due to coordinate transformation to UTM),
        or loads the set of traces from a cached pickle file.
        NOTE: when the MobilityTrace class changes, the cache must be updated!
        :return:
        """

        pickle_location = "../../Datasets/Geolife Trajectories 1.3.pickled"
        if reduced_data_set:
            pickle_location = "../../Datasets/Geolife Trajectories 1.3 reduced.pickled"

        # parse and cache

        mobility_traces = self.parse_geolife_traces(
            reduced_data_set=reduced_data_set,
            dataset_dir="../../Datasets/Geolife Trajectories 1.3/Data")
        print("dumping pickle")
        with open(pickle_location, 'wb') as f:
            pickle.dump(mobility_traces, f)
        print("finished pickling")

        # load from cache
        with open(pickle_location, 'rb') as f:
            user_traces = pickle.load(f)
        return mobility_traces

    def parse_geolife_traces(
            self,
            reduced_data_set=False,
            dataset_dir="Datasets/Geolife Trajectories 1.3/Data"):
        # these boundaries are a hand-chosen box around the 5th ring-road of
        # beijing that will be used to filter out traces that are not in
        # beijing.
        north_west_boundary = (40.1, 116.15)
        south_east_boundary = (39.75, 116.6)
        # to use only one year of the traces for debugging
        beginning_of_2009_timestamp = 1230764400
        middle_of_2009_timestamp = 1246399200
        # the UTM zone (beijing in this case) is needed to accurately convert
        # longitude and latitude to meters, acting as a reference point for the
        # planar projection
        utm_zone = "50S"
        utm_beijing = pyproj.Proj(
            "+proj=utm +zone=" +
            utm_zone +
            ", +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs")

        beijing_aabb = AABB2.from_vectors(
            [
                Vec2.from_tuple(
                    utm_beijing(
                        north_west_boundary[1],
                        north_west_boundary[0])),
                Vec2.from_tuple(
                    utm_beijing(
                        south_east_boundary[1],
                        south_east_boundary[0]))])
        print(
            "beijing aabb: ",
            beijing_aabb,
            ", w: ",
            beijing_aabb.width() /
            1000,
            "km, h:",
            beijing_aabb.height() /
            1000,
            "km")

        mobility_traces = []
        num_processed = 0
        num_rejected_traces_outside_beijing = 0
        for (dirpath, dirnames, filenames) in os.walk(dataset_dir):
            for filename in filenames:
                if filename.endswith(".plt"):
                    path = os.path.join(dirpath, filename)
                    with open(path) as f:
                        #user_id = int(str(path).split(os.sep)[-3])
                        # load trace:
                        mobility_trace = MobilityTrace()
                        for line_nr, line in enumerate(f):
                            # ignore the first
                            if line_nr < 6:
                                continue
                            latitude, longitude, _, altitude, _, date, time = line.split(
                                ',')
                            # parse date & time
                            year, month, day = [int(s)
                                                for s in date.split('-')]
                            hour, minute, second = [
                                int(s) for s in time.split(':')]
                            date_time_obj = datetime.datetime(
                                year, month, day, hour, minute, second)
                            if reduced_data_set and (date_time_obj.timestamp(
                            ) < beginning_of_2009_timestamp or date_time_obj.timestamp() > middle_of_2009_timestamp):
                                break
                            if date_time_obj != datetime.datetime.fromtimestamp(
                                    date_time_obj.timestamp()):
                                print("ambiguous timestamp!")
                                break

                            # parse latitude and longitude:
                            latitude, longitude = float(
                                latitude), float(longitude)
                            x, y = utm_beijing(longitude, latitude)

                            mobility_trace.add_data_point(
                                date_time_obj.timestamp(), Vec2(x, y))
                        else:  # if the parsing loop finished without break statement
                            if len(mobility_trace) > 0:
                                mobility_trace = ImmutableMobilityTrace(
                                    mobility_trace)
                                if beijing_aabb.intersects(
                                        mobility_trace.pos_aabb()):
                                    mobility_traces.append(mobility_trace)
                                else:
                                    num_rejected_traces_outside_beijing += 1
                    num_processed += 1
                    if num_processed % 10 == 0:
                        print(
                            "parsed ",
                            num_processed,
                            "traces, #rejected (outside beijing): ",
                            num_rejected_traces_outside_beijing)
        return mobility_traces

    def load_cabspotting_traces(self):

        pickle_location = "Datasets/cabspotting.pickled"

        """
        mobility_traces = self.parse_cabspotting_traces(dataset_dir="../../Datasets/cabspottingdata")
        print("dumping pickle")
        with gzip.open(pickle_location, 'wb') as f:
            pickle.dump(mobility_traces, f)
        print("finished pickling")
        """

        # load from cache
        with open(pickle_location, 'rb') as f:
            mobility_traces = pickle.load(f)

        return mobility_traces

    def load_one_day_cabspotting_traces(self):

        pickle_location = "Datasets/cabspotting_one_day.pickled.gz"

        """
        # parse and cache
        start = 1211094000 #18.5.2008, 00:00, us pacific
        end = start+24*60*60   #19.5.2008, 00:00, us pacific
        mobility_traces = self.parse_cabspotting_traces(dataset_dir="Datasets/cabspottingdata",timestamp_lower_bound=start, timestamp_upper_bound=end)
        print("dumping pickle")
        with gzip.open(pickle_location, 'wb') as f:
            pickle.dump(mobility_traces, f)
        print("finished pickling")
        """

        # load from cache
        try:
            with gzip.open(pickle_location, 'rb') as f:
                mobility_traces = pickle.load(f)
        except ModuleNotFoundError:
            print("Could not load traces due to refactoring. Rebuilding chache now.")
            # parse and cache
            start = 1211094000 #18.5.2008, 00:00, us pacific
            end = start+24*60*60   #19.5.2008, 00:00, us pacific
            mobility_traces = self.parse_cabspotting_traces(dataset_dir="Datasets/cabspottingdata",timestamp_lower_bound=start, timestamp_upper_bound=end)
            print("dumping pickle")
            with open(pickle_location, 'wb') as f:
                pickle.dump(mobility_traces, f)
            print("finished pickling")

        return mobility_traces

    def parse_cabspotting_traces(
            self,
            dataset_dir="Datasets/cabspottingdata",
            timestamp_lower_bound=-math.inf,
            timestamp_upper_bound=math.inf):
        # the UTM zone (beijing in this case) is needed to accurately convert
        # longitude and latitude to meters, acting as a reference point for the
        # planar projection
        utm_zone = "10S"
        utm_san_francisco = pyproj.Proj(
            "+proj=utm +zone=" +
            utm_zone +
            ", +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs")

        mobility_traces = []
        num_processed = 0
        for (dirpath, dirnames, filenames) in os.walk(dataset_dir):
            for filename in filenames:
                if filename.startswith("new_"):
                    path = os.path.join(dirpath, filename)
                    with open(path) as f:
                        # load trace:
                        mobility_trace = MobilityTrace()
                        datapoints = []
                        for line in f:
                            latitude, longitude, fare_active, timestamp = line.split(
                                ' ')
                            # parse latitude, longitude, timestamp:
                            latitude, longitude, timestamp = float(
                                latitude), float(longitude), int(timestamp)
                            if timestamp_lower_bound <= timestamp <= timestamp_upper_bound:
                                # convert coordinates to UTM
                                x, y = utm_san_francisco(longitude, latitude)
                                datapoints.append((timestamp, Vec2(x, y)))
                                #mobility_trace.add_data_point(timestamp, Vec2(x, y))
                        else:  # if the parsing loop finished without break statement
                            # add all datapoints in reverse order
                            for timestamp, pos in reversed(datapoints):
                                mobility_trace.add_data_point(timestamp, pos)
                            if len(mobility_trace) > 0:
                                mobility_traces.append(
                                    ImmutableMobilityTrace(mobility_trace))
                    num_processed += 1
                    if num_processed % 10 == 0:
                        print("parsed ", num_processed, "traces")
        return mobility_traces
