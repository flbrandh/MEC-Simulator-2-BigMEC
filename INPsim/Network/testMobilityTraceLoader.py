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


from INPsim.Network.User.Manager.mobilityTraceUserManager import MobilityTraceUserManager
from statistics import mean
from INPsim.Network.Service.serviceModel import ConstantServiceModel, PrototypeBasedServiceConfigurator
from INPsim.Network.Service import Service
import os
import matplotlib.pyplot as plt


cwd = os.getcwd()
print(cwd)

srvm = ConstantServiceModel(PrototypeBasedServiceConfigurator(
    Service(memory_requirement=1, latency_requirement=5)), 1)
m = MobilityTraceUserManager(
    service_model=srvm,
    dataset='cabspotting_san_francisco')

num_seconds = 60 * 60 * 24 * 30
num_active_traces_per_step = []
for i in range(num_seconds):
    m.step(1)
    num_active_traces_per_step.append(len(m.active_traces))
plt.plot(num_active_traces_per_step)
plt.show()
print("average number of simultaneous traces: ",
      mean(num_active_traces_per_step))