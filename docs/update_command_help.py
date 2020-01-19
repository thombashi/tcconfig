#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import print_function, unicode_literals

import os
from textwrap import indent

from subprocrunner import SubprocessRunner


for command in ["tcset", "tcdel", "tcshow"]:
    proc = SubprocessRunner("{:s} -h".format(command))
    proc.run(env=dict(os.environ, LC_ALL="C.UTF-8"))
    help_file_path = "pages/usage/{command:s}/{command:s}_help_output.txt".format(command=command)

    print(help_file_path)

    with open(help_file_path, "w") as f:
        f.write("::\n\n")
        f.write(indent(proc.stdout, "    "))
