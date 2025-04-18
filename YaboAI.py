import copy
import datetime

import ac  # type: ignore

from llm.services import chat_completion
from models import Driver, Event, EventType, RaceState
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

event_queue: list[Event] = []

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

    event_queue.extend(currentState.update())

    if len(event_queue) == 0:
        step()
        return

    if is_commentating:
        # use probability to determine if the next event in queue should be discarded
        pass
    else:
        is_commentating = True
        # TODO: focus camera on event.driver_id
        prompts: list[str] = []
        while event := event_queue.pop():
            prompts.append(generatePrompt(event))
        script = chat_completion(("\n".join(prompts)))
        audio = textToSpeech(script)
        if audio:
            is_commentating = False

    step()


def generatePrompt(event: Event):
    ac.console("{} -- event type: {}".format(datetime.datetime.now(), event.type))
    prompt = ""
    match event.type:
        case EventType.START_SAFETY_CAR:
            prompt += f"{1}"
        case EventType.END_SAFETY_CAR:
            prompt += f"{1}"
        case EventType.DNF:
            prompt += f"{1}"
        case EventType.COLLISION:
            prompt += f"{1}"
        case EventType.BEST_LAP:
            prompt += f"{1}"
        case EventType.FASTEST_LAP:
            prompt += f"{1}"
        case EventType.ENTERED_PIT:
            prompt += f'{event.params["driver"]} has entered the pit.'
        case EventType.QUICK_PIT:
            prompt += f"{1}"
        case EventType.LONG_PIT:
            prompt += f"{1}"
        case EventType.SHORT_INTERVAL:
            prompt += f"{1}"
        case EventType.DRS_RANGE:
            prompt += f"{1}"
        case EventType.OVERTAKE:
            prompt = f"{event.params['driver_a']} has overtaken {event.params['driver_b']} and is now in position {event.params['position']}"
        case EventType.LONG_STINT:
            pass

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


def textToSpeech(text):
    # time.sleep(10)
    return True
