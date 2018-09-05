import time
from struct import Struct

ATTR_SIZE_OFFSET = 0
ATTR_SIZE_SIZE = 4
ATTR_SIZE_FORMAT = Struct('<L')
ATTR_TYPE_OFFSET = 0x10
ATTR_TYPE_SIZE = 4
ATTR_TYPE_FORMAT = Struct('<L')

ATTR_FILENAME_HEADER_FORMAT = Struct('<LHHHHHHL')

ATTR_TYPE_FILENAME = 0x00010030

def read_filename_attribute(dump, offset):
    dump.seek(offset, 0)
    data = dump.read(ATTR_FILENAME_HEADER_FORMAT.size)
    data_fields = ATTR_FILENAME_HEADER_FORMAT.unpack_from(data, 0)
    attr = {'_absolute_offset': offset,
            'size': data_fields[0],
            'header_length': data_fields[1],
            'length': data_fields[2],
            'next_struct_offset': data_fields[4],
            'record_rem_data': data_fields[5],
            'type': data_fields[7]}
    f_size = attr['length'] - ATTR_TYPE_SIZE
    if f_size > 0:
        dump.seek(offset + ATTR_TYPE_OFFSET + ATTR_TYPE_SIZE, 0)
        fn = dump.read(f_size)
    else:
        fn = 'DEADBEEF'.encode('utf-16le')
    attr['filename'] = fn
    return attr

def _dump_filename_attribute(attr, prefix=''):
    print('{}- size: {val:#x} ({val})'.format(prefix, val=attr['size']))
    print('{}- header length: {val:#x} ({val})'.format(prefix, val=attr['header_length']))
    print('{}- filename + attribute type length: {val:#x} ({val})'.format(prefix, val=attr['length']))
    print('{}- next structure offset: {val:#x} ({val})'.format(prefix, val=attr['next_struct_offset']))
    print('{}- record remaining data: {val:#x} ({val})'.format(prefix, val=attr['record_rem_data']))
    print('{}- record type: {:#x} (filename attribute)'.format(prefix, attr['type']))
    print('{}- filename: {}'.format(prefix, attr['filename'].decode('utf-16le')))

ATTR_FILENAME_FOLDER_HEADER_1_FORMAT = Struct('<L6sHLL')
ATTR_FILENAME_FOLDER_HEADER_2_FORMAT = Struct('<Q2sQQQQ')

ATTR_TYPE_FILENAME_FOLDER   = 0x00020030

def read_filename_folder_attribute(dump, offset):
    dump.seek(offset, 0)
    data = dump.read(ATTR_FILENAME_FOLDER_HEADER_1_FORMAT.size)
    data_fields = ATTR_FILENAME_FOLDER_HEADER_1_FORMAT.unpack_from(data, 0)
    attr = {'_absolute_offset': offset,
            'size': data_fields[0],
            'end_name_offset': data_fields[2],
            'record_rem_data': data_fields[3],
            'type': data_fields[4]}
    f_size = attr['end_name_offset'] - (ATTR_TYPE_OFFSET + ATTR_TYPE_SIZE)
    if f_size > 0:
        dump.seek(offset + ATTR_TYPE_OFFSET + ATTR_TYPE_SIZE, 0)
        fn = dump.read(f_size)
    else:
        fn = 'DEADBEEF'.encode('utf-16le')
    attr['foldername'] = fn
    dump.seek(offset + attr['end_name_offset'], 0)
    data = dump.read(ATTR_FILENAME_FOLDER_HEADER_2_FORMAT.size)
    data_fields = ATTR_FILENAME_FOLDER_HEADER_2_FORMAT.unpack_from(data, 0)
    attr['nodeid'] = data_fields[0]
    attr['created'] = data_fields[2]
    attr['modified'] = data_fields[3]
    attr['metadata_modified'] = data_fields[4]
    attr['last_accessed'] = data_fields[5]
    return attr

def _dump_filename_folder_attribute(attr, prefix=''):
    print('{}- size: {val:#x} ({val})'.format(prefix, val=attr['size']))
    print('{}- end name offset: {val:#x} ({val})'.format(prefix, val=attr['end_name_offset']))
    print('{}- record remaining data: {val:#x} ({val})'.format(prefix, val=attr['record_rem_data']))
    print('{}- record type: {:#x} (filename folder attribute)'.format(prefix, attr['type']))
    print('{}- foldername: {}'.format(prefix, attr['foldername'].decode('utf-16le')))
    print('{}- node identifier: {:#x}'.format(prefix, attr['nodeid']))
    print('{}- created: {} ({})'.format(prefix,
                                        time.asctime(time.gmtime(attr['created']/10000000000)),
                                        attr['created']/10000000000))
    print('{}- modified: {} ({})'.format(prefix,
                                        time.asctime(time.gmtime(attr['modified']/10000000000)),
                                        attr['modified']/10000000000))
    print('{}- metadata modified: {:#x}'.format(prefix, attr['metadata_modified']))
    print('{}- last accessed: {:#x}'.format(prefix, attr['last_accessed']))

ATTR_CHILD_HEADER_FORMAT = Struct('<LHH2sHH2sL4sL4sQ8sHH')

ATTR_TYPE_CHILD    = 0x80000020

def read_child_attribute(dump, offset):
    dump.seek(offset, 0)
    data = dump.read(ATTR_CHILD_HEADER_FORMAT.size)
    data_fields = ATTR_CHILD_HEADER_FORMAT.unpack_from(data, 0)
    attr = {'_absolute_offset': offset,
            'size': data_fields[0],
            'offset_identifier': data_fields[1],
            'header_rem_data': data_fields[2],
            'header_length': data_fields[4],
            'record_rem_data': data_fields[5],
            'type': data_fields[7],
            'parentid': data_fields[9],
            'childid': data_fields[11],
            '000c': data_fields[13],
            'length_name': data_fields[14]}
    fn = dump.read(attr['length_name'])
    attr['filename'] = fn
    return attr

def _dump_child_attribute(attr, prefix=''):
    print('{}- size: {val:#x} ({val})'.format(prefix, val=attr['size']))
    print('{}- offset identifier: {val:#x} ({val})'.format(prefix, val=attr['offset_identifier']))
    print('{}- header remaining data: {val:#x} ({val})'.format(prefix, val=attr['header_rem_data']))
    print('{}- header length: {val:#x} ({val})'.format(prefix, val=attr['header_length']))
    print('{}- record remaining data: {val:#x} ({val})'.format(prefix, val=attr['record_rem_data']))
    print('{}- record type: {:#x} (child attribute)'.format(prefix, attr['type']))
    print('{}- parent id: {:#x}'.format(prefix, attr['parentid']))
    print('{}- child id: {:#x}'.format(prefix, attr['childid']))
    print('{}- 000c: {:x}'.format(prefix, attr['000c']))
    print('{}- filename: {}'.format(prefix, attr['filename'].decode('utf-16le')))

ATTR_DIR_METADATA_HEADER_FORMAT = Struct('<LHHHHHH')
ATTR_DIR_METADATA_HEADER_2_FORMAT = Struct('<L')

ATTR_TYPE_DIRECTORY_METADATA = 0x00000010

def read_directory_metadata_attribute(dump, offset):
    dump.seek(offset)
    data = dump.read(ATTR_DIR_METADATA_HEADER_FORMAT.size)
    fields = ATTR_DIR_METADATA_HEADER_FORMAT.unpack_from(data, 0)
    attr = {'_absolute_offset': offset,
            'size': fields[0],
            'offset_identifier': fields[1],
            'header_rem_data': fields[2],
            'header_length': fields[4],
            'record_rem_data': fields[5]}

def _dump_directory_metadata_attribute(attr, prefix=''):
    pass

ATTR_HEADER_FORMAT = Struct('<LHHHHHH')
ATTR_HEADER_2_FORMAT = Struct('<L')

def read_attribute(dump, offset):
    dump.seek(offset, 0)
    data = dump.read(ATTR_HEADER_FORMAT.size)
    header1 = ATTR_HEADER_FORMAT.unpack_from(data, 0)
    dump.seek(offset + header1[1], 0)
    data = dump.read(ATTR_HEADER_2_FORMAT.size)
    header2 = ATTR_HEADER_2_FORMAT.unpack_from(data, 0)
    if header2[0] == ATTR_TYPE_FILENAME:
        attr = read_filename_attribute(dump, offset)
    elif header2[0] == ATTR_TYPE_FILENAME_FOLDER:
        attr = read_filename_folder_attribute(dump, offset)
    elif header2[0] == ATTR_TYPE_CHILD:
        attr = read_child_attribute(dump, offset)
    # elif header2[0] == ATTR_TYPE_DIRECTORY_METADATA:
    #     attr = read_directory_metadata_attribute(dump, offset)
    else:
        attr = {'_absolute_offset': offset,
                'size': header1[0],
                'offset_identifier': header1[1],
                'header_rem_data': header1[2],
                'header_length': header1[4],
                'record_rem_data': header1[5],
                'type': header2[0]}
    return attr

def dump_attribute(attr, prefix=''):
    if attr['type'] == ATTR_TYPE_FILENAME:
        _dump_filename_attribute(attr, prefix)
    elif attr['type'] == ATTR_TYPE_FILENAME_FOLDER:
        _dump_filename_folder_attribute(attr, prefix)
    elif attr['type'] == ATTR_TYPE_CHILD:
        _dump_child_attribute(attr, prefix)
    # elif attr['type'] == ATTR_TYPE_DIRECTORY_METADATA:
    #     _dump_directory_metadata_attribute(attr, prefix)
    else:
        print('{}- size: {val:#x} ({val})'.format(prefix, val=attr['size']))
        print('{}- offset type identifier: {val:#x} ({val})'.format(prefix,
                                                                    val=attr['offset_identifier']))
        print('{}- header remaining bytes: {val:#x} ({val})'.format(prefix,
                                                                    val=attr['header_rem_data']))
        print('{}- header length: {val:#x} ({val})'.format(prefix, val=attr['header_length']))
        print('{}- record remaining data: {val:#x} ({val})'.format(prefix,
                                                                    val=attr['record_rem_data']))
        print('{}- type: {:#x} (unknown type)'.format(prefix, attr['type']))
