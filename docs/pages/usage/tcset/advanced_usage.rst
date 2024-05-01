Advanced usage
~~~~~~~~~~~~~~

Traffic control of incoming packets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can set traffic shaping rules to incoming packets by executing ``tcset`` command with ``--direction incoming`` option.
Other options are the same as in the case of the basic usage.

e.g. Set traffic control for both incoming and outgoing network
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
.. code-block:: console

    # tcset eth0 --direction outgoing --rate 200Kbps --network 192.168.0.0/24
    # tcset eth0 --direction incoming --rate 1Mbps --network 192.168.0.0/24

Requirements
''''''''''''
To set incoming packet traffic control requires an additional kernel module named ``ifb``,
which need the following conditions:

-  Equal or later than Linux kernel version **2.6.20**
-  Equal or later than ``iproute2`` package version **20070313**


Set latency distribution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Network latency setting by ``--delay`` option is a uniform distribution.
If you are using ``--delay-distro`` option, latency is decided by a normal distribution.

e.g. Set 100ms +- 20ms network latency with normal distribution
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
.. code-block:: console

    # tcset eth0 --delay 100ms --delay-distro 20


Set multiple traffic shaping rules to an interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can set multiple shaping rules to a network interface with ``--add`` option.

.. code-block:: console

    tcset eth0 --rate 500Mbps --network 192.168.2.1/32
    tcset eth0 --rate 100Mbps --network 192.168.2.2/32 --add


Using IPv6
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
IPv6 addresses can be used at ``tcset``/``tcshow`` commands with ``--ipv6`` option.

.. code-block:: console

    # tcset eth0 --delay 100ms --network 2001:db00::0/24 --ipv6
    # tcshow eth0 --ipv6
    {
        "eth0": {
            "outgoing": {
                "dst-network=2001:db00::/24, protocol=ipv6": {
                    "filter_id": "800::800",
                    "delay": "100.0ms",
                    "rate": "1Gbps"
                }
            },
            "incoming": {}
        }
    }


Get ``tc`` commands
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can get ``tc`` commands to be executed by ``tcconfig`` commands by
executing with ``--tc-command`` option
(Execution of ``tcconfig`` commands with ``--tc-command`` option does not affect the traffic rules to the server).

:Example:
    .. code-block:: console

        $ tcset eth0 --delay 10ms --tc-command
        /sbin/tc qdisc add dev eth0 root handle 1a1a: htb default 1
        /sbin/tc class add dev eth0 parent 1a1a: classid 1a1a:1 htb rate 1000000kbit
        /sbin/tc class add dev eth0 parent 1a1a: classid 1a1a:254 htb rate 1000000Kbit ceil 1000000Kbit
        /sbin/tc qdisc add dev eth0 parent 1a1a:254 handle 2873: netem delay 10ms
        /sbin/tc filter add dev eth0 protocol ip parent 1a1a: prio 2 u32 match ip dst 0.0.0.0/0 match ip src 0.0.0.0/0 flowid 1a1a:254



Generate a ``tc`` script file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
``--tc-script`` option generates an executable script which includes
tc commands to be executed by ``tcconfig`` commands.
The created script can execute at other servers where tcconfig is not installed
(However, you need the tc command to run the script).

:Example:
    .. code-block:: console

        $ tcset eth0 --delay 10ms --tc-script
        [INFO] tcconfig: written a tc script to 'tcset_eth0_delay10ms.sh'

        (copy the script to a remote server)
        $ sudo ./tcset_eth0_delay10ms.sh


Set a shaping rule for multiple destinations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Example Environment
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Multiple hosts (``A``, ``B``, ``C``, ``D``) are on the same network.

.. code-block:: console

    A (192.168.0.100) --+--B (192.168.0.2)
                        |
                        +--C (192.168.0.3)
                        |
                        +--D (192.168.0.4)

Set a shaping rule to multiple hosts
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
``--dst-network``/``--src-network`` option can specify not only a host but also network.
The following command executed at host ``A`` will set a shaping rule that incurs 100 msec network latency to packets
from ``A (192.168.0.100)`` to a specific network (``192.168.0.0/28`` which include ``B``/``C``/``D``).

:Example:
    .. code-block:: console

        # tcset eth0 --dst-network 192.168.0.0/28 --exclude-dst-network 192.168.0.3 --delay 100ms

You can exclude hosts from shaping rules by ``--exclude-dst-network``/``--exclude-src-network`` option.
The following command executed at host ``A`` will set a shaping rule that incurs 100 msec network latency to packets
from host ``A (192.168.0.100)`` to host ``B (192.168.0.2)``/``D (192.168.0.4)``.

:Example:
    .. code-block:: console

        # tcset eth0 --dst-network 192.168.0.0/28 --exclude-dst-network 192.168.0.3 --delay 100ms


Shaping rules between multiple hosts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Example Environment
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Existed multiple networks (``192.168.0.0/24``, ``192.168.1.0/24``).
Host ``A (192.168.0.100)`` and host ``C (192.168.1.10)`` belong to a different network.
Host ``B (192.168.0.2/192.168.1.2)`` belong to both networks.

.. code-block:: console

    A (192.168.0.100) -- (192.168.0.2) B (192.168.1.2) -- C (192.168.1.10)

Set a shaping rule to multiple hosts
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
The following command executed at host ``B`` will set a shaping rule that incurs 100 msec network latency to packets
only from host ``A (192.168.0.100)`` to host ``C (192.168.1.10)``.

:Example:
    .. code-block:: console

        # tcset eth0 --dst-network 192.168.0.2 --dst-network 192.168.1.2 --delay 100ms
