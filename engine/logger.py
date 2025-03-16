# engine/logger.py

import logging
import sys
from typing import Any, Dict

class Logger:
    _logger: logging.Logger = None

    @classmethod
    def _init_logger(cls):
        if cls._logger is None:
            cls._logger = logging.getLogger("workflow_logger")
            cls._logger.setLevel(logging.DEBUG)

            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.DEBUG)

            formatter = logging.Formatter(
                fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            cls._logger.addHandler(handler)
            cls._logger.propagate = True

    @classmethod
    def debug(cls, message: str, extra: Dict[str, Any] = None) -> None:
        cls._init_logger()
        cls._logger.debug(message, extra=extra or {})

    @classmethod
    def info(cls, message: str, extra: Dict[str, Any] = None) -> None:
        cls._init_logger()
        cls._logger.info(message, extra=extra or {})

    @classmethod
    def warning(cls, message: str, extra: Dict[str, Any] = None) -> None:
        cls._init_logger()
        cls._logger.warning(message, extra=extra or {})

    @classmethod
    def error(cls, message: str, extra: Dict[str, Any] = None) -> None:
        cls._init_logger()
        cls._logger.error(message, extra=extra or {})

    @classmethod
    def critical(cls, message: str, extra: Dict[str, Any] = None) -> None:
        cls._init_logger()
        cls._logger.critical(message, extra=extra or {})