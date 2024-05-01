e.g. Set a limit on bandwidth up to 100Kbps
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: console

    # tcset eth0 --rate 100Kbps

e.g. Set network latency
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can use time units (such as us/sec/min/etc.) to designate delay time.

Set 100 milliseconds of network latency
'''''''''''''''''''''''''''''''''''''''''''''''''''
.. code-block:: console

    # tcset eth0 --delay 100ms


Set 10 seconds of network latency
'''''''''''''''''''''''''''''''''''''''''''''''''''
.. code-block:: console

    # tcset eth0 --delay 10sec

Set 0.5 minutes (30 seconds) network latency
'''''''''''''''''''''''''''''''''''''''''''''''''''
.. code-block:: console

    # tcset eth0 --delay 0.5min

You can also use the following time units:

.. table:: 

    +------------+----------------------------------------------------------+
    |    Unit    |                Available specifiers (str)                |
    +============+==========================================================+
    |hours       |``h``/``hour``/``hours``                                  |
    +------------+----------------------------------------------------------+
    |minutes     |``m``/``min``/``mins``/``minute``/``minutes``             |
    +------------+----------------------------------------------------------+
    |seconds     |``s``/``sec``/``secs``/``second``/``seconds``             |
    +------------+----------------------------------------------------------+
    |milliseconds|``ms``/``msec``/``msecs``/``millisecond``/``milliseconds``|
    +------------+----------------------------------------------------------+
    |microseconds|``us``/``usec``/``usecs``/``microsecond``/``microseconds``|
    +------------+----------------------------------------------------------+

e.g. Set 0.1% packet loss
^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: console

    # tcset eth0 --loss 0.1%

e.g. All of the above settings at once
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: console

    # tcset eth0 --rate 100Kbps --delay 100ms --loss 0.1%

e.g. Specify the IP address of the traffic control
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: console

    # tcset eth0 --delay 100ms --network 192.168.0.10

e.g. Specify the IP network and port of traffic control
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: console

    # tcset eth0 --delay 100ms --network 192.168.0.0/24 --port 80
