# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import itertools

import pingparsing
import pytest
from subprocrunner import SubprocessRunner
import typepy

from tcconfig._const import (
    TcCommand,
    TrafficDirection,
)
from .common import execute_tcdel


WAIT_TIME = 3  # [sec]


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

        python setup.py test --addopts "--device=<test device> \n
            --local-host <IP address> --dst-host=<IP address>"

    These tests expected to execute in the following environment:
       - Linux w/ iputils-ping package
       - English locale (for parsing ping output)
    """

    @pytest.mark.parametrize(["shaping_algo", "delay"], [
        [params[0], params[1]]
        for params in itertools.product(["htb"], [100])
    ])
    def test_src_net_uniform_latency(
            self, device_option, local_host_option, dst_host_option,
            transmitter, pingparser, shaping_algo, delay):
        if device_option is None:
            pytest.skip("device option is null")
        if typepy.is_null_string(local_host_option):
            pytest.skip("local host is null")
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
            "--src-network {:s}".format(local_host_option),
            "--delay {:d}".format(delay),
            "--shaping-algo {:s}".format(shaping_algo),
        ]
        assert SubprocessRunner(" ".join(command_list)).run() == 0

        pingparser.parse(transmitter.ping().stdout)
        with_tc_rtt_avg = pingparser.rtt_avg

        # assertion ---
        rtt_diff = with_tc_rtt_avg - without_tc_rtt_avg

        print("w/o tc rtt: {} ms".format(without_tc_rtt_avg))
        print("w/ tc rtt: {} ms".format(with_tc_rtt_avg))

        assert rtt_diff > (delay / 2)

        # finalize ---
        execute_tcdel(device_option)


class Test_tcset_exclude(object):
    """
    Tests in this class are not executable on CI services.
    Execute the following command at the local environment to running tests:

        python setup.py test --addopts "--device=<test device> \n
            --local-host <IP address> --dst-host=<IP address>"

    These tests expected to execute in the following environment:
       - Linux w/ iputils-ping package
       - English locale (for parsing ping output)
    """

    @pytest.mark.parametrize(["shaping_algo", "delay"], [
        [params[0], params[1]]
        for params in itertools.product(["htb"], [100])
    ])
    def test_src_net_uniform_latency(
            self, device_option, local_host_option, dst_host_option,
            transmitter, pingparser, shaping_algo, delay):
        if device_option is None:
            pytest.skip("device option is null")
        if typepy.is_null_string(local_host_option):
            pytest.skip("local host is null")
        if typepy.is_null_string(dst_host_option):
            pytest.skip("destination host is null")

        execute_tcdel(device_option)
        transmitter.destination_host = dst_host_option

        # w/o latency tc ---
        pingparser.parse(transmitter.ping().stdout)
        without_tc_rtt_avg = pingparser.rtt_avg

        # w/o latency tc (exclude network) ---
        command_list = [
            TcCommand.TCSET,
            "--device {:s}".format(device_option),
            "--direction {:s}".format(TrafficDirection.INCOMING),
            "--exclude-dst-network {:s}".format(local_host_option),
            "--exclude-src-network {:s}".format(dst_host_option),
            "--delay {:d}".format(delay),
            "--shaping-algo {:s}".format(shaping_algo),
        ]
        assert SubprocessRunner(" ".join(command_list)).run() == 0

        pingparser.parse(transmitter.ping().stdout)
        exclude_tc_rtt_avg = pingparser.rtt_avg

        # assertion ---
        rtt_diff = exclude_tc_rtt_avg - without_tc_rtt_avg

        print("w/o tc rtt: {} ms".format(without_tc_rtt_avg))
        print("exclude tc rtt: {} ms".format(exclude_tc_rtt_avg))

        assert rtt_diff < (delay / 10)

        # finalize ---
        execute_tcdel(device_option)
