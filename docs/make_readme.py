#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import unicode_literals

import sys

from path import Path
from readmemaker import ReadmeMaker


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
    maker.write_file(usage_root.joinpath("tcset", "docker_usage.rst"))

    maker.write_file(usage_root.joinpath("tcdel", "header.rst"))
    maker.write_file(usage_root.joinpath("tcdel", "usage.rst"))

    maker.write_file(usage_root.joinpath("tcshow", "header.rst"))
    maker.write_file(usage_root.joinpath("tcshow", "usage.rst"))

    maker.write_chapter("For more information")
    maker.write_lines(
        [
            "More examples are available at ",
            "https://{:s}.rtfd.io/en/latest/pages/usage/index.html".format(PROJECT_NAME),
        ]
    )


def main():
    maker = ReadmeMaker(
        PROJECT_NAME,
        OUTPUT_DIR,
        is_make_toc=True,
        project_url="https://github.com/thombashi/{}".format(PROJECT_NAME),
    )
    maker.examples_dir_name = "usage"

    maker.write_chapter("Summary")
    maker.write_introduction_file("summary.txt")
    maker.write_introduction_file("badges.txt")
    maker.write_introduction_file("feature.txt")

    maker.write_lines([".. image:: docs/gif/tcset_example.gif"])

    write_examples(maker)

    maker.write_lines([])
    maker.write_file(maker.doc_page_root_dir_path.joinpath("installation.rst"))

    maker.set_indent_level(0)
    maker.write_chapter("Documentation")
    maker.write_lines(["https://{:s}.rtfd.io/".format(PROJECT_NAME)])

    maker.write_chapter("Troubleshooting")
    maker.write_lines(
        ["https://{:s}.rtfd.io/en/latest/pages/troubleshooting.html".format(PROJECT_NAME)]
    )

    maker.write_chapter("Docker image")
    maker.write_lines(["https://hub.docker.com/r/thombashi/tcconfig/"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
