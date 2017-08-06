# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import
from __future__ import division

import itertools

import pingparsing
import pytest
from subprocrunner import SubprocessRunner
import typepy

from tcconfig._const import TcCommand

from .common import execute_tcdel


WAIT_TIME = 3  # [sec]


@pytest.fixture
def device_option(request):
    return request.config.getoption("--device")


@pytest.fixture
def dst_host_option(request):
    return request.config.getoption("--dst-host")


@pytest.fixture
def transmitter():
    transmitter = pingparsing.PingTransmitter()
    transmitter.ping_option = "-f -q"
    transmitter.waittime = WAIT_TIME

    return transmitter


@pytest.fixture
def pingparser():
    return pingparsing.PingParsing()


class Test_tcset_one_network(object):
    """
    Tests in this class are not executable on CI services.
    Execute the following command at the local environment to running tests:

        python setup.py test --addopts \
            "--device=<test device> --dst-host=<IP address>"

    These tests expected to execute in the following environment:
       - Linux w/ iputils-ping package
       - English locale (for parsing ping output)
    """

    @pytest.mark.parametrize(["shaping_algo", "delay"], [
        [params[0], params[1]]
        for params in itertools.product(["htb"], [100])
    ])
    def test_dst_net_uniform_latency(
            self, device_option, dst_host_option, transmitter, pingparser,
            shaping_algo, delay):
        if device_option is None:
            pytest.skip("device option is null")
        if typepy.is_null_string(dst_host_option):
            pytest.skip("destination host is null")

        execute_tcdel(device_option)
        transmitter.destination_host = dst_host_option

        # w/o latency tc ---
        pingparser.parse(transmitter.ping().stdout)
        without_tc_rtt_avg = pingparser.rtt_avg

        # w/ latency tc ---
        command_list = [
            TcCommand.TCSET,
            "--device {:s}".format(device_option),
            "--delay {:d}".format(delay),
            "--shaping-algo {:s}".format(shaping_algo),
        ]
        assert SubprocessRunner(" ".join(command_list)).run() == 0

        pingparser.parse(transmitter.ping().stdout)
        with_tc_rtt_avg = pingparser.rtt_avg

        # assertion ---
        rtt_diff = with_tc_rtt_avg - without_tc_rtt_avg
        assert rtt_diff > (delay / 2.0)

        # finalize ---
        execute_tcdel(device_option)

    @pytest.mark.parametrize(["delay", "delay_distro"], [
        [100, 50],
    ])
    def test_dst_net_latency_distro(
            self, device_option, dst_host_option, transmitter, pingparser,
            delay, delay_distro):
        if typepy.is_null_string(dst_host_option):
            pytest.skip("destination host is null")

        execute_tcdel(device_option)
        transmitter.destination_host = dst_host_option

        # w/o latency tc ---
        result = transmitter.ping()
        pingparser.parse(result.stdout)
        without_tc_rtt_avg = pingparser.rtt_avg
        without_tc_rtt_mdev = pingparser.rtt_mdev

        # w/ latency tc ---
        command_list = [
            TcCommand.TCSET,
            "--device {:s}".format(device_option),
            "--delay {:d}".format(delay),
            "--delay-distro {:d}".format(delay_distro),
        ]
        assert SubprocessRunner(" ".join(command_list)).run() == 0

        result = transmitter.ping()
        pingparser.parse(result.stdout)
        with_tc_rtt_avg = pingparser.rtt_avg
        with_tc_rtt_mdev = pingparser.rtt_mdev

        # assertion ---
        rtt_diff = with_tc_rtt_avg - without_tc_rtt_avg
        assert rtt_diff > (delay / 2.0)

        rtt_diff = with_tc_rtt_mdev - without_tc_rtt_mdev
        assert rtt_diff > (delay_distro / 2.0)

        # finalize ---
        execute_tcdel(device_option)

    @pytest.mark.parametrize(["option", "value"], [
        ["--loss", 10],
        ["--corrupt", 10],
    ])
    def test_dst_net_packet_loss(
            self, device_option, dst_host_option, transmitter, pingparser,
            option, value):
        if typepy.is_null_string(dst_host_option):
            pytest.skip("destination host is null")

        execute_tcdel(device_option)
        transmitter.destination_host = dst_host_option

        # w/o packet loss tc ---
        result = transmitter.ping()
        pingparser.parse(result.stdout)
        without_tc_loss_rate = pingparser.packet_loss_rate

        # w/ packet loss tc ---
        command_list = [
            TcCommand.TCSET,
            "--device {:s}".format(device_option),
            "{:s} {:f}".format(option, value),
        ]
        assert SubprocessRunner(" ".join(command_list)).run() == 0

        result = transmitter.ping()
        pingparser.parse(result.stdout)
        with_tc_loss_rate = pingparser.packet_loss_rate

        # assertion ---
        loss_diff = with_tc_loss_rate - without_tc_loss_rate
        assert loss_diff > (value / 2)

        # finalize ---
        execute_tcdel(device_option)

    @pytest.mark.parametrize(["option", "value"], [
        ["--duplicate", 50],
    ])
    def test_dst_net_packet_duplicate(
            self, device_option, dst_host_option, transmitter, pingparser,
            option, value):
        if typepy.is_null_string(dst_host_option):
            pytest.skip("destination host is null")

        execute_tcdel(device_option)
        transmitter.destination_host = dst_host_option

        # w/o packet duplicate tc ---
        pingparser.parse(transmitter.ping().stdout)
        without_tc_duplicate_rate = pingparser.packet_duplicate_rate

        # w/ packet duplicate tc ---
        command_list = [
            TcCommand.TCSET,
            "--device {:s}".format(device_option),
            "{:s} {:f}".format(option, value),
        ]
        assert SubprocessRunner(" ".join(command_list)).run() == 0

        pingparser.parse(transmitter.ping().stdout)
        with_tc_duplicate_rate = pingparser.packet_duplicate_rate

        # assertion ---
        duplicate_rate_diff = (
            with_tc_duplicate_rate - without_tc_duplicate_rate)
        assert duplicate_rate_diff > (value / 2)

        # finalize ---
        execute_tcdel(device_option)

    def test_dst_net_exclude_dst_network(
            self, device_option, dst_host_option, transmitter, pingparser):
        if device_option is None:
            pytest.skip("device option is null")
        if typepy.is_null_string(dst_host_option):
            pytest.skip("destination host is null")

        delay = 100

        execute_tcdel(device_option)
        transmitter.destination_host = dst_host_option

        # w/ latency tc ---
        command_list = [
            TcCommand.TCSET,
            "--device {:s}".format(device_option),
            "--delay {:d}".format(100),
        ]
        assert SubprocessRunner(" ".join(command_list)).run() == 0

        pingparser.parse(transmitter.ping().stdout)
        with_tc_rtt_avg = pingparser.rtt_avg

        # exclude certain network ---
        command_list = [
            TcCommand.TCSET,
            "--device {:s}".format(device_option),
            "--exclude-dst-network {:s}/24".format(
                ".".join(dst_host_option.split(".")[:3] + ["0"])),
            "--delay {:d}".format(delay),
            "--overwrite",
        ]
        assert SubprocessRunner(" ".join(command_list)).run() == 0

        pingparser.parse(transmitter.ping().stdout)
        without_tc_rtt_avg = pingparser.rtt_avg

        # assertion ---
        rtt_diff = with_tc_rtt_avg - without_tc_rtt_avg
        assert rtt_diff > (delay / 2.0)

        # finalize ---
        execute_tcdel(device_option)
