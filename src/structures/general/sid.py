# -*- coding: UTF-8 -*-
# sid.py
# Noah Rubin
# 02/24/2018

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
