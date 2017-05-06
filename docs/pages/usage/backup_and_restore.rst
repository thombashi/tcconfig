Backup and restore traffic control configurations
-------------------------------------------------

``tcshow`` command output can be used as a backup,
and ``tcset`` command can restore configurations from a backup.


e.g. Backup configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

    # tcset --device eth0 --delay 10 --delay-distro 2  --loss 0.01 --rate 0.25M --network 192.168.0.10 --port 8080
    # tcset --device eth0 --delay 1 --loss 0.02 --rate 500K --direction incoming
    # tcset --device eth1 --delay 2.5 --delay-distro 1.2 --loss 0.01 --rate 0.25M --port 80
    # tcset --device eth1 --corrupt 0.02 --rate 1.5M --direction incoming --network 192.168.10.0/24

Redirect configurations to the ``tcconfig.json`` file.

.. code-block:: console

    # tcshow --device eth0 --device eth1 > tcconfig.json


e.g. Restore configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before restore

.. code-block:: console

    # tcshow --device eth0 --device eth1
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

    # tcset -f tcconfig.json

After restore

.. code-block:: console

    # tcshow --device eth0 --device eth1
    {
        "eth1": {
            "outgoing": {
                "dst-port=80": {
                    "delay": "2.5",
                    "loss": "0.01",
                    "rate": "250K",
                    "delay-distro": "1.2"
                },
                "network=0.0.0.0/0": {}
            },
            "incoming": {
                "network=192.168.10.0/24": {
                    "corrupt": "0.02",
                    "rate": "1500K"
                },
                "network=0.0.0.0/0": {}
            }
        },
        "eth0": {
            "outgoing": {
                "network=192.168.0.10/32, dst-port=8080": {
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
    