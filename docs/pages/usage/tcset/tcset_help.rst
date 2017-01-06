``tcset`` command help
~~~~~~~~~~~~~~~~~~~~~~

::

    usage: tcset [-h] [--version] [--logging] [--stacktrace] [--debug | --quiet]
                 (--device DEVICE | -f CONFIG_FILE) [--overwrite]
                 [--direction {outgoing,incoming}] [--rate BANDWIDTH_RATE]
                 [--delay NETWORK_LATENCY] [--delay-distro LATENCY_DISTRO_MS]
                 [--loss PACKET_LOSS_RATE] [--corrupt CORRUPTION_RATE]
                 [--network NETWORK] [--port PORT]

.. option:: tcset command options

    optional arguments:
      -h, --help            show this help message and exit
      --version             show program's version number and exit
      --debug               for debug print.
      --quiet               suppress execution log messages.
      --device DEVICE       network device name (e.g. eth0)
      -f CONFIG_FILE, --config-file CONFIG_FILE
                            setting traffic controls from a configuration file.
                            output file of the tcshow.

    Network Interface:
      --overwrite           overwrite existing settings

    Traffic Control:
      --direction {outgoing,incoming}
                            the direction of network communication that impose
                            traffic control. ``incoming`` requires linux kernel
                            version 2.6.20 or later. (default = ``outgoing``)
      --rate BANDWIDTH_RATE
                            network bandwidth rate [K|M|G bps]
      --delay NETWORK_LATENCY
                            round trip network delay [ms]. the valid range is 0 to
                            10000. (default=0)
      --delay-distro LATENCY_DISTRO_MS
                            distribution of network latency becomes X +- Y [ms]
                            (normal distribution), with this option. (X: value of
                            --delay option, Y: value of --delay-dist option)
                            network latency distribution will be uniform without
                            this option.
      --loss PACKET_LOSS_RATE
                            round trip packet loss rate [%]. the valid range is 0
                            to 100. (default=0)
      --corrupt CORRUPTION_RATE
                            packet corruption rate [%]. the valid range is 0 to
                            100. packet corruption means single bit error at a
                            random offset in the packet. (default=0)
      --network NETWORK     Target IP address/network of traffic control
      --port PORT           port number of traffic control
