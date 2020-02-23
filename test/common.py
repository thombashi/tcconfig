"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""


import json
import sys
from collections import OrderedDict

import humanreadable as hr
from subprocrunner import SubprocessRunner
from typepy import RealNumber


DEADLINE_TIME = 3  # [sec]
ASSERT_MARGIN = 0.5


def print_test_result(expected, actual, error=None):
    if isinstance(expected, (dict, OrderedDict)):
        expected = json.dumps(expected, indent=4)
    print("[expected]\n{}\n".format(expected))

    if isinstance(actual, (dict, OrderedDict)):
        actual = json.dumps(actual, indent=4)
    print("[actual]\n{}\n".format(actual))

    if error:
        print(error, file=sys.stderr)


def is_invalid_param(rate, delay, packet_loss, packet_duplicate, corrupt, reordering):
    param_values = [packet_loss, packet_duplicate, corrupt, reordering]

    print("rate={}, params={}".format(rate, param_values))

    is_invalid = all(
        [not RealNumber(param_value).is_type() or param_value <= 0 for param_value in param_values]
        + [hr.Time(delay, hr.Time.Unit.MILLISECOND).milliseconds <= 0]
    )

    try:
        hr.BitPerSecond(rate).bps
    except (TypeError, ValueError):
        pass
    else:
        is_invalid = False

    return is_invalid


def runner_helper(command):
    proc_runner = SubprocessRunner(command)
    proc_runner.run()

    print("{}\n{}\n".format(proc_runner.command_str, proc_runner.stderr), file=sys.stderr)

    assert proc_runner.returncode == 0

    return proc_runner


class NullLogger:
    level_name = None

    def remove(self, handler_id=None):  # pragma: no cover
        pass

    def add(self, sink, **kwargs):  # pragma: no cover
        pass

    def disable(self, name):  # pragma: no cover
        pass

    def enable(self, name):  # pragma: no cover
        pass

    def critical(self, __message, *args, **kwargs):  # pragma: no cover
        pass

    def debug(self, __message, *args, **kwargs):  # pragma: no cover
        pass

    def error(self, __message, *args, **kwargs):  # pragma: no cover
        pass

    def exception(self, __message, *args, **kwargs):  # pragma: no cover
        pass

    def info(self, __message, *args, **kwargs):  # pragma: no cover
        pass

    def log(self, __level, __message, *args, **kwargs):  # pragma: no cover
        pass

    def success(self, __message, *args, **kwargs):  # pragma: no cover
        pass

    def trace(self, __message, *args, **kwargs):  # pragma: no cover
        pass

    def warning(self, __message, *args, **kwargs):  # pragma: no cover
        pass
