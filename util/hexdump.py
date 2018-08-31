def hexdump(data, address=0, width=16):
    max_address = address + len(data)
    address_len = len('{:#x}'.format(max_address)) + 1
    data_format = ' {:02x}'
    text_format = '    {}'
    header_format = '{:<' + str(address_len) + '} ' + (data_format * width) + text_format
    buf = [ x % 0x100 for x in range(width) ]
    print(header_format.format('', *buf, ''))
    backup = None
    skip = -1
    line_range = list(range(0, len(data), width))
    last_range = line_range[-1]
    dot_line = '.' * len(('{:#0' + str(address_len) + 'x}:').format(0))
    for index in line_range:
        buf = data[index:index + width]
        dec = ''.join([ chr(x) if x >= 32 and x <= 126 else '.' for x in buf ])
        white_format = '   ' * (width - len(buf))
        line_format = '{:#0' + str(address_len) + 'x}:' + (data_format * len(buf)) + white_format + text_format
        line = line_format.format(address + index, *buf, dec)
        if skip == -1:
            print(line)
            skip = 0
        elif index == last_range:
            if skip > 0:
                print(backup)
                print(line)
        elif list(filter(lambda x: x != 0, buf)):
            if skip:
                print(backup)
            skip = 0
            print(line)
        else:
            if skip == 0:
                skip = 1
                backup = line
            elif skip == 1:
                backup_format = dot_line + (data_format * len(buf)) + white_format + text_format
                backup = backup_format.format(*buf, dec)
            else:
                skip = 2
