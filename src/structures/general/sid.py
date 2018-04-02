## -*- coding: UTF-8 -*-
## sid.py
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
NFTS SID: Windows user/group security identifier
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
NTFSSID = Struct(
    'Revision'              / Int8ul,
    'SubAuthoritiesCount'   / Int8ul,
    'Authority'             / BytesInteger(6),
    'SubAuthorities'        / Array(this.SubAuthoritiesCount, Int32ul)
)

def sid_to_string(sid):
    '''
    Args:
        sid: NTFSSID    => sid struct to convert to string
    Returns:
        String
        String representation of SID string in the form shown above
    Preconditions:
        sid is instance of NTFSSID
    '''
    return '-'.join(\
        ['S', str(sid.Revision), str(sid.Authority)] + \
        [str(sub_authority) for sub_authority in sid.SubAuthorities]\
    ) 

def string_to_sid(identifier):
    '''
    Args:
        identifier: String  => sid string to convert to NTFSSID
    Returns:
        Container<String, Any>
        Struct representation of String SID identifier
    Preconditions:
        identifier is of the format specified above (assumed True)
    '''
    split_identifier = identifier.strip().split('-')
    sub_authorities = [int(subauth) for subauth in split_identifier[3:]]
    return Container(\
        Revision=int(split_identifier[1]),
        SubAuthoritiesCount=len(sub_authorities),
        Authority=int(split_identifier[2]),
        SubAuthorities=sub_authorities\
    )
