import sys
import argparse
import media.mbr as mbr
import media.gpt as gpt
import part.refs as refs

parser = argparse.ArgumentParser(description='Read from provided dump.')
parser.add_argument('dump', action='store',
        type=argparse.FileType(mode='rb'))
args = parser.parse_args()
mbr_data = mbr.readMBR(args.dump)
# we make the supposition that if it is a GPT media then only one
# partition is declared in the MBR
if not (len(mbr_data) == 1 and mbr_data[0][1]['ptype'] == mbr.MBR_PARTTYPE_GPT):
    print(mbr_data)
    sys.exit()

gpt_data = gpt.readGPT(args.dump, mbr_data[0][1]['start'])
gpt.print_gpt(gpt_data)

for part in gpt_data['parts']:
    if part['type'] == gpt.GUID_PART_TYPE_W_BASIC_DATA_PART:
        if refs.is_refs_part(args.dump, part['first_lba']):
            refs_fsstat = refs.fsstat(args.dump, part['first_lba'], part['last_lba'])
            refs.dump_fsstat(refs_fsstat)
        else:
            print('no ReFS partition')
