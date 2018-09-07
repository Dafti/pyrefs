import carving
import part.refs.attribute as rattr
import part.refs.entry_block as reb

def filetree(dump, v_offset, v_end_offset, nodeid, block_list = None, block_size = 16 * 1024):
    if not block_list:
        block_list = carving.find_blocks(dump, v_offset, v_end_offset, block_size)
    tree = _filetree(dump, nodeid, block_list)
    print(tree)
    return tree

def _filetree(dump, nodeid, complete_block_list):
    node_block_list = [ reb.read_entryblock(dump, x['offset'])
                        for x in complete_block_list
                        if x['nodeid'] == nodeid ]
    if not node_block_list:
        return None
    node_ext_block_list = [ x for x in node_block_list if x['_contains_extents'] ]
    node_rec_block_list = [ x for x in node_block_list if x['_contains_records'] ]
    rec_block_list = []
    if node_ext_block_list:
        root_ext_block_list = []
        for block in node_ext_block_list:
            root = True
            for _block in node_ext_block_list:
                if block['eb_number'] in [ ext['eb_number'] for ext in _block['extents'] ]:
                    root = False
                    break
            if root:
                root_ext_block_list.append(block)
        max_counter = max([ x['counter'] for x in root_ext_block_list ])
        ext_block = [ x for x in root_ext_block_list if x['counter'] == max_counter ][0]
        rec_block_list.append(ext_block)
        while [ x for x in rec_block_list if x['_contains_extents'] ]:
            for i in range(len(rec_block_list)):
                block = rec_block_list[i]
                if block['_contains_extents']:
                    blocks = []
                    for blockid in [ b['eb_number'] for b in block['extents'] ]:
                        blocks.append([ b for b in node_block_list if b['eb_number'] == blockid ][0])
                    rec_block_list[i] = blocks
                else:
                    rec_block_list[i] = [rec_block_list[i]]
                _flatten = [ i for sub in rec_block_list for i in sub ]
                rec_block_list = _flatten
    else:
        if not node_rec_block_list:
            print('ERROR: didn\'t found any entryblock with extensions or records in any of the entryblocks of node {:#x} ({} entryblocks).'.format(nodeid, len(node_block_list)))
            return None
        max_counter = max([ x['counter'] for x in node_rec_block_list ])
        block = [ x for x in node_rec_block_list if x['counter'] == max_counter ][0]
        rec_block_list.append(block)
    dm = _get_directory_metadata(rec_block_list)
    if not dm:
        return None
    rootname = _get_directory_metadata_name(dm)
    files = _get_files(rec_block_list)
    folders = _get_folders(rec_block_list, dump, complete_block_list)
    folder = {'name': rootname,
              'nodeid': rec_block_list[0]['node_id'],
              # 'entryblocks': block_list,
              'files': files,
              'folders': folders}
    return folder

def _get_directory_metadata(blocks):
    for block in blocks:
        if 'pointers_data' in block.keys():
            ptrs = [ ptr
                     for ptr in block['pointers_data']
                     if ptr['type'] == rattr.ATTR_TYPE_DIRECTORY_METADATA ]
            if ptrs:
                return ptrs[0]
        else:
            reb.dump_entryblock(block)
    # should never reach this point
    print('ERROR: no directory metadata record found for node {}.'.format(blocks[0]['node_id']))
    return None

def _get_directory_metadata_name(attr):
    return [ ptr['name']
             for ptr in attr['pointers_data']
             if ptr['type'] == rattr.DM_SUBATTR_TYPE_FOLDER ][0]

def _get_files(blocks):
    files = []
    for block in blocks:
        bfiles = [ {'name': ptr['filename'],
                    'blockid': block['eb_number']}
                   for ptr in block['pointers_data']
                   if ptr['type'] == rattr.ATTR_TYPE_FILENAME ]
        files.extend(bfiles)
    return files

def _get_folders(blocks, dump, complete_block_list):
    folders = []
    for block in blocks:
        bfolders = [ {'name': ptr['foldername'],
                      'blockid': block['eb_number'],
                      'tree': _filetree(dump, ptr['nodeid'], complete_block_list)}
                     for ptr in block['pointers_data']
                     if ptr['type'] == rattr.ATTR_TYPE_FILENAME_FOLDER ]
        folders.extend(bfolders)
    return folders

def dump_filetree(tree, level=0, name='.'):
    if not tree:
        return
    print('D {} {} ({}) {:#x}'.format(level * '.',
        name,
        tree['name'].decode('utf-16le') if tree['name'] else '<unknown>',
        tree['nodeid']))
    for f in tree['files']:
        print('F {} {} {:#x}'.format((level + 1) * '.',
            f['name'].decode('utf-16le') if f['name'] else '<unknown>',
            f['blockid']))
    for f in tree['folders']:
        dump_filetree(f['tree'], level + 1, f['name'].decode('utf-16le'))
