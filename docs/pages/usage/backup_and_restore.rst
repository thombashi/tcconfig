Backup and restore traffic control configurations
-------------------------------------------------

``tcshow`` command output can be used as a backup,
and ``tcset`` command can restore configurations from a backup.


e.g. Backup configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

    # tcset eth0 --delay 10ms --delay-distro 2  --loss 0.01% --rate 0.25Mbps --network 192.168.0.10 --port 8080
    # tcset eth0 --delay 1ms --loss 0.02% --rate 500Kbps --direction incoming
    # tcset eth1 --delay 2.5ms --delay-distro 1.2 --loss 0.01% --rate 0.25Mbps --port 80
    # tcset eth1 --corrupt 0.02% --rate 1.5Mbps --direction incoming --network 192.168.10.0/24

Redirect configurations to the ``tcconfig.json`` file.

.. code-block:: console

    # tcshow eth0 eth1 > tcconfig.json


e.g. Restore configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before restore

.. code-block:: console

    # tcshow eth0 eth1
    {
        "eth1": {
            "outgoing": {},
            "incoming": {}
        },
        "eth0": {
            "outgoing": {},
            "incoming": {}
        }
    }

Restore from a configuration file (``tcconfig.json``).

.. code-block:: console

    # tcset tcconfig.json --import-setting

After restore

.. code-block:: console

    # tcshow eth0 eth1
    {
        "eth1": {
            "outgoing": {
                "dst-port=80, protocol=ip": {
                    "filter_id": "800::800",
                    "delay": "2.5ms",
                    "delay-distro": "1.2ms",
                    "loss": "0.01%",
                    "rate": "250Kbps"
                }
            },
            "incoming": {
                "dst-network=192.168.10.0/24, protocol=ip": {
                    "filter_id": "800::800",
                    "corrupt": "0.02%",
                    "rate": "1500Kbps"
                }
            }
        },
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
