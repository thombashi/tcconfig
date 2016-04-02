#!/usr/bin/env python
# encoding: utf-8


import os
import sys


VERSION = "0.4.0"
OUTPUT_DIR = ".."
README_WORK_DIR = "."
DOC_PAGE_DIR = os.path.join(README_WORK_DIR, "pages")


def get_usage_file_path(filename):
    return os.path.join(DOC_PAGE_DIR, "usage", filename)


def write_line_list(f, line_list):
    f.write("\n".join(line_list))
    f.write("\n" * 2)


def write_usage_file(f, filename):
    write_line_list(f, [
        line.rstrip()
        for line in
        open(get_usage_file_path(filename)).readlines()
    ])


def write_examples(f):
    write_line_list(f, [
        "Usage",
        "=====",
    ])

    write_usage_file(f, os.path.join("tcset", "header.rst"))
    write_line_list(f, [
        line.rstrip().replace("^", "~")
        for line in
        open(get_usage_file_path(
            os.path.join("tcset", "basic_usage.rst"))).readlines()
    ])

    write_usage_file(f, os.path.join("tcdel", "header.rst"))
    write_usage_file(f, os.path.join("tcdel", "usage.rst"))

    write_usage_file(f, os.path.join("tcshow", "header.rst"))
    write_usage_file(f, os.path.join("tcshow", "usage.rst"))

    write_line_list(f, [
        "For more information",
        "--------------------",
        "More examples are available at ",
        "http://tcconfig.readthedocs.org/en/latest/pages/usage/index.html",
        "",
    ])


def main():
    with open(os.path.join(OUTPUT_DIR, "README.rst"), "w") as f:
        write_line_list(f, [
            line.rstrip() for line in
            open(os.path.join(DOC_PAGE_DIR, "introduction.rst")).readlines()
        ])
        write_line_list(f, [
            ".. image:: docs/gif/tcset_example.gif",
        ])

        write_examples(f)

        write_line_list(f, [
            line.rstrip() for line in
            open(os.path.join(DOC_PAGE_DIR, "installation.rst")).readlines()
        ])

        write_line_list(f, [
            "Documentation",
            "=============",
            "",
            "http://tcconfig.readthedocs.org/en/latest/"
        ])

if __name__ == '__main__':
    sys.exit(main())
