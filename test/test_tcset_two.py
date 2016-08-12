# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import division

import dataproperty
import pingparsing
import pytest
from subprocrunner import SubprocessRunner


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
    Tests of in this class are inappropriate for Travis CI.
    Execute following command at the local environment  when running tests:
      python setup.py test --addopts \
        "--dst-host=<hostname or IP address> --dst-host-ex=<hostname or IP address>"

    These tests are expected to execute on following environment:
       - Linux(debian) w/ iputils-ping package
       - English environment (for parsing ping output)
    """

    def test_network(
            self, device_option, dst_host_option, dst_host_ex_option,
            transmitter, pingparser):
        if any([
            dataproperty.is_empty_string(dst_host_option),
            dataproperty.is_empty_string(dst_host_ex_option),
        ]):
            # alternative to pytest.mark.skipif
            return

        SubprocessRunner("tcdel --device " + device_option).run()
        delay = 100

        # tc to specific network ---
        command_list = [
            "tcset",
            "--device " + device_option,
            "--delay {:d}".format(delay),
            "--network " + dst_host_ex_option,
        ]
        assert SubprocessRunner(" ".join(command_list)).run() == 0

        # w/o tc network ---
        transmitter.destination_host = dst_host_option
        result = transmitter.ping()
        pingparser.parse(result)
        without_tc_rtt_avg = pingparser.rtt_avg

        # w/ tc network ---
        transmitter.destination_host = dst_host_ex_option
        result = transmitter.ping()
        pingparser.parse(result)
        with_tc_rtt_avg = pingparser.rtt_avg

        # assertion ---
        rtt_diff = with_tc_rtt_avg - without_tc_rtt_avg
        assert rtt_diff > (delay / 2.0)

        # finalize ---
        SubprocessRunner("tcdel --device " + device_option).run()