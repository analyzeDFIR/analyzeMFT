# -*- coding: UTF-8 -*-
# directives.py
# Noah Rubin
# 01/31/2018

import logging
Logger = logging.getLogger(__name__)
from os import path
from glob import glob
from argparse import Namespace

from src.utils.config import initialize_logger, synthesize_log_path
from src.utils.registry import RegistryMetaclassMixin 
import src.utils.parallel as parallel
import src.main.tasks as tasks

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
    MFT_RECORD_SIZE = 1024

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
                args.log_path: String   => path to log file directory
                args.log_prefix: String => log file prefix
                args.count: Integer     => number of records to process
                args.threads: Integer   => number of threads to use
        Procedure:
            Initialize the logging system and run this directive using the supplied arguments
        Preconditions:
            args is of type Namespace
            args.log_path is of type String
            args.log_prefix is of type String
            args.count is of type Integer
            args.threads is of type Integer > 0
            ** Any other preconditions must be checked by subclasses
        '''
        assert isinstance(args, Namespace), 'Args is not of type Namespace'
        assert hasattr(args, 'log_path'), 'Args does not contain log_path attribute'
        assert hasattr(args, 'log_prefix'), 'Args does not contain log_prefix attribute'
        assert hasattr(args, 'count'), 'Args does not contain count attribute'
        assert hasattr(args, 'threads'), 'Args does not contain threads attribute'
        assert args.threads > 0, 'Threads is not greater than 0'
        if args.threads > parallel.CPU_COUNT:
            args.threads = parallel.CPU_COUNT
        initialize_logger(args.log_path, args.log_prefix)
        Logger.info('BEGIN: %s'%cls.__name__)
        cls.run(args)
        Logger.info('END: %s'%cls.__name__)
        #logging.shutdown()
        #log_path = synthesize_log_path(args.log_path, args.log_prefix)
        #parallel.coalesce_files(path.join(args.lpath, '*_tmp_amft.log'), log_path)

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
        target_parent = path.dirname(args.target)
        frontier = cls.get_frontier(args.sources)
        record_count = 0
        for nodeidx, node in enumerate(frontier):
            Logger.info('Parsing $MFT file %s'%node)
            mft_file = open(node, 'rb')
            try:
                recordidx = 0
                mft_record = mft_file.read(cls.MFT_RECORD_SIZE)
                while mft_record != '' and (args.count is None or record_count < args.count):
                    tasks.ParseCSVTask(nodeidx, recordidx, args.info_type, mft_record, target=args.target, sep=args.sep)('')
                    mft_record = mft_file.read(cls.MFT_RECORD_SIZE)
                    recordidx += 1
                    record_count += 1
            finally:
                mft_file.close()
            if args.count is not None and record_count >= args.count:
                break

class ParseBODYDirective(BaseDirective):
    '''
    Directive for parsing $MFT file to BODY format
    '''
    @classmethod
    def run(cls, args):
        '''
        Args:
            @BaseDirective.run_directive
            args.sources: List<String>  => list of $MFT file(s) to parse
            args.target: String         => path to output file
            args.sep: String            => separator to use in output file
        Procedure:
            Parse $MFT information to BODY format
        Preconditions:
            @BaseDirective.run_directive
            args.sources is of type List<String>    (assumed True)
            args.target is of type String           (assumed True)
            args.target points to existing directory
            args.sep is of type String              (assumed True)
        '''
        assert path.isdir(path.dirname(args.target)), 'Target does not point to existing directory'
        args.target = path.abspath(args.target)
        frontier = cls.get_frontier(args.sources)
        record_count = 0
        for nodeidx, node in enumerate(frontier):
            Logger.info('Parsing $MFT file %s'%node)
            mft_file = open(node, 'rb')
            try:
                recordidx = 0
                mft_record = mft_file.read(cls.MFT_RECORD_SIZE)
                while mft_record != '' and (args.count is None or record_count < args.count):
                    tasks.ParseBODYTask(nodeidx, recordidx, mft_record, target=args.target, sep=args.sep)('')
                    mft_record = mft_file.read(cls.MFT_RECORD_SIZE)
                    recordidx += 1
                    record_count += 1
            finally:
                mft_file.close()
            if args.count is not None and record_count >= args.count:
                break

class ParseJSONDirective(BaseDirective):
    '''
    Directive for parsing $MFT file to JSON format
    '''
    @classmethod
    def run(cls, args):
        '''
        Args:
            @BaseDirective.run_directive
            args.sources: List<String>  => list of $MFT file(s) to parse
            args.target: String         => path to output file
            args.pretty                 => whether to pretty print JSON output
        Procedure:
            Parse $MFT information to JSON format
        Preconditions:
            @BaseDirective.run_directive
            args.sources is of type List<String>    (assumed True)
            args.target is of type String           (assumed True)
            args.target points to existing directory
            args.pretty is of type Boolean          (assumed True)
        '''
        assert path.isdir(path.dirname(args.target)), 'Target does not point to existing directory'
        args.target = path.abspath(args.target)
        frontier = cls.get_frontier(args.sources)
        record_count = 0
        for nodeidx, node in enumerate(frontier):
            Logger.info('Parsing $MFT file %s'%node)
            mft_file = open(node, 'rb')
            try:
                recordidx = 0
                mft_record = mft_file.read(cls.MFT_RECORD_SIZE)
                while mft_record != '' and (args.count is None or record_count < args.count):
                    tasks.ParseJSONTask(nodeidx, recordidx, mft_record, target=args.target, pretty=args.pretty)('')
                    mft_record = mft_file.read(cls.MFT_RECORD_SIZE)
                    recordidx += 1
                    record_count += 1
            finally:
                mft_file.close()
            if args.count is not None and record_count >= args.count:
                break
