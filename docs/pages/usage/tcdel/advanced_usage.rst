Advanced usage
~~~~~~~~~~~~~~
You can delete a specific shaping rule by either network specifier or ``filter_id``.

.. code-block:: console

    # tcset eth0 --delay 10ms --rate 10Kbps --network 192.168.1.2 --overwrite
    # tcset eth0 --delay 100ms --rate 50Kbps --network 192.168.1.3 --add
    # tcset eth0 --delay 200ms --rate 100Kbps --network 192.168.0.0/24 --add
    # tcshow eth0
    {
        "eth0": {
            "outgoing": {
                "dst-network=192.168.1.2/32, protocol=ip": {
                    "filter_id": "800::800",
                    "delay": "10.0ms",
                    "rate": "10Kbps"
                },
                "dst-network=192.168.1.3/32, protocol=ip": {
                    "filter_id": "800::801",
                    "delay": "100.0ms",
                    "rate": "50Kbps"
                },
                "dst-network=192.168.0.0/24, protocol=ip": {
                    "filter_id": "800::802",
                    "delay": "200.0ms",
                    "rate": "100Kbps"
                }
            },
            "incoming": {}
        }
    }

e.g. Delete a shaping rule with network specifier:

.. code-block:: console

    # tcdel eth0 --dst-network 192.168.1.2
    # tcshow eth0
    {
        "eth0": {
            "outgoing": {
                "dst-network=192.168.1.3/32, protocol=ip": {
                    "filter_id": "800::801",
                    "delay": "100.0ms",
                    "rate": "50Kbps"
                },
                "dst-network=192.168.0.0/24, protocol=ip": {
                    "filter_id": "800::802",
                    "delay": "200.0ms",
                    "rate": "100Kbps"
                }
            },
            "incoming": {}
        }
    }

e.g. Delete a shaping rule with filter id:

.. code-block:: console

    # tcdel eth0 --id 800::801
    # tcshow eth0
    {
        "eth0": {
            "outgoing": {
                "dst-network=192.168.0.0/24, protocol=ip": {
                    "filter_id": "800::802",
                    "delay": "200.0ms",
                    "rate": "100Kbps"
                }
            },
            "incoming": {}
        }
    }
