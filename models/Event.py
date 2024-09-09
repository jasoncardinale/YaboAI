from ctypes import c_int32
import datetime
from enum import Enum
from typing import Any

from third_party.sim_info import SimInfo


class Event:
    """
    Event
    """

    def __init__(self, event_type: "EventType", drivers, params: dict[str, Any]):
        self.event_type = event_type
        self.time = datetime.datetime.now()
        self.drivers = drivers
        self.params: dict[str, Any] = params

        self.raceMode: c_int32 = SimInfo().graphics.session

    def __str__(self):
        return f"{self.type} - {self.time} - {self.drivers} - {self.params} - {self.raceMode}"


class EventType(Enum):
    """
    Event Types

    We don't want to be reporting events that happened too long ago
    so this will apply weights to events according to how likely
    they are to be discarded from the queue if we are currently reporting
    and there are more events later in the queue
    """

    # Race has stopped due to an incident. Racer's line up to restart
    YELLOW_FLAG = "yellow_flag"
    # Driver A's engine died/(Did not finish)
    DNF = "dnf"
    # Driver A and Driver B collide
    COLLISION = "collision"
    # Driver A passes Driver B
    OVERTAKE = "overtake"
    # Driver sets the fastest lap
    FASTEST_LAP = "fastest_lap"
    # Driver enters the pit
    ENTERED_PIT = "entered_pit"
    # Driver A is 1 to 3 second behind Driver B
    SHORT_INTERVAL = "short_interval"
    # Driver has been on the same set of tires for over 15 laps
    LONG_STINT = "long_stint"
    # Driver has been in the pit for over 30 seconds
    LONG_PIT = "long_pit"
    # Driver was in the pits for less than 15 seconds
    QUICK_PIT = "quick_pit"
    # Driver A is less than 1 second behind Driver B
    DRS_RANGE = "drs_range"
