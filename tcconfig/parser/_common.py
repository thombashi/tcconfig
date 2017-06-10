# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals


def _to_unicode(text):
    try:
        return text.decode("ascii")
    except AttributeError:
        return text
