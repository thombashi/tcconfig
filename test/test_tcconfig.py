# encoding: utf-8

'''
@author: Tsuyoshi Hombashi
'''

import itertools

import dataproperty
import pingparsing
import pytest
import thutils
import tcconfig


DEVICE = "eth0"
WAIT_TIME = 5  # [sec]


@pytest.fixture
def dst_host_option(request):
    return request.config.getoption("--dst-host")


@pytest.fixture
def dst_host_ex_option(request):
    return request.config.getoption("--dst-host-ex")


@pytest.fixture
def subproc_wrapper():
    return thutils.subprocwrapper.SubprocessWrapper()


@pytest.fixture
def pingparser():
    return pingparsing.PingParsing()


@pytest.fixture
def transmitter():
    transmitter = pingparsing.PingTransmitter()
    transmitter.ping_option = "-f -q"
    transmitter.waittime = WAIT_TIME

    return transmitter


class NormalTestValue:
    RATE_LIST = [
        "",
        "--rate 100K",
        "--rate 0.5M",
    ]
    DELAY_LIST = [
        "",
        "--delay 1",
        "--delay 100",
    ]
    LOSS_LIST = [
        "",
        "--loss 0.1",
        "--loss 99",
    ]
    DIRECTION_LIST = [
        "",
        "--direction outgoing",
        "--direction incoming",
    ]
    NETWORK_LIST = [
        "",
        "--network 192.168.0.10",
        "--network 192.168.0.0/24",
    ]
    PORT_LIST = [
        "",
        "--port 80",
    ]
    OVERWRITE_LIST = [
        "",
        "--overwrite",
    ]


class Test_tcconfig:
    """
    Inappropriate tests to Travis CI.
    Run locally with following command:
      python setup.py test --addopts --runxfail

    These tests expected to execute on following environment:
       - Linux(debian) w/ iputils-ping package
       - English environment (for parsing ping output)
    """

    @pytest.mark.xfail
    @pytest.mark.parametrize(
        ["rate", "delay", "loss", "direction", "network", "port", "overwrite"],
        [
            opt_list
            for opt_list in itertools.product(
                NormalTestValue.RATE_LIST,
                NormalTestValue.DELAY_LIST,
                NormalTestValue.LOSS_LIST,
                NormalTestValue.DIRECTION_LIST,
                NormalTestValue.NETWORK_LIST,
                NormalTestValue.PORT_LIST,
                NormalTestValue.OVERWRITE_LIST)
        ])
    def test_smoke(
            self, subproc_wrapper, rate, delay, loss,
            direction, network, port, overwrite):
        command = " ".join([
            "tcset",
            "--device " + DEVICE,
            rate, delay, loss, direction, network, port, overwrite,
        ])
        assert subproc_wrapper.run(command) == 0

        assert subproc_wrapper.run("tcdel --device " + DEVICE) == 0


class Test_tcset_one_network:
    """
    Inappropriate tests to Travis CI.
    Run locally with following command:
      python setup.py test --addopts "--dst-host=<hostname or IP address>"

    These tests expected to execute on following environment:
       - Linux(debian) w/ iputils-ping package
       - English environment (for parsing ping output)
    """

    @pytest.mark.parametrize(["delay"], [
        [100],
    ])
    def test_const_latency(
            self, dst_host_option, subproc_wrapper, transmitter, pingparser, delay):
        if dataproperty.is_empty_string(dst_host_option):
            # alternative to pytest.mark.skipif
            return

        subproc_wrapper.run("tcdel --device " + DEVICE)
        transmitter.destination_host = dst_host_option

        # w/o latency tc ---
        result = transmitter.ping()
        pingparser.parse(result)
        without_tc_rtt_avg = pingparser.rtt_avg

        # w/ latency tc ---
        command_list = [
            "tcset",
            "--device " + DEVICE,
            "--delay %d" % (delay),
        ]
        assert subproc_wrapper.run(" ".join(command_list)) == 0

        result = transmitter.ping()
        pingparser.parse(result)
        with_tc_rtt_avg = pingparser.rtt_avg

        # assertion ---
        rtt_diff = with_tc_rtt_avg - without_tc_rtt_avg
        assert rtt_diff > (delay / 2.0)

        # finalize ---
        subproc_wrapper.run("tcdel --device " + DEVICE)

    @pytest.mark.parametrize(["packet_loss"], [
        [10],
    ])
    def test_const_packet_loss(
            self, dst_host_option, subproc_wrapper,
            transmitter, pingparser, packet_loss):
        if dataproperty.is_empty_string(dst_host_option):
            # alternative to pytest.mark.skipif
            return

        subproc_wrapper.run("tcdel --device " + DEVICE)
        transmitter.destination_host = dst_host_option

        # w/o packet loss tc ---
        result = transmitter.ping()
        pingparser.parse(result)
        without_tc_loss = (
            pingparser.packet_receive / float(pingparser.packet_transmit)) * 100.0

        # w/ packet loss tc ---
        command_list = [
            "tcset",
            "--device " + DEVICE,
            "--loss %f" % (packet_loss),
        ]
        assert subproc_wrapper.run(" ".join(command_list)) == 0

        result = transmitter.ping()
        pingparser.parse(result)
        with_tc_loss = (
            pingparser.packet_receive / float(pingparser.packet_transmit)) * 100.0

        # assertion ---
        loss_diff = without_tc_loss - with_tc_loss
        assert loss_diff > (packet_loss / 2.0)

        # finalize ---
        subproc_wrapper.run("tcdel --device " + DEVICE)


class Test_tcset_two_network:
    """
    Inappropriate tests to Travis CI.
    Run locally with following command:
      python setup.py test --addopts \
        "--dst-host=<hostname or IP address> --dst-host-ex=<hostname or IP address>"

    These tests expected to execute on following environment:
       - Linux(debian) w/ iputils-ping package
       - English environment (for parsing ping output)
    """

    def test_network(
            self, dst_host_option, dst_host_ex_option, subproc_wrapper,
            transmitter, pingparser):
        if any([
            dataproperty.is_empty_string(dst_host_option),
            dataproperty.is_empty_string(dst_host_ex_option),
        ]):
            # alternative to pytest.mark.skipif
            return

        subproc_wrapper.run("tcdel --device " + DEVICE)
        delay = 100

        # tc to specific network ---
        command_list = [
            "tcset",
            "--device " + DEVICE,
            "--delay %d" % (delay),
            "--network " + dst_host_ex_option,
        ]
        assert subproc_wrapper.run(" ".join(command_list)) == 0

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
        subproc_wrapper.run("tcdel --device " + DEVICE)
