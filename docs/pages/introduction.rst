tcconfig
========

.. image:: https://img.shields.io/pypi/pyversions/tcconfig.svg
   :target: https://pypi.python.org/pypi/tcconfig
.. image:: https://travis-ci.org/thombashi/tcconfig.svg?branch=master
   :target: https://travis-ci.org/thombashi/tcconfig


Summary
-------

``tcconfig`` is a Simple tc command wrapper.
Easy to set up traffic control of network bandwidth/latency/packet-loss to a network interface.


Traffic control features
------------------------

Network
~~~~~~~

Traffic control can be specified network to apply to:

-  Outgoing/Incoming packets
-  Certain IP address/network and port

Available parameters
~~~~~~~~~~~~~~~~~~~~

The following parameters can be set to network interfaces.

-  Network bandwidth rate [G/M/K bps]
-  Network latency [milliseconds]
-  Packet loss rate [%]
-  Packet corruption rate [%]