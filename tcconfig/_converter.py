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

from ._error import (
    InvalidParameterError,
    UnitNotFoundError,
)
from ._logger import logger

ByteUnit = namedtuple("ByteUnit", "regexp factor")


class Humanreadable(object):
    __UNIT_LIST = [
        ByteUnit(regexp=re.compile("^b$", re.IGNORECASE), factor=0),
        ByteUnit(regexp=re.compile("^bps$", re.IGNORECASE), factor=0),
        ByteUnit(regexp=re.compile("^k$", re.IGNORECASE), factor=1),
        ByteUnit(regexp=re.compile("^kbps$", re.IGNORECASE), factor=1),
        ByteUnit(regexp=re.compile("^m$", re.IGNORECASE), factor=2),
        ByteUnit(regexp=re.compile("^mbps$", re.IGNORECASE), factor=2),
        ByteUnit(regexp=re.compile("^g$", re.IGNORECASE), factor=3),
        ByteUnit(regexp=re.compile("^gbps$", re.IGNORECASE), factor=3),
        ByteUnit(regexp=re.compile("^t$", re.IGNORECASE), factor=4),
        ByteUnit(regexp=re.compile("^gbps$", re.IGNORECASE), factor=3),
        ByteUnit(regexp=re.compile("^p$", re.IGNORECASE), factor=5),
    ]
    __RE_NUMBER = re.compile("^[\-\+]?[0-9\.]+")

    def __init__(self, readable_size, kilo_size=1024):
        """
        String converter that humanreadable byte size to a number.

        :param str readable_size: human readable size (bytes). e.g. 256 M
        :param int kilo_size: size of ``kilo``. 1024 or 1000
        """

        self.__readable_size = readable_size
        self.kilo_size = kilo_size

        self.__validate_kilo_size()

    def to_bit(self):
        """
        :raises ValueError:
        """

        logger.debug("readable_size: {}".format(self.__readable_size))

        if not typepy.is_not_null_string(self.__readable_size):
            raise TypeError(
                "readable_size must be a string: actual={}".format(
                    self.__readable_size))

        self.__readable_size = self.__readable_size.strip()

        try:
            size = self.__RE_NUMBER.search(self.__readable_size).group()
        except AttributeError:
            raise InvalidParameterError(
                "invalid value: {}".format(self.__readable_size))
        size = float(size)
        if size < 0:
            raise InvalidParameterError(
                "size must be greater or equals to zero")

        unit = self.__RE_NUMBER.sub("", self.__readable_size).strip().lower()

        return size * self.__get_coefficient(unit)

    def to_kilo_bit(self):
        """
        :param str readable_size: human readable size (bytes). e.g. 256 M
        :raises ValueError:
        """

        return self.to_bit() / self.kilo_size

    def __validate_kilo_size(self):
        if self.kilo_size not in [1000, 1024]:
            raise ValueError("invalid kilo size: {}".format(self.kilo_size))

    def __get_coefficient(self, unit_str):
        self.__validate_kilo_size()

        for unit in self.__UNIT_LIST:
            if unit.regexp.search(unit_str):
                return self.kilo_size ** unit.factor

        raise UnitNotFoundError("unit not found: value={}".format(unit_str))
