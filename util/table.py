def print_table(_meta, _entries):
    # first we transform the entries
    entries = []
    for _e in _entries:
        entry = {}
        for col in _meta:
            entry[col['key']] = _e[col['key']] if 'transform' not in col.keys() else  col['transform'](_e[col['key']])
        entries.append(entry)
    # transform the values and compute columns lengths
    lengths = {m['key']:len(m['header']) for m in _meta}
    values = []
    for e in entries:
        value = {}
        for m in _meta:
            form = m['format'] if 'format' in m.keys() else ''
            val = ('{:' + form + '}').format(e[m['key']])
            value[m['key']] = val
            lengths[m['key']] = max(len(val), lengths[m['key']])
        values.append(value)
    lengths = {k:v+1 for k,v in lengths.items()}
    # print the table header
    for m in _meta:
        align = m['align'] if 'align' in m.keys() else ''
        print(('{:' + align + str(lengths[m['key']]) + '} ').format(
            m['key']), end='')
    print('')
    # print the table contents
    for v in values:
        for m in _meta:
            align = m['align'] if 'align' in m.keys() else ''
            print(('{:' + align + str(lengths[m['key']]) + '} ').format(
                v[m['key']]), end='')
        print('')

