import datetime
import sys
from ctypes import c_int32
from enum import Enum
from typing import Any, List

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
    DNF = "dnf"  # TODO
    # Driver A and Driver B collide
    COLLISION = "collision"  # TODO
    # Driver has set their best lap
    BEST_LAP = "best_lap"
    # Driver sets the fastest lap
    FASTEST_LAP = "fastest_lap"
    # Driver enters the pit
    ENTERED_PIT = "entered_pit"
    # Driver has been in the pit for over 60 seconds
    LONG_PIT = "long_pit"
    # Driver was in the pits for less than 30 seconds
    QUICK_PIT = "quick_pit"
    # Driver A is 1 to 3 second behind Driver B
    SHORT_INTERVAL = "short_interval"
    # Driver A is less than 1 second behind Driver B
    DRS_RANGE = "drs_range"
    # Driver A passes Driver B
    OVERTAKE = "overtake"
    # Driver has been on the same set of tires for over 15 laps
    LONG_STINT = "long_stint"


class Event:
    """
    Event

    Contains all relevant information for a particular event
    """

    def __init__(self, event_type: EventType, driver_id: int, params: dict[str, Any]):
        self.type = event_type
        self.driver_id = driver_id
        self.time = datetime.datetime.now()
        self.params = params

        self.race_mode: c_int32 = SimInfo().graphics.session

    def __str__(self):
        return "{} - {} - {} - {}".format(
            self.type, self.time, self.params, self.race_mode
        )


class Driver:
    """
    Driver

    Contains all race relevant information for a particular driver
    """

    # TODO: Need to keep track of events that have already been reported
    # probably using a dictionary with the event type as the key and the last lap it was reported on
    # as the value. This way we can make sure the reporting on similar events is spaced out

    def __init__(self, id: int):
        self.id = id
        self.name = str(ac.getDriverName(id))
        self.nation = str(ac.getDriverNationCode(id))
        self.car_name = str(ac.getCarName(id))
        self.pit_stops = 0
        self.tire_age = 0
        self.last_compound_change_lap = 0

        self.update()

    def __str__(self) -> str:
        return "{} - {}".format(self.id, self.name)

    def update(self) -> List[Event]:
        events: List[Event] = []

        self.last_lap = ac.getCarState(self.id, acsys.CS.LastLap)
        self.best_lap = ac.getCarState(self.id, acsys.CS.BestLap)
        self.lap_count = ac.getCarState(self.id, acsys.CS.LapCount)
        self.speed_kmh = ac.getCarState(self.id, acsys.CS.SpeedKMH)
        self.lap_distance = ac.getCarState(self.id, acsys.CS.NormalizedSplinePosition)
        self.distance = self.lap_count + self.lap_distance

        # Check if the driver has left the game (DNF)
        connected = ac.isConnected(self.id)
        if self.connected and not connected:
            ac.console("EVENT: {} - {}".format(EventType.DNF, self.name))
            events.append(
                Event(
                    EventType.DNF,
                    self.id,
                    {
                        "driver": self.name,
                        "reason": "Disconnected",
                    },
                )
            )
        self.connected = connected

        # Track the duration of the driver's pitstop
        in_pit = bool(ac.isCarInPitline(self.id) or ac.isCarInPit(self.id))
        if not self.in_pit and in_pit:
            self.latest_pit_start = datetime.datetime.now()
            self.pit_stops += 1
            ac.console("EVENT: {} - {}".format(EventType.ENTERED_PIT, self.name))
            events.append(
                Event(
                    EventType.ENTERED_PIT,
                    self.id,
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
                ac.console("EVENT: {} - {}".format(EventType.LONG_PIT, self.name))
                events.append(
                    Event(
                        EventType.LONG_PIT,
                        self.id,
                        {
                            "driver": self.name,
                            "compound": self.compound,
                            "duration": int(duration.total_seconds()),
                        },
                    )
                )
            elif duration.total_seconds() < 30:
                ac.console("EVENT: {} - {}".format(EventType.QUICK_PIT, self.name))
                events.append(
                    Event(
                        EventType.QUICK_PIT,
                        self.id,
                        {
                            "driver": self.name,
                            "compound": self.compound,
                            "duration": int(duration.total_seconds()),
                        },
                    )
                )
        self.in_pit = in_pit

        # Check if the driver has set their best lap
        if self.last_lap == self.best_lap:
            ac.console("EVENT: {} - {}".format(EventType.BEST_LAP, self.name))
            events.append(
                Event(
                    EventType.BEST_LAP,
                    self.id,
                    {"driver": self.name, "lap_time": self.best_lap},
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
                ac.console("EVENT: {} - {}".format(EventType.LONG_STINT, self.name))
                events.append(
                    Event(
                        EventType.LONG_STINT,
                        self.id,
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
    RaceState

    Used to keep track and the current and previous race states
    """

    def __init__(self):
        self.drivers: List[Driver] = []  # Ordered by position
        self.fastest_lap: float = sys.float_info.max
        self.safety_car: bool = False

    def add_driver(self, driver: Driver):
        self.drivers.append(driver)
        self.drivers.sort(key=lambda driver: driver.distance)

    def update(self) -> List[Event]:
        events: List[Event] = []

        avg_speed = 0
        for driver in self.drivers:
            events.extend(driver.update())
            avg_speed += driver.speed_kmh
        avg_speed /= len(self.drivers)

        sorted_drivers = sorted(
            self.drivers, key=lambda driver: driver.distance, reverse=True
        )

        # Check for overtakes and short intervals
        for i in range(len(sorted_drivers) - 2):
            if (
                sorted_drivers[i].id != self.drivers[i].id
                and sorted_drivers[i + 1].id == self.drivers[i].id
            ):
                ac.console(
                    "EVENT: {} - {}".format(EventType.OVERTAKE, sorted_drivers[i].name)
                )
                events.append(
                    Event(
                        EventType.OVERTAKE,
                        sorted_drivers[i].id,
                        {
                            "driver_a": sorted_drivers[i].name,
                            "driver_b": sorted_drivers[i + 1].name,
                            "position": i + 1,
                        },
                    )
                )

            interval = self._calculateTimeInterval(
                sorted_drivers[i], sorted_drivers[i + 1]
            )
            # TODO: definitely need to prevent repeat event reporting here
            if interval < 1:
                ac.console(
                    "EVENT: {} - {}".format(
                        EventType.DRS_RANGE, sorted_drivers[i + 1].name
                    )
                )
                events.append(
                    Event(
                        EventType.DRS_RANGE,
                        sorted_drivers[i + 1].id,
                        {
                            "driver_a": sorted_drivers[i].name,
                            "driver_b": sorted_drivers[i + 1].name,
                            "interval": interval,
                        },
                    )
                )
            elif interval < 3:
                ac.console(
                    "EVENT: {} - {}".format(
                        EventType.SHORT_INTERVAL, sorted_drivers[i + 1].name
                    )
                )
                events.append(
                    Event(
                        EventType.SHORT_INTERVAL,
                        sorted_drivers[i + 1].id,
                        {
                            "driver_a": sorted_drivers[i].name,
                            "driver_b": sorted_drivers[i + 1].name,
                            "interval": int(interval),
                        },
                    )
                )
        self.drivers = sorted_drivers

        current_lap = self.drivers[0].lap_count

        # Check for safety car
        if not self.safety_car and current_lap > 1 and avg_speed < 30:
            self.safety_car = True
            ac.console("EVENT: {}".format(EventType.START_SAFETY_CAR))
            events.append(
                Event(
                    EventType.START_SAFETY_CAR,
                    self.drivers[0].id,
                    {"lap_count": current_lap},
                )
            )
        elif self.safety_car and avg_speed > 160:
            self.safety_car = False
            ac.console("EVENT: {}".format(EventType.END_SAFETY_CAR))
            events.append(
                (
                    Event(
                        EventType.END_SAFETY_CAR,
                        self.drivers[0].id,
                        {"lap_count": current_lap},
                    )
                )
            )

        # Check for fastest lap
        for driver in self.drivers:
            if driver.best_lap < self.fastest_lap:
                self.fastest_lap = driver.best_lap
                if current_lap > 5:
                    # Don't report fastest lap on the first few laps
                    ac.console(
                        "EVENT: {} - {}".format(EventType.FASTEST_LAP, driver.name)
                    )
                    events.append(
                        Event(
                            EventType.FASTEST_LAP,
                            driver.id,
                            {
                                "driver": driver.name,
                                "lap_time": driver.best_lap,
                            },
                        )
                    )

        return events

    def _calculateTimeInterval(
        self, driverAhead: Driver, driverBehind: Driver
    ) -> float:
        deltaD = abs(driverAhead.distance - driverBehind.distance)
        return driverAhead.last_lap - (driverBehind.last_lap * (1 - deltaD))
