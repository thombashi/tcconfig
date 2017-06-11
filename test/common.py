# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import print_function

from subprocrunner import SubprocessRunner
from typepy.type import RealNumber

from tcconfig._const import TcCommand
from tcconfig._converter import Humanreadable


def is_invalid_param(
        rate, delay, packet_loss, packet_duplicate, corrupt, reordering):
    param_value_list = [
        delay,
        packet_loss,
        packet_duplicate,
        corrupt,
        reordering,
    ]

    print(param_value_list)

    is_invalid = all([
        not RealNumber(param_value).is_type() or param_value <= 0
        for param_value in param_value_list
    ])

    try:
        Humanreadable(rate, kilo_size=1000).to_bit()
    except (TypeError, ValueError):
        pass
    else:
        is_invalid = False

    return is_invalid


def execute_tcdel(device):
    SubprocessRunner(
        "{:s} --device {}".format(TcCommand.TCDEL, device),
        dry_run=False).run()
