import copy
import datetime

import ac  # type: ignore

from models import Driver, EventType, RaceState
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


def acMain(ac_version):
    global appWindow, driver_count, currentState, previousState

    appWindow = ac.newApp(APP_NAME)
    ac.setTitle(appWindow, APP_NAME)
    ac.setSize(appWindow, 200, 200)

    ac.addRenderCallback(appWindow, appGL)

    driver_count = ac.getCarsCount()
    for id in range(driver_count):
        driver = Driver(id)
        previousState.add_driver(driver)
        currentState.add_driver(driver)

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
    if last_update_time < 5:
        return

    currentState.update()

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
    if event["type"] == EventType.START_SAFETY_CAR:
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
