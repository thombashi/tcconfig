# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
import re


def split_line_list(
        line_list, re_line_separator=re.compile("^$"),
        is_include_match_line=False, is_strip=True):
    block_list = []
    block = []

    for line in line_list:
        if is_strip:
            line = line.strip()

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
