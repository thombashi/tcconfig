# encoding: utf-8

'''
@author: Tsuyoshi Hombashi
'''

import pytest
import thutils


DEVICE = "eth0"


@pytest.fixture
def subproc_wrapper():
    return thutils.subprocwrapper.SubprocessWrapper()


class Test_tcshow:
    """
    Tests of in this class are inappropriate for Travis CI.
    Execute following command at the local environment  when running tests:
      python setup.py test --addopts --runxfail
    """

    @pytest.mark.xfail
    def test_normal(self, subproc_wrapper):
        command = " ".join([
            "tcset",
            "--device", DEVICE,
            "--delay", "10",
            "--delay-distro", "2",
            "--loss", "0.01",
            "--rate", "0.25M",
            "--network", "192.168.0.10",
            "--port", "8080",
        ])
        assert subproc_wrapper.run(command) == 0

        command = " ".join([
            "tcset",
            "--device", DEVICE,
            "--delay", "1",
            "--loss", "0.02",
            "--rate", "500K",
            "--direction", "incoming",
        ])
        assert subproc_wrapper.run(command) == 0

        command = " ".join([
            "tcshow",
            "--device", DEVICE,
        ])
        proc = subproc_wrapper.popen_command(command)
        stdout, _stderr = proc.communicate()
        assert thutils.loader.JsonLoader.loads(stdout) == thutils.loader.JsonLoader.loads("""{
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
            "network=0.0.0.0/0": {
                "delay": "1.0", 
                "loss": "0.02", 
                "rate": "500K"
            }
        }
    }
}
""")

        assert subproc_wrapper.run("tcdel --device " + DEVICE) == 0
