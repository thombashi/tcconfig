# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import, unicode_literals

import hashlib

import humanreadable as hr
import six
import typepy
from typepy import RealNumber

from ._common import validate_within_min_max
from ._const import Tc
from ._network import get_no_limit_kbits


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


class NetemParameter(object):
    @property
    def bandwidth_rate(self):
        if self.__bandwidth_rate is None:
            return None

        try:
            return hr.BitPerSecond(self.__bandwidth_rate).kilo_bps
        except (hr.ParameterError, hr.UnitNotFoundError, TypeError):
            return None

    def __init__(
        self,
        device,
        bandwidth_rate=None,
        latency_time=None,
        latency_distro_time=None,
        packet_loss_rate=None,
        packet_duplicate_rate=None,
        corruption_rate=None,
        reordering_rate=None,
    ):
        self.__device = device

        self.__bandwidth_rate = bandwidth_rate
        self.__packet_loss_rate = convert_rate_to_f(packet_loss_rate)  # [%]
        self.__packet_duplicate_rate = convert_rate_to_f(packet_duplicate_rate)  # [%]
        self.__corruption_rate = convert_rate_to_f(corruption_rate)  # [%]
        self.__reordering_rate = convert_rate_to_f(reordering_rate)  # [%]

        self.__latency_time = None
        if latency_time:
            self.__latency_time = hr.Time(latency_time, hr.Time.Unit.MILLISECOND)

        self.__latency_distro_time = None
        if latency_distro_time:
            self.__latency_distro_time = hr.Time(latency_distro_time, hr.Time.Unit.MILLISECOND)

    def validate_netem_parameter(self):
        self.validate_bandwidth_rate()
        self.__validate_network_delay()
        self.__validate_packet_loss_rate()
        self.__validate_packet_duplicate_rate()
        self.__validate_corruption_rate()
        self.__validate_reordering_rate()
        self.__validate_reordering_and_delay()

        netem_param_value_list = [
            self.bandwidth_rate,
            self.__packet_loss_rate,
            self.__packet_duplicate_rate,
            self.__corruption_rate,
            self.__reordering_rate,
        ]

        check_results = [
            not RealNumber(netem_param_value).is_type() or netem_param_value <= 0
            for netem_param_value in netem_param_value_list
        ]

        if self.__latency_time:
            check_results.append(self.__latency_time <= hr.Time(Tc.ValueRange.LatencyTime.MIN))

        if all(check_results):
            raise hr.ParameterError(
                "there are no valid net emulation parameters found. "
                "at least one or more following parameters are required: "
                "--rate, --delay, --loss, --duplicate, --corrupt, --reordering"
            )

    def validate_bandwidth_rate(self):
        if typepy.is_null_string(self.__bandwidth_rate):
            return

        hr_bps = hr.BitPerSecond(self.__bandwidth_rate)

        if hr_bps.bps < 8:
            raise hr.ParameterError(
                "bandwidth rate must be greater or equals to 8bps", value=hr_bps.bps
            )

        no_limit_kbits = get_no_limit_kbits(self.__device)
        if hr_bps.kilo_bps > no_limit_kbits:
            raise hr.ParameterError(
                "exceed bandwidth rate limit",
                value="{} kbps".format(hr_bps.kilo_bps),
                expected="less than {} kbps".format(no_limit_kbits),
            )

    def make_param_name(self):
        item_list = [self.__device]

        if self.bandwidth_rate:
            item_list.append("rate{}".format(self.bandwidth_rate))

        if self.__latency_time and self.__latency_time.milliseconds > 0:
            item_list.append("delay{}".format(self.__latency_time.milliseconds))

        if self.__latency_distro_time and self.__latency_distro_time.milliseconds > 0:
            item_list.append("distro{}".format(self.__latency_distro_time.milliseconds))

        if self.__packet_loss_rate:
            item_list.append("loss{}".format(self.__packet_loss_rate))

        if self.__packet_duplicate_rate:
            item_list.append("duplicate{}".format(self.__packet_duplicate_rate))

        if self.__corruption_rate:
            item_list.append("corrupt{}".format(self.__corruption_rate))

        if self.__reordering_rate:
            item_list.append("reordering{}".format(self.__reordering_rate))

        return "_".join(item_list)

    def make_netem_command_parts(self):
        item_list = ["netem"]

        if self.__packet_loss_rate > 0:
            item_list.append("loss {:f}%".format(self.__packet_loss_rate))

        if self.__packet_duplicate_rate > 0:
            item_list.append("duplicate {:f}%".format(self.__packet_duplicate_rate))

        if self.__latency_time and self.__latency_time > hr.Time(Tc.ValueRange.LatencyTime.MIN):
            item_list.append("delay {}ms".format(self.__latency_time.milliseconds))

            if self.__latency_distro_time and self.__latency_distro_time > hr.Time(
                Tc.ValueRange.LatencyTime.MIN
            ):
                item_list.append(
                    "{}ms distribution normal".format(self.__latency_distro_time.milliseconds)
                )

        if self.__corruption_rate > 0:
            item_list.append("corrupt {:f}%".format(self.__corruption_rate))

        if self.__reordering_rate > 0:
            item_list.append("reorder {:f}%".format(self.__reordering_rate))

        return " ".join(item_list)

    def calc_hash(self, extra=""):
        return hashlib.md5(six.b(self.make_param_name() + extra)).hexdigest()

    def calc_device_qdisc_major_id(self):
        base_device_hash = self.calc_hash()[:3]
        device_hash_prefix = "2"

        return int(device_hash_prefix + base_device_hash, 16)

    def __validate_network_delay(self):
        if self.__latency_time:
            try:
                self.__latency_time.validate(
                    min_value=Tc.ValueRange.LatencyTime.MIN, max_value=Tc.ValueRange.LatencyTime.MAX
                )
            except hr.ParameterError as e:
                raise hr.ParameterError("delay {}".format(e))

        if self.__latency_distro_time:
            try:
                self.__latency_distro_time.validate(
                    min_value=Tc.ValueRange.LatencyTime.MIN, max_value=Tc.ValueRange.LatencyTime.MAX
                )
            except hr.ParameterError as e:
                raise hr.ParameterError("delay-distro {}".format(e))

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
