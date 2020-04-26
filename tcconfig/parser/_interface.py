"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

import abc


class ParserInterface(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def parse(self, device, text):  # pragma: no cover
        pass


class AbstractParser(ParserInterface, metaclass=abc.ABCMeta):
    def __init__(self, con):
        self._con = con
        self._clear()

    @property
    def con(self):
        return self._con

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
