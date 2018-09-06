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
    eb['num_extents'] = fields[2]
    eb['num_records'] = fields[4]
    eb['_structure_size'] = (eb['_structure_size'] +
                             eb['node_desc_length'])
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
    else:
        eb['pointers'] = None
        eb['pointers_data'] = None
    eb['_structure_size'] = (eb['_structure_size'] +
                             eb['header_length'])
    for ptr in eb['pointers']:
        ptr_addr = offset + eb['node_header_offset'] + ptr
        attr = rattr.read_attribute(dump, ptr_addr)
        eb['pointers_data'].append(attr)
        eb['_structure_size'] = eb['_structure_size'] + attr['size']
    return eb

def dump_entryblock(eb):
    print('Entryblock: <{:#x}> ({size},{size:#x})'.format(eb['_absolute_offset'],
                                                          size=eb['_structure_size']))
    print('- entryblock number: {:#x}'.format(eb['eb_number']))
    print('- counter: {}'.format(eb['counter']))
    print('- node id: {:#x}'.format(eb['node_id']))
    print('- node descriptor length: {val:#x} ({val})'.format(val=eb['node_desc_length']))
    print('- number of extents: {}'.format(eb['num_extents']))
    print('- number of records: {}'.format(eb['num_records']))
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
