"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

import json
from textwrap import dedent

import pytest
from subprocrunner import SubprocessRunner

from tcconfig._const import Tc
from tcconfig.parser.shaping_rule import TcShapingRuleParser
from tcconfig.traffic_control import delete_all_rules

from .common import NullLogger, print_test_result


@pytest.fixture
def device_value(request):
    return request.config.getoption("--device")


def make_config(device_value):
    return dedent(
        """\
        {{
            "{:s}": {{
                "outgoing": {{
                    "dst-network=192.168.0.10/32, dst-port=8080, protocol=ip": {{
                        "delay": "10.0ms",
                        "loss": "0.01%",
                        "rate": "250Kbps",
                        "delay-distro": "2.0ms"
                    }},
                    "src-network=192.168.44.0/24, src-port=1234, protocol=ip": {{
                        "delay": "50.0ms",
                        "rate": "1Gbps"
                    }}
                }},
                "incoming": {{
                    "dst-network=192.168.10.0/24, protocol=ip": {{
                        "corrupt": "0.02%",
                        "rate": "1500Kbps"
                    }}
                }}
            }}
        }}"""
    ).format(device_value)


class Test_import_config:
    @pytest.mark.parametrize(["overwrite"], [[""], ["--overwrite"]])
    def test_smoke(self, tmpdir, device_value, overwrite):
        if device_value is None:
            pytest.skip("device option is null")

        p = tmpdir.join("tcconfig.json")
        config = make_config(device_value)
        print("[config]\n{}\n".format(config))
        p.write(config)

        for device_option in [device_value]:
            delete_all_rules(device_value)
            command = " ".join([Tc.Command.TCSET, "--import-setting", str(p), overwrite])
            SubprocessRunner(command).run()

            parser = TcShapingRuleParser(
                device=device_value,
                ip_version=4,
                logger=NullLogger(),
                tc_command_output=None,
                is_parse_filter_id=False,
            )
            result = parser.get_tc_parameter()

            print_test_result(expected=config, actual=result)

            assert result == json.loads(config)

            delete_all_rules(device_value)

    def test_normal_tc_command(self, tmpdir, device_value):
        if device_value is None:
            pytest.skip("device option is null")

        p = tmpdir.join("tcconfig.json")
        config = make_config(device_value)
        print("[config]\n{}\n".format(config))
        p.write(config)

        for device_option in [device_value]:
            runner = SubprocessRunner(
                [Tc.Command.TCSET, "--import-setting", str(p), "--tc-command"]
            )
            assert runner.run() == 0
            assert len(runner.stdout.splitlines()) > 10
