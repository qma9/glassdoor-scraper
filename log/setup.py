from multiprocessing import Queue
from typing import Tuple
from threading import Thread
import json
from logging.config import dictConfig
from logging.handlers import QueueHandler, QueueListener
import logging
import pathlib
import queue
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)

def logger_thread(q: queue.Queue) -> None:
    while True:
        record = q.get()
        if record is None:
            break
        logger = logging.getLogger(record.name)
        logger.handle(record)

m_queue = None

def get_queue() -> Queue:
    global m_queue
    if m_queue is None:
        m_queue = Queue()
    return m_queue


def setup_logging() -> Tuple[QueueListener, Thread]: 
    config_file = pathlib.Path(__file__).parent / "config.json"
    with open(config_file) as f_in:
        config = json.load(f_in)

    # Modify filename attribute
    config["handlers"]["file_json"]["filename"] = os.path.join(
        os.getenv("LOG_PATH"), "log.jsonl"
    )

    log_queue = queue.Queue(-1)  # Create a Queue
    config["handlers"]["queue_handler"]["queue"] = log_queue  # Add the Queue to the queue_handler configuration

    dictConfig(config)

    # Create the QueueHandler directly
    queue_handler = QueueHandler(log_queue)

    # Get the root logger and set its handlers to the QueueHandler
    root_logger = logging.getLogger()
    root_logger.handlers = [queue_handler]

    # Create a QueueListener with the new QueueHandler
    listener = QueueListener(log_queue, queue_handler)
    listener.start()

    # Start the logger thread
    lt = Thread(target=logger_thread, args=(log_queue,))
    lt.start()

    return listener, lt


def main():
    setup_logging()
    logger.setLevel(logging.INFO)
    logger.debug("debug message", extra={"x": "hello"})
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")
    logger.critical("critical message")
    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("exception message")


if __name__ == "__main__":
    # Test logging
    main()
