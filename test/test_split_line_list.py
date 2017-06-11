# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import unicode_literals

import re

import pytest

from tcconfig._split_line_list import split_line_list


class Test_split_line_list(object):

    @pytest.mark.parametrize(
        [
            "value", "separator", "is_include_matched_line",
            "is_strip", "expected",
        ],
        [
            [
                [
                    "abcdefg",
                    "ABCDEFG",
                    "1234",
                ],
                re.compile("DEFG$"),
                False,
                True,
                [
                    ["abcdefg"],
                    ["1234"],
                ],
            ],
            [
                [
                    "abcdefg",
                    "ABCDEFG",
                    "ABCDEFG",
                    "1234",
                ],
                re.compile("DEFG$"),
                False,
                True,
                [
                    ["abcdefg"],
                    ["1234"],
                ],
            ],
            [
                [
                    "ABCDEFG",
                    "abcdefg",
                    "ABCDEFG",
                    "1234",
                    "ABCDEFG",
                ],
                re.compile("DEFG$"),
                False,
                True,
                [
                    ["abcdefg"],
                    ["1234"],
                ],
            ],
            [
                [
                    "abcdefg",
                    "ABCDEFG",
                    "1234"
                ],
                re.compile("DEFG$"),
                True,
                True,
                [
                    ["abcdefg"],
                    [
                        "ABCDEFG",
                        "1234",
                    ],
                ],
            ],
            [
                ["a", "  ", "b", "c"],
                re.compile("^$"),
                False,
                True,
                [
                    ["a"],
                    ["b", "c"]
                ],
            ],
            [
                ["a", "  ", "b", "c"],
                re.compile("^$"),
                False,
                False,
                [
                    ["a", "  ", "b", "c"],
                ],
            ],
        ])
    def test_normal(
            self, value, separator, is_include_matched_line, is_strip,
            expected):
        assert split_line_list(
            value, separator, is_include_matched_line, is_strip) == expected

    @pytest.mark.parametrize(
        [
            "value", "separator", "is_include_matched_line",
            "is_strip", "expected",
        ],
        [
            [None, "", False, True, TypeError],
            [["a", "b", "c"], None, False, True, AttributeError],
            [[1, 2, 3], re.compile(""), False, True, AttributeError],
            [[1, 2, 3], re.compile(""), False, False, TypeError],
        ])
    def test_exception(
            self, value, separator, is_include_matched_line, is_strip,
            expected):
        with pytest.raises(expected):
            split_line_list(
                value, separator, is_include_matched_line, is_strip)
