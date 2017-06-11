# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import division

import pingparsing
import pytest
from subprocrunner import SubprocessRunner
import typepy

from tcconfig._const import TcCommand

from .common import execute_tcdel


WAIT_TIME = 5  # [sec]


@pytest.fixture
def device_option(request):
    return request.config.getoption("--device")


@pytest.fixture
def dst_host_option(request):
    return request.config.getoption("--dst-host")


@pytest.fixture
def dst_host_ex_option(request):
    return request.config.getoption("--dst-host-ex")


@pytest.fixture
def transmitter():
    transmitter = pingparsing.PingTransmitter()
    transmitter.ping_option = "-f -q"
    transmitter.waittime = WAIT_TIME

    return transmitter


@pytest.fixture
def pingparser():
    return pingparsing.PingParsing()


class Test_tcset_two_network(object):
    """
    Tests in this class are not executable on CI services.
    Execute the following command at the local environment to running tests:
      python setup.py test --addopts \
        "--device=<test device> --dst-host=<hostname/IP-addr> --dst-host-ex=<hostname/IP-addr>"

    These tests are expected to execute on following environment:
       - Linux w/ iputils-ping package
       - English locale (for parsing ping output)
    """

    def test_network(
            self, device_option, dst_host_option, dst_host_ex_option,
            transmitter, pingparser):
        if device_option is None:
            pytest.skip("device option is null")

        if any([
            typepy.is_null_string(dst_host_option),
            typepy.is_null_string(dst_host_ex_option),
        ]):
            pytest.skip("destination host is null")

        execute_tcdel(device_option)
        delay = 100

        # tc to specific network ---
        command_list = [
            TcCommand.TCSET,
            "--device " + device_option,
            "--delay {:d}".format(delay),
            "--network " + dst_host_ex_option,
        ]
        assert SubprocessRunner(" ".join(command_list)).run() == 0

        # w/o tc network ---
        transmitter.destination_host = dst_host_option
        result = transmitter.ping()
        pingparser.parse(result.stdout)
        without_tc_rtt_avg = pingparser.rtt_avg

        # w/ tc network ---
        transmitter.destination_host = dst_host_ex_option
        result = transmitter.ping()
        pingparser.parse(result.stdout)
        with_tc_rtt_avg = pingparser.rtt_avg

        # assertion ---
        rtt_diff = with_tc_rtt_avg - without_tc_rtt_avg
        assert rtt_diff > (delay / 2.0)

        # finalize ---
        execute_tcdel(device_option)
