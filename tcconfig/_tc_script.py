# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import, unicode_literals

import datetime
import io
import os
import sys

import typepy

from ._const import Tc
from ._logger import logger


def write_tc_script(tcconfig_command, command_history, filename_suffix=None):
    filename_item_list = [tcconfig_command]
    if typepy.is_not_null_string(filename_suffix):
        filename_item_list.append(filename_suffix)

    script_line_list = ["#!/bin/sh", ""]

    org_tcconfig_cmd = _get_original_tcconfig_command(tcconfig_command)

    if tcconfig_command != Tc.Command.TCSHOW:
        script_line_list.extend(
            [
                "# command sequence in this script attempt to simulate the following "
                "tcconfig command:",
                "#",
                "#   {:s}".format(org_tcconfig_cmd),
            ]
        )

    script_line_list.extend(
        [
            "#",
            "# the script execution result may different from '{}'".format(org_tcconfig_cmd),
            "#",
            "# created by {:s} on {:s}.".format(
                tcconfig_command, datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
            ),
            "",
            command_history,
        ]
    )

    filename = "_".join(filename_item_list) + ".sh"
    with io.open(filename, "w", encoding="utf8") as fp:
        fp.write("\n".join(script_line_list) + "\n")

    os.chmod(filename, 0o755)
    logger.info("written a tc script to '{:s}'".format(filename))


def _get_original_tcconfig_command(tcconfig_command):
    return " ".join(
        [tcconfig_command]
        + [command_item for command_item in sys.argv[1:] if command_item != "--tc-script"]
    )
