# encoding: utf-8

from __future__ import absolute_import, unicode_literals

from ._const import TcCommandOutput
from ._docker import DockerClient
from ._logger import logger
from ._tc_script import write_tc_script


class Main(object):
    def __init__(self, options):
        self._options = options
        self._dclient = DockerClient(options.tc_command_output)

    def _fetch_tc_target_list(self):
        if not self._options.use_docker:
            return [self._options.device]

        container = self._options.device

        self._dclient.verify_container(container, exit_on_exception=True)
        self._dclient.create_veth_table(container)

        return self._dclient.fetch_veth_list(self._dclient.extract_container_info(container).name)

    def _dump_history(self, tc, tc_command):
        command_history = "\n".join(tc.get_command_history())
        command_output = self._options.tc_command_output

        if command_output == TcCommandOutput.STDOUT:
            print(command_history)
            return

        if command_output == TcCommandOutput.SCRIPT:
            write_tc_script(
                tc_command, command_history, filename_suffix=tc.netem_param.make_param_name()
            )
            return

        logger.debug("command history\n{}".format(command_history))
