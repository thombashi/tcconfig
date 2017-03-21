#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import unicode_literals
import sys

from path import Path
import readmemaker


PROJECT_NAME = "tcconfig"
OUTPUT_DIR = ".."


def write_examples(maker):
    maker.set_indent_level(0)
    maker.write_chapter("Usage")

    usage_root = Path("pages").joinpath("usage")

    maker.inc_indent_level()
    maker.write_chapter("Set traffic control (``tcset`` command)")
    maker.write_file(usage_root.joinpath("tcset", "description.txt"))
    maker.write_file(usage_root.joinpath("tcset", "basic_usage.rst"))

    maker.write_file(usage_root.joinpath("tcdel", "header.rst"))
    maker.write_file(usage_root.joinpath("tcdel", "usage.rst"))

    maker.write_file(usage_root.joinpath("tcshow", "header.rst"))
    maker.write_file(usage_root.joinpath("tcshow", "usage.rst"))

    maker.write_chapter("For more information")
    maker.write_line_list([
        "More examples are available at ",
        "http://{:s}.rtfd.io/en/latest/pages/usage/index.html".format(
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
        "http://{:s}.rtfd.io/".format(PROJECT_NAME),
    ])

    maker.write_chapter("Troubleshooting")
    maker.write_line_list([
        "http://tcconfig.readthedocs.io/en/latest/pages/troubleshooting.html",
    ])

    return 0


if __name__ == '__main__':
    sys.exit(main())
