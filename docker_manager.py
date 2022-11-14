import logging

import docker as docker_lib

from docker_container import DockerContainer


class DockerManager:
    """ This class manages Docker containers by preparing/creating/cleaning/etc. containers.
    """
    def __init__(self, max_active_containers: int, ready_container_amount: int):
        """ Initialize a DockerManager instance.

        :param max_active_containers: max amount of containers that can be active
        :param ready_container_amount: amount of containers that should be ready
        """
        self.docker = docker_lib.from_env()
        self.ready_containers = []
        self.occupied_containers = []
        self.max_active_containers = max_active_containers
        self.ready_container_amount = ready_container_amount

        # pull image
        logging.info("Pulling sagemath image...")
        self.docker.images.pull("sagemath/sagemath")

        # init ready containers
        self.prepare_containers()
    
    def prepare_containers(self):
        """ Prepare containers by creating new ones if possible.

        :return: None
        """
        num_ready = len(self.ready_containers)

        # if possible create more ready docker containers
        if num_ready < self.ready_container_amount:
            # get number of containers to create
            creation_amount = min(self.ready_container_amount - num_ready,
                                  self.max_active_containers - (len(self.occupied_containers) + num_ready))
            logging.info(f"Preparing {creation_amount} containers!")

            # create containers
            for _ in range(creation_amount):
                self.ready_containers.append(self.create_container_in_registry())

    def create_container_in_registry(self):
        """ Create a docker container and register in registry.

        :return: None
        """
        container = self.docker.containers.create("sagemath/sagemath")
        return DockerContainer(container.name, self.docker)

    @staticmethod
    def remove_container_from_registry(container: DockerContainer):
        """ Remove a container from the registry.

        :param container: container to remove
        :return: None
        """
        container.vanish()

    def allocate_container(self) -> DockerContainer | None:
        """ Allocate a ready container.

        :return: allocated container
        """
        # check if enough containers ready - otherwise queue (should not happen because the msg bus will balance load)
        if not self.ready_containers:
            logging.info("No containers ready! Adding to queue...")
            # TODO: queue request
            return None

        # Get ready container and occupy
        selection = self.ready_containers.pop()
        logging.info(f"Container available! Occupying container {selection.name}...")
        self.occupied_containers.append(selection)
        selection.add_result_observer(lambda x, y: self.finishContainer(selection))

        # create more ready containers
        self.prepare_containers()

        return selection

    def finishContainer(self, container: DockerContainer):
        """ Process a container that has done its job.

        :param container: finished container
        :return: None
        """
        logging.info(f"Cleaning up container {container.name}...")
        # remove container
        self.occupied_containers.remove(container)

        # remove docker container
        self.remove_container_from_registry(container)

        # check if another container should be prepared
        self.prepare_containers()

    def clear_all_containers(self):
        """ Remove all containers.

        :return: None
        """
        logging.info("Removing all containers from the registry...")
        for container in self.ready_containers:
            container.vanish()
    