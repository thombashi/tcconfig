#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import unicode_literals
import os.path
import sys

import readmemaker


PROJECT_NAME = "tcconfig"
OUTPUT_DIR = ".."


def write_examples(maker):
    maker.set_indent_level(0)
    maker.write_chapter("Usage")

    maker.inc_indent_level()
    maker.write_chapter("Set traffic control (``tcset`` command)")
    maker.write_example_file(os.path.join("tcset", "description.txt"))
    maker.write_example_file(os.path.join("tcset", "basic_usage.rst"))

    maker.write_example_file(os.path.join("tcdel", "header.rst"))
    maker.write_example_file(os.path.join("tcdel", "usage.rst"))

    maker.write_example_file(os.path.join("tcshow", "header.rst"))
    maker.write_example_file(os.path.join("tcshow", "usage.rst"))

    maker.write_chapter("For more information")
    maker.write_line_list([
        "More examples are available at ",
        "http://{:s}.readthedocs.org/en/latest/pages/usage/index.html".format(
            PROJECT_NAME),
    ])


def main():
    maker = readmemaker.ReadmeMaker(PROJECT_NAME, OUTPUT_DIR)
    maker.examples_dir_name = "usage"

    maker.write_introduction_file("badges.txt")

    maker.inc_indent_level()
    maker.write_chapter("Summary")
    maker.write_introduction_file("summary.txt")
    maker.write_introduction_file("feature.txt")
    maker.write_line_list([
        ".. image:: docs/gif/tcset_example.gif",
    ])

    write_examples(maker)

    maker.write_file(
        maker.doc_page_root_dir_path.joinpath("installation.rst"))

    maker.set_indent_level(0)
    maker.write_chapter("Documentation")
    maker.write_line_list([
        "http://{:s}.readthedocs.org/en/latest/".format(PROJECT_NAME),
    ])

    maker.write_file(
        maker.doc_page_root_dir_path.joinpath("troubleshooting.rst"))

    return 0


if __name__ == '__main__':
    sys.exit(main())
