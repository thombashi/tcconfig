"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

import itertools

import pingparsing
import pytest
import typepy
from subprocrunner import SubprocessRunner

from tcconfig._const import Tc, TrafficDirection
from tcconfig.traffic_control import delete_all_rules

from .common import ASSERT_MARGIN, DEADLINE_TIME


@pytest.fixture
def device_option(request):
    return request.config.getoption("--device")


@pytest.fixture
def local_host_option(request):
    return request.config.getoption("--local-host")


@pytest.fixture
def dst_host_option(request):
    return request.config.getoption("--dst-host")


@pytest.fixture
def transmitter():
    transmitter = pingparsing.PingTransmitter()
    transmitter.ping_option = "-i 0.2 -q"
    transmitter.deadline = DEADLINE_TIME

    return transmitter


@pytest.fixture
def pingparser():
    return pingparsing.PingParsing()


class Test_tcset_one_network:
    """
    Tests in this class are not executable on CI services.
    Execute the following command at the local environment to running tests:

        pytest --device=<test device> --local-host <IP address> --dst-host=<IP address>

    These tests expected to execute in the following environment:
       - Linux w/ iputils-ping package
       - English locale (for parsing ping output)
    """

    @pytest.mark.parametrize(
        ["shaping_algo", "delay"],
        [[params[0], params[1]] for params in itertools.product(["htb"], [100])],
    )
    def test_src_net_uniform_latency(
        self,
        device_option,
        local_host_option,
        dst_host_option,
        transmitter,
        pingparser,
        shaping_algo,
        delay,
    ):
        if device_option is None:
            pytest.skip("device option is null")
        if typepy.is_null_string(local_host_option):
            pytest.skip("local host is null")
        if typepy.is_null_string(dst_host_option):
            pytest.skip("destination host is null")

        for tc_target in [device_option, f"--device {device_option}"]:
            delete_all_rules(tc_target)
            transmitter.destination = dst_host_option

            # w/o latency tc ---
            without_tc_rtt_avg = pingparser.parse(transmitter.ping().stdout).rtt_avg

            # w/ latency tc ---
            assert (
                SubprocessRunner(
                    " ".join(
                        [
                            Tc.Command.TCSET,
                            tc_target,
                            f"--src-network {local_host_option:s}",
                            f"--delay {delay:d}ms",
                            f"--shaping-algo {shaping_algo:s}",
                        ]
                    )
                ).run()
                == 0
            )

            with_tc_rtt_avg = pingparser.parse(transmitter.ping().stdout).rtt_avg

            # assertion ---
            rtt_diff = with_tc_rtt_avg - without_tc_rtt_avg

            print(f"w/o tc rtt: {without_tc_rtt_avg} ms")
            print(f"w/ tc rtt: {with_tc_rtt_avg} ms")

            assert rtt_diff > (delay * ASSERT_MARGIN)

            # finalize ---
            delete_all_rules(tc_target)


class Test_tcset_exclude:
    """
    Tests in this class are not executable on CI services.
    Execute the following command at the local environment to running tests:

        pytest --device=<test device> --local-host <IP address> --dst-host=<IP address>"

    These tests expected to execute in the following environment:
       - Linux w/ iputils-ping package
       - English locale (for parsing ping output)
    """

    @pytest.mark.parametrize(
        ["shaping_algo", "delay"],
        [[params[0], params[1]] for params in itertools.product(["htb"], [100])],
    )
    def test_src_net_uniform_latency(
        self,
        device_option,
        local_host_option,
        dst_host_option,
        transmitter,
        pingparser,
        shaping_algo,
        delay,
    ):
        if device_option is None:
            pytest.skip("device option is null")
        if typepy.is_null_string(local_host_option):
            pytest.skip("local host is null")
        if typepy.is_null_string(dst_host_option):
            pytest.skip("destination host is null")

        for tc_target in [device_option, f"--device {device_option}"]:
            delete_all_rules(tc_target)
            transmitter.destination = dst_host_option

            # w/o latency tc ---
            without_tc_rtt_avg = pingparser.parse(transmitter.ping().stdout).rtt_avg

            # w/o latency tc (exclude network) ---
            assert (
                SubprocessRunner(
                    " ".join(
                        [
                            Tc.Command.TCSET,
                            tc_target,
                            f"--direction {TrafficDirection.INCOMING:s}",
                            f"--exclude-dst-network {local_host_option:s}",
                            f"--exclude-src-network {dst_host_option:s}",
                            f"--delay {delay:d}ms",
                            f"--shaping-algo {shaping_algo:s}",
                        ]
                    )
                ).run()
                == 0
            )

            exclude_tc_rtt_avg = pingparser.parse(transmitter.ping().stdout).rtt_avg

            # assertion ---
            rtt_diff = exclude_tc_rtt_avg - without_tc_rtt_avg

            print(f"w/o tc rtt: {without_tc_rtt_avg} ms")
            print(f"exclude tc rtt: {exclude_tc_rtt_avg} ms")

            assert rtt_diff < (delay / 10)

            # finalize ---
            delete_all_rules(tc_target)
