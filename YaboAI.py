import copy
import datetime

import ac  # type: ignore
import acsys  # type: ignore

from third_party.sim_info import SimInfo, sys

# Events
OVERTAKE = "overtake"  # Handled
COLLISION = "collision"
FASTEST_LAP = "fastest_lap"  # Handled
SHORT_INTERVAL = "short_interval"  # Handled
DNF = "dnf"
LONG_STINT = "long_stint"
ENTERED_PIT = "entered_pit"  # Handled
YELLOW_FLAG = "yellow_flag"
LONG_PIT = "long_pit"  # Handled
QUICK_PIT = "quick_pit"  # Handled
DRS_RANGE = "drs_range"  # Handled

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

currentState = {"drivers": [], "fastestLap": (sys.maxsize, "")}
previousState = {"drivers": [], "fastestLap": (sys.maxsize, "")}


def getEvent(type, drivers, params):
    return {
        "type": type,
        "time": datetime.datetime.now(),
        "drivers": drivers,
        "params": params,
        "raceMode": simInfo.graphics.session,
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
        "distance": ac.getCarState(id, acsys.CS.LapCount)
        + ac.getCarState(id, acsys.CS.NormalizedSplinePosition),
        "compound": ac.getCarTyreCompound(id),
        "inPit": ac.isCarInPitline(id) or ac.isCarInPit(id),
        "bestLap": ac.getCarState(id, acsys.CS.BestLap),
        "pitStops": 0,
        "lastPitStart": datetime.datetime.now(),
        "lastPitEnd": datetime.datetime.now(),
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


def step():
    global lastUpdateTime, currentState, previousState
    lastUpdateTime = 0
    previousState = copy.deepcopy(currentState)


def acUpdate(deltaT):
    global \
        lastUpdateTime, \
        eventQueue, \
        driverCount, \
        carInFocus, \
        isCommentating, \
        previousState, \
        currentState

    lastUpdateTime += deltaT
    if lastUpdateTime < 1:
        return

    ### Get current state ###
    for pos in range(len(currentState["drivers"])):
        updatedDriver = getDriverInfo(currentState["drivers"][pos]["id"])
        currentState["drivers"][pos] = updatedDriver
        # ac.console("time: {}".format(updatedDriver["bestLap"]))
        if (
            updatedDriver["bestLap"] > 0
            and updatedDriver["bestLap"] < currentState["fastestLap"][0]
        ):
            currentState["fastestLap"] = (updatedDriver["bestLap"], updatedDriver)
            # ac.console("fastest: {}".format(currentState["fastestLap"][0]))
    # if currentState["fastestLap"][0] < previousState["fastestLap"][0]:
    # ac.console("{} just set the fastest lap with a time of {}".format(currentState["fastestLap"][1], currentState["fastestLap"][0]))
    # Update drivers/Fastest lap
    # ac.console("=====================")
    # for pos in range(len(currentState["drivers"])):
    #   ac.console(driver["name"])
    #   currentState["drivers"][driver["id"]] = getDriverInfo(driver["id"]).copy()
    #   if currentState["drivers"][driver["id"]]["bestLap"] < previousState["fastestLap"][0]:
    #     currentState["fastestLap"] = (currentState["drivers"][driver["id"]]["bestLap"], currentState["drivers"][driver["id"]])
    # ac.console("=====================")

    # Standings
    if simInfo.graphics.session == 2:
        # ac.console(lastUpdateTime)
        currentState["drivers"].sort(
            key=lambda driver: driver["distance"], reverse=True
        )
        # ac.console("=====================")
        # for driver in currentState["drivers"]:
        #   ac.console(driver["name"])
        # ac.console("=====================")

        # curr_drivers = [driver["name"] for driver in currentState["drivers"]]
        # prev_drivers = [driver["name"] for driver in previousState["drivers"]]

        # ac.console("prev -- {}".format(', '.join(prev_drivers)))
        # ac.console("curr -- {}".format(', '.join(curr_drivers)))
    else:
        for driver in currentState["drivers"]:
            if driver["bestLap"] == 0:
                driver["bestLap"] = 9999999
        currentState["drivers"].sort(key=lambda driver: driver["bestLap"])

    # Overtakes
    for pos in range(len(currentState["drivers"])):
        # ac.console(currentState["drivers"][pos]["name"])
        # ac.console(previousState["drivers"])
        # ac.console("{}======".format(datetime.datetime.now()))
        # ac.console("{}".format(previousState["drivers"][pos]["name"]))
        # ac.console("name: {}, id: {}".format(currentState["drivers"][pos]["name"], currentState["drivers"][pos]["id"]))
        # ac.console("======")
        if currentState["drivers"][pos]["id"] != previousState["drivers"][pos]["id"]:
            ac.console("OVERTAKE")
            params = {
                "position": pos,
                "overtaker": currentState["drivers"][pos]["name"],
                "overtaken": previousState["drivers"][pos]["name"],
            }
            eventQueue.append(getEvent(OVERTAKE, [], params))
            break

    # # Intervals
    # if simInfo.graphics.session == 2:
    #   for pos in range(1, len(currentState["drivers"])):
    #     interval = calculateTimeInterval(currentState["drivers"][pos - 1], currentState["drivers"][pos])
    #     params = { "driverAhead": currentState["drivers"][pos - 1], "driverBehind": currentState["drivers"][pos], "interval": interval }
    #     if (interval < 2 and interval > 1):
    #       eventQueue.append(getEvent(SHORT_INTERVAL, [], params))
    #     elif (interval <= 1):
    #       eventQueue.append(getEvent(DRS_RANGE, [], params))

    # Compare fastest lap
    if currentState["fastestLap"] != previousState["fastestLap"]:
        eventQueue.append(
            getEvent(
                FASTEST_LAP,
                [currentState["fastestLap"][1]],
                {"lapTime": currentState["fastestLap"][0]},
            )
        )

    # Compare standing
    # if currentState["drivers"] != previousState["standing"]:
    #   max_len = max(len(previousState["standing"]), len(currentState["standing"]))
    #   for i in range(max_len):
    #     if currentState["standing"][i] != statePrevious["standing"][i]:
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

    if len(eventQueue) == 0:
        # ac.console("{} -- No events".format(datetime.datetime.now()))
        step()
        return

    if isCommentating:
        # use probability to determine if the next event in queue should be discarded
        pass
    else:
        isCommentating = True
        prompt = generatePrompt(eventQueue.pop())
        script = enhanceText(prompt)
        audio = textToSpeech(script)
        if audio:
            isCommentating = False

    step()


def calculateTimeInterval(driverAhead, driverBehind):
    deltaD = abs(driverAhead["distance"] - driverBehind["distance"])
    return driverAhead["lastLap"] - (driverBehind["lastLap"] * (1 - deltaD))


def generatePrompt(event):
    ac.console("{} -- event type: {}".format(datetime.datetime.now(), event["type"]))
    # for event in events.sort(reverse=True):
    # if event.type == MODE_CHANGE:
    #   # ToDo: need to figure out how to know when the checkered flag is shown
    #   if event.raceMode == 3:
    #     prompt += f'The race has completed. The results are: '
    #     for i, driver in enumerate(event.params["results"]):
    #       prompt += f"{driver} in {i+1}. "
    prompt = ""
    if event["type"] == YELLOW_FLAG:
        pass
    elif event["type"] == DNF:
        pass
    # elif event.type == COLLISION:
    #   prompt += f"{event['drivers'][0]} and {event['drivers'][1]} had a collision"
    #   pass
    elif event["type"] == OVERTAKE:
        prompt = "{} has overtaken {} and is now in position {}".format(
            event["params"]["overtaker"],
            event["params"]["overtaken"],
            event["params"]["position"],
        )
    elif event["type"] == FASTEST_LAP:
        prompt = "{} just set the fastest lap with a time of {}".format(
            event["drivers"][0]["name"], event["params"]["lapTime"]
        )
    # elif event.type == ENTERED_PIT:
    #   prompt += f'{event.drivers[0].name} has entered the pit. '
    # elif event.type == SHORT_INTERVAL:
    #   prompt += f'{event.drivers[0].name} is only {event.params["interval"]}'
    #   pass
    # elif event.type == LONG_STINT:
    #   prompt += f'{event.drivers[0].name} has completed {event.params["laps"]} laps on {event.param["tire"]} compound tires without pitting.'
    # elif event.type == LONG_PIT:
    #   prompt += f'{event.drivers[0].name} had a long pitstop that took {event.params["duration"]} seconds.'
    # elif event.type == QUICK_PIT:
    #   prompt += f'{event.drivers[0].name} had a very quick pitstop that took {event.params["duration"]} seconds.'

    ac.console(prompt)
    return prompt


def enhanceText(prompt):
    return prompt


def textToSpeech(text):
    # time.sleep(10)
    return True


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
