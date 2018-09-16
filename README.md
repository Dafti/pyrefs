# Introduction

`pyrefs` provides a series of libraries helpful to parse and analyze Resilient
FileSystems (ReFS).
An interactive application to analyze a ReFS dump named `Igor` is also
provided.

`pyrefs` is still very immature, as of today it has been only tested with
partitions using ReFS version 1.1.
The code is neither far from perfect, and it would need a good refactoring.
We are working on that, but be aware when you retrieve `pyrefs`.

Finally, `pyrefs` naming convention for ReFS structures is mainly guided by
Henry Georges thesis work.
You can find Henry Georges's thesis and the code he developed to analyze ReFS
here <https://brage.bibsys.no/xmlui/handle/11250/2502565>.

## Authors

 - Daniel Gracia Pérez \<<daniel.gracia-perez@cfa-afti.fr>\>
 - Eric Jouenne \<<eric.jouenne@cfa-afti.fr>\>
 - Tony Gerard \<<tony.gerard@cfa-afti.fr>\>
 - Francois-Xavier Babin \<<francois-xavier.babin@cfa-afti.fr>\>

## Thanks

We would like to thank: Henry Georges, his thesis document has been the
foundation of this project; Willi Ballenthin, for the ReFS dump images on his
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

## Examples

Some examples of Igor usage are provided in the `examples` folder as Igor
records.
To execute/playback the examples contained in the `examples` folder download
the `Windows8ReFSImages.zip` file provided by Willi Ballenthin at
<http://www.williballenthin.com/forensics/refs/test_images/>, copy it to the
`examples/dump` folder and uncompress it.
Then you can use igor to test the records in the examples folder with the
command `playback examples/<example_file>`.

## Command reference

### file

Usage: `file [-h] [-i] [-f] [-F] dump`

Load the provided dump file for analysis, and automatically select the ReFS
partition for you.
You can also initialize the list of entryblocks of the partition.

Positional arguments:

 - `dump`: File to use as dump for the analysis.

Optional arguments:

 - `-h`, `--help`: show this help message and exit
 - `-i`, `--initiliaze-entryblocks`: find blocks in provided dump
 - `-f`, `--files`: find files in provided dump (only considered if -i defined)
 - `-F`, `--folders`: find folders in provided dump (only considered if -i
   defined)

### vol

Usage: `vol [-h]`

Dump the volume record information from the current ReFS partition.

Optional arguments:

 - `-h`, `--help`: show this help message and exit

Dump the volume record information from the current ReFS partition.

### part

Usage: `part [-h] [partidx]`

Show available partitions in the currently loaded dump if no parameter is
given, switch to the provided partition if any provided.

Positional arguments:

 - `partidx`: Partition index of the partition to use for analysis

Optional arguments:

 - `-h`, `--help`: show this help message and exit

### find\_entryblocks

Usage: `find_entryblocks [-h] [-f] [-F]`

Find and show all the entryblocks in current partition. If requested number of
files and folders information will be also collected.

Optional arguments:

 - `-h`, `--help`: show this help message and exit
 - `-f`, `--files`: Collect information on the number of files in the
   entryblocks.
 - `-F`, `--folders`: Collect information on the number of folders in the
   entryblocks.

### find\_pattern

Usage: `find_pattern [-h] pattern`

Find a data pattern in all the blocks of the current partition. Special
characters (including spaces, carriage return, etc.) are not allowed in the
pattern, think of escaping them.

Positional arguments:

 - `pattern`: Pattern to find in the current partition blocks.

Optional arguments:

 - `-h`, `--help`: show this help message and exit

### list\_filenames

Usage: `list_filenames [-h]`

List the found filenames from the list of entryblocks with filenames.

Optional arguments:

 - `-h`, `--help`: show this help message and exit

### list\_folders

Usage: `list_folders [-h]`

List the found filename folders from the list of entryblocks with folders.

Optional arguments:

 - `-h`, `--help`: show this help message and exit

### entryblock

Usage: `entryblock [-h] entryblock_identifier`

Dump the provided entryblock identifier as EntryBlock.

Positional arguments:

 - `entryblock_identifier`: entryblock identifier of the EntryBlock to dump

Optional arguments:

 - `-h`, `--help`: show this help message and exit

### tree\_control

Usage: `tree_control [-h] [entryblock_identifier]`

Parse the given entryblock identifier as a TreeControl.
If no entryblock identifier is provided it uses 0x1e as entryblock identifier.

Positional arguments:

 - `entryblock_identifier`: entryblock identifier of the TreeControl to dump

Optional arguments:

 - `-h`, `--help`: show this help message and exit

### tree\_control\_extension

Usage: `tree_control_extension [-h] entryblock_identifier`

Parse the given entryblock identifier as a TreeControlExtension.

Positional arguments:

 - `entryblock_identifier`: entryblock identifier of the TreeControlExtension
   to dump

Optional arguments:

 - `-h`, `--help`: show this help message and exit

### object\_tree

Usage: `object_tree [-h] entryblock_identifier`

Parse the given entryblock identifier as an ObjectTree.

Positional arguments:

 - `entryblock_identifier`: entryblock identifier of the ObjectTree to dump

Optional arguments:

 - `-h`, `--help`: show this help message and exit

### allocator

Usage: `allocator [-h] entryblock_identifier`

Parse the given entryblock identifier as an Allocator.

Positional arguments:

 - `entryblock_identifier`: entryblock identifier of the Allocator to dump

Optional arguments:

 - `-h`, `--help`: show this help message and exit

### attribute

Usage: `attribute [-h] dump_offset`

Parse the given dump offset (in bytes) as an Attribute.

Positional arguments:

 - `dump_offset`: dump offset (in bytes) of the Attribute to dump

Optional arguments:

 - `-h`, `--help`: show this help message and exit

### datastream

Usage:
```
datastream [-h] output_filename output_size
           entryblock_identifier,number_of_blocks
           [entryblock_identifier,number_of_blocks ...]
```

Extract data from dump from the given datarun.
Dataruns can be extracted by exploring the EntryBlocks (command `entryblock`)
or using the `list_dataruns` command.

Positional arguments:

 - `output_filename`: name of the generated output file
 - `output_size`: total amount of data to extract
 - `entryblock_identifier,number_of_blocks`: datarun to follow for the data extraction

Optional arguments:

 - `-h`, `--help`: show this help message and exit

### list\_dataruns

Usage: `list_dataruns [-h]`

Retrieve list of all the files dataruns.

Optional arguments:

 - `-h`, `--help`: show this help message and exit

### filetree

Usage: `filetree [-h] node_id`

Extract the file tree structure from the given node (use node 0x600 by
default).

Positional arguments:

 - `node_id`: node identifier of the node to extract the file tree structure
   from

Optional arguments:

 - `-h`, `--help`: show this help message and exit

### hexdump

Usage: `hexdump [-h] dump_offset size`

Hexdump the number of bytes at the provided offset.

Positional arguments:

 - `dump_offset`: dump offset of the hexdump start
 - `size`: number of bytes to dump

Optional arguments:

 - `-h`, `--help`: show this help message and exit

### hexblock

Usage: `hexblock [-h] entryblock_id`

Hexdump the block with the provided entryblock identifier.

Positional arguments:

 - `entryblock_id`: entryblock identifier to hexdump

Optional arguments:

 - `-h`, `--help`: show this help message and exit

### bye or \<ctrl-d\>

Usage: `bye [-h]`

Exit the program. Are you sure?

Optional arguments:

 - `-h`, `--help`: show this help message and exit

### record

Usage: `record [-h] output_file`

Save the following commands to selected file.
Saved file can be used afterwards for replay with the `playback` command.

Positional arguments:

 - `output_file`: file onto which commands will be saved

Optional arguments:

 - `-h`, `--help`: show this help message and exit

### playback

Usage: `playback [-h] input_file`

Execute the sequence of commands defined in the input file.

Positional arguments:

 - `input_file`: file from which commands to execute will be read

Optional arguments:

 - `-h`, `--help`: show this help message and exit
