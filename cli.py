import cmd, sys

import media.mbr as mbr
import media.gpt as gpt
import part.refs.vol as vol
import part.refs.attribute as rattr
from util.hexdump import hexdump
import carving

class PyReFSShell(cmd.Cmd):
    intro = None
    #     intro = '''Hello master! Welcome home.
    # I will try to help you to analyze your ReFS partition dumps.
    # Type 'help' or '?' to list commands.\n'''
    prompt = '> '
    rec_file = None
    dump_filename = None
    dump_file = None
    part = None
    parts = None
    blocks = None

    def preloop(self):
        print('''Hello master! Welcome home.
I will try to help you to analyze your ReFS partition dumps.
Type 'help' or '?' to list commands.''')
        if not self.dump_filename:
            print('''Master I just realized you haven't set a dump to analyze.
Please use the 'file' command to set it.''')

    def do_file(self, arg):
        '''Use the provided dump file for your deep analysis.
        I will try to automatically select the right partition for you.'''
        print('Loading {}'.format(arg))
        self.dump_filename = arg
        self.dump_file = open(self.dump_filename, 'rb')
        mbr_data = mbr.readMBR(self.dump_file)
        gpt_part = None
        for part_index, part in mbr_data:
            if part['ptype'] == mbr.MBR_PARTTYPE_GPT:
                gpt_part = part
                break
        if not gpt_part:
            print('ARGH Master. I couldn\'t find a GPT volume in the dump' +
                  ' you provided me. Please, try with another file.')
            self.dump_filename = None
            self.dump_file.close()
            self.dump_file = None
            return
        gpt_data = gpt.readGPT(self.dump_file, gpt_part['start'])
        parts = [ p for p in gpt_data['parts']
                  if p['type'] == gpt.GUID_PART_TYPE_W_BASIC_DATA_PART
                  and vol.is_refs_part(self.dump_file, p['first_lba']) ]
        if not parts:
            print('ARGH Master. I couldn\'t find a ReFS' +
                  ' partition in the dump file you provided.' +
                  ' Please, try with another file.',
                  gpt.GUID_TRANSLATION[gpt.GUID_PART_TYPE_W_BASIC_DATA_PART])
            self.dump_filename = None
            self.dump_file.close()
            self.dump_file = None
            return
        if len(parts) > 1:
            print(('Master, {} ReFS partitions were found.\n' +
                   'I will be using partition {}, but you can list the available' +
                   ' partitions and switch between them with the \'part\' command.').format(
                       len(parts), parts[0]['index']))
        self.parts = parts
        self.part = parts[0]
        print('Partition {} will be used.'.format(self.part['index']))
        gpt.print_gpt_part(self.part)
        self.prompt = '\n{} part {} - first lba: {} last lba: {}\n> '.format(
                self.dump_filename,
                self.part['index'],
                self.part['first_lba'],
                self.part['last_lba'])
        return

    def do_part(self, arg):
        '''Show available partitions ('part') and select from them ('part <partition index>').'''
        if not arg:
            print('Master you have {} partition{} available, here they are.'.format(
                len(self.parts), 's' if len(self.parts) > 1 else ''))
            for p in self.parts:
                gpt.print_gpt_part(self.part)
            return
        if int(arg) not in [ p['index'] for p in self.parts ]:
            print('Master I don\'t have the partition index {} you provided.'.format(
                arg))
            return
        if int(arg) == self.part['index']:
            print('Nothing done, as we are already using partition {}.'.format(
                arg))
            return
        self.part = self.parts[int(arg)]
        print('Switched to partition {}, enjoy Master.'.format(arg))
        self.prompt = '\n{} part {} - first lba: {} last lba: {}\n> '.format(
                self.dump_filename,
                self.part['index'],
                self.part['first_lba'],
                self.part['last_lba'])
        gpt.print_gpt_part(self.part)

    def do_find_blocks(self, arg):
        'Extract all the entry blocks.'
        offset = self.part['first_lba']
        end_offset = self.part['last_lba']
        if arg:
            if len(arg.split()) != 2:
                print('Master, two offsets are expected start and end.')
                return
            offset, end_offset = tuple(map(lambda x: int(x), arg.split()))
        if self.blocks == None:
            print(('Looking for blocks between lba {} and lba {}.' +
                   ' This may take a while Master. A coffee?').format(
                       offset,
                       end_offset))
            self.blocks = carving.find_blocks(self.dump_file, offset, end_offset)
        print('Master I found {} blocks.'.format(len(self.blocks)))
        carving.print_blocks(self.blocks)

    def do_find_blocks_with_folders(self, arg):
        'Find which blocks have a folder attribute.'
        if not self.blocks:
            print('Master, first you need to look for the blocks.')
            print('Please Master, use \'find_blocks\' first.')
            return
        blocks = carving.blocks_with_folder_attributes(self.dump_file, self.blocks) 
        print('Master I found {} blocks with the folder attribute.'.format(len(blocks)))
        carving.print_blocks(blocks)

    def do_list_folders(self, arg):
        'List the found folders from the list of blocks with folders.'
        if not self.blocks:
            print('Master, first you need to look for the blocks and blocks with folders.')
            print('Please Master, use \'find_blocks\' and \'find_blocks_with_folders\' first.')
            return
        listed = 0
        for block in self.blocks:
            if block['folderids']:
                for fid in block['folderids']:
                    attr = rattr.read_attribute(self.dump_file, fid)
                    try:
                        foldername = attr['foldername'].decode('utf-16le')
                    except:
                        foldername = attr['foldername']
                    listed = listed + 1
                    print('{:#010x} {:#06x} {:#06x} {:#06x} {:#010x} {}'.format(
                        block['offset'], block['entryblock'],
                        block['nodeid'], block['childid'], attr['absolute_offset'], foldername))
        print('Master I listed {} folders.'.format(listed))
        if not listed:
            print('Master are you sure you performed \'find_blocks_with_folders\' before?')

    def do_hexblock(self, arg):
        'Hexdump the provided entryblock id.'
        if not arg:
            print('Please Master indicate the block to hexdump.')
        if not self.blocks:
            print('Master, first you need to look for the blocks.')
            print('Please Master use \'find_blocks\' first.')
        ebid = int(arg, 0)
        blks = [ b for b in self.blocks if b['entryblock'] == ebid ]
        if not blks:
            print('Master, are you sure such an entryblock exist?')
            return
        blk = blks[0]
        self.dump_file.seek(blk['offset'], 0)
        data = self.dump_file.read(16 * 1024)
        hexdump(data, blk['offset'])

    def do_bye(self, arg):
        'Are you sure?'
        print('''It's been a great to serve you master.
Bye!!!!''')
        self.close()
        return True

    # ----- record and playback -----
    def do_record(self, arg):
        'Save future commands to filename:  RECORD rose.cmd'
        self.rec_file = open(arg, 'w')

    def do_playback(self, arg):
        'Playback commands from a file:  PLAYBACK rose.cmd'
        self.close()
        with open(arg) as f:
            self.cmdqueue.extend(f.read().splitlines())

    def precmd(self, line):
        line = line.lower()
        if self.rec_file and 'playback' not in line:
            print(line, file=self.rec_file)
        return line

    def close(self):
        if self.rec_file:
            self.rec_file.close()
            self.rec_file = None

if __name__ == '__main__':
    PyReFSShell().cmdloop()
