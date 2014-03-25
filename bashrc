# Esmero local installation
#
# This bash file is meant to be used for local installation.
#

# The path to this local installation
export ESMERO_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Access to esmero
export PATH=$ESMERO_ROOT/bin:$PATH

# Python and C/C++
export PYTHONPATH=$ESMERO_ROOT:$PYTHONPATH

# ESMERO_CONFIG:
# If you have a configuration file for esmero that you wish to
# use then define this variable
#export ESMERO_CONFIG_PATH=/path/to/esmero.config
