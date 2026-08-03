import logging

from pythonjsonlogger import jsonlogger


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    if any(isinstance(h.formatter, jsonlogger.JsonFormatter) for h in root.handlers):
        return  # already configured (e.g. re-imported under a test runner)

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)

    root.handlers = [handler]
    root.setLevel(level)
