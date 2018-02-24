# -*- coding: UTF-8 -*-
# file_name.py
# Noah Rubin
# 02/24/2018

from construct import *
from .general import NTFSFileReference, NTFSFILETIME, MFTFileAttributeFlags

'''
MFTFileNameAttribute
'''
MFTFileNameAttribute = Struct(
    'ParentDirectory'       / NTFSFileReference,
    'CreateTime'            / NTFSFILETIME,
    'LastModifiedTime'      / NTFSFILETIME,
    'EntryModifiedTime'     / NTFSFILETIME,
    'LastAccessTime'        / NTFSFILETIME,
    'AllocatedFileSize'     / Int64ul,
    'FileSize'              / Int64ul,
    'FileAttributeFlags'    / MFTFileAttributeFlags,
    'ExtendedData'          / Int32ul,
    'FileNameLength'        / Int8ul,
    'FileNameNamespace'     / Int8ul,
    'FileName'              / PascalString(this.FileNameLength, encoding='utf16')
)
