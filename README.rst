.. contents:: **tcconfig**
   :backlinks: top
   :depth: 2

Summary
=========
`tcconfig <https://github.com/thombashi/tcconfig>`__ is a tc command wrapper. Make it easy to set up traffic control of network bandwidth/latency/packet-loss/packet-corruption/etc. to a network-interface/Docker-container(veth).

|PyPI pkg ver| |Supported Python ver| |CI status| |CodeQL|

.. |PyPI pkg ver| image:: https://badge.fury.io/py/tcconfig.svg
    :target: https://badge.fury.io/py/tcconfig
    :alt: PyPI package version

.. |Supported Python ver| image:: https://img.shields.io/pypi/pyversions/tcconfig.svg
    :target: https://pypi.org/project/tcconfig
    :alt: Supported Python versions

.. |CI status| image:: https://github.com/thombashi/tcconfig/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/thombashi/tcconfig/actions/workflows/ci.yml
    :alt: Test CI status

.. |CodeQL| image:: https://github.com/thombashi/tcconfig/actions/workflows/build_and_release.yml/badge.svg
   :target: https://github.com/thombashi/tcconfig/actions/workflows/build_and_release.yml
   :alt: Build CI status

Traffic control
------------------------

Setup traffic shaping rules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Easy to apply traffic shaping rules to specific networks:

- Outgoing/Incoming packets
- Source/Destination IP-address/network (IPv4/IPv6)
- Source/Destination ports

Available Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The following parameters can be set to network interfaces:

- Network bandwidth rate ``[G/M/K bps]``
- Network latency ``[microseconds/milliseconds/seconds/minutes]``
- Packet loss rate ``[%]``
- Packet corruption rate ``[%]``
- Packet duplicate rate ``[%]``
- Packet reordering rate  ``[%]``
- Packet limit count  ``[COUNT]``

Targets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Network interfaces: e.g. ``eth0``
- Docker container (``veth`` corresponding with a container)

.. image:: docs/gif/tcset_example.gif

Usage
=======
Set traffic control (``tcset`` command)
-----------------------------------------
``tcset`` is a command to add a traffic control rule to a network interface (device).

e.g. Set a limit on bandwidth up to 100Kbps
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: console

    # tcset eth0 --rate 100Kbps

e.g. Set network latency
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can use time units (such as us/sec/min/etc.) to designate delay time.

Set 100 milliseconds of network latency
'''''''''''''''''''''''''''''''''''''''''''''''''''
.. code-block:: console

    # tcset eth0 --delay 100ms


Set 10 seconds of network latency
'''''''''''''''''''''''''''''''''''''''''''''''''''
.. code-block:: console

    # tcset eth0 --delay 10sec

Set 0.5 minutes (30 seconds) network latency
'''''''''''''''''''''''''''''''''''''''''''''''''''
.. code-block:: console

    # tcset eth0 --delay 0.5min

You can also use the following time units:

.. table::

    +------------+----------------------------------------------------------+
    |    Unit    |                Available specifiers (str)                |
    +============+==========================================================+
    |hours       |``h``/``hour``/``hours``                                  |
    +------------+----------------------------------------------------------+
    |minutes     |``m``/``min``/``mins``/``minute``/``minutes``             |
    +------------+----------------------------------------------------------+
    |seconds     |``s``/``sec``/``secs``/``second``/``seconds``             |
    +------------+----------------------------------------------------------+
    |milliseconds|``ms``/``msec``/``msecs``/``millisecond``/``milliseconds``|
    +------------+----------------------------------------------------------+
    |microseconds|``us``/``usec``/``usecs``/``microsecond``/``microseconds``|
    +------------+----------------------------------------------------------+

e.g. Set 0.1% packet loss
^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: console

    # tcset eth0 --loss 0.1%

e.g. All of the above settings at once
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: console

    # tcset eth0 --rate 100Kbps --delay 100ms --loss 0.1%

e.g. Specify the IP address of the traffic control
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: console

    # tcset eth0 --delay 100ms --network 192.168.0.10

e.g. Specify the IP network and port of traffic control
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: console

    # tcset eth0 --delay 100ms --network 192.168.0.0/24 --port 80

Set traffic control to a docker container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Execute ``tcconfig`` with ``--docker`` option on a Docker host:

.. code-block:: console

    # tcset <container name or ID> --docker ...

You could use ``--src-container``/``--dst-container`` options to specify the source/destination container.


Set traffic control within a docker container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You need to run a container with ``--cap-add NET_ADMIN`` option
if you would like to set a tc rule within a container:

.. code-block:: console

    docker run -d --cap-add NET_ADMIN -t <docker image>

A container image that builtin tcconfig can be available at https://hub.docker.com/r/thombashi/tcconfig/

Delete traffic control (``tcdel`` command)
------------------------------------------
``tcdel`` is a command to delete traffic shaping rules from a network interface (device).

e.g. Delete traffic control of ``eth0``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can delete all of the shaping rules for the ``eth0`` with ``-a``/``--all`` option:

.. code-block:: console

    # tcdel eth0 --all

Display traffic control configurations (``tcshow`` command)
-----------------------------------------------------------
``tcshow`` is a command to display the current traffic control settings for network interface(s).

Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

    # tcset eth0 --delay 10ms --delay-distro 2  --loss 0.01% --rate 0.25Mbps --network 192.168.0.10 --port 8080
    # tcset eth0 --delay 1ms --loss 0.02% --rate 500Kbps --direction incoming
    # tcshow eth0
    {
        "eth0": {
            "outgoing": {
                "dst-network=192.168.0.10/32, dst-port=8080, protocol=ip": {
                    "filter_id": "800::800",
                    "delay": "10.0ms",
                    "delay-distro": "2.0ms",
                    "loss": "0.01%",
                    "rate": "250Kbps"
                }
            },
            "incoming": {
                "protocol=ip": {
                    "filter_id": "800::800",
                    "delay": "1.0ms",
                    "loss": "0.02%",
                    "rate": "500Kbps"
                }
            }
        }
    }

For more information
----------------------
More examples are available at 
https://tcconfig.rtfd.io/en/latest/pages/usage/index.html



Installation
============
Installation: pip
------------------------------
``tcconfig`` can be installed from `PyPI <https://pypi.python.org/pypi>`__ via
`pip <https://pip.pypa.io/en/stable/installing/>`__ (Python package manager) command.

.. code:: console

    sudo pip install tcconfig


Installation: dpkg (Debian/Ubuntu)
--------------------------------------------
.. code:: console

    curl -sSL https://raw.githubusercontent.com/thombashi/tcconfig/master/scripts/installer.sh | sudo bash


Dependencies
============
- Python 3.9+
- `Python package dependencies (automatically installed) <https://github.com/thombashi/tcconfig/network/dependencies>`__

Linux packages
--------------
- mandatory: required for ``tc`` command:
    - `Ubuntu`/`Debian`: ``iproute2``
    - `Fedora`/`RHEL`: ``iproute-tc``
- optional: required when you use the ``--iptables`` option:
    - ``iptables``

Linux kernel module
----------------------------
- ``sch_netem``

Optional Python packages
----------------------------
- `Pygments <http://pygments.org/>`__

Documentation
===============
https://tcconfig.rtfd.io/

Troubleshooting
=================
https://tcconfig.rtfd.io/en/latest/pages/troubleshooting.html

Docker image
==============
https://hub.docker.com/r/thombashi/tcconfig/

Sponsors
====================================
|chasbecker| |shiguredo| |b4tman| |Arturi0| |github|

.. |chasbecker| image:: https://avatars.githubusercontent.com/u/44389260?s=48&u=6da7176e51ae2654bcfd22564772ef8a3bb22318&v=4
   :target: https://github.com/chasbecker
   :alt: ex-sponsor: Charles Becker (chasbecker)
.. |shiguredo| image:: https://avatars.githubusercontent.com/u/2549434?s=48&v=4
   :target: https://github.com/shiguredo
   :alt: ex-sponsor: 時雨堂 (shiguredo)
.. |b4tman| image:: https://avatars.githubusercontent.com/u/3658062?s=48&v=4
   :target: https://github.com/b4tman
   :alt: onetime: Dmitry Belyaev (b4tman)
.. |Arturi0| image:: https://avatars.githubusercontent.com/u/46711571?s=48&u=57687c0e02d5d6e8eeaf9177f7b7af4c9f275eb5&v=4
   :target: https://github.com/Arturi0
   :alt: onetime: Arturi0
.. |github| image:: https://avatars.githubusercontent.com/u/9919?s=48&v=4
   :target: https://github.com/github
   :alt: onetime: GitHub (github)

`Become a sponsor <https://github.com/sponsors/thombashi>`__

