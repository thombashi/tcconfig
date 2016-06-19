# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

VERSION = "0.6.2"


def verify_network_interface(device):
    import netifaces

    if device not in netifaces.interfaces():
        raise ValueError("invalid network interface: " + device)
