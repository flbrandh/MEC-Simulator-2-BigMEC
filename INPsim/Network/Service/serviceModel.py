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


import abc
import copy
import random


class ServiceConfigurator:
    """
    Abstract base class for ServiceConfigurators, which create services according to a certain distribution.
    """

    @abc.abstractmethod
    def create_service_group(self, number_of_services):
        """
        Initializes a given number of services according to a specific distribution.
        The services are to be assigned to a single user.
        :param number_of_services: number of services that should be created
        :return: list of number_of_services services
        """
        pass


class PrototypeBasedServiceConfigurator(
        ServiceConfigurator):  # TODO rewrite such that the random priority, memory req., latency req. is not such a hack
    """
    Creates all services from a prototype service.
    """

    def __init__(self,
                 prototype_service,
                 min_priority,
                 max_priority,
                 min_memory_requirement,
                 max_memory_requirement,
                 min_latency_requirement,
                 max_latency_requirement):
        """
        Initializer.
        :param prototype_service: The service prototype that all services are created from by means of copying.
        """
        self._prototype_service = prototype_service
        self._rng = random.Random()
        self._rng.seed(1337)  # TODO don't hardocde the seed!
        self._min_priority = min_priority
        self._max_priority = max_priority
        self._min_memory_requirement = min_memory_requirement
        self._max_memory_requirement = max_memory_requirement
        self._min_latency_requirement = min_latency_requirement
        self._max_latency_requirement = max_latency_requirement

    def create_service_group(self, number_of_services):
        services = []
        for i in range(number_of_services):
            new_service = copy.copy(self._prototype_service)
            new_service.priority = self._rng.randint(self._min_priority, self._max_priority)
            new_service.memory_requirement = self._rng.randint(self._min_memory_requirement, self._max_memory_requirement)
            new_service.latency_requirement = self._rng.randint(self._min_latency_requirement, self._max_latency_requirement)
            services.append(new_service)
        return services


class ServiceModel:
    """
    abstract base class for SerciveModels, which create the services of newly generated users
    """

    def __init__(self, service_configurator):
        self._service_configurator = service_configurator

    def create_user_services(self):
        """
        Abstract method for the initialization_cost o a list of services for a user.
        Whenever this is called, a list of services should be generated, according to a specific distribution.
        The type of services is specified by the ServiceConfigurator of this class.
        :return: list of services
        """
        return self._service_configurator.create_service_group(
            self.num_services_for_new_user())

    @abc.abstractmethod
    def num_services_for_new_user(self):
        """
        To define the number of services that should be created for the next user, override this function.
        :return: the number of services that should be created for the nex new user.
        """
        pass


class ConstantServiceModel(ServiceModel):
    """
    Service model that creates a constant number of services for each user.
    """

    def __init__(self, service_configurator, services_per_user):
        """
        Initializes the service model with its containing_object to the desired number of services per user.
        :param service_configurator: the service configurator that creates each new service.
        :param services_per_user: the number of services that each user should have
        """
        super(ConstantServiceModel, self).__init__(service_configurator)
        self._services_per_user = services_per_user

    def num_services_for_new_user(self):
        """
        Always creates the specified number of services for each user.
        :return: number that was specified as the constant nubme ro f services per user.
        """
        return self._services_per_user
