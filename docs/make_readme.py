#!/usr/bin/env python3

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

import os
import sys
from textwrap import indent

from path import Path
from readmemaker import ReadmeMaker
from subprocrunner import SubprocessRunner


PROJECT_NAME = "tcconfig"
OUTPUT_DIR = ".."


def write_examples(maker: ReadmeMaker) -> None:
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
            f"https://{PROJECT_NAME:s}.rtfd.io/en/latest/pages/usage/index.html",
        ]
    )


def update_help() -> None:
    for command in ["tcset", "tcdel", "tcshow"]:
        runner = SubprocessRunner(f"{command:s} -h")
        runner.run(env=dict(os.environ, LC_ALL="C.UTF-8"))
        help_file_path = "pages/usage/{command:s}/{command:s}_help_output.txt".format(
            command=command
        )

        print(help_file_path)

        assert runner.returncode == 0
        assert runner.stdout
        with open(help_file_path, "w") as f:
            f.write("::\n\n")
            f.write(indent(runner.stdout, "    "))


def main() -> int:
    update_help()

    maker = ReadmeMaker(
        PROJECT_NAME,
        OUTPUT_DIR,
        is_make_toc=True,
        project_url=f"https://github.com/thombashi/{PROJECT_NAME}",
    )

    maker.write_chapter("Summary")
    maker.write_introduction_file("summary.txt")
    maker.write_introduction_file("badges.txt")
    maker.write_introduction_file("feature.txt")

    maker.write_lines([".. image:: docs/gif/tcset_example.gif"])

    write_examples(maker)

    maker.write_lines([])
    maker.write_introduction_file("installation.rst")

    maker.set_indent_level(0)
    maker.write_chapter("Documentation")
    maker.write_lines([f"https://{PROJECT_NAME:s}.rtfd.io/"])

    maker.write_chapter("Troubleshooting")
    maker.write_lines([f"https://{PROJECT_NAME:s}.rtfd.io/en/latest/pages/troubleshooting.html"])

    maker.write_chapter("Docker image")
    maker.write_lines(["https://hub.docker.com/r/thombashi/tcconfig/"])

    maker.write_file(maker.doc_page_root_dir_path.joinpath("sponsors.rst"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
