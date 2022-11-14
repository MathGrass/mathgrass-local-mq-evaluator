import io
import logging
import tarfile
from typing import Any, List

from docker import DockerClient


class ContentFile:
    """ This class represents a file with content and the files' path.
    """
    def __init__(self, filepath: str, content: Any):
        """ Initialize a ContentFile instance.

        :param filepath: filepath of file
        :param content: content of file
        """
        self.filepath = filepath
        self.content = content


class DockerContainer:
    """ This class represents Docker containers.
    """
    def __init__(self, name: str, docker_client: DockerClient):
        """ Initialize a DockerContainer instance.

        :param name: name of container
        :param docker_client: docker client
        """
        self.result_observers = []
        self.name = name
        self.docker_client = docker_client
        self.phy_container = self.docker_client.containers.get(self.name)

    def upload_content_files(self, content_files: List[ContentFile]):
        """ Upload a list of config files.

        :param content_files: list of config files
        :return: None
        """
        logging.info("Creating archive...")

        # create archive with content files
        fh = io.BytesIO()
        with tarfile.open(fileobj=fh, mode='w') as tar:
            for content_file in content_files:
                data = content_file.content.encode("utf-8")
                info = tarfile.TarInfo(content_file.filepath)
                info.size = len(data)
                tar.addfile(info, io.BytesIO(initial_bytes=data))

        # upload tar file
        self._upload_tar_file_inner(fh.getvalue())

    def _upload_tar_file_inner(self, tar_data: tarfile):
        """ Upload a tar file to the container.

        :param tar_data: tar file with ContentFiles
        :return: None
        """
        self.phy_container.start()
        logging.info("Uploading content files...")
        self.phy_container.put_archive(path="/home/sage/sage", data=tar_data)

    def run_task_solver(self, command: str, request_id: int):
        """ Run the container with specified command and notify observers with result.

        :param command: command to run
        :param request_id: ID of request
        :return: None
        """
        logging.info(f"Running command for request {request_id}: {command}")
        # start container and run command
        self.phy_container.start()
        result = self.phy_container.exec_run(cmd=command, workdir="/home/sage/sage", tty=True)

        # process result
        # TODO: use exit code to get result
        output_string = result.output.decode("utf-8").strip()
        if not output_string:
            logging.error(f"No output log from task request {request_id} received!")
        output_log_entries = output_string.split("\n")

        # check if is correct and send result to observers
        is_correct = output_log_entries[-1] == "True"
        self.call_observers(request_id, is_correct)

    def add_result_observer(self, observer):
        """ Add observers for new results.

        :param observer: function to be triggered
        :return: None
        """
        self.result_observers.append(observer)

    def call_observers(self, request_id: int, result: bool):
        """ Call all registered observers.

        :param request_id: ID of request
        :param result: task result
        :return: None
        """
        for observer in self.result_observers:
            observer(request_id, result)

    def vanish(self):
        """ Remove this container.

        :return: None
        """
        try:
            logging.info(f"Removing container {self.name}...")
            self.phy_container.stop()
            self.phy_container.remove()
        except:
            pass
