"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

import humanreadable as hr
import pytest

from tcconfig._network import (
    _get_iproute2_upper_limite_rate,
    get_anywhere_network,
    get_upper_limit_rate,
    is_anywhere_network,
    sanitize_network,
)


@pytest.fixture
def device_option(request):
    return request.config.getoption("--device")


class Test_is_anywhere_network:
    @pytest.mark.parametrize(
        ["network", "ip_version", "expected"],
        [
            ["0.0.0.0/0", 4, True],
            ["192.168.0.0/0", 4, False],
            ["::/0", 6, True],
            ["0:0:0:0:0:0:0:0/0", 6, True],
            ["2001:db00::0/24", 6, False],
        ],
    )
    def test_normal(self, network, ip_version, expected):
        assert is_anywhere_network(network, ip_version) == expected

    @pytest.mark.parametrize(
        ["network", "ip_version", "expected"],
        [[None, 4, ValueError], ["0.0.0.0/0", 5, ValueError], ["0.0.0.0/0", None, ValueError]],
    )
    def test_exception(self, network, ip_version, expected):
        with pytest.raises(expected):
            is_anywhere_network(network, ip_version)


class Test_get_iproute2_upper_limite_rate:
    def test_normal(self):
        assert _get_iproute2_upper_limite_rate() == hr.BitPerSecond("32Gbps")


class Test_get_anywhere_network:
    @pytest.mark.parametrize(
        ["value", "expected"], [[4, "0.0.0.0/0"], ["4", "0.0.0.0/0"], [6, "::/0"], ["6", "::/0"]]
    )
    def test_normal(self, value, expected):
        assert get_anywhere_network(value) == expected

    @pytest.mark.parametrize(["value", "expected"], [[None, ValueError], ["test", ValueError]])
    def test_exception(self, value, expected):
        with pytest.raises(expected):
            get_anywhere_network(value)


class Test_get_upper_limit_rate:
    @pytest.mark.parametrize(["speed", "expected"], [[1, 1000], [0, 0]])
    def test_normal(self, monkeypatch, device_option, speed, expected):
        if device_option is None:
            pytest.skip("device option is null")

        monkeypatch.setattr("tcconfig._network._read_iface_speed", lambda x: speed)

        assert get_upper_limit_rate(device_option).kilo_bps == expected

    @pytest.mark.parametrize(["speed", "expected"], [[-1, _get_iproute2_upper_limite_rate()]])
    def test_normal_paravirt(self, monkeypatch, device_option, speed, expected):
        if device_option is None:
            pytest.skip("device option is null")

        monkeypatch.setattr("tcconfig._network._read_iface_speed", lambda x: speed)

        assert get_upper_limit_rate(device_option) == expected

    @staticmethod
    def raise_ioerror(tc_device):
        raise OSError()

    def test_exception(self, monkeypatch, device_option):
        if device_option is None:
            pytest.skip("device option is null")

        monkeypatch.setattr("tcconfig._network._read_iface_speed", self.raise_ioerror)

        assert get_upper_limit_rate(device_option) == _get_iproute2_upper_limite_rate()


class Test_sanitize_network:
    @pytest.mark.parametrize(
        ["value", "ip_version", "expected"],
        [
            ["192.168.0.1", 4, "192.168.0.1/32"],
            ["192.168.0.1/32", 4, "192.168.0.1/32"],
            ["192.168.0.0/24", 4, "192.168.0.0/24"],
            ["192.168.0.0/23", 4, "192.168.0.0/23"],
            ["2001:db00::0/24", 6, "2001:db00::/24"],
            ["anywhere", 4, "0.0.0.0/0"],
            ["ANYWHERE", 4, "0.0.0.0/0"],
            ["anywhere", 6, "::/0"],
            ["ANYWHERE", 6, "::/0"],
            ["", 4, "0.0.0.0/0"],
            [None, 4, "0.0.0.0/0"],
            ["", 6, "::/0"],
            [None, 6, "::/0"],
        ],
    )
    def test_normal(self, value, ip_version, expected):
        assert sanitize_network(value, ip_version) == expected

    @pytest.mark.parametrize(
        ["value", "ip_version", "expected"],
        [
            ["192.168.0.1111", 4, ValueError],
            ["192.168.0.", 4, ValueError],
            [".168.0.1", 4, ValueError],
            ["192.168.1.0/23", 4, ValueError],
            ["192.168.0.0/33", 4, ValueError],
            ["192.168.1.0/24", 6, ValueError],
            ["2001:db00::0/24", 4, ValueError],
        ],
    )
    def test_exception(self, value, ip_version, expected):
        with pytest.raises(expected):
            sanitize_network(value, ip_version)
