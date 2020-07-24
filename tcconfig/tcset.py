#!/usr/bin/env python3

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""


import errno
import ipaddress
import sys

import humanreadable as hr
import msgfy
import subprocrunner as spr
from loguru import logger

from .__version__ import __version__
from ._argparse_wrapper import ArgparseWrapper
from ._capabilities import check_execution_authority
from ._common import initialize_cli, is_execute_tc_command, normalize_tc_value
from ._const import (
    DELAY_DISTRIBUTIONS,
    IPV6_OPTION_ERROR_MSG_FORMAT,
    ShapingAlgorithm,
    Tc,
    TrafficDirection,
)
from ._error import ContainerNotFoundError, ModuleNotFoundError, NetworkInterfaceNotFoundError
from ._importer import set_tc_from_file
from ._logger import set_log_level
from ._main import Main
from ._netem_param import (
    MAX_CORRUPTION_RATE,
    MAX_PACKET_DUPLICATE_RATE,
    MAX_PACKET_LOSS_RATE,
    MAX_REORDERING_RATE,
    MIN_CORRUPTION_RATE,
    MIN_PACKET_DUPLICATE_RATE,
    MIN_PACKET_LOSS_RATE,
    MIN_REORDERING_RATE,
    NetemParameter,
)
from ._shaping_rule_finder import TcShapingRuleFinder
from .traffic_control import TrafficControl


def _get_unit_help_msg():
    return ", ".join(["/".join(values) for values in hr.Time.get_text_units().values()])


def get_arg_parser():
    parser = ArgparseWrapper(__version__)

    if {"-d", "--device"}.intersection(set(sys.argv)):
        # deprecated: remain for backward compatibility
        parser.parser.add_argument(
            "-d", "--device", required=True, help="network device name (e.g. eth0)"
        )
    else:
        parser.parser.add_argument(
            "device", help="target name: network-interface/config-file (e.g. eth0)"
        )

    parser.parser.add_argument(
        "--import-setting",
        action="store_true",
        default=False,
        help="import traffic control settings from a configuration file.",
    )

    group = parser.parser.add_mutually_exclusive_group()
    group.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="overwrite existing traffic shaping rules.",
    )
    group.add_argument(
        "--change",
        dest="is_change_shaping_rule",
        action="store_true",
        default=False,
        help="""change existing traffic shaping rules to the new one.
        this option is effective to reduce the time between the shaping rule switching
        compared to --overwrite option.
        note: just adds a shaping rule if there are no existing shaping rules.
        """,
    )
    group.add_argument(
        "--add",
        dest="is_add_shaping_rule",
        action="store_true",
        default=False,
        help="add a traffic shaping rule in addition to existing rules.",
    )

    group = parser.parser.add_argument_group("Traffic Control Parameters")
    group.add_argument(
        "--rate",
        "--bandwidth-rate",
        dest="bandwidth_rate",
        help="""network bandwidth rate [bit per second].
        the minimum bandwidth rate is 8 bps.
        valid units are either: {}.
        e.g. tcset eth0 --rate 10Mbps
        """.format(
            ", ".join([", ".join(values) for values in hr.BitPerSecond.get_text_units().values()])
        ),
    )
    group.add_argument(
        "--delay",
        dest="latency_time",
        default=Tc.ValueRange.LatencyTime.MIN,
        help="""round trip network delay. the valid range is from {min_value:} to {max_value:}.
        valid time units are: {unit}. if no unit string found, considered milliseconds as
        the time unit. (default=%(default)s)
        """.format(
            min_value=Tc.ValueRange.LatencyTime.MIN,
            max_value=Tc.ValueRange.LatencyTime.MAX,
            unit=_get_unit_help_msg(),
        ),
    )
    group.add_argument(
        "--delay-distro",
        dest="latency_distro_time",
        default=Tc.ValueRange.LatencyTime.MIN,
        help="""distribution of network latency becomes X +- Y (normal distribution).
        Here X is the value of --delay option and Y is the value of --delay-dist option).
        network latency distribution is uniform, without this option. valid time units are: {unit}.
        if no unit string found, considered milliseconds as the time unit.
        """.format(
            unit=_get_unit_help_msg()
        ),
    )
    group.add_argument(
        "--delay-distribution",
        dest="latency_distribution",
        choices=DELAY_DISTRIBUTIONS,
        default=DELAY_DISTRIBUTIONS[0],
        help="""choose the delay distribution. (default=%(default)s)",
        [limitation] this parameter can not be shown by tcshow, and export/import as config.
        """,
    )
    group.add_argument(
        "--loss",
        dest="packet_loss_rate",
        default=0,
        help="""round trip packet loss rate [%%]. the valid range is from {:d}
        to {:d}. (default=%(default)s)
        """.format(
            MIN_PACKET_LOSS_RATE, MAX_PACKET_LOSS_RATE
        ),
    )
    group.add_argument(
        "--duplicate",
        dest="packet_duplicate_rate",
        default=0,
        help="""round trip packet duplicate rate [%%]. the valid range is
        from {:d} to {:d}. (default=%(default)s)
        """.format(
            MIN_PACKET_DUPLICATE_RATE, MAX_PACKET_DUPLICATE_RATE
        ),
    )
    group.add_argument(
        "--corrupt",
        dest="corruption_rate",
        default=0,
        help="""packet corruption rate [%%]. the valid range is from {:d} to {:d}.
        packet corruption means single bit error at a random offset in the packet.
        (default=%(default)s)
        """.format(
            MIN_CORRUPTION_RATE, MAX_CORRUPTION_RATE
        ),
    )
    group.add_argument(
        "--reordering",
        dest="reordering_rate",
        default=0,
        help="""packet reordering rate [%%]. the valid range is from {:d}
        to {:d}. (default=%(default)s)
        """.format(
            MIN_REORDERING_RATE, MAX_REORDERING_RATE
        ),
    )
    group.add_argument(
        "--shaping-algo",
        dest="shaping_algorithm",
        choices=[ShapingAlgorithm.HTB, ShapingAlgorithm.TBF],
        default=ShapingAlgorithm.HTB,
        help="shaping algorithm. defaults to %(default)s (recommended).",
    )
    group.add_argument(
        "--iptables",
        dest="is_enable_iptables",
        action="store_true",
        default=False,
        help="use iptables to traffic control.",
    )

    group = parser.add_routing_group()
    group.add_argument(
        "--exclude-dst-network",
        help="exclude a specific destination IP-address/network from a shaping rule.",
    )
    group.add_argument(
        "--exclude-src-network",
        help="exclude a specific source IP-address/network from a shaping rule.",
    )
    group.add_argument(
        "--exclude-dst-port", help="exclude a specific destination port from a shaping rule."
    )
    group.add_argument(
        "--exclude-src-port", help="exclude a specific source port from a shaping rule."
    )

    parser.add_docker_group()

    return parser.parser


def verify_netem_module():
    import re

    runner = spr.SubprocessRunner("lsmod")

    try:
        if runner.run() != 0:
            raise OSError(runner.returncode, "failed to execute lsmod")
    except spr.CommandError as e:
        # reach here when the kmod package not installed.
        # this kind of environments could exist such as slim Docker containers.
        logger.debug(msgfy.to_debug_message(e))
    else:
        if re.search(r"\bsch_netem\b", runner.stdout) is None:
            raise ModuleNotFoundError("sch_netem module not found")


class TcSetMain(Main):
    def run(self):
        return_code_list = []

        for device in self._fetch_tc_targets():
            tc = self.__create_tc(device)
            return_code = self.__check_tc(tc)

            if return_code != 0:
                return_code_list.append(return_code)
                continue

            normalize_tc_value(tc)

            if self._options.overwrite:
                if self._options.log_level == "INFO":
                    set_log_level("ERROR")

                try:
                    tc.delete_all_rules()
                except NetworkInterfaceNotFoundError:
                    pass

                set_log_level(self._options.log_level)

            if (
                self._options.is_add_shaping_rule
                and TcShapingRuleFinder(logger=logger, tc=tc).is_exist_rule()
            ):
                logger.error(
                    "\n".join(
                        [
                            "adding a shaping rule failed. a shaping rule for the same "
                            "network/port already exist. try to execute with:",
                            "  (a) --overwrite option if you want to overwrite "
                            "the existing rules.",
                            "  (b) --change option if you want to change "
                            "the existing rule parameters.",
                        ]
                    )
                )
                return errno.EINVAL

            try:
                return_code_list.append(tc.set_shaping_rule())
            except NetworkInterfaceNotFoundError as e:
                logger.error(e)
                return errno.EINVAL

            self._dump_history(tc, Tc.Command.TCSET)

        return self._get_return_code(return_code_list)

    def __check_tc(self, tc):
        try:
            tc.validate()
        except (NetworkInterfaceNotFoundError, ContainerNotFoundError) as e:
            logger.error(e)
            return errno.EINVAL
        except ipaddress.AddressValueError as e:
            logger.error(IPV6_OPTION_ERROR_MSG_FORMAT.format(e))
            return errno.EINVAL
        except hr.ParameterError as e:
            logger.error(msgfy.to_error_message(e))
            return errno.EINVAL

        return 0

    def __create_tc(self, device):
        options = self._options

        return TrafficControl(
            device,
            direction=options.direction,
            netem_param=NetemParameter(
                device=device,
                bandwidth_rate=options.bandwidth_rate,
                latency_time=options.latency_time,
                latency_distro_time=options.latency_distro_time,
                latency_distribution=options.latency_distribution,
                packet_loss_rate=options.packet_loss_rate,
                packet_duplicate_rate=options.packet_duplicate_rate,
                corruption_rate=options.corruption_rate,
                reordering_rate=options.reordering_rate,
            ),
            dst_network=self._extract_dst_network(),
            exclude_dst_network=options.exclude_dst_network,
            src_network=self._extract_src_network(),
            exclude_src_network=options.exclude_src_network,
            src_port=options.src_port,
            exclude_src_port=options.exclude_src_port,
            dst_port=options.dst_port,
            exclude_dst_port=options.exclude_dst_port,
            is_ipv6=options.is_ipv6,
            is_change_shaping_rule=options.is_change_shaping_rule,
            is_add_shaping_rule=options.is_add_shaping_rule,
            is_enable_iptables=options.is_enable_iptables,
            shaping_algorithm=options.shaping_algorithm,
            tc_command_output=options.tc_command_output,
        )


def main():
    options = get_arg_parser().parse_args()

    initialize_cli(options)

    if is_execute_tc_command(options.tc_command_output):
        check_execution_authority("tc")

        if options.direction == TrafficDirection.INCOMING:
            check_execution_authority("ip")
    else:
        if not options.import_setting:
            spr.SubprocessRunner.default_is_dry_run = True

    try:
        verify_netem_module()
    except ModuleNotFoundError as e:
        logger.debug(e)

    if options.import_setting:
        return set_tc_from_file(
            logger, options.device, options.overwrite, options.tc_command_output
        )

    spr.SubprocessRunner.clear_history()

    return TcSetMain(options).run()


if __name__ == "__main__":
    sys.exit(main())
