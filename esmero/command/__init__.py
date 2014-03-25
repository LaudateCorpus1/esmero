"""Command

Collection of functions to create esmero's command line utility.

"""

import sys


def error(msg):
    "Print a message to the standard error stream and exit. "
    sys.stderr.write(msg)
    sys.exit(2)


def warn(msg):
    "Print a message to the standard error "
    sys.stderr.write(msg)
