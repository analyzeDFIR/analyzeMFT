# -*- coding: UTF-8 -*-
# tasks.py
# Noah Rubin
# 02/05/2018

import logging
Logger = logging.getLogger(__name__)
from os import path

from src.parsers.mft import MFTEntry

class CSVParseTask(object):
    '''
    '''
    def __init__(self, nodeidx, recordidx, info_type, mft_record, target=None, sep=None):
        self.nodeidx = nodeidx
        self.recordidx = recordidx
        self.info_type = info_type
        self.mft_record = mft_record
        self.target = target
        self.sep = sep
    def __call__(self, worker_name):
        mft_entry = MFTEntry(self.mft_record)
        target_file = path.join(self.target, '%s_amft_csv.tmp'%worker_name)
        result_set = list()
        if info_type == 'summary':
            # FIELDS: SequenceNumber, MFTRecordNumber, Signature, 
            #         LogFileSequenceNumber, Active, HasIndex, UsedSize, TotalSize,
            #         ReferenceCount, StandardInformationCount, FileNameCount
            pass
        try:
            with open(target_file, 'a') as f:
                for result in result_set:
                    f.write(self.sep.join(result) + '\n')
        except Exception as e:
            Logger.error('Failed to write results to output file %s (%s)'%(target_file, str(e)))


