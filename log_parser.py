#!/usr/bin/env python3

from __future__ import annotations
import os
from re import VERBOSE
from log import Log, LogType
from enum import Enum
from math import sqrt, pow
from typing import Annotated, Union, Literal
import traceback
from html import unescape as html_unescape

HEARING_RANGE = 9

class NotSortableException(Exception): pass
class InvalidType(Exception): pass
class UnsupportedLogTypeException(Exception): pass

class LogFileType(Enum):
    UNKNOWN = 0
    COLLATED = 1
    GAME = 2
    ATTACK = 3
    PDA = 4
    SILICON = 5
    MECHA = 6
    VIRUS = 7
    TELECOMMS = 8
    UPLINK = 9
    SHUTTLE = 10
    TGUI = 11

    @staticmethod
    def parse_log_file_type(string: str):
        try:
            return LogFileType[string.upper()]
        except:
            return LogFileType.UNKNOWN
class LogFile:
    """An object representing a log file. Most functions use `self.work_set`, original logs sotred in `self.logs`.

    Parameters:
    `logs` (list[str]): list of log lines
    `type` (LogFileType): type of the log file
    `verbose` (bool): toggles verbose mode
    `quiet` (bool): toggles quiet mode

    Examples:

    `log_file = LogFile() # Empty log file, useful for combining more later using `collate``,
    `log_file = LogFile(open("game.log").readlines(), LogFileType.UNKNOWN)`,
    `log_file = LogFile(["logline 1", "log line 2", "log line 3"]) # NOTE: must be a valid log or the parser will raise an exception`
    """
    round_id: Annotated[int, "Stores the round ID. If unknown, it will equal -1"]
    unfiltered_logs: Annotated[list[Log], "Stores a list of all logs"]
    logs: Annotated[list[Log], "Stores a list of filtered logs"]
    who: Annotated[list[str], "Stores a list of all connected ckeys"]
    sortable: bool
    log_source: Annotated[str, "Source of the logs (if available)"]

    def __init__(self, logs: list[str] = [], type: LogFileType = LogFileType.UNKNOWN, verbose: bool = False, quiet: bool = False) -> None:
        if verbose and quiet:
            print("Really? You want me to be silent and verbose? Those are mutually exclusive you know")
        self.round_id = -1
        self.unfiltered_logs = []
        self.logs = []
        self.who = []
        self.sortable = True
        self.log_type = type
        
        if not logs: return
        if "Starting up round ID" in logs[0]:
            self.round_id = int(logs[0].split("Starting up round ID ")[1].strip(". \r\n")) # Also remove \r\n just in case, had some errors with that before
            logs = logs[2:]

        for line in logs:
            if not line: continue
            try:
                line = line.strip("\r\n ")
                if line.startswith("-censored"): continue # Skip censored lines
                # VOTE is split into multiple lines, so account for that
                if line.startswith("- <b>") and self.unfiltered_logs and self.unfiltered_logs[-1].log_type == LogType.VOTE:
                    self.unfiltered_logs[-1].text += ", " + html_unescape(line.replace("- <b>", "").replace("</b>", ""))
                    continue
                # Priority announcements (and others like it) sometimes do this
                elif line.startswith("- ") and self.unfiltered_logs:
                    # Don't actually insert a new line
                    line = self.unfiltered_logs[-1].raw_line + "\\n" + line.replace("- ", "")
                    # Remove the incomplete entry (so we can parse location too!)
                    self.unfiltered_logs.pop()
                log = Log(line)
                self.unfiltered_logs.append(log)
                if log.agent and log.agent.ckey and log.agent.ckey.replace("[DC]","") not in self.who: self.who.append(log.agent.ckey.replace("[DC]",""))
            except Exception as e:
                if not quiet: print(f"Could not be parsed: '{line}', with the reason:", e)
                if verbose: traceback.print_exc()
        self.unfiltered_logs.sort(key=lambda l:l.time)
        self.logs = self.unfiltered_logs

    def __len__(self) -> int:
        """Returns the length of the logs array"""
        return self.logs.__len__()

    def add_log(self, log: Log, reset_workset: bool = True, sort: bool = True) -> None:
        """Appends a log entry to the end.
        
        Parameters:
        `log` (Log): the Log object to be added
        `reset_workset` (bool): if we should also reset the working set
        `sort` (bool): if we should also sort the logs afterwards

        NOTE: the log variable MUST be of type Log

        Returns None
        """
        if not isinstance(log, Log): raise InvalidType(f"Type Log required but type {str(type(log))} was found")
        self.unfiltered_logs.append(log)
        if reset_workset:
            self.reset_work_set()
        if sort:
            self.sort()

    def add_logs(self, logs: list[Log], reset_workset: bool = True, sort: bool = True) -> None:
        """Appends a list of log entries to the end.
        
        Parameters:
        logs (list[Log]): the Log objects list to be added
        `reset_workset` (bool): if we should also reset the working set
        `sort` (bool): if we should also sort the logs afterwards

        Returns None
        """
        self.unfiltered_logs.extend(logs)
        if reset_workset:
            self.reset_work_set()
        if sort:
            self.sort()

    def sort(self) -> None:
        """Sorts the current work set, using the time at which the log was added, descending
        
        Example call: `my_log.sort()`
        
        Returns None"""
        if not self.sortable: raise NotSortableException("Not enough information to sort the logs")
        self.logs.sort(key=lambda l:l.time)

    def collate(self, logfile: LogFile) -> None:
        """Collates (extends, adds together) two LogFile objects and changes the LogFileType to COLLATED.
        The result is stored in the the object this was called on. A call to this function will reset the
        current work set.
        
        Parameters:
        `logfile` (LogFile): the LogFile object you want to combine

        Example: `my_log = LogFile()` `my_log.collate(LogFile.from_file("game.txt"))` `my_log.collate(LogFile.from_file("attack.txt"))`

        Returns `None`
        """
        self.add_logs(logfile.unfiltered_logs, sort=True)
        self.log_type = LogFileType.COLLATED
        self.who.extend(logfile.who)
        self.who = list(set(self.who)) # Remove duplicates
        self.who.sort()
        self.logs = self.unfiltered_logs

    def filter_ckeys(self, *ckeys: str) -> None:
        """Removes all logs in which the specified ckeys are not present, saving the result in self.work_set. Works much like Notepad++,
        but only counts the agent (actor, the one who performed the action). See `filter_strings` for a function like Notepad++ bookmark
        
        Parameters:
        `ckeys` (tuple[str, ...]): ckeys to filter

        Example call: `my_log.filter_ckeys("ckey1", "ckey2")` (as many or little ckeys as you want)
        
        Returns `None`"""
        filtered = []
        for log in self.logs:
            if log.agent and log.agent.ckey in ckeys:
                filtered.append(log)
        if not filtered:
            print("Operation completed with empty set. Aborting.")
            return
        self.logs = filtered

    def filter_strings(self, *strings: str) -> None:
        """Removes all logs in which the specified strings are not present, saving them in `self.work_set`. Works exactly like Notepad++ bookmark
        
        Parameters:
        `strings` (tuple[str, ...]): strings to filter

        Example calls: `my_log.filter_strings("Hi!")`, `my_log.filter_strings("attacked", "injected", "I hate you")` (as many strings as you want)
        
        Returns `None`"""
        filtered = []
        for log in self.logs:
            for string in strings:
                if string in log.raw_line:
                    filtered.append(log)
                break
        if not filtered:
            print("Operation completed with empty set. Aborting.")
            return
        self.logs = filtered

    def filter_heard(self, ckey: str) -> None:
        """Removes all log entries which could not have been heard by the specified ckey (very much in alpha) and stores the remaining lines in `self.work_set`
        
        Parameters:
        `ckey` (str): desired ckey

        Example call: `my_log.filter_heard("ckey")`
        
        Returns `None`"""
        self.logs = self.get_only_heard(ckey)

    def filter_conversation(self, *ckeys: str) -> None: # TODO: hide lines not in conversation
        """Tries to get a conversation between multiple parties, excluding what they would and would not hear. Only accounts for local say (for now). Saves the result in `self.work_set`
        
        Parameters:
        `ckeys` (tuple[str, ...]): ckeys to use for sorting

        Example call: `my_log.filter_conversation("ckey1", "ckey2", "ckey3")` (as many or little ckeys as you want)
        
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
        self.logs = final

    def reset_work_set(self):
        """Removes all filters; sets the working set to be equal to all logs
        
        Example call: my_log.reset_work_set()"""
        self.logs = self.unfiltered_logs

    def get_only_heard(self, ckey: str, logs_we_care_about: Union[list[LogType], Literal["ALL"]] = "ALL") -> list[Log]:
        """Removes all log entries which could not have been heard by the specified ckey (very much in alpha). Uses logs from `self.work_set`

        Parameters:
        `ckey` (str): ckeys to use
        `logs_we_care_about` (list[LogType])

        Example calls: `my_log.get_only_heard("ckey")`, `my_log.get_only_heard("ckey", "ALL")`, `my_log.get_only_heard("ckey", [LogType.SAY, LogType.WHISPER])`
        
        Returns `list[Log]`"""
        self.sort()
        walking_error = 4
        # Adjust for error created by lack of logs
        hearing_range = HEARING_RANGE + walking_error
        filtered = []
        cur_loc = (0, 0, 0)
        last_loc = cur_loc
        for log in self.logs:
            # Check for ckey. If our target was included in the action we can safely assume they saw it
            if (log.agent and ckey == log.agent.ckey) or (log.patient and ckey == log.patient.ckey) or (log.text and f"{ckey}/(" in log.text): 
                # If there's a location attached, update it
                if log.location:
                    last_loc = cur_loc
                    cur_loc = log.location
                filtered.append(log)
                continue
            # If our target didn't participate, we need to check how far away it happened

            # Check z-level, if they differ save location and continue
            if not cur_loc[2] == last_loc[2]: 
                continue
            # Filter logs that we don't care about but still use their location
            if logs_we_care_about and (logs_we_care_about != "ALL"):
                continue
            if type(logs_we_care_about) == list and not log.log_type in logs_we_care_about:
                continue

            # Calculate distance
            #if sqrt(pow(cur_loc[0] - log.location[0], 2) + pow(cur_loc[1] - log.location[1], 2)) - hearing_range < 0:
            if abs(cur_loc[0] - log.location[0]) - hearing_range < 0 and abs(cur_loc[1] - log.location[1]) - hearing_range < 0:
                filtered.append(log)
            elif log.log_type == LogType.TCOMMS:
                filtered.append(log)

        return filtered

    def filter_by_location_name(self, location_name: str) -> None:
        """Removes all logs that did not happen in the specified location,
        and stores the result in the work set.
        
        Parameters:
        `location_name` (str): the name of the location, case insensitive

        Example call: my_log.filter_by_location_name("Bar")
        
        Returns `None`"""
        filtered = []
        for log in self.logs:
            if location_name.lower() == log.location_name.lower():
                filtered.append(log)
        if not filtered:
            print("Operation completed with empty set. Aborting.")
            return
        self.logs = filtered

    def filter_by_radius(self, location: tuple[int, int, int], radius: int) -> None:
        """Removes all logs that did not happen in the specified radius around the location,
        and stores the result in the work set.
        
        Parameters:
        `location` (tuple[int, int, int]): the location
        `radius` (int): the radius

        Example call: `my_log.filter_by_radius((32, 41, 2), 5)`
        
        Returns None"""
        filtered = []
        for log in self.logs:
            # Z level must match
            if log.location[2] != location[2]: continue
            if abs(location[0] - log.location[0]) - radius < 0 and abs(location[1] - log.location[1]) - radius < 0:
                filtered.append(log)
        if not filtered:
            print("Operation completed with empty set. Aborting.")
            return
        self.logs = filtered

    def print_working(self) -> None:
        """Prints working set to the console
        
        Example call: `my_log.print_working()`
        
        Returns `None`"""
        if not self.logs:
            print("Working set empty")
            return
        for log in self.logs:
            print(log.raw_line)

    def head(self, n: int = 10) -> None:
        """Prints the first few lines of the working set to the console.

        Parameters:
        `n` (int): number to print, defaults to 10

        Example call: `my_log.head()`

        Returns `None`"""
        if not self.logs:
            print("Working set empty")
            return
        for log in self.logs[:n]:
            print(log.raw_line)

    def tail(self, n: int = 10) -> None:
        """Prints the last few lines of the working set to the console.

        Parameters:
        `n` (int): number to print, defaults to 10

        Example call: `my_log.tail()`

        Returns `None`"""
        if not self.logs:
            print("Working set empty")
            return
        for log in self.logs[-n:]:
            print(log.raw_line)

    def write_working_to_file(self, filename: str) -> None:
        """Writes current `self.work_set` to the desired file.
        
        Parameters:
        `filename` (str): name of the file to write to (overwrites everything)

        Example call: `my_log.write_working_to_file("logs.txt")`
        
        Returns None"""
        with open(filename, "w", encoding = "utf-8") as f:
            for log in self.logs:
                f.write(str(log) + "\n")
            from version import VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH
            f.write(f"Created using LogBuddy v{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH} https://github.com/RigglePrime/LogBuddy\n")
            if self.log_source:
                f.write(f"Logs acquired from {self.log_source}")

    @staticmethod
    def from_file(filename: str, log_type: LogFileType = None, verbose: bool = False, quiet: bool = False) -> LogFile:
        """Parses the specified log file
        
        Parameters:
        `filename` (str): name (and location) of the desired file
        `type` (LogFileType): type of the log. Use if you want to override log type detection (optional, defaults to LogFileType.UNKNOWN)
        `verbose` (bool): toggle verbose mode (False by default)
        `quiet` (bool): toggle quiet mode (False by default)

        Example call: `my_log = LogFile.from_file("game.txt")`
        
        Returns LogFile"""
        if filename.endswith(".html"): UnsupportedLogTypeException(f"{filename} does not seem to be supported")
        if not log_type and "." in filename:
            log_type = LogFileType.parse_log_file_type(filename.split(".", 1))
        with open(filename, "r", encoding = "utf-8") as f:
            lines = f.readlines()
        return LogFile(lines, log_type, verbose, quiet)

    @staticmethod
    def from_folder(folder: str, verbose: bool = False, quiet: bool = False) -> LogFile:
        """Parses all log files in a folder, combining them into a single file
        
        Parameters:
        `filename` (str): name (and location) of the desired folder
        `verbose` (bool): toggle verbose mode (False by default)
        `quiet` (bool): toggle quiet mode (False by default)

        Example call: `my_log = LogFile.from_file("game.txt")`
        
        Returns `LogFile`"""
        if not os.path.isdir(folder): raise Exception("Is not a folder")
        folder = folder.replace("\\", "/")
        if folder[-1] != "/": folder += "/"
        log_collection = LogFile()
        for file in os.listdir(folder):
            if not quiet: print("Parsing", file)
            try:
                log_collection.collate(LogFile.from_file(folder + file, verbose=verbose, quiet=quiet))
            except UnsupportedLogTypeException:
                if not quiet: print(f"{file} isn't supported, skipping")
                continue
        return log_collection

    @staticmethod
    def from_logs_link(link: str, logs_we_care_about: list[str] = None, verbose: bool = False, quiet: bool = False) -> LogFile:
        """Downloads multiple files from a public logs link. The link should look like
        `https://tgstation13.org/parsed-logs/{server}/data/logs/{year}/{month}/{day}/round-{round_id}/`,
        but with actual values inserted.

        Parameters:
        `logs_we_care_about` (list[str]): list of strings, containing the file names. For example: `["game.txt", "attack.txt"]`.This defaults to all supported files.
        `verbose` (bool): toggle verbose mode (False by default)
        `quiet` (bool): toggle quiet mode (False by default)

        Example call: `my_log = LogFile.from_logs_link("link here")`

        Returns `LogFile`"""
        import requests as req
        # Should be all supported log types as a default. Don't forget to update this list! (you will)
        if not logs_we_care_about: logs_we_care_about = ["game.txt", "attack.txt", "pda.txt", "silicon.txt", "mecha.txt", "virus.txt", "telecomms.txt", "uplink.txt", "shuttle.txt"]
        if not link[-1] == "/": link += "/"
        log_collection = LogFile()
        for log_file in logs_we_care_about:
            if not quiet: print(f"Retrieving {log_file}")
            r = req.get(link + str(log_file))
            if not r.ok:
                if not quiet: print(f"Error {r.status_code} while retrieving {log_file}")
                continue
            log_collection.collate(LogFile(r.text.replace("\r", "").split("\n"), verbose=verbose, quiet=quiet))
        log_collection.log_source = link
        return log_collection

if __name__ == "__main__":
    import sys
    LogFile.from_file(sys.argv[1]).print_working()
