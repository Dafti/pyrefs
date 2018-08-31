from struct import Struct

AL_HEADER_FORMAT = Struct('<QQ8sQ16sL28sL20sLLLLLLQ')

def read_allocator(dump, offset):
    dump.seek(offset, 0)
    data = dump.read(AL_HEADER_FORMAT.size)
    fields = AL_HEADER_FORMAT.unpack_from(data, 0)
    al = {'absolute_offset': offset,
          'eb_number': fields[0],
          'counter': fields[1],
          'node_id': fields[3],
          'node_desc_length': fields[5],
          'num_records_in_node': fields[7],
          'node_header_length': fields[9],
          'offset_next_free_rec': fields[10],
          'free_space': fields[11],
          'node_header_unknown': fields[12],
          'offset_first_ptr': fields[13],
          'num_ptrs_in_node': fields[14],
          'offset_end_node': fields[15]}
    al['_structure_size'] = AL_HEADER_FORMAT.size
    return al

def dump_allocator(al):
    print('Allocator {:#x} ({size},{size:#x}):'.format(al['absolute_offset'], size=al['_structure_size']))
    print('- entryblock number: {:#x}'.format(al['eb_number']))
    print('- counter: {}'.format(al['counter']))
    print('- node id: {:#x}'.format(al['node_id']))
    print('- node descriptor length: {val:#x} ({val})'.format(val=al['node_desc_length']))
    print('- number of records in node: {}'.format(al['num_records_in_node']))
    print('- offset to next free record: {val:#x} ({val})'.format(val=al['offset_next_free_rec']))
    print('- free space in node: {val:#x} ({val})'.format(val=al['free_space']))
    print('- <node header unknown>: {val:#x} ({val})'.format(val=al['node_header_unknown']))
    print('- offset to first pointer: {val:#x} ({val})'.format(val=al['offset_first_ptr']))
    print('- number of pointers in this node: {}'.format(al['num_ptrs_in_node']))
    print('- offset to end of node: {val:#x} ({val})'.format(val=al['offset_end_node']))
