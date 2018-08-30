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
            counter=f.read(1)[0]
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
        fileids = find_bytes([0x30,0,1,0], block)
        folderids = find_bytes([0x30,0,2,0], block)
        block['fileids'] = [ x + block['offset'] - 0x10 for x in fileids ]
        block['folderids'] = [ x + block['offset'] - 0x10 for x in folderids ]
        blocks_found.append(block)
    return blocks_found

# tree_control_entryblock_addr = 0
# for i in range(offset,end,step):
#     f.seek(i, 0)
#     data = f.read(4)
#     entryblock,=ENTRYBLOCK_FORMAT.unpack_from(data, 0)
#     if entryblock != 0:
#         f.seek(i+nodeid_offset,0)
#         data=f.read(2)
#         nodeid,=NODEID_FORMAT.unpack_from(data, 0)
#         if nodeid == 0x0600:
#             tree_control_entryblock_addr = i
#         f.seek(i+childid_offset,0)
#         data = f.read(2)
#         childid,=NODEID_FORMAT.unpack_from(data, 0)
#         f.seek(i+counter_offset, 0)
#         counter=f.read(1)[0]
#         steps = int((i - offset) / step)
#         print('{:6} {:#010x} - {:#010x}: {:#06x} {:>3} {:#06x} {:#06x}'.format(steps, i, i+step, entryblock, counter, nodeid, childid))
        # f.seek(i,0)
        # block = f.read(step)
        # fileids = find_bytes([0x30,0,1,0], block)
        # folderids = find_bytes([0x30,0,2,0], block)
        # print('{:6} {:#010x} - {:#010x}: {:#06x} {:>3} {:#06x} {:#06x} {:2} {:2}'.format(steps, i, i+step, entryblock, counter, nodeid, childid, len(fileids), len(folderids)))
        # if fileids:
        #     print('{:6} {:10}   {:10}  fileids = {}'.format('', '', '', fileids))
        # if folderids:
        #     print('{:6} {:10}   {:10}  forderids = {}'.format('', '', '', folderids))

f = open('resilient_fs.raw.001', 'rb')

offset=0x8100000
end=0x16d00000
step=16*1024
counter_offset=0x8
nodeid_offset=0x18
childid_offset=0x20
ENTRYBLOCK_FORMAT=Struct('<H')
NODEID_FORMAT=Struct('<H')

blocks = find_blocks(f, offset, end, step)
print("==================================================================")
print("Blocks found")
print("==================================================================")
for b in blocks:
    print('{:#010x} - {:#010x}: {:#06x} {:>3} {:#06x} {:#06x}'.format(b['offset'],
        b['offset'] + step, b['entryblock'], b['counter'], b['nodeid'], b['childid']))

# print("Tree control entry block address = {:#x}".format(tree_control_entryblock_addr))
# 
# f.seek(tree_control_entryblock_addr,0)
# block = f.read(step)
# fileids = find_bytes([0x30,0,1,0], block)
# if fileids:
#     print('  fileids = {}'.format(fileids))
#     for fid in fileids:
#         attr = refs_attr.read_attribute(f, tree_control_entryblock_addr + fid - 0x10)
#         print('{:#010x} {}'.format(attr['type'], attr['filename'].decode('utf-16le')))
# folderids = find_bytes([0x30,0,2,0], block)
# if folderids:
#     print('  folderids = "{}"'.format(folderids))
#     for fid in folderids:
#         attr = refs_attr.read_attribute(f, tree_control_entryblock_addr + fid - 0x10)
#         print('{:#010x} "{}"'.format(attr['type'], attr['foldername'].decode('utf-16le')))
 
f.close()
