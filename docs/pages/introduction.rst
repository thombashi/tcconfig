tcconfig
========

.. image:: https://img.shields.io/pypi/pyversions/tcconfig.svg
   :target: https://pypi.python.org/pypi/tcconfig
.. image:: https://travis-ci.org/thombashi/tcconfig.svg?branch=master
   :target: https://travis-ci.org/thombashi/tcconfig


Summary
-------

``tcconfig`` is a Simple tc command wrapper.
Easy to set up traffic control of network bandwidth/latency/packet-loss to a network interface.


Feature
-------

- Automatic table creation from data
- Support various data types of record(s) insertion into a table:
    - dictionary
    - namedtuple
    - list
    - tuple
- Create a table from a csv file

