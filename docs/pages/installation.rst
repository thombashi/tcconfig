Installation
============
Installation: pip
------------------------------
``tcconfig`` can be installed from `PyPI <https://pypi.python.org/pypi>`__ via
`pip <https://pip.pypa.io/en/stable/installing/>`__ (Python package manager) command.

.. code:: console

    sudo pip install tcconfig


Installation: dpkg (Debian/Ubuntu)
--------------------------------------------
.. code:: console

    curl -sSL https://raw.githubusercontent.com/thombashi/tcconfig/master/scripts/installer.sh | sudo bash


Dependencies
============
Python 3.5+

Linux packages
--------------
- mandatory: required for ``tc`` command:
    - `Ubuntu`/`Debian`: ``iproute2``
    - `Fedora`/`RHEL`: ``iproute-tc``
- optional: required to when you use ``--iptables`` option:
    - ``iptables``

Linux kernel module
----------------------------
- ``sch_netem``

Python packages
---------------
Dependency python packages are automatically installed during
``tcconfig`` installation via pip.

- `DataProperty <https://github.com/thombashi/DataProperty>`__
- `docker <https://github.com/docker/docker-py>`__
- `humanreadable <https://github.com/thombashi/humanreadable>`__
- `loguru <https://github.com/Delgan/loguru>`__
- `msgfy <https://github.com/thombashi/msgfy>`__
- `pyparsing <https://github.com/pyparsing/pyparsing>`__
- `pyroute2 <https://github.com/svinota/pyroute2>`__
- `subprocrunner <https://github.com/thombashi/subprocrunner>`__
- `typepy <https://github.com/thombashi/typepy>`__
- `voluptuous <https://github.com/alecthomas/voluptuous>`__

Optional Python packages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- `Pygments <http://pygments.org/>`__

Test dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- `allpairspy <https://github.com/thombashi/allpairspy>`__
- `pingparsing <https://github.com/thombashi/pingparsing>`__
- `pytest <https://docs.pytest.org/en/latest/>`__
- `tox <https://testrun.org/tox/latest/>`__
