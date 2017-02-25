# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
import re

import typepy


class Humanreadable(object):
    __RE_EXP_PAIR_LIST = [
        [re.compile("^b$", re.IGNORECASE), 0],
        [re.compile("^k$", re.IGNORECASE), 1],
        [re.compile("^m$", re.IGNORECASE), 2],
        [re.compile("^g$", re.IGNORECASE), 3],
        [re.compile("^t$", re.IGNORECASE), 4],
        [re.compile("^p$", re.IGNORECASE), 5],
    ]

    def __init__(self, readable_size, kilo_size=1024):
        """
        String converter that humanreadable byte size to a number.

        :param str readable_size: human readable size (bytes). e.g. 256 M
        :param int kilo_size: size of ``kilo``. 1024 or 1000
        """

        self.__readable_size = readable_size
        self.kilo_size = kilo_size  # [byte]

    def to_no_prefix_value(self):
        """
        :raises ValueError:
        """

        if typepy.is_null_string(self.__readable_size):
            raise ValueError("readable_size is empty")

        size = self.__readable_size[:-1]
        unit = self.__readable_size[-1]

        size = float(size)
        unit = unit.lower()

        if size < 0:
            raise ValueError("minus size")

        coefficient = self.__unit_to_no_prefix(unit)

        return size * coefficient

    def to_kilo_value(self):
        """
        :param str readable_size: human readable size (bytes). e.g. 256 M
        :raises ValueError:
        """

        return self.to_no_prefix_value() / self.kilo_size

    def __unit_to_no_prefix(self, unit):
        if self.kilo_size not in [1000, 1024]:
            raise ValueError("invalid kilo size: {}".format(self.kilo_size))

        for re_exp_pair in self.__RE_EXP_PAIR_LIST:
            re_pattern, exp = re_exp_pair

            if re_pattern.search(unit):
                return self.kilo_size ** exp

        raise ValueError("unknown unit: {}".format(unit))
