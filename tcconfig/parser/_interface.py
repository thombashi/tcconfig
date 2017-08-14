# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals

import abc

import six


@six.add_metaclass(abc.ABCMeta)
class ParserInterface(object):

    @abc.abstractmethod
    def parse(self, text):  # pragma: no cover
        pass


@six.add_metaclass(abc.ABCMeta)
class AbstractParser(ParserInterface):

    def __init__(self):
        self._clear()

    @abc.abstractproperty
    def _tc_subcommand(self):  # pragma: no cover
        pass

    @abc.abstractmethod
    def _clear(self):  # pragma: no cover
        pass

    @staticmethod
    def _to_unicode(text):
        try:
            return text.decode("ascii")
        except AttributeError:
            return text
