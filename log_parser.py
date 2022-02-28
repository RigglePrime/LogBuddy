#!/usr/bin/env python3

from __future__ import annotations
import os
from re import VERBOSE
from log import Log, LogType
from enum import Enum
from math import sqrt, pow
from typing import Annotated
import traceback

HEARING_RANGE = 9

class NotSortableException(Exception): pass
class InvalidType(Exception): pass

class LogFileType(Enum):
    UNKNOWN = 0
    GAME = 1
    ATTACK = 2
    COLLATED = 3

class LogFile:
    """An object representing a log file. Most functions use `self.work_set`, original logs sotred in `self.logs`.

    Parameters:
    type (LogFileType): type of the log file
    logs (list[str]): list of log lines

    Examples:

    `log_file = LogFile()`,
    `log_file = LogFile(LogFileType.UNKNOWN, open("game.log").readlines())`,
    `log_file = LogFile(logs=["logline 1", "log line 2", "log line 3"]) # NOTE: must be a valid log or the parser will raise an exception`
    """
    round_id: Annotated[int, "Stores the round ID. If unknown, it will equal -1"]
    logs: Annotated[list[Log], "Stores a list of all logs"]
    work_set: Annotated[list[Log], "Stores a list of filtered logs"]
    who: Annotated[list[str], "Stores a list of all connected ckeys"]
    sortable: bool

    def __init__(self, type: LogFileType = LogFileType.UNKNOWN, logs: list[str] = [], verbose: bool = False) -> None:
        self.round_id = -1
        self.logs = [] # Python is dumb. I hate python#
        self.work_set = []
        self.who = []
        self.sortable = True

        self.log_type = type
        if "Starting up round ID" in logs[0]:
            self.round_id = int(logs[0].split("Starting up round ID ")[1].strip(". "))
            logs = logs[2:]

        for line in logs:
            try:
                line = line.strip("\n").strip()
                log = Log(line)
                self.logs.append(log)
                if log.agent and log.agent.ckey and log.agent.ckey.replace("[DC]","") not in self.who: self.who.append(log.agent.ckey.replace("[DC]",""))
            except Exception as e:
                print(f"Could not be parsed: '{line}', with the reason:", e)
                if verbose: traceback.print_exc()
        self.logs.sort(key=lambda l:l.time)
        self.work_set = self.logs

    def add_log(self, log: Log) -> None:
        """Appends a log entry to the end.
        
        Parameters:
        log (Log): the Log object to be added

        NOTE: the log variable MUST be of type Log

        Returns None
        """
        if not isinstance(log, Log): raise InvalidType(f"Type Log required but type {str(type(log))} was found")
        self.logs.append(log)

    def add_logs(self, logs: list[Log]) -> None:
        """Appends a list of log entries to the end.
        
        Parameters:
        logs (list[Log]): the Log objects list to be added

        Returns None
        """
        self.logs.extend(logs)

    def sort(self) -> None:
        """Sorts the current work set, using the time at which the log was added, descending"""
        if not self.sortable: raise NotSortableException("Not enough information to sort the logs")
        self.work_set.sort(key=lambda l:l.time)

    def collate(self, logfile: LogFile) -> None:
        """Collates (extends, adds together) two LogFile objects and changes the LogFileType to COLLATED.
        
        Parameters:
        logfile (LogFile): 

        Returns None
        """
        self.add_logs(logfile.logs)
        self.log_type = LogFileType.COLLATED
        self.logs.sort(key=lambda l:l.time)
        self.who.extend(logfile.who)
        self.who = list(set(self.who))
        self.who.sort()

    def filter_ckeys(self, *ckeys: str):
        """Removes all logs in which the specified ckeys are not present, saving the result in self.work_set. Works much like Notepad++,
        but only counts the agent (actor). See filter_strings for a function like Notepad++ bookmark"""
        filtered = []
        for log in self.work_set:
            if log.agent and log.agent.ckey in ckeys:
                filtered.append(log)
        if not filtered:
            print("Operation completed with empty set. Aborting.")
            return
        self.work_set = filtered

    def filter_strings(self, *strings: str):
        """Removes all logs in which the specified strings are not present, saving them in `self.work_set`. Works exactly like Notepad++ bookmark
        
        Parameters:
        strings (tuple[str, ...]): strings to filter
        
        Returns None"""
        filtered = []
        for log in self.logs:
            for string in strings:
                if string in log.raw_line:
                    filtered.append(log)
                break
        if not filtered:
            print("Operation completed with empty set. Aborting.")
            return
        self.work_set = filtered

    def filter_heard(self, ckey: str) -> None:
        """Removes all log entries which could not have been heard by the specified ckey (very much in alpha) and stores the remaining lines in `self.work_set`
        
        Parameters:
        ckey (str): desired ckey
        
        Returns None"""
        self.work_set = self.get_only_heard(ckey)

    def filter_conversation(self, *ckeys: str): # TODO: hide lines not in conversation
        """Tries to get a conversation between multiple parties, excluding what they would and would not hear. Only accounts for local say (for now). Saves the result in `self.work_set`
        
        Parameters:
        ckeys (tuple[str, ...]): ckeys to use for sorting
        
        Returns None"""
        self.filter_ckeys(*ckeys)
        final = []
        for ckey in ckeys:
            final.extend(self.get_only_heard(ckey))

        if not final:
            print("Operation completed with empty set. Aborting.")
            return
        final = list(set(final))
        final.sort(key=lambda l:l.time)
        self.work_set = final

    def reset_work_set(self):
        """Removes all filters; sets the working set to be equal to all logs"""
        self.work_set = self.logs

    def get_only_heard(self, ckey: str) -> list[Log]:
        """Removes all log entries which could not have been heard by the specified ckey (very much in alpha). Uses logs from `self.work_set`

        Parameters:
        ckeys (tuple[str, ...]): ckeys to use for sorting
        
        Returns list[Log]"""
        self.sort()
        logs_we_care_about = [LogType.ATTACK, LogType.EMOTE, LogType.WHISPER, LogType.SAY]
        walking_error = 4
        # Adjust for error created by lack of logs
        hearing_range = HEARING_RANGE + walking_error
        filtered = []
        cur_loc = (0, 0, 0)
        last_loc = cur_loc
        for log in self.work_set:
            # Check if location exists, if not skip
            if not log.location:
                continue
            # Check for ckey, update location
            if log.agent and ckey == log.agent.ckey: 
                last_loc = cur_loc
                cur_loc = log.location
                filtered.append(log)
                continue
            # Check z-level, if they differ save location and continue
            if not cur_loc[2] == last_loc[2]: 
                continue
            # Filter logs that we don't care about but still use their location
            if not log.log_type in logs_we_care_about:
                continue

            # Calculate distance
            #if sqrt(pow(cur_loc[0] - log.location[0], 2) + pow(cur_loc[1] - log.location[1], 2)) - hearing_range < 0:
            if abs(cur_loc[0] - log.location[0]) - hearing_range < 0 and abs(cur_loc[1] - log.location[1]) - hearing_range < 0:
                filtered.append(log)

        return filtered

    def print_working(self) -> None:
        """Prints working set to the console"""
        if not self.work_set:
            print("Working set empty")
            return
        for log in self.work_set:
            print(log.raw_line)

    def write_working_to_file(self, filename: str) -> None:
        """Writes current `self.work_set` to the desired file.
        
        Parameters:
        filename (str): name of the file to write to (overwrites everything)
        
        Returns None"""
        with open(filename, "w") as f:
            for log in self.work_set:
                f.write(str(log) + "\n")

    @staticmethod
    def from_file(filename: str, type: LogFileType = LogFileType.UNKNOWN, verbose: bool = False) -> LogFile:
        """Parses the specified log file
        
        Parameters:
        filename (str): name (and location) of the desired file
        type (LogFileType): type of the log (can be left out)
        
        Returns LogFile"""
        with open(filename, "r") as f:
            lines = f.readlines()
        return LogFile(type, lines, verbose)

    @staticmethod
    def from_folder(folder: str, verbose: bool = False):
        """Parses all log files in a folder"""
        if not os.path.isdir(folder): raise Exception("Is not a folder")
        folder = folder.replace("\\", "/")
        if folder[-1] != "/": folder += "/"
        log_collection = LogFile()
        for file in os.listdir(folder):
            if verbose: print("Parsing", file)
            log_collection.collate(LogFile.from_file(folder + file, verbose=verbose))
        return log_collection

    @staticmethod
    def from_round_id(round_id: int) -> LogFile:
        raise Exception("Not yet implemented!")

if __name__ == "__main__":
    import sys
    LogFile.from_file(sys.argv[1]).print_working()
