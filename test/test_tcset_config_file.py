# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import division, print_function

import pytest
import simplejson as json
from subprocrunner import SubprocessRunner

from tcconfig._const import Tc

from .common import execute_tcdel, print_test_result


@pytest.fixture
def device_value(request):
    return request.config.getoption("--device")


class Test_tcconfig(object):
    @pytest.mark.parametrize(["overwrite"], [[""], ["--overwrite"]])
    def test_config_file_smoke(self, tmpdir, device_value, overwrite):
        if device_value is None:
            pytest.skip("device option is null")

        p = tmpdir.join("tcconfig.json")
        config = (
            "{"
            + '"{:s}"'.format(device_value)
            + ": {"
            + """
        "outgoing": {
            "dst-network=192.168.0.10/32, dst-port=8080, protocol=ip": {
                "filter_id": "800::800",
                "delay": "10.0ms",
                "loss": "0.01%",
                "rate": "250Kbps",
                "delay-distro": "2.0ms"
            },
            "src-port=1234, protocol=ip": {
                "filter_id": "800::801",
                "delay": "50.0ms",
                "rate": "1Gbps"
            }
        },
        "incoming": {
            "dst-network=192.168.10.0/24, protocol=ip": {
                "filter_id": "800::800",
                "corrupt": "0.02%",
                "rate": "1500Kbps"
            }
        }
    }
}
"""
        )
        print("[config]\n{}\n".format(config))
        p.write(config)

        for device_option in [device_value, "--device {}".format(device_value)]:
            execute_tcdel(device_value)
            command = " ".join([Tc.Command.TCSET, str(p), "--import-setting", overwrite])
            SubprocessRunner(command).run()

            runner = SubprocessRunner("{:s} {:s}".format(Tc.Command.TCSHOW, device_option))
            runner.run()

            print_test_result(expected=config, actual=runner.stdout, error=runner.stderr)

            assert json.loads(runner.stdout) == json.loads(config)

            execute_tcdel(device_value)
