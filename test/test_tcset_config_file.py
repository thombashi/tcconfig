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
            "network=192.168.0.10/32, dst-port=8080, protocol=ip": {
                "delay": "10.0",
                "loss": "0.01",
                "rate": "250K",
                "delay-distro": "2.0"
            },
            "network=0.0.0.0/0, src-port=1234, protocol=ip": {
                "delay": "50.0",
                "rate": "1G"
            }
        },
        "incoming": {
            "network=192.168.10.0/24, protocol=ip": {
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
        SubprocessRunner(command).run()

        runner = SubprocessRunner("tcshow {:s}".format(device_option))
        runner.run()

        print("[expected]\n{}\n".format(config))
        print("[actual]\n{}\n".format(runner.stdout))
        print("[stderr]\n{}".format(runner.stderr))

        assert json.loads(runner.stdout) == json.loads(config)

        SubprocessRunner("tcdel {:s}".format(device_option)).run()
