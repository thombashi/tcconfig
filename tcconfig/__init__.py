# encoding: utf-8

'''
@author: Tsuyoshi Hombashi
'''

VERSION = "0.6.1"


def verify_network_interface(device):
    import netifaces

    if device not in netifaces.interfaces():
        raise ValueError("invalid network interface: " + device)
