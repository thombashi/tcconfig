Installation
============

Installing from PyPI
------------------------------
``tcconfig`` can be installed from `PyPI <https://pypi.python.org/pypi>`__ via
`pip <https://pip.pypa.io/en/stable/installing/>`__ (Python package manager) command.

.. code:: console

    sudo pip install tcconfig


Installing from files
------------------------------
The following package include ``tcconfig`` and dependency packages.
This package is for environments which cannot access to 
`PyPI <https://pypi.python.org/pypi>`__ directly.

How to install:

1. Navigate to ``https://github.com/thombashi/tcconfig/releases/``
2. Download the latest version of ``tcconfig_wheel.tar.gz``
3. Copy ``tcconfig_wheel.tar.gz`` to installation target
4. ``tar xvf tcconfig_wheel.tar.gz``
5. ``cd tcconfig_wheel/``
6. ``./install.sh``


Dependencies
============

Linux packages
--------------
- `iproute`/`iproute2` (mandatory: required for tc command)
- `iptables` (optional: required to when you use ``--iptables`` option)

Linux kernel module
----------------------------
- sch_netem

Python packages
---------------
Dependency python packages are automatically installed during
``tcconfig`` installation via pip.

- `DataPropery <https://github.com/thombashi/DataProperty>`__
- `ipaddress <https://pypi.python.org/pypi/ipaddress>`__
- `logbook <http://logbook.readthedocs.io/en/stable/>`__
- `pyparsing <https://pyparsing.wikispaces.com/>`__
- `six <https://pypi.python.org/pypi/six/>`__
- `subprocrunner <https://github.com/thombashi/subprocrunner>`__
- `typepy <https://github.com/thombashi/typepy>`__
- `voluptuous <https://github.com/alecthomas/voluptuous>`__

Optional
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- `netifaces <https://bitbucket.org/al45tair/netifaces>`__
    - Suppress excessive error messages if this package is installed

Test dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- `allpairspy <https://github.com/thombashi/allpairspy>`__
- `pingparsing <https://github.com/thombashi/pingparsing>`__
- `pytest <http://pytest.org/latest/>`__
- `pytest-runner <https://pypi.python.org/pypi/pytest-runner>`__
- `tox <https://testrun.org/tox/latest/>`__
