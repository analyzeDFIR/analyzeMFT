# -*- coding: UTF-8 -*-
# object_id.py
# Noah Rubin
# 02/24/2018

from construct import *
from .general import NTFSGUID

'''
MFTObjectID
'''
MFTObjectID = Struct(
    'ObjectID'              / NTFSGUID,
    'BirthVolumeID'         / NTFSGUID,
    'BirthObjectID'         / NTFSGUID,
    'DomainID'              / NTFSGUID
)
