
# Perplex

A Movie Renamer for Plex Metadata

## Overview

This is a simple script for renaming movie files based on Plex
metadata. [Plex](http://plex.tv/) is a software suite for organizing
videos, music and photos.  It can identify movies based on their file
names and retrieve corresponding metadata.  In practice, however, not
all files are named appropriate and thus some movies usually need to
be manually assigned to the corresponding movie title. Unfortunately,
Plex is not able to rename these files and thus if the database is
deleted or re-installed, these files need to be manually fixed again.

The script `perplex.py` solves this problem.  Given an installation of
Plex and the corresponding database of metadata, the script extracts
all movies and renames the corresponding files according to the
retrieved metadata.  To avoid breaking the current installation, the
renamed files are copied to another directory.

## Usage

First, extract all the metadata from the Plex database and save it.

    $ ./perplex.py --save movies.db --plex /var/plex
    Analyzing Plex database: Found 335 movies and 365 files
 	Saving metadata to movies.db

Now start the renaming process. The renamed movies are written to
the given directory.

    $ ./perplex.py --load movies.db --dest ./output
    Loading metadata from movies.db
    Copying renamed files to ./output
	100% |#################################################| Time: 0:00:00

Done.
