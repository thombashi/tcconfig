# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import, unicode_literals

import errno
import io

import msgfy
import pyparsing as pp
import simplejson as json
import six
import subprocrunner as spr

from ._const import Network, Tc, TrafficDirection


class TcConfigLoader(object):
    def __init__(self, logger):
        self.__logger = logger
        self.__config_table = None
        self.is_overwrite = False

    def load_tcconfig(self, config_file_path):
        from voluptuous import Schema, Required, Any, ALLOW_EXTRA

        schema = Schema(
            {
                Required(six.text_type): {
                    Any(*TrafficDirection.LIST): {
                        six.text_type: {six.text_type: Any(six.text_type, int, float)}
                    }
                }
            },
            extra=ALLOW_EXTRA,
        )

        with io.open(config_file_path, encoding="utf-8") as fp:
            self.__config_table = json.load(fp)

        schema(self.__config_table)
        self.__logger.debug(
            "tc config file: {:s}".format(json.dumps(self.__config_table, indent=4))
        )

    def get_tcconfig_commands(self):
        from .tcset import get_arg_parser

        command_list = []

        for device, device_table in six.iteritems(self.__config_table):
            if self.is_overwrite:
                command_list.append(" ".join([Tc.Command.TCDEL, device, "--all"]))

            for direction, direction_table in six.iteritems(device_table):
                is_first_set = True

                for tc_filter, filter_table in six.iteritems(direction_table):
                    self.__logger.debug(
                        "is_first_set={}, filter='{}', table={}".format(
                            is_first_set, tc_filter, filter_table
                        )
                    )

                    if not filter_table:
                        continue

                    option_list = [device, "--direction={:s}".format(direction)]
                    for key, value in six.iteritems(filter_table):
                        arg_item = "--{:s}={}".format(key, value)

                        parse_result = get_arg_parser().parse_known_args(["dummy", arg_item])
                        if parse_result[1]:
                            self.__logger.debug(
                                "unknown parameter: key={}, value={}".format(key, value)
                            )
                            continue

                        option_list.append(arg_item)

                    try:
                        dst_network = self.__parse_tc_filter_network(tc_filter)
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

                    is_first_set = False

                    command_list.append(" ".join([Tc.Command.TCSET] + option_list))

        return command_list

    @staticmethod
    def __parse_tc_filter_network(text):
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


def set_tc_from_file(logger, config_file_path, is_overwrite):
    return_code = 0

    loader = TcConfigLoader(logger)
    loader.is_overwrite = is_overwrite

    try:
        loader.load_tcconfig(config_file_path)
    except IOError as e:
        logger.error(msgfy.to_error_message(e))
        return errno.EIO

    for tcconfig_command in loader.get_tcconfig_commands():
        return_code |= spr.SubprocessRunner(tcconfig_command).run()

    return return_code
