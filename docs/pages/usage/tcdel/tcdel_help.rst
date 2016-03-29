``tcdel`` command help
~~~~~~~~~~~~~~~~~~~~~~

::

    usage: tcdel [-h] [--version] [--logging] [--stacktrace] [--debug | --quiet]
                 --device DEVICE

.. option:: tcdel command options

    optional arguments:
      -h, --help       show this help message and exit
      --version        show program's version number and exit
      --debug          for debug print.
      --quiet          suppress output of execution log message.

    Miscellaneous:
      --logging        output execution log to a file (tcdel.log).
      --stacktrace     display stack trace when an error occurred.

    Traffic Control:
      --device DEVICE  network device name (e.g. eth0)
