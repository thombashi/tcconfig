# encoding: utf-8

'''
@author: Tsuyoshi Hombashi
'''

import itertools
import platform

import dataproperty
import pingparsing
import pytest
import six
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
        "--delay 100",
    ]
    DELAY_DISTRO_LIST = [
        "",
        "--delay-distro 20",
    ]
    PACKET_LOSS_RATE_LIST = [
        "",
        "--loss 0.1",
    ]
    CORRUPTION_RATE_LIST = [
        "",
        "--corrupt 0.1",
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
    Tests of in this class are inappropriate for Travis CI.
    Execute following command at the local environment  when running tests:
      python setup.py test --addopts --runxfail

    These tests are expected to execute on following environment:
       - Linux(debian) w/ iputils-ping package
       - English environment (for parsing ping output)
    """

    @pytest.mark.xfail
    @pytest.mark.parametrize(
        [
            "rate", "delay", "delay_distro", "loss", "corrupt",
            "direction", "network", "port", "overwrite",
        ],
        [
            opt_list
            for opt_list in itertools.product(
                NormalTestValue.RATE_LIST,
                NormalTestValue.DELAY_LIST,
                NormalTestValue.DELAY_DISTRO_LIST,
                NormalTestValue.PACKET_LOSS_RATE_LIST,
                NormalTestValue.CORRUPTION_RATE_LIST,
                NormalTestValue.DIRECTION_LIST,
                NormalTestValue.NETWORK_LIST,
                NormalTestValue.PORT_LIST,
                NormalTestValue.OVERWRITE_LIST)
        ])
    def test_smoke(
            self, subproc_wrapper, rate, delay, delay_distro, loss, corrupt,
            direction, network, port, overwrite):
        command = " ".join([
            "tcset",
            "--device " + DEVICE,
            rate, delay, delay_distro, loss,
            direction, network, port, overwrite,
        ])
        assert subproc_wrapper.run(command) == 0

        assert subproc_wrapper.run("tcdel --device " + DEVICE) == 0

    @pytest.mark.xfail
    @pytest.mark.parametrize(["overwrite", "expected"], [
        ["", 0],
        ["--overwrite", 255],
    ])
    def test_config_file(self, tmpdir, subproc_wrapper, overwrite, expected):
        p = tmpdir.join("tcconfig.json")
        config = """{
    "eth0": {
        "outgoing": {
            "network=192.168.0.10/32, port=8080": {
                "delay": "10.0", 
                "loss": "0.01", 
                "rate": "250K", 
                "delay-distro": "2.0"
            }, 
            "network=0.0.0.0/0": {}
        }, 
        "incoming": {
            "network=192.168.10.0/24": {
                "corrupt": "0.02", 
                "rate": "1500K"
            }, 
            "network=0.0.0.0/0": {}
        }
    }
}
"""
        p.write(config)

        subproc_wrapper.run("tcdel --device " + DEVICE)
        command = " ".join(["tcset -f ", str(p), overwrite])
        assert subproc_wrapper.run(command) == expected

        proc = subproc_wrapper.popen_command("tcshow --device " + DEVICE)
        tcshow_stdout, _stderr = proc.communicate()
        assert thutils.loader.JsonLoader.loads(
            tcshow_stdout) == thutils.loader.JsonLoader.loads(config)

        assert subproc_wrapper.run("tcdel --device " + DEVICE) == 0


class Test_tcset_one_network:
    """
    Tests of in this class are inappropriate for Travis CI.
    Execute following command at the local environment  when running tests:
      python setup.py test --addopts "--dst-host=<hostname or IP address>"

    These tests are expected to execute on following environment:
       - Linux(debian) w/ iputils-ping package
       - English environment (for parsing ping output)
    """

    @pytest.mark.parametrize(["delay"], [
        [100],
    ])
    def test_const_latency(
            self, dst_host_option, subproc_wrapper,
            transmitter, pingparser, delay):
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
        assert subproc_wrapper.run("tcdel --device " + DEVICE) == 0

    @pytest.mark.skipif("platform.system() == 'Windows'")
    @pytest.mark.parametrize(["delay", "delay_distro"], [
        [100, 50],
    ])
    def test_const_latency_distro(
            self, dst_host_option, subproc_wrapper,
            transmitter, pingparser, delay, delay_distro):
        if dataproperty.is_empty_string(dst_host_option):
            # alternative to pytest.mark.skipif
            return

        subproc_wrapper.run("tcdel --device " + DEVICE)
        transmitter.destination_host = dst_host_option

        # w/o latency tc ---
        result = transmitter.ping()
        pingparser.parse(result)
        without_tc_rtt_avg = pingparser.rtt_avg
        without_tc_rtt_mdev = pingparser.rtt_mdev

        # w/ latency tc ---
        command_list = [
            "tcset",
            "--device " + DEVICE,
            "--delay %d" % (delay),
            "--delay-distro %d" % (delay_distro),
        ]
        assert subproc_wrapper.run(" ".join(command_list)) == 0

        result = transmitter.ping()
        pingparser.parse(result)
        with_tc_rtt_avg = pingparser.rtt_avg
        with_tc_rtt_mdev = pingparser.rtt_mdev

        # assertion ---
        rtt_diff = with_tc_rtt_avg - without_tc_rtt_avg
        assert rtt_diff > (delay / 2.0)

        rtt_diff = with_tc_rtt_mdev - without_tc_rtt_mdev
        assert rtt_diff > (delay_distro / 2.0)

        # finalize ---
        subproc_wrapper.run("tcdel --device " + DEVICE)

    @pytest.mark.parametrize(["option", "value"], [
        ["--loss", 10],
        ["--corrupt", 10],
    ])
    def test_const_packet_loss(
            self, dst_host_option, subproc_wrapper,
            transmitter, pingparser, option, value):
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
            "%s %f" % (option, value),
        ]
        assert subproc_wrapper.run(" ".join(command_list)) == 0

        result = transmitter.ping()
        pingparser.parse(result)
        with_tc_loss = (
            pingparser.packet_receive / float(pingparser.packet_transmit)) * 100.0

        # assertion ---
        loss_diff = without_tc_loss - with_tc_loss
        assert loss_diff > (value / 2.0)

        # finalize ---
        subproc_wrapper.run("tcdel --device " + DEVICE)


class Test_tcset_two_network:
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
