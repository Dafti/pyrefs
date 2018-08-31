import argparse
import sys
from struct import Struct
import part.refs.entry_block as reb
import part.refs.tree_control as rtc
import part.refs.attribute as refs_attr
import part.refs.allocator as alloc
import part.refs.object_tree as rot
from util.hexdump import hexdump

SECTOR_SIZE = 512
ENTRYBLOCK_SIZE = 16 * 1024

def find_bytes(entry, block):
    hits = []
    for i in range(0, len(block) - (len(entry) - 1)):
        match = True
        for l in range(0, len(entry)):
            match = entry[l] == block[i + l]
            if not match:
                break
        if match:
            hits.append(i)
    return hits

def find_blocks(dump, offset, end, step):
    blocks = []
    for i in range(offset,end,step):
        dump.seek(i, 0)
        data = dump.read(4)
        entryblock, = ENTRYBLOCK_FORMAT.unpack_from(data, 0)
        if (i - offset) / step == entryblock:
        # if entryblock != 0:
        # if reb.is_entry_block(dump, i, offset):
            dump.seek(i+nodeid_offset,0)
            data = dump.read(4)
            nodeid, = NODEID_FORMAT.unpack_from(data, 0)
            dump.seek(i+childid_offset,0)
            data = dump.read(4)
            childid, = NODEID_FORMAT.unpack_from(data, 0)
            dump.seek(i+counter_offset, 0)
            counter = dump.read(1)[0]
            steps = int((i - offset) / step)
            block = {'offset': i, 'entryblock': entryblock,
                     'counter': counter, 'nodeid': nodeid,
                     'childid': childid}
            blocks.append(block)
    return blocks

def blocks_with_file_attributes(dump, blocks, block_size):
    blocks_found = []
    for block in blocks:
        dump.seek(block['offset'])
        data = dump.read(block_size)
        fileids = find_bytes([0x30,0,1,0], data)
        folderids = find_bytes([0x30,0,2,0], data)
        if fileids or folderids:
            block['fileids'] = [ x + block['offset'] - 0x10 for x in fileids ]
            block['folderids'] = [ x + block['offset'] - 0x10 for x in folderids ]
            blocks_found.append(block)
    return blocks_found

def blocks_with_child_attributes(dump, blocks, block_size):
    blocks_found = []
    for block in blocks:
        dump.seek(block['offset'])
        data = dump.read(block_size)
        ids = find_bytes([0x20,0,0,0x80], data)
        if ids:
            block['childids'] = [ x + block['offset'] - 0x10 for x in ids ]
            blocks_found.append(block)
    return blocks_found

parser = argparse.ArgumentParser(description='ReFS carving on provided dump.')
parser.add_argument('dump', action='store',
        type=argparse.FileType(mode='rb'))
args = parser.parse_args()

offset = 0x8100000
end = (41940991*512)+512 # complete partition
# end = offset + (20000 * 1024 * 16)
# end = 0x16d34000
step=16*1024
counter_offset=0x8
nodeid_offset=0x18
childid_offset=0x20
ENTRYBLOCK_FORMAT=Struct('<L')
NODEID_FORMAT=Struct('<L')

# blocks = find_blocks(args.dump, offset, end, step)
# print("==================================================================")
# print("Blocks found ({})".format(len(blocks)))
# print("==================================================================")
# for b in blocks:
#     print('{:#010x} - {:#010x}: {:#010x} {:>3} {:#010x} {:#010x}'.format(b['offset'],
#         b['offset'] + step, b['entryblock'], b['counter'], b['nodeid'], b['childid']))

# blocks_with_files = blocks_with_file_attributes(args.dump, blocks, step)
# print("==================================================================")
# print("Blocks found with files found")
# print("==================================================================")
# for b in blocks_with_files:
#     print('{:#010x} - {:#010x}: {:#06x} {:>3} {:#06x} {:#06x} {:4} {:4}'.format(b['offset'],
#         b['offset'] + step, b['entryblock'], b['counter'], b['nodeid'], b['childid'],
#         len(b['fileids']), len(b['folderids'])))
#
# print("==================================================================")
# print("Files found")
# print("==================================================================")
# for block in blocks_with_files:
#     for fid in block['fileids']:
#         attr = refs_attr.read_attribute(args.dump, fid)
#         try:
#             filename = attr['filename'].decode('utf-16le')
#         except:
#             filename = attr['filename']
#         print('{:#010x} {:#06x} {:#06x} {:#06x} {:#010x} {}'.format(
#             block['offset'], block['entryblock'],
#             block['nodeid'], block['childid'], attr['absolute_offset'], filename))
#
# print("==================================================================")
# print("Folders found")
# print("==================================================================")
# for block in blocks_with_files:
#     for fid in block['folderids']:
#         attr = refs_attr.read_attribute(args.dump, fid)
#         try:
#             foldername = attr['foldername'].decode('utf-16le')
#         except:
#             foldername = attr['foldername']
#         print('{:#010x} {:#06x} {:#06x} {:#06x} {:#010x} {}'.format(
#             block['offset'], block['entryblock'],
#             block['nodeid'], block['childid'], attr['absolute_offset'], foldername))
#
# blocks_with_child = blocks_with_child_attributes(args.dump, blocks, step)
# print("==================================================================")
# print("Blocks with child found")
# print("==================================================================")
# for b in blocks_with_child:
#     print('{:#010x} - {:#010x}: {:#06x} {:>3} {:#06x} {:#06x} {:4}'.format(b['offset'],
#         b['offset'] + step, b['entryblock'], b['counter'], b['nodeid'], b['childid'],
#         len(b['childids'])))
#     for oc in b['childids']:
#         attr = refs_attr.read_attribute(args.dump, oc)
#         if attr['000c'] != 0x000c:
#             print('False positive')
#         else:
#             try:
#                 attr['filename'] = attr['filename'].decode('utf-16le')
#             except:
#                 attr['filename'] = attr['filename']
#             print(attr)

addr = offset + (16 * 1024 * 0x1e)
tc = rtc.read_tree_control(args.dump, addr)
print(tc)
rtc.dump_tree_control(tc)
args.dump.seek(addr, 0)
data = args.dump.read(tc['tree_control_size'])
hexdump(data, addr)

# tree control copies
tc_c_addrs = [0x4fc0f4000, 0x4fc0f8000] 
print('')

addr = 0x4fc0f4000
tc = rtc.read_tree_control(args.dump, addr)
print(tc)
rtc.dump_tree_control(tc)
args.dump.seek(addr, 0)
data = args.dump.read(tc['tree_control_size'])
hexdump(data, addr)

print('')

addr = 0x4fc0f8000
tc = rtc.read_tree_control(args.dump, addr)
print(tc)
rtc.dump_tree_control(tc)
args.dump.seek(addr, 0)
data = args.dump.read(tc['tree_control_size'])
hexdump(data, addr)

print('')

tc_e = []
addr = offset + (16 * 1024 * tc['extent_pointers'][0])
tc_e.append(rtc.read_tree_control_ext(args.dump, addr))
print(tc_e[0])
rtc.dump_tree_control_ext(tc_e[0])
args.dump.seek(addr, 0)
data = args.dump.read(tc_e[0]['tree_control_ext_size'])
hexdump(data, addr)

print('')

addr = offset + (16 * 1024 * tc['extent_pointers'][1])
tc_e.append(rtc.read_tree_control_ext(args.dump, addr))
print(tc_e[1])
rtc.dump_tree_control_ext(tc_e[1])
args.dump.seek(addr, 0)
data = args.dump.read(tc_e[1]['tree_control_ext_size'])
hexdump(data, addr)

print('')

for i, rec in enumerate(tc_e[0]['records']):
    if i not in [0]:
        continue
    print('')

    addr = offset + (16 * 1024 * rec['eb_number'])
    ot = rot.read_object_tree(args.dump, addr)
    print(ot)
    rot.dump_object_tree(ot)
    args.dump.seek(addr, 0)
    data = args.dump.read(ot['_structure_size'])
    hexdump(data, addr)

print('')

for i, rec in enumerate(tc_e[0]['records']):
    if i not in [1, 2, 3]:
        continue
    print('')

    addr = offset + (16 * 1024 * rec['eb_number'])
    al = alloc.read_allocator(args.dump, addr)
    print(al)
    alloc.dump_allocator(al)
    args.dump.seek(addr, 0)
    data = args.dump.read(al['_structure_size'])
    # data = args.dump.read(16 * 1024)
    hexdump(data, addr)

for i, rec in enumerate(tc_e[0]['records']):
    if i not in [4,5]:
        continue
    print('')

    addr = offset + (16 * 1024 * rec['eb_number'])
    args.dump.seek(addr, 0)
    data = args.dump.read(16 * 1024)
    hexdump(data, addr)

args.dump.close()
