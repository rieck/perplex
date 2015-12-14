#!/usr/bin/env python
# -*- coding: utf8 -*-
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

# Chars to remove from titles
del_chars = '.[]()'

def find_db(plex_dir, name):
    """ Search for database file in directory """

    for root, dirs, files in os.walk(plex_dir):
        for file in files:
            if file == name:
                return os.path.join(root, file)

    return None

def build_db(plex_dir, movies={}):
    """ Build movie database from sqlite database """

    print "Analyzing Plex database:",
    dbfile = find_db(plex_dir, "com.plexapp.plugins.library.db")
    db = sqlite3.connect(dbfile)

    # Select only movies with year
    query = """
        SELECT id, title, originally_available_at FROM metadata_items
        WHERE metadata_type = 1 AND originally_available_at """

    for row in db.execute(query):
        title = filter(lambda x: x not in del_chars, row[1])
        year = row[2].split('-')[0]
        movies[row[0]] = (title, year, [])

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
    print "%d movies and %d files" % (len(movies), files)

    return movies


def build_map(movies, dest, mapping=[]):
    """ Build mapping to new names """

    for title, year, files in movies.values():
        for i, old_name in enumerate(files):
            _, ext = os.path.splitext(old_name)

            template = "%s (%s)/%s (%s)" % (title, year, title, year)
            template += " - part%d" % (i + 1) if len(files) > 1 else ""
            template += ext

            dest = os.path.normpath(dest)
            new_name = os.path.join(dest, *template.split("/"))
            mapping.append((old_name, new_name))

    mapping = filter(lambda (x,y): x.lower() != y.lower(), mapping)
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
    elif args.load:
        print "Loading metadata from " + args.load
        movies = json.load(gzip.open(args.load))
    else:
        print "Error: Provide a Plex database or stored database."
        sys.exit(-1)

    if args.save:
        print "Saving metadata to " + args.save
        json.dump(movies, gzip.open(args.save, 'w'))


    if args.dest:
        print "Building file mapping for " + args.dest
        mapping = build_map(movies, args.dest)

        print "Copying renamed files to " + args.dest
        copy_rename(mapping, args.dest)
