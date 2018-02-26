# -*- coding: UTF-8 -*-
# mft.py
# Noah Rubin
# 02/21/2017

from io import BytesIO
import logging
Logger = logging.getLogger(__name__)

import src.structures.mft as mftstructs
from src.utils.time import WindowsTime
from src.utils.item import BaseItem, Field

class MFTAttributes(BaseItem):
    '''
    Represents resident attributes of an MFT entry
    '''
    STANDARD_INFORMATION    = Field(1)
    ATTRIBUTE_LIST          = Field(2)
    FILE_NAME               = Field(3)
    OBJECT_ID               = Field(4)
    SECURITY_DESCRIPTOR     = Field(5)
    VOLUME_NAME             = Field(6)
    VOLUME_INFORMATION      = Field(7)

class MFTEntry(BaseItem):
    '''
    Class for parsing Windows $MFT file entries
    '''
    header      = Field(1)
    attributes  = Field(2)

    def __init__(self, raw_entry, load=True):
        super(MFTEntry, self).__init__()
        self._stream = None
        self.raw_entry = raw_entry
        if load:
            self.parse()
    def get_stream(self, persist=False):
        '''
        '''
        stream = BytesIO(self.raw_entry)
        if persist:
            self._stream = stream
        return stream
    def tell(self, stream=None):
        '''
        '''
        if stream is not None:
            try:
                return stream.tell()
            except:
                return None
        if self._stream is not None:
            try:
                return self._stream.tell()
            except:
                return None
    def parse_header(self, stream=None):
        '''
        '''
        if stream is None:
            stream = self._stream
        header = mftstructs.MFTEntryHeader.parse_stream(stream)
        if header.MultiSectorHeader.RawSignature == 0x454c4946:
            header.MultiSectorHeader.Signature = 'FILE'
        elif header.MultiSectorHeader.RawSignature == 0x44414142:
            header.MultiSectorHeader.Signature = 'BAAD'
        else:
            header.MultiSectorHeader.Signature = 'CRPT'
        def transform(value): return value if isinstance(value, (int, float, str, bool)) else dict(value)
        return {key:transform(value) for key,value in header.items() if not key.startswith('Raw')}
    def parse(self):
        '''
        args:
            N/A
        Procedure:
            Attempt to parse the supplied MFT entry, extracting
            header information and resident attribute data
        Preconditions:
            self.raw_entry is byte string of length 1024
        '''
        try:
            self.get_stream(True)
            self.header = self.parse_header()
            while self.tell() < len(self.raw_entry):
                self.parse_next_attribute()
        except Exception as e:
            Logger.error('Uncaught exception while parsing MFT entry (%s)'%(str(e)))
        finally:
            if self._stream is not None:
                self._stream.close()
