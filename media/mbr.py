from struct import unpack, Struct
from media.gpt import readGPT

SECTOR_SIZE = 512
MBR_SIZE = SECTOR_SIZE
MBR_TERMINATOR = 0x55aa
MBR_TERMINATOR_OFFSET = 510
MBR_PART_TABLE_OFFSET = 0x1be
MBR_PART_TABLE_SIZE = 4
MBR_PART_ENTRY_SIZE = 16
MBR_PARTTYPE_NOPART = 0
MBR_PARTTYPE_REFS_EXFAT_NTFS = 7
MBR_PARTTYPE_REFS_EXFAT_GPT = 0xee
MBR_PARTTYPE_GPT = 0xee

'''
MBR Partition format

offset,size,name, interpretation

0   ubyte     boot flag        0x80 means bootable, 0 means not bootable
1   3 bytes   CHS              obsolete
4   ubyte     partition type   0x7 means NTFS, Exfat or ReFS
5   3 bytes   CHS              obsolete
8   ulong     1st sector       address of first sector
12  ulong     size             size in sectors
'''
#https://docs.python.org/3/library/struct.html
MBR_PART_FORMAT = Struct('<B3sB3sLL') #'<' means little endian
MBR_TERMINATOR_FORMAT = Struct('>H')

def readMBR(stream):
    data = stream.read(MBR_SIZE)
    mbr = []
    terminator, = MBR_TERMINATOR_FORMAT.unpack_from(data, MBR_TERMINATOR_OFFSET)
    if terminator != MBR_TERMINATOR:
        print('not an MBR, missing MBR terminator ({})'.format(MBR_TERMINATOR))
        return None #we should raise an Exception. https://docs.python.org/fr/3.5/tutorial/errors.html
    else:
        for p in range(MBR_PART_TABLE_SIZE):
            # by convention, _ is the variable name for ignored values in Python
            mbr_entry = MBR_PART_FORMAT.unpack_from(data, MBR_PART_TABLE_OFFSET + (p * MBR_PART_ENTRY_SIZE))
            bflag, _, ptype, _, start, size = mbr_entry
            if ptype != 0:
                mbr.append( (p, { 'bflag':bflag, 'ptype':ptype, 'start':start, 'size':size } ) )
            # else:
            #     print('Ignored entry')
    # print(mbr)    
    return mbr


