## -*- coding: UTF-8 -*-
## security_descriptor.py
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

from construct import Struct, FlagsEnum, Int32ul, Int16ul, Int8ul
from .general.access_control import *

'''
MFT Security Descriptor Control Flags: determines how security descriptor should be interpreted
    SE_OWNER_DEFAULTED: owner SID was set by default mechanism (can be used by resource manager)
    SE_GROUP_DEFAULTED: group SID was set by default mechanism (can be used by resource manager)
    SE_DACL_PRESENT: indicates whether the security descriptor has a DACL (if null or is set 
                     and DALC is null, full permissions on object are granted to everyone)
    SE_DACL_DEFAULTED: indicates the security descriptor has a default DACL (i.e. if a user
                       does not specify a DACL on creation of an object, that object will receive
                       the default DACL of the user's access token)
    SE_SACL_PRESENT: indicates whether the security descriptor has an SACL
    SE_SACL_DEFAULTED: indicates whether a default mechanism set the SACL
    SE_DACL_AUTO_INHERIT_REQ: indicates a required security descriptor in which the DACL supports
                              automatic propogation of inheritable access control entries to child objects
    SE_SACL_AUTO_INHERIT_REQ: indicates a required security descriptor in which the SACL supports
                              automatic propogation of inheritable access control entries to child objects
    SE_DACL_AUTO_INHERITED: same as SE_DACL_AUTO_INHERIT_REQ, but for non-required security descriptors
    SE_SACL_AUTO_INHERITED: same as SE_SACL_AUTO_INHERIT_REQ, but for non-required security descriptors
    SE_DACL_PROTECTED: prevents DACL from being modified by inheritable access control entries
    SE_SACL_PROTECTED: prevents SACL from being modified by inheritable access control entries
    SE_RM_CONTROL_VALID: indicates that the resource manager control is valid
    SE_SELF_RELATIVE: whether the security descriptor is in absolute or self-relative format
                      (absolute security descriptors contain pointers to the information, whereas
                      self-relative security descriptors contain the information in a contiguous 
                      memory/disk block)
    NOTE:
        See https://msdn.microsoft.com/en-us/library/windows/desktop/aa379566(v=vs.85).aspx
        for more details.
'''
MFTSecurityDescriptorControlFlags = FlagsEnum(Int16ul,
    SE_OWNER_DEFAULTED          = 0x0001,
    SE_GROUP_DEFAULTED          = 0x0002,
    SE_DACL_PRESENT             = 0x0004,
    SE_DACL_DEFAULTED           = 0x0008,
    SE_SACL_PRESENT             = 0x0010,
    SE_SACL_DEFAULTED           = 0x0020,
    SE_DACL_AUTO_INHERIT_REQ    = 0x0100,
    SE_SACL_AUTO_INHERIT_REQ    = 0x0200,
    SE_DACL_AUTO_INHERITED      = 0x0400,
    SE_SACL_AUTO_INHERITED      = 0x0800,
    SE_DACL_PROTECTED           = 0x1000,
    SE_SACL_PROTECTED           = 0x2000,
    SE_RM_CONTROL_VALID         = 0x4000,
    SE_SELF_RELATIVE            = 0x8000
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
