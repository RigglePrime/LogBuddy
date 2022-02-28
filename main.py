#!/usr/bin/env python3
import inspect
import os
from typing import Any

# Log is unused, but it's here so the user doesn't have to import it manually
from log import Log
from log_parser import LogFile

# Change the help text, so users can more easily understand what to do
from _sitebuiltins import _Helper
_Helper.__repr__ = lambda self: """Welcome to LogBuddy!
Type help(Log) for information about the log, and help(LogFile) for information about log files.
Type functions(object) for a list of all defined functions and variables(object) for a list of all variables. Both are currently quite bad (I will get to it some day I promise).

If -- More -- is displayed on the bottom of the screen, press enter to advance one line, space to advance a screen or q to quit.

For Python's interactive help, type help(), or help(object) for help about object."""

def functions(cls: object) -> list[tuple[str, Any]]:
    """Returns all methods of an object"""
    return inspect.getmembers(cls, predicate=inspect.ismethod)

def variables(cls: object) -> dict[str, Any]:
    """Returns all variables of an object"""
    return cls.__dict__


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Parses-the-logs')

    parser.add_argument("-v", "--verbose", action="store_true", help="Toggle verbose mode") # TODO: fix option, it gets interpreted as a file
    parser.add_argument("-q", "--quiet", "--silent", action="store_false", help="Toggle silent mode")
    parser.add_argument("--version", action="version", version="LogBuddy v0.1")
    parser.add_argument("file", nargs="?", help="One or multiple log files or a single folder containing log files to parse")
    args = parser.parse_args()

    main_file = LogFile()

    if args.file:
        if len(args.file) == 1 and os.path.isdir(args.file[0]):
            main_file = LogFile.from_folder(args.file[0], verbose=args.verbose)
        else:
            for file in args.file:
                if args.verbose: print("Parsing", file)
                main_file.collate(LogFile.parse_file(file, verbose=args.verbose))

    from IPython import embed
    embed(header="""
    _                ______           _     _       
    | |               | ___ \         | |   | |      
    | |     ___   __ _| |_/ /_   _  __| | __| |_   _ 
    | |    / _ \ / _` | ___ \ | | |/ _` |/ _` | | | |
    | |___| (_) | (_| | |_/ / |_| | (_| | (_| | |_| |
    \_____/\___/ \__, \____/ \__,_|\__,_|\__,_|\__, |
                __/ |                         __/ |
                |___/                         |___/ 
                
    Switching to interactive

    Press tab to autocomplete
    For LogBuddy specific help type 'help' or '?' for IPython's help (without the quotes).
    """, local=locals())
