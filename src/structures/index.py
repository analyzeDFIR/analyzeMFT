# -*- coding: UTF-8 -*-
# index.py
# Noah Rubin
# 02/27/2018

from construct import *
from .general import NTFSFileReference

'''
MFTIndexValueFlags
'''
MFTIndexValueFlags = FlagsEnum(Int32ul,
    HAS_SUB_NODE    = 0x00000001,
    IS_LAST         = 0x00000002
)

'''
MFTIndexValue
'''
MFTIndexValue = Struct(
    'FileReference'     / NTFSFileReference,
    'IndexValueSize'    / Int16ul,
    'IndexKeyDataSize'  / Int16ul,
    'Flags'             / MFTIndexValueFlags
    #TODO: index key and value data
)

'''
MFTIndexEntryHeader
'''
MFTIndexEntryHeader = Struct(
    'Signature'             / Const(b'INDX'),
    'FixupValuesOffset'     / Int16ul,
    'FixupValuesCount'      / Int16ul,
    'LogFileSequenceNumber' / Int64ul,
    'VirtualClusterNumber'  / Int64ul
)

'''
MFTIndexNodeFlags
'''
MFTIndexNodeFlags = FlagsEnum(Int32ul,
    HasIndexAllocation      = 0x00000001
)

'''
MFTIndexNodeHeader
'''
MFTIndexNodeHeader = Struct(
    'IndexValuesOffset'         / Int32ul,
    'IndexNodeSize'             / Int32ul,
    'AllocatedIndexNodeSize'    / Int32ul,
    Embedded(MFTIndexNodeFlags)
)

'''
MFTIndexRootCollationType
'''
MFTIndexRootCollationType = Enum(Int32ul,
    COLLATION_BINARY                = 0x00000000,
    COLLATION_FILENAME              = 0x00000001,
    COLLATION_UNICODE_STRING        = 0x00000002,
    COLLATION_NTOFS_ULONG           = 0x00000010,
    COLLATION_NTOFS_SID             = 0x00000011,
    COLLATION_NTOFS_SECURITY_HASH   = 0x00000012,
    COLLATION_NTOFS_ULONGS          = 0x00000013
)

'''
MFTIndexRootHeader
'''
MFTIndexRootHeader = Struct(
    'AttributeType'     / Int32ul,
    'CollationType'     / MFTIndexRootCollationType,
    'EntrySize'         / Int32ul,
    'ClusterBlockCount' / Int32ul
)
