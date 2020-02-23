"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""


import sys

import simplesqlite
import subprocrunner
from loguru import logger


MODULE_NAME = "tcconfig"

logger.disable(MODULE_NAME)


def set_logger(is_enable):
    if is_enable:
        logger.enable(MODULE_NAME)
    else:
        logger.disable(MODULE_NAME)

    simplesqlite.set_logger(is_enable)
    subprocrunner.set_logger(is_enable)


def set_log_level(log_level):
    if log_level == "DEBUG":
        log_format = (
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
    else:
        log_format = "<level>[{level}]</level> {message}"

    logger.remove()
    logger.add(sys.stderr, colorize=True, format=log_format, level=log_level)

    if log_level == "QUIET":
        set_logger(is_enable=False)
    else:
        set_logger(is_enable=True)
