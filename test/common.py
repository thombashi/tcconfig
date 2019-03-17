# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import, print_function

import sys

import humanreadable as hr
from subprocrunner import SubprocessRunner
from typepy import RealNumber

from tcconfig._const import Tc


DEADLINE_TIME = 3  # [sec]
ASSERT_MARGIN = 0.5


def print_test_result(expected, actual, error=None):
    print("[expected]\n{}\n".format(expected))
    print("[actual]\n{}\n".format(actual))

    if error:
        print(error, file=sys.stderr)


def is_invalid_param(rate, delay, packet_loss, packet_duplicate, corrupt, reordering):
    param_values = [packet_loss, packet_duplicate, corrupt, reordering]

    print(param_values)

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


def execute_tcdel(device):
    return SubprocessRunner([Tc.Command.TCDEL, device, "--all"], dry_run=False).run()


def runner_helper(command):
    proc_runner = SubprocessRunner(command)
    proc_runner.run()

    print("{}\n{}\n".format(proc_runner.command_str, proc_runner.stderr), file=sys.stderr)

    assert proc_runner.returncode == 0

    return proc_runner
