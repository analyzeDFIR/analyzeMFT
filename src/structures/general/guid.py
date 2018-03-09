## -*- coding: UTF-8 -*-
## guid.py
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
NTFS GUID: globally unique identifier
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
NTFSGUID = Struct(
    'Group1'                / Int32ul,
    'Group2'                / Int16ul,
    'Group3'                / Int16ul,
    'Group4'                / Int16ul,
    'Group5'                / BytesInteger(6, swapped=True)
)
