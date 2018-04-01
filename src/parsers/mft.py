## -*- coding: UTF-8 -*-
## mft.py
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

import logging
Logger = logging.getLogger(__name__)
from os import path
from io import BytesIO
import inspect
from construct.lib import Container
import hashlib
from datetime import datetime
from dateutil.tz import tzlocal, tzutc

import src.structures.mft as mftstructs
from src.utils.time import WindowsTime

class MFTEntry(Container):
    '''
    Class for parsing Windows $MFT file entries
    '''

    def __init__(self, raw_entry, load=False):
        super(MFTEntry, self).__init__()
        for attribute in [\
            'standard_information',
            'attribute_list',
            'file_name',
            'object_id',  
            'security_descriptor',
            'volume_name',
            'volume_information',
            'data',
            'index_root',
            'index_allocation',
            'bitmap',
            'logged_utility_stream'\
        ]:
            self[attribute] = list()
        self._raw_entry = raw_entry
        self._stream = None
        if load:
            self.parse()
    def _clean_transform(self, value, serialize=False):
        '''
        Args:
            value: Any  => value to be converted
        Returns:
            Any
            Raw value if it is not of type Container, else recursively removes
            any key beginning with 'Raw'
        Preconditions:
            N/A
        '''
        if issubclass(type(value), Container):
            cleaned_value = Container(value)
            if '_raw_entry' in cleaned_value:
                del cleaned_value['_filepath']
            if '_stream' in cleaned_value:
                del cleaned_value['_stream']
            for key in cleaned_value:
                if key.startswith('Raw') or key.startswith('_'):
                    del cleaned_value[key]
                else:
                    cleaned_value[key] = self._clean_transform(cleaned_value[key], serialize)
            return cleaned_value
        elif isinstance(value, list):
            return list(map(lambda entry: self._clean_transform(entry, serialize), value))
        elif isinstance(value, datetime) and serialize:
            return value.strftime('%Y-%m-%d %H:%M:%S.%f%z')
        elif isinstance(value, (bytes, bytearray)):
            return value.decode('UTF8', errors='replace')
        else:
            return value
    def _prepare_kwargs(self, structure_parser, **kwargs):
        '''
        Args:
            structure_parser: Callable  => function to prepare kwargs for
            kwargs: Dict<String, Any>   => kwargs to prepare
        Returns:
            Dict<String, Any>
            Same set of keyword arguments but with values filled in
            for kwargs supplied as None with attribute values from self
            NOTE:
                This function uses the inspect module to get the keyword
                arguments for the given structure parser.  I know this is weird
                and non-standard OOP, and is subject to change int the future,
                but it works as a nice abstraction on the various structure parsers 
                for now.
        Preconditions:
            structure_parser is callable that takes 0 or more keyword arguments
            Only keyword arguments supplied to function
        '''
        argspec = inspect.getargspec(structure_parser)
        kwargs_keys = argspec.args[(len(argspec.args) - len(argspec.defaults))+1:]
        prepared_kwargs = dict()
        for key in kwargs_keys:
            if key in kwargs:
                if kwargs[key] is None:
                    prepared_kwargs[key] = getattr(\
                        self, 
                        key if key != 'stream' else '_stream', 
                        None\
                    )
                    if prepared_kwargs[key] is None:
                        raise Exception('Attribute %s was no provided and has not been parsed'%key)
                else:
                    prepared_kwargs[key] = kwargs[key]
            else:
                prepared_kwargs[key] = getattr(\
                    self, 
                    key if key != 'stream' else '_stream', 
                    None\
                )
        return prepared_kwargs
    def _parse_index_root(self, original_position, attribute_header, stream=None):
        '''
        Args:
            original_position: Integer                  => position in stream before parsing this structure
            attribute_header: Container<String, Any>    => header of this attribute
            stream: TextIOWrapper|BytesIO               => stream to parse structure from
        Returns:
            Container<String, Any>
            MFT entry index root attribute (see: src.structures.index)
        Preconditions:
            original_position is of type Integer                (assumed True)
            attribute_header is of type Container<String, Any>  (assumed True)
            stream is of type TextIOWrapper or BytesIO          (assumed True)
        '''
        index_root = Container()
        index_root.root_header = mftstructs.MFTIndexRootHeader.parse_stream(stream)
        node_header_position = stream.tell()
        index_root.node_header = mftstructs.MFTIndexNodeHeader.parse_stream(stream)
        index_root.entries = list()
        stream.seek(node_header_position + index_root.node_header.IndexValuesOffset)
        index_entry_start_position = stream.tell()
        index_entry_size = index_root.node_header.IndexNodeSize - mftstructs.MFTIndexNodeHeader.sizeof()
        while (stream.tell() - index_entry_start_position) < index_entry_size:
            try:
                index_entry_position = stream.tell()
                index_entry = mftstructs.MFTIndexEntry.parse_stream(stream)
                seek_length = mftstructs.MFTIndexEntry.sizeof() + \
                    index_entry.IndexValueSize + \
                    index_entry.IndexKeyDataSize
                if index_entry.Flags.HAS_SUB_NODE:
                    seek_length += 8
                index_root.entries.append(index_entry)
                if index_entry.Flags.IS_LAST:
                    break
                else:
                    stream.seek(index_entry_position + seek_length)
            except:
                break
        return self._clean_transform(index_root)
    def _parse_data(self, original_position, attribute_header, stream=None):
        '''
        Args:
            original_position: Integer                  => position in stream before parsing this structure
            attribute_header: Container<String, Any>    => header of this attribute
            stream: TextIOWrapper|BytesIO               => stream to parse structure from
        Returns:
            Container<String, Any>
            MFT entry resident data attribute
        Preconditions:
            original_position is of type Integer                (assumed True)
            attribute_header is of type Container<String, Any>  (assumed True)
            stream is of type TextIOWrapper or BytesIO          (assumed True)
        '''
        data = Container(content=stream.read(attribute_header.RecordLength))
        data.sha2hash = hashlib.sha256(data.content).hexdigest()
        return data
    def _parse_volume_information(self, original_position, attribute_header, stream=None):
        '''
        Args:
            original_position: Integer                  => position in stream before parsing this structure
            attribute_header: Container<String, Any>    => header of this attribute
            stream: TextIOWrapper|BytesIO               => stream to parse structure from
        Returns:
            Container<String, Any>
            MFT entry volume information attribute (see: src.structures.volume_information)
        Preconditions:
            original_position is of type Integer                (assumed True)
            attribute_header is of type Container<String, Any>  (assumed True)
            stream is of type TextIOWrapper or BytesIO          (assumed True)
        '''
        return self._clean_transform(mftstructs.MFTVolumeInformation.parse_stream(stream))
    def _parse_volume_name(self, original_position, attribute_header, stream=None):
        '''
        Args:
            original_position: Integer                  => position in stream before parsing this structure
            attribute_header: Container<String, Any>    => header of this attribute
            stream: TextIOWrapper|BytesIO               => stream to parse structure from
        Returns:
            String
            MFT entry volume name attribute (see: src.structures.volume_name)
        Preconditions:
            original_position is of type Integer                (assumed True)
            attribute_header is of type Container<String, Any>  (assumed True)
            stream is of type TextIOWrapper or BytesIO          (assumed True)
        '''
        return stream.read(attribute_header.Form.ValueLength).decode('UTF16')
    def _parse_access_control_list(self, stream=None):
        '''
        Args:
            original_position: Integer                  => position in stream before parsing this structure
            attribute_header: Container<String, Any>    => header of this attribute
            stream: TextIOWrapper|BytesIO               => stream to parse structure from
        Returns:
            Container<String, Container<String, Any>>
            MFT entry access control list attribute (see: src.structures.general.access_control_list)
        Preconditions:
            original_position is of type Integer                (assumed True)
            attribute_header is of type Container<String, Any>  (assumed True)
            stream is of type TextIOWrapper or BytesIO          (assumed True)
        '''
        try:
            acl = Container()
            acl.header = mftstructs.NTFSACLHeader.parse_stream(stream)
            acl_position = stream.tell()
            acl_size = acl.header.AclSize - mftstructs.NTFSACLHeader.sizeof()
            acl.body = list()
            while (stream.tell() - acl_position) < acl_size:
                ace_position = stream.tell()
                try:
                    ace = Container()
                    ace.header = mftstructs.NTFSACEHeader.parse_stream(stream)
                    ace.body = mftstructs.NTFSACEAcessMask.parse_stream(stream)
                    acl.body.append(ace)
                    stream.seek(ace_position + ace.header.AceSize)
                except:
                    break
            return self._clean_transform(acl)
        except:
            return None
    def _parse_security_descriptor(self, original_position, attribute_header, stream=None):
        '''
        Args:
            original_position: Integer                  => position in stream before parsing this structure
            attribute_header: Container<String, Any>    => header of this attribute
            stream: TextIOWrapper|BytesIO               => stream to parse structure from
        Returns:
            Container<String, Any>
            MFT entry security descriptor attribute (see: src.structures.security_descriptor)
        Preconditions:
            original_position is of type Integer                (assumed True)
            attribute_header is of type Container<String, Any>  (assumed True)
            stream is of type TextIOWrapper or BytesIO          (assumed True)
        '''
        header_position = stream.tell()
        security_descriptor = Container(\
            header=None,
            body=Container()\
        )
        security_descriptor.header = mftstructs.MFTSecurityDescriptorHeader.parse_stream(stream)
        if security_descriptor.header.Control.SE_SELF_RELATIVE:
            stream.seek(header_position + security_descriptor.header.OwnerSIDOffset)
            security_descriptor.body.OwnerSID = mftstructs.NTFSSID.parse_stream(stream)
            stream.seek(header_position + security_descriptor.header.GroupSIDOffset)
            security_descriptor.body.GroupSID = mftstructs.NTFSSID.parse_stream(stream)
            if security_descriptor.header.Control.SE_SACL_PRESENT:
                stream.seek(header_position + security_descriptor.header.SACLOffset)
                security_descriptor.body.SACL = self._parse_access_control_list(stream=stream)
            else:
                security_descriptor.body.SACL = None
            if security_descriptor.header.Control.SE_DACL_PRESENT:
                stream.seek(header_position + security_descriptor.header.DACLOffset)
                security_descriptor.body.DACL = self._parse_access_control_list(stream=stream)
            else:
                security_descriptor.body.DACL = None
        else:
            security_descriptor.body.OwnerSID = None
            security_descriptor.body.GroupSID = None
            security_descriptor.body.SACL = None
            security_descriptor.body.DACL = None
        return self._clean_transform(security_descriptor)
    def _parse_object_id(self, original_position, attribute_header, stream=None):
        '''
        Args:
            original_position: Integer                  => position in stream before parsing this structure
            attribute_header: Container<String, Any>    => header of this attribute
            stream: TextIOWrapper|BytesIO               => stream to parse structure from
        Returns:
            Container<String, Any>
            MFT entry object id attribute (see: src.structures.object_id)
        Preconditions:
            original_position is of type Integer                (assumed True)
            attribute_header is of type Container<String, Any>  (assumed True)
            stream is of type TextIOWrapper or BytesIO          (assumed True)
        '''
        object_id = mftstructs.MFTObjectID.parse_stream(stream)
        return self._clean_transform(object_id)
    def _parse_file_name(self, original_position, attribute_header, stream=None):
        '''
        Args:
            original_position: Integer                  => position in stream before parsing this structure
            attribute_header: Container<String, Any>    => header of this attribute
            stream: TextIOWrapper|BytesIO               => stream to parse structure from
        Returns:
            Container<String, Any>
            MFT entry file name attribute (see: src.structures.file_name)
        Preconditions:
            original_position is of type Integer                (assumed True)
            attribute_header is of type Container<String, Any>  (assumed True)
            stream is of type TextIOWrapper or BytesIO          (assumed True)
        '''
        file_name = mftstructs.MFTFileNameAttribute.parse_stream(stream)
        for field in file_name:
            if field.startswith('Raw') and field.endswith('Time'):
                file_name[field.replace('Raw', '')] = WindowsTime(file_name[field]).parse()
        file_name.FileName = stream.read(file_name.FileNameLength * 2).decode('UTF16')
        return self._clean_transform(file_name)
    def _parse_attribute_list(self, original_position, attribute_header, stream=None):
        '''
        Args:
            original_position: Integer                  => position in stream before parsing this structure
            attribute_header: Container<String, Any>    => header of this attribute
            stream: TextIOWrapper|BytesIO               => stream to parse structure from
        Returns:
            Container<String, Any>
            MFT entry attribute list attribute (see: src.structures.attribute_list)
        Preconditions:
            original_position is of type Integer                (assumed True)
            attribute_header is of type Container<String, Any>  (assumed True)
            stream is of type TextIOWrapper or BytesIO          (assumed True)
        '''
        attributes = Container()
        while stream.tell() < attribute_header.Form.ValueLength:
            AL_original_position = stream.tell()
            try:
                attribute_list_entry = mftstructs.MFTAttributeListEntry.parse_stream(stream)
                if attribute_list_entry.AttributeTypeCode == 'END_OF_ATTRIBUTES':
                    break
                stream.seek(AL_original_position + attribute_list_entry.AttributeNameOffset)
                attribute_list_entry.AttributeName = stream.read(attribute_list_entry.AttributeNameLength * 2).decode('UTF16')
            except:
                break
            else:
                if attribute_list_entry.AttributeTypeCode.lower() not in attributes:
                    attributes[attribute_list_entry.AttributeTypeCode.lower()] = list()
                attributes[attribute_list_entry.AttributeTypeCode.lower()].append(attribute_list_entry)
                stream.seek(AL_original_position + attribute_list_entry.RecordLength)
        return self._clean_transform(attributes)
    def _parse_standard_information(self, original_position, attribute_header, stream=None):
        '''
        Args:
            original_position: Integer                  => position in stream before parsing this structure
            attribute_header: Container<String, Any>    => header of this attribute
            stream: TextIOWrapper|BytesIO               => stream to parse structure from
        Returns:
            Container<String, Any>
            MFT entry standard information attribute (see: src.structures.standard_information)
        Preconditions:
            original_position is of type Integer                (assumed True)
            attribute_header is of type Container<String, Any>  (assumed True)
            stream is of type TextIOWrapper or BytesIO          (assumed True)
        '''
        standard_information = mftstructs.MFTStandardInformationAttribute.parse_stream(stream)
        for field in standard_information:
            if field.startswith('Raw') and field.endswith('Time'):
                standard_information[field.replace('Raw', '')] = WindowsTime(standard_information[field]).parse()
        return self._clean_transform(standard_information)
    def _parse_attribute_header(self, original_position, stream=None):
        '''
        Args:
            original_position: Integer      => position in stream before parsing this structure
            stream: TextIOWrapper|BytesIO   => stream to parse structure from
        Returns:
            Container<String, Any>
            MFT entry attribute header information (see: src.structures.headers)
        Preconditions:
            original_position is of type Integer        (assumed True)
            stream is of type TextIOWrapper or BytesIO  (assumed True)
        '''
        attribute_header = mftstructs.MFTAttributeHeader.parse_stream(stream)
        if attribute_header.NameLength > 0:
            try:
                stream.seek(original_position + attribute_header.NameOffset)
                attribute_header.Name = stream.read(attribute_header.NameLength * 2).decode('UTF16')
            except Exception as e:
                Logger.error('Failed to get name of attribute from header (%s)'%str(e))
                attribute_header.Name = None
        else:
            attribute_header.Name = None
        return self._clean_transform(attribute_header)
    def _parse_next_attribute(self, original_position, stream=None, header=None):
        '''
        Args:
            original_position: Integer      => position in stream before parsing this structure
            stream: TextIOWrapper|BytesIO   => stream to parse structure from
            header: Container<String, Any>  => header of this MFT entry
        Returns:
            Tuple<String, Container<String, Any>>
            Next attribute in MFT entry
        Preconditions:
            original_position is of type Integer        (assumed True)
            stream is of type TextIOWrapper or BytesIO  (assumed True)
            header is of type Container<String, Any>    (assumed True)
        '''
        type_code = mftstructs.MFTAttributeTypeCode.parse_stream(stream)
        if type_code == 'END_OF_ATTRIBUTES':
            return None, None
        stream.seek(original_position)
        next_attribute = Container()
        next_attribute.header = self.parse_structure('attribute_header')
        try:
            if next_attribute.header.FormCode != 0:
                return next_attribute.header.TypeCode, self._clean_transform(next_attribute)
            stream.seek(original_position + next_attribute.header.Form.ValueOffset)
            next_attribute.body = self.parse_structure(next_attribute.header.TypeCode.lower(), next_attribute.header)
            return next_attribute.header.TypeCode, self._clean_transform(next_attribute)
        except:
            return next_attribute.header.TypeCode, None
        finally:
            stream.seek(original_position + next_attribute.header.RecordLength)
    def _parse_entry_header(self, original_position, stream=None):
        '''
        Args:
            original_position: Integer      => position in stream before parsing this structure
            stream: TextIOWrapper|BytesIO   => stream to parse structure from
        Returns:
            Container<String, Any>
            MFT entry attribute header information (see: src.structures.headers)
        Preconditions:
            original_position is of type Integer        (assumed True)
            stream is of type TextIOWrapper or BytesIO  (assumed True)
        '''
        header = mftstructs.MFTEntryHeader.parse_stream(stream)
        if header.MultiSectorHeader.RawSignature == 0x454c4946:
            header.MultiSectorHeader.Signature = 'FILE'
        elif header.MultiSectorHeader.RawSignature == 0x44414142:
            header.MultiSectorHeader.Signature = 'BAAD'
        else:
            header.MultiSectorHeader.Signature = 'CRPT'
        return self._clean_transform(header)
    def get_stream(self, persist=False):
        '''
        Args:
            persist: Boolean    => whether to persist stream as attribute on self
        Returns:
            TextIOWrapper|BytesIO
            Stream of prefetch file at self._filepath
        Preconditions:
            persist is of type Boolean  (assumed True)
        '''
        stream = BytesIO(self._raw_entry)
        if persist:
            self._stream = stream
        return stream
    def serialize(self):
        '''
        Args:
            N/A
        Returns:
            Container<String, Any>
            Serializable representation of self in Container object
        Preconditions:
            N/A
        '''
        return self._clean_transform(self, serialize=True)
    def parse_structure(self, structure, *args, stream=None, **kwargs):
        '''
        Args:
            structure: String               => structure to parse
            stream: TextIOWrapper|BytesIO   => stream to parse structure from
        Returns:
            Container
            Parsed structure if parsed successfully, None otherwise
        Preconditions:
            structure is of type String
            stream is of type TextIOWrapper|BytesIO (assumed True)
        '''
        if stream is None:
            stream = self._stream
        structure_parser = getattr(self, '_parse_' + structure, None)
        if structure_parser is None:
            Logger.error('Structure %s is not a known structure'%structure)
            return None
        try:
            prepared_kwargs = self._prepare_kwargs(structure_parser, **kwargs)
        except Exception as e:
            Logger.error('Failed to parse provided kwargs for structure %s (%s)'%(structure, str(e)))
            return None
        original_position = stream.tell()
        try:
            return structure_parser(original_position, *args, stream=stream, **prepared_kwargs)
        except Exception as e:
            Logger.error('Failed to parse %s structure (%s)'%(structure, str(e)))
            return None
    def parse(self):
        '''
        Args:
            N/A
        Procedure:
            Attempt to parse the supplied MFT entry, extracting
            header information and resident attribute data
        Preconditions:
            self._raw_entry is byte string of length 1024
        '''
        try:
            self.get_stream(persist=True)
            self.header = self.parse_structure('entry_header')
            self._stream.seek(self.header.FirstAttributeOffset)
            while self._stream.tell() < self.header.UsedSize:
                attribute_type, attribute_data = self.parse_structure('next_attribute')
                if attribute_type is None:
                    break
                elif attribute_type.lower() not in self:
                    continue
                elif attribute_data is not None:
                    self[attribute_type.lower()].append(attribute_data)
            return self
        finally:
            if self._stream is not None:
                self._stream.close()
                self._stream = None

class MFT(Container):
    '''
    Class for parsing Windows $MFT file
    '''
    def __init__(self, filepath):
        super(MFT, self).__init__()
        self._filepath = filepath
        self._record_size = 1024
    @property
    def entries(self):
        '''
        @entries.getter
        '''
        if self._filepath is None:
            return list()
        mft_file = open(self._filepath, 'rb')
        try:
            mft_entry = mft_file.read(self._record_size)
            while mft_entry != b'':
                yield mft_entry
                mft_entry = mft_file.read(self._record_size)
        finally:
            mft_file.close()
            mft_file = None
    @entries.setter
    def entries(self, value):
        '''
        @entries.setter
        Preconditions:
            N/A
        '''
        raise AttributeError('entries is a dynamic attribute and cannot be set')
    def get_metadata(self, simple_hash=True):
        '''
        Args:
            simple_hash: Boolean    => whether to only collect SHA256 hash or
                                       MD5 and SHA1 as well
        Returns:
            Container<String, Any>
            Container of metadata about this $MFT file:
                file_name: $MFT file name
                file_path: full path on local system
                file_size: size of file on local system
                md5hash: MD5 hash of $MFT file
                sha1hash: SHA1 hash of $MFT file
                sha2hash: SHA256 hash of $MFT file
                modify_time: last modification time of $MFT file on local system
                access_time: last access time of $MFT file on local system
                create_time: create time of $MFT file on local system
        Preconditions:
            simple_hash is of type Boolean
        '''
        assert isinstance(simple_hash, bool), 'Simple_hash is of type Boolean'
        return Container(\
            file_name=path.basename(self._filepath),
            file_path=path.abspath(self._filepath),
            file_size=path.getsize(self._filepath),
            md5hash=self._hash_file('md5') if not simple_hash else None,
            sha1hash=self._hash_file('sha1') if not simple_hash else None,
            sha2hash=self._hash_file('sha256'),
            modify_time=datetime.fromtimestamp(path.getmtime(self._filepath), tzlocal()).astimezone(tzutc()),
            access_time=datetime.fromtimestamp(path.getatime(self._filepath), tzlocal()).astimezone(tzutc()),
            create_time=datetime.fromtimestamp(path.getctime(self._filepath), tzlocal()).astimezone(tzutc())\
        )
    def parse(self):
        '''
        Args:
            N/A
        Returns:
            Gen<MFTEntry>
            Iterator over the mft entries in this $MFT
        Preconditions:
            N/A
        '''
        for entry in self.entries:
            yield MFTEntry(entry)
