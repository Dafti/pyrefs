import argparse
from struct import Struct
import part.refs.attribute as refs_attr

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
        entryblock,=ENTRYBLOCK_FORMAT.unpack_from(data, 0)
        if entryblock != 0:
            dump.seek(i+nodeid_offset,0)
            data = dump.read(2)
            nodeid, = NODEID_FORMAT.unpack_from(data, 0)
            dump.seek(i+childid_offset,0)
            data = dump.read(2)
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

offset=0x8100000
end=0x16d00000
step=16*1024
counter_offset=0x8
nodeid_offset=0x18
childid_offset=0x20
ENTRYBLOCK_FORMAT=Struct('<H')
NODEID_FORMAT=Struct('<H')

blocks = find_blocks(args.dump, offset, end, step)
print("==================================================================")
print("Blocks found")
print("==================================================================")
for b in blocks:
    print('{:#010x} - {:#010x}: {:#06x} {:>3} {:#06x} {:#06x}'.format(b['offset'],
        b['offset'] + step, b['entryblock'], b['counter'], b['nodeid'], b['childid']))

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

blocks_with_child = blocks_with_child_attributes(args.dump, blocks, step)
print("==================================================================")
print("Blocks with child found")
print("==================================================================")
for b in blocks_with_child:
    print('{:#010x} - {:#010x}: {:#06x} {:>3} {:#06x} {:#06x} {:4}'.format(b['offset'],
        b['offset'] + step, b['entryblock'], b['counter'], b['nodeid'], b['childid'],
        len(b['childids'])))
    for oc in b['childids']:
        attr = refs_attr.read_attribute(args.dump, oc)
        if attr['000c'] != 0x000c:
            print('False positive')
        else:
            try:
                attr['filename'] = attr['filename'].decode('utf-16le')
            except:
                attr['filename'] = attr['filename']
            print(attr)

args.dump.close()
