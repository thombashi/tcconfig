# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import


def verify_network_interface(device):
    import netifaces

    if device not in netifaces.interfaces():
        raise ValueError("invalid network interface: " + device)
