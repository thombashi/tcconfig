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
    def make_qdisc(self, qdisc_major_id):  # pragma: no cover
        pass

    @abc.abstractmethod
    def add_rate(self, qdisc_major_id):  # pragma: no cover
        pass

    @abc.abstractmethod
    def add_filter(self, qdisc_major_id):  # pragma: no cover
        pass


class AbstractShaper(ShaperInterface):

    def __init__(self, tc_obj):
        self._tc_obj = tc_obj
