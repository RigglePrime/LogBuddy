from dateutil.parser import isoparse
from datetime import datetime
from enum import Enum
from typing import Annotated, Tuple, Optional
import re

class LogType(Enum):
    UNKNOWN = 0
    ACCESS = 1
    GAME = 2
    ADMIN = 3
    OOC = 4
    SAY = 5
    WHISPER = 6
    EMOTE = 7
    ATTACK = 8
    VOTE = 9

    @staticmethod
    def parse_log_type(string: str):
        try:
            return LogType[string.upper()]
        except:
            return LogType.UNKNOWN
    
class Player:
    ckey: Optional[str]
    mob_name: Optional[str]

    def __init__(self, ckey: str, mob_name: str) -> None:
        self.ckey = None if ckey == "*no key*" else ckey
        self.mob_name = mob_name

    @staticmethod
    def parse_player(string: str):
        """Gets player's ckey and name from the following format: 'ckey/(name)' (parentheses not required)"""
        ckey, name = string.strip().split("/", 1)
        return Player(ckey, name.strip("()"))

    @staticmethod
    def parse_players_from_full_log(string: str):
        """Gets all players from a full log line. Currently not implemented. (will be soon hopefully)"""
        # (\w+|\*no key\*)\/\(((?:\w+ ?)+?)\)
        # The above regex is not yet good enough, it catches "MY NAME/(John Smith)" as the ckey "NAME"

        # ((?:\w+ ?)+|\*no key\*)\/\(((?:\w+ ?)+?)\)
        # Above does not work since it catches "has grabbed MY NAME/(John Smith)" as the ckey "has grabbed MY NAME"
        raise Exception("Not yet implemented")

class UnknownLogException(Exception): pass

class Log:
    """Represents one log entry
    
    Examples:
    log = `Log("log line here")` # NOTE: must be a valid log entry"""
    def __init__(self, line: Optional[str] = None) -> None:
        if not line or line[0] != "[": raise UnknownLogException("Does not start with [")
        self.raw_line = line
        dt, other = self.raw_line.split("] ", 1)
        self.time = isoparse(dt[1:]) # Remove starting [
        log_type, other = other.split(": ", 1)
        self.log_type = LogType.parse_log_type(log_type)
        # Python go brrrrrrr
        f = getattr(self, f"parse_{self.log_type.name.lower()}", None)
        if f: f(other)

    time: Annotated[datetime, "Time of logging"] = None
    agent: Annotated[Optional[Player], "Player performing the action"] = None
    patient: Annotated[Optional[Player], "Player receiving the action"] = None
    raw_line: Annotated[str, "Raw, unmodified line"] = None
    log_type: Annotated[LogType, "Type of the log"] = None
    location: Annotated[Optional[Tuple[int,int,int]], "X, Y, Y where the action was performed"] = None
    location_name: Annotated[Optional[str], "Name of the location where the action was performed"] = None
    text: Annotated[Optional[str], "Any remaining unparsed text"] = None
    is_dead: Annotated[Optional[bool], "Is the agent dead?"] = None

    def parse_game(self, log: str) -> None:
        """Parses a game log entry from `GAME:` onwards (GAME: should not be included)"""
        self.text = log

    def parse_access(self, log: str) -> None:
        """Parses a game log entry from `ACCESS:` onwards (ACCESS: should not be included)"""
        self.text = log

    def parse_admin(self, log: str):
        """Parses a game log entry from `ADMIN:` onwards (ADMIN: should not be included)"""
        self.text = log

    def parse_ooc(self, log: str):
        """Parses a game log entry from `OOC:` onwards (OOC: should not be included)"""
        self.generic_say_parse(log)

    def parse_say(self, log: str):
        """Parses a game log entry from `SAY:` onwards (SAY: should not be included)"""
        self.generic_say_parse(log)

    def parse_whisper(self, log: str):
        """Parses a game log entry from `WHISPER:` onwards (WHISPER: should not be included)"""
        self.generic_say_parse(log)

    def parse_emote(self, log: str) -> None:
        """Parses a game log entry from `EMOTE:` onwards (EMOTE: should not be included)"""
        agent, other = log.split(") ", 1) # Ensure that we didn't get a name with spaces
        self.agent = Player.parse_player(agent)
        action, location = other.split(' (', 1)
        self.text = action
        loc_start = self.parse_and_set_location(location)
        self.location_name = location[:loc_start]

    def parse_attack(self, log: str) -> None:
        """Parses a game log entry from `ATTACK:` onwards (ATTACK: should not be included)"""
        agent, other = log.split(") ", 1) # Ensure that we didn't get a name with spaces
        self.agent = Player.parse_player(agent)
        if "/" in other:
            print(other) # TODO: fix this part
        self.action = other

    def parse_and_set_location(self, log: str) -> int:
        """Finds and parses a location entry. (location name (x, y, z)). Can parse a raw line."""
        # Find all possible location strings
        r = re.findall("\(\d{1,3},\d{1,3},\d{1,2}\)", log)
        # Check if there are any results
        if not len(r): return -1 
        # Get location of last match
        loc = log.index(r[-1]) 
        # Take the last result from the regex, remove the first and last character and turn into a list
        r = r[-1][1:-1].split(",")
        # Turn all elements to ints, convert to tuple
        self.location = tuple([int(x) for x in r]) # Bad practice since it's a side effect
        return loc

    def generic_say_parse(self, log: str) -> None:
        """Parses a generic SAY log entry from SAY: onwards (includes SAY, WHISPER, OOC) (should only include line from SAY: onwards, without the SAY)"""
        agent, other = log.split(") ", 1) # Ensure that we didn't get a name with spaces
        self.agent = Player.parse_player(agent)
        text, other = other.split('" ', 1)
        self.text = text
        other, location = other.split('(', 1)
        other = other.strip()
        if other:
            self.text += " | " + other
        
        self.is_dead = False
        if "(DEAD)" in text:
            text = text.replace("(DEAD) ", "", 1)
            self.is_dead = True
        loc_start = self.parse_and_set_location(location)
        self.location_name = location[:loc_start]

    def __str__(self):
        """String representation"""
        return self.raw_line
    def __repr__(self):
        """Object representation"""
        return self.raw_line

if __name__ == "__main__": print("This file is a module and is not meant to be run")
