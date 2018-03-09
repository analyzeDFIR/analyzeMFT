# -*- coding: UTF-8 -*-
# app.py
# Noah Rubin
# 01/31/2018

from multiprocessing import freeze_support

from src.utils.config import initialize_paths
initialize_paths()
from src.main.cli import initialize_parser

def amft_main():
    freeze_support()
    parser = initialize_parser()
    args = parser.parse_args()
    args.func(args)
    return 0
