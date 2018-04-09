# analyzeMFT

## What is analyzeMFT?

[analyzeMFT](https://github.com/noahrubin/analyzeMFT) is a command line tool for parsing information from $MFT files extracted from drives using the NTFS filesystem.  The tool was originally written by [David Kovar](https://github.com/dkovar), and is intended to parse as much information from an $MFT file as possible in the most accurate way possible.  I chose to re-write the tool with the following goals/enhancements in mind:

1) Construct a framework for parallel processing to reduce parsing time.
2) Extract as much information from the $MFT as possible without taking an opinion on how analysts should use that information.
3) Embrace the relational nature of the $MFT, and enable/encourage outputting information to a database.
4) Create a command line interface (CLI) framework to minimize the cost of adding new functionality.

## Installation

This version of analyzeMFT is not yet available on PyPi, so it can be cloned via the following:

```bash
$ git clone git@github.com:noahrubin/analyzeMFT.git # (or https://github.com/noahrubin/analyzeMFT.git)
$ cd analyzeMFT
$ ./amft.py -h # show CLI usage
```

## Dependencies

All of the core dependencies beside [six](https://pypi.python.org/pypi/six) come shipped with analyzeMFT in the [lib/](https://github.com/noahrubin/analyzeMFT/tree/rewrite2018/lib) directory, and the application uses those by default.  If there is a consensus that users want the ability to use already-installed versions of those packages (i.e. in a virtualenv), that change can be made easily.  Thus, the only potential dependencies are database drivers for SQLAlchemy to use.  See below:

| RDBMS Name | SQLAlchemy Link |
|------------|-----------------|
| SQLite | <a href="http://docs.sqlalchemy.org/en/latest/dialects/sqlite.html" target="_blank">http://docs.sqlalchemy.org/en/latest/dialects/sqlite.html</a> |
| PostgreSQL | <a href="http://docs.sqlalchemy.org/en/latest/dialects/postgresql.html" target="_blank">http://docs.sqlalchemy.org/en/latest/dialects/postgresql.html</a> |
| MySQL | <a href="http://docs.sqlalchemy.org/en/latest/dialects/mysql.html" target="_blank">http://docs.sqlalchemy.org/en/latest/dialects/mysql.html</a> |
| MSSQL | <a href="http://docs.sqlalchemy.org/en/latest/dialects/mssql.html" target="_blank">http://docs.sqlalchemy.org/en/latest/dialects/mssql.html</a> |
| Oracle | <a href="http://docs.sqlalchemy.org/en/latest/dialects/oracle.html" target="_blank">http://docs.sqlalchemy.org/en/latest/dialects/oracle.html</a> |

## Getting Started

analyzeMFT can output information into CSV, bodyfile, and JSON file formats, as well as into a relational database.  Which output format you want will determine the command to use. See the [Usage](#usage) section for full usage documentation.

#### CSV Output

```bash
$ ./amft.py parse csv summary -s /path/to/MFT -t /path/to/output.csv
```

```bash
$ ./amft.py parse csv summary -s /path/to/MFT -t /path/to/output.tsv --threads 3 --sep '    '
```

```bash
$ ./amft.py parse csv summary --lpath /path/to/log/ --lpref output -s /path/to/MFT -t /path/to/output.csv --threads 3
```

#### Bodyfile Output

```bash
$ ./amft.py parse body -s /path/to/MFT -t /path/to/output.body
```

```bash
$ ./amft.py parse body -s /path/to/MFT -t /path/to/output.body --threads 3
```

```bash
$ ./amft.py parse body --lpath /path/to/log/ --lpref output -s /path/to/MFT -t /path/to/output.body --threads 3
```

#### JSON Output

```bash
$ ./amft.py parse json -s /path/to/MFT -t /path/to/output.csv
```

```bash
$ ./amft.py parse json -s /path/to/MFT -t /path/to/output.tsv --threads 3 --sep '    '
```

```bash
$ ./amft.py parse json --lpath /path/to/log/ --lpref output -s /path/to/MFT -t /path/to/output.csv --threads 3
```

#### Database Output

```bash
$ ./amft.py parse db -s /path/to/MFT -n /path/to/output.db # SQLite by default
```

```bash
$ ./amft.py parse db -s /path/to/MFT -n testdb -C "postgres:passwd@localhost:5432" # PostgreSQL server running on localhost
```


```bash
$ ./amft.py parse db -s /path/to/MFT -n testdb -d postgresql -u postgres -p root -H localhost -P 5432 # Same as above
```

```bash
$ ./amft.py parse db -s /path/to/MFT -n testdb -C /path/to/config/file # Read connection string from file
```

## Usage

Much like [Git](https://git-scm.com/docs), the CLI for analyzeMFT is separated into directives.  See below for a detailed, hierarchical description of the directives.

### CLI Menu Root (amft.py -h)

| Directive | Description |
|-----------|-------------|
| parse | $MFT file parser directives |
| query | Submit query to $MFT database |

### Parse Menu (amft.py parse -h)

| Directive | Description |
|-----------|-------------|
| csv | Parse $MFT file(s) to CSV |
| body | Parse $MFT file(s) MACB times to bodyfile |
| json | Parse $MFT file(s) to JSON |
| file | Parse $MFT file(s) to multiple output formats (simultaneously) |
| db | Parse $MFT file(s) to database |

#### Parse CSV Menu (amft.py parse csv -h)

| Argument | Flags | Optional | Description |
|-----------|------|----------|-------------|
| info_type | N/A | False | Type of information to output (choices: summary) |
| sources | -s, --source | False | Path to input file(s) - can use multiple times |
| target | -t, --target | False | Path to output file |
| help | -h, --help | True | Show help message and exit |
| log_path | --lpath | True | Path to log file directory (i.e. /path/to/logs or C:\Users\<user>\Documents\) |
| log_prefix | --lpref | True | Prefix for log file (default: amft_\<date\>) |
| count | -c, --count | True | Number of records to process (default: all) |
| threads | --threads | True | Number of processes to use |
| sep | -S, --sep | True | Output file separator (default: ",") |

#### Parse Body Menu (amft.py parse body -h)

| Argument | Flags | Optional | Description |
|-----------|------|----------|-------------|
| sources | -s, --source | False | Path to input file(s) - can use multiple times |
| target | -t, --target | False | Path to output file |
| help | -h, --help | True | Show help message and exit |
| log_path | --lpath | True | Path to log file directory (i.e. /path/to/logs or C:\Users\<user>\Documents\) |
| log_prefix | --lpref | True | Prefix for log file (default: amft_\<date\>) |
| count | -c, --count | True | Number of records to process (default: all) |
| threads | --threads | True | Number of processes to use |
| sep | -S, --sep | True | Output file separator (default: "\|") |

#### Parse JSON Menu (amft.py parse json -h)

| Argument | Flags | Optional | Description |
|-----------|------|----------|-------------|
| sources | -s, --source | False | Path to input file(s) - can use multiple times |
| target | -t, --target | False | Path to output file |
| help | -h, --help | True | Show help message and exit |
| log_path | --lpath | True | Path to log file directory (i.e. /path/to/logs or C:\Users\<user>\Documents\) |
| log_prefix | --lpref | True | Prefix for log file (default: amft_\<date\>) |
| count | -c, --count | True | Number of records to process (default: all) |
| threads | --threads | True | Number of processes to use |
| pretty | -p, --pretty | True | Whether to pretty-print the JSON output (ignored if threads > 1) |

#### Parse File Menu (amft.py parse file -h)

| Argument | Flags | Optional | Description |
|-----------|------|----------|-------------|
| sources | -s, --source | False | Path to input file(s) - can use multiple times |
| target | -t, --target | False | Path to output file (without extension) |
| formats | -f, --format | False | Comma-separated list of output formats (choices: csv, body, and json) |
| help | -h, --help | True | Show help message and exit |
| log_path | --lpath | True | Path to log file directory (i.e. /path/to/logs or C:\Users\<user>\Documents\) |
| log_prefix | --lpref | True | Prefix for log file (default: amft_\<date\>) |
| count | -c, --count | True | Number of records to process (default: all) |
| threads | --threads | True | Number of processes to use |
| pretty | -p, --pretty | True | Whether to pretty-print the JSON output (ignored if threads > 1) |
| info_type | -i, --info-type | True | Information type for CSV output |

#### Parse DB Menu (amft.py parse db -h)

| Argument | Flags | Optional | Description |
|-----------|------|----------|-------------|
| sources | -s, --source | False | Path to input file(s) - can use multiple times |
| db_name | -n, --db | False | Name of database to connect to (path to database if using sqlite) |
| help | -h, --help | True | Show help message and exit |
| db_conn_string | -C, --connect | True | Database connection string, or filepath to file containing connection string |
| db_driver | -d, --driver | True | Database driver to use (default: sqlite) |
| db_user | -u, --user | True | Name of database user (alternative to connection string) |
| db_passwd | -p, --passwd | True | Database user password (alternative to connection string) |
| db_host | -H, --host | True | Hostname or IP address of database (alternative to connection string) |
| db_port | -C, --connect | True | Port database is listening on (alternative to connection string) |
| log_path | --lpath | True | Path to log file directory (i.e. /path/to/logs or C:\Users\<user>\Documents\) |
| log_prefix | --lpref | True | Prefix for log file (default: amft_\<date\>) |
| count | -c, --count | True | Number of records to process (default: all) |
| threads | --threads | True | Number of processes to use |

For examples, see [Getting Started](#getting-started)

### Query Menu (amft.py query -h)

| Argument | Flags | Optional | Description |
|-----------|------|----------|-------------|
| query | -q, --query | False | Query to submit to database |
| db_name | -n, --db | False | Name of database to connect to (path to database if using sqlite) |
| help | -h, --help | True | Show help message and exit |
| db_conn_string | -C, --connect | True | Database connection string, or filepath to file containing connection string |
| db_driver | -d, --driver | True | Database driver to use (default: sqlite) |
| db_user | -u, --user | True | Name of database user (alternative to connection string) |
| db_passwd | -p, --passwd | True | Database user password (alternative to connection string) |
| db_host | -H, --host | True | Hostname or IP address of database (alternative to connection string) |
| db_port | -C, --connect | True | Port database is listening on (alternative to connection string) |
| log_path | --lpath | True | Path to log file directory (i.e. /path/to/logs or C:\Users\<user>\Documents\) |
| log_prefix | --lpref | True | Prefix for log file (default: amft_\<date\>) |
| target | -t, --target | True | Path to output file (default: stdout) |
| sep | -S, --sep | True | Output file separator (default: ",") |
| title | -T, --title | True | Title to use for output table |

Example:

```bash
$ ./amft.py query -n ./test.db -q "select file_name, file_path, sha2hash from fileledger"
```

## Output Formats

Due to the relational nature of the $MFT, the various file formats output different types of information.  See the sections below for a detailed desciption of each.

### CSV Format

| Field | Description |
|-------|-------------|
| RecordNumber | See <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/headers.py" target="_blank">src/structures/headers.py</a> (MFTEntryHeader) |
| Signature | See <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/headers.py" target="_blank">src/structures/headers.py</a> (MFTEntryHeader) |
| SequenceNumber | See <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/headers.py" target="_blank">src/structures/headers.py</a> (MFTEntryHeader) |
| LogFileSequenceNumber | See <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/headers.py" target="_blank">src/structures/headers.py</a> (MFTEntryHeader) |
| BaseFileRecordSegmentNumber | See <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/headers.py" target="_blank">src/structures/headers.py</a> (MFTEntryHeader) |
| BaseFileRecordSequenceNumber | See <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/headers.py" target="_blank">src/structures/headers.py</a> (MFTEntryHeader) |
| Active | See <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/headers.py" target="_blank">src/structures/headers.py</a> (MFTEntryHeader) |
| HasIndex | See <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/headers.py" target="_blank">src/structures/headers.py</a> (MFTEntryHeader) |
| UsedSize | See <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/headers.py" target="_blank">src/structures/headers.py</a> (MFTEntryHeader) |
| TotalSize | See <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/headers.py" target="_blank">src/structures/headers.py</a> (MFTEntryHeader) |
| ReferenceCount | See <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/headers.py" target="_blank">src/structures/headers.py</a> (MFTEntryHeader) |
| FirstAttributeId | See <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/headers.py" target="_blank">src/structures/headers.py</a> (MFTEntryHeader) |
| FileName | Longest file name found in $FILE_NAME attributes |
| StandardInformationModifyDate | M time from first $STANDARD_INFORMATION attribute |
| StandardInformationAccessDate | A time from first $STANDARD_INFORMATION attribute |
| StandardInformationEntryDate | C time from first $STANDARD_INFORMATION attribute |
| StandardInformationCreateDate | B time from first $STANDARD_INFORMATION attribute |
| FileNameModifyDate | M time from first $FILE_NAME attribute |
| FileNameAccessDate | A time from first $FILE_NAME attribute |
| FileNameEntryDate | C time from first $FILE_NAME attribute |
| FileNameCreateDate | B time from first $FILE_NAME attribute |
| StandardInformationCount | Number of $STANDARD_INFORMATION attributes found |
| AttributeListCount | Number of $ATTRIBUTE_LIST attributes found |
| FileNameCount | Number of $FILE_NAME attributes found |
| ObjectIDCount | Number of $OBJECT_ID attributes found |
| SecurityDescriptorCount | Number of $SECURITY_DESCRIPTOR attributes found |
| VolumeNameCount | Number of $VOLUME_NAME attributes found |
| VolumeInformationCount | Number of $VOLUME_INFORMATION attributes found |
| DataCount | Number of $DATA attributes found |
| IndexRootCount | Number of $INDEX_ROOT attributes found |
| IndexAllocationCount | Number of $INDEX_ALLOCATION attributes found |

### Bodyfile Format

The body format attempts to mimic the bodyfile format v3.x created by [TSK](http://wiki.sleuthkit.org/index.php?title=Body_file):

| Field | Description |
|-------|-------------|
| nodeidx | Index of $MFT file parsed\* |
| recordidx | Index of record in $MFT file\* |
| MD5 | Hash of $MFT entry |
| name | Longest file name found in $FILE_NAME attributes |
| inode | NULL |
| mode_as_string | NULL |
| UID | NULL |
| GID | 'FN' if timestamps taken from $FILE_NAME attribute, 'SI' if taken from $STANDARD_INFORMATION attribute |
| size | File size present in first $FILE_NAME attribute |
| atime | A time in UNIX time format |
| mtime | m time in UNIX time format |
| ctime | c time in UNIX time format |
| crtime | b time in UNIX time format |

\*: the nodeidx and recordidx fields exist so that when processing data in parallel, the program knows how to properly sort output data.

## JSON Format

The JSON format is an unordered collection of data parsed from each $MFT entry, and contains the following top-level keys:

| Key Name | Description |
|----------|-------------|
| header | See <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/headers.py" target="_blank">src/structures/headers.py</a> (MFTEntryHeader) |
| standard_information | See <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/standard_information.py" target="_blank">src/structures/standard_information.py</a> |
| attribute_list | See <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/attribute_list.py" target="_blank">src/structures/attribute_list.py</a> |
| file_name | See <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/file_name.py" target="_blank">src/structures/file_name.py</a> |
| object_id | See <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/object_id.py" target="_blank">src/structures/object_id.py</a> |
| security_descriptor | See <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/security_descriptor.py" target="_blank">src/structures/security_descriptor.py</a> |
| volume_name | NTFS volume name |
| volume_information | See <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/volume_information.py" target="_blank">src/structures/volume_information.py</a> |
| data | If data is resident in $MFT, will contain UTF-8 encoded version of binary data, as well as hash of original binary data |
| index_root | See <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/index.py" target="_blank">src/structures/index.py</a> |
| index_allocation | Only contains attribute header information (see <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/headers.py" target="_blank">src/structures/headers.py</a>) |
| bitmap | Only contains attribute header information (see <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/headers.py" target="_blank">src/structures/headers.py</a>) |
| logged_utility_stream | Only contains attribute header information (see <a href="https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/structures/headers.py" target="_blank">src/structures/headers.py</a>) |

## JSON Format

See [src/database/models.py](https://github.com/noahrubin/analyzeMFT/blob/rewrite2018/src/database/models.py).

## Contributing/Suggestions

analyzeMFT is the first of a set of tools I intend on writing to parse forensic artifacts pertinent to DFIR with the [aforementioned](#what-is-analyzemft) four goals in mind.  Writing these parsers is my way of aiding in the democratization of DFIR, reducing the need for expensive licenses to solve cases.  To that end, any and all help/suggestions are welcome! Please open an issue if you find a bug or have a feature request, or please reach out to me at adfir [at] sudomail [dot] com with any comments!

## Resources


\#\#TODO
