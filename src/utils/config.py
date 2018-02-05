# -*- coding: UTF-8 -*-
# config.py
# Noah Rubin
# 02/01/2018

import sys
import os

from src.main.exceptions import PathInitializationError

def initialize_paths():
    '''
    Args:
        N/A
    Procedure:
        Initialize sys.path to include the lib directory of dependencies.  Raises
        exception if unable to successfully append to sys.path, for example if sys.arv[0]
        is not a valid path.
    Preconditions:
        N/A
    '''
    try:
        runpath = os.path.abspath(sys.argv[0])
        assert os.path.exists(runpath), 'Run path %s does not exist'%runpath
    except Exception as e:
        raise PathInitializationException(e)
    else:
        try:
            sys.path.append(os.path.join(runpath))          # add runpath so 'from src.<module> import <object>' doesn't fail
            sys.path.append(os.path.join(runpath, 'lib'))   # add lib so 'import {sqlalchemy, construct}' doesn't fail
        except Exception as e:
            raise PathInitializationException(e)
