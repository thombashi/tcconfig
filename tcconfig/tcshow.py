#!/usr/bin/env python3

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

import sys

import msgfy
import subprocrunner as spr
from docker.errors import DockerException
from simplesqlite import SimpleSQLite
from simplesqlite.model import Integer, Model, Text

from .__version__ import __version__
from ._argparse_wrapper import ArgparseWrapper
from ._common import check_command_installation, initialize_cli
from ._const import Tc, TcCommandOutput
from ._docker import DockerClient
from ._error import TargetNotFoundError
from ._logger import logger
from ._network import verify_network_interface
from ._tc_script import write_tc_script
from .parser.shaping_rule import TcShapingRuleParser


try:
    import ujson as json
except ImportError:
    import json  # type: ignore


class ShapingRuleModel(Model):
    device = Text(not_null=True)
    direction = Text(not_null=True)
    filter_id = Text(not_null=True)
    dst_network = Text()
    dst_port = Integer()
    src_network = Text()
    src_port = Integer()
    protocol = Text(not_null=True)

    delay = Text()
    delay_distro = Text()
    loss = Text()
    duplicate = Text()
    corrupt = Text()
    reorder = Text()
    rate = Text()


def parse_option():
    parser = ArgparseWrapper(__version__)

    group = parser.parser.add_argument_group("Traffic Control")
    if {"-d", "--device"}.intersection(set(sys.argv)):
        # deprecated: remain for backward compatibility
        group.add_argument(
            "-d", "--device", action="append", required=True, help="network device name (e.g. eth0)"
        )
    else:
        group.add_argument("device", nargs="+", help="network device name (e.g. eth0)")
    group.add_argument(
        "--ipv6",
        dest="ip_version",
        action="store_const",
        const=6,
        default=4,
        help="Display IPv6 shaping rules. Defaults to show IPv4 shaping rules.",
    )

    parser.add_docker_group(is_add_srcdst=False)

    parser.parser.add_argument(
        "--color",
        action="store_true",
        default=False,
        help="colorize the output. require Pygments package.",
    )
    parser.parser.add_argument("--export", dest="export_path", help="[experimental]")
    parser.parser.add_argument(
        "--exclude-filter-id",
        action="store_true",
        default=False,
        help="[experimental] not display filter_id.",
    )
    parser.parser.add_argument(
        "--dump-db",
        dest="dump_db_path",
        help="[experimental] dump parsed results to a SQLite database file",
    )

    return parser.parser.parse_args()


def print_tc(text, is_colorize):
    try:
        from pygments import highlight
        from pygments.formatters import TerminalTrueColorFormatter
        from pygments.lexers import JsonLexer

        pygments_installed = True
    except ImportError:
        pygments_installed = False

    if is_colorize and pygments_installed:
        print(
            highlight(
                code=text, lexer=JsonLexer(), formatter=TerminalTrueColorFormatter(style="monokai")
            )
        )
    else:
        print(text)


def export_settings(export_path, out_rules, in_rules):
    with SimpleSQLite(export_path, mode="a") as con:
        ShapingRuleModel.attach(con)
        ShapingRuleModel.create()

        for out_rule in out_rules:
            ShapingRuleModel.insert(ShapingRuleModel(**out_rule))

        for in_rule in in_rules:
            ShapingRuleModel.insert(ShapingRuleModel(**in_rule))


def extract_tc_params(options):
    dclient = None
    if options.use_docker:
        try:
            dclient = DockerClient(options.tc_command_output)
        except DockerException as e:
            logger.error(msgfy.to_error_message(e))
            sys.exit(1)

    tc_params = {}

    for device in options.device:
        try:
            if options.use_docker:
                container = device
                container_info = dclient.extract_container_info(container)

                if not container_info.state.running:
                    logger.error(
                        "{id} ({name}) not running (current status: {status})".format(
                            id=container,
                            name=container_info.name,
                            status=container_info.state.status,
                        )
                    )
                    continue

                dclient.create_veth_table(container)

                for veth in dclient.fetch_veth_list(container_info.name):
                    rule_parser = TcShapingRuleParser(
                        device=veth,
                        ip_version=options.ip_version,
                        tc_command_output=options.tc_command_output,
                        logger=logger,
                        export_path=options.export_path,
                        is_parse_filter_id=not options.exclude_filter_id,
                        dump_db_path=options.dump_db_path,
                    )
                    rule_parser.parse()

                    if options.export_path:
                        rule_parser.con.dump(options.export_path)
                        out_rules, in_rules = rule_parser.extract_export_parameters()
                        export_settings(options.export_path, out_rules, in_rules)

                    tc_params.update(rule_parser.get_tc_parameter())
                    key = "{id} (device={veth})".format(id=container_info.id[:12], veth=veth)
                    tc_params[key] = tc_params.pop(veth)
            else:
                verify_network_interface(device, options.tc_command_output)
                rule_parser = TcShapingRuleParser(
                    device=device,
                    ip_version=options.ip_version,
                    tc_command_output=options.tc_command_output,
                    logger=logger,
                    export_path=options.export_path,
                    is_parse_filter_id=not options.exclude_filter_id,
                    dump_db_path=options.dump_db_path,
                )
                rule_parser.parse()

                if options.export_path:
                    rule_parser.con.dump(options.export_path)
                    out_rules, in_rules = rule_parser.extract_export_parameters()
                    export_settings(options.export_path, out_rules, in_rules)

                tc_params.update(rule_parser.get_tc_parameter())
        except TargetNotFoundError as e:
            logger.warning(e)
            continue

    return tc_params


def main():
    options = parse_option()

    initialize_cli(options)
    check_command_installation("tc")

    if options.tc_command_output != TcCommandOutput.NOT_SET:
        spr.SubprocessRunner.default_is_dry_run = True

    tc_params = extract_tc_params(options)
    command_history = "\n".join(spr.SubprocessRunner.get_history())

    if options.tc_command_output == TcCommandOutput.STDOUT:
        print(command_history)
        return 0

    if options.tc_command_output == TcCommandOutput.SCRIPT:
        write_tc_script(
            Tc.Command.TCSHOW, command_history, filename_suffix="-".join(options.device)
        )
        return 0

    logger.debug("command history\n{}".format(command_history))

    print_tc(json.dumps(tc_params, ensure_ascii=False, indent=4), options.color)

    return 0


if __name__ == "__main__":
    sys.exit(main())
