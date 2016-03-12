# encoding: utf-8

'''
@author: Tsuyoshi Hombashi
'''

VERSION = "0.4.0"


def verify_network_interface(self, device):
    import netifaces

    if device not in netifaces.interfaces():
        raise ValueError("invalid network interface: " + device)
