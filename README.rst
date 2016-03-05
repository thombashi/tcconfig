**tcconfig**

.. image:: https://img.shields.io/pypi/pyversions/tcconfig.svg
   :target: https://pypi.python.org/pypi/tcconfig
.. image:: https://travis-ci.org/thombashi/tcconfig.svg?branch=master
   :target: https://travis-ci.org/thombashi/tcconfig

.. contents:: Table of contents
   :backlinks: top
   :local:

Summary
=======
Simple tc command wrapper.
Easy to setup traffic control of
network bandwidth/latency/packet-loss to a network interface.

Traffic control
===============

Network
-------

Traffic control can be specified network to apply to:

-  Outgoing/Incoming packets
-  Certain IP address/network and port

Parameters
----------

The following parameters can be set of network interfaces.

-  Network bandwidth [G/M/K bps]
-  Network latency [milliseconds]
-  Packet loss rate [%]

Installation
============

Install via pip
---------------

tcconfig canbe installed via
`pip <https://pip.pypa.io/en/stable/installing/>`__ (Python package
manager).

.. code:: console

    sudo pip install tcconfig

Basic usage
===========

Outgoing packet traffic control settings are as follows

Set traffic control (tcset)
---------------------------

tcset is a command to impose traffic control to a network interface
(device).

tcset help
~~~~~~~~~~

.. code:: console

    usage: tcset [-h] [--version] [--logging] [--stacktrace] [--debug | --quiet]
                 --device DEVICE [--direction {outgoing,incoming}] [--rate RATE]
                 [--delay DELAY] [--loss LOSS] [--network NETWORK] [--port PORT]
                 [--overwrite]

    optional arguments:
      -h, --help            show this help message and exit
      --version             show program's version number and exit
      --debug               for debug print.
      --quiet               suppress output of execution log message.

    Miscellaneous:
      --logging             output execution log to a file (tcset.log).
      --stacktrace          display stack trace when an error occurred.

    Traffic Control:
      --device DEVICE       network device name (e.g. eth0)
      --direction {outgoing,incoming}
                            direction of network communication that impose traffic
                            control. default=outgoing
      --rate RATE           network bandwidth [K|M|G bps]
      --delay DELAY         round trip network delay [ms] (default=0)
      --loss LOSS           round trip packet loss rate [%] (default=0)
      --network NETWORK     destination network of traffic control
      --port PORT           destination port of traffic control
      --overwrite           overwrite existing settings

e.g. Set a limit on bandwidth up to 100Kbps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: console

    # tcset --device eth0 --rate 100k

e.g. Set 100ms network delay
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: console

    # tcset --device eth0 --delay 100

e.g. Set 0.1% packet loss
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: console

    # tcset --device eth0 --loss 0.1

e.g. All of the above at onece
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: console

    # tcset --device eth0 --rate 100k --delay 100 --loss 0.1

e.g. Specify the IP address of traffic control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: console

    # tcset --device eth0 --delay 100 --network 192.168.0.10

e.g. Specify the IP network and port of traffic control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: console

    # tcset --device eth0 --delay 100 --network 192.168.0.0/24 --port 80

Delete traffic control (tcdel)
------------------------------

tcdel is a command to delete traffic control from a network interface
(device).

tcdel help
~~~~~~~~~~

.. code:: console

    usage: tcdel [-h] [--version] [--logging] [--stacktrace] [--debug | --quiet]
                 --device DEVICE

    optional arguments:
      -h, --help       show this help message and exit
      --version        show program's version number and exit
      --debug          for debug print.
      --quiet          suppress output of execution log message.

    Miscellaneous:
      --logging        output execution log to a file (tcdel.log).
      --stacktrace     display stack trace when an error occurred.

    Traffic Control:
      --device DEVICE  network device name (e.g. eth0)

e.g.
~~~~

.. code:: console

    # tcdel --device eth0

Advanced usage
==============

Traffic control of incoming packets
-----------------------------------

Execute ``tcset`` command with ``--direction incoming`` option to set
incoming traffic control. Other options are the same as in the case of
the basic usage.

e.g. Set traffic control both incoming and outgoing network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: console

    tcset --device eth0 --direction outgoing --rate 200K --network 192.168.0.0/24
    tcset --device eth0 --direction incoming --rate 1M --network 192.168.0.0/24

Requirements
~~~~~~~~~~~~

Incoming packet traffic control requires additional ifb module, Which
need to the following conditions:

-  Equal or greater than Linux kernel version 2.6.20
-  Equal or newer than iproute2 package version 20070313

Dependencies
============

Linux package
-------------

-  iproute2 (reqrequired for tc commandured)

Python packagge
---------------

Dependency python packages are automatically installed during AAA
installation via pip.

-  `DataPropery <https://github.com/thombashi/DataProperty>`__
-  `ipaddress <https://pypi.python.org/pypi/ipaddress>`__
-  `six <https://pypi.python.org/pypi/six/>`__
-  `thutils <https://github.com/thombashi/thutils>`__

Test dependencies
~~~~~~~~~~~~~~~~~

-  `pingparsing <https://github.com/thombashi/pingparsing>`__
-  `pytest <https://pypi.python.org/pypi/pytest>`__
-  `pytest-runner <https://pypi.python.org/pypi/pytest-runner>`__
-  `tox <https://pypi.python.org/pypi/tox>`__
