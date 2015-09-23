"""Command

Collection of functions to create esmero's command line utility.

"""
import sys


def disp(msg, *args):
    """Write to stdout. """
    sys.stdout.write(msg % args)


def import_mod(name):
    """Return a module by string. """
    mod = __import__(name)
    for sub in name.split(".")[1:]:
        mod = getattr(mod, sub)
    return mod


class EsmeroError(Exception):
    """Every known error should be raised via this exception. """
    pass
