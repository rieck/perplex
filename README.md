
# Perplex

A Movie Renamer for Plex Metadata

## Overview

This simple Python script for renaming movie files in a Plex database.
[Plex](http://plex.tv/) is a software suite for organizing videos,
music and photos.  It can identify movies based on their file names
and retrieve corresponding metadata.  In practice, however, not all
file names are appropriate and thus some movies usually need to be
assigned to the corresponding movie titles manually.  Unfortunately,
Plex is not able to rename these files and thus if the database is
initialized from the scratch these files need to be manually fixed
again.

The Python script `perplex` solves this problem.  Given an
installation of Plex and the corresponding database, it lists all
imported movies and renames them according to the retrieved movie
metadata.  To avoid breaking the current installation, the renamed
files are copied to another directory.

That's it.
