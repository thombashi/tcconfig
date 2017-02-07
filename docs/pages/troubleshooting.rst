Troubleshooting
========================

Phenomenon
------------------------
``tcset`` command failed with an error message `RTNETLINK answers: No such file or directory`.


Solutions
~~~~~~~~~~~~~~~~~~~~~~~~
The cause of this error is ``sch_netem`` kernel module is not loaded in your system.
Execute the following command to solve this problem: 

.. code:: console

    # modprobe sch_netem

The command is loading the ``sch_netem`` module.
If the command failed with below message, you need to install additional kernel module.

.. code:: console

    # modprobe: FATAL: Module sch_netem not found in directory /lib/modules/xxxxxx

Execute the following command to install kernel modules (includes the `sch_netem` module).

.. code:: console

    # dnf install kernel-modules-extra

(in the case of `RHEL`/`CentOS`/`Fedora`).
After that, re-execute `modprobe sch_netem` command.

.. code:: console

    # modprobe sch_netem
    #


Phenomenon
------------------------
``tcset`` command with ``--direction incoming`` failed with an error message `RTNETLINK answers: Operation not supported`.

Solutions
~~~~~~~~~~~~~~~~~~~~~~~~
The cause may be some mandatory kernel configurations are disabled.
Following configurations are needed to be enabled to use ``--direction incoming`` option.

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

e.g. Display kernel configurations that enabled the above configurations (Debian)

.. code:: console

    cat /boot/config-3.16.0-4-amd64 | egrep "NETFILTER_NETLINK=|NETFILTER_NETLINK_QUEUE=|NETFILTER_NETLINK_LOG=|NF_CT_NETLINK=|SCSI_NETLINK=|IP_ADVANCED_ROUTER=|NET_SCH_INGRESS=|NET_SCHED=|IP_MULTIPLE_TABLES=|NETFILTER_XT_TARGET_MARK="
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

These configurations need to either ``y`` or ``m``.
If some of the configurations are disabled, you need to enable the configurations and recompile the kernel.

.. note::
    
    Name of the `/boot/config-3.16.0-4-amd64` will be changed depends on environment.
