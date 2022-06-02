import logging
from typing import TYPE_CHECKING, Dict, List, Set

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from core.configservice.base import ConfigService


class ConfigServiceDependencies:
    """
    Generates sets of services to start in order of their dependencies.
    """

    def __init__(self, services: Dict[str, "ConfigService"]) -> None:
        """
        Create a ConfigServiceDependencies instance.

        :param services: services for determining dependency sets
        """
        # helpers to check validity
        self.dependents: Dict[str, Set[str]] = {}
        self.started: Set[str] = set()
        self.node_services: Dict[str, "ConfigService"] = {}
        for service in services.values():
            self.node_services[service.name] = service
            for dependency in service.dependencies:
                dependents = self.dependents.setdefault(dependency, set())
                dependents.add(service.name)

        # used to find paths
        self.path: List["ConfigService"] = []
        self.visited: Set[str] = set()
        self.visiting: Set[str] = set()

    def startup_paths(self) -> List[List["ConfigService"]]:
        """
        Find startup path sets based on service dependencies.

        :return: lists of lists of services that can be started in parallel
        """
        paths = []
        for name in self.node_services:
            service = self.node_services[name]
            if service.name in self.started:
                logger.debug(
                    "skipping service that will already be started: %s", service.name
                )
                continue

            path = self._start(service)
            if path:
                paths.append(path)

        if self.started != set(self.node_services):
            raise ValueError(
                "failure to start all services: %s != %s"
                % (self.started, self.node_services.keys())
            )

        return paths

    def _reset(self) -> None:
        """
        Clear out metadata used for finding service dependency sets.

        :return: nothing
        """
        self.path = []
        self.visited.clear()
        self.visiting.clear()

    def _start(self, service: "ConfigService") -> List["ConfigService"]:
        """
        Starts a oath for checking dependencies for a given service.

        :param service: service to check dependencies for
        :return: list of config services to start in order
        """
        logger.debug("starting service dependency check: %s", service.name)
        self._reset()
        return self._visit(service)

    def _visit(self, current_service: "ConfigService") -> List["ConfigService"]:
        """
        Visits a service when discovering dependency chains for service.

        :param current_service: service being visited
        :return: list of dependent services for a visited service
        """
        logger.debug("visiting service(%s): %s", current_service.name, self.path)
        self.visited.add(current_service.name)
        self.visiting.add(current_service.name)

        # dive down
        for service_name in current_service.dependencies:
            if service_name not in self.node_services:
                raise ValueError(
                    "required dependency was not included in node services: %s"
                    % service_name
                )

            if service_name in self.visiting:
                raise ValueError(
                    "cyclic dependency at service(%s): %s"
                    % (current_service.name, service_name)
                )

            if service_name not in self.visited:
                service = self.node_services[service_name]
                self._visit(service)

        # add service when bottom is found
        logger.debug("adding service to startup path: %s", current_service.name)
        self.started.add(current_service.name)
        self.path.append(current_service)
        self.visiting.remove(current_service.name)

        # rise back up
        for service_name in self.dependents.get(current_service.name, []):
            if service_name not in self.visited:
                service = self.node_services[service_name]
                self._visit(service)

        return self.path
