import ac
import acsys
from third_party.sim_info import *
import random
import datetime

# Events
OVERTAKE = "overtake"
COLLISION = "collision"
FASTEST_LAP = "fastest_lap"
SHORT_INTERVAL = "short_interval"
DNF = "dnf"
LONG_STINT = "long_stint"
ENTERED_PIT = "entered_pit"
YELLOW_FLAG = "yellow_flag"
RACE_COMPLETE = "race_complete"
LONG_PIT = "long_pit"
QUICK_PIT = "quick_pit"

# Global constants
appName = "YaboAI"
simInfo = SimInfo()
focusTimeMin = 3
focusTimeMax = 15

# We don't want to be reporting events that happened too long ago
# so this will apply weights to events according to how likely 
# they are to be discarded from the queue if we are currently reporting
# and there are more events later in the queue
eventPriority = {
  RACE_COMPLETE: 10,
  YELLOW_FLAG: 9,
  DNF: 8,
  COLLISION: 7,
  OVERTAKE: 6,
  FASTEST_LAP: 5,
  ENTERED_PIT: 4,
  SHORT_INTERVAL: 3,
  LONG_STINT: 2,
  LONG_PIT: 1,
  QUICK_PIT: 0
}

# Global variables
lastUpdateTime = 0
isCommentating = False
driverCount = 32
sectorCount = 0
carInFocus = 0

eventQueue = []

stateCurrent: any = None
statePrevious: any = None

class RaceState:
  def __init__(self, drivers, fastestLap, intervals, raceMode):
    self.drivers = drivers
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
    self.bestLaps = [0, 0, 0]
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

  def update(self, raceMode):
    self.connected = ac.isConnected(id)
    self.bestLaps[raceMode] = ac.getCarState(id, acsys.CS.BestLap)
    self.lastLap = ac.getCarState(id, acsys.CS.LastLap)
    self.lapCount = ac.getCarState(id, acsys.CS.LapCount)
    self.speedKMH = ac.getCarState(id, acsys.CS.SpeedKMH)
    self.lapDistance = ac.getCarState(id, acsys.CS.NormalizedSplinePosition)
    self.distance = ac.getCarState(id, acsys.CS.LapCount) + ac.getCarState(id, acsys.CS.NormalizedSplinePosition) if self.connected else -1
    self.compound = ac.getCarTyreCompound(id)
    self.inPit = (ac.isCarInPitline(id) or ac.isCarInPit(id)) if not self.inPit else True

class Event:
  def __init__(self, type, timestamp, drivers, params, mode):
    self.type = type
    self.time = timestamp
    self.drivers = drivers
    self.params = params
    self.mode = mode


def acMain(ac_version):
  global appWindow, driverCount, stateCurrent, statePrevious

  appWindow = ac.newApp(appName)
  ac.setTitle(appWindow, appName)
  ac.setSize(appWindow, 200, 200)

  ac.addRenderCallback(appWindow, appGL)

  drivers = []
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
  global lastUpdateTime, eventQueue, driverCount, carInFocus, statePrevious, stateCurrent

  lastUpdateTime += deltaT
  if lastUpdateTime < 1:
    return


  ### Get current state ###
  # Race mode
  stateCurrent.raceMode = simInfo.graphics.session

  # Update drivers/Fastest lap
  fastestLap = statePrevious.fastestLap
  for driver in stateCurrent.drivers:
    driver.update(stateCurrent.raceMode)
    if driver.bestLap < fastestLap[0]:
      fastestLap = (driver.bestLap, driver)

  # Standings
  if stateCurrent.raceMode == 2:
    stateCurrent.drivers.sort(key=lambda driver: driver.distance, reverse=True)
  else:
    for driver in stateCurrent.drivers:
      if driver.bestLap == 0:
        driver.bestLap = 9999999
    stateCurrent.drivers.sort(key=lambda driver: driver.bestLap[stateCurrent.raceMode])

  # Intervals
  if stateCurrent.raceMode == 2:
    stateCurrent.intervals[0] = (stateCurrent.drivers[0], 0)
    for pos in range(1, len(stateCurrent.drivers)):
      interval = calculateTimeInterval(stateCurrent.drivers[pos - 1], stateCurrent.drivers[pos])
      stateCurrent.intervals[pos] = (stateCurrent.drivers[pos], interval)


  ### Compare the previous and current states ###
  if statePrevious == None:
    reset()
    return
  
  # Compare race mode
  if stateCurrent.raceMode != statePrevious.raceMode:


  # Compare fastest lap

  # 

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
      if pitLength > 60:
        eventQueue.append(Event(LONG_PIT, datetime.datetime.now(), driverCurrent, { "pit_length": pitLength }))
      elif pitLength < 30:
        eventQueue.append(Event(QUICK_PIT, datetime.datetime.now(), driverCurrent, { "pit_length": pitLength }))

  if not eventQueue:
    reset()
    return

  if isCommentating:
    # use probability to determine if the next event in queue should be discarded
    pass
  else:
    isCommentating = True
    prompt = generatePrompt(eventQueue)
    script = enhanceText(prompt)
    audio = textToSpeech(script)
    # Write audio to disk

  reset()

def calculateTimeInterval(driverAhead, driverBehind):
  distanceDelta = abs(driverAhead.distance - driverBehind.distance)
  return driverAhead.lastLap - (driverBehind.lastLap * (1 - distanceDelta))


def generatePrompt(events):
  prompt = ''
  for event in events.sort(reverse=True):
    if event.type == RACE_COMPLETE:
      prompt += f'The race has completed. The results are: '
      for i, driver in enumerate(event.params["results"]):
        prompt += f"{driver} in {i+1}. "
    if event.type == YELLOW_FLAG:
      pass
    elif event.type == DNF:
      pass
    elif event.type == COLLISION:
      pass
    elif event.type == OVERTAKE:
      pass
    elif event.type == FASTEST_LAP:
      prompt += f'{event.drivers[0]} just got the fastest lap with a time of {event.params["time"]}. '
    elif event.type == ENTERED_PIT:
      prompt += f'{event.drivers[0]} has entered the pit. '
    elif event.type == SHORT_INTERVAL:
      pass
    elif event.type == LONG_STINT:
      prompt += f'{event.drivers[0]} has completed {event.params["laps"]} laps on {event.param["tire"]} compound tires without pitting. '
    elif event.type == LONG_PIT:
      prompt += f'{event.drivers[0]} had a long pitstop that took {event.params["duration"]} seconds. '
    elif event.type == QUICK_PIT:
      prompt += f'{event.drivers[0]} had a very quick pitstop that took {event.params["duration"]} seconds. '

def enhanceText(prompt):
  pass


def textToSpeech(text):
  pass
