# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals


VERSION = "0.7.2"

ANYWHERE_NETWORK = "0.0.0.0/0"
KILO_SIZE = 1000


class Tc(object):

    class Subcommand(object):
        CLASS = "class"
        FILTER = "filter"
        QDISC = "qdisc"
        SHOW = "show"

    class Param(object):
        CLASS_ID = "classid"
        FLOW_ID = "flowid"
        HANDLE = "handle"
        NETWORK = "network"
        PARENT = "parent"
        PORT = "port"
