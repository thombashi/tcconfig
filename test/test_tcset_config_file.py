# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import division
from __future__ import print_function

import json

import pytest
from subprocrunner import SubprocessRunner

from tcconfig._const import Tc

from .common import execute_tcdel


@pytest.fixture
def device_value(request):
    return request.config.getoption("--device")


class Test_tcconfig(object):

    @pytest.mark.parametrize(["overwrite"], [
        [""],
        ["--overwrite"],
    ])
    def test_config_file_smoke(self, tmpdir, device_value, overwrite):
        if device_value is None:
            pytest.skip("device option is null")

        p = tmpdir.join("tcconfig.json")
        config = "{" + '"{:s}"'.format(device_value) + ": {" + """
        "outgoing": {
            "dst-network=192.168.0.10/32, dst-port=8080, protocol=ip": {
                "filter_id": "800::800",
                "delay": "10.0ms",
                "loss": 0.01,
                "rate": "250K",
                "delay-distro": "2.0ms"
            },
            "src-port=1234, protocol=ip": {
                "filter_id": "800::801",
                "delay": "50.0ms",
                "rate": "1G"
            }
        },
        "incoming": {
            "dst-network=192.168.10.0/24, protocol=ip": {
                "filter_id": "800::800",
                "corrupt": 0.02,
                "rate": "1500K"
            }
        }
    }
}
"""
        print("[config]\n{}\n".format(config))
        p.write(config)

        device_option = "--device {:s}".format(device_value)

        execute_tcdel(device_value)
        command = " ".join(
            ["{:s} -f ".format(Tc.Command.TCSET), str(p), overwrite])
        SubprocessRunner(command).run()

        runner = SubprocessRunner("{:s} {:s}".format(
            Tc.Command.TCSHOW, device_option))
        runner.run()

        print("[expected]\n{}\n".format(config))
        print("[actual]\n{}\n".format(runner.stdout))
        print("[stderr]\n{}".format(runner.stderr))

        assert json.loads(runner.stdout) == json.loads(config)

        execute_tcdel(device_value)
