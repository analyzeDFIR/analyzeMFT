# -*- coding: UTF-8 -*-
# mft_structs.py
# Noah Rubin
# 02/01/2018

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
MFTAttributeTypeCode = Enum(Int64ul, 
    std_info    = 0x10,
    attr_list   = 0x20,
    file_name   = 0x30,
    obj_id      = 0x40,
    sec_descr   = 0x50,
    vol_name    = 0x60,
    vol_info    = 0x70,
    data        = 0x80,
    idx_root    = 0x90,
    idx_alloc   = 0xA0,
    bitmap      = 0xB0,
    rep_point   = 0xC0,
    ea_info     = 0xD0,
    ea          = 0xE0,
    log_utl_str = 0x100
)

'''
MFT File Reference: pointer to base (parent) MFT record (0 if this is base record)
    SegmentNumber:  MFT entry index value
    SequenceNumber: MFT entry sequence number
'''
MFTFileReference = Struct(
    'SegmentNumber'     / Int32ul,
    Padding(2),
    'SequenceNumber'    / Int16ul
)

'''
MFT Resident Attribute Data: length and offset of resident data in MFT attribute
    ValueLength:    size of attribute data in bytes
    ValueOffset:    offset of attribute data in bytes from start of MFT attribute
    IndexFlag:      Unknown (TODO: figure out what this is)
'''
MFTResidentAttributeData = Struct(
    'ValueLength'           / Int32ul,
    'ValueOffset'           / Int16ul,
    'IndexFlag'             / Int8ul,
    Padding(2)
)

'''
MFT Non-Resident Attribute Data: length and offset information of non-resident MFT attribute data
    LowestVCN:              lowest virtual cluster number (VCN) covered by attribute
    HighestVCN:             highest virtual cluster number (VCN) covered by attribute
    MappingPairsOffset:     offset to the mapping pairs array from start of attribute record in bytes,
                            where the mapping pairs array is a mapping from virtual to logical
                            cluster numbers
    CompressionUnitSize:    compression unit size as 2^n number of cluster blocks
    AllocatedLength:        allocated size of file in bytes, where size is event multiple of cluster
                            size (invalid if LowestVCN is non-zero)
    FileSize                file size in bytes, where size is highest readable byte plus 1 (invalid if
                            LowestVCN is non-zero)
    ValidDataLength:        length of valid data in file in bytes, where length is highest initialized
                            byte plus 1 (invalid if LowestVCN is non-zero)
    TotalAllocated:         sum of allocated clusters for the file

'''
MFTNonResidentAttributeData = Struct(
    'LowestVCN'             / Int32ul,
    Padding(4),
    'HighestVCN'            / Int32ul,
    Padding(4),
    'MappingPairsOffset'    / Int16ul,
    'CompressionUnitSize',  / Int16ul,
    Padding(4),
    'AllocatedLength'       / Int64ul,
    'FileSize'              / Int64ul,
    'ValidDataLength'       / Int64ul,
    'TotalAllocated'        / Optional(Int64ul)
)

'''
MFT Multi Sector Header: update sequence array metadata container
    Signature:                  header signature (in MFT entry header, will be 'FILE', 'BAAD', or
                                other value signalling a corrupt entry)
    UpdateSequenceArrayOffset:  offset to update sequence array from start of this structure in bytes
    UpdateSequenceArraySize:    size of update sequence array in bytes

NOTE:
    the update sequence array is a sequence of n unsigned short (Int16ul) values that provide detection
    of incomplete multisector transfers for devices that have a physical sector size greater than or equal
    to the sequence number stride (512) or that do not transfer sectors out of order.
'''
MFTEntryMultiSectorHeader = Struct(
    'Signature'                 / Int32ul,
    'UpdateSequenceArrayOffset' / Int16ul,
    'UpdateSequenceArraySize'   / Int16ul
)

'''
MFTFileAttributeFlags
'''
MFTFileAttributeFlags = Struct(
    'Flags'                 / Int32ul,
    'READONLY'              / Computed(lambda this: this.Flags & 0x00000001),
    'HIDDEN'                / Computed(lambda this: this.Flags & 0x00000002),
    'SYSTEM'                / Computed(lambda this: this.Flags & 0x00000004),
    'VOLUME'                / Computed(lambda this: this.Flags & 0x00000008),
    'DIRECTORY'             / Computed(lambda this: this.Flags & 0x00000010),
    'ARCHIVE'               / Computed(lambda this: this.Flags & 0x00000020),
    'DEVICE'                / Computed(lambda this: this.Flags & 0x00000040),
    'NORMAL'                / Computed(lambda this: this.Flags & 0x00000080),
    'TEMPORARY',            / Computed(lambda this: this.Flags & 0x00000100),
    'SPARSE_FILE',          / Computed(lambda this: this.Flags & 0x00000200),
    'REPARSE_POINT',        / Computed(lambda this: this.Flags & 0x00000400),
    'COMPRESSED',           / Computed(lambda this: this.Flags & 0x00000800),
    'OFFLINE',              / Computed(lambda this: this.Flags & 0x00001000),
    'NOT_CONTENT_INDEXED',  / Computed(lambda this: this.Flags & 0x00002000),
    'ENCRYPTED',            / Computed(lambda this: this.Flags & 0x00004000),
    'VIRTUAL'               / Computed(lambda this: this.Flags & 0x00010000)
)

'''
MFTFILETIME
'''
MFTFILETIME = Struct(
    'dwLowDateTime'         / Int32ul,
    'dwHighDateTime'        / Int32ul,
    '_DateTime'             / Computed(WindowsTime(this).parse())
)

'''
MFT Entry Header: header structure for MFT entry
    MultiSectorHeader:          see MFTEntryMultiSectorHeader
    LogFileSequenceNumber:      $LogFile sequence number
    SequenceNumber:             MFT entry sequence number, incremented each time an MFT entry
                                is freed (must match SequenceNumber of BaseFileRecordSegment,
                                otherwise record segment is likely obsolete)
    ReferenceCount:             number of child MFT entries (TODO: clarify correctness)
    FirstAttributeOffset:       offset of first attribute of MFT entry from start of entry in bytes
    Flags:                      file flags
                                _Active (0x0001): FILE_RECORD_SEGMENT_IN_USE
                                _HasIndex (0x0002): FILE_FILE_NAME_INDEX_PRESENT (record is directory)
    UsedSize:                   number of bytes of the MFT entry in use
    TotalSize:                  total number of bytes of MFT entry (should be 1024)
    BaseFileRecordSegment:      see MFTFileReference
    MFTRecordNumber:            Unknown (TODO: figure out what this is)
'''
MFTEntryHeader = Struct(
    'MultiSectorHeader'     / MFTEntryMultiSectorHeader,
    'LogFileSequenceNumber' / Int64ul,
    'SequenceNumber'        / Int16ul,
    'ReferenceCount'        / Int16ul,
    'FirstAttributeOffset'  / Int16ul,
    'Flags'                 / Int16ul,
    '_Active'               / Computed(lambda this: this.Flags & 0x0001),
    '_HasIndex'             / Computed(lambda this: this.Flags & 0x0002),
    'UsedSize'              / Int32ul,
    'TotalSize'             / Int32ul,
    'BaseFileRecordSegment' / MFTFileReference,
    'FirstAttributeId'      / Int16ul,
    Optional(Padding(2)),
    'MFTRecordNumber'       / Optional(Int32ul)
)

'''
MFTAttributeHeader
'''
MFTAttributeHeader = Struct(
    'TypeCode'              / MFTAttributeTypeCode,
    'RecordLength'          / Int32ul,
    'FormCode'              / Int8ul,
    'NameLength'            / Int8ul,
    'NameOffset'            / Int16ul,
    'Flags'                 / Int16ul,
    'Instance'              / Int16ul,
    'Form'                  / IfThenElse(
        this.FormCode == 0,
        'Resident'          / MFTResidentAttributeData,
        'NonResident'       / MFTNonResidentAttributeData
    )
)

'''
MFTFileNameAttribute
'''
MFTFileNameAttribute = Struct(
    'ParentDirectory'       / MFTFileReference,
    'CreateTime'            / MFTFILETIME,
    'LastModifiedTime'      / MFTFILETIME,
    'EntryModifiedTime'     / MFTFILETIME,
    'LastAccessTime'        / MFTFILETIME,
    'AllocatedFileSize'     / Int64ul,
    'FileSize'              / Int64ul,
    'FileAttributeFlags'    / MFTFileAttributeFlags,
    'ExtendedData'          / Int32ul,
    'FileNameLength'        / Int8ul,
    'FileNameNamespace'     / Int8ul,
    'FileName'              / Computed(PascalString(Bytes(this.FileSize), encoding='UTF16'))
)

'''
MFTStandardInformationAttribute
'''
MFTStandardInformationAttribute = Struct(
    'CreateTime'            / MFTFILETIME,
    'LastModifiedTime'      / MFTFILETIME,
    'EntryModifiedTime'     / MFTFILETIME,
    'LastAccessTime'        / MFTFILETIME,
    'FileAttributeFlags'    / MFTFileAttributeFlags,
    'MaximumVersions'       / Int32ul,
    'VersionNumber'         / Int32ul,
    'ClassIdentifier'       / Int32ul,
    'OwnerIdentifier'       / Int32ul,
    'SecurityDescriptorID'  / Int32ul,
    'Quota'                 / Int64ul,
    'USN'                   / Int64ul
)
