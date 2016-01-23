tcconfig

.. image:: https://travis-ci.org/thombashi/tcconfig.svg?branch=master
    :target: https://travis-ci.org/thombashi/tcconfig

About
=====

tcconfig is a simple tc (traffic control) command wrapper.

Installation
============

.. code:: console

    pip install tcconfig

Usage
=====

Set traffic control
-------------------

Help
~~~~

.. code:: console

    usage: tcset [-h] [--version] [--time-measure] [--logging] [--stacktrace]
                 [--debug | --quiet] --device DEVICE [--rate RATE] [--delay DELAY]
                 [--loss LOSS] [--overwrite]

    optional arguments:
      -h, --help       show this help message and exit
      --version        show program's version number and exit
      --debug          for debug print.
      --quiet          suppress output of execution log message.

    Miscellaneous:
      --time-measure   measuring execution time.
      --logging        suppress output of execution log files.
      --stacktrace     display stack trace when an error occurred.

    Traffic Control:
      --device DEVICE  network device name
      --rate RATE      network bandwidth [K|M|G bps]
      --delay DELAY    round trip network delay [ms] (default=0)
      --loss LOSS      round trip packet loss rate [%] (default=0)
      --overwrite      overwrite existing setting

e.g. Set a limit on bandwidth up to 100Kbps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: console

    # tcset --device eth0 --rate 100k

e.g. Set 100ms network delay
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: console

    # tcset --device eth0 --delay 100

e.g. Set 0.1% packet loss
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: console

    # tcset --device eth0 --loss 0.1

Delete traffic control
----------------------

.. code:: console

    # tcdel --device eth0
