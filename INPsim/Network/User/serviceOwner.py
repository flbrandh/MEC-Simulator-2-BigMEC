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


class ServiceOwner:
    """
    Describes the owner of a service.
    """

    def __init__(self):
        """
        initializes th service owner with no services
        """
        self._services = []

    def services(self):
        """
        Returns all services that are owned by this service owner.
        :return:
        """
        return self._services

    def add_service(self, service):
        """
        Add a service to this service owner.
        :param service:
        :return:
        """
        assert service not in self._services
        service.set_owner(self)
        self._services.append(service)

    def remove_service(self, service):
        """
        Remove a service from the service owner.
        :param service:
        :return:
        """
        assert service in self._services
        service.set_owner(None)
        service.get_cloud().remove_service(service)
        self._services.remove(service)

    def remove_all_services(self):
        """
        Removes all services from the service owner.
        :return: None
        """
        while self._services:
            self.remove_service(self._services[-1])
