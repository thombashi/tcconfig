import thutils


VERSION = "0.1.0"

_MAX_LOSS_RATE = 99
_MAX_DELAY_MS = 10000
_MIN_BUFFER_BYTE = 1600


def _set_delay_and_loss(sys_wrapper, device, delay_ms, loss_percent):
    if loss_percent > _MAX_LOSS_RATE:
        raise ValueError("packet loss rate is too high")

    if delay_ms > _MAX_DELAY_MS:
        raise ValueError("delay time is too high")

    command_list = [
        "tc qdisc add",
        "dev %s" % (device),
        "root handle 1:0 netem",
    ]
    if loss_percent > 0:
        command_list.append("loss %s%%" % (loss_percent))
    if delay_ms > 0:
        command_list.append("delay %dms" % (delay_ms))

    return sys_wrapper.run(" ".join(command_list))


def _set_rate(sys_wrapper, device, rate):
    if thutils.common.isEmptyString(rate):
        return 0

    rate_kbps = thutils.common.humanreadable_to_byte(
        rate, kilo_size=1000) / 1000.0
    if rate_kbps <= 0:
        raise ValueError("rate must be greater than zero")

    command_list = [
        "tc qdisc add",
        "dev %s" % (device),
        "parent 1:1",
        "handle 10:",
        "tbf",
        "rate %dkbit" % (rate_kbps),
        "buffer %d" % (max(rate_kbps, _MIN_BUFFER_BYTE)),  # [byte]
        "limit 10000",
    ]

    return sys_wrapper.run(" ".join(command_list))


def set_tc(sys_wrapper, device, rate, delay_ms, loss_percent):
    _set_delay_and_loss(sys_wrapper, device, delay_ms, loss_percent)
    _set_rate(sys_wrapper, device, rate)


def delete_tc(sys_wrapper, device):
    command = "tc qdisc del dev %s root" % (device)
    return sys_wrapper.run(command)
