import ac
import acsys
from third_party.sim_info import *
import random

# Events
OVERTAKE = "overtake"
COLLISION = "collision"
FASTEST_LAP = "fastest_lap"
FASTEST_SECTOR = "fastest_sector"
SHORT_INTERVAL = "short_interval"
DNF = "dnf"

# Global constants
appName = "YaboAI"
simInfo = SimInfo()
focusTimeMin = 3
focusTimeMax = 10

# We don't want to be reporting events that happened too long ago
# so this will apply weights to events according to how likely 
# they are to be discarded from the queue if we are currently reporting
# and there are more events later in the queue
eventPriority = { OVERTAKE: 0.2, COLLISION: 0.2, FASTEST_LAP: 0.4, FASTEST_SECTOR: 0.6, SHORT_INTERVAL: 0.5, DNF: 0.1 }

# Global variables
lastUpdateTime = 0
isCommentating = False
driverCount = 32
carInFocus = 0
raceMode = -1

eventQueue = []
driverList = []

stateCurrent: any = None
statePrevious: any = None


class RaceState:
    def __init__(self, standing):
        self.standing = standing
        

class Driver:
    def __init__(self, id):
        self.carId = id
        self.connected = ac.isConnected(id)
        self.name = ac.getDriverName(id)
        self.nation = ac.getDriverNationCode(id)
        self.carName = ac.getCarName(id)
        self.bestLap = ac.getCarState(id, acsys.CS.BestLap)
        self.lastLap = ac.getCarState(id, acsys.CS.LastLap)
        self.lapCount = ac.getCarState(id, acsys.CS.LapCount)
        self.speedKMH = ac.getCarState(id, acsys.CS.SpeedKMH)
        self.lapDistance = ac.getCarState(id, acsys.CS.NormalizedSplinePosition)
        self.distance = ac.getCarState(id, acsys.CS.LapCount) + ac.getCarState(id, acsys.CS.NormalizedSplinePosition)
        self.compound = ac.getCarTyreCompound(id)
        self.inPit = ac.isCarInPitline(id)
        self.currentSector = -1
        self.pitStops = 0
        self.runningPosition = 0


class Event:
    def __init__(self, type, time, drivers, parameters):
        self.type = type
        self.time = time
        self.drivers = drivers
        self.parameters = parameters


def acMain(ac_version):
    global appWindow, driverCount

    appWindow = ac.newApp(appName)
    ac.setTitle(appWindow, appName)
    ac.setSize(appWindow, 200, 200)

    ac.addRenderCallback(appWindow, appGL)

    driverCount = ac.getCarsCount()
    for id in range(driverCount):
        driverList.append(Driver(id))

    return appName


def appGL(deltaT):
    pass


def eventPriority():
    pass

def resetState():
    global lastUpdateTime, stateCurrent, statePrevious
    lastUpdateTime = 0
    statePrevious = stateCurrent

def acUpdate(deltaT):
    global lastUpdateTime, eventQueue, driverCount, carInFocus, raceMode, statePrevious, stateCurrent

    lastUpdateTime += deltaT
    if lastUpdateTime < 1:
        return

    if raceMode == 2:
        driverList.sort(key=lambda driver: driver.distance, reverse=True)
    else:
        for driver in driverList:
            if driver.bestLap == 0:
                driver.bestLap = 9999999
        driverList.sort(key=lambda driver: driver.bestLap)
    
    standing = [d for d in driverList if d.connected]

    stateCurrent = RaceState(standing)

    if statePrevious == None:
        resetState()
        return

    if stateCurrent.standing != statePrevious.standing:
        max_len = max(len(statePrevious.standing), len(stateCurrent.standing))
        for i in range(max_len):
            if stateCurrent.standing[i] != statePrevious.standing[i]:
                pass

    if not eventQueue:
        resetState()
        return

    if isCommentating:
        # use probability to determine if the next event in queue should be discarded
        pass
    else:
        event = eventQueue.pop(0)
        prompt = generatePrompt(event)

    resetState()



def generatePrompt(event):
    prompt = f"" 
    pass


def enhanceText(prompt):
    pass


def textToSpeech(text):
    pass
    


