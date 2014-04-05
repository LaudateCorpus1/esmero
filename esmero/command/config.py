"""Config

This module is in charge of providing all the necessary settings to
the rest of the modules in esmero.

"""
from __future__ import print_function

import os
import sys
import argparse
import textwrap
import json
from esmero.command import error, import_mod


DESC = """View and edit a configuration file for esmero.

Some actions performed by esmero can be overwritten by using
configuration files.

To see the values that the configuration file can overwrite use the
`defaults` command. This will print a list of the keys and values
esmero uses for the given command.

"""

CONFIG = {
    'path': None,  # read only
    'name': None,  # read only
    'cfg_path': None,  # COMMAND LINE USE ONLY
    'cfg_user': None,  # COMMAND LINE USE ONLY
    'arg': None  # COMMAND LINE USE ONLY
}


def var_completer(**_):
    """var completer. """
    return ['SEC.KEY']


def value_completer(**_):
    """value completer. """
    return ['VALUE']


class ConfigDispAction(argparse.Action):  # pylint: disable=R0903
    """Derived argparse Action class to use when displaying the
    configuration file and location."""
    def __call__(self, parser, namespace, values, option_string=None):
        CONFIG['cfg_user'] = namespace.cfg_user
        CONFIG['cfg_path'] = namespace.cfg_path
        cfg_file = read_config()
        fname = '%s/%s' % (CONFIG['path'], CONFIG['name'])
        print('esmero configuration file: %s' % fname)
        json.dump(cfg_file, sys.stdout,
                  sort_keys=True, indent=4, separators=(',', ': '))
        sys.stdout.write('\n')
        exit(0)


def add_parser(subp, fclass):
    "Add a parser to the main subparser. "
    tmpp = subp.add_parser('config', help='configure esmero',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument('var', type=str,
                      help='Must be in the form of sec.key'
                      ).completer = var_completer
    tmpp.add_argument('value', type=str, nargs='?', default=None,
                      help='var value').completer = value_completer
    tmpp.add_argument('-v', action='store_true',
                      help='print config file location')
    tmpp.add_argument('--display', action=ConfigDispAction,
                      nargs=0,
                      help='print config file and exit')


def read_config(path='.'):
    """Read a configuration file."""
    name = 'esmero.config'
    if CONFIG['cfg_user']:
        path = os.environ['HOME']
        name = '.esmero.config'
    elif CONFIG['cfg_path'] is None:
        if not os.path.exists(name):
            if 'ESMERO_CONFIG_PATH' in os.environ:
                path = os.environ['ESMERO_CONFIG_PATH']
            else:
                path = os.environ['HOME']
                name = '.esmero.config'
    else:
        path = CONFIG['cfg_path']
        if not os.path.exists('%s/%s' % (path, name)):
            error("ERROR: %s/%s does not exist.\n" % (path, name))
    try:
        with open('%s/%s' % (path, name)) as fp_:
            cfg_file = json.load(fp_)
    except IOError:
        cfg_file = {}
    CONFIG['name'] = name
    CONFIG['path'] = path
    return cfg_file


def write_config(cfg_file):
    "Write the configuration file. "
    fname = '%s/%s' % (CONFIG['path'], CONFIG['name'])
    with open(fname, 'w') as tmp:
        json.dump(
            cfg_file, tmp,
            sort_keys=True, indent=4, separators=(',', ': ')
        )


def run():
    "Run command. "
    arg = CONFIG['arg']
    cfg_file = read_config()
    keys = arg.var.split('.')
    if arg.v:
        fname = '%s/%s' % (CONFIG['path'], CONFIG['name'])
        print('esmero configuration file: %s' % fname)
    parent = None
    crt = cfg_file
    for i in xrange(len(keys)-1):
        if keys[i] in crt:
            parent = crt
            crt = parent[keys[i]]
        else:
            try:
                crt[keys[i]] = dict()
            except TypeError:
                parent[keys[i-1]] = dict()
                crt = parent[keys[i-1]]
                crt[keys[i]] = dict()
            parent = crt
            crt = parent[keys[i]]
    if arg.value is None:
        try:
            json.dump(crt[keys[-1]], sys.stdout, sort_keys=True,
                      indent=4, separators=(',', ': '))
            sys.stdout.write('\n')
        except KeyError:
            pass
        return
    try:
        crt[keys[-1]] = arg.value
    except TypeError:
        parent[keys[-2]] = dict()
        crt = parent[keys[-2]]
        crt[keys[-1]] = arg.value
    write_config(cfg_file)


def update_single(cfg, name, defaults=None):
    "Helper function for get_cfg."
    if defaults:
        for var, val in defaults.iteritems():
            cfg[name][var] = os.path.expandvars(str(val))
    else:
        try:
            mod = import_mod('esmero.command.%s' % name)
            if hasattr(mod, "DEFAULTS"):
                for var, val in mod.DEFAULTS.iteritems():
                    cfg[name][var] = os.path.expandvars(val)
        except ImportError:
            pass


def _update_from_file(cfg, name, cfg_file):
    "Helper function for get_cfg."
    if name in cfg_file:
        for var, val in cfg_file[name].iteritems():
            cfg[name][var] = os.path.expandvars(val)


def _update_from_arg(cfg, argdict, key):
    "Helper function for get_cfg."
    for var in cfg[key]:
        if var in argdict and argdict[var] is not None:
            cfg[key][var] = argdict[var]


def get_cfg(names, defaults=None):
    "Obtain settings from the configuration file."
    cfg = {
        'esmero': {
            'path': ''
        }
    }
    cfg_file = read_config()
    if 'esmero' in cfg_file:
        for var, val in cfg_file['esmero'].iteritems():
            cfg['esmero'][var] = val
    cfg['esmero']['root'] = CONFIG['path']
    if isinstance(names, list):
        for name in names:
            cfg[name] = dict()
            update_single(cfg, name)
            _update_from_file(cfg, name, cfg_file)
    else:
        if names != 'esmero':
            cfg[names] = dict()
            update_single(cfg, names, defaults)
            _update_from_file(cfg, names, cfg_file)
    if CONFIG['arg']:
        argdict = vars(CONFIG['arg'])
        if argdict['parser_name'] in cfg:
            _update_from_arg(cfg, argdict, argdict['parser_name'])
        _update_from_arg(cfg, argdict, 'esmero')
        CONFIG['arg'] = None
    return cfg
