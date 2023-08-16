import ac
import acsys
from third_party.sim_info import *
import random
import datetime
# from selenium import webdriver
# from selenium.webdriver.common.keys import Keys
import time

# Events
OVERTAKE = "overtake" # Handled
COLLISION = "collision"
FASTEST_LAP = "fastest_lap" # Handled
SHORT_INTERVAL = "short_interval" # Handled
DNF = "dnf"
LONG_STINT = "long_stint"
ENTERED_PIT = "entered_pit" # Handled
YELLOW_FLAG = "yellow_flag" 
LONG_PIT = "long_pit" # Handled
QUICK_PIT = "quick_pit" # Handled
MODE_CHANGE = "mode_change" # Handled
DRS_RANGE = "drs_range" # Handled

# Global constants
appName = "YaboAI"
simInfo = SimInfo()
focusTimeMin = 3
focusTimeMax = 15

# We don't want to be reporting events that happened too long ago
# so this will apply weights to events according to how likely 
# they are to be discarded from the queue if we are currently reporting
# and there are more events later in the queue
# eventPriority = {
#   YELLOW_FLAG: 9,
#   DNF: 8,
#   COLLISION: 7,
#   OVERTAKE: 6,
#   FASTEST_LAP: 5,
#   ENTERED_PIT: 4,
#   SHORT_INTERVAL: 3,
#   LONG_STINT: 2,
#   LONG_PIT: 1,
#   QUICK_PIT: 0
# }

# Global variables
lastUpdateTime = 0
isCommentating = False
driverCount = 32
sectorCount = 0
carInFocus = 0

eventQueue = []

stateCurrent = None
statePrevious = None

currentState = {
  "drivers": [],
  "fastestLap": (99999, {})
}
previousState = {
  "drivers": [],
  "fastestLap": (99999, {})
}

def getEvent(type, drivers, params, raceMode):
  return {
    "type": type,
    "time": datetime.datetime.now(),
    "drivers": drivers,
    "params": params,
    "raceMode": simInfo.graphics.session
  }

def getDriverInfo(id):
  return {
      "id": id,
      "name": ac.getDriverName(id),
      "nation": ac.getDriverNationCode(id),
      "carName": ac.getCarName(id),
      "connected": ac.isConnected(id),
      "lastLap": ac.getCarState(id, acsys.CS.LastLap),
      "lapCount": ac.getCarState(id, acsys.CS.LapCount),
      "speedKMH": ac.getCarState(id, acsys.CS.SpeedKMH),
      "lapDistance": ac.getCarState(id, acsys.CS.NormalizedSplinePosition),
      "distance": ac.getCarState(id, acsys.CS.LapCount) + ac.getCarState(id, acsys.CS.NormalizedSplinePosition),
      "compound": ac.getCarTyreCompound(id),
      "inPit": ac.isCarInPitline(id) or ac.isCarInPit(id),
      "bestLap": ac.getCarState(id, acsys.CS.BestLap),
      "pitStops": 0,
      "lastPitStart": datetime.datetime.now(),
      "lastPitEnd": datetime.datetime.now() 
    }

def acMain(ac_version):
  global appWindow, driverCount, currentState, previousState

  appWindow = ac.newApp(appName)
  ac.setTitle(appWindow, appName)
  ac.setSize(appWindow, 200, 200)

  ac.addRenderCallback(appWindow, appGL)

  drivers = []
  driverCount = ac.getCarsCount()
  for id in range(driverCount):
    drivers.append(getDriverInfo(id))

  previousState["drivers"] = drivers
  currentState["drivers"] = drivers

  return appName


def appGL(deltaT):
  pass


def eventPriority():
  pass


def reset():
  global lastUpdateTime, currentState, previousState
  lastUpdateTime = 0
  previousState = currentState


def acUpdate(deltaT):
  global lastUpdateTime, eventQueue, driverCount, carInFocus, isCommentating, previousState, currentState

  lastUpdateTime += deltaT
  if lastUpdateTime < 1:
    return


  ### Get current state ###
  # Race mode
  # ac.log(statePrevious)

  # Update drivers/Fastest lap
  for driver in currentState["drivers"]:
    driver = getDriverInfo(driver["id"])
    if driver["bestLap"] < previousState["fastestLap"][0]:
      currentState["fastestLap"] = (driver["bestLap"], driver)

  # Standings
  if simInfo.graphics.session == 2:
    currentState["drivers"].sort(key=lambda driver: driver["distance"], reverse=True)
  else:
    for driver in currentState["drivers"]:
      if driver["bestLap"] == 0:
        driver["bestLap"] = 9999999
    currentState["drivers"].sort(key=lambda driver: driver["bestLap"])

  # # Overtakes
  # for driver in range(stateCurrent.drivers.length):
  #   if stateCurrent.drivers[driver].carId != statePrevious.drivers[driver].cardId:
  #     params = { "position": driver, "overtaker": stateCurrent.drivers[driver].name, "overtaken": statePrevious.drivers[driver].name }
  #     eventQueue.append(Event(OVERTAKE, datetime.datetime.now(), [], params, stateCurrent.raceMode))
  #     break

  # # Intervals
  # if stateCurrent.raceMode == 2:
  #   for pos in range(1, len(stateCurrent.drivers)):
  #     interval = calculateTimeInterval(stateCurrent.drivers[pos - 1], stateCurrent.drivers[pos])
  #     params = { "driverAhead": stateCurrent.drivers[pos - 1], "driverBehind": stateCurrent.drivers[pos] }
  #     involvedDrivers = stateCurrent.drivers[pos-1:pos+1]
  #     params = { "interval": interval }
  #     if (interval < 2 and interval > 1):
  #       eventQueue.append(Event(SHORT_INTERVAL, datetime.datetime.now(), involvedDrivers, params, stateCurrent.raceMode))
  #     elif (interval <= 1):
  #       eventQueue.append(Event(DRS_RANGE, datetime.datetime.now(), involvedDrivers, params, stateCurrent.raceMode))


  # ### Compare the previous and current states ###
  # if statePrevious == None:
  #   reset()
  #   return
  
  # # Compare race mode
  # if stateCurrent.raceMode != statePrevious.raceMode:
  #   eventQueue.append(Event(MODE_CHANGE, datetime.datetime.now(), [], {}, stateCurrent.raceMode))

  # # Compare fastest lap
  # if stateCurrent.fastestLap != statePrevious.fastestLap:
  #   eventQueue.append(Event(FASTEST_LAP, datetime.datetime.now(), [stateCurrent.fastestLap[1]], { "lapTime": stateCurrent.fastestLap[0] }, stateCurrent.raceMode))

  # # Compare standing
  # if stateCurrent.standing != statePrevious.standing:
  #   max_len = max(len(statePrevious.standing), len(stateCurrent.standing))
  #   for i in range(max_len):
  #     if stateCurrent.standing[i] != statePrevious.standing[i]:
  #       pass

  # # Compare pit times
  # for driverCurrent in stateCurrent.drivers:
  #   driverPrevious = statePrevious[[i for i, d in enumerate(statePrevious.drivers) if d.carId == driverCurrent.carId][0]]
  #   # Driver has entered the pits
  #   if not driverPrevious.inPit and driverCurrent.inPit:
  #     driverCurrent.lastPitStart = datetime.datetime.now()
  #     eventQueue.append(Event(ENTERED_PIT, datetime.datetime.now(), [driverCurrent], {}, stateCurrent.raceMode))
  #   # Driver has exited the pits
  #   if driverPrevious.inPit and not driverCurrent.inPit:
  #     driverCurrent.lastPitEnd = datetime.datetime.now()
  #     pitLength = (driverCurrent.lastPitEnd - driverCurrent.lastPitStart).total_seconds()
  #     if pitLength > 60:
  #       eventQueue.append(Event(LONG_PIT, datetime.datetime.now(), [driverCurrent], { "pit_length": pitLength }, stateCurrent.raceMode))
  #     elif pitLength < 30:
  #       eventQueue.append(Event(QUICK_PIT, datetime.datetime.now(), [driverCurrent], { "pit_length": pitLength }, stateCurrent.raceMode))

  # if not eventQueue:
  #   reset()
  #   return

  # if isCommentating:
  #   # use probability to determine if the next event in queue should be discarded
  #   pass
  # else:
  #   isCommentating = True
  #   prompt = generatePrompt(eventQueue)
  #   script = enhanceText(prompt)
  #   audio = textToSpeech(script)
  #   if audio:
  #     isCommentating = False

  # reset()

# def calculateTimeInterval(driverAhead, driverBehind):
#   deltaD = abs(driverAhead.distance - driverBehind.distance)
#   return driverAhead.lastLap - (driverBehind.lastLap * (1 - deltaD))


# def generatePrompt(event):
#   prompt = ''
#   # for event in events.sort(reverse=True):
#   if event.type == MODE_CHANGE:
#     # ToDo: need to figure out how to know when the checkered flag is shown
#     if event.raceMode == 3:
#       prompt += f'The race has completed. The results are: '
#       for i, driver in enumerate(event.params["results"]):
#         prompt += f"{driver} in {i+1}. "
#   if event.type == YELLOW_FLAG:
#     pass
#   elif event.type == DNF:
#     pass
#   elif event.type == COLLISION:
#     prompt += f'{event.drivers[0]} and {event.drivers[1]} had a collision'
#     pass
#   elif event.type == OVERTAKE:
#     prompt += f'{event.params["overtaker"]} just overtook {event.params["overtaken"]} and is now in position {event.params["position"]}'
#   elif event.type == FASTEST_LAP:
#     prompt += f'{event.drivers[0].name} just got the fastest lap with a time of {event.params["time"]}. '
#   elif event.type == ENTERED_PIT:
#     prompt += f'{event.drivers[0].name} has entered the pit. '
#   elif event.type == SHORT_INTERVAL:
#     prompt += f'{event.drivers[0].name} is only {event.params["interval"]}'
#     pass
#   elif event.type == LONG_STINT:
#     prompt += f'{event.drivers[0].name} has completed {event.params["laps"]} laps on {event.param["tire"]} compound tires without pitting.'
#   elif event.type == LONG_PIT:
#     prompt += f'{event.drivers[0].name} had a long pitstop that took {event.params["duration"]} seconds.'
#   elif event.type == QUICK_PIT:
#     prompt += f'{event.drivers[0].name} had a very quick pitstop that took {event.params["duration"]} seconds.'
  
#   return prompt

# def enhanceText(prompt):
#   return prompt


# def textToSpeech(text):
#   time.sleep(10)
#   return True

# def requestChatGPT(prompt):
#   driver = webdriver.Chrome()
#   driver.get('https://chatgpt.openai.com/')

#   input_field = driver.find_element(By.ID, "prompt-textarea")
#   input_field.send_keys(prompt)
#   input_field.send_keys(Keys.RETURN)

#   driver.implicitly_wait(10)

#   response = driver.find_element(By.CLASS_NAME, "markdown").text
#   with open('prompts.txt', 'w') as f:
#       f.write(response)

#   driver.quit()

#   return response
