import basic_evaluator
import unittest

from unittest.mock import Mock

from database import BasicEvalRequestData
from docker_manager import DockerManager
from model.graph_model import Graph


class BasicEvaluatorTest(unittest.TestCase):

    def setUp(self):
        docker_manager = DockerManager(max_active_containers=2,
                                       ready_container_amount=1)
        database = Mock()

        self.MOCK_GRAPH = Graph(id=1, label="label", vertices={}, edges={})
        self.MOCK_SCRIPT = "print(True)"
        self.request: basic_evaluator.BasicEvalRequest = basic_evaluator.BasicEvalRequest(request_id=1,
                                                                                          task_id=1,
                                                                                          input_answer="myAnswer")

        def mock_basic_eval_request_function(task_id):
            return BasicEvalRequestData(self.MOCK_GRAPH, self.MOCK_SCRIPT)

        database.get_basic_eval_request_data = lambda task_id: mock_basic_eval_request_function(task_id)

        def add_evaluation_result(request_id, is_correct, time):
            self.assertTrue(is_correct, "Evaluation result is not correct")

        database.add_evaluation_result = add_evaluation_result

        self.evaluator = basic_evaluator.BasicEvaluator(docker_manager=docker_manager)
        self.evaluator.db = database

    def test_smoke_test_run_evaluator(self):
        self.evaluator.run(self.request)


if __name__ == '__main__':
    unittest.main()
