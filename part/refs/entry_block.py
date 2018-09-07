from struct import Struct
import part.refs.attribute as rattr

SECTOR_SIZE = 512
ENTRYBLOCK_SIZE = 16 * 1024

EB_NUM_OFFSET = 0
EB_OWN_OFFSET_OFFSET = 0x38
EB_LENGTH_OWN_OFFSET_OFFSET = 0x3c
EB_NUM_POINTERS_EXTENT_OFFSET = 0x58
EB_NUM_SIZE = 8
EB_OWN_OFFSET_SIZE = 4
EB_LENGTH_OWN_OFFSET_SIZE = 4
EB_NUM_POINTERS_EXTENT_SIZE = 4

EB_HEADER_FORMAT = Struct('<QQ8sQ16s')
EB_NODE_DESC_FORMAT = Struct('<L20sH6sL')
EB_NODE_HEADER_FORMAT = Struct('<LLLLLLQ')

EB_EXTENT_TABLE_FORMAT = Struct('<LLLLLLLL')

def is_entryblock(dump, offset, vbr_offset, block_size = 16 * 1024):
    dump.seek(offset, 0)
    data = dump.read(EB_HEADER_FORMAT.size)
    eb_num = EB_HEADER_FORMAT.unpack_from(data, 0)
    return (offset - vbr_offset) / block_size == eb_num[0]
    # return eb_num != 0

def read_entryblock(dump, offset):
    dump.seek(offset, 0)
    data = dump.read(EB_HEADER_FORMAT.size)
    fields = EB_HEADER_FORMAT.unpack_from(data, 0)
    eb = {'_absolute_offset': offset,
          'eb_number': fields[0],
          'counter': fields[1],
          'node_id': fields[3]}
    eb['_structure_size'] = EB_HEADER_FORMAT.size
    data = dump.read(EB_NODE_DESC_FORMAT.size)
    fields = EB_NODE_DESC_FORMAT.unpack_from(data, 0)
    eb['node_desc_length'] = fields[0]
    if eb['node_desc_length'] != 0x08:
        eb['num_extents'] = fields[2]
        eb['num_records'] = fields[4]
    eb['_structure_size'] = (eb['_structure_size'] +
                             eb['node_desc_length'])
    eb['_contains_records'] = False
    eb['_contains_extents'] = False
    if (eb['node_desc_length'] == 0x08 or
            eb['num_extents'] == 0):
        eb['_contains_records'] = True
        eb['node_header_offset'] = eb['_structure_size']
        dump.seek(offset + eb['_structure_size'], 0)
        data = dump.read(EB_NODE_HEADER_FORMAT.size)
        fields = EB_NODE_HEADER_FORMAT.unpack_from(data, 0)
        eb['header_length'] = fields[0]
        eb['offset_free_record'] = fields[1]
        eb['free_space'] = fields[2]
        eb['header_unknown'] = fields[3]
        eb['offset_first_pointer'] = fields[4]
        eb['num_pointers'] = fields[5]
        eb['offset_end_node'] = fields[6]
        if eb['num_pointers']:
            pointers_format = Struct('<' + ('L' * eb['num_pointers']))
            dump.seek(offset + eb['node_header_offset'] + eb['offset_first_pointer'], 0)
            data = dump.read(pointers_format.size)
            fields = pointers_format.unpack_from(data, 0)
            eb['pointers'] = fields
            eb['pointers_data'] = []
            for ptr in eb['pointers']:
                ptr_addr = offset + eb['node_header_offset'] + ptr
                attr = rattr.read_attribute(dump, ptr_addr)
                eb['pointers_data'].append(attr)
                eb['_structure_size'] = eb['_structure_size'] + attr['size']
        else:
            eb['pointers'] = None
            eb['pointers_data'] = None
        eb['_structure_size'] = (eb['_structure_size'] +
                                 eb['header_length'])
    elif (eb['node_desc_length'] != 0x08 and eb['num_extents'] != 0):
        eb['_contains_extents'] = True
        eb['extent_table_offset'] = eb['_structure_size']
        dump.seek(offset + eb['_structure_size'], 0)
        data = dump.read(EB_EXTENT_TABLE_FORMAT.size)
        fields = EB_EXTENT_TABLE_FORMAT.unpack_from(data, 0)
        eb['extent_table_length'] = fields[0]
        eb['extent_table_unknown0'] = fields[1]
        eb['extent_table_unknown1'] = fields[2]
        eb['extent_table_unknown2'] = fields[3]
        eb['offset_first_extent_pointer'] = fields[4]
        eb['num_extent_pointers'] = fields[5]
        eb['offset_end_of_extent_pointers'] = fields[6]
        eb['extent_table_unknown3'] = fields[7]
        eb['_structure_size'] = eb['_structure_size'] + eb['extent_table_length']
        pointers_format = Struct('<' + ('L' * eb['num_extent_pointers']))
        dump.seek(offset + eb['extent_table_offset'] + eb['offset_first_extent_pointer'], 0)
        data = dump.read(pointers_format.size)
        fields = pointers_format.unpack_from(data, 0)
        eb['extent_pointers'] = fields
        eb['extents'] = []
        for ptr in eb['extent_pointers']:
            ptr_addr = offset + eb['extent_table_offset'] + ptr
            ext = _read_extent(dump, ptr_addr)
            eb['extents'].append(ext)
            eb['_structure_size'] = eb['_structure_size'] + ext['_structure_size']
    return eb

EB_EXTENT_HEADER_FORMAT = Struct('<LLHHH')
EB_EXTENT_BODY_FORMAT = Struct('<QQQ')

def _read_extent(dump, offset):
    dump.seek(offset)
    data = dump.read(EB_EXTENT_HEADER_FORMAT.size)
    fields = EB_EXTENT_HEADER_FORMAT.unpack_from(data, 0)
    ext = {'_absolute_offset': offset,
           'size': fields[0],
           'unknown0': fields[1],
           'unknown1': fields[2],
           'header_length': fields[3],
           'body_length': fields[4],
           '_structure_size': fields[0]}
    dump.seek(offset + ext['header_length'])
    data = dump.read(EB_EXTENT_BODY_FORMAT.size)
    fields = EB_EXTENT_BODY_FORMAT.unpack_from(data, 0)
    ext['eb_number'] = fields[0]
    ext['0x0000000808020000'] = fields[1]
    ext['crc'] = fields[2]
    return ext

def dump_entryblock(eb):
    print('Entryblock: <{:#x}> ({size},{size:#x})'.format(eb['_absolute_offset'],
                                                          size=eb['_structure_size']))
    print('- entryblock number: {:#x}'.format(eb['eb_number']))
    print('- counter: {}'.format(eb['counter']))
    print('- node id: {:#x}'.format(eb['node_id']))
    print('- node descriptor length: {val:#x} ({val})'.format(val=eb['node_desc_length']))
    if 'num_extents' in eb:
        print('- number of extents: {}'.format(eb['num_extents']))
    if 'num_records' in eb:
        print('- number of records: {}'.format(eb['num_records']))
    if eb['_contains_records']:
        print('- node header offset: {val:#x} ({val})'.format(val=eb['node_header_offset']))
        print('- node header length: {val:#x} ({val})'.format(val=eb['header_length']))
        print('- offset to next free record: {val:#x} ({val})'.format(val=eb['offset_free_record']))
        print('- free space in node: {val:#x} ({val})'.format(val=eb['free_space']))
        print('- node header unknown: {val:#x} ({val})'.format(val=eb['header_unknown']))
        print('- offset to first pointer: {val:#x} ({val}) -> entryblock offset: {ebo:#x}'.format(
            val=eb['offset_first_pointer'],
            ebo=eb['offset_first_pointer']+eb['node_header_offset']))
        print('- number of pointers in node: {}'.format(eb['num_pointers']))
        print('- offset to end node: {val:#x} ({val}) -> entryblock offset: {ebo:#x}'.format(
            val=eb['offset_end_node'],
            ebo=eb['offset_end_node']+eb['node_header_offset']))
        print('- pointers:', end='')
        if eb['pointers']:
            for ptr in eb['pointers']:
                print(' {:#x}'.format(ptr), end='')
            print('')
            print('- pointers data:')
            for ptr_i, ptr in enumerate(eb['pointers_data']):
                print('  - pointer {}: <{:#x}>'.format(ptr_i, ptr['_absolute_offset']))
                rattr.dump_attribute(ptr, '    ')
        else:
            print('None')
            print('- pointers data: None')
    elif eb['_contains_extents']:
        print('- extent table offset: {val:#x} ({val})'.format(val=eb['extent_table_offset']))
        print('- extent table length: {val:#x} ({val})'.format(val=eb['extent_table_length']))
        print('- extent table unknown 0: {val:#x} ({val})'.format(val=eb['extent_table_unknown0']))
        print('- extent table unknown 1: {val:#x} ({val})'.format(val=eb['extent_table_unknown1']))
        print('- extent table unknown 2: {val:#x} ({val})'.format(val=eb['extent_table_unknown2']))
        print('- offset to first extent pointer: {val:#x} ({val})'.format(
            val=eb['offset_first_extent_pointer']))
        print('- number of extent pointers: {}'.format(eb['num_extent_pointers']))
        print('- offset en of extent pointers: {val:#x} ({val})'.format(
            val=eb['offset_end_of_extent_pointers']))
        print('- extent table unknown 3: {val:#x} ({val})'.format(val=eb['extent_table_unknown3']))
        print('- extent pointers:', end='')
        for ptr in eb['extent_pointers']:
            print(' {:#x}'.format(ptr), end='')
        print('')
        print('- extents:')
        for ext_i, ext in enumerate(eb['extents']):
            print('  - extent {}: <{:#x}>'.format(ext_i, ext['_absolute_offset']))
            _dump_extent(ext, '    ')

def _dump_extent(ext, prefix):
    print('{}- size: {val:#x} ({val})'.format(prefix, val=ext['size']))
    print('{}- unknown 0: {val:#x} ({val})'.format(prefix, val=ext['unknown0']))
    print('{}- unknown 1: {val:#x} ({val})'.format(prefix, val=ext['unknown1']))
    print('{}- header length: {val:#x} ({val})'.format(prefix, val=ext['header_length']))
    print('{}- body length: {val:#x} ({val})'.format(prefix, val=ext['body_length']))
    print('{}- entryblock id: {val:#x} ({val})'.format(prefix, val=ext['eb_number']))
    print('{}- 0x0000000808020000: {:#018x}'.format(prefix, ext['0x0000000808020000']))
    print('{}- crc(?): {:#018x}'.format(prefix, ext['crc']))
