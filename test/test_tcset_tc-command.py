"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from textwrap import dedent

import pytest
from subprocrunner import SubprocessRunner

from tcconfig._const import Tc

from .common import print_test_result


@pytest.fixture
def device_option(request):
    return request.config.getoption("--device")


class Test_tcset_iface_speed:
    def test_smoke_speed(self, device_option):
        if device_option is None:
            pytest.skip("device option is null")

        for tc_target in [device_option]:
            expected = dedent(
                """\
                /usr/sbin/tc qdisc add dev {device} root handle 1a1a: htb default 1
                /usr/sbin/tc class add dev {device} parent 1a1a: classid 1a1a:1 htb rate 10000000.0kbit
                /usr/sbin/tc class add dev {device} parent 1a1a: classid 1a1a:252 htb rate 10000000.0Kbit ceil 10000000.0Kbit
                /usr/sbin/tc qdisc add dev {device} parent 1a1a:252 handle 21ff: netem loss 1.000000% limit 1000.000000
                /usr/sbin/tc filter add dev {device} protocol ip parent 1a1a: prio 5 u32 match ip dst 0.0.0.0/0 match ip src 0.0.0.0/0 flowid 1a1a:252
                """.format(device=device_option)
            )

            runner = SubprocessRunner(
                [Tc.Command.TCSET, tc_target, "--tc-command", "--loss=1%", "--limit=1000"]
            )

            assert runner.run() == 0, (
                runner.command_str,
                runner.returncode,
                runner.stderr,
            )

            print_test_result(expected=expected, actual=runner.stdout, error=runner.stderr)

            assert runner.stdout == expected, runner.stderr
