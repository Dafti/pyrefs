import time
from struct import Struct

ATTR_SIZE_OFFSET = 0
ATTR_SIZE_SIZE = 4
ATTR_SIZE_FORMAT = Struct('<L')
ATTR_TYPE_OFFSET = 0x10
ATTR_TYPE_SIZE = 4
ATTR_TYPE_FORMAT = Struct('<L')

ATTR_FN_METADATA_FORMAT = Struct('<LH34sQQQQB7sQQQQQ')

def read_filename_attribute_metadata(dump, offset):
    dump.seek(offset, 0)
    data = dump.read(ATTR_FN_METADATA_FORMAT.size)
    fields = ATTR_FN_METADATA_FORMAT.unpack_from(data, 0)
    attr = {'_absolute_offset': offset,
            'size': fields[0],
            'offset_to_val?': fields[1],
            'created': fields[3],
            'modified': fields[4],
            'metadata_modified': fields[5],
            'last_accessed': fields[6],
            'flags': fields[7],
            'parentid': fields[9],
            'childid': fields[10],
            'unknown': fields[11],
            'logical_size': fields[12],
            'physical_size': fields[13]}
    return attr

def _dump_filename_attribute_metadata(attr, prefix=''):
    print('{}- size: {val:#x} ({val})'.format(prefix, val=attr['size']))
    print('{}- offset to first value(?): {val:#x} ({val})'.format(prefix, val=attr['offset_to_val?']))
    print('{}- created: {:#x}'.format(prefix, attr['created']))
    print('{}- modified: {:#x}'.format(prefix, attr['modified']))
    print('{}- metadata modified: {:#x}'.format(prefix, attr['metadata_modified']))
    print('{}- last accessed: {:#x}'.format(prefix, attr['last_accessed']))
    print('{}- flags: {:#x}'.format(prefix, attr['flags']))
    print('{}- parent node id: {:#x}'.format(prefix, attr['parentid']))
    print('{}- child node id: {:#x}'.format(prefix, attr['childid']))
    print('{}- unknown field: {:#x}'.format(prefix, attr['unknown']))
    print('{}- logical size: {val:#x} ({val})'.format(prefix, val=attr['logical_size']))
    print('{}- physical size: {val:#x} ({val})'.format(prefix, val=attr['physical_size']))

ATTR_FN_DATARUN_ENTRY_HEADER_FORMAT = Struct('<LHHHHLLLL')

def read_filename_attribute_datarun_entry(dump, offset):
    dump.seek(offset, 0)
    data = dump.read(ATTR_FN_DATARUN_ENTRY_HEADER_FORMAT.size)
    fields = ATTR_FN_DATARUN_ENTRY_HEADER_FORMAT.unpack_from(data, 0)
    attr = {'_absolute_offset': offset,
            'size': fields[0],
            'unknown0': fields[1],
            'unknown1': fields[2],
            'unknown2': fields[3],
            'header_size': fields[4],
            'body_size': fields[5],
            'body_size_copy': fields[6],
            'unknown3': fields[7],
            'attributeid?': fields[8]}
    return attr

def _dump_filename_attribute_datarun_entry(attr, prefix=''):
    print('{}- size: {val:#x} ({val})'.format(prefix, val=attr['size']))
    print('{}- unknown field 0: {val:#x} ({val})'.format(prefix, val=attr['unknown0']))
    print('{}- unknown field 1: {val:#x} ({val})'.format(prefix, val=attr['unknown1']))
    print('{}- unknown field 2: {val:#x} ({val})'.format(prefix, val=attr['unknown2']))
    print('{}- header size: {val:#x} ({val})'.format(prefix, val=attr['header_size']))
    print('{}- body size: {val:#x} ({val})'.format(prefix, val=attr['body_size']))
    print('{}- body size (copy): {val:#x} ({val})'.format(prefix, val=attr['body_size_copy']))
    print('{}- unknown field 3: {val:#x} ({val})'.format(prefix, val=attr['unknown3']))
    print('{}- attribute type identifier: {:#010x}'.format(prefix, attr['attributeid?']))

ATTR_FN_DATARUN_HEADER_FORMAT = Struct('<LLLLLLL')

def read_filename_attribute_datarun(dump, offset):
    dump.seek(offset, 0)
    data = dump.read(ATTR_FN_DATARUN_HEADER_FORMAT.size)
    fields = ATTR_FN_DATARUN_HEADER_FORMAT.unpack_from(data, 0)
    attr = {'_absolute_offset': offset,
            'size': fields[0],
            'offset_next_free_record': fields[1],
            'free_space': fields[2],
            'unknown0': fields[3],
            'offset_first_pointer': fields[4],
            'num_pointers': fields[5],
            'end_of_struct': fields[6]}
    if attr['num_pointers']:
        pointers_format = Struct('<' + ('L' * attr['num_pointers']))
        dump.seek(offset + attr['offset_first_pointer'], 0)
        data = dump.read(pointers_format.size)
        fields = pointers_format.unpack_from(data, 0)
        attr['pointers'] = fields
        attr['pointers_data'] = []
        for ptr in attr['pointers']:
            ptr_addr = offset + ptr
            attr['pointers_data'].append(read_filename_attribute_datarun_entry(dump, ptr_addr))
    else:
        attr['pointers'] = None
        attr['pointers_data'] = None
    return attr

def _dump_filename_attribute_datarun(attr, prefix=''):
    print('{}- size: {val:#x} ({val})'.format(prefix, val=attr['size']))
    print('{}- offset next free record: {:#x}'.format(prefix, attr['offset_next_free_record']))
    print('{}- free space: {val:#x} ({val})'.format(prefix, val=attr['free_space']))
    print('{}- unknown value: {val:#x} ({val})'.format(prefix, val=attr['unknown0']))
    print('{}- offset to first pointer: {:#x}'.format(prefix, attr['offset_first_pointer']))
    print('{}- number of pointers: {}'.format(prefix, attr['num_pointers']))
    print('{}- end of structure: {val:#x} ({val})'.format(prefix, val=attr['end_of_struct']))
    if attr['pointers']:
        print('{}- pointers:'.format(prefix), end='')
        for ptr in attr['pointers']:
            print(' {:#x}'.format(ptr), end='')
        print('')
        for ptr_i, ptr in enumerate(attr['pointers_data']):
            print('{}  - pointer {}: <{:#x}>'.format(prefix, ptr_i, ptr['_absolute_offset']))
            _dump_filename_attribute_datarun_entry(ptr, prefix + '    ')
    else:
        print('{}- pointers: None'.format(prefix))
        print('{}- pointers data: None'.format(prefix))

ATTR_FILENAME_HEADER_FORMAT = Struct('<LHHHHHHL')

ATTR_TYPE_FILENAME = 0x00010030

def read_filename_attribute(dump, offset):
    dump.seek(offset, 0)
    # TODO: the header should be read in two steps using header_length
    data = dump.read(ATTR_FILENAME_HEADER_FORMAT.size)
    fields = ATTR_FILENAME_HEADER_FORMAT.unpack_from(data, 0)
    attr = {'_absolute_offset': offset,
            'size': fields[0],
            'header_length': fields[1],
            'length': fields[2],
            'next_struct_offset': fields[4],
            'record_rem_data': fields[5],
            'type': fields[7]}
    f_size = attr['length'] - ATTR_TYPE_SIZE
    if f_size > 0:
        dump.seek(offset + ATTR_TYPE_OFFSET + ATTR_TYPE_SIZE, 0)
        fn = dump.read(f_size)
    else:
        fn = 'DEADBEEF'.encode('utf-16le')
    attr['filename'] = fn
    attr['_offset_metadata'] = attr['next_struct_offset']
    attr['metadata'] = read_filename_attribute_metadata(dump, offset + attr['_offset_metadata'])
    attr['_offset_datarun'] = attr['_offset_metadata'] + attr['metadata']['size']
    attr['datarun'] = read_filename_attribute_datarun(dump, offset + attr['_offset_datarun'])
    return attr

def _dump_filename_attribute(attr, prefix=''):
    print('{}- size: {val:#x} ({val})'.format(prefix, val=attr['size']))
    print('{}- header length: {val:#x} ({val})'.format(prefix, val=attr['header_length']))
    print('{}- filename + attribute type length: {val:#x} ({val})'.format(prefix, val=attr['length']))
    print('{}- next structure offset: {val:#x} ({val})'.format(prefix, val=attr['next_struct_offset']))
    print('{}- record remaining data: {val:#x} ({val})'.format(prefix, val=attr['record_rem_data']))
    print('{}- record type: {:#x} (filename attribute)'.format(prefix, attr['type']))
    print('{}- filename: {}'.format(prefix, attr['filename'].decode('utf-16le')))
    print('{}- metadata: <{:#x}>'.format(prefix, attr['metadata']['_absolute_offset']))
    _dump_filename_attribute_metadata(attr['metadata'], prefix + '  ')
    print('{}- datarun: <{:#x}>'.format(prefix, attr['datarun']['_absolute_offset']))
    _dump_filename_attribute_datarun(attr['datarun'], prefix + '  ')

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
ATTR_DIR_METADATA_BODY_FORMAT = Struct('<LH34sQQQQ8sQ')
ATTR_DIR_METADATA_PSEC_FORMAT = Struct('<L12sLLL')

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
            'record_rem_data': fields[5],
            '_structure_size': fields[0]}
    dump.seek(offset + attr['offset_identifier'])
    data = dump.read(ATTR_DIR_METADATA_HEADER_2_FORMAT.size)
    fields = ATTR_DIR_METADATA_HEADER_2_FORMAT.unpack_from(data, 0)
    attr['type'] = fields[0]
    dump.seek(offset + attr['header_length'])
    data = dump.read(ATTR_DIR_METADATA_BODY_FORMAT.size)
    fields = ATTR_DIR_METADATA_BODY_FORMAT.unpack_from(data, 0)
    attr['_offset_body'] = attr['header_length']
    attr['body_length'] = fields[0]
    attr['offset_first_timestamp'] = fields[1]
    attr['created'] = fields[3]
    attr['modified'] = fields[4]
    attr['metadata_modified'] = fields[5]
    attr['last_accessed'] = fields[6]
    attr['nodeid'] = fields[8]
    attr['_offset_psec'] = attr['_offset_body'] + attr['body_length']
    dump.seek(offset + attr['_offset_psec'], 0)
    data = dump.read(ATTR_DIR_METADATA_PSEC_FORMAT.size)
    fields = ATTR_DIR_METADATA_PSEC_FORMAT.unpack_from(data, 0)
    attr['psec_length'] = fields[0]
    attr['offset_first_pointer'] = fields[2]
    attr['num_pointers'] = fields[3]
    attr['offset_end_pointers_area?'] = fields[4]
    if attr['num_pointers']:
        pointers_format = Struct('<' + ('L' * attr['num_pointers']))
        dump.seek(offset + attr['_offset_psec'] + attr['offset_first_pointer'], 0)
        data = dump.read(pointers_format.size)
        fields = pointers_format.unpack_from(data, 0)
        attr['pointers'] = fields
        attr['pointers_data'] = []
    else:
        attr['pointers'] = None
        attr['pointers_data'] = None
    attr['_offset_rec_area'] = attr['_offset_psec'] + attr['psec_length']
    rec_offset = attr['_offset_rec_area']
    for ptr in attr['pointers']:
        ptr_addr = offset + attr['_offset_psec'] + ptr
        attr['pointers_data'].append(read_directory_metadata_subattribute(dump, ptr_addr))
    return attr

def _dump_directory_metadata_attribute(attr, prefix=''):
    print('{}- size: {val:#x} ({val})'.format(prefix, val=attr['size']))
    print('{}- offset type identifier: {val:#x} ({val})'.format(prefix,
                                                                val=attr['offset_identifier']))
    print('{}- header remaining bytes: {val:#x} ({val})'.format(prefix,
                                                                val=attr['header_rem_data']))
    print('{}- header length/offset metadata: {val:#x} ({val})'.format(prefix,
                                                                       val=attr['header_length']))
    print('{}- record remaining data: {val:#x} ({val})'.format(prefix,
                                                               val=attr['record_rem_data']))
    print('{}- type: {:#x} (directory metadata attribute)'.format(prefix, attr['type']))
    print('{}- body: <{:#x}>'.format(prefix, attr['_absolute_offset'] + attr['_offset_body']))
    print('{}  - length: {val:#x} ({val})'.format(prefix, val=attr['body_length']))
    print('{}  - offset_first_timestamp: {val:#x} ({val})'.format(prefix,
                                                                  val=attr['offset_first_timestamp']))
    print('{}  - created: {:#x}'.format(prefix, attr['created']))
    print('{}  - modified: {:#x}'.format(prefix, attr['modified']))
    print('{}  - metadata modified: {:#x}'.format(prefix, attr['metadata_modified']))
    print('{}  - last accessed: {:#x}'.format(prefix, attr['last_accessed']))
    print('{}  - node id: {:#x}'.format(prefix, attr['nodeid']))
    print('{}- pointers section: <{:#x}>'.format(prefix,
                                                 attr['_absolute_offset'] + attr['_offset_psec']))
    print('{}  - length: {val:#x} ({val})'.format(prefix, val=attr['psec_length']))
    print('{}  - offset to first pointer: {:#x}'.format(prefix, attr['offset_first_pointer']))
    print('{}  - number of pointers: {}'.format(prefix, attr['num_pointers']))
    print('{}  - offset end pointers area(?): {val:#x} ({val})'.format(prefix,
        val=attr['offset_end_pointers_area?']))
    print('{}  - pointers:'.format(prefix), end='')
    if attr['pointers']:
        for ptr in attr['pointers']:
            print(' {:#x}'.format(ptr), end='')
        print('')
        print('{}- pointers data:'.format(prefix))
        for ptr_i, ptr in enumerate(attr['pointers_data']):
            print('{}  - pointer {}: <{:#x}>'.format(prefix, ptr_i, ptr['_absolute_offset']))
            _dump_directory_metadata_subattribute(ptr, prefix + '    ')
    else:
        print(' None')
        print('{}  - pointers data: None'.format(prefix))

DM_SUBATTR_SI30_HEADER_FORMAT = Struct('<LHHHHLLLL8s')

DM_SUBATTR_TYPE_SI30 = 0x00000090

def read_dm_si30_subattribute(dump, offset):
    dump.seek(offset)
    data = dump.read(DM_SUBATTR_SI30_HEADER_FORMAT.size)
    fields = DM_SUBATTR_SI30_HEADER_FORMAT.unpack_from(data, 0)
    attr = {'_absolute_offset': offset,
            'size': fields[0],
            'unknown0': fields[1],
            'header_rem_data': fields[2],
            'header_length': fields[4],
            'record_rem_data': fields[5],
            'record_rem_data_copy': fields[6],
            'unknown1': fields[7],
            'type': fields[8],
            '$I30': fields[9],
            '_structure_size': fields[0]}
    dump.seek(offset + attr['header_length'])
    # TODO: find what is at the end of the $I30
    return attr

def _dump_dm_si30_subattribute(attr, prefix=''):
    print('{}- size: {val:#x} ({val})'.format(prefix, val=attr['size']))
    print('{}- unknown field 0: {val:#x} ({val})'.format(prefix, val=attr['unknown0']))
    print('{}- header remaining bytes: {val:#x} ({val})'.format(prefix, val=attr['header_rem_data']))
    print('{}- header length: {val:#x} ({val})'.format(prefix, val=attr['header_length']))
    print('{}- record remaining data: {val:#x} ({val})'.format(prefix, val=attr['record_rem_data']))
    print('{}- record remaining data (copy?): {val:#x} ({val})'.format(prefix,
                                                                       val=attr['record_rem_data_copy']))
    print('{}- unknown field 1: {val:#x} ({val})'.format(prefix, val=attr['unknown1']))
    print('{}- type: {:#x} ($I30 type)'.format(prefix, attr['type']))
    print('{}- $I30 string: {}'.format(prefix, attr['$I30'].decode('utf-16le')))

DM_SUBATTR_FOLDER_HEADER_FORMAT = Struct('<LHHHHHH')
DM_SUBATTR_FOLDER_HEADER_2_FORMAT = Struct('<L')
DM_SUBATTR_FOLDER_HEADER_FORMAT = Struct('<LHHHHLLLL8s')

DM_SUBATTR_FOLDER_BODY_FORMAT = Struct('<LLHHQQQQQQ24sH')

DM_SUBATTR_TYPE_FOLDER = 0x00000038

def read_dm_folder_subattribute(dump, offset):
    dump.seek(offset)
    data = dump.read(DM_SUBATTR_FOLDER_HEADER_FORMAT.size)
    fields = DM_SUBATTR_FOLDER_HEADER_FORMAT.unpack_from(data, 0)
    attr = {'_absolute_offset': offset,
            'size': fields[0],
            'unknown0': fields[1],
            'header_rem_data': fields[2],
            'header_length': fields[4],
            'record_rem_data': fields[5],
            'record_rem_data_copy': fields[6],
            'unknown1': fields[7],
            'type': fields[8],
            '_structure_size': fields[0]}
    dump.seek(offset + attr['header_length'])
    data = dump.read(DM_SUBATTR_FOLDER_BODY_FORMAT.size)
    fields = DM_SUBATTR_FOLDER_BODY_FORMAT.unpack_from(data, 0)
    attr['parentid'] = fields[4]
    attr['created'] = fields[6]
    attr['modified'] = fields[7]
    attr['metadata_modified'] = fields[8]
    attr['last_accessed'] = fields[9]
    attr['name_size'] = fields[11]
    dump.seek(offset + attr['header_length'] + 0x5e)
    data = dump.read(attr['name_size'] * 2)
    attr['name'] = data
    return attr

def _dump_dm_folder_subattribute(attr, prefix=''):
    print('{}- size: {val:#x} ({val})'.format(prefix, val=attr['size']))
    print('{}- unknown field 0: {val:#x} ({val})'.format(prefix, val=attr['unknown0']))
    print('{}- header remaining bytes: {val:#x} ({val})'.format(prefix, val=attr['header_rem_data']))
    print('{}- header length: {val:#x} ({val})'.format(prefix, val=attr['header_length']))
    print('{}- record remaining data: {val:#x} ({val})'.format(prefix, val=attr['record_rem_data']))
    print('{}- record remaining data (copy?): {val:#x} ({val})'.format(prefix,
                                                                       val=attr['record_rem_data_copy']))
    print('{}- unknown field 1: {val:#x} ({val})'.format(prefix, val=attr['unknown1']))
    print('{}- type: {:#x} ($I30 type)'.format(prefix, attr['type']))
    print('{}- parent node id: {:#x}'.format(prefix, attr['parentid']))
    print('{}- created: {} ({})'.format(prefix,
                                        time.asctime(time.gmtime(attr['created']/10000000000)),
                                        attr['created']/10000000000))
    print('{}- modified: {} ({})'.format(prefix,
                                        time.asctime(time.gmtime(attr['modified']/10000000000)),
                                        attr['modified']/10000000000))
    print('{}- metadata modified: {} ({})'.format(prefix,
                                        time.asctime(time.gmtime(attr['metadata_modified']/10000000000)),
                                        attr['metadata_modified']/10000000000))
    print('{}- last accessed: {} ({})'.format(prefix,
                                        time.asctime(time.gmtime(attr['last_accessed']/10000000000)),
                                        attr['last_accessed']/10000000000))
    print('{}- folder name size: {val:#x} ({val})'.format(prefix, val=attr['name_size']))
    print('{}- folder name: {}'.format(prefix, attr['name'].decode('utf-16le')))

DM_SUBATTR_HEADER_FORMAT = Struct('<LHHHHLLLLL')

def read_directory_metadata_subattribute(dump, offset):
    dump.seek(offset, 0)
    data = dump.read(DM_SUBATTR_HEADER_FORMAT.size)
    header = DM_SUBATTR_HEADER_FORMAT.unpack_from(data, 0)
    if header[8] == DM_SUBATTR_TYPE_SI30:
        attr = read_dm_si30_subattribute(dump, offset)
    elif header[8] == DM_SUBATTR_TYPE_FOLDER:
        attr = read_dm_folder_subattribute(dump, offset)
    else:
        attr = {'_absolute_offset': offset,
                'size': header[0],
                'unknown0': header[1],
                'header_rem_data': header[2],
                'header_length': header[4],
                'record_rem_data': header[5],
                'record_rem_data_copy': header[6],
                'unknown1': header[7],
                'type': header[8]}
    return attr

def _dump_directory_metadata_subattribute(attr, prefix=''):
    if attr['type'] == DM_SUBATTR_TYPE_SI30:
        _dump_dm_si30_subattribute(attr, prefix)
    elif attr['type'] == DM_SUBATTR_TYPE_FOLDER:
        _dump_dm_folder_subattribute(attr, prefix)
    else:
        print('{}- size: {val:#x} ({val})'.format(prefix, val=attr['size']))
        print('{}- unknown field 0: {val:#x} ({val})'.format(prefix, val=attr['unknown0']))
        print('{}- header remaining bytes: {val:#x} ({val})'.format(prefix,
                                                                    val=attr['header_rem_data']))
        print('{}- header length: {val:#x} ({val})'.format(prefix, val=attr['header_length']))
        print('{}- record remaining data: {val:#x} ({val})'.format(prefix,
                                                                    val=attr['record_rem_data']))
        print('{}- record remaining data (copy?): {val:#x} ({val})'.format(prefix,
                                                                    val=attr['record_rem_data_copy']))
        print('{}- unknown field 1: {val:#x} ({val})'.format(prefix, val=attr['unknown1']))
        print('{}- type: {:#x} (unknown type)'.format(prefix, attr['type']))

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
    elif header2[0] == ATTR_TYPE_DIRECTORY_METADATA:
        attr = read_directory_metadata_attribute(dump, offset)
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
    elif attr['type'] == ATTR_TYPE_DIRECTORY_METADATA:
        _dump_directory_metadata_attribute(attr, prefix)
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
