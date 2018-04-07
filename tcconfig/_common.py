# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import, unicode_literals

import contextlib
import errno
import sys

import logbook
import subprocrunner as spr
import typepy

from ._const import IPV6_OPTION_ERROR_MSG_FORMAT, Tc, TcCommandOutput
from ._error import NetworkInterfaceNotFoundError
from ._logger import logger


@contextlib.contextmanager
def logging_context(name):
    logger.debug("|---- {:s}: {:s} -----".format("start", name))
    try:
        yield
    finally:
        logger.debug("----- {:s}: {:s} ----|".format("complete", name))


def check_tc_command_installation():
    try:
        spr.Which("tc").verify()
    except spr.CommandNotFoundError as e:
        logger.error("{:s}: {}".format(e.__class__.__name__, e))
        sys.exit(errno.ENOENT)


def check_execution_authority():
    import os

    if os.getuid() != 0:
        # using OSError for Python2 compatibility reason.
        # (PermissionError introduced since Python 3.3)
        raise OSError("Permission denied (you must be root)")


def initialize_cli(options):
    from ._logger import set_log_level

    debug_format_str = (
        "[{record.level_name}] {record.channel} {record.func_name} "
        "({record.lineno}): {record.message}")
    if options.log_level == logbook.DEBUG:
        info_format_str = debug_format_str
    else:
        info_format_str = (
            "[{record.level_name}] {record.channel}: {record.message}")

    logbook.StderrHandler(
        level=logbook.DEBUG, format_string=debug_format_str
    ).push_application()
    logbook.StderrHandler(
        level=logbook.INFO, format_string=info_format_str
    ).push_application()

    set_log_level(options.log_level)
    spr.SubprocessRunner.is_save_history = True

    if options.is_output_stacktrace:
        spr.SubprocessRunner.is_output_stacktrace = (
            options.is_output_stacktrace)


def is_execute_tc_command(tc_command_output):
    return tc_command_output == TcCommandOutput.NOT_SET


def normalize_tc_value(tc_obj):
    import ipaddress

    try:
        tc_obj.sanitize()
    except ipaddress.AddressValueError as e:
        logger.error(IPV6_OPTION_ERROR_MSG_FORMAT.format(e))
        sys.exit(errno.EINVAL)
    except ValueError as e:
        logger.error("{:s}: {}".format(e.__class__.__name__, e))
        sys.exit(errno.EINVAL)


def run_command_helper(command, error_regexp, notice_message, exception_class=None):
    proc = spr.SubprocessRunner(command, error_log_level=logbook.NOTSET)
    proc.run()

    if proc.returncode == 0:
        return 0

    match = error_regexp.search(proc.stderr)
    if match is None:
        logger.error(proc.stderr)
        return proc.returncode

    if typepy.is_not_null_string(notice_message):
        logger.notice(notice_message)

    if exception_class is not None:
        raise exception_class(command)

    return proc.returncode


def run_tc_show(subcommand, device):
    from ._network import verify_network_interface

    if subcommand not in Tc.Subcommand.LIST:
        raise ValueError("unexpected tc sub command: {}".format(subcommand))

    verify_network_interface(device)

    runner = spr.SubprocessRunner(
        "tc {:s} show dev {:s}".format(subcommand, device))
    if runner.run() != 0 and runner.stderr.find("Cannot find device") != -1:
        # reach here if the device does not exist at the system and netiface
        # not installed.
        raise NetworkInterfaceNotFoundError(device=device)

    return runner.stdout
