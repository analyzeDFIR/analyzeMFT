# -*- coding: UTF-8 -*-
# volume_information.py
# Noah Rubin
# 02/24/2018

from construct import *

MFTVolumeInformationFlags = FlagsEnum(Int16ul,
    DIRTY               = 0x0001,
    RESIZE_LOGFILE      = 0x0002,
    MOUNT_UPGRADE       = 0x0004,
    MOUNT_NT4           = 0x0008,
    DELETE_USN          = 0x0010,
    OBJECTID_REPAIR     = 0x0020,
    CHKDSK_MODIFIED     = 0x8000
)

MFTVolumeInformation = Struct(
    Padding(8),
    'MajorVersion'      / Int8ul,
    'MinorVersion'      / Int8ul,
    'Flags'             / MFTVolumeInformationFlags
)
