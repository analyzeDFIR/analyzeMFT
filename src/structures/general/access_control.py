## -*- coding: UTF-8 -*-
## access_control.py
##
## Copyright (c) 2018 Noah Rubin
## 
## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:
## 
## The above copyright notice and this permission notice shall be included in all
## copies or substantial portions of the Software.
## 
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
## SOFTWARE.

from construct import *

'''
MFT ACE Acess Mask Standard Rights: standard access rights 
'''
MFTACEAccessMaskStandardRights = FlagsEnum(Int8ul,
    DELETE                  = 0x00010000,
    READ_CONTROL            = 0x00020000,
    WRITE_DAC               = 0x00040000,
    WRITE_OWNER             = 0x00080000,
    SYNCHRONIZE             = 0x00100000
)

'''
MFT ACE Access Mask: access control entry permissions flags
'''
MFTACEAcessMask = Struct(
    'SpecificRights'        / Int16ul,
    'StandardRights'        / MFTACEAccessMaskStandardRights,
    'ACCESS_SYSTEM_SECURITY'    / Bitwise(Flag),
    'MAXIMUM_ALLOWED'       / Bitwise(Flag),
    Padding(2),
    'GENERIC_ALL'           / Bitwise(Flag),
    'GENERIC_EXECUTE'       / Bitwise(Flag),
    'GENERIC_WRITE'         / Bitwise(Flag),
    'GENERIC_READ'          / Bitwise(Flag)
)

'''
MFT ACE Type: access control entry type
'''
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

'''
MFT ACE Flags: access control entry header flags
    OBJECT_INHERIT_ACE: Noncontainer child objects inherit 
                        the ACE as an effective ACE.
    CONTAINER_INHERIT_ACE: Child objects that are containers, 
                           such as directories, inherit the ACE as 
                           an effective ACE. The inherited ACE is 
                           inheritable unless the 
                           NO_PROPAGATE_INHERIT_ACE bit flag is also set.
    NO_PROPAGATE_INHERIT_ACE: If the ACE is inherited by a child object, 
                              the system clears the OBJECT_INHERIT_ACE and 
                              CONTAINER_INHERIT_ACE flags in the inherited ACE. 
                              This prevents the ACE from being inherited by 
                              subsequent generations of objects.
    INHERIT_ONLY_ACE: Indicates an inherit-only ACE, which does not control access 
                      to the object to which it is attached. If this flag is not set, 
                      the ACE is an effective ACE which controls access to the 
                      object to which it is attached.
    SUCCESSFUL_ACCESS_ACE_FLAG: Used with system-audit ACEs in a SACL to generate 
                                audit messages for successful access attempts.
    FAILED_ACCESS_ACE_FLAG: Used with system-audit ACEs in a system access control 
                            list (SACL) to generate audit messages for failed access attempts.
'''
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
