## -*- coding: UTF-8 -*-
## tasks.py
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
from hashlib import md5
from itertools import chain as itertools_chain
from datetime import datetime, timezone, timedelta
from json import dumps
from construct.lib import Container

import src.database.models as db
from src.parsers.mft import MFTEntry

class BaseParseTask(object):
    '''
    Base class for parsing tasks
    '''

    def __init__(self, source):
        self._source = source
        self._resultset = None
    @property
    def source(self):
        '''
        @source.getter
        '''
        return self._source
    @source.setter
    def source(self, value):
        '''
        @source.setter
        Preconditions:
            N/A
        '''
        raise AttributeError('source attribute must be set in the constructor')
    @property
    def resultset(self):
        '''
        @resultset.getter
        '''
        return self._resultset
    @resultset.setter
    def resultset(self, value):
        '''
        @_resultset.setter
        Preconditions:
            value if of type List<Any>
        '''
        assert isinstance(value, list)
        self._resultset = value
    def extract_resultset(self, worker):
        '''
        Args:
            worker: BaseQueueWorker => worker that called this task
        Procedure:
            Convert source into result set
        Preconditions:
            worker is subclass of BaseQueueWorker
        '''
        raise NotImplementedError('extract_resultset method not implemented for %s'%type(self).__name__)
    def process_resultset(self, worker):
        '''
        Args:
            worker: BaseQueueWorker => worker that called this task
        Returns:
            List<Any>
            Process result set created in extract_resultset and return results of processing
        Preconditions:
            worker is subclass of BaseQueueWorker
        '''
        raise NotImplementedError('process_resultset method not implemented for %s'%type(self).__name__)
    def __call__(self, worker):
        '''
        Args:
            worker: BaseQueueWorker => worker that called this task
        Returns:
            Any
            Result of running this task
        Preconditions:
            worker is subclass of BaseQueueWorker
        '''
        self.extract_resultset(worker)
        return self.process_resultset(worker)

class BaseParseFileOutputTask(BaseParseTask):
    '''
    Base class for tasks that write output to file
    '''
    NULL = ''

    def __init__(self, source, nodeidx, recordidx, **context):
        super(BaseParseFileOutputTask, self).__init__(source)
        self._nodeidx = nodeidx
        self._recordidx = recordidx
        if 'target' not in context:
            raise KeyError('target was not provided as a keyword argument')
        self._context = Container(**context)
    @property
    def nodeidx(self):
        '''
        @nodeidx.getter
        '''
        return self._nodeidx
    @nodeidx.setter
    def nodeidx(self, value):
        '''
        @nodeidx.setter
        Preconditions:
            N/A
        '''
        raise AttributeError('nodeidx attribute must be set in the constructor')
    @property
    def recordidx(self):
        '''
        @recordidx.getter
        '''
        return self._recordidx
    @recordidx.setter
    def recordidx(self, value):
        '''
        @recordidx.setter
        Preconditions:
            N/A
        '''
        raise AttributeError('recordidx attribute must be set in the constructor')
    @property
    def context(self):
        '''
        @context.getter
        '''
        return self._context
    @context.setter
    def context(self, value):
        '''
        @context.setter
        Preconditions:
            value is of type Container
        '''
        if self._context is None:
            assert isinstance(value, Container)
            self._context = value
        else:
            raise AttributeError('context attribute has already been set')
    def process_resultset(self, worker):
        '''
        @BaseParseTask.process_resultset
        '''
        target_file = path.join(self.context.target, '%s_tmp_amft.out'%worker.name)
        try:
            if len(self.result_set) > 0:
                successful_results = 0
                with open(target_file, 'a') as f:
                    for result in self.result_set:
                        try:
                            if 'sep' in self.context:
                                f.write(self.context.sep.join(result) + '\n')
                            else:
                                f.write(result + '\n')
                            successful_results += 1
                        except Exception as e:
                            Logger.error('Failed to write result for MFT entry %d from node %d (%s)'%(self.recordidx, self.nodeidx, str(e)))
        except Exception as e:
            Logger.error('Failed to write results for MFT entry %d from node %d (%s)'%(self.recordidx, self.nodeidx, str(e)))
        else:
            Logger.info('Successfully wrote %d result(s) for MFT entry %d from node %d'%(successful_results, self.recordidx, self.nodeidx))
        finally:
            return [True]

class FileNameResolutionMixin(object):
    '''
    Mixin class for working with file_name attributes
    '''
    @classmethod
    def _get_longest_filename(cls, file_name_set, default=None):
        '''
        Args:
            file_name_set: List<Container<String, Any>> => list of file_name attributes
            default: Any                                => default value to return if not file_name found
        Returns:
            String
            Longest file name if found, default otherwise
        Preconditions:
            class extending this mixin has (static) class attribute NULL
            file_name_set is of type List<Container<String, Any>>   (assumed True)
        '''
        if default is None:
            default = cls.NULL
        if len(file_name_set) == 0:
            return default
        file_name = None
        for attribute in file_name_set:
            if file_name is None or \
                (hasattr(attribute.body, 'FileName') and \
                len(attribute.body.FileName) > len(file_name)):
                file_name = attribute.body.FileName
        return file_name if file_name is not None else default


class ParseCSVTask(BaseParseFileOutputTask, FileNameResolutionMixin):
    '''
    Class for parsing single MFT record to CSV format
    '''
    def extract_resultset(self, worker):
        '''
        @BaseParseTask.extract_resultset
        '''
        self.result_set = list()
        # FIELDS: RecordNumber, Signature, SequenceNumber, LogFileSequenceNumber, BaseFileRecordSegmentNumber, BaseFileRecordSequenceNumber, 
        #         Active, HasIndex, UsedSize, TotalSize, ReferenceCount, FirstAttributeId, FileName,
        #         StandardInformationModifyDate, StandardInformationAccessDate, StandardInformationCreateDate, StandardInformationEntryDate,
        #         FileNameModifyDate, FileNameAccessDate, FileNameCreateDate, FileNameEntryDate,
        #         StandardInformationCount, AttributeListCount, FileNameCount, ObjectIDCount, SecurityDescriptorCount, VolumeNameCount,
        #         VolumeInformationCount, DataCount, IndexRootCount, IndexAllocationCount
        if self.context.info_type == 'summary':
            try:
                mft_entry = MFTEntry(self.source)
                mft_entry.parse()
            except Exception as e:
                Logger.error('Failed to parse MFT entry %d for node %d (%s)'%(self.recordidx, self.nodeidx, str(e)))
            else:
                try:
                    result = [\
                        str(self.nodeidx),
                        str(self.recordidx),
                        str(mft_entry.header.MFTRecordNumber),
                        str(mft_entry.header.MultiSectorHeader.Signature),
                        str(mft_entry.header.SequenceNumber),
                        str(mft_entry.header.LogFileSequenceNumber),
                        str(mft_entry.header.BaseFileRecordSegment.SegmentNumber),
                        str(mft_entry.header.BaseFileRecordSegment.SequenceNumber),
                        str(mft_entry.header.Flags.ACTIVE),
                        str(mft_entry.header.Flags.HAS_INDEX),
                        str(mft_entry.header.UsedSize),
                        str(mft_entry.header.TotalSize),
                        str(mft_entry.header.ReferenceCount),
                        str(mft_entry.header.FirstAttributeId),
                        self._get_longest_filename(mft_entry.file_name)\
                    ]
                    if len(mft_entry.standard_information) > 0:
                        result.append(mft_entry.standard_information[0].body.LastModifiedTime.strftime('%Y-%m-%d %H:%M:%S.%f%z'))
                        result.append(mft_entry.standard_information[0].body.LastAccessTime.strftime('%Y-%m-%d %H:%M:%S.%f%z'))
                        result.append(mft_entry.standard_information[0].body.CreateTime.strftime('%Y-%m-%d %H:%M:%S.%f%z'))
                        result.append(mft_entry.standard_information[0].body.EntryModifiedTime.strftime('%Y-%m-%d %H:%M:%S.%f%z'))
                    else:
                        result.append(self.NULL)
                        result.append(self.NULL)
                        result.append(self.NULL)
                        result.append(self.NULL)
                    if len(mft_entry.file_name) > 0:
                        result.append(mft_entry.file_name[0].body.LastModifiedTime.strftime('%Y-%m-%d %H:%M:%S.%f%z'))
                        result.append(mft_entry.file_name[0].body.LastAccessTime.strftime('%Y-%m-%d %H:%M:%S.%f%z'))
                        result.append(mft_entry.file_name[0].body.CreateTime.strftime('%Y-%m-%d %H:%M:%S.%f%z'))
                        result.append(mft_entry.file_name[0].body.EntryModifiedTime.strftime('%Y-%m-%d %H:%M:%S.%f%z'))
                    else:
                        result.append(self.NULL)
                        result.append(self.NULL)
                        result.append(self.NULL)
                        result.append(self.NULL)
                    for key in mft_entry:
                        if not key.startswith('_'):
                            result.append(str(len(mft_entry[key])))
                    self.result_set.append(result)
                except Exception as e:
                    Logger.error('Failed to create CSV output record of MFT entry %d for node %d (%s)'%(self.recordidx, self.nodeidx, str(e)))

class ParseBODYTask(BaseParseFileOutputTask, FileNameResolutionMixin):
    '''
    Task class for parsing single MFT entry to BODY format
    '''
    @staticmethod
    def to_timestamp(dt):
        '''
        Args:
            dt: DateTime<UTC>   => datetime object to convert
        Returns:
            Float
            Datetime object converted to Unix epoch time
        Preconditions:
            dt is timezone-aware timestamp with timezone UTC
        '''
        return (dt - datetime(1970,1,1, tzinfo=timezone.utc)) / timedelta(seconds=1)

    def extract_resultset(self, worker):
        '''
        @BaseParseTask.extract_resultset
        '''
        self.result_set = list()
        # FIELDS: nodeidx|recordidx|MD5|name|inode|mode_as_string|UID|GID|size|atime|mtime|ctime|crtime
        try:
            mft_entry = MFTEntry(self.source)
            mft_entry.parse()
        except Exception as e:
            Logger.error('Failed to parse MFT entry %d for node %d (%s)'%(self.recordidx, self.nodeidx, str(e)))
        else:
            try:
                if len(mft_entry.standard_information) > 0 or len(mft_entry.file_name) > 0:
                    file_name = self._get_longest_filename(mft_entry.file_name)
                    file_size = str(mft_entry.file_name[0].body.FileSize if len(mft_entry.file_name) > 0 else self.NULL)
                    md5hash = md5(mft_entry._raw_entry).hexdigest()
                    for attribute in itertools_chain(mft_entry.standard_information, mft_entry.file_name):
                        try:
                            result = list()
                            result.append(str(self.nodeidx))
                            result.append(str(self.recordidx))
                            result.append(md5hash)
                            result.append(file_name)
                            result.append(self.NULL)
                            result.append(self.NULL)
                            result.append(self.NULL)
                            result.append('FN' if hasattr(attribute.body, 'ParentDirectory') else 'SI')
                            result.append(str(file_size))
                            result.append(str(self.to_timestamp(attribute.body.LastAccessTime)))
                            result.append(str(self.to_timestamp(attribute.body.LastModifiedTime)))
                            result.append(str(self.to_timestamp(attribute.body.EntryModifiedTime)))
                            result.append(str(self.to_timestamp(attribute.body.CreateTime)))
                            self.result_set.append(result)
                        except Exception as e:
                                Logger.error('Failed to create BODY output record of MFT entry %d for node %d (%s)'%(self.recordidx, self.nodeidx, str(e)))
            except Exception as e:
                    Logger.error('Failed to create BODY output records of MFT entry %d for node %d (%s)'%(self.recordidx, self.nodeidx, str(e)))

class ParseJSONTask(BaseParseFileOutputTask):
    '''
    Class for parsing single MFT entry to JSON format
    '''
    def extract_resultset(self, worker):
        '''
        @BaseParseTask.extract_resultset
        '''
        self.result_set = list()
        try:
            mft_entry = MFTEntry(self.source)
            result = dumps(mft_entry.parse().serialize(), sort_keys=True, indent=(2 if self.context.pretty else None))
        except Exception as e:
            Logger.error('Failed to parse MFT entry %d for node %d (%s)'%(self.recordidx, self.nodeidx, str(e)))
        else:
            try:
                self.result_set.append(result)
            except Exception as e:
                Logger.error('Failed to create JSON output records of MFT entry %d for node %d (%s)'%(self.recordidx, self.nodeidx, str(e)))

class ParseDBTaskStage2(BaseParseTask):
    '''
    Class to push MFT entry information to database
    '''
    @staticmethod
    def _prepare_attribute_header(attribute):
        '''
        Args:
            attribute: Container<String, Any>   => attribute to extract header from
        Returns:
            db.AttributeHeader
            attribute header object
        Preconditions:
            attribute is of type Container  (assumed True)
            attribute contains header field (assumed True)
        '''
        attribute_header = db.AttributeHeader().populate_fields(attribute.header)
        attribute_header.populate_fields(attribute.header.Flags)
        attribute_header.populate_fields(attribute.header.Form)
        return attribute_header

    def extract_resultset(self, worker):
        '''
        @BaseParseTask.extract_resultset
        '''
        self.result_set = list()
        for mft_entry in self.source:
            try:
                fileledger = mft_entry.fileledger
                base_file_record_segment = mft_entry.header.BaseFileRecordSegment
                del mft_entry.fileledger
                del mft_entry.header.BaseFileRecordSegment
                entry_header = db.EntryHeader().populate_fields(mft_entry.header)
                entry_header.populate_fields(mft_entry.header.MultiSectorHeader)
                entry_header.populate_fields(mft_entry.header.Flags)
                entry_header.meta_id = fileledger.id
            except Exception as e:
                Logger.error('Failed to get header information from %s (%s)'%(mft_entry._filepath, str(e)))
            else:
                for standard_information in mft_entry.standard_information:
                    try:
                        attribute_header = self._prepare_attribute_header(standard_information)
                        file_attribute_flags = standard_information.body.FileAttributeFlags
                        del standard_information.body.file_attribute_flags
                        standard_information = db.StandardInformation().populate_fields(standard_information.body)
                        file_attribute_flags = db.FileAttributeFlags().populate_fields(file_attribute_flags)
                        standard_information.file_attribute_flags = file_attribute_flags
                        attribute_header.standard_information = standard_information
                        entry_header.attributes.append(attribute_header)
                    except Exception as e:
                        Logger.error('Failed to add standard information attribute (%s)'%str(e))
                for attribute_list in mft_entry.attribute_list:
                    try:
                        attribute_header = self.self._prepare_attribute_header(attribute_list)
                        for attribute_list_entry in attribute_list.body:
                            try:
                                segment_reference = attribute_list_entry.SegmentReference
                                del attribute_list_entry.SegmentReference
                                attribute_list_entry = db.AttributeListEntry().populate_fields(attribute_list_entry)
                                segment_reference = db.FileReference().populate_fields(segment_reference)
                                attribute_list_entry.segment_reference = segment_reference
                                attribute_header.attribute_list.append(attribute_list_entry)
                            except Exception as e:
                                Logger.error('Failed to add attribute list entry (%s)'%str(e))
                        entry_header.attributes.append(attribute_header)
                    except Exception as e:
                        Logger.error('Failed to add attribute list attribute (%s)'%str(e))
                for file_name in mft_entry.file_name:
                    try:
                        attribute_header = self._prepare_attribute_header(file_name)
                        file_attribute_flags = file_name.body.FileAttributeFlags
                        parent_directory = file_name.body.ParentDirectory
                        del file_name.body.FileAttributeFlags
                        del file_name.body.ParentDirectory
                        file_name = db.FileName().populate_fields(file_name)
                        file_attribute_flags = db.FileAttributeFlags().populate_fields(file_attribute_flags)
                        parent_directory = db.FileReference().populate_fields(parent_directory)
                        file_name.file_attribute_flags = file_attribute_flags
                        file_name.parent_directory = parent_directory
                        attribute_header.file_name = file_name
                        entry_header.attributes.append(attribute_header)
                    except Exception as e:
                        Logger.error('Failed to add file name attribute (%s)'%str(e))
                for object_id in mft_entry.object_id:
                    #TODO
                    pass
                for security_descriptor in mft_entry.security_descriptor:
                    #TODO
                    pass
                for volume_name in mft_entry.volume_name:
                    try:
                        attribute_header = self.self._prepare_attribute_header(volume_name)
                        if len(volume_name.body) > 0:
                            volume_name = db.VolumeName(name=volume_name.body)
                            attribute_header.volume_name = volume_name
                        entry_header.attributes.append(attribute_header)
                    except Exception as e:
                        Logger.error('Failed to add volume name attribute (%s)'%str(e))
                for volume_information in mft_entry.volume_information:
                    try:
                        attribute_header = self.self._prepare_attribute_header(volume_information)
                        flags = volume_information.body.flags
                        del volume_information.body.flags
                        volume_information = db.VolumeInformation().populate_fields(volume_information.body)
                        volume_information.populate_fields(flags)
                        attribute_header.volume_information = volume_information
                        entry_header.attributes.append(attribute_header)
                    except Exception as e:
                        Logger.error('Failed to add volume information attribute (%s)'%str(e))
                for data in mft_entry.data:
                    try:
                        attribute_header = self.self._prepare_attribute_header(data)
                        if 'body' in data and data.body is not None:
                            data = db.Data().populate_fields(data.body)
                            attribute_header.data = data
                        entry_header.attributes.append(attribute_header)
                    except Exception as e:
                        Logger.error('Failed to add data attribute (%s)'%str(e))
                for index_root in mft_entry.index_root:
                    #TODO
                    pass
                for index_allocation in mft_entry.index_allocation:
                    try:
                        attribute_header = self.self._prepare_attribute_header(index_allocation)
                        entry_header.attributes.append(attribute_header)
                    except Exception as e:
                        Logger.error('Failed to add index allocation attribute (%s)'%str(e))
                for bitmap in mft_entry.bitmap:
                    try:
                        attribute_header = self.self._prepare_attribute_header(bitmap)
                        entry_header.attributes.append(attribute_header)
                    except Exception as e:
                        Logger.error('Failed to add bitmap attribute (%s)'%str(e))
                for logged_utility_stream in mft_entry.logged_utility_stream:
                    try:
                        attribute_header = self.self._prepare_attribute_header(logged_utility_stream)
                        entry_header.attributes.append(attribute_header)
                    except Exception as e:
                        Logger.error('Failed to add logged utility stream attribute (%s)'%str(e))

    def process_resultset(self, worker):
        '''
        @BaseParseTask.process_resultset
        '''
        if worker.manager.session is None:
            try:
                worker.manager.create_session()
            except Exception as e:
                Logger.error('Failed to create database session (%s)'%str(e))
                return [False]
        successful_results = 0
        for result in self.result_set:
            try:
                worker.manager.add(result)
                worker.manager.commit()
                successful_results += 1
            except Exception as e:
                Logger.error('Failed to commit result to database (%s)'%str(e))
                worker.manager.rollback()
        if successful_results > 0:
            Logger.info('Successfully committed %d result(s) to database'%successful_results)
        return [True]

class ParseDBTaskStage1(BaseParseFileOutputTask):
    '''
    Task class to parse single MFT entry in preparation for insertion into DB
    '''

    def __init__(self, source, nodeidx, recordidx, fileledger):
        super(BaseParseFileOutputTask, self).__init__(source)
        self._nodeidx = nodeidx
        self._recordidx = recordidx
        self._context = None
        self._fileledger = fileledger
    @property
    def fileledger(self):
        '''
        @fileledger.getter
        '''
        return self._fileledger
    @fileledger.setter
    def fileledger(self, value):
        '''
        @fileledger.setter
        Preconditions:
            value is of type Container
        '''
        assert isinstance(value, Container)
        self._fileledger = fileledger
    def extract_resultset(self, worker):
        '''
        @BaseParseTask.extract_resultset
        '''
        self.result_set = list()
        try:
            mft_entry = MFTEntry(self.source)
            mft_entry.parse()
            mft_entry._stream = None
            mft_entry.fileledger = self._fileledger
        except Exception as e:
            Logger.error('Failed to parse MFT entry %d from node %d (%s)'%(self.recordidx, self.nodeidx, str(e)))
        else:
            try:
                self.result_set.append(ParseDBTaskStage2([mft_entry]))
            except Exception as e:
                Logger.error('Failed to create DB output record for MFT entry %d from node %d (%s)'%(self.recordidx, self.nodeidx, str(e)))
    def process_resultset(self, worker):
        '''
        @BaseParseTask.process_resultset
        '''
        return self.result_set
