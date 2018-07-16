Advanced usage
~~~~~~~~~~~~~~
You can delete a specific shaping rule by either network specifier or ``filter_id``.

.. code-block:: console

    # tcset ens33 --delay 10 --rate 10k --network 192.168.1.2 --overwrite
    # tcset ens33 --delay 100 --rate 50k --network 192.168.1.3 --add
    # tcset ens33 --delay 200 --rate 100k --network 192.168.0.0/24 --add
    # tcshow ens33
    {
        "ens33": {
            "outgoing": {
                "dst-network=192.168.1.2/32, protocol=ip": {
                    "delay": 10,
                    "rate": "10K",
                    "filter_id": "800::800"
                },
                "dst-network=192.168.0.0/24, protocol=ip": {
                    "delay": 200,
                    "rate": "100K",
                    "filter_id": "800::802"
                },
                "dst-network=192.168.1.3/32, protocol=ip": {
                    "delay": 100,
                    "rate": "50K",
                    "filter_id": "800::801"
                }
            },
            "incoming": {}
        }
    }

e.g. Delete a shaping rule with network specifier:

.. code-block:: console

    # tcdel ens33 --dst-network 192.168.1.2
    # tcshow ens33
    {
        "ens33": {
            "outgoing": {
                "dst-network=192.168.0.0/24, protocol=ip": {
                    "delay": 200,
                    "rate": "100K",
                    "filter_id": "800::802"
                },
                "dst-network=192.168.1.3/32, protocol=ip": {
                    "delay": 100,
                    "rate": "50K",
                    "filter_id": "800::801"
                }
            },
            "incoming": {}
        }
    }

e.g. Delete a shaping rule with filter id:

.. code-block:: console

    # tcdel ens33 --id 800::801
    # tcshow ens33
    {
        "ens33": {
            "outgoing": {
                "dst-network=192.168.0.0/24, protocol=ip": {
                    "delay": 200,
                    "rate": "100K",
                    "filter_id": "800::802"
                }
            },
            "incoming": {}
        }
    }
