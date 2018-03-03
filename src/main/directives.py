# -*- coding: UTF-8 -*-
# directives.py
# Noah Rubin
# 01/31/2018

import logging
Logger = logging.getLogger(__name__)
from os import path
from glob import glob
from argparse import Namespace

from src.utils.config import initialize_logger
from src.utils.registry import RegistryMetaclassMixin 

class DirectiveRegistry(RegistryMetaclassMixin, type):
    '''
    Directive registry metaclass to store registered directives
    available to command line interface in `src.main.cli`.
    '''
    _REGISTRY = dict()

    @classmethod
    def _add_class(cls, name, new_cls):
        '''
        @RegistryMetaclassMixin._add_class
        '''
        if cls.retrieve(name) is not None or name == 'BaseDirective':
            return False
        if not hasattr(new_cls, 'run_directive') or not callable(new_cls.run_directive):
            return False
        cls._REGISTRY.update({name: new_cls})
        return True

class BaseDirective(object, metaclass=DirectiveRegistry):
    '''
    Base class for creating new directives. This
    class is not included in the registry of directives
    exposed to the command line interface and should not
    be referenced outside of this module unless type checking
    a directive class.
    '''
    @staticmethod
    def get_frontier(sources, gen=True):
        '''
        '''
        frontier = list()
        for src in sources:
            src = path.abspath(src)
            if path.isfile(src):
                frontier.append(src)
            elif path.isdir(src):
                for subsrc in glob(path.join(src, '*')):
                    frontier.append(subsrc)
        if gen:
            for node in frontier:
                yield node
        else:
            return frontier
    @classmethod
    def run(cls, args):
        '''
        Args:
            @BaseDirective.run_directive
        Procedure:
            Entry point for directive
        Preconditions:
            @BaseDirective.run_directive
        '''
        raise NotImplementedError('method run not implemented for %s'%cls.__name__)
    @classmethod
    def run_directive(cls, args):
        '''
        Args:
            args: Namespace => parsed command line arguments
                args.log_path: String   => path to directory file directory
                args.log_prefix: String => log file prefix
        Procedure:
            Initialize the logging system and run this directive using the supplied arguments
        Preconditions:
            args is of type Namespace
            args.log_path is of type String
            args.log_prefix is of type String
            ** Any other preconditions must be checked by subclasses
        '''
        assert isinstance(args, Namespace), 'Args is not of type Namespace'
        assert hasattr(args, 'log_path'), 'Args does not contain log_path attribute'
        assert hasattr(args, 'log_prefix'), 'Args does not contain log_prefix attribute'
        initialize_logger(args.log_path, args.log_prefix)
        Logger.info('BEGIN: %s'%cls.__name__)
        cls.run(args)
        Logger.info('END: %s'%cls.__name__)
    def __init__(self, args):
        self.run_directive(args)

class ParseCSVDirective(BaseDirective):
    '''
    Directive for parsing $MFT file to CSV format
    '''
    @classmethod
    def run(cls, args):
        '''
        Args:
            @BaseDirective.run_directive
            args.info_type: String      => type of information to extract
            args.sources: List<String>  => list of $MFT file(s) to parse
            args.target: String         => path to output file
            args.sep: String            => separator to use in output file
        Procedure:
            Parse $MFT information to CSV format
        Preconditions:
            @BaseDirective.run_directive
            args.info_type is of type String        (assumed True)
            args.sources is of type List<String>    (assumed True)
            args.target is of type String           (assumed True)
            args.target points to existing directory
            args.sep is of type String              (assumed True)
        '''
        assert path.isdir(path.dirname(args.target)), 'Target does not point to existing directory'
        args.target = path.abspath(args.target)
        frontier = cls.get_frontier(args.sources)
        parse_pool = None
        results_pool = None
        for idx, node in enumerate(frontier):
            Logger.info('Parsing $MFT file %s'%node)
