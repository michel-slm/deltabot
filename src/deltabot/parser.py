# PYTHON_ARGCOMPLETE_OK

import os
import sys
import py
import argparse

from deltachat import Account

from .plugins import get_global_plugin_manager
from .bot import DeltaBot


main_description = """
The deltabot command line offers sub commands for initialization, configuration
and web-serving of Delta Chat Bots.  New sub commands may be added via plugins.
"""


def main(argv=None):
    """delta.chat bot management command line interface."""
    pm = get_global_plugin_manager()
    parser = get_base_parser(plugin_manager=pm)
    args = parser.main_parse_argv(argv or sys.argv)
    bot = make_bot_from_args(args, plugin_manager=pm)
    parser.main_run(bot=bot, args=args)


def make_bot_from_args(args, plugin_manager, account=None):
    basedir = os.path.abspath(os.path.expanduser(args.basedir))
    if not os.path.exists(basedir):
        os.makedirs(basedir)

    if account is None:
        db_path = os.path.join(basedir, "account.db")
        account = Account(db_path, "deltabot/{}".format(sys.platform))

    logger = plugin_manager.hook.deltabot_get_logger(args=args)
    return DeltaBot(account, logger, plugin_manager=plugin_manager)


class MyArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class ArgumentError(Exception):
        """ and error from the argparse subsystem. """
    def error(self, error):
        """raise errors instead of printing and raising SystemExit"""
        raise self.ArgumentError(error)

    def add_generic_option(self, *flags, **kwargs):
        """ add a generic argument option. """
        if not hasattr(self, "subparsers"):
            raise ValueError("can not add generic option to sub command")
        if not (flags and flags[0].startswith("-")):
            raise ValueError("can not generically add positional args")
        self.generic_options.add_argument(*flags, **kwargs)

    def add_subcommand(self, cls):
        """ Add a subcommand to deltabot. """
        if not hasattr(self, "subparsers"):
            raise ValueError("can not add sub command to subcommand")
        doc, description = parse_docstring(cls.__doc__)
        name = getattr(cls, "name", None)
        if name is None:
            name = cls.__name__.lower()
        subparser = self.subparsers.add_parser(
            name=name,
            description=description,
            help=doc
        )
        subparser.Action = argparse.Action

        inst = cls()
        meth = getattr(inst, "add_arguments", None)
        if meth is not None:
            meth(parser=subparser)
        subparser.set_defaults(subcommand_instance=inst)

    def main_parse_argv(self, argv):
        try_argcomplete(self)
        try:
            return self.parse_args(argv[1:])
        except self.ArgumentError as e:
            if not argv[1:]:
                return self.parse_args(["-h"])
            self.print_usage()
            self.exit(2, "%s: error: %s\n" % (self.prog, e.args[0]))

    def main_run(self, bot, args):
        out = CmdlineOutput()

        if args.command is None:
            out.line(self.format_usage())
            out.line(self.description.strip())
            out.line()
            for name, p in self.subparsers.choices.items():
                out.line("{:20s} {}".format(name, p.description.split("\n")[0].strip()))
            out.line()
            out.ok_finish("please specify a subcommand", red=True)

        try:
            res = args.subcommand_instance.run(bot=bot, args=args, out=out)
        except ValueError as ex:
            res = str(ex)
        if res:
            out.fail(str(res))


class CmdlineOutput:
    def __init__(self):
        self.tw = py.io.TerminalWriter()

    def line(self, message="", **kwargs):
        self.tw.line(message, **kwargs)

    def fail(self, message):
        self.tw.line("FAIL: {}".format(message), red=True)
        raise SystemExit(1)

    def ok_finish(self, message, **kwargs):
        self.line(message, **kwargs)
        raise SystemExit(0)


def try_argcomplete(parser):
    if os.environ.get('_ARGCOMPLETE'):
        try:
            import argcomplete
        except ImportError:
            pass
        else:
            argcomplete.autocomplete(parser)


def get_base_parser(plugin_manager):
    parser = MyArgumentParser(prog="deltabot", description=main_description)
    parser.plugin_manager = plugin_manager
    parser.subparsers = parser.add_subparsers(dest="command")
    parser.generic_options = parser.add_argument_group("generic options")
    plugin_manager.hook.deltabot_init_parser(parser=parser)
    return parser


def parse_docstring(txt):
    description = txt
    i = txt.find(".")
    if i == -1:
        doc = txt
    else:
        doc = txt[:i + 1]
    return doc, description
