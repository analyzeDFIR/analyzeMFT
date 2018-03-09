## Copyright (c) 2018 Noah Rubin
## 
## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:
## 
## The above copyright notice and this permission notice shall be included in all
## copies or substantial portions of the Software.
## 
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
## SOFTWARE.

# -*- coding: UTF-8 -*-
# headers.py
# Noah Rubin
# 02/24/2018

from construct import *
from .general import NTFSFileReference, MFTAttributeTypeCode

'''
MFT Resident Attribute Data: length and offset of resident data in MFT attribute
    ValueLength:    size of attribute data in bytes
    ValueOffset:    offset of attribute data in bytes from start of MFT attribute
    IndexFlag:      Unknown (TODO: figure out what this is)
'''
MFTResidentAttributeData = Struct(
    'ValueLength'           / Int32ul,
    'ValueOffset'           / Int16ul,
    'IndexFlag'             / Int8ul,
    Padding(2)
)

'''
MFT Non-Resident Attribute Data: length and offset information of non-resident MFT attribute data
    LowestVCN:              lowest virtual cluster number (VCN) covered by attribute
    HighestVCN:             highest virtual cluster number (VCN) covered by attribute
    MappingPairsOffset:     offset to the mapping pairs array from start of attribute record in bytes,
                            where the mapping pairs array is a mapping from virtual to logical
                            cluster numbers
    CompressionUnitSize:    compression unit size as 2^n number of cluster blocks
    AllocatedLength:        allocated size of file in bytes, where size is event multiple of cluster
                            size (invalid if LowestVCN is non-zero)
    FileSize                file size in bytes, where size is highest readable byte plus 1 (invalid if
                            LowestVCN is non-zero)
    ValidDataLength:        length of valid data in file in bytes, where length is highest initialized
                            byte plus 1 (invalid if LowestVCN is non-zero)
    TotalAllocated:         sum of allocated clusters for the file

'''
MFTNonResidentAttributeData = Struct(
    'LowestVCN'             / Int32ul,
    Padding(4),
    'HighestVCN'            / Int32ul,
    Padding(4),
    'MappingPairsOffset'    / Int16ul,
    'CompressionUnitSize'   / Int16ul,
    Padding(4),
    'AllocatedLength'       / Int64ul,
    'FileSize'              / Int64ul,
    'ValidDataLength'       / Int64ul,
    'TotalAllocated'        / Optional(Int64ul)
)

'''
MFT Multi Sector Header: update sequence array metadata container
    Signature:                  header signature (in MFT entry header, will be 'FILE', 'BAAD', or
                                other value signalling a corrupt entry)
    UpdateSequenceArrayOffset:  offset to update sequence array from start of this structure in bytes
    UpdateSequenceArraySize:    size of update sequence array in bytes

NOTE:
    the update sequence array is a sequence of n unsigned short (Int16ul) values that provide detection
    of incomplete multisector transfers for devices that have a physical sector size greater than or equal
    to the sequence number stride (512) or that do not transfer sectors out of order.
'''
MFTEntryMultiSectorHeader = Struct(
    'RawSignature'              / Int32ul,
    'UpdateSequenceArrayOffset' / Int16ul,
    'UpdateSequenceArraySize'   / Int16ul
)

'''
MFT Entry Header: header structure for MFT entry
    MultiSectorHeader:          see MFTEntryMultiSectorHeader
    LogFileSequenceNumber:      $LogFile sequence number
    SequenceNumber:             MFT entry sequence number, incremented each time an MFT entry
                                is freed (must match SequenceNumber of BaseFileRecordSegment,
                                otherwise record segment is likely obsolete)
    ReferenceCount:             number of child MFT entries (TODO: clarify correctness)
    FirstAttributeOffset:       offset of first attribute of MFT entry from start of entry in bytes
    Flags:                      file flags
                                _Active (0x0001): FILE_RECORD_SEGMENT_IN_USE
                                _HasIndex (0x0002): FILE_FILE_NAME_INDEX_PRESENT (record is directory)
    UsedSize:                   number of bytes of the MFT entry in use
    TotalSize:                  total number of bytes of MFT entry (should be 1024)
    BaseFileRecordSegment:      see NTFSFileReference
    MFTRecordNumber:            Unknown (TODO: figure out what this is)
'''
MFTEntryHeader = Struct(
    'MultiSectorHeader'     / MFTEntryMultiSectorHeader,
    'LogFileSequenceNumber' / Int64ul,
    'SequenceNumber'        / Int16ul,
    'ReferenceCount'        / Int16ul,
    'FirstAttributeOffset'  / Int16ul,
    'Flags'                 / FlagsEnum(Int16ul,
        ACTIVE      = 0x0001,
        HAS_INDEX   = 0x0002),
    'UsedSize'              / Int32ul,
    'TotalSize'             / Int32ul,
    'BaseFileRecordSegment' / NTFSFileReference,
    'FirstAttributeId'      / Int16ul,
    Padding(2),
    'MFTRecordNumber'       / Int32ul
)

'''
MFT Attribute Header: header for MFT entry attribute
'''
MFTAttributeHeader = Struct(
    'TypeCode'              / MFTAttributeTypeCode,
    'RecordLength'          / Int32ul,
    'FormCode'              / Int8ul,
    'NameLength'            / Int8ul,
    'NameOffset'            / Int16ul,
    'Flags'                 / Int16ul,
    'Instance'              / Int16ul,
    'Form'                  / IfThenElse(
        this.FormCode == 0,
        'Resident'          / MFTResidentAttributeData,
        'NonResident'       / MFTNonResidentAttributeData
    )
)
