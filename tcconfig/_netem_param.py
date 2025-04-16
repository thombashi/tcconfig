"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

import hashlib
from textwrap import dedent

import humanreadable as hr
import typepy
from typepy import RealNumber

from ._common import validate_within_min_max
from ._const import DELAY_DISTRIBUTIONS, Tc
from ._logger import logger
from ._network import get_upper_limit_rate


MIN_PACKET_LOSS_RATE = 0  # [%]
MAX_PACKET_LOSS_RATE = 100  # [%]

MIN_PACKET_DUPLICATE_RATE = 0  # [%]
MAX_PACKET_DUPLICATE_RATE = 100  # [%]

MIN_CORRUPTION_RATE = 0  # [%]
MAX_CORRUPTION_RATE = 100  # [%]

MIN_REORDERING_RATE = 0  # [%]
MAX_REORDERING_RATE = 100  # [%]


def convert_rate_to_f(rate):
    if typepy.is_not_null_string(rate):
        return float(rate.rstrip("% "))

    return rate


class NetemParameter:
    @property
    def bandwidth_rate(self):
        return self.__bandwidth_rate

    @property
    def mtu(self):
        return self.__mtu

    @property
    def burst(self):
        return self.__burst

    def __init__(
        self,
        device,
        bandwidth_rate=None,
        latency_time=None,
        latency_distro_time=None,
        latency_distribution=None,
        packet_loss_rate=None,
        packet_duplicate_rate=None,
        corruption_rate=None,
        reordering_rate=None,
        packet_limit_count=None,
        mtu=None,
        burst=None,
    ):
        self.__device = device

        self.__bandwidth_rate = self.__normalize_bandwidth_rate(bandwidth_rate)
        self.__packet_loss_rate = convert_rate_to_f(packet_loss_rate)  # [%]
        self.__packet_duplicate_rate = convert_rate_to_f(packet_duplicate_rate)  # [%]
        self.__corruption_rate = convert_rate_to_f(corruption_rate)  # [%]
        self.__reordering_rate = convert_rate_to_f(reordering_rate)  # [%]
        self.__packet_limit_count = convert_rate_to_f(packet_limit_count)  # [COUNT]
        self.__mtu = mtu  # [bytes]
        self.__burst = burst  # [bytes]

        self.__latency_time = None
        if latency_time:
            self.__latency_time = hr.Time(latency_time, hr.Time.Unit.MILLISECOND)

        self.__latency_distro_time = None
        if latency_distro_time:
            self.__latency_distro_time = hr.Time(latency_distro_time, hr.Time.Unit.MILLISECOND)

        self.__latency_distribution = (
            "normal" if latency_distribution is None else latency_distribution
        )
        if self.__latency_distribution not in DELAY_DISTRIBUTIONS:
            raise ValueError(f"latency_distribution must be one of {DELAY_DISTRIBUTIONS}")

    def __normalize_bandwidth_rate(self, bandwidth_rate):
        if not bandwidth_rate:
            return None

        hr_bps = hr.BitsPerSecond(bandwidth_rate)
        upper_limit_rate = get_upper_limit_rate(self.__device)

        if hr_bps > upper_limit_rate:
            logger.info(
                dedent(
                    """\
                    clipping specified bandwidth rate limit with the {device} maximum bandwidth rate
                    ({value}Mbps -> {limit}Mbps)
                    """
                ).format(
                    value=hr_bps.mega_bps,
                    limit=upper_limit_rate.mega_bps,
                    device=self.__device,
                )
            )
            hr_bps = upper_limit_rate

        return hr_bps

    def validate_netem_parameter(self):
        self.validate_bandwidth_rate()
        self.__validate_network_delay()
        self.__validate_packet_loss_rate()
        self.__validate_packet_duplicate_rate()
        self.__validate_corruption_rate()
        self.__validate_reordering_rate()
        self.__validate_reordering_and_delay()
        self.__validate_packet_limit_count()

        netem_param_values = [
            self.__packet_loss_rate,
            self.__packet_duplicate_rate,
            self.__corruption_rate,
            self.__reordering_rate,
            self.__packet_limit_count,
            self.__mtu,
            self.__burst,
        ]
        if self.__bandwidth_rate:
            netem_param_values.append(self.__bandwidth_rate.kilo_bps)

        check_results = [
            not RealNumber(netem_param_value).is_type() or netem_param_value <= 0
            for netem_param_value in netem_param_values
        ]

        if self.__latency_time:
            check_results.append(self.__latency_time <= hr.Time(Tc.ValueRange.LatencyTime.MIN))

        if all(check_results):
            raise hr.ParameterError(
                "there are no valid net emulation parameters found. "
                "at least one or more following parameters are required: "
                "--rate, --delay, --loss, --duplicate, --corrupt, --reordering, --limit"
            )

    def validate_bandwidth_rate(self):
        hr_bps = self.__bandwidth_rate

        if not hr_bps:
            return

        if hr_bps.bps < 8:
            raise hr.ParameterError(
                "bandwidth rate must be greater or equals to 8bps",
                value=f"{hr_bps.bps}bps",
            )

        upper_limit_rate = get_upper_limit_rate(self.__device)
        if hr_bps > upper_limit_rate:
            raise hr.ParameterError(
                "exceed bandwidth rate limit",
                value=f"{hr_bps.kilo_bps} kbps",
                expected=f"less than {upper_limit_rate.kilo_bps} kbps",
            )

    def make_param_name(self):
        item_list = [self.__device]

        if self.bandwidth_rate:
            item_list.append(f"rate{int(self.bandwidth_rate.kilo_bps)}kbps")

        if self.__latency_time and self.__latency_time.milliseconds > 0:
            item_list.append(f"delay{self.__latency_time.milliseconds}")

        if self.__latency_distro_time and self.__latency_distro_time.milliseconds > 0:
            item_list.append(f"distro{self.__latency_distro_time.milliseconds}")

        if self.__packet_loss_rate:
            item_list.append(f"loss{self.__packet_loss_rate}")

        if self.__packet_duplicate_rate:
            item_list.append(f"duplicate{self.__packet_duplicate_rate}")

        if self.__corruption_rate:
            item_list.append(f"corrupt{self.__corruption_rate}")

        if self.__reordering_rate:
            item_list.append(f"reordering{self.__reordering_rate}")

        if self.__packet_limit_count:
            item_list.append(f"limit{self.__packet_limit_count}")

        return "_".join(item_list)

    def make_netem_command_parts(self):
        item_list = ["netem"]

        if self.__packet_loss_rate > 0:
            item_list.append(f"loss {self.__packet_loss_rate:f}%")

        if self.__packet_duplicate_rate > 0:
            item_list.append(f"duplicate {self.__packet_duplicate_rate:f}%")

        if self.__latency_time and self.__latency_time > hr.Time(Tc.ValueRange.LatencyTime.MIN):
            item_list.append(f"delay {self.__latency_time.milliseconds}ms")

            if self.__latency_distro_time and self.__latency_distro_time > hr.Time(
                Tc.ValueRange.LatencyTime.MIN
            ):
                item_list.append(
                    "{}ms distribution {}".format(
                        self.__latency_distro_time.milliseconds,
                        self.__latency_distribution,
                    )
                )

        if self.__corruption_rate > 0:
            item_list.append(f"corrupt {self.__corruption_rate:f}%")

        if self.__reordering_rate > 0:
            item_list.append(f"reorder {self.__reordering_rate:f}%")

        if self.__packet_limit_count > 0:
            item_list.append(f"limit {self.__packet_limit_count:f}")

        return " ".join(item_list)

    def calc_hash(self, extra=""):
        return hashlib.md5((self.make_param_name() + extra).encode("latin-1")).hexdigest()

    def calc_device_qdisc_major_id(self):
        base_device_hash = self.calc_hash()[:3]
        device_hash_prefix = "2"

        return int(device_hash_prefix + base_device_hash, 16)

    def __validate_network_delay(self):
        if self.__latency_time:
            try:
                self.__latency_time.validate(
                    min_value=Tc.ValueRange.LatencyTime.MIN,
                    max_value=Tc.ValueRange.LatencyTime.MAX,
                )
            except hr.ParameterError as e:
                raise hr.ParameterError(f"delay {e}")

        if self.__latency_distro_time:
            try:
                self.__latency_distro_time.validate(
                    min_value=Tc.ValueRange.LatencyTime.MIN,
                    max_value=Tc.ValueRange.LatencyTime.MAX,
                )
            except hr.ParameterError as e:
                raise hr.ParameterError(f"delay-distro {e}")

    def __validate_packet_loss_rate(self):
        validate_within_min_max(
            "loss (packet loss rate)",
            self.__packet_loss_rate,
            MIN_PACKET_LOSS_RATE,
            MAX_PACKET_LOSS_RATE,
            unit="%",
        )

    def __validate_packet_duplicate_rate(self):
        validate_within_min_max(
            "duplicate (packet duplicate rate)",
            self.__packet_duplicate_rate,
            MIN_PACKET_DUPLICATE_RATE,
            MAX_PACKET_DUPLICATE_RATE,
            unit="%",
        )

    def __validate_corruption_rate(self):
        validate_within_min_max(
            "corruption (packet corruption rate)",
            self.__corruption_rate,
            MIN_CORRUPTION_RATE,
            MAX_CORRUPTION_RATE,
            unit="%",
        )

    def __validate_reordering_rate(self):
        validate_within_min_max(
            "reordering (packet reordering rate)",
            self.__reordering_rate,
            MIN_REORDERING_RATE,
            MAX_REORDERING_RATE,
            unit="%",
        )

    def __validate_reordering_and_delay(self):
        if self.__reordering_rate and self.__latency_time and self.__latency_time.milliseconds <= 0:
            raise hr.ParameterError("reordering needs latency to be specified: set latency > 0")

    def __validate_packet_limit_count(self):
        if self.__packet_limit_count and self.__packet_limit_count <= 0:
            raise hr.ParameterError("packets limit count can't be less than 1: set limit > 0")
