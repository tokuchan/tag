#!/usr/bin/env python
# Copyright 2014 (C) Sean R. Spillane
# This program is hereby released under the BSD license.

import argparse
import logging
import re
import hashlib

from Monads.Maybe import *
from TagDB.TagDB import *

from functools import reduce

def list_tag(args):
    '''
    This function is used to process command lines for listing tags.
    '''
    file_name = args.file
    log = logging.getLogger("tags")
    log.info("Called tags")
    log.info("Getting tags for {}".format(file_name))
    log.info("Starting DB.")
    tagdb = TagDB()
    log.info("Reading file contents to compute SHA hash.")
    hashData = hashFile(file_name)
    log.info("Getting tags.")
    tag_set = tagdb.get(hashData)
    log.debug("Parsed values are: {}".format(tag_set))
    for tag in tag_set.fromMaybe(set()):
        print(tag)

def get_tag(args):
    '''
    This function is used to process command lines for listing files.
    '''
    tag_list = args.tags
    log = logging.getLogger("get")
    log.info("Called get")
    log.info("Getting paths for expression {}".format(tag_list))
    log.info("Starting DB.")
    tagdb = TagDB()
    file_set = map(lambda x: tagdb.get(x).fromMaybe(set()),tag_list)
    file_set = reduce(lambda x, y: x | y,file_set)
    log.debug("Raw file list is: {}".format(file_set))
    for fileName in file_set:
        print(fileName)

def set_tag(args):
    '''
    This function is used to process command lines for setting tags on files.
    '''
    log = logging.getLogger("set")
    log.info("Called set")
    log.info("Starting DB.")
    tagdb = TagDB()
    log.info("Getting file name.")
    fileName = args.file
    log.debug("File name is: {}.".format(fileName))
    hashData = hashFile(fileName)
    log.debug("File hash is: {}.".format(hashData))
    log.info("Getting tag list.")
    tagList = args.tags
    log.debug("Tag list is: {}.".format(tagList))
    log.info("Processing tag list expression.")
    (m,d,e) = process(tagList)
    addTags = (m | d) - e
    remTags = e
    log.debug("Tags to add are: {}.".format(addTags))
    log.debug("Tags to remove are: {}.".format(remTags))
    oldTags = tagdb.get(hashData).fromMaybe(set())
    log.debug("Old tags are: {}.".format(oldTags))
    newTags = (oldTags | addTags) - remTags
    assert(newTags is not None)
    log.debug("New tags are: {}.".format(newTags))
    log.info("Setting {}'s new tags.".format(hashData))
    for tag in oldTags:
        log.debug("Removing path from tag: {}.".format(tag))
        tagData = tagdb.get(tag).fromMaybe(set())
        tagdb.set(tag,tagData - set([hashData]))
    for tag in newTags:
        log.debug("Setting tag: {} to include path.".format(tag))
        tagData = tagdb.get(tag).fromMaybe(set())
        tagdb.set(tag,tagData | set([hashData]))
    log.debug("Setting file {} to point to tags.".format(hashData))
    tagdb.set(hashData, newTags)

def process(tagList):
    '''Given a list of tag expressions, return a triple of lists: (mandatory tags, discretional tags, excluded tags).'''
    mandatories = set()
    discretionals = set()
    excluded = set()
    for tag in tagList:
        match = re.match("^\+(.*)$", tag)
        if match:
            mandatories.add(match.group(1))
        else:
            match = re.match("^\-(.*)$", tag)
            if match:
                excluded.add(match.group(1))
            else:
                discretionals.add(tag)
    return (mandatories,discretionals,excluded)

def hashFile(fileName):
    '''Given a path to a file, return the SHA256 of its contents.'''
    log = logging.getLogger("hashFile")
    log.debug("Hashing file name: {}".format(fileName))
    hashData = hashlib.sha256()
    with open(fileName) as f:
        for line in f:
            hashData.update(line.encode())
    hashData = hashData.hexdigest()
    log.debug("Hash is: {}".format(hashData))
    return hashData

def parser(log):
    parser = argparse.ArgumentParser(description="A program that tags arbitrary files with arbitrary strings.")
    parser.add_argument("--verbose", action="store_true", help="If set, make the application emit DEBUG log statements.")
    parser.add_argument("--quiet",   action="store_true", help="If set, make the application silent except for errors.")

    subparsers = parser.add_subparsers(help="Action to perform.")

    parser_tag = subparsers.add_parser("tags", help="Given a file, return the set of associated tags.")
    parser_tag.set_defaults(func=list_tag)
    parser_tag.add_argument("file", help="Specifies the file to list.")

    parser_get = subparsers.add_parser("get",  help="Given a tag expression, return the set of matching files.")
    parser_get.set_defaults(func=get_tag)
    parser_get.add_argument("tags", help="Specifies the tag expression to match.", nargs=argparse.REMAINDER)

    parser_set = subparsers.add_parser("set",  help="Given a file and a tag expression, apply the expression to the file.")
    parser_set.set_defaults(func=set_tag)
    parser_set.add_argument("file", help="Specifies the file to tag.")
    parser_set.add_argument("tags", help="Specifies the tag expression to apply.", nargs=argparse.REMAINDER)

    args = parser.parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)
        log.debug("Maximum verbosity enabled!")
    if args.quiet:
        log.setLevel(logging.WARNING)

    return args

def main():
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger()
    args = parser(log)
    log.info("Starting program")
    args.func(args)
    log.info("Program complete")
    logging.shutdown()

if __name__ == '__main__':
    main()
