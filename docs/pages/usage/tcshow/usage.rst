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
