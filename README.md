% pyrefs: Refs file system dumps analyzer

# Introduction

`pyrefs` provides a series of libraries helpful to parse and analyze Resilient
FileSystems (ReFS).
An interactive application to analyze a ReFS dump named `Igor` is also
provided.

## Authors

 - Daniel Gracia Pérez <daniel.gracia-perez@cfa-afti.fr>
 - Eric Jouenne <eric.jouenne@cfa-afti.fr>
 - Tony Gerard <tony.gerard@cfa-afti.fr>
 - Francois-Xavier Babin <francois-xavier.babin@cfa-afti.fr>

## Thanks

We would like to thank: Henry Georges, his thesis document has been the
foundation of this project; William Ballantine, for the ReFS dump images on his
website and his ReFS articles; and all the other authors providing information
on the ReFS filesystem.

We would like to also thank Juan Romero, Olivier Gilles, Isabelle and Claudia
Duho, who performed a similar work than ours. Your feedback was unvaluable.

# Dependencies

`pyrefs` was developed using Python 3 (Python 3.6.6) at the time of this
release, and has been tested to work on Windows and Linux platforms.

No special dependencies, if you find any please let us know.

# Sources organization

The sources are organized as follows:

 - root folder:

   - `igor.py`:
   - `part`: contains the functions to parse the ReFS structures

# Igor

An interactive command line tool is provided to facilitate the analysis of
those not willing to play with the code.
We call it `Igor` and it can be launched with Python.

`Igor` provides a limited toolset to analyze ReFS partitions exploiting the
`pyrefs` library, the following sections enumerate them.

## Command reference

### `file`

### `vol`

### `part`

### `find_blocks`

### `find_data_blocks_with_pattern`

### `find_blocks_with_filenames`

### `find_blocks_with_folders`

### `list_filenames`

### `list_folders`

### `entryblock`

### `hexdump`

### `hexblock`

### `tree_control`

### `tree_control_extension`

### `object_tree`

### `allocator`

### `attribute`

### `datastream`

### `list_dataruns`

### `filetree`

### `bye`

### `record`

### `playback`
