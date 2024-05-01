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
- Python 3.7+
- `Python package dependencies (automatically installed) <https://github.com/thombashi/tcconfig/network/dependencies>`__

Linux packages
--------------
- mandatory: required for ``tc`` command:
    - `Ubuntu`/`Debian`: ``iproute2``
    - `Fedora`/`RHEL`: ``iproute-tc``
- optional: required when you use the ``--iptables`` option:
    - ``iptables``

Linux kernel module
----------------------------
- ``sch_netem``

Optional Python packages
----------------------------
- `Pygments <http://pygments.org/>`__
