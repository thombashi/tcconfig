    .. note::

        ``tcdel`` will be deleted mangle tables in ``iptables``.
        (any other tables are not affected).


``tcdel`` command help
~~~~~~~~~~~~~~~~~~~~~~

::

    usage: tcdel [-h] [--version] [--debug | --quiet] --device DEVICE

.. option:: tcdel command options

    optional arguments:
      -h, --help       show this help message and exit
      --version        show program's version number and exit
      --debug          for debug print.
      --quiet          suppress execution log messages.

    Traffic Control:
      --device DEVICE  network device name (e.g. eth0)

