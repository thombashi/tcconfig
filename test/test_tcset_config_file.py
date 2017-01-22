# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import division
from __future__ import print_function
import json

import pytest
from subprocrunner import SubprocessRunner


@pytest.fixture
def device_value(request):
    return request.config.getoption("--device")


class Test_tcconfig(object):

    @pytest.mark.xfail
    @pytest.mark.parametrize(["overwrite", "expected"], [
        ["", 0],
        ["--overwrite", 0],
    ])
    def test_config_file(self, tmpdir, device_value, overwrite, expected):
        if device_value is None:
            pytest.skip("device option is null")

        p = tmpdir.join("tcconfig.json")
        config = "{" + '"{:s}"'.format(device_value) + ": {" + """
        "outgoing": {
            "network=192.168.0.10/32, port=8080": {
                "delay": "10.0",
                "loss": "0.01",
                "rate": "250K",
                "delay-distro": "2.0"
            }
        },
        "incoming": {
            "network=192.168.10.0/24": {
                "corrupt": "0.02",
                "rate": "1500K"
            }
        }
    }
}
"""
        p.write(config)

        device_option = "--device {:s}".format(device_value)

        SubprocessRunner("tcdel {:s}".format(device_option)).run()
        command = " ".join(["tcset -f ", str(p), overwrite])
        assert SubprocessRunner(command).run() == expected

        runner = SubprocessRunner("tcshow {:s}".format(device_option))
        runner.run()

        print("[expected]\n{}".format(config))
        print("\n[actual]\n{}".format(runner.stdout))

        assert json.loads(runner.stdout) == json.loads(config)

        SubprocessRunner("tcdel {:s}".format(device_option)).run()
