Execute with not a super-user
-------------------------------------------------
You can execute tcconfig commands with no super-user by using Linux capabilities.
Setup Linux capabilities as follows:

.. code-block:: sh

    # the following execution binary paths may be different for each environment:
    TC_BIN_PATH=/sbin/tc
    IP_BIN_PATH=/bin/ip
    IPTABLES_BIN_PATH=/sbin/xtables-multi

    sudo setcap cap_net_admin+ep $TC_BIN_PATH  # mandatory
    sudo setcap cap_net_raw,cap_net_admin+ep $IP_BIN_PATH  # optional: required to use --direction incoming option
    sudo setcap cap_net_raw,cap_net_admin+ep $IPTABLES_BIN_PATH  # optional: required to use --iptables option

.. seealso::
    `capabilities(7) - Linux manual page <http://man7.org/linux/man-pages/man7/capabilities.7.html>`__
