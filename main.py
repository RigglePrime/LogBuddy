#!/usr/bin/env python3
import code
from log_parser import LogFile, parse_file
#import argparse
import sys
from log import Log
from _sitebuiltins import _Helper
import inspect
import readline
import rlcompleter

readline.parse_and_bind("tab: complete")

#parser = argparse.ArgumentParser(description='Parses-the-logs')

if len(sys.argv) < 2: raise Exception("No files provided. Usage: python main.py <logfile1> <logfile2> ...")
main_file = parse_file(sys.argv[1])
for file in sys.argv[2:]:
    main_file.collate(parse_file(file))

_Helper.__repr__ = lambda self: """Welcome to LogBuddy!
Type help(Log) for information about the log, and help(LogFile) for information about log files.
Type functions(object) for a list of all defined functions and variables(object) for a list of all variables. Both are currently quite shitty.

For Python's interactive help, type help(), or help(object) for help about object."""

def functions(cls: object):
    return inspect.getmembers(cls, predicate=inspect.ismethod)

def variables(cls: object):
    return cls.__dict__


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
