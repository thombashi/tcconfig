import json

import pytest

import tcconfig
from tcconfig._const import TrafficDirection
from tcconfig._netem_param import NetemParameter
from tcconfig.traffic_control import TrafficControl, delete_all_rules

from ..common import NullLogger, print_test_result


@pytest.fixture
def device_value(request):
    return request.config.getoption("--device")


class Test_TcShapingRuleParser:
    def test_normal(self, device_value):
        if device_value is None:
            pytest.skip("device option is null")

        delete_all_rules(device_value)

        tc = TrafficControl(
            device=device_value,
            shaping_algorithm="htb",
            direction=TrafficDirection.INCOMING,
            netem_param=NetemParameter(
                device=device_value,
                bandwidth_rate="200kbps",
                packet_loss_rate=0,
                packet_duplicate_rate=0,
                corruption_rate=0,
                reordering_rate=0,
            ),
            src_network="192.168.3.188",
            dst_port=5201,
        )
        assert tc.set_shaping_rule() == 0

        tc = TrafficControl(
            device=device_value,
            shaping_algorithm="htb",
            direction=TrafficDirection.OUTGOING,
            netem_param=NetemParameter(
                device=device_value,
                bandwidth_rate="1000000kbps",
                packet_loss_rate=0,
                packet_duplicate_rate=0,
                corruption_rate=0,
                reordering_rate=0,
            ),
            dst_network="192.168.3.188",
        )
        assert tc.set_shaping_rule() == 0

        result = tcconfig.parser.shaping_rule.TcShapingRuleParser(
            device=device_value,
            ip_version=4,
            logger=NullLogger(),
            tc_command_output=None,
            is_parse_filter_id=False,
        ).get_tc_parameter()
        expected = json.loads(
            """\
            {
                "enp0s3": {
                    "outgoing": {
                        "dst-network=192.168.3.188/32, protocol=ip": {
                            "rate": "1Gbps"
                        }
                    },
                    "incoming": {
                        "src-network=192.168.3.188/32, dst-port=5201, protocol=ip": {
                            "rate": "200Kbps"
                        }
                    }
                }
            }
            """
        )

        print_test_result(expected=expected, actual=result)
        assert result == expected
