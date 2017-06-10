# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from collections import namedtuple
import re

import typepy


ByteUnit = namedtuple("ByteUnit", "regexp factor")


class Humanreadable(object):
    __UNIT_LIST = [
        ByteUnit(regexp=re.compile("^b$", re.IGNORECASE), factor=0),
        ByteUnit(regexp=re.compile("^k$", re.IGNORECASE), factor=1),
        ByteUnit(regexp=re.compile("^m$", re.IGNORECASE), factor=2),
        ByteUnit(regexp=re.compile("^g$", re.IGNORECASE), factor=3),
        ByteUnit(regexp=re.compile("^t$", re.IGNORECASE), factor=4),
        ByteUnit(regexp=re.compile("^p$", re.IGNORECASE), factor=5),
    ]

    def __init__(self, readable_size, kilo_size=1024):
        """
        String converter that humanreadable byte size to a number.

        :param str readable_size: human readable size (bytes). e.g. 256 M
        :param int kilo_size: size of ``kilo``. 1024 or 1000
        """

        self.__readable_size = readable_size
        self.kilo_size = kilo_size  # [byte]

        self.__validate_kilo_size()

    def to_byte(self):
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

        return size * self.__get_coefficient(unit)

    def to_kilo_value(self):
        """
        :param str readable_size: human readable size (bytes). e.g. 256 M
        :raises ValueError:
        """

        return self.to_byte() / self.kilo_size

    def __validate_kilo_size(self):
        if self.kilo_size not in [1000, 1024]:
            raise ValueError("invalid kilo size: {}".format(self.kilo_size))

    def __get_coefficient(self, unit_str):
        self.__validate_kilo_size()

        for unit in self.__UNIT_LIST:
            if unit.regexp.search(unit_str):
                return self.kilo_size ** unit.factor

        raise ValueError("unit not found: value={}".format(unit_str))
