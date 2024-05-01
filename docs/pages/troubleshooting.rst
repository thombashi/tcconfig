Troubleshooting
========================

RTNETLINK answers: No such file or directory
------------------------------------------------

Phenomenon
~~~~~~~~~~~~~~~~~~~~~~~~
``tcset`` command failed with an error message:

    - ``RTNETLINK answers: No such file or directory``
    - ``Error: Specified qdisc not found``

:Example:

    .. code:: console

        $ sudo tcset eth0 --rate 1Mbps
        [ERROR] tcconfig: command execution failed
          command=/usr/sbin/tc qdisc add dev eth0 parent 1a1a:2 handle 2873: netem delay 10ms
          stderr=Error: Specified qdisc not found.

Solution
~~~~~~~~~~~~~~~~~~~~~~~~
Execute the following command to load ``sch_netem`` module.
The cause of the error is ``sch_netem`` kernel module is not loaded in your system which is required to set up traffic control. 

.. code:: console

    $ sudo modprobe sch_netem

If the command fails with the below message, you need to install an additional kernel module.

:Example - Fedora:

    .. code:: console

        $ sudo modprobe sch_netem
        modprobe: FATAL: Module sch_netem not found in directory /lib/modules/4.20.11-200.fc29.x86_64

In that case, install ``kernel-modules-extra`` package.
This package includes the ``sch_netem`` module.

:Example - Fedora:

    .. code:: console

        $ sudo dnf install -y kernel-modules-extra

Load ``sch_netem`` module after the package installation.

.. code:: console

    $ sudo modprobe sch_netem
    $


RTNETLINK answers: Operation not supported
------------------------------------------------

Phenomenon
~~~~~~~~~~~~~~~~~~~~~~~~
``tcset`` command with ``--direction incoming`` failed with an error message
``RTNETLINK answers: Operation not supported``.

Solutions
~~~~~~~~~~~~~~~~~~~~~~~~
Checking Linux kernel configurations and reconfiguring them if required configurations are disabled.

The cause may be some mandatory kernel configurations are disabled.
The following configurations are needed to be enabled to use ``--direction incoming`` option.

- CONFIG_IP_ADVANCED_ROUTER
- CONFIG_IP_MULTIPLE_TABLES
- CONFIG_NETFILTER_NETLINK
- CONFIG_NETFILTER_NETLINK_QUEUE
- CONFIG_NETFILTER_NETLINK_LOG
- CONFIG_NF_CT_NETLINK
- CONFIG_NETFILTER_XT_TARGET_MARK
- CONFIG_NET_SCHED
- CONFIG_NET_SCH_INGRESS
- CONFIG_SCSI_NETLINK

e.g. Kernel configurations that enabled the above configurations (Debian)

.. sourcecode:: console

    $ cat /boot/config-3.16.0-4-amd64 | egrep "NETFILTER_NETLINK=|NETFILTER_NETLINK_QUEUE=|NETFILTER_NETLINK_LOG=|NF_CT_NETLINK=|SCSI_NETLINK=|IP_ADVANCED_ROUTER=|NET_SCH_INGRESS=|NET_SCHED=|IP_MULTIPLE_TABLES=|NETFILTER_XT_TARGET_MARK="
    CONFIG_IP_ADVANCED_ROUTER=y
    CONFIG_IP_MULTIPLE_TABLES=y
    CONFIG_NETFILTER_NETLINK=m
    CONFIG_NETFILTER_NETLINK_QUEUE=m
    CONFIG_NETFILTER_NETLINK_LOG=m
    CONFIG_NF_CT_NETLINK=m
    CONFIG_NETFILTER_XT_TARGET_MARK=m
    CONFIG_NET_SCHED=y
    CONFIG_NET_SCH_INGRESS=m
    CONFIG_SCSI_NETLINK=y

These configurations need to be either ``y`` or ``m``.
If some of the configurations are disabled, you need to:

1. enable the kernel configurations
2. build kernel
3. using the compiled kernel image as the boot kernel

.. note::

    The name of the kernel configuration file (``/boot/config-3.16.0-4-amd64``) differs depending on the environment.
