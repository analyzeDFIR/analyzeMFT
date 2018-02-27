# -*- coding: UTF-8 -*-
# standard_information.py
# Noah Rubin
# 02/24/2018

from construct import *
from .general import NTFSFILETIME, MFTFileAttributeFlags

'''
MFTStandardInformationAttribute
'''
MFTStandardInformationAttribute = Struct(
    'RawCreateTime'         / NTFSFILETIME,
    'RawLastModifiedTime'   / NTFSFILETIME,
    'RawEntryModifiedTime'  / NTFSFILETIME,
    'RawLastAccessTime'     / NTFSFILETIME,
    'FileAttributeFlags'    / MFTFileAttributeFlags,
    'MaximumVersions'       / Int32ul,
    'VersionNumber'         / Int32ul,
    'ClassIdentifier'       / Int32ul,
    'OwnerIdentifier'       / Int32ul,
    'SecurityDescriptorID'  / Int32ul,
    'Quota'                 / Int64ul,
    'USN'                   / Int64ul
)

