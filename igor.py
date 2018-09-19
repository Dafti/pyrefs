import argparse
import cmd
import sys
import ast

import media.mbr as mbr
import media.gpt as gpt
import part.refs.vol as vol
import part.refs.entry_block as reb
import part.refs.tree_control as rtc
import part.refs.allocator as ralloc
import part.refs.object_tree as rot
import part.refs.attribute as rattr
from util.hexdump import hexdump
from util.filetree import filetree, dump_filetree
import util.carving as carving
from util.func_parser import FuncArgumentParser, FuncArgumentParserError, FuncArgumentParserHelp
from util.table import print_table

def _datarun_arg(s):
    try:
        ebid, n = map(lambda x: int(x, 0), s.split(','))
        return (ebid, n)
    except:
        raise argparse.ArgumentTypeError('Datarun entry must be <entryblock_identifier>,<number>.')

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

    def __init__(self, **args):
        cmd.Cmd.__init__(self, args)
        self._init_func_args()

    def _init_func_args(self):
        file_argparser = FuncArgumentParser(
                prog='file',
                description='Load the provided dump file for analysis, and ' +
                            'automatically select the ReFS partition for ' +
                            'you. You can also initialize the list of ' +
                            'entryblocks of the partition.')
        file_argparser.add_argument('dump', action='store',
                help='file to use as dump for the analysis')
        file_argparser.add_argument('-i', '--initiliaze-entryblocks', action='store_true',
                default=False, dest='initialize_entryblocks',
                help='find blocks in provided dump')
        file_argparser.add_argument('-f', '--files', action='store_true',
                default=False,
                help='find files in provided dump (only considered if -i defined)')
        file_argparser.add_argument('-F', '--folders', action='store_true',
                default=False,
                help='find folders in provided dump (only considered if -i defined)')
        vol_argparser = FuncArgumentParser(
                prog='vol',
                description='Dump the volume record information from the current ReFS partition.')
        part_argparser = FuncArgumentParser(
                prog='part',
                description='Show available partitions in the currently loaded dump if no parameter' +
                            ' is given, switch to the provided partition if any provided.')
        part_argparser.add_argument('partidx', action='store', type=int,
                default=None, nargs='?',
                help='Partition index of the partition to use for analysis')
        feb_argparser = FuncArgumentParser(
                prog='find_entryblocks',
                description='Find and show all the entryblocks in current partition.' +
                            ' If requested number of files and folders information will be also' +
                            ' collected.')
        feb_argparser.add_argument('-f', '--files', action='store_true',
                default=False, dest='files',
                help='Collect information on the number of files in the entryblocks.')
        feb_argparser.add_argument('-F', '--folders', action='store_true',
                default=False, dest='folders',
                help='Collect information on the number of folders in the entryblocks.')
        fp_argparser = FuncArgumentParser(
                prog='find_pattern',
                description='Find a data pattern in all the blocks of the current partition.' +
                            ' Special characters (including spaces, carriage return, etc.)' +
                            ' are not allowed in the pattern, think of escaping them.')
        fp_argparser.add_argument('pattern', action='store',
                type=str,
                help='Pattern to find in the current partition blocks.')
        lfiles_argparser = FuncArgumentParser(
                prog='list_filenames',
                description='List the found filenames from the list of ' +
                            'entryblocks with filenames.')
        lfolders_argparser = FuncArgumentParser(
                prog='list_folders',
                description='List the found filename folders from the list ' +
                            'of entryblocks with folders.')
        eb_argparser = FuncArgumentParser(
                prog='entryblock',
                description='Dump the provided entryblock identifier as ' +
                'EntryBlock.')
        eb_argparser.add_argument('entryblock_identifier', action='store',
                type=lambda x: int(x, 0),
                help='entryblock identifier of the EntryBlock to dump')
        tc_argparser = FuncArgumentParser(
                prog='tree_control',
                description='Parse the given entryblock identifier as a ' +
                            'TreeControl. If no entryblock identifier is ' +
                            'provided it uses 0x1e as entryblock identifier.')
        tc_argparser.add_argument('entryblock_identifier', action='store',
                type=lambda x: int(x, 0), nargs='?', default=0x1e,
                help='entryblock identifier of the TreeControl to dump')
        tce_argparser = FuncArgumentParser(
                prog='tree_control_extension',
                description='Parse the given entryblock identifier as a ' +
                            'TreeControlExtension.')
        tce_argparser.add_argument('entryblock_identifier', action='store',
                type=lambda x: int(x, 0),
                help='entryblock identifier of the TreeControlExtension to ' +
                     'dump')
        ot_argparser = FuncArgumentParser(
                prog='object_tree',
                description='Parse the given entryblock identifier as an ' +
                            'ObjectTree.')
        ot_argparser.add_argument('entryblock_identifier', action='store',
                type=lambda x: int(x, 0),
                help='entryblock identifier of the ObjectTree to ' +
                     'dump')
        alloc_argparser = FuncArgumentParser(
                prog='allocator',
                description='Parse the given entryblock identifier as an ' +
                            'Allocator.')
        alloc_argparser.add_argument('entryblock_identifier', action='store',
                type=lambda x: int(x, 0),
                help='entryblock identifier of the Allocator to dump')
        attr_argparser = FuncArgumentParser(
                prog='attribute',
                description='Parse the given dump offset (in bytes) as an ' +
                            'Attribute.')
        attr_argparser.add_argument('dump_offset', action='store',
                type=lambda x: int(x, 0),
                help='dump offset (in bytes) of the Attribute to dump')
        ds_argparser = FuncArgumentParser(
                prog='datastream',
                description='Extract data from dump from the given datarun. ' +
                            'Dataruns can be extracted by exploring the ' +
                            'EntryBlocks (command `entryblock`) or using ' +
                            'the `list_dataruns` command.'
                            )
        ds_argparser.add_argument('output_filename', action='store',
                help='name of the generated output file')
        ds_argparser.add_argument('output_size', action='store',
                type=lambda x: int(x, 0),
                help='total amount of data to extract')
        ds_argparser.add_argument('dataruns', action='store',
                type=_datarun_arg, nargs='+',
                metavar='entryblock_identifier,number_of_blocks',
                help='datarun to follow for the data extraction')
        ldr_argparser = FuncArgumentParser(
                prog='list_dataruns',
                description='Retrieve list of all the files dataruns.')
        ft_argparser = FuncArgumentParser(
                prog='filetree',
                description='Extract the file tree structure from the given ' +
                            'node (use node 0x600 by default).')
        ft_argparser.add_argument('node_id', action='store',
                type=lambda x: int(x, 0), nargs='?', default=0x600,
                help='node identifier of the node to extract the file tree ' +
                     'structure from')
        hd_argparser = FuncArgumentParser(
                prog='hexdump',
                description='Hexdump the number of bytes at the provided ' +
                            'offset.')
        hd_argparser.add_argument('dump_offset', action='store',
                type=lambda x: int(x, 0),
                help='dump offset of the hexdump start')
        hd_argparser.add_argument('size', action='store',
                type=lambda x: int(x, 0),
                help='number of bytes to dump')
        hb_argparser = FuncArgumentParser(
                prog='hexblock',
                description='Hexdump the block with the provided ' +
                            'entryblock identifier.')
        hb_argparser.add_argument('entryblock_id', action='store',
                type=lambda x: int(x, 0),
                help='entryblock identifier to hexdump')
        bye_argparser = FuncArgumentParser(
                prog='bye',
                description='Exit the program. Are you sure?')
        record_argparser = FuncArgumentParser(
                prog='record',
                description='Save the following commands to selected file. ' +
                            'Saved file can be used afterwards for replay ' +
                            'with the \'playback\' command.')
        record_argparser.add_argument('output_file', action='store',
                help='file onto which commands will be saved')
        playback_argparser = FuncArgumentParser(
                prog='playback',
                description='Execute the sequence of commands defined in ' +
                            'the input file.')
        playback_argparser.add_argument('input_file', action='store',
                help='file from which commands to execute will be read')
        self._args = {file_argparser.prog: file_argparser,
                      vol_argparser.prog: vol_argparser,
                      part_argparser.prog: part_argparser,
                      feb_argparser.prog: feb_argparser,
                      fp_argparser.prog: fp_argparser,
                      lfiles_argparser.prog: lfiles_argparser,
                      lfolders_argparser.prog: lfolders_argparser,
                      eb_argparser.prog: eb_argparser,
                      tc_argparser.prog: tc_argparser,
                      tce_argparser.prog: tce_argparser,
                      ot_argparser.prog: ot_argparser,
                      alloc_argparser.prog: alloc_argparser,
                      attr_argparser.prog: attr_argparser,
                      ds_argparser.prog: ds_argparser,
                      ldr_argparser.prog: ldr_argparser,
                      ft_argparser.prog: ft_argparser,
                      hd_argparser.prog: hd_argparser,
                      hb_argparser.prog: hb_argparser,
                      bye_argparser.prog: bye_argparser,
                      record_argparser.prog: record_argparser,
                      playback_argparser.prog: playback_argparser
                     }

    def _check_func_args(self, func, arg):
        parser = self._args[func]
        out = {'return': True, 'args': None}
        try:
            args = parser.parse_args(arg.split())
        except FuncArgumentParserHelp:
            return out
        except FuncArgumentParserError:
            print('Master your command is badly formatted.')
            return out
        out = {'return': False, 'args': args}
        return out

    def preloop(self):
        print('''Hello master! Welcome home.
I will try to help you to analyze your ReFS partition dumps.
Type 'help' or '?' to list commands, and 'bye' or <ctrl-d> to exit.
Type 'help <command>' for a short description of the command.
Type '<command> -h' for the usage instructions of the command.''')
        if not self.dump_filename:
            print('''Master I just realized you haven't set a dump to analyze.
Please use the 'file' command to set it.''')

    def do_file(self, arg):
        '''Use the provided dump file for your ReFS analysis.
I will try to automatically select the right partition for you.
You can also initialize the list of entryblocks of the partition.'''
        cargs = self._check_func_args('file', arg)
        if cargs['return']:
            return
        args = cargs['args']
        self.dump_filename = args.dump
        print('Master I will try to follow your wishes by loading `{}`.'.format(self.dump_filename))
        try:
            self.dump_file = open(self.dump_filename, 'rb')
        except:
            print('I tried hard Master, but I couldn\'t open the requested file.')
            print('Are you sure it exists?')
            return
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
        print(('Master, {} ReFS partitions were found.\n' +
               'I will be using partition {}, but you can list the available' +
               ' partitions and switch between them with the \'part\' command.').format(
                   len(parts), parts[0]['index']))
        for part in parts:
            gpt.print_gpt_part(part)
        self.parts = parts
        self.part = parts[0]
        self.prompt = '\n{} part {} - first lba: {} last lba: {}\n> '.format(
                self.dump_filename,
                self.part['index'],
                self.part['first_lba'],
                self.part['last_lba'])
        if args.initialize_entryblocks:
            f_args = ''
            if args.files:
                f_args = '-f'
            if args.folders:
                f_args = f_args + ' -F' if f_args != '' else '-F'
            self.do_find_entryblocks(f_args)
        return

    def do_vol(self, arg):
        'Dump the volume record information from the current ReFS partition.'
        cargs = self._check_func_args('vol', arg)
        if cargs['return']:
            return
        args = cargs['args']
        _vol = vol.fsstat(self.dump_file,
                          self.part['first_lba'],
                          self.part['last_lba'])
        vol.dump_fsstat(_vol)
        return

    def do_part(self, arg):
        '''Show available partitions information ('part') and select from them
('part <partition index>').'''
        cargs = self._check_func_args('part', arg)
        if cargs['return']:
            return
        args = cargs['args']
        if args.partidx is None:
            print('Master you have {} partition{} available, here they are.'.format(
                len(self.parts), 's' if len(self.parts) > 1 else ''))
            for p in self.parts:
                gpt.print_gpt_part(self.part)
            return
        if args.partidx not in [ p['index'] for p in self.parts ]:
            print('Master I don\'t have the partition index {} you provided.'.format(
                args.partidx))
            return
        if args.partidx == self.part['index']:
            print('Nothing done, as we are already using partition {}.'.format(
                args.partidx))
            return
        self.part = self.parts[args.partidx]
        print('Switched to partition {}, enjoy Master.'.format(arg))
        self.prompt = '\n{} part {} - first lba: {} last lba: {}\n> '.format(
                self.dump_filename,
                self.part['index'],
                self.part['first_lba'],
                self.part['last_lba'])
        gpt.print_gpt_part(self.part)

    def do_find_entryblocks(self, arg):
        '''Extract and show all the entryblocks used in the current partition.
If requested also extract an estimation of the number of filenames and folders
found per entryblock.'''
        cargs = self._check_func_args('find_entryblocks', arg)
        if cargs['return']:
            return
        args = cargs['args']
        if not self.dump_file:
            print('Master you have not defined a dump to analyze.')
            print('Please provide a dump file.')
            return
        offset = self.part['first_lba']
        end_offset = self.part['last_lba']
        if self.blocks == None:
            print(('Looking for blocks between lba {} and lba {}.' +
                   ' This may take a while Master. A coffee?').format(
                       offset,
                       end_offset))
            self.blocks = carving.find_blocks(self.dump_file, offset, end_offset)
        print('Master I found {} blocks.'.format(len(self.blocks)))
        if args.files:
            blocks = carving.blocks_with_filename_attributes(self.dump_file, self.blocks)
            print('Master I found {} blocks with the filename attribute.'.format(len(blocks)))
        if args.folders:
            blocks = carving.blocks_with_folder_attributes(self.dump_file, self.blocks)
            print('Master I found {} blocks with the filename folder attribute.'.format(len(blocks)))
        carving.print_blocks(self.blocks)

    def do_find_pattern(self, arg):
        '''Find a data pattern in all the blocks of the current partition.
Special characters (including spaces, carriage return, etc.) are not allowed in
the pattern, think of escaping them.'''
        cargs = self._check_func_args('find_pattern', arg)
        if cargs['return']:
            return
        args = cargs['args']
        _pattern = ast.literal_eval('"{}"'.format(args.pattern))
        offset = self.part['first_lba']
        end_offset = self.part['last_lba']
        pattern = [ ord(x) for x in _pattern ]
        print('Master I will be analyzing your pattern \'{}\' ({}) but it may take a while.'.format(
            args.pattern, [ '{:#x}'.format(x) for x in pattern ]))
        print('Do you want a cup of tea?')
        blocks = carving.find_data_blocks_with_pattern(self.dump_file, pattern, offset, end_offset)
        print('Master I found {} blocks with your wiseful pattern.'.format(len(blocks)))
        # print table of found blocks
        columns = [ {'key': 'addr', 'header': 'Address', 'align': '<', 'format': '#x'},
                    {'key': 'lba_offset', 'header': 'LBA offset', 'align': '<', 'format': '#x'},
                    {'key': 'block_offset', 'header': 'Block offset', 'align': '<', 'format': '#x'} ]
        if blocks:
            print_table(columns, blocks)

    def do_list_filenames(self, arg):
        'List the found filenames from the list of entryblocks with filenames.'
        cargs = self._check_func_args('list_filenames', arg)
        if cargs['return']:
            return
        args = cargs['args']
        if not self.blocks:
            print('Master, first you need to look for the blocks and blocks with filenames.')
            print('Please Master, use \'find_blocks\' and \'find_blocks_with_filenames\' first.')
            return
        listed = 0
        for block in self.blocks:
            if block['fnas']:
                for fid in block['fnas']:
                    attr = rattr.read_attribute(self.dump_file, fid)
                    try:
                        filename = attr['filename'].decode('utf-16le')
                    except:
                        filename = attr['filename']
                    listed = listed + 1
                    print('{:#010x} {:#06x} {:#06x} {:#06x} {:#010x} {}'.format(
                        block['offset'], block['entryblock'],
                        block['nodeid'], block['childid'], attr['_absolute_offset'], filename))
        print('Master I listed {} filenames.'.format(listed))
        if not listed:
            print('Master are you sure you performed \'find_blocks_with_folders\' before?')

    def do_list_folders(self, arg):
        'List the found filename folders from the list of entryblocks with folders.'
        cargs = self._check_func_args('list_folders', arg)
        if cargs['return']:
            return
        args = cargs['args']
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
                        block['nodeid'], block['childid'], attr['_absolute_offset'], foldername))
        print('Master I listed {} folders.'.format(listed))
        if not listed:
            print('Master are you sure you performed \'find_blocks_with_folders\' before?')

    def do_hexdump(self, arg):
        'Hexdump the number of bytes at the provided offset.'
        cargs = self._check_func_args('hexdump', arg)
        if cargs['return']:
            return
        args = cargs['args']
        offset = args.dump_offset
        size = args.size
        self.dump_file.seek(offset, 0)
        data = self.dump_file.read(size)
        hexdump(data, offset)

    def do_hexblock(self, arg):
        'Hexdump the block with the provided entryblock identifier.'
        cargs = self._check_func_args('hexblock', arg)
        if cargs['return']:
            return
        args = cargs['args']
        ebid = args.entryblock_id
        if not self.blocks:
            print('Master, first you need to look for the blocks.')
            print('Please Master use \'find_blocks\' first or use \'hexdump\'.')
            return
        blks = [ b for b in self.blocks if b['entryblock'] == ebid ]
        if not blks:
            print('Master, are you sure such an entryblock exist?')
            return
        blk = blks[0]
        self.dump_file.seek(blk['offset'], 0)
        data = self.dump_file.read(16 * 1024)
        hexdump(data, blk['offset'])

    def do_entryblock(self, arg):
        'Dump the provided entryblock identifier as entryblock.'
        cargs = self._check_func_args('entryblock', arg)
        if cargs['return']:
            return
        args = cargs['args']
        ebid = args.entryblock_identifier
        if not self.blocks:
            print('Master, first you need to look for the blocks.')
            print('Please Master use \'find_blocks\' first.')
            return
        blocks = [ b for b in self.blocks if b['entryblock'] == ebid ]
        if len(blocks) != 1:
            print('Master, I couldn\'t find the block you asked for.')
            return
        block = blocks[0]
        eb = reb.read_entryblock(self.dump_file, block['offset'])
        reb.dump_entryblock(eb)

    def do_tree_control(self, arg):
        '''Parse the given entryblock identifier as a TreeControl.
If no entryblock identifier is provided it uses 0x1e as entryblock
identifier.'''
        cargs = self._check_func_args('tree_control', arg)
        if cargs['return']:
            return
        args = cargs['args']
        ebid = args.entryblock_identifier
        if not self.blocks:
            print('Master, first you need to look for the blocks.')
            print('Please Master use \'find_blocks\' first.')
            return
        blocks = [ b for b in self.blocks if b['entryblock'] == ebid ]
        if len(blocks) != 1:
            print('Master, I couldn\'t find the block you asked for.')
            return
        block = blocks[0]
        tc = rtc.read_tree_control(self.dump_file, block['offset'])
        rtc.dump_tree_control(tc)

    def do_tree_control_extension(self, arg):
        'Parse the given entryblock identifier as a TreeControlExtension.'
        cargs = self._check_func_args('tree_control_extension', arg)
        if cargs['return']:
            return
        args = cargs['args']
        ebid = args.entryblock_identifier
        if not self.blocks:
            print('Master, first you need to look for the blocks.')
            print('Please Master use \'find_blocks\' first.')
            return
        blocks = [ b for b in self.blocks if b['entryblock'] == ebid ]
        if len(blocks) != 1:
            print('Master, I couldn\'t find the block you asked for.')
            return
        block = blocks[0]
        tce = rtc.read_tree_control_ext(self.dump_file, block['offset'])
        rtc.dump_tree_control_ext(tce)

    def do_object_tree(self, arg):
        'Parse the given entryblock identifier as an ObjectTree.'
        cargs = self._check_func_args('object_tree', arg)
        if cargs['return']:
            return
        args = cargs['args']
        ebid = args.entryblock_identifier
        if not self.blocks:
            print('Master, first you need to look for the blocks.')
            print('Please Master use \'find_blocks\' first.')
            return
        blocks = [ b for b in self.blocks if b['entryblock'] == ebid ]
        if len(blocks) != 1:
            print('Master, I couldn\'t find the block you asked for.')
            return
        block = blocks[0]
        ot = rot.read_object_tree(self.dump_file, block['offset'])
        rot.dump_object_tree(ot)

    def do_allocator(self, arg):
        'Parse the given entryblock identifier as an Allocator.'
        cargs = self._check_func_args('allocator', arg)
        if cargs['return']:
            return
        args = cargs['args']
        ebid = args.entryblock_identifier
        if not self.blocks:
            print('Master, first you need to look for the blocks.')
            print('Please Master use \'find_blocks\' first.')
            return
        blocks = [ b for b in self.blocks if b['entryblock'] == ebid ]
        if len(blocks) != 1:
            print('Master, I couldn\'t find the block you asked for.')
            return
        block = blocks[0]
        al = ralloc.read_allocator(self.dump_file, block['offset'])
        ralloc.dump_allocator(al)

    def do_attribute(self, arg):
        'Parse the given dump offset (in bytes) as an Attribute.'
        cargs = self._check_func_args('attribute', arg)
        if cargs['return']:
            return
        args = cargs['args']
        offset = args.dump_offset
        attr = rattr.read_attribute(self.dump_file, offset)
        rattr.dump_attribute(attr)

    def do_datastream(self, arg):
        '''Extract data from dump from the given datarun.
Dataruns can be extracted by exploring the EntryBlocks (command `entryblock`)
or using the `list_dataruns` command.'''
        cargs = self._check_func_args('datastream', arg)
        if cargs['return']:
            return
        args = cargs['args']
        ofn = args.output_filename
        size = args.output_size
        dataruns = args.dataruns
        of = open(ofn, 'wb')
        for offset, length in dataruns:
            offset = (offset * 1024 * 16) + (self.part['first_lba'] * 512)
            length = length * 1024 * 16
            if length > size:
                length = size
            size = size - length
            self.dump_file.seek(offset, 0)
            data = self.dump_file.read(length)
            of.write(data)
        of.close()

    def do_list_dataruns(self, arg):
        'Retrieve list of all the files dataruns.'
        cargs = self._check_func_args('list_dataruns', arg)
        if cargs['return']:
            return
        files = 0
        drs = 0
        for block in self.blocks:
            if block['fnas']:
                for fid in block['fnas']:
                    files = files + 1
                    attr = rattr.read_attribute(self.dump_file, fid)
                    dataruns = []
                    if attr['datarun'] and attr['datarun']['pointers_data']:
                        for ptr in attr['datarun']['pointers_data']:
                            if ptr['pointers_data']:
                                datarun = [ (x['blockid'], x['num_blocks'])
                                            for x in ptr['pointers_data'] ]
                                dataruns.append((ptr['logical_size'], datarun))
                                drs = drs + 1
                    try:
                        filename = attr['filename'].decode('utf-16le')
                    except:
                        filename = attr['filename']
                    print('{:#010x} {:#06x} {:#06x} {:6} {}'.format(
                        block['offset'], block['entryblock'],
                        block['nodeid'], block['counter'], filename))
                    for length, datarun in dataruns:
                        print('  size: {:#x} datarun: '.format(length), end='')
                        for run in datarun:
                            blockid,num = run
                            print(' {:#x},{}'.format(blockid,num), end='')
                        print('')
        if files:
            print('Master I listed {} data runs from {} files.'.format(drs, files))
        else:
            print('Master I could not find any file, did you already execute \'find_blocks_with_filenames\'?')

    def do_filetree(self, arg):
        'Extract the file tree structure from the given node (use node 0x600 by default).'
        cargs = self._check_func_args('filetree', arg)
        if cargs['return']:
            return
        args = cargs['args']
        nodeid = args.node_id
        block_list = None
        if self.blocks:
            block_list = self.blocks
        offset = self.part['first_lba']
        end_offset = self.part['last_lba']
        tree = filetree(self.dump_file, offset, end_offset, nodeid, block_list)
        dump_filetree(tree)

    def do_bye(self, arg):
        'Exit the program. Are you sure?'
        cargs = self._check_func_args('bye', arg)
        if cargs['return']:
            return
        print('''It's been a great to serve you master.
Bye!!!!''')
        self.close()
        return True

    def do_EOF(self, arg):
        'Exit the program. Really are you sure?'
        print('\nI would have liked a \'bye\' Master, but I follow your orders.')
        return self.do_bye(arg)

    # ----- record and playback -----
    def do_record(self, arg):
        ''''Save the following commands to selected file.
Saved file can be used afterwards for replay with the \'playback\' command.'''
        cargs = self._check_func_args('record', arg)
        if cargs['return']:
            return
        args = cargs['args']
        self.close()
        try:
            self.rec_file = open(args.output_file, 'w')
        except:
            print('Master I couldn\'t open file to save commands.')
            self.rec_file = None

    def do_playback(self, arg):
        'Execute the sequence of commands defined in the input file.'
        cargs = self._check_func_args('playback', arg)
        if cargs['return']:
            return
        args = cargs['args']
        self.close()
        try:
            with open(args.input_file) as f:
                self.cmdqueue.extend(f.read().splitlines())
        except:
            print('Master I couldn\'t open file to read commands to execute.')

    def precmd(self, line):
        if self.rec_file and 'playback' not in line:
            print(line, file=self.rec_file)
        return line

    def close(self):
        if self.rec_file:
            self.rec_file.close()
            self.rec_file = None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ReFS carving on provided dump.')
    parser.add_argument('-d', '--dump', action='store', required=False, type=str,
                        help='ReFS dump to analyze')
    args = parser.parse_args()

    if args.dump:
        rshell = PyReFSShell()
        rshell.onecmd('file ' + args.dump)
        rshell.cmdloop()
    else:
        PyReFSShell().cmdloop()
