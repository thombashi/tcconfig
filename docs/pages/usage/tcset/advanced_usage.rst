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


Set latency distribution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Latency setting by ``--delay`` option is a uniform distribution.
If you are using ``--delay-distro`` option, latency decided by a normal distribution.

e.g. Set 100ms +- 20ms network latency with normal distribution
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
.. code-block:: console

    # tcset --device eth0 --delay 100 --delay-distro 20



Multiple traffic shaping rules per interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can set multiple shaping rules to a network interface with ``--add`` option.

.. code-block:: console

    tcset --device eth0 --rate 500M --network 192.168.2.0/24
    tcset --device eth0 --rate 100M --network 192.168.0.0/24 --add


Using IPv6
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
IPv6 addresses can be used at ``tcset``/``tcshow`` commands with ``--ipv6`` option.

.. code-block:: console

    # tcset --device eth0 --delay 100 --network 2001:db00::0/24 --ipv6
    # tcshow --device eth0 --ipv6
    {
        "eth0": {
            "outgoing": {
                "dst-network=2001:db00::/24, protocol=ipv6": {
                    "delay": "100.0",
                    "rate": "1G"
                }
            },
            "incoming": {}
        }
    }


Get ``tc`` commands
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can get ``tc`` commands to be executed by ``tcconfig`` commands by
executing with ``--tc-command`` option
(no tc configuration have made to the execution server by this command).

:Example:

    .. code-block:: console

        # tcset --device eth0 --delay 10 --tc-command
        tc qdisc add dev eth0 root handle 1f87: htb default 1
        tc class add dev eth0 parent 1f87: classid 1f87:1 htb rate 1000000kbit
        tc class add dev eth0 parent 1f87: classid 1f87:2 htb rate 1000000Kbit ceil 1000000Kbit
        tc qdisc add dev eth0 parent 1f87:2 handle 2007: netem delay 10.0ms
        tc filter add dev eth0 protocol ip parent 1f87: prio 1 u32 match ip dst 0.0.0.0/0 flowid 1f87:2


Generate a ``tc`` script file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
``--tc-script`` option generates an executable script which includes
tc commands to be executed by tcconfig commands.
The created script can execute at other servers where tcconfig not installed (however, you need the tc command to run the script).

:Example:
    .. code-block:: console

        # tcset --device eth0 --delay 10 --tc-script
        [INFO] tcconfig: written a tc script to 'tcset_eth0.sh'
        # ./tcset_eth0.sh
