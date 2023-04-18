import ac
import acsys
from third_party.sim_info import *

appName = "YaboAI"
simInfo = SimInfo()

# GLobal variables
lastUpdateTime = 0
eventQueue = []
isCommentating = False

def acMain(ac_version):
    global appWindow

    appWindow = ac.newApp(appName)
    ac.setTitle(appWindow, appName)
    ac.setSize(appWindow, 200, 200)

    ac.addRenderCallback(appWindow, appGL)

    ac.log("Hello, Assetto Corsa application world!")
    ac.console("Hello, Assetto Corsa console!")

    return appName


def appGL(deltaT):
    pass


def acUpdate(deltaT):
    global lastUpdateTime
    global eventQueue

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
    


