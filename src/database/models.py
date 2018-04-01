## -*- coding: UTF8 -*-
## models.py
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

from datetime import datetime
import re
from sqlalchemy.orm import relationship
from sqlalchemy.types import String, Text, Integer, TIMESTAMP, BigInteger, Boolean, LargeBinary
from sqlalchemy import Column, ForeignKey, Index, text
from sqlalchemy.schema import UniqueConstraint, CheckConstraint, DDL
from sqlalchemy.ext.declarative import declarative_base, declared_attr

from src.utils.database import TimestampDefaultExpression, create_view 

class BaseTableTemplate(object):
    '''
    Base table class
    '''
    @declared_attr
    def __tablename__(cls):
        return str(cls.__name__.lower())

    @staticmethod
    def _convert_key(key):
        '''
        Args:
            key: String => key to convert
        Returns:
            String
            key converted from camel case to snake case
            NOTE:
                Implementation taken from:
                https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case#1176023
        Preconditions:
            key is of type String
        '''
        assert isinstance(key, str), 'Key is not of type String'
        return re.sub(\
            '([a-z0-9])([A-Z])', r'\1_\2', re.sub(\
                '(.)([A-Z][a-z]+)', r'\1_\2', key\
            )\
        ).lower()
    def populate_fields(self, data_dict, overwrite=True):
        '''
        Args:
            data_dict: Dict<String, Any>    => dict containing data to map to fields
            overwrite: Boolean              => whether to overwrite values of current instance
        Procedure:
            Populate attributes of this instance with values from data_dict
            where each key in data_dict maps a value to an attribute.
            For example, to populate id and created_at, data_dict would be:
            {
                'id': <Integer>,
                'created_at': <DateTime>
            }
        Preconditions:
            data_dict is of type Dict<String, Any>
        '''
        assert hasattr(data_dict, '__getitem__') and all((isinstance(key, str) for key in data_dict)), 'Data_dict is not of type Dict<String, Any>'
        for key in data_dict:
            converted_key = self._convert_key(key)
            if hasattr(self, converted_key) and (getattr(self, converted_key) is None or overwrite):
                setattr(self, converted_key, data_dict[key])
        return self

BaseTable = declarative_base(cls=BaseTableTemplate)

class ViewMixin(object):
    '''
    Mixin for (materialized) views
    '''
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

class ConcreteTableMixin(ViewMixin):
    '''
    Mixin class for (non-view) tables
    '''
    id          = Column(BigInteger().with_variant(Integer, 'sqlite'), primary_key=True)
    created_at  = Column(TIMESTAMP(timezone=True), server_default=TimestampDefaultExpression(), index=True)

class FileLedgerLinkedMixin(object):
    '''
    Mixin for tables linked to fileledger table
    fileledger table serves as accounting system for parser
    '''
    @declared_attr
    def meta_id(cls):
        return Column(BigInteger, ForeignKey('fileledger.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)

class EntryHeaderLinkedMixin(object):
    '''
    Mixin for tables linked to entry header table
    '''
    @declared_attr
    def entry_header_id(cls):
        return Column(BigInteger, ForeignKey('entryheader.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)

class AttributeHeaderLinkedMixin(object):
    '''
    Mixin for tables linked to attribute header table
    '''
    @declared_attr
    def attribute_header_id(cls):
        return Column(BigInteger, ForeignKey('attributeheader.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)

class FileLedger(BaseTable, ConcreteTableMixin):
    '''
    Parsed $MFT file ledger (tracking) table
    '''
    file_name               = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    file_path               = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    file_size               = Column(BigInteger, nullable=False)
    md5hash                 = Column(String().with_variant(Text, 'postgresql'))
    sha1hash                = Column(String().with_variant(Text, 'postgresql'))
    sha2hash                = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    modify_time             = Column(TIMESTAMP(timezone=True))
    access_time             = Column(TIMESTAMP(timezone=True))
    create_time             = Column(TIMESTAMP(timezone=True))
    completed               = Column(Boolean, index=True)
    entry_headers           = relationship('EntryHeader', backref='file_ledger')

class EntryHeader(BaseTable, ConcreteTableMixin, FileLedgerLinkedMixin):
    '''
    $MFT entry header table
    '''
    mft_record_number               = Column(Integer, nullable=False)
    sequence_number                 = Column(Integer, nullable=False)
    log_file_sequence_number        = Column(Integer, nullable=False)
    signature                       = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    active                          = Column(Boolean, index=True)
    has_index                       = Column(Boolean, index=True)
    first_attribute_id              = Column(Integer, nullable=False)
    first_attribute_offset          = Column(Integer, nullable=False)
    update_sequence_array_offset    = Column(Integer, nullable=False)
    update_sequence_array_size      = Column(Integer, nullable=False)
    reference_count                 = Column(Integer, nullable=False)
    total_size                      = Column(Integer, nullable=False)
    used_size                       = Column(Integer, nullable=False)
    base_file_record_segment        = relationship('FileReference', uselist=False, backref='entry_header')

class AttributeHeader(BaseTable, ConcreteTableMixin, EntryHeaderLinkedMixin):
    '''
    $MFT entry attribute header table
    '''
    type_code               = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    record_length           = Column(Integer, nullable=False)
    name_length             = Column(Integer, nullable=False)
    name_offset             = Column(Integer, nullable=False)
    name                    = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    instance                = Column(Integer, nullable=False)
    form_code               = Column(Integer, nullable=False)
    index_flag              = Column(Integer, nullable=False)
    value_length            = Column(Integer, nullable=False)
    value_offset            = Column(Integer, nullable=False)
    flag_compression_mask   = Column(Boolean)
    flag_encrypted          = Column(Boolean)
    flag_sparse             = Column(Boolean)
    lowest_vcn              = Column(Integer)
    highest_vcn             = Column(Integer)
    mapping_pairs_offset    = Column(Integer)
    compression_unit_size   = Column(Integer)
    allocated_length        = Column(Integer)
    file_size               = Column(Integer)
    valid_data_length       = Column(Integer)
    total_allocated         = Column(Integer)
    standard_information    = relationship('StandardInformation', uselist=False, backref='header')
    attribute_list          = relationship('AttributeListEntry', backref='header')
    file_name               = relationship('FileName', uselist=False, backref='header')
    object_id               = relationship('ObjectIdEntry', backref='header')
    volume_name             = relationship('VolumeName', uselist=False, backref='header')
    volume_information      = relationship('VolumeInformation', uselist=False, backref='header')
    index_root              = relationship('IndexRoot', uselist=False, backref='header')

class StandardInformation(BaseTable, ConcreteTableMixin, AttributeHeaderLinkedMixin):
    '''
    $MFT entry standard information attribute table
    '''
    version_number          = Column(Integer, nullable=False)
    usn                     = Column(Integer, nullable=False)
    security_descriptor_id  = Column(Integer, nullable=False)
    quota                   = Column(Integer, nullable=False)
    owner_identifier        = Column(Integer, nullable=False)
    maximum_versions        = Column(Integer, nullable=False)
    last_modified_time      = Column(TIMESTAMP(timezone=True), nullable=False)
    last_access_time        = Column(TIMESTAMP(timezone=True), nullable=False)
    entry_modified_time     = Column(TIMESTAMP(timezone=True), nullable=False)
    create_time             = Column(TIMESTAMP(timezone=True), nullable=False)
    file_attribute_flags    = relationship('FileAttributeFlags', uselist=False)

class AttributeListEntry(BaseTable, ConcreteTableMixin, AttributeHeaderLinkedMixin):
    '''
    $MFT entry atrribute list entry table
    '''
    attribute_identifier    = Column(Integer, nullable=False)
    attribute_name          = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    attribute_name_length   = Column(Integer, nullable=False)
    attribute_name_offset   = Column(Integer, nullable=False)
    attribute_type_code     = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    lowest_vcn              = Column(Integer, nullable=False)
    record_length           = Column(Integer, nullable=False)
    segment_reference       = relationship('FileReference', uselist=False)

class FileName(BaseTable, ConcreteTableMixin, AttributeHeaderLinkedMixin):
    '''
    $MFT entry file name attribute table
    '''
    file_name_length        = Column(Integer, nullable=False)
    file_name_namespace     = Column(Integer, nullable=False)
    file_name               = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    file_size               = Column(Integer, nullable=False)
    last_modified_time      = Column(TIMESTAMP(timezone=True), nullable=False)
    last_access_time        = Column(TIMESTAMP(timezone=True), nullable=False)
    entry_modified_time     = Column(TIMESTAMP(timezone=True), nullable=False)
    create_time             = Column(TIMESTAMP(timezone=True), nullable=False)
    file_attribute_flags    = relationship('FileAttributeFlags', uselist=False)
    parent_directory        = relationship('FileReference', uselist=False)

class ObjectIdEntry(BaseTable, ConcreteTableMixin, AttributeHeaderLinkedMixin):
    '''
    $MFT entry object id attribute entry table
    '''
    title                   = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    group_1                 = Column(Integer, nullable=False)
    group_2                 = Column(Integer, nullable=False)
    group_3                 = Column(Integer, nullable=False)
    group_4                 = Column(Integer, nullable=False)
    group_5                 = Column(Integer, nullable=False)

class SecurityDescriptor(BaseTable, ConcreteTableMixin, AttributeHeaderLinkedMixin):
    '''
    $MFT entry security descriptor table
    '''
    revision                        = Column(Integer, nullable=False)
    sbz1                            = Column(Integer, nullable=False)
    owner_sid_offset                = Column(Integer, nullable=False)
    group_sid_offset                = Column(Integer, nullable=False)
    sacl_offset                     = Column(Integer, nullable=False)
    dacl_offset                     = Column(Integer, nullable=False)
    flag_se_dacl_auto_inherited     = Column(Boolean, nullable=False)
    flag_se_dacl_auto_inherit_req   = Column(Boolean, nullable=False)
    flag_se_dacl_defaulted          = Column(Boolean, nullable=False)
    flag_se_dacl_present            = Column(Boolean, nullable=False)
    flag_se_dacl_protected          = Column(Boolean, nullable=False)
    flag_se_group_defaulted         = Column(Boolean, nullable=False)
    flag_se_owner_defaulted         = Column(Boolean, nullable=False)
    flag_se_rm_control_valid        = Column(Boolean, nullable=False)
    flag_se_sacl_auto_inherited     = Column(Boolean, nullable=False)
    flag_se_sacl_auto_inherit_req   = Column(Boolean, nullable=False)
    flag_se_sacl_defaulted          = Column(Boolean, nullable=False)
    flag_se_sacl_present            = Column(Boolean, nullable=False)
    flag_se_sacl_protected          = Column(Boolean, nullable=False)
    flag_se_self_relative           = Column(Boolean, nullable=False)
    owner_sid                       = relationship(\
        'SID', 
        uselist=False, 
        primaryjoin='and_(SecurityDescriptor.id == SID.security_descriptor_id, SID.tag == "owner")'\
    )
    group_sid               = relationship(\
        'SID', 
        uselist=False, 
        primaryjoin='and_(SecurityDescriptor.id == SID.security_descriptor_id, SID.tag == "group")'\
    )
    sacl                    = relationship(\
        'AccessControlList',
        uselist=False,
        primaryjoin='and_(SecurityDescriptor.id == AccessControlList.security_descriptor_id, AccessControlList.tag == "system")'\
    )
    dacl                    = relationship(\
        'AccessControlList',
        uselist=False,
        primaryjoin='and_(SecurityDescriptor.id == AccessControlList.security_descriptor_id, AccessControlList.tag == "discretionary")'\
    )

class AccessControlList(BaseTable, ConcreteTableMixin):
    '''
    Security descriptor access control list table
    '''
    security_descriptor_id  = Column(BigInteger, ForeignKey('securitydescriptor.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True, index=True)
    acl_revision            = Column(Integer, nullable=False)
    ace_count               = Column(Integer, nullable=False)
    acl_size                = Column(Integer, nullable=False)
    tag                     = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    entries                 = relationship('AccessControlEntry')

class AccessControlEntry(BaseTable, ConcreteTableMixin):
    '''
    Access control list access control entry table
    '''
    access_control_entry_id         = Column(BigInteger, ForeignKey('accesscontrolentry.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True, index=True)
    ace_size                        = Column(Integer, nullable=False)
    ace_type                        = Column(Integer, nullable=False)
    flag_container_inherit_ace      = Column(Boolean, nullable=False)
    flag_inherit_only_ace           = Column(Boolean, nullable=False)
    flag_no_propagate_inherit_ace   = Column(Boolean, nullable=False)
    flag_object_inherit_ace         = Column(Boolean, nullable=False)
    flag_failed_access_ace_flag     = Column(Boolean, nullable=False)
    flag_successful_access_ace_flag = Column(Boolean, nullable=False)
    flag_access_system_security     = Column(Boolean, nullable=False)
    flag_generic_all                = Column(Boolean, nullable=False)
    flag_generic_execute            = Column(Boolean, nullable=False)
    flag_generic_read               = Column(Boolean, nullable=False)
    flag_generic_write              = Column(Boolean, nullable=False)
    flag_maximum_allowed            = Column(Boolean, nullable=False)
    flag_delete                     = Column(Boolean, nullable=False)
    flag_read_control               = Column(Boolean, nullable=False)
    flag_synchronize                = Column(Boolean, nullable=False)
    flag_write_dac                  = Column(Boolean, nullable=False)
    flag_write_owner                = Column(Boolean, nullable=False)
    standard_rights                 = Column(Integer, nullable=False)
    trustee_sid                     = relationship('SID', uselist=False)

class VolumeName(BaseTable, ConcreteTableMixin, AttributeHeaderLinkedMixin):
    '''
    $MFT entry volume name table
    '''
    name                    = Column(String().with_variant(Text, 'postgresql'), nullable=False)

class VolumeInformation(BaseTable, ConcreteTableMixin, AttributeHeaderLinkedMixin):
    '''
    $MFT entry volume information table
    '''
    major_version           = Column(Integer, nullable=False)
    minor_version           = Column(Integer, nullable=False)
    flag_dirty              = Column(Boolean, nullable=False)
    flag_resize_logifle     = Column(Boolean, nullable=False)
    flag_mount_upgrade      = Column(Boolean, nullable=False)
    flag_mount_nt4          = Column(Boolean, nullable=False)
    flag_delete_usn         = Column(Boolean, nullable=False)
    flag_objectid_repair    = Column(Boolean, nullable=False)
    flag_chkdsk_modified    = Column(Boolean, nullable=False)

class IndexRoot(BaseTable, ConcreteTableMixin, AttributeHeaderLinkedMixin):
    '''
    $MFT entry index root table
    '''
    attribute_type                      = Column(Integer, nullable=False)
    collation_type                      = Column(Integer, nullable=False)
    index_allocation_entry_size         = Column(Boolean, nullable=False)
    index_record_cluster_block_count    = Column(Boolean, nullable=False)
    index_entrys_offset                 = Column(Integer, nullable=False)
    index_node_size                     = Column(Integer, nullable=False)
    allocated_index_node_size           = Column(Integer, nullable=False)
    flag_has_allocation_index           = Column(Boolean, nullable=False)
    entries                             = relationship('IndexEntry')

class IndexEntry(BaseTable, ConcreteTableMixin):
    '''
    Index entry value table
    '''
    index_root_id           = Column(BigInteger, ForeignKey('indexroot.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    index_entry_size        = Column(Integer, nullable=False)
    index_key_data_size     = Column(Integer, nullable=False)
    flag_has_sub_node       = Column(Boolean, nullable=False)
    flag_is_last            = Column(Boolean, nullable=False)
    file_reference          = relationship('FileReference', uselist=False)

class Data(BaseTable, ConcreteTableMixin, AttributeHeaderLinkedMixin):
    '''
    $MFT entry data attribute table
    '''
    content                 = Column(LargeBinary, nullable=False)
    sha2hash                = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    
class SID(BaseTable, ConcreteTableMixin):
    '''
    $MFT entry SID table
    '''
    security_descriptor_id  = Column(BigInteger, ForeignKey('securitydescriptor.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True, index=True)
    access_control_entry_id = Column(BigInteger, ForeignKey('accesscontrolentry.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True, index=True)
    identifier              = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    tag                     = Column(String().with_variant(Text, 'postgresql'))
    __table_args__ = (\
        CheckConstraint('security_descriptor_id IS NOT NULL OR access_control_entry_id IS NOT NULL'),
    )

class FileAttributeFlags(BaseTable, ConcreteTableMixin):
    '''
    $MFT entry file attribute flags table
    '''
    standard_information_id = Column(BigInteger, ForeignKey('standardinformation.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True, index=True)
    file_name_id            = Column(BigInteger, ForeignKey('filename.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True, index=True)
    attribute_list_entry_id = Column(BigInteger, ForeignKey('attributelistentry.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True, index=True)
    archive                 = Column(Boolean, nullable=False)
    compressed              = Column(Boolean, nullable=False)
    device                  = Column(Boolean, nullable=False)
    directory               = Column(Boolean, nullable=False)
    encrypted               = Column(Boolean, nullable=False)
    hidden                  = Column(Boolean, nullable=False)
    normal                  = Column(Boolean, nullable=False)
    not_content_indexed     = Column(Boolean, nullable=False)
    offline                 = Column(Boolean, nullable=False)
    readonly                = Column(Boolean, nullable=False)
    reparse_point           = Column(Boolean, nullable=False)
    sparse_file             = Column(Boolean, nullable=False)
    system                  = Column(Boolean, nullable=False)
    temporary               = Column(Boolean, nullable=False)
    virtual                 = Column(Boolean, nullable=False)
    volume                  = Column(Boolean, nullable=False)
    __table_args__ = (\
        CheckConstraint('standard_information_id IS NOT NULL OR file_name_id IS NOT NULL OR attribute_list_entry_id IS NOT NULL'),
    )

class FileReference(BaseTable, ConcreteTableMixin):
    '''
    $MFT entry file references table
    '''
    entry_header_id         = Column(BigInteger, ForeignKey('entryheader.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True, index=True)
    file_name_id            = Column(BigInteger, ForeignKey('filename.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True, index=True)
    index_entry_id          = Column(BigInteger, ForeignKey('indexentry.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True, index=True)
    segment_number          = Column(Integer, nullable=False)
    sequence_number         = Column(Integer, nullable=False)
    __table_args__ = (\
        CheckConstraint('entry_header_id IS NOT NULL OR file_name_id IS NOT NULL OR index_entry_id IS NOT NULL'),
    )
