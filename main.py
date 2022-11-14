import logging.config
import signal
import sys
import time

from basic_evaluator import BasicEvaluator
from docker_manager import DockerManager
from rabbitmq_client import MessageQueueMiddleware

ALL_EVALUATORS = [BasicEvaluator]

BROKER_HOST = "127.0.0.1"
MAX_ACTIVE_CONTAINERS = 100
READY_CONTAINERS = 1

# configure logging
logging.config.fileConfig("logging.conf")


def run_forever():
    """ Keep evaluator running.

    :return: None
    """
    while True:
        time.sleep(10)


def main():
    """ Initialize Docker manager and message queue and keep running.

    :return: None
    """
    logging.info("Starting evaluator microservice!")

    # initializing docker manager
    docker_manager = DockerManager(MAX_ACTIVE_CONTAINERS, READY_CONTAINERS)

    def cleanup():
        logging.info("Clearing docker containers...")
        docker_manager.clear_all_containers()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)

    # create message queue middleware instance
    msg_queue_middleware = MessageQueueMiddleware(BROKER_HOST)

    # map queues to evaluators
    for evaluator in ALL_EVALUATORS:
        instance = evaluator(docker_manager)
        queue_name = instance.get_queue_name()

        def on_request_received(ch, method, properties, body):
            instance.on_request_received(body)
    
        msg_queue_middleware.consume(queue_name, on_request_received)

    run_forever()


if __name__ == '__main__':
    main()
