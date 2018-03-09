# -*- coding: UTF-8 -*-
# mft.py
# Noah Rubin
# 02/01/2018

from .general import *
from .headers import *
from .standard_information import *
from .attribute_list import *
from .file_name import *
from .object_id import *
from .security_descriptor import *
from .volume_name import *
from .volume_information import *
from .index import *

'''
MFTDataRunEntry
TODO: Incomplete
'''
MFTDataRunEntry = Struct(
    'DataRunSize'           / Bitwise(BitsInteger(4, signed=True, swapped=True)),
    'DataRunOffset'         / Bitwise(BitsInteger(4, swapped=True))
)
