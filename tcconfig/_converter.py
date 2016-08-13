# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
import re


class Humanreadable(object):
    __RE_EXP_PAIR_LIST = [
        [re.compile("^b$", re.IGNORECASE), 0],
        [re.compile("^k$", re.IGNORECASE), 1],
        [re.compile("^m$", re.IGNORECASE), 2],
        [re.compile("^g$", re.IGNORECASE), 3],
        [re.compile("^t$", re.IGNORECASE), 4],
        [re.compile("^p$", re.IGNORECASE), 5],
    ]

    def __init__(self, kilo_size=1024):
        self.kilo_size = kilo_size  # [byte]

    def humanreadable_to_byte(self, readable_size):
        """
        :param str readable_size: human readable size (bytes). e.g. 256 M
        :param int kilo_size: size of kilo. 1024 or 1000
        :raises ValueError:
        """

        size = readable_size[:-1]
        unit = readable_size[-1]

        size = float(size)
        unit = unit.lower()

        if size < 0:
            raise ValueError("minus size")

        coefficient = self.__unit_to_byte(unit)

        return size * coefficient

    def __unit_to_byte(self, unit):
        if self.kilo_size not in [1000, 1024]:
            raise ValueError("invalid kilo size: {}".format(self.kilo_size))

        for re_exp_pair in self.__RE_EXP_PAIR_LIST:
            re_pattern, exp = re_exp_pair

            if re_pattern.search(unit):
                return self.kilo_size ** exp

        raise ValueError("unknown unit: {}".format(unit))
