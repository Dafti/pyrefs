from struct import Struct

OT_HEADER_1_FORMAT = Struct('<QQ8sQ16sL28sL') # entryblock and node descriptor
OT_HEADER_2_FORMAT = Struct('<LLLLLLQ') # node header
OT_HEADER_3_FORMAT = Struct('<L20sQQ8sQ') # record

OT_NODE_DESC_OFFSET = 0x30

def read_object_tree(dump, offset):
    dump.seek(offset, 0)
    data = dump.read(OT_HEADER_1_FORMAT.size)
    fields = OT_HEADER_1_FORMAT.unpack_from(data, 0)
    ot = {'_dump_offset': offset,
          '_absolute_offset': offset,
          'eb_number': fields[0],
          'counter': fields[1],
          'node_id': fields[3],
          'node_desc_length': fields[5],
          'num_records_in_node': fields[7]}
    node_header_offset = offset + OT_NODE_DESC_OFFSET + ot['node_desc_length']
    dump.seek(node_header_offset)
    data = dump.read(OT_HEADER_2_FORMAT.size)
    fields = OT_HEADER_2_FORMAT.unpack_from(data, 0)
    ot['node_header_length'] = fields[0]
    ot['offset_next_free_rec'] = fields[1]
    ot['free_space'] = fields[2]
    ot['node_header_unknown'] = fields[3]
    ot['offset_first_ptr'] = fields[4]
    ot['num_ptrs_in_node'] = fields[5]
    ot['offset_end_node'] = fields[6]
    record_offset = node_header_offset + ot['node_header_length']
    ot['records_offset'] = record_offset - offset
    records = []
    for rec_i in range(ot['num_records_in_node']):
        dump.seek(record_offset, 0)
        data = dump.read(OT_HEADER_3_FORMAT.size)
        fields = OT_HEADER_3_FORMAT.unpack_from(data, 0)
        rec = {'record_length': fields[0],
               'nodeid': fields[2],
               'eb_num': fields[3],
               'id': fields[5],
               '_record_offset': record_offset - offset}
        records.append(rec)
        record_offset = record_offset + rec['record_length']
    ot['records'] = records
    ot['_structure_size'] = record_offset - offset
    return ot

def dump_object_tree(ot):
    print('Object tree: <{:#x}> ({size},{size:#x})'.format(ot['_absolute_offset'], size=ot['_structure_size']))
    print('- entryblock number: {:#x}'.format(ot['eb_number']))
    print('- counter: {}'.format(ot['counter']))
    print('- node id: {:#x}'.format(ot['node_id']))
    print('- node descriptor length: {val:#x} ({val})'.format(val=ot['node_desc_length']))
    print('- number of records in node: {}'.format(ot['num_records_in_node']))
    print('- offset to next free record: {val:#x} ({val})'.format(val=ot['offset_next_free_rec']))
    print('- free space in node: {val:#x} ({val})'.format(val=ot['free_space']))
    print('- <node header unknown>: {val:#x} ({val})'.format(val=ot['node_header_unknown']))
    print('- offset to first pointer: {val:#x} ({val})'.format(val=ot['offset_first_ptr']))
    print('- number of pointers in this node: {}'.format(ot['num_ptrs_in_node']))
    print('- offset to end of node: {val:#x} ({val})'.format(val=ot['offset_end_node']))
    if ot['records']:
        print('- records: <{:#x}>'.format(ot['records_offset']))
        for i, rec in enumerate(ot['records']):
            print('  - record {}: <{:#x}>'. format(i, rec['_record_offset']))
            print('    - record length: {val:#x} ({val})'.format(val=rec['record_length']))
            print('    - node id: {:#x}'.format(rec['nodeid']))
            print('    - entryblock number: {:#x}'.format(rec['eb_num']))
            print('    - identifier(?): {:#x}'.format(rec['id']))
