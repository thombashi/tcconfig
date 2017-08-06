tcconfig
========

.. image:: https://travis-ci.org/thombashi/tcconfig.svg?branch=master
   :target: https://travis-ci.org/thombashi/tcconfig
   :alt: Linux CI test status

.. image:: https://img.shields.io/github/stars/thombashi/tcconfig.svg?style=social&label=Star
   :target: https://github.com/thombashi/tcconfig
   :alt: GitHub repository

Summary
-------

A Simple tc command wrapper tool. Easy to set up traffic control of network bandwidth/latency/packet loss/packet-corruption to a network interface.

Traffic control features
------------------------

Traffic shaping target
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Apply traffic shaping rules to specific targets:

- Outgoing/Incoming packets
- Source/Destination IP-address/network (IPv4/IPv6)
- Source/Destination ports

Moreover, exclude from shaping rules from specific targets:

- Source/Destination IP-address/network (IPv4/IPv6)
- Source/Destination ports

Available parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The following parameters can set to network interfaces:

- Network bandwidth rate ``[G/M/K bps]``
- Network latency ``[milliseconds]``
- Packet loss rate ``[%]``
- Packet corruption rate ``[%]``
- Packet duplicate rate ``[%]``
- Packet reordering rate  ``[%]``

.. image:: docs/gif/tcset_example.gif

Usage
=====

Set traffic control (``tcset`` command)
---------------------------------------

``tcset`` is a command to add traffic control rule to a network interface (device).

e.g. Set a limit on bandwidth up to 100Kbps
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code:: console

    # tcset --device eth0 --rate 100k

e.g. Set 100ms network latency
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code:: console

    # tcset --device eth0 --delay 100

e.g. Set 0.1% packet loss
^^^^^^^^^^^^^^^^^^^^^^^^^
.. code:: console

    # tcset --device eth0 --loss 0.1

e.g. All of the above at once
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code:: console

    # tcset --device eth0 --rate 100k --delay 100 --loss 0.1

e.g. Specify the IP address of traffic control
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code:: console

    # tcset --device eth0 --delay 100 --network 192.168.0.10

e.g. Specify the IP network and port of traffic control
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code:: console

    # tcset --device eth0 --delay 100 --network 192.168.0.0/24 --port 80

Delete traffic control (``tcdel`` command)
------------------------------------------

``tcdel`` is a command to delete traffic shaping rules from a network interface (device).

e.g. Delete traffic control of ``eth0``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: console

    # tcdel --device eth0


Display traffic control configurations (``tcshow`` command)
-----------------------------------------------------------
``tcshow`` is a command to display the current traffic control settings for network interface(s).

Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: console

    # tcset --device eth0 --delay 10 --delay-distro 2  --loss 0.01 --rate 0.25M --network 192.168.0.10 --port 8080
    # tcset --device eth0 --delay 1 --loss 0.02 --rate 500K --direction incoming
    # tcshow --device eth0
    {
        "eth0": {
            "outgoing": {
                "dst-network=192.168.0.10/32, dst-port=8080": {
                    "delay": "10.0",
                    "loss": "0.01",
                    "rate": "250K",
                    "delay-distro": "2.0"
                },
                "dst-network=0.0.0.0/0": {}
            },
            "incoming": {
                "dst-network=0.0.0.0/0": {
                    "delay": "1.0",
                    "loss": "0.02",
                    "rate": "500K"
                }
            }
        }
    }

For more information
--------------------

More examples are available at 
http://tcconfig.rtfd.io/en/latest/pages/usage/index.html

Installation
============

Installing from PyPI
------------------------------
``tcconfig`` can be installed from `PyPI <https://pypi.python.org/pypi>`__ via
`pip <https://pip.pypa.io/en/stable/installing/>`__ (Python package manager) command.

.. code:: console

    sudo pip install tcconfig


Installing from files
------------------------------
The following package includes ``tcconfig`` and dependency packages.
This package is for environments which cannot access to
`PyPI <https://pypi.python.org/pypi>`__ directly.

How to install:

1. Navigate to ``https://github.com/thombashi/tcconfig/releases/``
2. Download the latest version of ``tcconfig_wheel.tar.gz``
3. Copy ``tcconfig_wheel.tar.gz`` to installation target
4. ``tar xvf tcconfig_wheel.tar.gz``
5. ``cd tcconfig_wheel/``
6. ``./install.sh``


Dependencies
============

Linux packages
--------------
- ``iproute``/``iproute2``/``iproute-tc`` (mandatory: required for ``tc`` command)
- ``iptables`` (optional: required to when you use ``--iptables`` option)

Linux kernel module
----------------------------
- ``sch_netem``

Python packages
---------------
Dependency python packages are automatically installed during
``tcconfig`` installation via pip.

- `DataPropery <https://github.com/thombashi/DataProperty>`__
- `ipaddress <https://pypi.python.org/pypi/ipaddress>`__
- `logbook <http://logbook.readthedocs.io/en/stable/>`__
- `pyparsing <https://pyparsing.wikispaces.com/>`__
- `six <https://pypi.python.org/pypi/six/>`__
- `subprocrunner <https://github.com/thombashi/subprocrunner>`__
- `typepy <https://github.com/thombashi/typepy>`__
- `voluptuous <https://github.com/alecthomas/voluptuous>`__

Optional
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- `netifaces <https://bitbucket.org/al45tair/netifaces>`__
    - Suppress excessive error messages if this package installed

Test dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- `allpairspy <https://github.com/thombashi/allpairspy>`__
- `pingparsing <https://github.com/thombashi/pingparsing>`__
- `pytest <http://pytest.org/latest/>`__
- `pytest-runner <https://pypi.python.org/pypi/pytest-runner>`__
- `tox <https://testrun.org/tox/latest/>`__

Documentation
=============

http://tcconfig.rtfd.io/

Troubleshooting
===============

http://tcconfig.readthedocs.io/en/latest/pages/troubleshooting.html

