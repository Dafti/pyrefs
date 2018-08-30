from struct import Struct

ATTR_SIZE_OFFSET = 0
ATTR_SIZE_SIZE = 4
ATTR_SIZE_FORMAT = Struct('<L')
ATTR_TYPE_OFFSET = 0x10
ATTR_TYPE_SIZE = 4

ATTR_HEADER_FORMAT = Struct('<LHHHHHHL')

ATTR_TYPE_FILENAME = 0x00010030
ATTR_TYPE_FOLDER   = 0x00020030

def read_filename_attribute(attr, dump, offset):
    dump.seek(offset + ATTR_TYPE_OFFSET + ATTR_TYPE_SIZE, 0)
    fn = dump.read(attr['length'] - ATTR_TYPE_SIZE)
    attr['filename'] = fn

def read_folder_attribute(attr, dump, offset):
    dump.seek(offset + ATTR_TYPE_OFFSET + ATTR_TYPE_SIZE, 0)
    fn = dump.read(attr['length'] - ATTR_TYPE_SIZE)
    attr['foldername'] = fn

def read_attribute(dump, offset):
    dump.seek(offset, 0)
    data = dump.read(ATTR_HEADER_FORMAT.size)
    data_fields = ATTR_HEADER_FORMAT.unpack_from(data, 0)
    attr_size = data_fields[0]
    attr = {'size': data_fields[0],
            'header_length': data_fields[1],
            'length': data_fields[2],
            'next_struct_offset': data_fields[4],
            'record_rem_data': data_fields[5],
            'type': data_fields[7]}
    if attr['type'] == ATTR_TYPE_FILENAME:
        read_filename_attribute(attr, dump, offset)
    if attr['type'] == ATTR_TYPE_FOLDER:
        read_folder_attribute(attr, dump, offset)
    return attr

def dump_attribute(attr):
    print(attr)
