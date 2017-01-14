# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals
import abc

import six


@six.add_metaclass(abc.ABCMeta)
class ShaperInterface(object):

    @abc.abstractproperty
    def algorithm_name(self):  # pragma: no cover
        pass

    @abc.abstractmethod
    def make_qdisc(self):  # pragma: no cover
        pass

    @abc.abstractmethod
    def add_rate(self):  # pragma: no cover
        pass

    @abc.abstractmethod
    def add_filter(self):  # pragma: no cover
        pass


class AbstractShaper(ShaperInterface):

    @property
    def dev(self):
        return "dev {:s}".format(self._tc_obj.get_tc_device())

    def __init__(self, tc_obj):
        self._tc_obj = tc_obj
