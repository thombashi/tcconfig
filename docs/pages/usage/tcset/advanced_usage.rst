Advanced usage
~~~~~~~~~~~~~~

Traffic control of incoming packets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Execute ``tcset`` command with ``--direction incoming`` option to set
incoming traffic control. Other options are the same as in the case of
the basic usage.

e.g. Set traffic control both incoming and outgoing network
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. code-block:: console

    # tcset --device eth0 --direction outgoing --rate 200K --network 192.168.0.0/24
    # tcset --device eth0 --direction incoming --rate 1M --network 192.168.0.0/24

Requirements
''''''''''''

Incoming packet traffic control requires additional ``ifb`` module, Which
need to the following conditions:

-  Equal or later than Linux kernel version **2.6.20**
-  Equal or later than ``iproute2`` package version **20070313**

e.g. Set 100ms +- 20ms network latency with normal distribution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

    # tcset --device eth0 --delay 100 --delay-distro 20


Multiple traffic shaping rules per interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

    tcset --device eth0 --rate 500M --network 192.168.2.0/24
    tcset --device eth0 --rate 100M --network 192.168.0.0/24 --add
