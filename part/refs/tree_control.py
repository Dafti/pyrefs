from struct import Struct

TC_HEADER_FORMAT = Struct('<Q72sLLLL')
TC_EXTENT_POINTER_FORMAT = Struct('<Q')

def read_tree_control(dump, offset):
    dump.seek(offset, 0)
    data = dump.read(TC_HEADER_FORMAT.size)
    fields = TC_HEADER_FORMAT.unpack_from(data, 0)
    tc = {'absolute_offset': offset,
          'eb_number': fields[0],
          'offset_extents': fields[2],
          'num_extents': fields[3],
          'offset_record': fields[4],
          'length_record': fields[5]}
    e_pts = []
    for i in range(tc['num_extents']):
        e_offset = tc['offset_extents'] + (i * TC_EXTENT_POINTER_FORMAT.size)
        dump.seek(offset + e_offset, 0)
        data = dump.read(TC_EXTENT_POINTER_FORMAT.size)
        e_pt, = TC_EXTENT_POINTER_FORMAT.unpack_from(data, 0)
        e_pts.append(e_pt)
    tc['extent_pointers'] = e_pts
    tc['tree_control_size'] = tc['offset_record'] + tc['length_record']
    return tc

def dump_tree_control(tc):
    print('Tree control {:#x} ({size},{size:#x}):'.format(tc['absolute_offset'], size=tc['tree_control_size']))
    print('- entryblock number: {:#x}'.format(tc['eb_number']))
    print('- offset of extents: {val:#x} ({val})'.format(val=tc['offset_extents']))
    print('- number of extents: {}'.format(tc['num_extents']))
    print('- offset of record: {val:#x} ({val})'.format(val=tc['offset_record']))
    print('- length of record: {val:#x} ({val})'.format(val=tc['length_record']))
    if tc['extent_pointers']:
        print('- extent pointers: ', end='')
        for pt in tc['extent_pointers']:
            print('{:#x} '.format(pt), end='')
        print('')

TC_EXT_HEADER_FORMAT = Struct('<Q52sL24sL')
TC_EXT_RECORD_PTR_FORMAT = Struct('<L')
TC_EXT_RECORD_OFFSET = 0x98

def read_tree_control_ext(dump, offset):
    dump.seek(offset, 0)
    data = dump.read(TC_EXT_HEADER_FORMAT.size)
    fields = TC_EXT_HEADER_FORMAT.unpack_from(data, 0)
    tc_e = {'absolute_offset': offset,
            'eb_number': fields[0],
            'length_record': fields[2],
            'num_records': fields[4]}
    r_pts = []
    for i in range(tc_e['num_records']):
        r_offset = TC_EXT_HEADER_FORMAT.size + (i * TC_EXT_RECORD_PTR_FORMAT.size)
        dump.seek(offset + r_offset, 0)
        data = dump.read(TC_EXT_RECORD_PTR_FORMAT.size)
        r_pt, = TC_EXT_RECORD_PTR_FORMAT.unpack_from(data, 0)
        r_pts.append(r_pt)
    tc_e['record_offsets'] = r_pts
    recs = []
    for _rec_offset in tc_e['record_offsets']:
        rec_offset = offset + _rec_offset
        dump.seek(rec_offset, 0)
        data = dump.read(tc_e['length_record'])
        recs.append(data)
    tc_e['records'] = recs
    tc_e['tree_control_ext_size'] = TC_EXT_RECORD_OFFSET + (tc_e['num_records'] * tc_e['length_record'])
    return tc_e

def dump_tree_control_ext(tc_e):
    print('Tree control extension {:#x} ({size},{size:#x}):'.format(tc_e['absolute_offset'], size=tc_e['tree_control_ext_size']))
    print('- entryblock number: {:#x}'.format(tc_e['eb_number']))
    print('- length of record: {val:#x} ({val})'.format(val=tc_e['length_record']))
    print('- num_records: {}'.format(tc_e['num_records']))
    if tc_e['record_offsets']:
        print('- record offsets: ', end='')
        for pt in tc_e['record_offsets']:
            print('{:#x} '.format(pt), end='')
        print('')
