
def set_tc(sys_wrapper, device, rate_mbps, delay_ms, loss_percent):
    import delete_tc

    delete_tc.delete_tc(sys_wrapper, device)

    command = "tc qdisc add dev %s root handle 1: htb default 0" % (device)
    if sys_wrapper.run(command) != 0:
        return

    if thutils.common.is_float(rate_mbps):
        command = "tc class add dev %s parent 1:0 classid 1:0 htb rate %dmbit" % (
            device, rate_mbps)
        sys_wrapper.run(command)

    if thutils.common.is_float(loss_percent) and thutils.common.is_float(delay_ms):
        one_way_loss = loss_percent
        one_way_delay = delay_ms
        command = "tc qdisc add dev %s root netem loss %s%% delay %dms limit 100000000000000" % (
            device, str(one_way_loss), one_way_delay)
        sys_wrapper.run(command)


def delete_tc(sys_wrapper, device):
    command = "tc qdisc del dev %s root" % (device)
    sys_wrapper.run(command)

    command = "tc qdisc del dev %s root" % (device)
    sys_wrapper.run(command)
