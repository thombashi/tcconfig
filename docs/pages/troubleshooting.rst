Troubleshooting
========================

Phenomenon
------------------------
`tcset` command failed with an error message `RTNETLINK answers: No such file or directory`.


Solutions
--------------------------
The cause of this error is `sch_netem` kernel module is not loaded in your system.
Execute the following command to solve this problem: 

.. code:: console

    # modprobe sch_netem

The command is loading the `sch_netem` module.
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
