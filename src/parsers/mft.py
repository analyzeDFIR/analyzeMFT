# -*- coding: UTF-8 -*-
# mft.py
# Noah Rubin
# 02/21/2017

import logging
Logger = logging.getLogger(__name__)
from io import BytesIO
from construct.lib import Container

import src.structures.mft as mftstructs
from src.utils.time import WindowsTime
from src.utils.item import BaseItem, Field

class MFTAttributes(BaseItem):
    '''
    Represents resident attributes of an MFT entry
    '''
    STANDARD_INFORMATION    = Field(1)
    ATTRIBUTE_LIST          = Field(2)
    FILE_NAME               = Field(3)
    OBJECT_ID               = Field(4)
    SECURITY_DESCRIPTOR     = Field(5)
    VOLUME_NAME             = Field(6)
    VOLUME_INFORMATION      = Field(7)
    DATA                    = Field(8)
    INDEX_ROOT              = Field(9)
    INDEX_ALLOCATION        = Field(10)

class MFTEntry(BaseItem):
    '''
    Class for parsing Windows $MFT file entries
    '''
    Header      = Field(1)
    Attributes  = Field(2)

    def __init__(self, raw_entry, *args, load=False, **kwargs):
        super(MFTEntry, self).__init__(*args, **kwargs)
        self.Attributes = MFTAttributes()
        for key in self.Attributes.iterkeys:
            self.Attributes[key] = list()
        self._stream = None
        self.raw_entry = raw_entry
        if load:
            self.parse()
    def _clean_transform(self, value):
        '''
        '''
        if issubclass(type(value), Container):
            cleaned_value = Container(value)
            for key in cleaned_value.keys():
                if key.startswith('Raw'):
                    del cleaned_value[key]
                else:
                    cleaned_value[key] = self._clean_transform(cleaned_value[key])
            return cleaned_value
        else:
            return value
    def get_stream(self, persist=False):
        '''
        '''
        stream = BytesIO(self.raw_entry)
        if persist:
            self._stream = stream
        return stream
    def tell(self, stream=None):
        '''
        '''
        if stream is not None:
            try:
                return stream.tell()
            except:
                return None
        elif self._stream is not None:
            try:
                return self._stream.tell()
            except:
                return None
        else:
            #TODO: implement custom exception
            raise Exception('No stream to tell position of')
    def _parse_index_allocation(self, attribute_header, original_position, stream):
        '''
        '''
        #TODO
        return None
    def _parse_index_root(self, attribute_header, original_position, stream):
        '''
        '''
        #TODO
        return None
    def _parse_data(self, attribute_header, original_position, stream):
        '''
        '''
        #TODO
        return None
    def _parse_volume_information(self, attribute_header, original_position, stream):
        '''
        '''
        return self._clean_transform(mftstructs.MFTVolumeInformation.parse_stream(stream))
    def _parse_volume_name(self, attribute_header, original_position, stream):
        '''
        '''
        #TODO: check if ValueLength * 2 or just ValueLength
        return stream.read(attribute_header.Form.ValueLength).decode('UTF16')
    def _parse_access_control_list(self, stream=None):
        '''
        '''
        if stream is None:
            stream = self._stream
        try:
            acl = Container()
            acl.Header = mftstructs.MFTACLHeader.parse_stream(stream)
            acl_position = stream.tell()
            acl_size = acl.Header.AclSize - mftstructs.MFTACLHeader.sizeof()
            acl.Body = list()
            while (stream.tell() - acl_position) < acl_size:
                ace_position = stream.tell()
                try:
                    ace = Container()
                    ace.Header = mftstructs.MFTACEHeader.parse_stream(stream)
                    ace.Body = None
                    acl.Body.append(ace)
                    stream.seek(ace_position + ace.Header.AceSize)
                except:
                    break
            return self._clean_transform(acl)
        except:
            return None
    def _parse_security_descriptor(self, attribute_header, original_position, stream):
        '''
        '''
        header_position = self.tell(stream=stream)
        security_descriptor = dict(
            Revision=None, 
            Control=None, 
            OwnerSID=None, 
            GroupSID=None, 
            SACL=None, 
            DACL=None
        )
        security_descriptor_header = mftstructs.MFTSecurityDescriptorHeader.parse_stream(stream)
        security_descriptor['Revision'] = security_descriptor_header.Revision
        security_descriptor['Control'] = dict(security_descriptor_header.Control)
        stream.seek(header_position + security_descriptor_header.OwnerSIDOffset)
        security_descriptor['OwnerSID'] = mftstructs.NTFSSID.parse_stream(stream)
        stream.seek(header_position + security_descriptor_header.GroupSIDOffset)
        security_descriptor['GroupSID'] = mftstructs.NTFSSID.parse_stream(stream)
        stream.seek(header_position + security_descriptor_header.SACLOffset)
        security_descriptor['SACL'] = self._parse_access_control_list(stream=stream)
        stream.seek(header_position + security_descriptor_header.DACLOffset)
        security_descriptor['DACL'] = self._parse_access_control_list(stream=stream)
        return security_descriptor
    def _parse_object_id(self, attribute_header, original_position, stream):
        '''
        '''
        object_id = mftstructs.MFTObjectID.parse_stream(stream)
        return self._clean_transform(object_id)
    def _parse_file_name(self, attribute_header, original_position, stream):
        '''
        '''
        file_name = mftstructs.MFTFileNameAttribute.parse_stream(stream)
        for field in file_name:
            if field.startswith('Raw') and field.endswith('Time'):
                file_name[field.replace('Raw', '')] = WindowsTime(file_name[field]).parse()
        file_name.FileName = stream.read(file_name.FileNameLength * 2).decode('UTF16')
        return self._clean_transform(file_name)
    def _parse_attribute_list(self, attribute_header, original_position, stream):
        '''
        '''
        attributes = MFTAttributes()
        while self.tell(stream=stream) < attribute_header.get('Form').get('ValueLength'):
            AL_original_position = self.tell(stream=stream)
            try:
                attribute_list_entry = mftstructs.MFTAttributeListEntry.parse_stream(stream)
                if attribute_list_entry.AttributeTypeCode == 'END_OF_ATTRIBUTES':
                    break
                stream.seek(AL_original_position + attribute_list_entry.AttributeNameOffset)
                attribute_list_entry.AttributeName = stream.read(attribute_list_entry.AttributeNameLength * 2).decode('UTF16')
            except:
                break
            else:
                if attributes[attribute_list_entry.AttributeTypeCode] is None:
                    attributes[attribute_list_entry.AttributeTypeCode] = list()
                attributes[attribute_list_entry.AttributeTypeCode].append(self._clean_transform(attribute_list_entry))
                stream.seek(AL_original_position + attribute_list_entry.RecordLength)
        return self._clean_transform(attributes)
    def _parse_standard_information(self, attribute_header, original_position, stream):
        '''
        '''
        standard_information = mftstructs.MFTStandardInformationAttribute.parse_stream(stream)
        for field in standard_information:
            if field.startswith('Raw') and field.endswith('Time'):
                standard_information[field.replace('Raw', '')] = WindowsTime(standard_information[field]).parse()
        return self._clean_transform(standard_information)
    def parse_attribute(self, attribute_header, original_position, *args, stream=None, **kwargs):
        '''
        '''
        if stream is None:
            stream = self._stream
        stream.seek(original_position + attribute_header.Form.ValueOffset)
        try:
            attribute_parser = getattr(self, '_parse_' + attribute_header.TypeCode.lower(), None)
            if attribute_parser is None:
                #TODO: raise custom exception
                return None
            else:
                return attribute_parser(attribute_header, original_position, stream, *args, **kwargs)
        finally:
            stream.seek(original_position)
    def parse_attribute_header(self, original_position, stream=None):
        '''
        '''
        if stream is None:
            stream = self._stream
        attribute_header = mftstructs.MFTAttributeHeader.parse_stream(stream)
        if attribute_header.NameLength > 0:
            try:
                stream.seek(original_position + attribute_header.NameOffset)
                attribute_header.Name = stream.read(attribute_header.NameLength * 2.).decode('UTF16')
            except:
                attribute_header.Name = None
        else:
            attribute_header.Name = None
        return self._clean_transform(attribute_header)
    def parse_next_attribute(self, stream=None, header=None, attr_filter=None):
        '''
        '''
        if stream is None:
            stream = self._stream
        if header is None:
            header = self.Header
        original_position = self.tell(stream=stream)
        type_code = mftstructs.MFTAttributeTypeCode.parse_stream(stream)
        if type_code == 'END_OF_ATTRIBUTES' or \
            (attr_filter is not None and type_code not in attr_filter):
            return None, None
        stream.seek(original_position)
        next_attribute = Container()
        next_attribute.Header = self.parse_attribute_header(original_position, stream=stream)
        try:
            if next_attribute.Header.FormCode != 0:
                return next_attribute.Header.TypeCode, None
            next_attribute.Data = self.parse_attribute(next_attribute.Header, original_position, stream=stream)
            return next_attribute.Header.TypeCode, self._clean_transform(next_attribute)
        except:
            return next_attribute.Header.TypeCode, None
        finally:
            stream.seek(original_position + next_attribute.Header.RecordLength)
    def parse_header(self, stream=None):
        '''
        '''
        if stream is None:
            stream = self._stream
        header = mftstructs.MFTEntryHeader.parse_stream(stream)
        if header.MultiSectorHeader.RawSignature == 0x454c4946:
            header.MultiSectorHeader.Signature = 'FILE'
        elif header.MultiSectorHeader.RawSignature == 0x44414142:
            header.MultiSectorHeader.Signature = 'BAAD'
        else:
            header.MultiSectorHeader.Signature = 'CRPT'
        return self._clean_transform(header)
    def parse(self, attr_filter=None):
        '''
        args:
            N/A
        Procedure:
            Attempt to parse the supplied MFT entry, extracting
            header information and resident attribute data
        Preconditions:
            self.raw_entry is byte string of length 1024
        '''
        try:
            self.get_stream(True)
            self.Header = self.parse_header()
            self._stream.seek(self.Header.FirstAttributeOffset)
            while self.tell() < self.Header.UsedSize:
                attribute_type, attribute_data = self.parse_next_attribute(attr_filter=attr_filter)
                if attribute_type is None:
                    break
                elif attribute_type not in self.Attributes:
                    continue
                elif attribute_data is not None:
                    self.Attributes[attribute_type].append(attribute_data)
        finally:
            if self._stream is not None:
                self._stream.close()
