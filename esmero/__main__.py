""" Command line use of esmero

To run esmero from the command line do the following:

    python -m esmero ...

Use the option --help for more information.

"""
import sys
import argparse
import textwrap
import os.path as pt
from glob import iglob
from esmero.__version__ import VERSION
from esmero.command import config, import_mod, EsmeroError
from esmero.util.logging import L


class ConfigPathAction(argparse.Action):
    """Derived argparse Action class store the configuration path."""
    def __call__(self, parser, namespace, values, option_string=None):
        namespace.cfg_path = values
        config.CONFIG['cfg_path'] = values


# pylint: disable=W0212
def get_argparse_options(argp):
    "Helper function to pre-parse the arguments. "
    opt = dict()
    for action in argp._optionals._actions:
        for key in action.option_strings:
            if action.type is None:
                opt[key] = 1
            else:
                opt[key] = 2
    return opt


def preparse_args(argv, argp, subp):
    """Pre-parse the arguments to be able to have a default subparser
    based on the filename provided. """
    opt = get_argparse_options(argp)
    parsers = subp.choices.keys()
    index = 1
    arg = None
    default = 'build'
    try:
        while argv[index] in opt:
            index += opt[argv[index]]
        if index == 1 and argv[index][0] == '-':
            argv.insert(index, default)
            argv.insert(index, '.')
            return
        arg = argv[index]
        if arg == 'defaults':
            argv.insert(index, '.')
        if argv[index+1] in parsers:
            return
        if arg not in parsers:
            argv.insert(index+1, default)
    except IndexError:
        if arg not in parsers:
            argv.append(default)
            if arg is None:
                arg = default
    if arg in parsers:
        argv.insert(index, '.')


def parse_options(mod):
    "Interpret the command line inputs and options. "
    desc = """
esmero can perform various commands. Use the help option with a
command for more information.

"""
    ver = "esmero %s" % VERSION
    epi = """
shortcut:

    esmero . <==> esmero build .

More info:
  http://jmlopez-rod.github.com/esmero

Version:
  This is esmero version %s

""" % VERSION
    raw = argparse.RawDescriptionHelpFormatter
    argp = argparse.ArgumentParser(formatter_class=raw, version=ver,
                                   description=textwrap.dedent(desc),
                                   epilog=textwrap.dedent(epi))
    argp.add_argument('inputpath', type=str, default='.', nargs='?',
                      help='input path to build')
    argp.add_argument('--debug', action='store_true', dest='debug',
                      help='log events')
    argp.add_argument('--debug-path', type=str, dest='debug_path',
                      metavar='PATH', default=None,
                      help='directory to write lexor debug logs')
    argp.add_argument('--cfg', type=str, dest='cfg_path',
                      metavar='CFG_PATH', default='.',
                      action=ConfigPathAction,
                      help='configuration file directory')
    subp = argp.add_subparsers(title='subcommands',
                               dest='parser_name',
                               help='additional help',
                               metavar="<command>")
    names = mod.keys()
    names.sort()
    for name in names:
        mod[name].add_parser(subp, raw)
    preparse_args(sys.argv, argp, subp)
    return argp.parse_args()


def run():
    """Run esmero from the command line. """
    mod = dict()
    rootpath = pt.split(pt.abspath(__file__))[0]

    mod_names = [name for name in iglob('%s/command/*.py' % rootpath)]
    for name in mod_names:
        tmp_name = pt.split(name)[1][:-3]
        tmp_mod = import_mod('esmero.command.%s' % tmp_name)
        if hasattr(tmp_mod, 'add_parser'):
            mod[tmp_name] = tmp_mod

    arg = parse_options(mod)

    if arg.debug:
        L.enable()

    config.CONFIG['cfg_path'] = arg.cfg_path
    config.CONFIG['arg'] = arg
    try:
        if L.on:
            msg = 'running esmero v%s `%s` command from `%s`'
            L.info(msg, VERSION, arg.parser_name, rootpath)
        mod[arg.parser_name].run()
    except EsmeroError as err:
        L.error(err.message, exception=err)
    except Exception as err:
        L.error('Unhandled error: ' + err.message, exception=err)

    if arg.debug:
        fp = sys.stderr
        if arg.debug_path:
            try:
                fp = open(pt.join(arg.debug_path, 'esmero.debug'), 'w')
            except IOError as err:
                L.error('invalid debug log directory', exception=err)
        fp.write('[ESMERO DEBUG LOG]\n')
        fp.write('%r\n' % L)
        if arg.debug_path:
            fp.close()


if __name__ == '__main__':
    run()
