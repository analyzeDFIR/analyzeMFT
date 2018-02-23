# -*- coding: UTF-8 -*-
# mft.py
# Noah Rubin
# 02/21/2017

import src.structures.mft as mftstructs
from src.utils.time import WindowsTime
from src.utils.item import BaseItem

class MFTAttributes(BaseItem):
    '''
    Represents resident attributes of MFT entry
    '''
    pass

class MFTEntry(BaseItem):
    '''
    Class for parsing Windows $MFT file entries
    '''
    pass
