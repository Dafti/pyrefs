import argparse
import media.mbr as mbr
import media.gpt as gpt

def mmls():
    parser = argparse.ArgumentParser(description='Read MBR from provided dump.')
    parser.add_argument('dump', action='store',
            type=argparse.FileType(mode='rb'))
    args = parser.parse_args()
    mbr_data = mbr.readMBR(args.dump)
    # we make the supposition that if it is a GPT media then only one
    # partition is declared in the MBR
    if len(mbr_data) == 1 and mbr_data[0][1]['ptype'] == mbr.MBR_PARTTYPE_GPT:
        gpt_data = gpt.readGPT(args.dump, mbr_data[0][1]['start'])
        gpt.print_gpt(gpt_data)
    else:
        print(mbr_data)

if __name__ == '__main__':
    mmls()
