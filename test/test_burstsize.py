"""
.. codeauthor:: Jonathan Lennox <jonathan.lennox@8x8.com>
"""

import humanreadable as hr
import pytest

from tcconfig.shaper.htb import adjusted_burst_size, default_burst_size


@pytest.mark.parametrize(
    ["rate_hr", "mtu", "expected"],
    [
        ("1Mbps", 1600, 1600),
        ("1Gbps", 1600, 1600),
        ("8Gbps", 1600, 1601),
        ("80Gbps", 1600, 1610),
        ("80Gbps", 9000, 9010),
    ],
)
def test_default_burst(rate_hr, mtu, expected):
    rate = hr.BitsPerSecond(rate_hr).byte_per_sec
    default_burst = default_burst_size(rate, mtu)
    assert default_burst == expected


@pytest.mark.parametrize(
    ["desired_burst", "rate_hr", "expected"],
    [
        (1600, "1Mbps", 1600),
        (1600, "1Gbps", 1625),
        (1600, "8Gbps", 2000),
        (1610, "80Gbps", 10000),
        (9010, "80Gbps", 10000),
    ],
)
def test_adjusted_burst(monkeypatch, desired_burst, rate_hr, expected):
    monkeypatch.setattr("tcconfig.shaper.htb.tick_in_usec", lambda: 15.625)
    rate = hr.BitsPerSecond(rate_hr).byte_per_sec
    adjusted_burst = adjusted_burst_size(desired_burst, rate)
    assert adjusted_burst == expected
