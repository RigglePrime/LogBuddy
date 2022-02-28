#!/usr/bin/env python3
import code
import inspect
import os
from typing import Any

# Log is unused, but it's here so the user doesn't have to import it manually
from log import Log
from log_parser import LogFile

# Autocomplete
import readline
import rlcompleter
readline.parse_and_bind("tab: complete")

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
    parser.add_argument("file", nargs="+", help="One or multiple log files or a single folder containing log files to parse")
    args = parser.parse_args()

    file_list: list[str] = args.file
    if len(file_list) == 1 and os.path.isdir(file_list[0]):
        folder = file_list[0]
        file_list = os.listdir(folder)
        folder = folder.replace("\\", "/")
        if folder[-1] != "/": folder += "/"
        file_list = [folder + file for file in file_list]

    log_file_list: list[LogFile] = []

    for file in file_list:
        print("Parsing", file)
        log_file_list.append(LogFile.parse_file(file, verbose=args.verbose))

    main_file = LogFile()
    [main_file.collate(lf) for lf in log_file_list]


    code.interact(banner="""
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
    For help type help
    """, local=locals())
