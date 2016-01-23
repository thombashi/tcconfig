#!/usr/bin/env python
# encoding: utf-8

'''
@author: Tsuyoshi Hombashi
'''

from __future__ import with_statement
import sys

import thutils
import tcconfig


def parse_option():
    parser = thutils.option.ArgumentParserObject()
    parser.make(version=tcconfig.VERSION)

    group = parser.add_argument_group("Traffic Control")
    group.add_argument(
        "--device", required=True,
        help="network device name")
    group.add_argument(
        "--rate",
        help="network bandwidth [K|M|G bps]")
    group.add_argument(
        "--delay", type=float, default=0,
        help="round trip network delay [ms] (default=%(default)s)")
    group.add_argument(
        "--loss", type=float, default=0,
        help="round trip packet loss rate [%%] (default=%(default)s)")
    group.add_argument(
        "--overwrite", action="store_true", default=False,
        help="overwrite existing setting")

    return parser.parse_args()


@thutils.main.Main
def main():
    options = parse_option()

    thutils.initialize_library(__file__, options)
    thutils.common.verify_install_command(["tc"])

    subproc_wrapper = thutils.subprocwrapper.SubprocessWrapper()

    if options.overwrite:
        tcconfig.delete_tc(subproc_wrapper, options.device)

    tcconfig.set_tc(subproc_wrapper, options.device,
                    options.rate, options.delay, options.loss)

    return 0


if __name__ == '__main__':
    sys.exit(main())
