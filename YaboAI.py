import ac
import acsys
from third_party.sim_info import *
import random
import datetime

# Events
OVERTAKE = "overtake"
COLLISION = "collision"
FASTEST_LAP = "fastest_lap"
FASTEST_SECTOR = "fastest_sector"
SHORT_INTERVAL = "short_interval"
DNF = "dnf"
LONG_STINT = "long_stint"
ABNORMAL_PIT = "abnormal_pit"
ENTERED_PIT = "entered_pit"

# Global constants
appName = "YaboAI"
simInfo = SimInfo()
focusTimeMin = 3
focusTimeMax = 10

# We don't want to be reporting events that happened too long ago
# so this will apply weights to events according to how likely 
# they are to be discarded from the queue if we are currently reporting
# and there are more events later in the queue
eventPriority = { OVERTAKE: 0.2, COLLISION: 0.2, FASTEST_LAP: 0.4, FASTEST_SECTOR: 0.6, SHORT_INTERVAL: 0.5, DNF: 0, LONG_STINT: 0.5 }

# Global variables
lastUpdateTime = 0
isCommentating = False
driverCount = 32
sectorCount = 0
carInFocus = 0

eventQueue = []
drivers = []

stateCurrent: any = None
statePrevious: any = None

class RaceState:
    def __init__(self, drivers, standing, fastestLap, intervals, raceMode):
        self.drivers = drivers
        self.standing = standing
        self.fastestLap = fastestLap
        self.intervals = intervals
        self.raceMode = raceMode

class Driver:
    def __init__(self, id):
        # Constant
        self.carId = id
        self.name = ac.getDriverName(id)
        self.nation = ac.getDriverNationCode(id)
        self.carName = ac.getCarName(id)

        # Continuously updated
        self.connected = ac.isConnected(id)
        self.bestLaps = ac.getCarState(id, acsys.CS.BestLap)
        self.lastLap = ac.getCarState(id, acsys.CS.LastLap)
        self.lapCount = ac.getCarState(id, acsys.CS.LapCount)
        self.speedKMH = ac.getCarState(id, acsys.CS.SpeedKMH)
        self.lapDistance = ac.getCarState(id, acsys.CS.NormalizedSplinePosition)
        self.distance = ac.getCarState(id, acsys.CS.LapCount) + ac.getCarState(id, acsys.CS.NormalizedSplinePosition)
        self.compound = ac.getCarTyreCompound(id)
        self.inPit = ac.isCarInPitline(id) or ac.isCarInPit(id)

        # Periodically updated
        self.pitStops = 0
        self.lastPitStart = datetime.datetime.now()
        self.lastPitEnd = datetime.datetime.now()

    def update(self):
        self.connected = ac.isConnected(id)
        self.bestLaps = ac.getCarState(id, acsys.CS.BestLap)
        self.lastLap = ac.getCarState(id, acsys.CS.LastLap)
        self.lapCount = ac.getCarState(id, acsys.CS.LapCount)
        self.speedKMH = ac.getCarState(id, acsys.CS.SpeedKMH)
        self.lapDistance = ac.getCarState(id, acsys.CS.NormalizedSplinePosition)
        self.distance = ac.getCarState(id, acsys.CS.LapCount) + ac.getCarState(id, acsys.CS.NormalizedSplinePosition)
        self.compound = ac.getCarTyreCompound(id)
        self.inPit = (ac.isCarInPitline(id) or ac.isCarInPit(id)) if not self.inPit else True

class Event:
    def __init__(self, type, time, drivers, parameters):
        self.type = type
        self.time = time
        self.drivers = drivers
        self.parameters = parameters


def acMain(ac_version):
    global appWindow, driverCount, stateCurrent, statePrevious

    appWindow = ac.newApp(appName)
    ac.setTitle(appWindow, appName)
    ac.setSize(appWindow, 200, 200)

    ac.addRenderCallback(appWindow, appGL)

    driverCount = ac.getCarsCount()
    for id in range(driverCount):
        drivers.append(Driver(id))

    standing = [d.carId for d in drivers if d.connected]
    intervals = [0 for d in standing]
    stateCurrent, statePrevious = RaceState(drivers, standing, 9999999, [intervals], -1)
    return appName


def appGL(deltaT):
    pass


def eventPriority():
    pass

def reset():
    global lastUpdateTime, stateCurrent, statePrevious
    lastUpdateTime = 0
    statePrevious = stateCurrent

def acUpdate(deltaT):
    global lastUpdateTime, eventQueue, driverCount, carInFocus, statePrevious, stateCurrent, drivers

    lastUpdateTime += deltaT
    if lastUpdateTime < 1:
        return

    # Get current state
    # Race mode
    stateCurrent.raceMode = simInfo.graphics.session

    # Update drivers
    for driver in stateCurrent.drivers:
        driver.update()

    # Determine current standings
    if stateCurrent.raceMode == 2:
        drivers.sort(key=lambda driver: driver.distance, reverse=True)
    else:
        for driver in drivers:
            if driver.bestLap == 0:
                driver.bestLap = 9999999
        drivers.sort(key=lambda driver: driver.bestLap)
    standing = [d.carId for d in drivers if d.connected]

    # Determine the fastest lap
    fastestLap = statePrevious.bestLap
    for driver in stateCurrent.drivers:
        if driver.bestLap < fastestLap[0]:
            fastestLap = (driver.bestLap, driver)



    stateCurrent = RaceState(standing, fastestLap)

    # Compare the previous and current race states
    if statePrevious == None:
        reset()
        return

    # Compare standing
    if stateCurrent.standing != statePrevious.standing:
        max_len = max(len(statePrevious.standing), len(stateCurrent.standing))
        for i in range(max_len):
            if stateCurrent.standing[i] != statePrevious.standing[i]:
                pass

    # Compare pit times
    for driverCurrent in stateCurrent.drivers:
        driverPrevious = statePrevious[[i for i, d in enumerate(statePrevious.drivers) if d.carId == driverCurrent.carId][0]]
        # Driver has entered the pits
        if not driverPrevious.inPit and driverCurrent.inPit:
            driverCurrent.lastPitStart = datetime.datetime.now()
            eventQueue.append(Event(ENTERED_PIT, datetime.datetime.now(), driverCurrent))
        # Driver has exited the pits
        if driverPrevious.inPit and not driverCurrent.inPit:
            driverCurrent.lastPitEnd = datetime.datetime.now()
            pitLength = (driverCurrent.lastPitEnd - driverCurrent.lastPitStart).total_seconds()
            if pitLength > 60 or pitLength < 30:
                eventQueue.append(Event(ABNORMAL_PIT, datetime.datetime.now(), driverCurrent, { "pit_length": pitLength }))


    if not eventQueue:
        reset()
        return

    if isCommentating:
        # use probability to determine if the next event in queue should be discarded
        pass
    else:
        isCommentating = True
        event = eventQueue.pop(0)
        prompt = generatePrompt(event)

    reset()



def generatePrompt(event):
    prompt = f"" 
    pass


def enhanceText(prompt):
    pass


def textToSpeech(text):
    pass
    


