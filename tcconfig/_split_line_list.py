"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""


import re


def __null_line_strip(line):
    return line


def __line_strip(line):
    return line.strip()


def split_line_list(line_list, re_block_separator=None, is_include_match_line=False, is_strip=True):
    block_list = []
    block = []
    strip_func = __line_strip if is_strip else __null_line_strip

    if not re_block_separator:
        re_block_separator = re.compile("^$")

    for line in line_list:
        line = strip_func(line)

        if re_block_separator.search(line):
            if block:
                block_list.append(block)

            block = []
            if is_include_match_line:
                block.append(line)
            continue

        block.append(line)

    if block:
        block_list.append(block)

    return block_list
