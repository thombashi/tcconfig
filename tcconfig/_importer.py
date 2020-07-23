"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

import errno
import re
from typing import Optional

import msgfy
import pyparsing as pp
import subprocrunner as spr

from ._const import Network, Tc, TcCommandOutput, TrafficDirection


try:
    import ujson as json
except ImportError:
    import json  # type: ignore


RE_CONTAINER_ID = re.compile(r"[a-z0-9]{12}\s+\(device=[a-z0-9]+\)")
# e.g. edfd9dbb3969 (device=veth6f7b798)


class TcConfigLoader:
    def __init__(self, logger):
        self.__logger = logger
        self.__config_table = None
        self.is_overwrite = False
        self.tc_command_output = TcCommandOutput.NOT_SET

    def load_tcconfig(self, config_file_path):
        from voluptuous import ALLOW_EXTRA, Any, Required, Schema

        schema = Schema(
            {Required(str): {Any(*TrafficDirection.LIST): {str: {str: Any(str, int, float)}}}},
            extra=ALLOW_EXTRA,
        )

        with open(config_file_path, encoding="utf-8") as fp:
            self.__config_table = json.load(fp)

        schema(self.__config_table)
        self.__logger.debug(
            "tc config file: {:s}".format(json.dumps(self.__config_table, indent=4))
        )

    def get_tcconfig_commands(self):
        from .tcset import get_arg_parser

        command_list = []

        for device, device_table in self.__config_table.items():
            is_container = RE_CONTAINER_ID.search(device) is not None
            if is_container:
                device = device.split()[0]

            if self.is_overwrite:
                command_list.append(
                    " ".join(
                        [Tc.Command.TCDEL, device, "--all"] + (["--docker"] if is_container else [])
                    )
                )

            for direction, direction_table in device_table.items():
                is_first_set = True

                for tc_filter, filter_table in direction_table.items():
                    self.__logger.debug(
                        "is_first_set={}, filter='{}', table={}".format(
                            is_first_set, tc_filter, filter_table
                        )
                    )

                    if not filter_table:
                        continue

                    option_list = [device, "--direction={:s}".format(direction)] + (
                        ["--docker"] if is_container else []
                    )

                    for key, value in filter_table.items():
                        arg_item = "--{:s}={}".format(key, value)

                        parse_result = get_arg_parser().parse_known_args(["dummy", arg_item])
                        if parse_result[1]:
                            self.__logger.debug(
                                "unknown parameter: key={}, value={}".format(key, value)
                            )
                            continue

                        option_list.append(arg_item)

                    try:
                        src_network = self.__parse_tc_filter_src_network(tc_filter)
                        if src_network not in (Network.Ipv4.ANYWHERE, Network.Ipv6.ANYWHERE):
                            option_list.append("--src-network={:s}".format(src_network))
                    except pp.ParseException:
                        pass

                    try:
                        dst_network = self.__parse_tc_filter_dst_network(tc_filter)
                        if dst_network not in (Network.Ipv4.ANYWHERE, Network.Ipv6.ANYWHERE):
                            option_list.append("--dst-network={:s}".format(dst_network))
                    except pp.ParseException:
                        pass

                    try:
                        src_port = self.__parse_tc_filter_src_port(tc_filter)
                        option_list.append("--src-port={}".format(src_port))
                    except pp.ParseException:
                        pass

                    try:
                        dst_port = self.__parse_tc_filter_dst_port(tc_filter)
                        option_list.append("--dst-port={}".format(dst_port))
                    except pp.ParseException:
                        pass

                    if not is_first_set:
                        option_list.append("--add")

                    if self.tc_command_output == TcCommandOutput.STDOUT:
                        option_list.append("--tc-command")
                    elif self.tc_command_output == TcCommandOutput.SCRIPT:
                        option_list.append("--tc-script")

                    is_first_set = False

                    command_list.append(" ".join([Tc.Command.TCSET] + option_list))

        return command_list

    @staticmethod
    def __parse_tc_filter_src_network(text):
        network_pattern = pp.SkipTo("{:s}=".format(Tc.Param.SRC_NETWORK), include=True) + pp.Word(
            pp.alphanums + "." + "/"
        )

        return network_pattern.parseString(text)[-1]

    @staticmethod
    def __parse_tc_filter_dst_network(text):
        network_pattern = pp.SkipTo("{:s}=".format(Tc.Param.DST_NETWORK), include=True) + pp.Word(
            pp.alphanums + "." + "/"
        )

        return network_pattern.parseString(text)[-1]

    @staticmethod
    def __parse_tc_filter_src_port(text):
        port_pattern = pp.SkipTo("{:s}=".format(Tc.Param.SRC_PORT), include=True) + pp.Word(pp.nums)

        return port_pattern.parseString(text)[-1]

    @staticmethod
    def __parse_tc_filter_dst_port(text):
        port_pattern = pp.SkipTo("{:s}=".format(Tc.Param.DST_PORT), include=True) + pp.Word(pp.nums)

        return port_pattern.parseString(text)[-1]


def set_tc_from_file(
    logger, config_file_path: str, is_overwrite: bool, tc_command_output: Optional[str]
) -> int:
    return_code = 0

    loader = TcConfigLoader(logger)
    loader.is_overwrite = is_overwrite
    loader.tc_command_output = tc_command_output

    try:
        loader.load_tcconfig(config_file_path)
    except OSError as e:
        logger.error(msgfy.to_error_message(e))
        return errno.EIO

    for tcconfig_command in loader.get_tcconfig_commands():
        runner = spr.SubprocessRunner(tcconfig_command)
        return_code |= runner.run()

        if return_code != 0:
            logger.error(runner.stderr)
        elif tc_command_output == TcCommandOutput.STDOUT:
            print(runner.stdout.strip())

    return return_code
