# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
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

_RE_NUMBER = re.compile("^[\-\+]?[0-9\.]+")


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

    def __init__(self, readable_size, kilo_size=1024):
        """
        String converter that human-readable byte size to a number.

        :param str readable_size: human readable size (bytes). e.g. 256 M
        :param int kilo_size: size of ``kilo``. 1024 or 1000
        """

        self.__readable_size = readable_size
        self.kilo_size = kilo_size

        self.__validate_kilo_size()

    def to_bit(self):
        """
        :raises InvalidParameterError:
        """

        logger.debug("human readable size to bit: {}".format(
            self.__readable_size))

        if not typepy.is_not_null_string(self.__readable_size):
            raise TypeError(
                "readable_size must be a string: actual={}".format(
                    self.__readable_size))

        self.__readable_size = self.__readable_size.strip()

        try:
            size = _RE_NUMBER.search(self.__readable_size).group()
        except AttributeError:
            raise InvalidParameterError(
                "invalid value", value=self.__readable_size)
        size = float(size)
        if size < 0:
            raise InvalidParameterError(
                "size must be greater or equals to zero", value=size)

        unit = _RE_NUMBER.sub("", self.__readable_size).strip().lower()

        return size * self.__get_coefficient(unit)

    def to_kilo_bit(self):
        """
        :param str readable_size: human readable size (bytes). e.g. 256 M
        :raises ValueError:
        """

        return self.to_bit() / self.kilo_size

    def __validate_kilo_size(self):
        VALID_KILLO_SIZE = [1000, 1024]

        if self.kilo_size not in VALID_KILLO_SIZE:
            raise InvalidParameterError(
                "invalid kilo size",
                expected=VALID_KILLO_SIZE, value=self.kilo_size)

    def __get_coefficient(self, unit_str):
        self.__validate_kilo_size()

        for unit in self.__UNIT_LIST:
            if unit.regexp.search(unit_str):
                return self.kilo_size ** unit.factor

        raise UnitNotFoundError("unit not found: value={}".format(unit_str))


class HumanReadableTime(object):
    __VALID_MINUTE_UNIT_LIST = ["m", "min", "mins", "minute", "minutes"]
    __VALID_SEC_UNIT_LIST = ["s", "sec", "secs", "second", "seconds"]
    __VALID_MSEC_UNIT_LIST = [
        "ms", "msec", "msecs",  "millisecond", "milliseconds"]
    __VALID_USEC_UNIT_LIST = [
        "us", "usec", "usecs", "microsecond", "microseconds"]
    __VALID_UNIT_LIST = (
        __VALID_MINUTE_UNIT_LIST + __VALID_SEC_UNIT_LIST +
        __VALID_MSEC_UNIT_LIST + __VALID_USEC_UNIT_LIST)

    def __init__(self, readable_time):
        self.__readable_time = readable_time

    def __eq__(self, other):
        return self.get_msec() == other.get_msec()

    def __ne__(self, other):
        return self.get_msec() != other.get_msec()

    def __lt__(self, other):
        return self.get_msec() < other.get_msec()

    def __le__(self, other):
        return self.get_msec() <= other.get_msec()

    def __gt__(self, other):
        return self.get_msec() > other.get_msec()

    def __ge__(self, other):
        return self.get_msec() >= other.get_msec()

    def __repr__(self):
        return self.get_value()

    @classmethod
    def get_valid_unit_list(cls):
        return cls.__VALID_UNIT_LIST

    def get_value(self):
        self.__preprocess()

        return "{:f}{:s}".format(self.__number, self.__unit)

    def get_msec(self):
        self.__preprocess()

        coef = 1
        if self.__unit == "sec":
            coef = 1000
        elif self.__unit == "us":
            coef = .001

        return self.__number * coef

    def validate(self, min_value=None, max_value=None):
        if min_value is not None:
            if not isinstance(min_value, HumanReadableTime):
                min_value = HumanReadableTime(min_value)

            if self < min_value:
                raise InvalidParameterError(
                    "time value is too low",
                    expected="greater than or equal to {}".format(min_value),
                    value=self)

        if max_value is not None:
            if not isinstance(max_value, HumanReadableTime):
                max_value = HumanReadableTime(max_value)

            if self > max_value:
                raise InvalidParameterError(
                    "time value is too high",
                    expected="less than or equal to {}".format(max_value),
                    value=self)

        if self.__unit not in self.__VALID_UNIT_LIST:
            raise UnitNotFoundError(
                "unknown unit".format(self.__readable_time))

    def __normalize(self):
        if self.__unit in self.__VALID_SEC_UNIT_LIST:
            self.__unit = "sec"
        elif self.__unit in self.__VALID_MSEC_UNIT_LIST:
            self.__unit = "ms"
        elif self.__unit in self.__VALID_USEC_UNIT_LIST:
            self.__unit = "us"
        elif self.__unit in self.__VALID_MINUTE_UNIT_LIST:
            self.__number *= 60
            self.__unit = "sec"

    def __get_number(self):
        match = _RE_NUMBER.search(self.__readable_time)
        if not match:
            raise InvalidParameterError(
                "human-readable time must be include a number",
                value=self.__readable_time)

        return float(match.group())

    def __get_unit(self):
        if typepy.type.RealNumber(self.__readable_time).is_type():
            # if the input value is real numbers consider unit as milliseconds.
            return "ms"

        return _RE_NUMBER.sub("", self.__readable_time).strip().lower()

    def __preprocess(self):
        self.__number = self.__get_number()
        self.__unit = self.__get_unit()
        self.validate()
        self.__normalize()
