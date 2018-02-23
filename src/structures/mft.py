# -*- coding: UTF-8 -*-
# mft.py
# Noah Rubin
# 02/01/2018

from construct import *

'''
MFT GUID: globally unique identifier
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
MFTGUID = Struct(
    'Group1'                / Int32ul,
    'Group2'                / Int16ul,
    'Group3'                / Int16ul,
    'Group4'                / Int16ul,
    'Group5'                / BytesInteger(6, swapped=True)
)

'''
MFT SID: Windows user/group security identifier
    Revision: SID format revision number
    SubAuthoritiesCount: Number of sub-authorities in this SID
    Authority: 48-bit (big endian) identifier authority identifying the authority that issues the SID
    SubAuthorities: Array of sub-authorities that identify the trustee relative to the authority (SID issuer)
    NOTE:
        A valid, full SID is of the form:
        S-1-5-32-544
        "S" is added when converting a SID to String form
        "1" the revision number
        "5" the identifier-authority value (SECURITY_NT_AUTHORITY)
        "32" the first subauthority value (SECURITY_BUILTIN_DOMAIN_RID)
        "544" the second subauthority value (DOMAIN_ALIAS_RID_ADMINS)
'''
MFTSID = Struct(
    'Revision'              / Int8ul,
    'SubAuthoritiesCount'   / Int8ul,
    'Authority'             / BytesInteger(6),
    'SubAuthorities'        / Array(this.SubAuthoritiesCount, Int32ul)
)

MFTACEType = Enum(Int8ul, 
    ACCESS_ALLOWED_ACE_TYPE                 = 0x00,
    ACCESS_DENIED_ACE_TYPE                  = 0x01,
    SYSTEM_AUDIT_ACE_TYPE                   = 0x02,
    SYSTEM_ALARM_ACE_TYPE                   = 0x03,
    ACCESS_ALLOWED_COMPOUND_ACE_TYPE        = 0x04,
    ACCESS_ALLOWED_OBJECT_ACE_TYPE          = 0x05,
    ACCESS_DENIED_OBJECT_ACE_TYPE           = 0x06,
    SYSTEM_AUDIT_OBJECT_ACE_TYPE            = 0x07,
    SYSTEM_ALARM_OBJECT_ACE_TYPE            = 0x08,
    ACCESS_ALLOWED_CALLBACK_ACE_TYPE        = 0x09,
    ACCESS_DENIED_CALLBACK_ACE_TYPE         = 0x0a,
    ACCESS_ALLOWED_CALLBACK_OBJECT_ACE_TYPE = 0x0b,
    ACCESS_DENIED_CALLBACK_OBJECT_ACE_TYPE  = 0x0c,
    SYSTEM_AUDIT_CALLBACK_ACE_TYPE          = 0x0d,
    SYSTEM_ALARM_CALLBACK_ACE_TYPE          = 0x0e,
    SYSTEM_AUDIT_CALLBACK_OBJECT_ACE_TYPE   = 0x0f,
    SYSTEM_ALARM_CALLBACK_OBJECT_ACE_TYPE   = 0x10,
    SYSTEM_MANDATORY_LABEL_ACE_TYPE         = 0x11
)

MFTACEFlags = FlagsEnum(Int8ul,
    OBJECT_INHERIT_ACE          = 0x01,
    CONTAINER_INHERIT_ACE       = 0x02,
    NO_PROPAGATE_INHERIT_ACE    = 0x04,
    INHERIT_ONLY_ACE            = 0x08,
    SUCCESSFUL_ACCESS_ACE_FLAG  = 0x40,
    FAILED_ACCESS_ACE_FLAG      = 0x80
)

'''
MFT ACE Header: access control list entry
    AceType: the ACE type (see: MFTACEType)
    AceFlags: the ACE flags (see: MFTACEFlags)
    AceSize: the size of the ACE in bytes
'''
MFTACEHeader = Struct(
    'AceType'               / MFTACEType,
    'AceFlags'              / MFTACEFlags,
    'AceSize'               / Int16ul
)

'''
MFT ACL Header: access control list header
    AclRevision: the ACL revision number
    AclSize: The total size of the ACL in bytes, including the ACL header and all ACEs
    AceCount: The number of ACEs stored in the ACL
'''
MFTACLHeader = Struct(
    'AclRevision'           / Int8ul,
    Padding(1),
    'AclSize'               / Int16ul,
    'AceCount'              / Int16ul,
    Padding(2)
)

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
    STANDARD_INFORMATION    = 0x10,
    ATTRIBUTE_LIST          = 0x20,
    FILE_NAME               = 0x30,
    OBJECT_ID               = 0x40,
    SECURITY_DESCRIPTOR     = 0x50,
    VOLUME_NAME             = 0x60,
    VOLUME_INFORMATION      = 0x70,
    DATA                    = 0x80,
    INDEX_ROOT              = 0x90,
    INDEX_ALLOCATION        = 0xA0,
    BITMAP                  = 0xB0,
    REPARSE_POINT           = 0xC0,
    EA_INFORMATION          = 0xD0,
    EA                      = 0xE0,
    LOGGED_UTILITY_STREAM   = 0x100
)

'''
MFT File Reference: pointer to base (parent) MFT record (0 if this is base record)
    SegmentNumber:  MFT entry index value
    SequenceNumber: MFT entry sequence number
'''
MFTFileReference = Struct(
    'SegmentNumber'         / Int32ul,
    Padding(2),
    'SequenceNumber'        / Int16ul
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
MFTFileAttributeFlags = FlagsEnum(Int32ul,
    READONLY                = 0x00000001,
    HIDDEN                  = 0x00000002,
    SYSTEM                  = 0x00000004,
    VOLUME                  = 0x00000008,
    DIRECTORY               = 0x00000010,
    ARCHIVE                 = 0x00000020,
    DEVICE                  = 0x00000040,
    NORMAL                  = 0x00000080,
    TEMPORARY,              = 0x00000100,
    SPARSE_FILE,            = 0x00000200,
    REPARSE_POINT,          = 0x00000400,
    COMPRESSED,             = 0x00000800,
    OFFLINE,                = 0x00001000,
    NOT_CONTENT_INDEXED,    = 0x00002000,
    ENCRYPTED,              = 0x00004000,
    VIRTUAL                 = 0x00010000
)

'''
MFTFILETIME
'''
MFTFILETIME = Struct(
    'dwLowDateTime'         / Int32ul,
    'dwHighDateTime'        / Int32ul
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
    'Flags'                 / FlagsEnum(Int16ul,
        ACTIVE      = 0x0001,
        HAS_INDEX   = 0x0002),
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
    'FileName'              / PascalString(this.FileNameLength, encoding='utf16')
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

'''
MFTDataRunEntry
TODO: Incomplete
'''
MFTDataRunEntry = Struct(
    'DataRunSize'           / Bitwise(BitsInteger(4, signed=True, swapped=True)),
    'DataRunOffset'         / Bitwise(BitsInteger(4, swapped=True))
)

'''
MFTAttributeListEntry
'''
MFTAttributeListEntry = Struct(
    'AttributeTypeCode'     / MFTAttributeTypeCode,
    'RecordLength'          / Int16ul,
    'AttributeNameLength'   / Int8ul,
    'AttributeNameOffset'   / Int8ul,
    'LowestVcn'             / Int64ul,
    'SegmentReference'      / MFTFileReference,
    'AttributeIdentifier'   / Int16ul,
    'AttributeName'         / PascalString(this.AttributeNameLength * 2, encoding='utf16')
)

'''
MFTObjectID
'''
MFTObjectID = Struct(
    'ObjectID'              / MFTGUID,
    'BirthVolumeID'         / MFTGUID,
    'BirthObjectID'         / MFTGUID,
    'DomainID'              / MFTGUID
)

'''
MFTSecurityDescriptorControlFlags
'''
MFTSecurityDescriptorControlFlags = FlagsEnum(Int16ul,
    SE_OWNER_DEFAULTED      = 0x0001,
    SE_GROUP_DEFAULTED      = 0x0002,
    SE_DACL_PRESENT         = 0x0004,
    SE_DACL_DEFAULTED       = 0x0008,
    SE_SACL_PRESENT         = 0x0010,
    SE_SACL_DEFAULTED       = 0x0020,
    SE_DACL_AUTO_INHERIT_REQ    = 0x0100,
    SE_SACL_AUTO_INHERIT_REQ    = 0x0200,
    SE_DACL_AUTO_INHERITED      = 0x0400,
    SE_SACL_AUTO_INHERITED      = 0x0800,
    SE_DACL_PROTECTED       = 0x1000,
    SE_SACL_PROTECTED       = 0x2000,
    SE_RM_CONTROL_VALID     = 0x4000,
    SE_SELF_RELATIVE        = 0x8000
)

'''
MFTSecurityDescriptorHeader
'''
MFTSecurityDescriptorHeader = Struct(
    'Revision'              / Int8ul,
    'Sbz1'                  / Int8ul,
    'Control'               / MFTSecurityDescriptorControlFlags,
    'OwnerSIDOffset'        / Int32ul,
    'GroupSIDOffset'        / Int32ul,
    'SACLOffset'            / Int32ul,
    'DACLOffset'            / Int32ul
)
