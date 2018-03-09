# -*- coding: UTF-8 -*-
# mft.py
# Noah Rubin
# 02/24/2018

from construct import *

'''
MFT Attribute Type Code: type of attribute
    0x10: $STANDARD_INFORMATION:    File attributes (such as read-only and archive), 
                                    time stamps (such as file creation and last modified), 
                                    and the hard link count.
    Ox20: $ATTRIBUTE_LIST:          A list of attributes that make up the file and the 
                                    file reference of the MFT file record in which 
                                    each attribute is located.
    0X30: $FILE_NAME:               The name of the file, in Unicode characters.
    0X40: $OBJECT_ID:               An 64-byte object identifier
    0x50: $SECURITY_DESCRIPTOR:     Object containing ACL lists and other security properties.
    0X60: $VOLUME_NAME:             The volume label. Present in the $Volume file.
    0X70: $VOLUME_INFORMATION:      The volume information. Present in the $Volume file.
    0X80: $DATA:                    Contents of the file (if it can fit in the MFT).
    0X90: $INDEX_ROOT:              Used to implement filename allocation for large directories.
    0XA0: $INDEX_ALLOCATION:        Used to implement filename allocation for large directories.
    0XB0: $BITMAP:                  A bitmap index for a large directory.
    0XC0: $REPARSE_POINT:           The reparse point data.
'''
MFTAttributeTypeCode = Enum(Int32ul, 
    STANDARD_INFORMATION    = 0x00000010,
    ATTRIBUTE_LIST          = 0x00000020,
    FILE_NAME               = 0x00000030,
    OBJECT_ID               = 0x00000040,
    SECURITY_DESCRIPTOR     = 0x00000050,
    VOLUME_NAME             = 0x00000060,
    VOLUME_INFORMATION      = 0x00000070,
    DATA                    = 0x00000080,
    INDEX_ROOT              = 0x00000090,
    INDEX_ALLOCATION        = 0x000000A0,
    BITMAP                  = 0x000000B0,
    REPARSE_POINT           = 0x000000C0,
    EA_INFORMATION          = 0x000000D0,
    EA                      = 0x000000E0,
    LOGGED_UTILITY_STREAM   = 0x00000100,
    END_OF_ATTRIBUTES       = 0xFFFFFFFF
)

'''
MFTFileAttributeFlags
'''
MFTFileAttributeFlags = FlagsEnum(Int32ul,
    READONLY                = 0x00000001,
    HIDDEN                  = 0x00000002,
    SYSTEM                  = 0x00000004,
    VOLUME                  = 0x00000008,
    DIRECTORY               = 0x00000010,
    ARCHIVE                 = 0x00000020,
    DEVICE                  = 0x00000040,
    NORMAL                  = 0x00000080,
    TEMPORARY               = 0x00000100,
    SPARSE_FILE             = 0x00000200,
    REPARSE_POINT           = 0x00000400,
    COMPRESSED              = 0x00000800,
    OFFLINE                 = 0x00001000,
    NOT_CONTENT_INDEXED     = 0x00002000,
    ENCRYPTED               = 0x00004000,
    VIRTUAL                 = 0x00010000
)
