
import os
import sys

# The path of the current Python script.
_CURRENT_PATH       = os.path.dirname(os.path.realpath(__file__))
_TOP_PATH           = os.path.join(_CURRENT_PATH, '..')
sys.path.insert( 0, _TOP_PATH )
for i, p in enumerate(sys.path):
    print(f'{i}: {p}')

from config_helper import (
    construct_config_on_filesystem,
    read_config )

if __name__ == '__main__':
    config_name = construct_config_on_filesystem(sys.argv)
    config = read_config(config_name)
    print(config)
    