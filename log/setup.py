import atexit
import json
import logging.config
import logging.handlers
import pathlib
import queue
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)


def setup_logging():
    config_file = pathlib.Path(__file__).parent / "config.json"
    with open(config_file) as f_in:
        config = json.load(f_in)

    # Modify filename attribute
    config["handlers"]["file_json"]["filename"] = os.path.join(
        os.getenv("LOG_PATH"), "log.jsonl"
    )

    log_queue = queue.Queue(-1)  # Create a Queue
    config["handlers"]["queue_handler"][
        "queue"
    ] = log_queue  # Add the Queue to the queue_handler configuration

    logging.config.dictConfig(config)

    # Get the handlers from the root logger
    root_logger = logging.getLogger()
    handlers = root_logger.handlers

    # Replace the handlers in the root logger with the QueueHandler
    queue_handler = [
        handler
        for handler in handlers
        if isinstance(handler, logging.handlers.QueueHandler)
    ][0]
    root_logger.handlers = [queue_handler]

    # Create a QueueListener with the handlers
    listener = logging.handlers.QueueListener(log_queue, *handlers)
    listener.start()

    return listener


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
