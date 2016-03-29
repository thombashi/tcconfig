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

.. image:: docs/gif/tcset_example.gif

Usage
=====

Set traffic control (``tcset`` command)
---------------------------------------

``tcset`` is a command to impose traffic control to a network interface (device).

e.g. Set a limit on bandwidth up to 100Kbps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

    # tcset --device eth0 --rate 100k

e.g. Set 100ms network latency
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

    # tcset --device eth0 --delay 100

e.g. Set 0.1% packet loss
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

    # tcset --device eth0 --loss 0.1

e.g. All of the above at once
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

    # tcset --device eth0 --rate 100k --delay 100 --loss 0.1

e.g. Specify the IP address of traffic control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

    # tcset --device eth0 --delay 100 --network 192.168.0.10

e.g. Specify the IP network and port of traffic control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

    # tcset --device eth0 --delay 100 --network 192.168.0.0/24 --port 80

Delete traffic control (``tcdel`` command)
------------------------------------------

``tcdel`` is a command to delete traffic control from a network
interface (device).

e.g. Delete traffic control of eth0
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

    # tcdel --device eth0


Display traffic control configurations (``tcshow`` command)
-----------------------------------------------------------

``tcshow`` is a command to display traffic control to network interface(s).

Example
~~~~~~~

.. code-block:: console

    # tcset --device eth0 --delay 10 --delay-distro 2  --loss 0.01 --rate 0.25M --network 192.168.0.10 --port 8080
    # tcset --device eth0 --delay 1 --loss 0.02 --rate 500K --direction incoming
    # tcshow --device eth0
    {
        "eth0": {
            "outgoing": {
                "network=192.168.0.10/32, port=8080": {
                    "delay": "10.0",
                    "loss": "0.01",
                    "rate": "250K",
                    "delay-distro": "2.0"
                },
                "network=0.0.0.0/0": {}
            },
            "incoming": {
                "network=0.0.0.0/0": {
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
http://tcconfig.readthedocs.org/en/latest/pages/usage/index.html


Installation
============

Install via pip
---------------

``tcconfig`` can be installed via
`pip <https://pip.pypa.io/en/stable/installing/>`__ (Python package manager).

.. code:: console

    sudo pip install tcconfig


Dependencies
============

Linux package
-------------

-  iproute2 (reqrequired for tc commandured)

Python packagge
---------------

Dependency python packages are automatically installed during
``tcconfig`` installation via pip.

-  `DataPropery <https://github.com/thombashi/DataProperty>`__
-  `ipaddress <https://pypi.python.org/pypi/ipaddress>`__
-  `pyparsing <https://pyparsing.wikispaces.com/>`__
-  `six <https://pypi.python.org/pypi/six/>`__
-  `thutils <https://github.com/thombashi/thutils>`__

Test dependencies
~~~~~~~~~~~~~~~~~

-  `pingparsing <https://github.com/thombashi/pingparsing>`__
-  `pytest <http://pytest.org/latest/>`__
-  `pytest-runner <https://pypi.python.org/pypi/pytest-runner>`__
-  `tox <https://testrun.org/tox/latest/>`__

Documentation
=============

http://tcconfig.readthedocs.org/en/latest/

