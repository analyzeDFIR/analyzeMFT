# -*- coding: UTF-8 -*-
# attribute_list.py
# Noah Rubin
# 02/24/2018

from construct import *
from .general import NTFSFileReference, MFTAttributeTypeCode

'''
MFTAttributeListEntry
'''
MFTAttributeListEntry = Struct(
    'AttributeTypeCode'     / MFTAttributeTypeCode,
    'RecordLength'          / Int16ul,
    'AttributeNameLength'   / Int8ul,
    'AttributeNameOffset'   / Int8ul,
    'LowestVcn'             / Int64ul,
    'SegmentReference'      / NTFSFileReference,
    'AttributeIdentifier'   / Int16ul,
)
