# -*- coding: UTF-8 -*-
# guid.py
# Noah Rubin
# 02/24/2018

from construct import *

'''
NTFS GUID: globally unique identifier
    Group1: first group of (8) hexadecimal digits of the GUID
    Group2: second group of (4) hexadecimal digits of the GUID
    Group3: third group of (4) hexadecimal digits of the GUID
    Group4: fourth group of (4) hexadecimal digits of the GUID
    Group5: fifth group of (12) hexadecimal digits of the GUID
    NOTE:
        A valid, full GUID is of the form:
           (1)    (2)  (3)  (4)     (5)
        6B29FC40-CA47-1067-B31D-00DD010662DA
'''
NTFSGUID = Struct(
    'Group1'                / Int32ul,
    'Group2'                / Int16ul,
    'Group3'                / Int16ul,
    'Group4'                / Int16ul,
    'Group5'                / BytesInteger(6, swapped=True)
)
