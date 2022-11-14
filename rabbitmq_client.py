import logging
import threading
from typing import Dict

import pika


class MessageQueueMiddleware:
    """ This class manages any connections with the evaluator.
    """
    def __init__(self, broker_host: str):
        """ Initialize a MessageQueueMiddleWare instance.

        :param broker_host: host address
        """
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=broker_host))
        logging.info("Connected to message queue!")
        self.channel = connection.channel()

    def consume(self, queue: str, callback):
        """ Consume a callback in another thread.

        :param queue: name of message queue
        :param callback: function to call
        :return: None
        """
        self.channel.queue_declare(queue=queue)
        thread = threading.Thread(target=self._inner_consume, args=(queue, callback))
        thread.start()
        logging.info("Consuming started!")

    def _inner_consume(self, queue: str, callback):
        """ Consume callback internally.

        :param queue: name of message queue
        :param callback: function to call
        :return: None
        """
        self.channel.basic_consume(queue=queue, on_message_callback=callback, auto_ack=True)
        logging.info(f'Waiting for messages on queue "{queue}"')
        self.channel.start_consuming()

    def publish(self, queue: str, msg):
        """ Publish message on message queue.

        :param queue: name of message queue
        :param msg: message to send
        :return: None
        """
        self.channel.basic_publish(exchange='', routing_key=queue, body=msg)
        logging.info(f"Published {msg} on {queue}!")


def build_answer_queue_msg(request_id: int, is_correct: bool) -> Dict:
    """ Build a dictionary containing the answer message.

    :param request_id: ID of request
    :param is_correct: whether task result was correct or not
    :return: dictionary containing answer
    """
    return {
        "request": request_id,
        "is_correct": is_correct
    }
