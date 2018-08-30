import sys
from struct import Struct
from util.hexdump import hexdump

SECTOR_SIZE = 512
REFS_VR_JUMPINSTRUCTION_OFFSET = 0x0
REFS_VR_JUMPINSTRUCTION_SIZE = 3
REFS_VR_FILESYSTEMNAME_OFFSET = 0x3
REFS_VR_FILESYSTEMNAME_SIZE = 8
REFS_VR_RESV_OFFSET = 0x7
REFS_VR_RESV_SIZE = 5
REFS_VR_STRUCT_ID_OFFSET = 0x10
REFS_VR_STRUCT_ID_SIZE = 4
REFS_VR_NUMBYTES_OFFSET = 0x14
REFS_VR_NUMBYTES_SIZE = 2
REFS_VR_CHECKSUM_OFFSET = 0x16
REFS_VR_CHECKSUM_SIZE = 2
REFS_VR_BACKUP_OFFSET = 0x18
REFS_VR_BACKUP_SIZE = 8
REFS_VR_BYTES_PER_SECTOR_OFFSET = 0x20
REFS_VR_BYTES_PER_SECTOR_SIZE = 4
REFS_VR_SECTORS_PER_CLUSTER_OFFSET = 0x24
REFS_VR_SECTORS_PER_CLUSTER_SIZE = 4
REFS_VR_VERSION_MAJOR_OFFSET = 0x28
REFS_VR_VERSION_MAJOR_SIZE = 1
REFS_VR_VERSION_MINOR_OFFSET = 0x29
REFS_VR_VERSION_MINOR_SIZE = 1
REFS_VR_UNKNOWN_OFFSET = 0x2a
REFS_VR_UNKNOWN_SIZE = 14
REFS_VR_SN_OFFSET = 0x38
REFS_VR_SN_SIZE = 8
REFS_VR_SIZE = 64

REFS_VR_JUMPINSTRUCTION_POS = 0
REFS_VR_FILESYSTEMNAME_POS = 1
REFS_VR_RESV_POS = 2
REFS_VR_STRUCT_ID_POS = 3
REFS_VR_NUMBYTES_POS = 4
REFS_VR_CHECKSUM_POS = 5
REFS_VR_BACKUP_POS = 6
REFS_VR_BYTES_PER_SECTOR_POS = 7
REFS_VR_SECTORS_PER_CLUSTER_POS = 8
REFS_VR_VERSION_MAJOR_POS = 9
REFS_VR_VERSION_MINOR_POS = 10
REFS_VR_UNKNOWN_POS = 11
REFS_VR_SN_POS = 12

REFS_VR_FILESYSTEMNAME_SIGNATURE = 'ReFS\x00\x00\x00\x00'
REFS_VR_STRUCT_ID_SIGNATURE = 'FSRS'

REFS_VR_FORMAT = Struct('<3s8s5s4sHHQLLBB14sQ')
_JUMPINSTRUCTION_FORMAT = Struct('BBB')

def is_refs_part(dump, lba):
    """Check the given LBA for the ReFS signature and
    filesystem strings to decide if it is an ReFS volume."""
    dump.seek(lba * SECTOR_SIZE, 0)
    header = dump.read(REFS_VR_SIZE)
    signature = header[REFS_VR_FILESYSTEMNAME_OFFSET:REFS_VR_FILESYSTEMNAME_OFFSET + REFS_VR_FILESYSTEMNAME_SIZE].decode('ascii')
    fs = header[0x10:0x14].decode('ascii')
    return (signature == REFS_VR_FILESYSTEMNAME_SIGNATURE and
            fs == REFS_VR_STRUCT_ID_SIGNATURE)

def _check_is_refs_part(dump, lba):
    if not is_refs_part(dump, lba):
        print("ERROR(part.refs.fsstat): no ReFS partition")
        sys.exit(1)

def _dec_volume_record(dump, lba):
    dump.seek(lba * SECTOR_SIZE, 0)
    vr_raw = dump.read(REFS_VR_SIZE)
    vr_entries = REFS_VR_FORMAT.unpack_from(vr_raw, 0)
    ji_entries = _JUMPINSTRUCTION_FORMAT.unpack_from(vr_entries[REFS_VR_JUMPINSTRUCTION_OFFSET], 0)
    ji = ji_entries[0] + (ji_entries[1] * 256) + (ji_entries[2] * 256 * 256)
    vr = {'absolute_lba': lba,
          'jump_instruction': ji,
          'filesystem_name': vr_entries[REFS_VR_FILESYSTEMNAME_POS],
          'reserved': vr_entries[REFS_VR_RESV_POS],
          'struct_id': vr_entries[REFS_VR_STRUCT_ID_POS],
          'numbytes': vr_entries[REFS_VR_NUMBYTES_POS],
          'checksum': vr_entries[REFS_VR_CHECKSUM_POS],
          'backup': vr_entries[REFS_VR_BACKUP_POS],
          'bytes_per_sector': vr_entries[REFS_VR_BYTES_PER_SECTOR_POS],
          'sectors_per_cluster': vr_entries[REFS_VR_SECTORS_PER_CLUSTER_POS],
          'version_major': vr_entries[REFS_VR_VERSION_MAJOR_POS],
          'version_minor': vr_entries[REFS_VR_VERSION_MINOR_POS],
          'unknown': vr_entries[REFS_VR_UNKNOWN_POS],
          'serial_number': vr_entries[REFS_VR_SN_POS]}
    return vr

def fsstat(dump, lba, last_lba):
    _check_is_refs_part(dump, lba)
    vr = _dec_volume_record(dump, lba)
    vr_backup = _dec_volume_record(dump, last_lba)
    fs = {'volume_record': vr,
          'volume_record_backup': vr_backup}
    return fs

def _dump_volume_record(vr):
    print('- Jump instruction: {:#08x}'.format(vr['jump_instruction']))
    print('- Filesystem name: {}'.format(vr['filesystem_name'].decode('utf-8')))
    print('- Struct identifier: {}'.format(vr['struct_id'].decode('utf-8')))
    print('- Size of volume record: {}'.format(vr['numbytes']))
    print('- FSRS checksum: {:#06x}'.format(vr['checksum']))
    print('- Volume record backup LBA offset: {}'.format(vr['backup']))
    print('- Bytes per sector: {}'.format(vr['bytes_per_sector']))
    print('- Sectors per cluster: {}'.format(vr['sectors_per_cluster']))
    print('- Filesystem major version: {}'.format(vr['version_major']))
    print('- Filesystem minor version: {}'.format(vr['version_minor']))
    print('- Volume serial number: {}'.format(vr['serial_number']))

def _dump_fsstat_volume_record_main(fs):
    vr = fs['volume_record']
    print('Volume record (lba: {}):'.format(vr['absolute_lba']))
    _dump_volume_record(vr)

def _dump_fsstat_volume_record_backup(fs):
    vr = fs['volume_record_backup']
    print('Volume record backup (lba: {}):'.format(vr['absolute_lba']))
    _dump_volume_record(vr)

def dump_fsstat(fs):
    _dump_fsstat_volume_record_main(fs)
    _dump_fsstat_volume_record_backup(fs)
