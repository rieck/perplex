#!/usr/bin/env python
# -*- coding: utf8 -*-
# Perplex - A Movie Renamer for Plex Metadata
# Copyright (c) 2015 Konrad Rieck (konrad@mlsec.org)

import argparse
import datetime
import gzip
import json
import os
import shutil
import sqlite3
import sys

import progressbar as pb

# Chars to remove from titles
del_chars = '.'
forbiddenCharsInNames = '\\', '/',':','*','?','"','<','>','|'


def find_db(plex_dir, name):
    """ Search for database file in directory """

    for root, dirs, files in os.walk(plex_dir, onerror=errorOut):
        for file in files:
            if file == name:
                databasePath = os.path.join(root, file)
                print("Found Database: " + databasePath)
                return databasePath

    return None


def build_db(plex_dir, movies={}):
    """ Build movie database from sqlite database """

    print("Analyzing Plex database:")
    dbfile = find_db(plex_dir, "com.plexapp.plugins.library.db")

    db = sqlite3.connect(dbfile)

    # Select only movies with year
    query = """
        SELECT id, title, originally_available_at FROM metadata_items
        WHERE metadata_type = 1 AND originally_available_at """

    for row in db.execute(query):
        title = convert([x for x in row[1] if x not in del_chars])
        year = datetime.date.fromtimestamp(row[2]).strftime("%Y")
        movies[row[0]] = (title, year, [])

    # Get files for each movie
    query = """
        SELECT mp.file FROM media_items AS mi, media_parts AS mp
        WHERE mi.metadata_item_id = %s AND mi.id = mp.media_item_id """

    files = 0
    for id in movies:
        try:
            for file in db.execute(query % id):
                movies[id][2].append(file[0])
                files += 1
        except Exception as e:
            errorOut(e);
    db.close()
    print(("%d movies and %d files" % (len(movies), files)))

    return movies

def print_doubles(files):
    print("Found multiple files :")
    for old_name in enumerate(files):
        print(old_name)

def errorOut(error):
    print("Error occured: " + str(error));
    sys.exit(-1)

def convert(s):
    new = ""
    for x in s:
        if x not in forbiddenCharsInNames:
            new += x
    return new

def build_map(movies, dest,printDoubles, directoryToRunOn = "" ,mapping=[] ):
    """ Build mapping to new names """

    for title, year, files in list(movies.values()):
        counter = 0;
        for i, old_name in enumerate(files):
            modifyedDirectory = str(directoryToRunOn).replace("\\", "/")
            modifyedOldName = str(old_name).replace("\\", "/")
            if modifyedDirectory != "" and not str(modifyedOldName).__contains__(modifyedDirectory):
                print("skipping file because not in given directory " + old_name)
                continue
            counter = counter + 1;
            if counter > 1 and printDoubles:
                print_doubles(files)
            _, ext = os.path.splitext(old_name)

            template = "%s (%s)/%s (%s)" % (title, year, title, year)
            template += " - part%d" % (i + 1) if len(files) > 1 else ""
            template += ext

            if dest is None:
                dest, garbage = str(_).rsplit("/", 1)
            else:
                dest = os.path.normpath(dest)

            new_name = os.path.join(dest, *template.split("/"))
            if new_name == old_name:
                continue
            mapping.append((old_name, new_name))

    mapping = [x_y for x_y in mapping if x_y[0].lower() != x_y[1].lower()]
    return mapping

def progressbar(dry):
    if dry:
        widgets = ['']
    else:
        widgets = [pb.Percentage(), ' ', pb.Bar(), ' ', pb.ETA()]
    return pb.ProgressBar(widgets=widgets)

def rename(mapping,dry):
    pbar=progressbar(dry)
    for old_name, new_name in pbar(mapping):
         try:
             if not os.path.exists(os.path.dirname(new_name)):
                 if not dry:
                     os.makedirs(os.path.dirname(new_name))
             if not os.path.exists(new_name):
                 if dry:
                     print(("%s\n    %s" % (old_name, new_name)))
                 else:
                     os.rename(old_name, new_name)
         except Exception as e:
             print("Exception on file " + old_name + " : " + str(e))


def copy_rename(mapping, dest, dry):
    """ Copy and rename files to destination """
    pbar = progressbar(dry)
    for old_name, new_name in pbar(mapping):
        dp = os.path.join(dest, os.path.dirname(new_name))
        fp = os.path.join(dp, os.path.basename(new_name))
        try:
            if not os.path.exists(dp):
                if not dry:
                    os.makedirs(dp)
            if not os.path.exists(fp):
                if dry:
                    print(("%s\n    %s" % (old_name, fp)))
                else:
                    shutil.copy(old_name, fp)
        except Exception as e:
            print("Exception on file " + old_name + " : " + str(e))


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
    parser.add_argument('--dry', action='store_true',
                        help='show dry run of what will happen')
    parser.add_argument('--justRename', metavar='<dir>', type=str,
                        help='renames the original files instead of copying them - provide the <dir> to rename files in')
    parser.add_argument('--printDoubles', action='store_true',
                        help='Print double movies with locations if found')


    parser.set_defaults(dry=False)
    parser.set_defaults(printDoubles=False)
    args = parser.parse_args()

    if (args.justRename is not None and args.justRename is not False) and (args.dest is not None):
        errorOut("Cant provide --dest and --justRename Args at the same time");


    if args.plex:
        movies = build_db(args.plex)
    elif args.load:
        print(("Loading metadata from " + args.load))
        movies = json.load(gzip.open(args.load))
    else:
        print("Error: Provide a Plex database or stored database.")
        sys.exit(-1)

    if args.save:
        print(("Saving metadata to " + args.save))
        with gzip.open(args.save, 'wt', encoding='ascii') as file:
            json.dump(movies, file)

    if args.printDoubles:
        printDoubles = True
    else:
        printDoubles = False

    if args.justRename:
        print(("Building file mapping for each Movie itself"))
        mapping = build_map(movies, None, printDoubles , args.justRename)
        print(("Start Renaming the files in their original path"))
        rename(mapping,args.dry)
    elif args.dest:
        print(("Building file mapping for " + args.dest))
        mapping = build_map(movies, args.dest, printDoubles)
        print(("Copying renamed files to " + args.dest))
        copy_rename(mapping, args.dest, args.dry)
    else:
        if args.printDoubles:
            print("Print doubles can only be used when building the mapping, try it with the --dry parameter")


