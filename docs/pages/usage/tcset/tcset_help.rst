``tcset`` command help
~~~~~~~~~~~~~~~~~~~~~~

::

    usage: tcset [-h] [--version] [--debug | --quiet]
                 (--device DEVICE | -f CONFIG_FILE) [--overwrite | --add]
                 [--direction {outgoing,incoming}] [--rate BANDWIDTH_RATE]
                 [--delay NETWORK_LATENCY] [--delay-distro LATENCY_DISTRO_MS]
                 [--loss PACKET_LOSS_RATE] [--corrupt CORRUPTION_RATE]
                 [--network NETWORK] [--port PORT] [--shaping-algo {tbf,htb}]
                 [--iptables] [--src-network SRC_NETWORK]

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
      --overwrite           overwrite existing settings
      --add                 add a traffic shaping rule in addition to existing
                            rules.

    Traffic Control:
      --direction {outgoing,incoming}
                            the direction of network communication that impose
                            traffic control. ``incoming`` requires Linux kernel
                            version 2.6.20 or later. (default = ``outgoing``)
      --rate BANDWIDTH_RATE
                            network bandwidth rate [K|M|G bit per second]
      --delay NETWORK_LATENCY
                            round trip network delay [ms]. the valid range is 0 to
                            3600000. (default=0)
      --delay-distro LATENCY_DISTRO_MS
                            distribution of network latency becomes X +- Y [ms]
                            (normal distribution). Here X is the value of --delay
                            option and Y is the value of --delay-dist option).
                            network latency distribution will be uniform without
                            this option.
      --loss PACKET_LOSS_RATE
                            round trip packet loss rate [%]. the valid range is 0
                            to 100. (default=0)
      --corrupt CORRUPTION_RATE
                            packet corruption rate [%]. the valid range is 0 to
                            100. packet corruption means single bit error at a
                            random offset in the packet. (default=0)
      --network NETWORK     target IP address/network to control traffic
      --port PORT           target port number to control traffic.
      --shaping-algo {tbf,htb}
                            shaping algorithm. defaults to htb (recommended).

    Routing:
      --iptables            use iptables to traffic shaping.
      --src-network SRC_NETWORK
                            set traffic shaping rule to a specific packets that
                            routed from --src-network to --network. This option
                            required to execute with the --iptables option. the
                            shaping rule only affect to outgoing packets (no
                            effect to if you execute with "--direction incoming"
                            option)
