Installation
============

Install via pip
---------------

``tcconfig`` can be installed via
`pip <https://pip.pypa.io/en/stable/installing/>`__ (Python package manager).

.. code:: console

    sudo pip install tcconfig


Dependencies
============

Linux packages
--------------

- iproute2 (required for tc command)
- sch_netem

Python packages
---------------

Dependency python packages are automatically installed during
``tcconfig`` installation via pip.

- `DataPropery <https://github.com/thombashi/DataProperty>`__
- `ipaddress <https://pypi.python.org/pypi/ipaddress>`__
- `pyparsing <https://pyparsing.wikispaces.com/>`__
- `six <https://pypi.python.org/pypi/six/>`__
- `subprocrunner <https://github.com/thombashi/subprocrunner>`__
- `voluptuous <https://github.com/alecthomas/voluptuous>`__

Optional
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- `netifaces <https://bitbucket.org/al45tair/netifaces>`__

Test dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- `pingparsing <https://github.com/thombashi/pingparsing>`__
- `pytest <http://pytest.org/latest/>`__
- `pytest-runner <https://pypi.python.org/pypi/pytest-runner>`__
- `tox <https://testrun.org/tox/latest/>`__
