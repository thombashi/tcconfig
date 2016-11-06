# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals
import re


def __null_line_strip(line):
    return line


def __line_strip(line):
    return line.strip()


def split_line_list(
        line_list, re_line_separator=re.compile("^$"),
        is_include_match_line=False, is_strip=True):
    block_list = []
    block = []
    strip_func = __line_strip if is_strip else __null_line_strip

    for line in line_list:
        line = strip_func(line)

        if re_line_separator.search(line):
            if len(block) > 0:
                block_list.append(block)

            block = []
            if is_include_match_line:
                block.append(line)
            continue

        block.append(line)

    if len(block) > 0:
        block_list.append(block)

    return block_list
