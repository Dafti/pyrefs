def hexdump(data, address=0, width=16):
    max_address = address + len(data)
    address_len = len('{:#x}'.format(max_address)) + 1
    data_format = ' {:02x}'
    text_format = '    {}'
    header_format = '{:<' + str(address_len) + '} ' + (data_format * width) + text_format
    buf = [ x % 0x100 for x in range(width) ]
    print(header_format.format('', *buf, ''))
    for index in range(0, len(data), width):
        buf = data[index:index + width]
        dec = ''.join([ chr(x) if x >= 32 and x <= 126 else '.' for x in buf ])
        white_format = '   ' * (width - len(buf))
        line_format = '{:#0' + str(address_len) + 'x}:' + (data_format * len(buf)) + white_format + text_format
        print(line_format.format(address + index, *buf, dec))

