class AbstractEvaluator:
    """ This abstract class defines an interface for Evaluator implementations.
    """

    def on_request_received(self, body):
        pass

    def get_queue_name(self):
        pass
