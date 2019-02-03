# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import sys

import msgfy
from docker.errors import DockerException

from ._const import TcCommandOutput
from ._docker import DockerClient
from ._logger import logger
from ._tc_script import write_tc_script


class Main(object):
    def __init__(self, options):
        self._options = options

        self._dclient = None
        if self._options.use_docker:
            try:
                self._dclient = DockerClient(options.tc_command_output)
            except DockerException as e:
                logger.error(msgfy.to_error_message(e))
                sys.exit(1)

    def _extract_dst_network(self):
        if self._options.dst_container:
            return self._dclient.extract_container_info(self._options.dst_container).ipaddr

        return self._options.dst_network

    def _extract_src_network(self):
        if self._options.src_container:
            return self._dclient.extract_container_info(self._options.src_container).ipaddr

        return self._options.src_network

    def _fetch_tc_targets(self):
        if not self._options.use_docker:
            return [self._options.device]

        container = self._options.device

        self._dclient.verify_container(container, exit_on_exception=True)
        self._dclient.create_veth_table(container)

        return self._dclient.fetch_veth_list(self._dclient.extract_container_info(container).name)

    def _get_return_code(self, return_code_list):
        error_return_code = None

        for return_code in return_code_list:
            if return_code == 0:
                return return_code

            error_return_code = return_code

        return error_return_code

    def _dump_history(self, tc, tc_command):
        command_history = "\n".join(tc.get_command_history())
        command_output = self._options.tc_command_output

        if command_output == TcCommandOutput.STDOUT:
            print(command_history)
            return

        try:
            filename_suffix = tc.netem_param.make_param_name()
        except AttributeError:
            filename_suffix = None

        if command_output == TcCommandOutput.SCRIPT:
            write_tc_script(tc_command, command_history, filename_suffix=filename_suffix)
            return

        logger.debug("command history\n{}".format(command_history))
