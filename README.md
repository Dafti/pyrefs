# Introduction

`pyrefs` provides a series of libraries helpful to parse and analyze Resilient
FileSystems (ReFS).
An interactive application to analyze a ReFS dump named `Igor` is also
provided.

## Authors

 - Daniel Gracia Pérez \<<daniel.gracia-perez@cfa-afti.fr>\>
 - Eric Jouenne \<<eric.jouenne@cfa-afti.fr>\>
 - Tony Gerard \<<tony.gerard@cfa-afti.fr>\>
 - Francois-Xavier Babin \<<francois-xavier.babin@cfa-afti.fr>\>

## Thanks

We would like to thank: Henry Georges, his thesis document has been the
foundation of this project; William Ballantine, for the ReFS dump images on his
website and his ReFS articles; and all the other authors providing information
on the ReFS filesystem.

We would like to also thank Juan Romero, Olivier Gilles, Isabelle Isabelle
Moukala-Mouberi and Claudia Duhoo, who performed a similar work than ours.
Your feedback was unvaluable.

# Dependencies

`pyrefs` was developed using Python 3 (Python 3.6.6) at the time of this
release, and has been tested to work on Windows and Linux platforms.

No special dependencies, if you find any please let us know.

# Sources organization

```
.
+-- README.md
+-- LICENSE
+-- igor.py
+-- part
|   +-- refs
|       +-- allocator.py
|       +-- attribute.py
|       +-- entry_block.py
|       +-- object.py
|       +-- object_tree.py
|       +-- tree_control.py
|       +-- vol.py
+-- media
|   +-- gpt.py
|   +-- mbr.py
+-- util
|   +-- carving.py
|   +-- filetree.py
|   +-- hexdump.py
|   +-- table.py
|   +-- time.py
+-- examples
    +-- carving.rec
    +-- filetree.rec
    +-- tree_explorer.rec
```

# Igor

An interactive command line tool is provided to facilitate the analysis of
those not willing to play with the code.
We call it `Igor` and it can be launched with Python.

`Igor` provides a limited toolset to analyze ReFS partitions exploiting the
`pyrefs` library, the following sections enumerate them.

## Command reference

### file

Command format:
```
file <dump filename>
```

### vol

Command format:
```
vol
```

### part

Command format:
```
part <partition index>
```

### find\_blocks

### find\_data\_blocks\_with\_pattern

### find\_blocks\_with\_filenames

### find\_blocks\_with\_folders

### list\_filenames

### list\_folders

### entryblock

Command format:
```
entryblock <entryblock identifier>
```

### hexdump

Command format:
```
hexdump <dump offset address>
```

### hexblock

`hexblock` is a specialized version of `hexdump`.
It takes as input the entryblock identifier and dumps in hexadecimal format the
correspondent entryblock completely.

Command format:
```
hexblock <entryblock identifier>
```

### tree\_control

Parses the given entryblock identifier as TreeControl.
If no entryblock is provided it uses 0x1e as entryblock identifier.

Command format:
```
tree_control <entryblock identifier>
```

### tree\_control\_extension

Command format:
```
tree_control_identifier <entryblock identifier>
```

### object\_tree

Command format:
```
object_tree <entryblock identifier>
```

### allocator

Command format:
```
allocator <entryblock identifier>
```

### attribute

Command format:
```
attribute <dump offset address>
```

### datastream

Command format:
```
datastream [<entryblock identifier> <number of blocks>]+
```

### list\_dataruns

Command format:
```
list_dataruns
```

### filetree

Command format:
```
filetree [<node identifier>]
```

### bye

Command format:
```
bye
```

### record

Command format:
```
record <filename>
```

### playback

Command format:
```
playback <filename>
```
