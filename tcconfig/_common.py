# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import, unicode_literals

import contextlib
import errno
import os
import re
import sys

import logbook
import logbook.more
import msgfy
import subprocrunner as spr
import typepy
from humanreadable import ParameterError
from path import Path
from simplesqlite import SimpleSQLite

from ._const import IPV6_OPTION_ERROR_MSG_FORMAT, TcCommandOutput
from ._logger import logger


_bin_path_cache = {}


@contextlib.contextmanager
def logging_context(name):
    logger.debug("|---- {:s}: {:s} -----".format("start", name))
    try:
        yield
    finally:
        logger.debug("----- {:s}: {:s} ----|".format("complete", name))


def find_bin_path(command):
    def _to_regular_bin_path(file_path):
        path_obj = Path(file_path)
        if path_obj.islink():
            return path_obj.readlinkabs()

        return file_path

    if command in _bin_path_cache:
        return _bin_path_cache.get(command)

    bin_path = spr.Which(command)
    if bin_path.is_exist():
        _bin_path_cache[command] = _to_regular_bin_path(bin_path.abspath())
        return _bin_path_cache[command]

    for sbin_path in ("/sbin/{:s}".format(command), "/usr/sbin/{:s}".format(command)):
        if os.path.isfile(sbin_path):
            _bin_path_cache[command] = _to_regular_bin_path(sbin_path)
            return _bin_path_cache[command]

    return None


def check_command_installation(command):
    if find_bin_path(command):
        return

    logger.error("command not found: {}".format(command))
    sys.exit(errno.ENOENT)


def initialize_cli(options):
    from ._logger import set_log_level

    debug_level_format_str = (
        "[{record.level_name}] {record.channel} {record.func_name} "
        "({record.lineno}): {record.message}"
    )
    if options.log_level == logbook.DEBUG:
        info_level_format_str = debug_level_format_str
    else:
        info_level_format_str = "[{record.level_name}] {record.channel}: {record.message}"

    logbook.more.ColorizedStderrHandler(
        level=logbook.DEBUG, format_string=debug_level_format_str
    ).push_application()
    logbook.more.ColorizedStderrHandler(
        level=logbook.INFO, format_string=info_level_format_str
    ).push_application()

    set_log_level(options.log_level)
    spr.SubprocessRunner.is_save_history = True

    if options.is_output_stacktrace:
        spr.SubprocessRunner.is_output_stacktrace = options.is_output_stacktrace

    SimpleSQLite.global_debug_query = options.debug_query


def is_execute_tc_command(tc_command_output):
    return tc_command_output == TcCommandOutput.NOT_SET


def validate_within_min_max(param_name, value, min_value, max_value, unit):
    from dataproperty import DataProperty

    if value is None:
        return

    if unit is None:
        unit = ""
    else:
        unit = "[{:s}]".format(unit)

    if value > max_value:
        raise ParameterError(
            "'{:s}' is too high".format(param_name),
            expected="<={:s}{:s}".format(DataProperty(max_value).to_str(), unit),
            value="{:s}{:s}".format(DataProperty(value).to_str(), unit),
        )

    if value < min_value:
        raise ParameterError(
            "'{:s}' is too low".format(param_name),
            expected=">={:s}{:s}".format(DataProperty(min_value).to_str(), unit),
            value="{:s}{:s}".format(DataProperty(value).to_str(), unit),
        )


def normalize_tc_value(tc_obj):
    import ipaddress

    try:
        tc_obj.sanitize()
    except ipaddress.AddressValueError as e:
        logger.error(IPV6_OPTION_ERROR_MSG_FORMAT.format(e))
        sys.exit(errno.EINVAL)
    except ValueError as e:
        logger.error(msgfy.to_error_message(e))
        sys.exit(errno.EINVAL)


def run_command_helper(command, ignore_error_msg_regexp, notice_msg, exception_class=None):
    proc = spr.SubprocessRunner(command, error_log_level=logbook.NOTSET)
    proc.run()

    if proc.returncode == 0:
        return 0

    if ignore_error_msg_regexp:
        match = ignore_error_msg_regexp.search(proc.stderr)
        if match is None:
            error_msg = "\n".join(
                [
                    "command execution failed",
                    "  command={}".format(command),
                    "  stderr={}".format(proc.stderr),
                ]
            )

            if re.search("RTNETLINK answers: Operation not permitted", proc.stderr):
                logger.error(error_msg)
                sys.exit(proc.returncode)

            logger.error(error_msg)

            return proc.returncode

    if typepy.is_not_null_string(notice_msg):
        logger.notice(notice_msg)

    if exception_class is not None:
        raise exception_class(command)

    return proc.returncode
