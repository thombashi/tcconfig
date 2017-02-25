# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from typepy.type import RealNumber

from tcconfig._converter import Humanreadable


def is_invalid_param(rate, delay, loss, corrupt):
    params = [
        delay,
        loss,
        corrupt,
    ]

    is_invalid = all([
        not RealNumber(param).is_type() or param == 0 for param in params
    ])

    try:
        Humanreadable(rate, kilo_size=1000).to_no_prefix_value()
    except ValueError:
        pass
    else:
        is_invalid = False

    return is_invalid
