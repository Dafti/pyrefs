from struct import unpack, Struct
from binascii import hexlify

SECTOR_SIZE = 512
GPT_HEADER_OFFSET = 0
GPT_HEADER_SIZE = SECTOR_SIZE    
GPT_HEADER_SIGNATURE = b'EFI PART'

'''
0 signature 
8 version, L
12 size, L
16 CRC32, L
20 L
24 header LBA, Q
'''
GPT_HEADER_FORMAT = Struct('<8sLLLLQQQQ16sQLLL')
GPT_PART_FORMAT = Struct('<16s16sQQQ72s')

GUID_LE_FORMAT = Struct('<LHH')
GUID_BG_FORMAT = Struct('>HHL')
GUID_UNUSED_PART_STRING = '00000000-0000-0000-0000-000000000000'
GUID_PART_TYPE_W_BASIC_DATA_PART = 'ebd0a0a2-b9e5-4433-87c0-68b6b72699c7'
GUID_PART_TYPE_W_MS_RESV_PART = 'e3c9e316-0b5c-4db8-817d-f92df00215ae'
GUID_TRANSLATION = {
    GUID_PART_TYPE_W_MS_RESV_PART: 'Windows - Microsoft Reserved Partition',
    GUID_PART_TYPE_W_BASIC_DATA_PART: 'Windows - Basic data partition'
    }

def guid_string(guid):
    _guid_le = GUID_LE_FORMAT.unpack_from(guid, 0)
    _guid_bg = GUID_BG_FORMAT.unpack_from(guid, 8)
    res = '{:08x}-{:04x}-{:04x}-{:04x}-{:04x}{:08x}'.format(
            _guid_le[0], _guid_le[1], _guid_le[2],
            _guid_bg[0], _guid_bg[1], _guid_bg[2])
    return res

def _gpt_init(header):
    gpt = {'signature': header[0],
           'revision': header[1],
           'header_size': header[2],
           'header_crc': header[3],
           'cur_lba': header[5],
           'bkp_lba': header[6],
           'first_lba': header[7],
           'last_lba': header[8],
           'disk_guid': guid_string(header[9]),
           'part_lba': header[10],
           'npart': header[11],
           'part_size': header[12],
           'part_crc': header[13]
           }
    return gpt

def _gpt_add_partitions(gpt, part_list):
    gpt['parts'] = part_list

def _gpt_part_init(entry, index):
    part = {'index': index,
            'type': guid_string(entry[0]),
            'guid': guid_string(entry[1]),
            'first_lba': entry[2],
            'last_lba': entry[3],
            'attr': entry[4],
            'name': entry[5].decode('utf-16le')}
    return part

def _read_gpt_partitions(stream, part_lba, num_part, part_size):
    parts = []
    for pi in range(num_part):
        part_offset = (part_lba * SECTOR_SIZE) + (pi * part_size)
        stream.seek(part_offset, 0)
        part_block = stream.read(part_size)
        part = GPT_PART_FORMAT.unpack_from(part_block, 0)
        part = _gpt_part_init(part, pi)
        if part['type'] != GUID_UNUSED_PART_STRING:
            parts.append(part)
    return parts

def readGPT(stream, offset=1):
    stream.seek(offset * SECTOR_SIZE, 0)
    _header = stream.read(GPT_HEADER_SIZE)
    header = GPT_HEADER_FORMAT.unpack_from(_header, GPT_HEADER_OFFSET)
    gpt = _gpt_init(header)
    if gpt['signature'] != GPT_HEADER_SIGNATURE:
        print('no gpt header magic found')
        return {}
    parts = _read_gpt_partitions(stream, gpt['part_lba'],
                                 gpt['npart'], gpt['part_size'])
    _gpt_add_partitions(gpt, parts)
    return gpt

def print_gpt_part(part, prefix=''):
    print('{}Partition {}:'.format(prefix, part['index']))
    print('{}  Type (GUID type): {} ({})'.format(prefix,
                                                 GUID_TRANSLATION[part['type']], part['type']))
    print('{}  GUID: {}'.format(prefix, part['guid']))
    print('{}  First LBA: {}'.format(prefix, part['first_lba']))
    print('{}  Last LBA: {}'.format(prefix, part['last_lba']))
    print('{}  Attributes: {}'.format(prefix, part['attr']))
    print('{}  Name: {}'.format(prefix, part['name']))

def print_gpt(gpt):
    print('GPT media')
    print('Signature: {}'.format(gpt['signature'].decode('utf-8')))
    print('Revision: {}'.format(gpt['revision']))
    print('Header size: {}'.format(gpt['header_size']))
    print('Header CRC: {}'.format(gpt['header_crc']))
    print('Current LBA: {}'.format(gpt['cur_lba']))
    print('Backup LBA: {}'.format(gpt['bkp_lba']))
    print('First LBA: {}'.format(gpt['first_lba']))
    print('Last LBA: {}'.format(gpt['last_lba']))
    print('Disk GUID: {}'.format(gpt['disk_guid']))
    print('Partitions LBA: {}'.format(gpt['part_lba']))
    print('Number of partitions: {}'.format(gpt['npart']))
    print('Partition size: {}'.format(gpt['part_size']))
    print('Partition CRC: {}'.format(gpt['part_crc']))
    print('Partition list:')
    for part in gpt['parts']:
        print_gpt_part(part, '  ')
