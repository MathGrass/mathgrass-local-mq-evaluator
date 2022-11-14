import base64
import datetime
import json
import logging
from types import SimpleNamespace
from typing import Any

from abstract_evaluator import AbstractEvaluator
from database import Database
from docker_container import ContentFile
from docker_manager import DockerManager


class BasicEvalRequest:
    """ This class represents an evaluation request for the BasicEvaluator.
    """
    def __init__(self, request_id: int, task_id: int, input_answer: Any):
        """ Initialize a BasicEvalRequest instance.

        :param request_id: ID of request
        :param task_id: ID of task
        :param input_answer: Input answer
        """
        self.request_id = request_id
        self.task_id = task_id
        self.input_answer = input_answer

    def __str__(self):
        return "InputAnswer: request_id=" + str(self.request_id) + " task_id=" + str(self.task_id) + \
               " input_answer=" + str(self.input_answer)
    

class BasicEvaluator(AbstractEvaluator):
    """ This class represents the standard MathGrass evaluator.
    """
    def __init__(self, docker_manager: DockerManager):
        """ Initialize an AbstractEvaluator instance.

        :param docker_manager: DockerManager
        """
        self.db = Database()
        self.docker_manager = docker_manager

    def get_queue_name(self):
        """ Return the message queue name.

        :return: string
        """
        return "TASK_REQUEST"

    def run(self, request: BasicEvalRequest):
        """ Run an evaluation.

        :param request: evaluation request
        :return: None
        """
        # get a free container
        container = self.docker_manager.allocate_container()
        if not container:
            logging.info(f"Could not run task {request.request_id} because no docker container could be allocated")
            return
        
        # fetch data
        request_data = self.db.get_basic_eval_request_data(request.task_id)
        if not request_data:
            logging.info("No data available, aborting...")
            # TODO: save error in db with request_id
            return

        # extract data from request
        eval_script = request_data.script
        graph_obj = request_data.graph

        # decode graph
        graph_json = json.dumps(graph_obj.to_json())
        graph_decoded = base64.b64encode(graph_json.encode("utf-8")).decode("utf-8")

        # decode answer
        answer_decoded = base64.b64encode(request.input_answer.encode("utf-8")).decode("utf-8")

        # build command to run
        command = f"sage eval.sage {answer_decoded} {graph_decoded}"

        # load and move evaluation script to docker
        container.upload_content_files([ContentFile("eval.sage", eval_script)])

        # prepare and launch
        container.add_result_observer(self.on_result)
        container.run_task_solver(command, request.request_id)
        
    def on_result(self, request_id: int, is_correct: bool):
        """ Process an incoming result by adding the result to the database.

        :param request_id: ID of request
        :param is_correct: whether result was correct or not
        :return: None
        """
        logging.info(f"Result with ID {request_id} received! Result was correct: {is_correct}")
        self.db.add_evaluation_result(request_id, is_correct)
        # TODO: save to db

    def on_request_received(self, body):
        """ Process an incoming request by triggering the evaluation on the requests body.

        :param body: request body
        :return: None
        """
        logging.info("Request received! Starting to process request...")
        request = json.loads(body, object_hook=lambda d: SimpleNamespace(**d))
        self.run(BasicEvalRequest(request.requestId, request.taskId, request.inputAnswer))
