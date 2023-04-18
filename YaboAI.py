import ac
import acsys
from third_party.sim_info import *

# Global constants
appName = "YaboAI"
simInfo = SimInfo()
promptSuffix = "In the style of Jeremy Clarkson working as an F1 commentator"

# Global variables
lastUpdateTime = 0
eventQueue = []
isCommentating = False
driverCount = 32

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
        self.speedMS = ac.getCarState(id, acsys.CS.SpeedMS)
        self.lapDistance = ac.getCarState(id, acsys.CS.NormalizedSplinePosition)
        self.distance = ac.getCarState(id, acsys.CS.LapCount) + ac.getCarState(id, acsys.CS.NormalizedSplinePosition)
        self.compound = ac.getCarTyreCompound(id)
        self.inPit = ac.isCarInPitline(id)
        self.currentSector = -1
        self.pitStops = 0

def acMain(ac_version):
    global appWindow, driverCount

    appWindow = ac.newApp(appName)
    ac.setTitle(appWindow, appName)
    ac.setSize(appWindow, 200, 200)

    ac.addRenderCallback(appWindow, appGL)

    ac.log("Hello, Assetto Corsa application world!")
    ac.console("Hello, Assetto Corsa console!")
    driverCount = ac.getCarsCount()

    return appName

def appGL(deltaT):
    pass

def acUpdate(deltaT):
    global lastUpdateTime, eventQueue, driverCount

    lastUpdateTime += deltaT

    if lastUpdateTime < 1:
        return

    lastUpdateTime = 0
    ac.log(simInfo.static.playerName)
    ac.log(simInfo.static.playerNick)

def generatePrompt(event):
    pass

def enhanceText(prompt):
    pass

def textToSpeech(text):
    pass
    


