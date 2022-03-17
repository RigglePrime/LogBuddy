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
Use right click to copy something, CTRL + C will terminate the program.

To get started, type "LogFile.from_file('game.txt')" (if there is a file named game.txt in the same directory) or "LogFile.from_folder('logs')" (if your game.txt, attack.txt... are stored in a folder named logs)

Type help(Log) for information about the log, and help(LogFile) for information about log files.
Type functions(object) for a list of all defined functions and variables(object) for a list of all variables. Both are currently quite bad (I will get to it some day I promise).

LogBuddy performs all operations on an internal work set, so you can chain filters (functions). To reset the work set, call reset_work_set on your log instance.

If -- More -- is displayed on the bottom of the screen, press enter to advance one line, space to advance a screen or q to quit.

For Python's interactive help, type help(), or help(object) for help about object."""

def functions(cls: object) -> list[tuple[str, Any]]:
    """Returns all methods of an object"""
    return inspect.getmembers(cls, predicate=inspect.ismethod)

def variables(cls: object) -> dict[str, Any]:
    """Returns all variables of an object"""
    return cls.__dict__


if __name__ == "__main__":
    print("LogBuddy starting...")
    import argparse
    parser = argparse.ArgumentParser(description='Parses-the-logs')

    parser.add_argument("-v", "--verbose", action="store_true", help="Toggle verbose mode")
    parser.add_argument("-q", "--quiet", "--silent", action="store_true", help="Toggle silent mode")
    parser.add_argument("--version", action="version", version="LogBuddy v1.1")
    parser.add_argument("file", nargs="*", help="One or multiple log files or a single folder containing log files to parse")
    args = parser.parse_args()

    if args.verbose and args.quiet:
        print("Really? You want me to be silent and verbose? Those are mutually exclusive you know")
        exit(1)

    main_file = LogFile()

    if args.file:
        if len(args.file) == 1 and os.path.isdir(args.file[0]):
            main_file = LogFile.from_folder(args.file[0], verbose=args.verbose)
        else:
            for file in args.file:
                if args.verbose: print("Parsing", file)
                main_file.collate(LogFile.from_file(file, verbose=args.verbose, quiet=args.quiet))

    help = _Helper() # When you bundle everything with pyinstaller, help stops working for some reason
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
