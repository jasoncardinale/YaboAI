import copy
import datetime

import ac  # type: ignore
import acsys  # type: ignore

from models import Event, EventType, RaceState
from third_party.sim_info import SimInfo

# Global constants
APP_NAME = "YaboAI"
FOCUS_DURATION_MIN_MS = 300
FOCUS_DURATION_MAX_MS = 1500

simInfo = SimInfo()

# Global variables
last_update_time = 0
is_commentating = False
driver_count = 32
sector_count = 0
car_in_focus = 0

event_queue = []

currentState = RaceState()
previousState = RaceState()


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
    global appWindow, driver_count, currentState, previousState

    appWindow = ac.newApp(APP_NAME)
    ac.setTitle(appWindow, APP_NAME)
    ac.setSize(appWindow, 200, 200)

    ac.addRenderCallback(appWindow, appGL)

    drivers = []
    driver_count = ac.getCarsCount()
    for id in range(driver_count):
        drivers.append(getDriverInfo(id))

    previousState["drivers"] = drivers
    currentState["drivers"] = drivers

    return APP_NAME


def appGL(deltaT):
    pass


def eventPriority():
    pass


def step():
    global last_update_time, currentState, previousState
    last_update_time = 0
    previousState = copy.deepcopy(currentState)


def acUpdate(deltaT):
    global \
        last_update_time, \
        event_queue, \
        driver_count, \
        car_in_focus, \
        is_commentating, \
        previousState, \
        currentState

    last_update_time += deltaT
    if last_update_time < 1:
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
            event_queue.append(Event(EventType.OVERTAKE, params))
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
        event_queue.append(
            Event(
                EventType.FASTEST_LAP,
                {
                    "lapTime": currentState["fastestLap"][0],
                    "driver": currentState["fastestLap"][1],
                },
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

    if len(event_queue) == 0:
        # ac.console("{} -- No events".format(datetime.datetime.now()))
        step()
        return

    if is_commentating:
        # use probability to determine if the next event in queue should be discarded
        pass
    else:
        is_commentating = True
        prompt = generatePrompt(event_queue.pop())
        script = enhanceText(prompt)
        audio = textToSpeech(script)
        if audio:
            is_commentating = False

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
    if event["type"] == EventType.SAFETY_CAR:
        pass
    elif event["type"] == EventType.DNF:
        pass
    # elif event.type == COLLISION:
    #   prompt += f"{event['drivers'][0]} and {event['drivers'][1]} had a collision"
    #   pass
    elif event["type"] == EventType.OVERTAKE:
        prompt = "{} has overtaken {} and is now in position {}".format(
            event["params"]["overtaker"],
            event["params"]["overtaken"],
            event["params"]["position"],
        )
    elif event["type"] == EventType.FASTEST_LAP:
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
