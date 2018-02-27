# -*- coding: UTF-8 -*-
# mft.py
# Noah Rubin
# 02/21/2017

from io import BytesIO
from construct import Container, Construct
import logging
Logger = logging.getLogger(__name__)

import src.structures.mft as mftstructs
from src.utils.time import WindowsTime
from src.utils.item import BaseItem, Field

class MFTAttributes(BaseItem):
    '''
    Represents resident attributes of an MFT entry
    '''
    ATTRIBUTE_LIST          = Field(1)
    FILE_NAME               = Field(2)
    OBJECT_ID               = Field(3)
    SECURITY_DESCRIPTOR     = Field(4)
    STANDARD_INFORMATION    = Field(5)
    VOLUME_NAME             = Field(6)
    VOLUME_INFORMATION      = Field(7)

class MFTEntry(BaseItem):
    '''
    Class for parsing Windows $MFT file entries
    '''
    header      = Field(1)
    attributes  = Field(2)

    def __init__(self, raw_entry, load=True):
        super(MFTEntry, self).__init__()
        self.header = None
        self.attributes = MFTAttributes()
        for key in self.attributes.iterkeys:
            self.attributes[key] = list()
        self._stream = None
        self.raw_entry = raw_entry
        if load:
            self.parse()
    def _transform_value(self, value):
        '''
        '''
        if issubclass(type(value), (Container, Construct)):
            return { \
                key : self._transform_value(val) \
                for key,val in value.items() \
                if not key.startswith('Raw') \
            }
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
    def parse_standard_information(self, attribute_header, original_position, stream=None):
        '''
        '''
        if stream is None:
            stream = self._stream
        stream.seek(original_position + attribute_header.get('Form').get('ValueOffset'))
        try:
            standard_information = mftstructs.MFTStandardInformationAttribute.parse_stream(stream)
            for field in standard_information:
                if field.startswith('Raw') and field.endswith('Time'):
                    standard_information[field.replace('Raw', '')] = WindowsTime(standard_information[field]).parse()
            return self._transform_value(standard_information)
        finally:
            stream.seek(original_position)
    def parse_object_id(self, attribute_header, original_position, stream=None):
        '''
        '''
        if stream is None:
            stream = self._stream
        stream.seek(original_position + attribute_header.get('Form').get('ValueOffset'))
        try:
            object_id = mftstructs.MFTObjectID.parse_stream(stream)
            return self._transform_value(object_id)
        finally:
            stream.seek(original_position)
    def parse_file_name(self, attribute_header, original_position, stream=None):
        '''
        '''
        if stream is None:
            stream = self._stream
        stream.seek(original_position + attribute_header.get('Form').get('ValueOffset'))
        try:
            file_name = mftstructs.MFTFileNameAttribute.parse_stream(stream)
            for field in file_name:
                if field.startswith('Raw') and field.endswith('Time'):
                    file_name[field.replace('Raw', '')] = WindowsTime(file_name[field]).parse()
            file_name.FileName = stream.read(file_name.FileNameLength * 2).decode('UTF16')
            return self._transform_value(file_name)
        finally:
            stream.seek(original_position)
    def parse_attribute_list(self, attribute_header, original_position, stream=None):
        '''
        '''
        if stream is None:
            stream = self._stream
        stream.seek(original_position + attribute_header.get('Form').get('ValueOffset'))
        try:
            attributes = MFTAttributes()
            while self.tell(stream=stream) < attribute_header.get('Form').get('ValueLength'):
                AL_original_position = self.tell(stream=stream)
                attribute_list_entry = mftstructs.MFTAttributeListEntry.parse_stream(stream)
                stream.seek(AL_original_position + attribute_list_entry.AttributeNameOffset)
                attribute_list_entry.AttributeName = stream.read(attribute_list_entry.AttributeNameLength * 2).decode('UTF16')
                if attributes[attribute_list_entry.AttributeTypeCode] is None:
                    attributes[attribute_list_entry.AttributeTypeCode] = list()
                attributes[attribute_list_entry.AttributeTypeCode].append(self._transform_value(attribute_list_entry))
            return self._transform_value(attributes)
        finally:
            stream.seek(original_position)
    def get_attribute_parser(self, type_code):
        '''
        '''
        return getattr(self, 'parse_' + type_code.lower(), None)
    def parse_attribute_header(self, stream=None):
        '''
        '''
        if stream is None:
            stream = self._stream
        return self._transform_value(mftstructs.MFTAttributeHeader.parse_stream(stream))
    def parse_next_attribute(self, stream=None, header=None):
        '''
        '''
        if stream is None:
            stream = self._stream
        if header is None:
            header = self.header
        original_position = self.tell(stream=stream)
        attribute_header = self.parse_attribute_header(stream=stream)
        try:
            attribute_parser = self.get_attribute_parser(attribute_header.TypeCode)
            if attribute_header.TypeCode == 'END_OF_ATTRIBUTES' or \
                attribute_parser is None or \
                attribute_header.FormCode != 0:
                return attribute_header.TypeCode, None
            if attribute_header.NameLength > 0:
                stream.seek(original_position + attribute_header.NameOffset)
                attribute_header.Name = stream.read(attribute_header.NameLength * 2.).decode('UTF16')
            else:
                attribute_header.Name = None
            attribute_body = attribute_parser(attribute_header, original_position, stream=stream)
            return ( \
                attribute_header.get('TypeCode'), \
                { \
                    'Header': self._transform_value(attribute_header), \
                    'Body': self._transform_value(attribute_body) \
                }\
            )
        finally:
            stream.seek(original_position + attribute_header.RecordLength)
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
        return self._transform_value(header)
    def parse(self):
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
            self.header = self.parse_header()
            self._stream.seek(header.get('FirstAttributeOffset'))
            while self.tell() < self.header.get('UsedSize'):
                attribute_type, attribute_data = self.parse_next_attribute()
                if attribute_type is None:
                    break
                elif attribute_data is not None:
                    self.attributes[attribute_type].append(attribute_data)
        finally:
            if self._stream is not None:
                self._stream.close()
