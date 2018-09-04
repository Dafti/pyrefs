from struct import Struct

ATTR_SIZE_OFFSET = 0
ATTR_SIZE_SIZE = 4
ATTR_SIZE_FORMAT = Struct('<L')
ATTR_TYPE_OFFSET = 0x10
ATTR_TYPE_SIZE = 4
ATTR_TYPE_FORMAT = Struct('<L')

ATTR_HEADER_FORMAT = Struct('<LHHHHHHL')

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

ATTR_FOLDER_HEADER_1_FORMAT = Struct('<L6sHLL')
ATTR_FOLDER_HEADER_2_FORMAT = Struct('<Q2sQQQQ')

ATTR_TYPE_FOLDER   = 0x00020030

def read_folder_attribute(dump, offset):
    dump.seek(offset, 0)
    data = dump.read(ATTR_FOLDER_HEADER_1_FORMAT.size)
    data_fields = ATTR_FOLDER_HEADER_1_FORMAT.unpack_from(data, 0)
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
    data = dump.read(ATTR_FOLDER_HEADER_2_FORMAT.size)
    data_fields = ATTR_FOLDER_HEADER_2_FORMAT.unpack_from(data, 0)
    attr['nodeid'] = data_fields[0]
    attr['created'] = data_fields[2]
    attr['modified'] = data_fields[3]
    attr['metadata_modified'] = data_fields[4]
    attr['last_accessed'] = data_fields[5]
    return attr

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

def read_attribute(dump, offset):
    dump.seek(offset + ATTR_TYPE_OFFSET, 0)
    data = dump.read(ATTR_TYPE_FORMAT.size)
    attr_type, = ATTR_TYPE_FORMAT.unpack_from(data,0)
    if attr_type == ATTR_TYPE_FILENAME:
        attr = read_filename_attribute(dump, offset)
    if attr_type == ATTR_TYPE_FOLDER:
        attr = read_folder_attribute(dump, offset)
    if attr_type == ATTR_TYPE_CHILD:
        attr = read_child_attribute(dump, offset)
    return attr

def dump_attribute(attr):
    print(attr)
