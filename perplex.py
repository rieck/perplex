#!/usr/bin/env python
# Perplex - A Movie Renamer for Plex Metadata
# Copyright (c) 2015 Konrad Rieck (konrad@mlsec.org)

import argparse
import gzip
import json
import os
import shutil
import sqlite3
import sys

import progressbar as pb

# Default path to metadata database
dbpath = "Plug-in Support/Databases/com.plexapp.plugins.library.db"


def build_db(plex_dir, movies={}):
    """ Build movie database from sqlite database """

    print "Analyzing Plex database: ",
    dbfile = os.path.join(plex_dir, *dbpath.split("/"))
    db = sqlite3.connect(dbfile)

    # Select only movies with year
    query = """
        SELECT id, title, year FROM metadata_items
        WHERE metadata_type = 1 AND year """

    for row in db.execute(query):
        movies[row[0]] = (row[1], row[2], [])

    # Get files for each movie
    query = """
        SELECT mp.file FROM media_items AS mi, media_parts AS mp
        WHERE mi.metadata_item_id = %s AND mi.id = mp.media_item_id """

    files = 0
    for id in movies:
        for file in db.execute(query % id):
            movies[id][2].append(file[0])
            files += 1

    db.close()
    print "Found %d movies and %d files" % (len(movies), files)

    return movies


def build_map(movies, mapping=[]):
    """ Build mapping to new names """

    for title, year, files in movies.values():
        for i, old_name in enumerate(files):
            _, ext = os.path.splitext(old_name)

            template = "%s (%s)/%s (%s)" % (title, year, title, year)
            template += " - part%d" % (i + 1) if len(files) > 1 else ""
            template += ext

            new_name = os.path.join(*template.split("/"))
            mapping.append((old_name, new_name))

    return mapping


def copy_rename(mapping, dest):
    """ Copy and rename files to destination """

    widgets = [pb.Percentage(), ' ', pb.Bar(), ' ', pb.ETA()]
    pbar = pb.ProgressBar(widgets=widgets)

    for old_name, new_name in pbar(mapping):
        dp = os.path.join(dest, os.path.dirname(new_name))
        fp = os.path.join(dp, os.path.basename(new_name))

        try:
            if not os.path.exists(dp):
                os.makedirs(dp)

            if not os.path.exists(fp):
                shutil.copy(old_name, fp)

        except Exception, e:
            print str(e)


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Plex-based Movie Renamer.')
    parser.add_argument('--plex', metavar='<dir>', type=str,
                        help='set directory of Plex database.')
    parser.add_argument('--dest', metavar='<dir>', type=str,
                        help='copy and rename files to directory')
    parser.add_argument('--save', metavar='<file>', type=str,
                        help='save database of movie titles and files')
    parser.add_argument('--load', metavar='<file>', type=str,
                        help='load database of movie titles and files')

    args = parser.parse_args()

    if args.plex:
        movies = build_db(args.plex)
        mapping = build_map(movies)
    elif args.load:
        print "Loading metadata from " + args.load
        movies, mapping = json.load(gzip.open(args.load))
    else:
        print "Error: Provide a Plex database or stored database."
        sys.exit(-1)

    if args.save:
        print "Saving metadata to " + args.save
        json.dump((movies, mapping), gzip.open(args.save, 'w'))

    if args.dest:
        print "Copying renamed files to " + args.dest
        copy_rename(mapping, args.dest)
