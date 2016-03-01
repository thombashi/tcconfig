import dataproperty
import thutils


VERSION = "0.1.4"

_MIN_LOSS_RATE = 0
_MAX_LOSS_RATE = 99

_MIN_DELAY_MS = 0
_MAX_DELAY_MS = 10000

_MIN_BUFFER_BYTE = 1600


def _validate_network_delay(delay_ms):
    if delay_ms > _MAX_DELAY_MS:
        raise ValueError(
            "network delay is too high: expected<=%d[ms], value=%d[ms]" % (
                _MAX_DELAY_MS, delay_ms))

    if delay_ms < _MIN_DELAY_MS:
        raise ValueError(
            "delay time is too low: expected>=%d[ms], value=%d[ms]" % (
                _MIN_DELAY_MS, delay_ms))


def _validate_packet_loss_rate(loss_percent):
    if loss_percent > _MAX_LOSS_RATE:
        raise ValueError(
            "packet loss rate is too high: expected<=%d[%%], value=%d[%%]" % (
                _MAX_LOSS_RATE, loss_percent))

    if loss_percent < _MIN_LOSS_RATE:
        raise ValueError(
            "packet loss rate is too low: expected>=%d[%%], value=%d[%%]" % (
                _MIN_LOSS_RATE, loss_percent))


def _set_delay_and_loss(subproc_wrapper, device, delay_ms, loss_percent):
    _validate_network_delay(delay_ms)
    _validate_packet_loss_rate(loss_percent)

    command_list = [
        "tc qdisc add",
        "dev %s" % (device),
        "root handle 1:0 netem",
    ]
    if loss_percent > 0:
        command_list.append("loss %s%%" % (loss_percent))
    if delay_ms > 0:
        command_list.append("delay %dms" % (delay_ms))

    return subproc_wrapper.run(" ".join(command_list))


def _set_rate(subproc_wrapper, device, rate):
    if dataproperty.is_empty_string(rate):
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

    return subproc_wrapper.run(" ".join(command_list))


def set_tc(subproc_wrapper, device, rate, delay_ms, loss_percent):
    _set_delay_and_loss(subproc_wrapper, device, delay_ms, loss_percent)
    _set_rate(subproc_wrapper, device, rate)


def delete_tc(subproc_wrapper, device):
    command = "tc qdisc del dev %s root" % (device)
    return subproc_wrapper.run(command)
