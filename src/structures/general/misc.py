# -*- coding: UTF-8 -*-
# general.py
# Noah Rubin
# 02/24/2018

from construct import *

'''
NTFSFILETIME
'''
NTFSFILETIME = Struct(
    'dwLowDateTime'         / Int32ul,
    'dwHighDateTime'        / Int32ul
)

'''
NTFS File Reference: pointer to base (parent) MFT record (0 if this is base record)
    SegmentNumber:  MFT entry index value
    SequenceNumber: MFT entry sequence number
'''
NTFSFileReference = Struct(
    'SegmentNumber'         / Int32ul,
    Padding(2),
    'SequenceNumber'        / Int16ul
)
