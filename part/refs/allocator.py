from struct import Struct

AL_HEADER_FORMAT = Struct('<Q40sL28sL20sLLLLLLQ')

def read_allocator(dump, offset):
    dump.seek(offset, 0)
    data = dump.read(AL_HEADER_FORMAT.size)
    fields = AL_HEADER_FORMAT.unpack_from(data, 0)
    al = {'absolute_offset': offset,
          'eb_number': fields[0],
          'node_length': fields[2],
          'num_records_in_node': fields[4],
          'node_header_length': fields[6],
          'offset_next_free_rec': fields[7],
          'free_space': fields[8],
          'node_header_unknown': fields[9],
          'offset_first_ptr': fields[10],
          'num_ptrs_in_node': fields[11],
          'offset_end_node': fields[12]}
    al['_structure_size'] = AL_HEADER_FORMAT.size
    return al

def dump_allocator(al):
    print('Allocator {:#x} ({size},{size:#x}):'.format(al['absolute_offset'], size=al['_structure_size']))
    print('- entryblock number: {:#x}'.format(al['eb_number']))
    print('- node descriptor length: {val:#x} ({val})'.format(val=al['node_length']))
    print('- number of records in node: {}'.format(al['num_records_in_node']))
    print('- offset to next free record: {val:#x} ({val})'.format(val=al['offset_next_free_rec']))
    print('- free space in node: {val:#x} ({val})'.format(val=al['free_space']))
    print('- <node header unknown>: {val:#x} ({val})'.format(val=al['node_header_unknown']))
    print('- offset to first pointer: {val:#x} ({val})'.format(val=al['offset_first_ptr']))
    print('- number of pointers in this node: {}'.format(al['num_ptrs_in_node']))
    print('- offset to end of node: {val:#x} ({val})'.format(val=al['offset_end_node']))


