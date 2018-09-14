import argparse
import sys
from struct import Struct
import part.refs.entry_block as reb
import part.refs.tree_control as rtc
import part.refs.attribute as refs_attr
import part.refs.allocator as alloc
import part.refs.object_tree as rot
from util.hexdump import hexdump
from util.table import print_table

SECTOR_SIZE = 512
ENTRYBLOCK_SIZE = 16 * 1024
CLUSTER_SIZE = 4 * ENTRYBLOCK_SIZE
counter_offset=0x8
nodeid_offset=0x18
childid_offset=0x20
ENTRYBLOCK_FORMAT=Struct('<Q')
NODEID_FORMAT=Struct('<Q')

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

def find_blocks(dump, lba_offset, lba_end, step = ENTRYBLOCK_SIZE):
    offset = lba_offset * SECTOR_SIZE
    end = lba_end * SECTOR_SIZE
    blocks = []
    for i in range(offset,end,step):
        dump.seek(i, 0)
        data = dump.read(8)
        entryblock, = ENTRYBLOCK_FORMAT.unpack_from(data, 0)
        if reb.is_entryblock(dump, i, offset):
            dump.seek(i+nodeid_offset,0)
            data = dump.read(8)
            nodeid, = NODEID_FORMAT.unpack_from(data, 0)
            dump.seek(i+childid_offset,0)
            data = dump.read(8)
            childid, = NODEID_FORMAT.unpack_from(data, 0)
            dump.seek(i+counter_offset, 0)
            counter = dump.read(1)[0]
            steps = int((i - offset) / step)
            block = {'offset': i, 'entryblock': entryblock,
                     'counter': counter, 'nodeid': nodeid,
                     'childid': childid, 'fnas': None,
                     'folderids': None}
            blocks.append(block)
    return blocks

def find_data_blocks_with_pattern(dump, pattern, lba_offset, lba_end, step=ENTRYBLOCK_SIZE):
    offset = lba_offset * SECTOR_SIZE
    end = lba_end * SECTOR_SIZE
    block_offsets = []
    for i in range(offset,end,step):
        dump.seek(i, 0)
        data = dump.read(128)
        addrs = find_bytes(pattern, data)
        if addrs:
            block_offsets.append({'block_offset': int((i - lba_offset)/step),
                                  'addr': i,
                                  'lba_offset': int((i - lba_offset)/SECTOR_SIZE)})
    return block_offsets

def print_blocks(blocks):
    columns = [ {'key': 'offset', 'header': 'Offset', 'align': '<', 'format': '#x'},
                {'key': 'entryblock', 'header': 'Entryblock', 'align': '<', 'format': '#x'},
                {'key': 'nodeid', 'header': 'NodeId', 'align': '<', 'format': '#x'},
                {'key': 'childid', 'header': 'ChildId', 'align': '<', 'format': '#x'},
                {'key': 'counter', 'header': 'Counter', 'align': '>'},
                {'key': 'fnas', 'header': 'FNAs', 'align': '>',
                 'transform': lambda x: 'N/A' if x == None else len(x)},
                {'key': 'folderids', 'header': 'Folders', 'align': '>',
                 'transform': lambda x: 'N/A' if x == None else len(x)} ]
    if blocks:
        print_table(columns, blocks)

def blocks_with_filename_attributes(dump, blocks, block_size = ENTRYBLOCK_SIZE):
    blocks_found = []
    for block in blocks:
        dump.seek(block['offset'])
        data = dump.read(block_size)
        fileids = find_bytes([0x30,0,1,0], data)
        if fileids:
            block['fnas'] = [ x + block['offset'] - 0x10 for x in fileids ]
            blocks_found.append(block)
        else:
            block['fnas'] = []
    return blocks_found

def blocks_with_folder_attributes(dump, blocks, block_size = ENTRYBLOCK_SIZE):
    blocks_found = []
    for block in blocks:
        dump.seek(block['offset'], 0)
        data = dump.read(block_size)
        _folderids = find_bytes([0x30,0,2,0], data)
        folderids = []
        # this loop tries to check that the pattern found is in a filename_folder
        # attribute
        # TODO: find a better way to determine if the pattern is in a filename_folder
        # attribute or in a folder attribute
        for fid in _folderids:
            dump.seek(fid + block['offset'] - 0x10 + 0x4, 0)
            data = dump.read(2)
            offset = data[0] + (data[1] * 256)
            if offset == 0x10:
                folderids.append(fid)
        if folderids:
            block['folderids'] = [ x + block['offset'] - 0x10 for x in folderids ]
            blocks_found.append(block)
        else:
            block['folderids'] = []
    return blocks_found

def blocks_with_child_attributes(dump, blocks, block_size = ENTRYBLOCK_SIZE):
    blocks_found = []
    for block in blocks:
        dump.seek(block['offset'])
        data = dump.read(block_size)
        ids = find_bytes([0x20,0,0,0x80], data)
        if ids:
            block['childids'] = [ x + block['offset'] - 0x10 for x in ids ]
            blocks_found.append(block)
    return blocks_found
