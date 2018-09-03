from struct import Struct

OBJ_HEADER_1_FORMAT = Struct('<Q40sL28sL') # entryblock and node descriptor
OBJ_HEADER_2_FORMAT = Struct('<LLLLLLQ') # node header
OBJ_HEADER_3_FORMAT = Struct('<L20sQQ8sQ') # record

OBJ_NODE_DESC_OFFSET = 0x30

def read_object(dump, offset):
    dump.seek(offset, 0)
    data = dump.read(OBJ_HEADER_1_FORMAT.size)
    fields = OBJ_HEADER_1_FORMAT.unpack_from(data, 0)
    obj = {'_absolute_offset': offset,
           'eb_number': fields[0],
           'node_desc_length': fields[2],
           'num_records_in_node': fields[4]}
    node_header_offset = offset + OBJ_NODE_DESC_OFFSET + obj['node_desc_length']
    dump.seek(node_header_offset)
    data = dump.read(OBJ_HEADER_2_FORMAT.size)
    fields = OBJ_HEADER_2_FORMAT.unpack_from(data, 0)
    obj['node_header_length'] = fields[0]
    obj['offset_next_free_rec'] = fields[1]
    obj['free_space'] = fields[2]
    obj['node_header_unknown'] = fields[3]
    obj['offset_first_ptr'] = fields[4]
    obj['num_ptrs_in_node'] = fields[5]
    obj['offset_end_node'] = fields[6]
    record_offset = node_header_offset + ot['node_header_length']
    obj['records_offset'] = record_offset
    records = []
    for rec_i in range(ot['num_records_in_node']):
        dump.seek(record_offset)
        data = dump.read(OT_HEADER_3_FORMAT.size)
        fields = OT_HEADER_3_FORMAT.unpack_from(data, 0)
        rec = {'record_length': fields[0],
               'nodeid': fields[2],
               'eb_num': fields[3],
               'id': fields[5]}
        records.append(rec)
        record_offset = record_offset + rec['record_length']
    ot['records'] = records
    ot['_structure_size'] = record_offset - offset
    return ot


