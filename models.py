import datetime
import sys
from ctypes import c_int32
from enum import Enum
from typing import Any

import ac  # type: ignore
import acsys  # type: ignore

from third_party.sim_info import SimInfo


class EventType(Enum):
    """
    Event Types

    We don't want to be reporting events that happened too long ago
    so this will apply weights to events according to how likely
    they are to be discarded from the queue if we are currently reporting
    and there are more events later in the queue
    """

    # Race has stopped due to an incident. Racer's line up to restart
    START_SAFETY_CAR = "safety_car"
    # Race has restarted after a safety car
    END_SAFETY_CAR = "end_safety_car"
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
    # Driver has been in the pit for over 60 seconds
    LONG_PIT = "long_pit"
    # Driver was in the pits for less than 30 seconds
    QUICK_PIT = "quick_pit"
    # Driver has set their best lap
    BEST_LAP = "best_lap"
    # Driver A is less than 1 second behind Driver B
    DRS_RANGE = "drs_range"


class Event:
    """
    Event

    Contains all relevant information for a particular event
    """

    def __init__(self, event_type: EventType, params: dict[str, Any]):
        self.event_type = event_type
        self.time = datetime.datetime.now()
        self.params = params

        self.race_mode: c_int32 = SimInfo().graphics.session

    def __str__(self):
        return f"{self.type} - {self.time} - {self.params} - {self.race_mode}"


class Driver:
    """
    Driver

    Contains all race relevant information for a particular driver
    """

    def __init__(self, id: int):
        self.id = id
        self.name = ac.getDriverName(id)
        self.nation = ac.getDriverNationCode(id)
        self.car_name = ac.getCarName(id)
        self.pit_stops = 0
        self.tire_age = 0
        self.last_compound_change_lap = 0

        self.update()

    def __str__(self) -> str:
        return f"{self.id} - {self.name}"

    def update(self) -> list[Event]:
        events: list[Event] = []

        self.last_lap = ac.getCarState(self.id, acsys.CS.LastLap)
        self.best_lap = ac.getCarState(self.id, acsys.CS.BestLap)
        self.lap_count = ac.getCarState(self.id, acsys.CS.LapCount)
        self.speed_kmh = ac.getCarState(self.id, acsys.CS.SpeedKMH)
        self.lap_distance = ac.getCarState(self.id, acsys.CS.NormalizedSplinePosition)
        self.distance = self.lap_count + self.lap_distance

        # Check if the driver has left the game (DNF)
        connected = ac.isConnected(self.id)
        if self.connected and not connected:
            events.append(
                Event(
                    EventType.DNF,
                    {
                        "driver": self.name,
                        "reason": "Disconnected",
                    },
                )
            )
        self.connected = connected

        # Track the duration of the driver's pitstop
        in_pit = ac.isCarInPitline(self.id) or ac.isCarInPit(self.id)
        if not self.in_pit and in_pit:
            self.latest_pit_start = datetime.datetime.now()
            self.pit_stops += 1
            events.append(
                Event(
                    EventType.ENTERED_PIT,
                    {
                        "driver": self.name,
                        "lap_count": self.lap_count,
                        "last_lap": self.last_lap,
                        "compound": self.compound,
                    },
                )
            )
        elif self.in_pit and not in_pit:
            duration = datetime.datetime.now() - self.latest_pit_start
            if duration.total_seconds() > 60:
                events.append(
                    Event(
                        EventType.LONG_PIT,
                        {
                            "driver": self.name,
                            "lap_count": self.lap_count,
                            "last_lap": self.last_lap,
                            "compound": self.compound,
                            "duration": duration,
                        },
                    )
                )
            elif duration.total_seconds() < 30:
                events.append(
                    Event(
                        EventType.QUICK_PIT,
                        {
                            "driver": self.name,
                            "lap_count": self.lap_count,
                            "last_lap": self.last_lap,
                            "compound": self.compound,
                            "duration": duration,
                        },
                    )
                )
        self.in_pit = in_pit

        # Check if the driver has set their best lap
        if self.last_lap == self.best_lap:
            events.append(
                Event(
                    EventType.BEST_LAP, {"driver": self.name, "lap_time": self.best_lap}
                )
            )

        # Check tire age
        compound = ac.getCarTyreCompound(self.id)
        if compound != self.compound:
            self.tire_age = 0
            self.last_compound_change_lap = 0
        else:
            self.tire_age = self.lap_count - self.last_compound_change_lap
            if self.tire_age > 15:
                events.append(
                    Event(
                        EventType.LONG_STINT,
                        {
                            "driver": self.name,
                            "lap_count": self.lap_count,
                            "tire_age": self.tire_age,
                            "last_lap": self.last_lap,
                            "compound": self.compound,
                        },
                    )
                )
        self.compound = compound

        return events


class RaceState:
    """
    State

    Used to keep track and the current and previous race states
    """

    def __init__(self):
        self.drivers: list[Driver] = []  # Ordered by position
        self.fastest_lap: tuple[float, str] = (sys.maxsize, "")
        self.safety_car: bool = False

    def add_driver(self, driver: Driver):
        self.drivers.append(driver)
        self.drivers.sort(key=lambda driver: driver.distance)

    def update(self) -> list[Event]:
        events: list[Event] = []

        avg_speed = 0
        for driver in self.drivers:
            driver.update()
            avg_speed += driver.speed_kmh
        avg_speed /= len(self.drivers)

        current_lap = self.drivers[0].lap_count

        # Check for safety car
        if not self.safety_car and current_lap > 1 and avg_speed < 30:
            self.safety_car = True
            events.append(Event(EventType.SAFETY_CAR, {"lap_count": current_lap}))
        elif self.safety_car and avg_speed > 100:
            self.safety_car = False
            events.append((Event(EventType.END_SAFETY_CAR, {"lap_count": current_lap})))
